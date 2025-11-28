"""
Função de fitness especializada para o problema do drone
"""
from ..core.settings import Config

class FitnessFunction:
    """Calcula fitness de indivíduos considerando múltiplos objetivos"""
    
    def __init__(self, peso_tempo=1.0, peso_custo=1.0, peso_penalidades=1.0, peso_distancia=0.0):
        """
        Inicializa função de fitness com pesos configuráveis.
        
        Args:
            peso_tempo: Peso para tempo total
            peso_custo: Peso para custo monetário
            peso_penalidades: Peso para penalidades
            peso_distancia: Peso para distância total
        """
        self.peso_tempo = peso_tempo
        self.peso_custo = peso_custo
        self.peso_penalidades = peso_penalidades
        self.peso_distancia = peso_distancia
    
    def calcular(self, individuo):
        """
        Calcula fitness de um indivíduo.
        
        Args:
            individuo: Instância de Individuo
        
        Returns:
            float: Valor de fitness (menor é melhor)
        """
        if not individuo.viabilidade:
            return float('inf')
        
        # Simular se ainda não foi simulado
        if not individuo.trechos:
            individuo.simular_rota()
        
        # Componentes do fitness
        custo_componente = individuo.custo_total * self.peso_custo
        tempo_componente = individuo.tempo_total * self.peso_tempo
        penalidades_componente = individuo.penalidades * self.peso_penalidades
        
        # Normalizar distância
        distancia_km = getattr(individuo, 'distancia_total', 0)
        try:
            norma = float(Config.FITNESS_DIST_NORMALIZATION)
            distancia_normalizada = distancia_km / norma if norma and norma > 0 else distancia_km
        except Exception:
            distancia_normalizada = distancia_km
        
        distancia_componente = distancia_normalizada * self.peso_distancia
        
        fitness = custo_componente + tempo_componente + penalidades_componente + distancia_componente
        
        # Penalidade extra para muitos dias
        if individuo.dias_utilizados >= 6:
            fitness *= 1.1
        
        return fitness
    
    def calcular_media_geracao(self, populacao):
        """
        Calcula média de fitness de uma geração.
        
        Args:
            populacao: Lista de indivíduos
        
        Returns:
            float: Fitness médio
        """
        valores = []
        for ind in populacao:
            if hasattr(ind, 'fitness') and ind.fitness is not None:
                valor = ind.fitness
            else:
                valor = self.calcular(ind)
                if hasattr(ind, '__dict__'):
                    ind.fitness = valor
            valores.append(valor)
        
        # Ignorar indivíduos inviáveis
        valores_validos = [v for v in valores if v != float('inf')]
        if not valores_validos:
            return float('inf')
        
        return sum(valores_validos) / len(valores_validos)
    
    def __repr__(self):
        return (f"FitnessFunction(tempo={self.peso_tempo}, custo={self.peso_custo}, "
                f"distancia={self.peso_distancia})")
