"""Helpers para conversão de minutos/horas usados pela simulação."""
from ..core.settings import Config


def abs_to_day_and_minuto(minutos_abs):
    """Retorna (dia, minuto_do_dia) dado minutos absolutos desde início."""
    total = Config.HORA_INICIO + minutos_abs
    dia = total // (24 * 60) + 1
    minuto_do_dia = total % (24 * 60)
    return int(dia), int(minuto_do_dia)


def formatar_hora(minutos):
    """Formata minutos em `HH:MM`."""
    horas, mins = divmod(int(minutos), 60)
    return f"{horas:02d}:{mins:02d}"


def formatar_hora_csv(minutos):
    """Formata minutos em `HH:MM:SS` (segundos sempre :00)."""
    horas, mins = divmod(int(minutos), 60)
    return f"{horas:02d}:{mins:02d}:00"
