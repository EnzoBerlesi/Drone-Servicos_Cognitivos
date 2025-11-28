"""
Funções de cálculo geográfico e físico para o projeto
"""
import math

def distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula distância entre duas coordenadas usando fórmula de Haversine.
    
    Args:
        lat1, lon1: Latitude e longitude do ponto 1 (graus)
        lat2, lon2: Latitude e longitude do ponto 2 (graus)
    
    Returns:
        float: Distância em quilômetros
    """
    R = 6371.0  # Raio da Terra em km
    
    # Converter para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferenças
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = (math.sin(dlat/2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calcular_direcao(lat1, lon1, lat2, lon2):
    """
    Calcula bearing (direção) do movimento entre dois pontos.
    
    Args:
        lat1, lon1: Coordenadas do ponto inicial
        lat2, lon2: Coordenadas do ponto final
    
    Returns:
        float: Ângulo em graus (0 = Norte, 90 = Leste, sentido horário)
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    
    x = math.sin(dlon) * math.cos(lat2_rad)
    y = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
    
    direcao_rad = math.atan2(x, y)
    direcao_graus = math.degrees(direcao_rad)
    
    return (direcao_graus + 360) % 360

def cardinal_para_angulo(cardinal):
    """
    Converte direção cardinal para ângulo em graus.
    
    Args:
        cardinal: String com direção (N, NE, E, SE, S, SW, W, NW, etc.)
    
    Returns:
        float: Ângulo em graus (0-360)
    """
    direcoes = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return direcoes.get(cardinal.upper(), 0)

def calcular_velocidade_efetiva(velocidade_drone, direcao_voo, vento_velocidade, vento_direcao):
    """
    Calcula velocidade efetiva no solo usando soma vetorial.
    
    Args:
        velocidade_drone: Velocidade do ar do drone (airspeed) em km/h
        direcao_voo: Direção do voo em graus (bearing)
        vento_velocidade: Velocidade do vento em km/h
        vento_direcao: Direção PARA ONDE o vento sopra em graus
    
    Returns:
        float: Velocidade efetiva no solo (groundspeed) em km/h
    """
    angulo_voo_rad = math.radians(direcao_voo)
    angulo_vento_rad = math.radians(vento_direcao)
    
    # Componentes da velocidade do drone no ar
    v_drone_x = velocidade_drone * math.sin(angulo_voo_rad)
    v_drone_y = velocidade_drone * math.cos(angulo_voo_rad)
    
    # Componentes do vento
    v_vento_x = vento_velocidade * math.sin(angulo_vento_rad)
    v_vento_y = vento_velocidade * math.cos(angulo_vento_rad)
    
    # Soma vetorial: velocidade no solo
    v_ground_x = v_drone_x + v_vento_x
    v_ground_y = v_drone_y + v_vento_y
    
    # Magnitude do vetor resultante
    ground_speed = math.sqrt(v_ground_x**2 + v_ground_y**2)
    
    # Evitar velocidade zero ou negativa
    return max(0.1, ground_speed)

def validar_velocidade(velocidade):
    """
    Valida e ajusta velocidade para estar dentro dos limites do projeto.
    - Deve ser múltiplo de 4 km/h
    - Entre 36 e 96 km/h
    
    Args:
        velocidade: Velocidade desejada em km/h
    
    Returns:
        int: Velocidade válida mais próxima
    """
    # Arredondar para múltiplo de 4 mais próximo
    velocidade = round(velocidade / 4) * 4
    # Aplicar limites
    velocidade = max(36, min(96, velocidade))
    return int(velocidade)

def get_velocidades_validas():
    """
    Retorna lista de todas as velocidades válidas.
    
    Returns:
        list: Lista de velocidades em km/h [36, 40, 44, ..., 96]
    """
    return list(range(36, 97, 4))
