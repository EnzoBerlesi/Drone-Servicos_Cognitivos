import math
from datetime import datetime, timedelta, time
import csv
import os

# Constants
MAX_SPEED_KMH = 96.0
# Velocidade mínima: 10 m/s = 36 km/h (conforme especificação do PDF)
MIN_SPEED_KMH = 36.0
REF_SPEED_KMH = 36.0
# Velocidades reguladas: múltiplos de 4 km/h, mínimo 36 km/h
SPEED_STEP = 4.0
VALID_SPEEDS = list(range(36, 97, 4))  # [36, 40, 44, 48, ..., 96]
# Autonomia nominal em laboratório (20°C, sem vento) conforme especificação do PDF
NOMINAL_AUTONOMY_S = 5000.0
# Fator de correção para Curitiba (aplicado sobre a autonomia calculada pela fórmula)
CURITIBA_FACTOR = 0.93
STOP_AUTONOMY_COST_S = 72.0
RECHARGE_DURATION_S = 1800.0  # 30 minutes to recharge to full

# Autonomia base para cálculos (será ajustada pela velocidade usando a fórmula)
# A fórmula é: A(v) = 5000 * (36/v)²
# Para Curitiba: A(v) = 5000 * (36/v)² * 0.93
def get_autonomy_for_speed(speed_kmh):
    """
    Calcula autonomia em segundos para uma dada velocidade.
    Fórmula: A(v) = NOMINAL_AUTONOMY_S * (REF_SPEED_KMH / v)² * CURITIBA_FACTOR
    
    Onde:
    - NOMINAL_AUTONOMY_S = 5000s (autonomia nominal em laboratório a 20°C, sem vento)
    - REF_SPEED_KMH = 36 km/h (velocidade de referência)
    - CURITIBA_FACTOR = 0.93 (fator de correção para condições de Curitiba)
    """
    if speed_kmh <= 0:
        return 0
    return NOMINAL_AUTONOMY_S * (REF_SPEED_KMH / speed_kmh) ** 2 * CURITIBA_FACTOR

# Autonomia padrão (quando velocidade = 36 km/h)
AUTONOMY_S = get_autonomy_for_speed(REF_SPEED_KMH)

HOME_CEP = "82821020"

def validate_speed(speed_kmh):
    """
    Valida e ajusta velocidade conforme regras do PDF:
    - Deve ser múltiplo de 4 km/h
    - Mínimo 36 km/h (10 m/s)
    - Máximo 96 km/h
    
    Retorna a velocidade válida mais próxima.
    """
    # Arredondar para o múltiplo de 4 mais próximo
    speed_kmh = round(speed_kmh / SPEED_STEP) * SPEED_STEP
    # Aplicar limites
    speed_kmh = max(MIN_SPEED_KMH, min(MAX_SPEED_KMH, speed_kmh))
    return speed_kmh

def get_valid_speeds():
    """
    Retorna lista de todas as velocidades válidas.
    Velocidades: 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96 km/h
    """
    return VALID_SPEEDS.copy()

def haversine_km(lat1, lon1, lat2, lon2):
    # returns distance in km
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def load_ceps(path):
    ceps = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            ceps.append({
                'cep': row['cep'],
                'lat': float(row['lat']),
                'lon': float(row['lon'])
            })
    return ceps

def load_wind_table(path):
    # returns dict[(day:int,hour:int)]=(speed_kmh, dir_deg)
    table = {}
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            # skip empty or commented lines (e.g. lines starting with '#')
            day_str = (row.get('day') or '').strip()
            if not day_str or day_str.startswith('#'):
                continue
            try:
                d = int(day_str)
                h = int(row['hour'])
                table[(d, h)] = (float(row['wind_kmh']), float(row['wind_dir_deg']))
            except (ValueError, KeyError):
                # skip malformed rows
                continue
    return table

