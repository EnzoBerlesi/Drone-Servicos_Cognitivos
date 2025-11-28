"""
Configurações centralizadas do projeto baseadas no PDF
"""

class Config:
    """Configurações do projeto de otimização de rotas de drone"""
    
    # === PARÂMETROS DO DRONE ===
    VELOCIDADE_REFERENCIA = 36  # km/h (velocidade base para cálculos)
    AUTONOMIA_REFERENCIA = 5000  # segundos (autonomia em lab a 20°C sem vento)
    FATOR_CORRECAO = 0.93  # Fator de correção para condições de Curitiba
    VELOCIDADE_MINIMA = 36  # km/h (10 m/s conforme PDF)
    VELOCIDADE_MAXIMA = 96  # km/h
    TEMPO_PARADA = 72  # segundos por parada (foto/pouso)
    TEMPO_RECARGA = 1.2  # minutos (72 segundos)
    BATTERY_RESERVE_SECONDS = 300  # Margem de segurança (5 minutos)
    
    # === HORÁRIOS DE OPERAÇÃO ===
    HORA_INICIO = 6 * 60  # 06:00 em minutos desde meia-noite
    HORA_FIM = 19 * 60    # 19:00 em minutos
    HORA_TAXA_EXTRA = 17 * 60  # 17:00 para taxa adicional
    HORA_LIMITE_TAXA = 18 * 60  # 18:00 em minutos (1080 minutos)
    
    # === CUSTOS ===
    CUSTO_RECARGA = 80.0  # R$ por recarga base
    CUSTO_TAXA_TARDE = 80.0  # R$ adicional por pouso após 17:00
    TAXA_TARDE = 80.0  # R$ adicional (alias para compatibilidade)
    CUSTO_POR_MINUTO = 0.0  # R$ por minuto de operação
    TAXA_BASEADA_EM = 'start'  # 'start' ou 'end' - quando aplicar taxa tarde
    
    # === PROJETO ===
    DIAS_MAXIMOS = 7  # Máximo de dias para completar missão
    CEP_INICIAL = "82821020"  # Unibrasil (ponto de partida e chegada)
    
    # === HEURÍSTICAS ===
    # Função custo para escolha de velocidade: custo = ALPHA * tempo + BETA * consumo
    HEURISTICA_ALPHA = 3.0
    HEURISTICA_BETA = 1.0
    
    # === PENALIDADES ===
    HARD_DIAS_MAX = False  # Se True, invalida rotas que excedem DIAS_MAXIMOS
    PENALIDADE_POR_DIA_EXCEDIDO = 10000  # Penalidade por dia além do limite
    
    # === FITNESS ===
    FITNESS_PESO_DISTANCIA = 10.0  # Peso da distância no cálculo de fitness
    FITNESS_DIST_NORMALIZATION = 8.0  # Normalizador para distância (km)
    FITNESS_PESO_TEMPO = 0.5  # Peso do tempo
    FITNESS_PESO_CUSTO = 1.0  # Peso do custo monetário
    FITNESS_PESO_PENALIDADES = 10.0  # Peso das penalidades
    
    # === COMPARAÇÃO (para análises) ===
    AUTONOMIA_COMPARISON_MINUTES = [20, 30, 45, 77]  # Lista para análises comparativas
