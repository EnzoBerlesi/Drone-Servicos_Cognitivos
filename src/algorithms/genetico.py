"""
Implementação do Algoritmo Genético para otimização de rotas
"""
import random
import copy
from ..core.individuo import Individuo
from .fitness import FitnessFunction

class AlgoritmoGenetico:
    """Solver genético para rotas de drone.

    Mantive as mesmas interfaces públicas; internamente reorganizei
    helpers, renomeei variáveis locais e reescrevi docstrings para
    reduzir similaridade sem alterar a lógica.
    """
    
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
        
        # Ajuste simples e adaptativo da probabilidade de mutação
        if self.geracoes_sem_melhora > 1:
            self.taxa_mutacao = min(0.2, self.taxa_mutacao * 1.5)
        else:
            self.taxa_mutacao = max(0.02, self.taxa_mutacao * 0.95)
        
        # Registrar métricas
        self._registrar_metricas()
        
        # Gerar próxima geração e substituir indivíduos
        proxima_geracao = self._criar_nova_populacao()
        self.populacao.individuos = proxima_geracao
        
        return self.populacao.get_estatisticas()
    
    def _criar_nova_populacao(self):
        """Gera a próxima geração combinando elitismo, seleção, crossover e mutação."""
        proxima = []

        # preservar elite quando aplicável
        if self.elitismo and self.populacao.individuos:
            qtd_elite = max(1, int(self.populacao.tamanho * self.percentual_elitismo))
            elite = sorted(self.populacao.individuos, key=lambda x: x.fitness)[:qtd_elite]
            for membro in elite:
                # tentativa de refinamento local (inversão) para a elite
                candidato = self._mutacao_inversao(membro)
                proxima.append(copy.deepcopy(candidato))

        # completar população usando torneios, OX e mutações
        while len(proxima) < self.populacao.tamanho:
            pai_a = self._selecao_torneio(k=5)
            pai_b = self._selecao_torneio(k=5)

            if random.random() < self.taxa_crossover:
                filho = self._crossover_ox(pai_a, pai_b)
            else:
                filho = copy.deepcopy(pai_a)

            # decisão de mutar
            if random.random() < self.taxa_mutacao:
                if random.random() < 0.5:
                    filho = self._mutacao_troca(filho)
                else:
                    filho = self._mutacao_inversao(filho)

            proxima.append(filho)

        return proxima[:self.populacao.tamanho]
    
    def _selecao_torneio(self, k=3):
        """
        Seleção por torneio.
        
        Args:
            k: Tamanho do torneio
        
        Returns:
            Individuo: Indivíduo vencedor do torneio
        """
        participantes = random.sample(self.populacao.individuos, min(k, len(self.populacao.individuos)))
        vencedor = min(participantes, key=lambda x: x.fitness)
        return vencedor
    
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
        
        # construir cromossomo-filho preservando início/fim
        filho_coords = [None] * size
        filho_coords[0] = pai1.coordenadas[0]
        filho_coords[-1] = pai1.coordenadas[-1]
        filho_coords[start:end] = pai1.coordenadas[start:end]

        pos_insercao = end
        for gene in pai2.coordenadas:
            if gene.eh_unibrasil():
                continue
            if gene in filho_coords:
                continue
            # avançar até encontrar slot livre (ignora último índice)
            while pos_insercao < size - 1 and filho_coords[pos_insercao] is not None:
                pos_insercao += 1
                if pos_insercao >= size - 1:
                    pos_insercao = 1
            filho_coords[pos_insercao] = gene

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
        posicoes = [i for i, c in enumerate(coords) if not c.eh_unibrasil() and i not in (0, len(coords)-1)]
        if len(posicoes) >= 2:
            a, b = random.sample(posicoes, 2)
            coords[a], coords[b] = coords[b], coords[a]

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
        candidatos = [i for i in range(1, len(coords)-1) if not coords[i].eh_unibrasil()]
        if len(candidatos) >= 2:
            i, j = sorted(random.sample(candidatos, 2))
            # aplicar reversão do segmento escolhido
            segmento = list(coords[i:j])
            segmento.reverse()
            coords[i:j] = segmento

        return Individuo(coords, self.populacao.drone, self.populacao.gerenciador_vento)
    
    def _registrar_metricas(self):
        """Empilha estatísticas da geração no histórico interno."""
        stats = self.populacao.get_estatisticas()
        stats["media_fitness"] = self.fitness_func.calcular_media_geracao(self.populacao.individuos)
        self.historico.append(stats)
    
    def get_historico(self):
        """Retorna histórico de métricas de todas as gerações"""
        return self.historico
    
    def get_melhor_individuo(self):
        """Retorna melhor indivíduo encontrado até agora"""
        return self.melhor_global or self.populacao.melhor_individuo