def unit_vector_from_bearing(bearing_deg):
    # bearing degrees from North clockwise -> returns (dx, dy) in km components (East, North)
    # Convert to radians and compute unit vector in (east, north)
    theta = math.radians(bearing_deg)
    # bearing 0 = north -> (0,1)
    dx = math.sin(theta)
    dy = math.cos(theta)
    return dx, dy

def bearing_deg(lat1, lon1, lat2, lon2):
    # formula for bearing from point1 to point2 (degrees from North)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def wind_component_along_course(wind_kmh, wind_dir_deg, course_deg):
    """
    DEPRECATED: Esta função calculava apenas a projeção do vento.
    Use effective_speed_kmh_vectorial para cálculo correto com soma vetorial.
    
    Retorna a componente do vento ao longo do curso (projeção).
    Positivo se vento de cauda (tailwind), negativo se vento de frente (headwind).
    """
    wx, wy = unit_vector_from_bearing(wind_dir_deg)
    cx, cy = unit_vector_from_bearing(course_deg)
    dot = wx*cx + wy*cy
    return wind_kmh * dot

def effective_speed_kmh(requested_speed_kmh, wind_kmh, wind_dir_deg, course_deg):
    """
    Calcula velocidade efetiva no solo (ground speed) usando soma vetorial.
    
    Args:
        requested_speed_kmh: Velocidade do ar do drone (airspeed)
        wind_kmh: Magnitude do vento
        wind_dir_deg: Direção para onde o vento sopra (bearing em graus do Norte)
        course_deg: Direção do curso do drone (bearing em graus do Norte)
    
    Returns:
        Velocidade efetiva no solo em km/h
    
    Método:
        1. Calcula componentes do vetor velocidade do drone no ar
        2. Calcula componentes do vetor vento
        3. Soma vetorialmente: v_ground = v_drone + v_wind
        4. Retorna magnitude do vetor resultante
    """
    import math
    
    # Componentes da velocidade do drone (no ar)
    v_drone_x = requested_speed_kmh * math.sin(math.radians(course_deg))
    v_drone_y = requested_speed_kmh * math.cos(math.radians(course_deg))
    
    # Componentes do vento
    v_wind_x = wind_kmh * math.sin(math.radians(wind_dir_deg))
    v_wind_y = wind_kmh * math.cos(math.radians(wind_dir_deg))
    
    # Soma vetorial: velocidade no solo (ground speed)
    v_ground_x = v_drone_x + v_wind_x
    v_ground_y = v_drone_y + v_wind_y
    
    # Magnitude do vetor resultante
    ground_speed = math.sqrt(v_ground_x**2 + v_ground_y**2)
    
    # Garantir que a velocidade não seja negativa
    return max(1e-3, ground_speed)

def seconds_for_distance_km(distance_km, speed_kmh):
    # time in seconds
    hours = distance_km / max(1e-6, speed_kmh)
    return hours * 3600.0

def datetime_from_day_hour(day:int, hour:int, minute:int=0):
    # day: 1..7 -> returns a datetime anchored at arbitrary date
    base = datetime(2025,11,1)  # arbitrary anchor
    return base + timedelta(days=day-1, hours=hour, minutes=minute)

def time_to_day_hour(dt:datetime):
    base = datetime(2025,11,1)
    delta = dt - base
    day = delta.days + 1
    return day, dt.hour, dt.minute

def clamp_to_day_window(dt:datetime):
    # if dt time <06:00 -> move to 06:00 same day; if >19:00 -> move to 06:00 next day
    h = dt.time()
    if h < time(6,0):
        return dt.replace(hour=6, minute=0, second=0, microsecond=0)
    if h >= time(19,0):
        return (dt + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    return dt

def format_time(dt:datetime):
    day, hour, minute = time_to_day_hour(dt)
    return f"{day},{dt.strftime('%H:%M')}", day, dt.strftime('%H:%M')

def ensure_within_7_days(dt:datetime):
    base = datetime(2025,11,1)
    return dt <= base + timedelta(days=7, hours=19)
