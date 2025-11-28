"""Representa um segmento de voo com seus cálculos de tempo/consumo."""
from ..settings import Config
from ...utils_custom.calculos import distancia_haversine, calcular_direcao, calcular_velocidade_efetiva


class Trecho:
    """Trecho entre `origem` e `destino` contendo métricas calculadas."""

    def __init__(self, origem, destino, velocidade, dia, hora_partida, vento_velocidade, vento_angulo):
        self.origem = origem
        self.destino = destino
        self.velocidade = int(velocidade)
        self.dia = dia
        self.hora_partida = int(hora_partida)
        self.vento_velocidade = vento_velocidade
        self.vento_angulo = vento_angulo

        self._calcular_metricas()

    def _calcular_metricas(self):
        self.distancia = distancia_haversine(self.origem.latitude, self.origem.longitude, self.destino.latitude, self.destino.longitude)

        self.direcao_voo = calcular_direcao(self.origem.latitude, self.origem.longitude, self.destino.latitude, self.destino.longitude)

        self.velocidade_efetiva = calcular_velocidade_efetiva(self.velocidade, self.direcao_voo, self.vento_velocidade, self.vento_angulo)

        tempo_horas = self.distancia / max(0.001, self.velocidade_efetiva)
        self.tempo_voo_segundos = int(tempo_horas * 3600) + 1

        self.consumo_bateria = self.tempo_voo_segundos
        self.custo = 0

    def get_hora_chegada(self):
        return self.hora_partida + (self.tempo_voo_segundos // 60)

    def precisa_recarregar(self, bateria_atual):
        reserva = getattr(Config, 'BATTERY_RESERVE_SECONDS', 0)
        return (self.consumo_bateria + reserva) > bateria_atual

    def __repr__(self):
        return (f"Trecho({self.origem.cep}→{self.destino.cep}: {self.distancia:.1f}km, v={self.velocidade}km/h, t={self.tempo_voo_segundos}s)")
