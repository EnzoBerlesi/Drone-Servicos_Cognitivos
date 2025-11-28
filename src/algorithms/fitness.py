"""Fitness multi-objetivo utilizado pelo AG.

Reformulei comentários e compactei alguns trechos mantendo a
semântica inalterada.
"""
from ..core.settings import Config


class FitnessFunction:
    """Agrega componentes (tempo, custo, penalidades, distância)."""

    def __init__(self, peso_tempo=1.0, peso_custo=1.0, peso_penalidades=1.0, peso_distancia=0.0):
        self.peso_tempo = peso_tempo
        self.peso_custo = peso_custo
        self.peso_penalidades = peso_penalidades
        self.peso_distancia = peso_distancia

    def calcular(self, individuo):
        """Retorna o valor de fitness (menor é melhor).

        A função assegura que a rota esteja simulada antes do cálculo.
        """
        if not individuo.viabilidade:
            return float('inf')

        if not individuo.trechos:
            individuo.simular_rota()

        custo = individuo.custo_total * self.peso_custo
        tempo = individuo.tempo_total * self.peso_tempo
        penalidades = individuo.penalidades * self.peso_penalidades

        distancia_km = getattr(individuo, 'distancia_total', 0)
        try:
            norma = float(Config.FITNESS_DIST_NORMALIZATION)
            dist_norm = distancia_km / norma if norma and norma > 0 else distancia_km
        except Exception:
            dist_norm = distancia_km

        distancia = dist_norm * self.peso_distancia

        valor = custo + tempo + penalidades + distancia

        if individuo.dias_utilizados >= 6:
            valor *= 1.1

        return valor

    def calcular_media_geracao(self, populacao):
        """Calcula a média de fitness ignorando indivíduos inviáveis."""
        valores = []
        for ind in populacao:
            if getattr(ind, 'fitness', None) is not None:
                valores.append(ind.fitness)
            else:
                f = self.calcular(ind)
                try:
                    ind.fitness = f
                except Exception:
                    pass
                valores.append(f)

        validos = [v for v in valores if v != float('inf')]
        if not validos:
            return float('inf')

        return sum(validos) / len(validos)

    def __repr__(self):
        return f"FitnessFunction(tempo={self.peso_tempo}, custo={self.peso_custo}, distancia={self.peso_distancia})"
