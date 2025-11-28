"""Operações matemáticas auxiliares (geodésicas e vetoriais)."""
import math


def distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula a distância (km) entre dois pontos via Haversine."""
    R = 6371.0

    a1 = math.radians(lat1)
    b1 = math.radians(lon1)
    a2 = math.radians(lat2)
    b2 = math.radians(lon2)

    da = a2 - a1
    db = b2 - b1

    sin_da = math.sin(da / 2.0)
    sin_db = math.sin(db / 2.0)

    a = sin_da * sin_da + math.cos(a1) * math.cos(a2) * (sin_db * sin_db)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calcular_direcao(lat1, lon1, lat2, lon2):
    """Calcula o bearing de P1 -> P2 em graus no intervalo [0,360)."""
    a1 = math.radians(lat1)
    b1 = math.radians(lon1)
    a2 = math.radians(lat2)
    b2 = math.radians(lon2)

    dlon = b2 - b1

    x = math.sin(dlon) * math.cos(a2)
    y = math.cos(a1) * math.sin(a2) - math.sin(a1) * math.cos(a2) * math.cos(dlon)

    ang = math.degrees(math.atan2(x, y))
    return (ang + 360) % 360


def cardinal_para_angulo(cardinal):
    """Mapeia pontos cardeais abreviados para ângulo em graus."""
    direcoes = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return direcoes.get(cardinal.upper(), 0)


def calcular_velocidade_efetiva(velocidade_drone, direcao_voo, vento_velocidade, vento_direcao):
    """Retorna a ground speed (km/h) resultante do somatório vetorial."""
    av = math.radians(direcao_voo)
    avv = math.radians(vento_direcao)

    vdx = velocidade_drone * math.sin(av)
    vdy = velocidade_drone * math.cos(av)

    wdx = vento_velocidade * math.sin(avv)
    wdy = vento_velocidade * math.cos(avv)

    gx = vdx + wdx
    gy = vdy + wdy

    # usa hypot para legibilidade
    ground_speed = math.hypot(gx, gy)
    return max(0.1, ground_speed)


def validar_velocidade(velocidade):
    """Ajusta velocidade para o espaço válido (múltiplo de 4 entre 36 e 96)."""
    prox = round(velocidade / 4) * 4
    prox = max(36, min(96, prox))
    return int(prox)


def get_velocidades_validas():
    return list(range(36, 97, 4))
