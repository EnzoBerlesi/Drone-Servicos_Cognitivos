"""
Implementação do Algoritmo Genético para otimização de rotas
"""
import random
import copy
from ..core.individuo import Individuo
from .fitness import FitnessFunction

class AlgoritmoGenetico:
    """Algoritmo Genético para otimização de rotas de drone"""
    
    def __init__(self, populacao, taxa_mutacao=0.02, taxa_crossover=0.8, 
                 elitismo=True, percentual_elitismo=0.1):
        """
        Inicializa o Algoritmo Genético.
        
        Args:
            populacao: Instância de Populacao
            taxa_mutacao: Taxa de mutação (0-1)
            taxa_crossover: Taxa de crossover (0-1)
            elitismo: Se True, mantém melhores indivíduos
            percentual_elitismo: Percentual de elite a preservar
        """
        self.populacao = populacao
        self.taxa_mutacao = taxa_mutacao
        self.taxa_crossover = taxa_crossover
        self.elitismo = elitismo
        self.percentual_elitismo = percentual_elitismo
        self.historico = []
        self.melhor_global = None
        self.fitness_func = FitnessFunction()
        self.geracoes_sem_melhora = 0
    
    def executar_geracao(self):
        """
        Executa uma geração completa do AG.
        
        Returns:
            dict: Estatísticas da geração
        """
        # Avaliar população atual
        self.populacao.avaliar_populacao()
        
        # Atualizar melhor global
        if self.populacao.melhor_individuo:
            atual = self.populacao.melhor_individuo
            if self.melhor_global is None or atual.fitness < self.melhor_global.fitness:
                self.melhor_global = copy.deepcopy(atual)
                self.geracoes_sem_melhora = 0
            else:
                self.geracoes_sem_melhora += 1
        
        # Ajuste adaptativo da taxa de mutação
        if self.geracoes_sem_melhora > 1:
            self.taxa_mutacao = min(0.2, self.taxa_mutacao * 1.5)
        else:
            self.taxa_mutacao = max(0.02, self.taxa_mutacao * 0.95)
        
        # Registrar métricas
        self._registrar_metricas()
        
        # Criar nova geração
        nova_populacao = self._criar_nova_populacao()
        self.populacao.individuos = nova_populacao
        
        return self.populacao.get_estatisticas()
    
    def _criar_nova_populacao(self):
        """
        Cria nova geração através de seleção, crossover e mutação.
        
        Returns:
            list: Nova população de indivíduos
        """
        nova_populacao = []
        
        # Elitismo: preservar os melhores
        if self.elitismo and self.populacao.individuos:
            num_elite = max(1, int(self.populacao.tamanho * self.percentual_elitismo))
            elite_sorted = sorted(self.populacao.individuos, key=lambda x: x.fitness)[:num_elite]
            for ind in elite_sorted:
                # Tentar melhorar elite com heurística de inversão
                melhorado = self._mutacao_inversao(ind)
                nova_populacao.append(copy.deepcopy(melhorado))
        
        # Preencher restante da população
        while len(nova_populacao) < self.populacao.tamanho:
            # Seleção por torneio
            pai1 = self._selecao_torneio(k=5)
            pai2 = self._selecao_torneio(k=5)
            
            # Crossover
            if random.random() < self.taxa_crossover:
                filho = self._crossover_ox(pai1, pai2)
            else:
                filho = copy.deepcopy(pai1)
            
            # Mutação
            if random.random() < self.taxa_mutacao:
                if random.random() < 0.5:
                    filho = self._mutacao_troca(filho)
                else:
                    filho = self._mutacao_inversao(filho)
            
            nova_populacao.append(filho)
        
        return nova_populacao[:self.populacao.tamanho]
    
    def _selecao_torneio(self, k=3):
        """
        Seleção por torneio.
        
        Args:
            k: Tamanho do torneio
        
        Returns:
            Individuo: Indivíduo vencedor do torneio
        """
        participantes = random.sample(
            self.populacao.individuos, 
            min(k, len(self.populacao.individuos))
        )
        return min(participantes, key=lambda x: x.fitness)
    
    def _crossover_ox(self, pai1, pai2):
        """
        Crossover por ordem (Order Crossover - OX).
        
        Args:
            pai1, pai2: Indivíduos pais
        
        Returns:
            Individuo: Filho gerado
        """
        size = len(pai1.coordenadas)
        if size <= 3:
            return copy.deepcopy(pai1)
        
        # Selecionar segmento aleatório
        start, end = sorted(random.sample(range(1, size - 1), 2))
        
        # Criar filho
        filho_coords = [None] * size
        filho_coords[0] = pai1.coordenadas[0]  # Unibrasil início
        filho_coords[-1] = pai1.coordenadas[-1]  # Unibrasil fim
        filho_coords[start:end] = pai1.coordenadas[start:end]
        
        # Preencher com genes do pai2
        pos = end
        for gene in pai2.coordenadas:
            if gene.eh_unibrasil():
                continue
            if gene not in filho_coords:
                while filho_coords[pos] is not None and pos < size - 1:
                    pos += 1
                    if pos >= size - 1:
                        pos = 1
                filho_coords[pos] = gene
        
        return Individuo(filho_coords, self.populacao.drone, self.populacao.gerenciador_vento)
    
    def _mutacao_troca(self, individuo):
        """
        Mutação por troca de duas posições.
        
        Args:
            individuo: Indivíduo a mutar
        
        Returns:
            Individuo: Novo indivíduo mutado
        """
        coords = individuo.coordenadas.copy()
        indices_validos = [
            i for i, coord in enumerate(coords) 
            if not coord.eh_unibrasil() and i not in (0, len(coords)-1)
        ]
        
        if len(indices_validos) >= 2:
            i, j = random.sample(indices_validos, 2)
            coords[i], coords[j] = coords[j], coords[i]
        
        return Individuo(coords, self.populacao.drone, self.populacao.gerenciador_vento)
    
    def _mutacao_inversao(self, individuo):
        """
        Mutação por inversão de subrota (2-opt local).
        
        Args:
            individuo: Indivíduo a mutar
        
        Returns:
            Individuo: Novo indivíduo mutado
        """
        coords = individuo.coordenadas.copy()
        indices_validos = [
            i for i in range(1, len(coords)-1) 
            if not coords[i].eh_unibrasil()
        ]
        
        if len(indices_validos) >= 2:
            i, j = sorted(random.sample(indices_validos, 2))
            coords[i:j] = reversed(coords[i:j])
        
        return Individuo(coords, self.populacao.drone, self.populacao.gerenciador_vento)
    
    def _registrar_metricas(self):
        """Registra métricas da geração atual no histórico"""
        stats = self.populacao.get_estatisticas()
        media_fitness = self.fitness_func.calcular_media_geracao(self.populacao.individuos)
        stats["media_fitness"] = media_fitness
        self.historico.append(stats)
    
    def get_historico(self):
        """Retorna histórico de métricas de todas as gerações"""
        return self.historico
    
    def get_melhor_individuo(self):
        """Retorna melhor indivíduo encontrado até agora"""
        return self.melhor_global or self.populacao.melhor_individuo
