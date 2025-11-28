"""
Utilitários para manipulação de tempo e conversões
"""
from ..core.settings import Config

def abs_to_day_and_minuto(minutos_abs):
    """
    Converte minutos absolutos desde o início da missão para (dia, minuto_do_dia).
    
    Args:
        minutos_abs: Minutos desde o início da simulação
    
    Returns:
        tuple: (dia, minuto_do_dia)
    """
    minutos_totais = Config.HORA_INICIO + minutos_abs
    dia = (minutos_totais // (24 * 60)) + 1
    minuto_do_dia = minutos_totais % (24 * 60)
    return int(dia), int(minuto_do_dia)

def formatar_hora(minutos):
    """
    Formata minutos desde meia-noite para string HH:MM.
    
    Args:
        minutos: Minutos desde 00:00
    
    Returns:
        str: Hora formatada como HH:MM
    """
    horas = int(minutos) // 60
    mins = int(minutos) % 60
    return f"{horas:02d}:{mins:02d}"

def formatar_hora_csv(minutos):
    """
    Formata hora para CSV com segundos (HH:MM:SS).
    
    Args:
        minutos: Minutos desde 00:00
    
    Returns:
        str: Hora formatada como HH:MM:SS
    """
    horas = int(minutos) // 60
    mins = int(minutos) % 60
    return f"{horas:02d}:{mins:02d}:00"
