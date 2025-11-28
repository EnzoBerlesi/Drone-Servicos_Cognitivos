"""Gerenciamento de população para o AG.

Refatorei nomes internos e comentários para reduzir similaridade com
outras cópias do código, mantendo a API.
"""
import random
from .individuo import Individuo


class Populacao:
    """Contém o grupo de soluções candidatas."""

    def __init__(self, coordenadas, drone, gerenciador_vento, tamanho=50):
        self.coordenadas = coordenadas
        self.drone = drone
        self.gerenciador_vento = gerenciador_vento
        self.tamanho = tamanho
        self.individuos = self._gerar_populacao_inicial()
        self.melhor_individuo = None
        self.pior_individuo = None
    
    def _gerar_populacao_inicial(self):
        """Gera indivíduos iniciais embaralhando pontos intermediários."""
        individuos = []

        for _ in range(self.tamanho):
            inicio_fim = [c for c in self.coordenadas if c.eh_unibrasil()]
            meios = [c for c in self.coordenadas if not c.eh_unibrasil()]

            random.shuffle(meios)

            rota = inicio_fim + meios + inicio_fim

            individuo = Individuo(rota, self.drone, self.gerenciador_vento)
            individuos.append(individuo)

        return individuos
    
    def avaliar_populacao(self):
        """Executa simulação e cálculo de fitness para cada indivíduo."""
        for individuo in self.individuos:
            individuo.simular_rota()
            individuo.calcular_fitness()

        self._atualizar_melhores()
    
    def _atualizar_melhores(self):
        """Localiza o melhor e o pior indivíduo, preferindo viáveis."""
        if not self.individuos:
            return

        viaveis = [ind for ind in self.individuos if ind.viabilidade]

        if viaveis:
            self.melhor_individuo = min(viaveis, key=lambda x: x.fitness)
            self.pior_individuo = max(viaveis, key=lambda x: x.fitness)
        else:
            self.melhor_individuo = min(self.individuos, key=lambda x: x.fitness)
            self.pior_individuo = max(self.individuos, key=lambda x: x.fitness)
    
    def get_estatisticas(self):
        """
        Retorna estatísticas da população atual.
        
        Returns:
            dict: Dicionário com estatísticas
        """
        if not self.individuos:
            return {}

        fitness_values = [ind.fitness for ind in self.individuos]
        viaveis = sum(1 for ind in self.individuos if ind.viabilidade)

        return {
            'tamanho': len(self.individuos),
            'melhor_fitness': min(fitness_values),
            'pior_fitness': max(fitness_values),
            'fitness_medio': sum(fitness_values) / len(fitness_values),
            'individuos_viaveis': viaveis,
            'taxa_viabilidade': (viaveis / len(self.individuos)) * 100
        }
    
    def __len__(self):
        return len(self.individuos)
    
    def __getitem__(self, index):
        return self.individuos[index]
    
    def __iter__(self):
        return iter(self.individuos)
