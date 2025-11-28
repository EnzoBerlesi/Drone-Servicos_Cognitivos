"""
Ponto de entrada principal do sistema de otimização de rotas de drone
"""
import os
import sys
import random

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils_custom.file_handlers import carregar_coordenadas
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento
from src.core.populacao import Populacao
from src.algorithms.genetico import AlgoritmoGenetico
from src.simulation.csv_exporter import CSVExporter
from src.utils_custom.calculos import distancia_haversine

def calcular_distancia_total(coordenadas):
    """Calcula distância total de uma rota"""
    return sum(
        distancia_haversine(
            coordenadas[i].latitude, coordenadas[i].longitude,
            coordenadas[i+1].latitude, coordenadas[i+1].longitude
        )
        for i in range(len(coordenadas) - 1)
    )

def aplicar_2opt(coordenadas, max_iter=1000):
    """Aplica otimização 2-opt à rota"""
    n = len(coordenadas)
    if n < 4:
        return coordenadas
    
    improved = True
    it = 0
    
    while improved and it < max_iter:
        improved = False
        it += 1
        
        if it % 100 == 0:
            print(f"      2-opt: iteracao {it}/{max_iter} ({it*100//max_iter}%)")
        
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                a, b = coordenadas[i - 1], coordenadas[i]
                c, d = coordenadas[j], coordenadas[j + 1]
                
                delta = (
                    distancia_haversine(a.latitude, a.longitude, c.latitude, c.longitude) +
                    distancia_haversine(b.latitude, b.longitude, d.latitude, d.longitude) -
                    distancia_haversine(a.latitude, a.longitude, b.latitude, b.longitude) -
                    distancia_haversine(c.latitude, c.longitude, d.latitude, d.longitude)
                )
                
                if delta < -1e-6:
                    # Reverter segmento
                    coordenadas[i:j+1] = list(reversed(coordenadas[i:j+1]))
                    improved = True
                    break
            
            if improved:
                break
    
    print(f"      2-opt: iteracao {it}/{max_iter} (100%)")
    return coordenadas

def main():
    """Função principal que executa a otimização"""
    print("=" * 70)
    print("SISTEMA DE OTIMIZACAO DE ROTAS DE DRONE - UNIBRASIL SURVEYOR")
    print("=" * 70)
    
    # Configurações - usar caminho absoluto baseado na raiz do projeto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ARQUIVO_COORDENADAS = os.path.join(BASE_DIR, "data", "coordenadas.csv")
    TAMANHO_POPULACAO = 50
    NUMERO_GERACOES = 10
    
    # Carregar dados
    print(f"\nCarregando coordenadas...")
    coordenadas = carregar_coordenadas(ARQUIVO_COORDENADAS)
    
    if not coordenadas:
        print("ERRO: Nenhuma coordenada foi carregada.")
        return
    
    # Inicializar componentes
    print("\nInicializando componentes do sistema...")
    drone = Drone()
    vento = GerenciadorVento()
    populacao = Populacao(coordenadas, drone, vento, TAMANHO_POPULACAO)
    algoritmo = AlgoritmoGenetico(populacao, taxa_mutacao=0.02, taxa_crossover=0.8)
    exporter = CSVExporter()
    
    print(f"OK Drone configurado (autonomia padrao: {drone.calcular_autonomia(36)/60:.1f} min)")
    print(f"OK {len(coordenadas)} coordenadas carregadas")
    print(f"OK Populacao inicial: {TAMANHO_POPULACAO} individuos")
    
    # Executar algoritmo genético
    print(f"\nExecutando Algoritmo Genetico...")
    print(f"Parametros: {NUMERO_GERACOES} geracoes | Elite: 10% | Mutacao adaptativa")
    print("=" * 70)
    
    for geracao in range(NUMERO_GERACOES):
        stats = algoritmo.executar_geracao()
        
        # Mostrar progresso de cada geração
        print(f"Geracao {geracao + 1:3d}/{NUMERO_GERACOES} | "
              f"Melhor fitness: {stats.get('melhor_fitness', float('inf')):.2f} | "
              f"Viaveis: {stats.get('individuos_viaveis', 0)}/{stats.get('tamanho', 0)}")
    
    # Obter melhor solução
    print("\n" + "=" * 70)
    print("RESULTADOS FINAIS")
    print("=" * 70)
    
    melhor = algoritmo.get_melhor_individuo()
    historico = algoritmo.get_historico()
    
    if melhor is None:
        print("ERRO: Nenhuma solucao viavel foi encontrada.")
        return
    
    # Aplicar otimização 2-opt local ao melhor indivíduo
    print("\nAplicando otimizacao 2-opt local (limitada a 1000 iteracoes)...")
    print(f"   Otimizando rota com {len(melhor.coordenadas)} pontos...")
    print(f"   Distancia antes: {calcular_distancia_total(melhor.coordenadas):.2f} km")
    
    try:
        melhor.coordenadas = aplicar_2opt(melhor.coordenadas, max_iter=1000)
        # Revalidar viabilidade
        melhor.viabilidade = True
        melhor.penalidades = 0
        melhor.validar_estrutura()
        print(f"   Distancia depois: {calcular_distancia_total(melhor.coordenadas):.2f} km")
        print("   2-opt concluido")
    except Exception as e:
        print(f"   Erro ao aplicar 2-opt: {e}")
    
    # Simular rota final (se ainda não foi simulada)
    print("\nSimulando rota otimizada...")
    melhor.simular_rota(verbose=False)
    melhor.calcular_fitness()
    
    # Exibir resultados
    print(f"\nOK Solucao encontrada:")
    print(f"   - Fitness: {melhor.fitness:.2f}")
    print(f"   - Viavel: {'SIM' if melhor.viabilidade else 'NAO'}")
    print(f"   - Distancia total: {melhor.distancia_total:.2f} km")
    print(f"   - Tempo total (voo): {melhor.tempo_total:.2f} min")

    # Tempo total da missão (inclui pausas/recargas/dormidas)
    minutos_missao = getattr(melhor, 'minutos_totais_desde_inicio', None)
    if minutos_missao is None:
        num_recargas = len(getattr(melhor, 'lista_recargas', []))
        tempo_recargas_min = num_recargas * getattr(Config, 'TEMPO_RECARGA', 0)
        num_trechos = len(getattr(melhor, 'trechos', []))
        tempo_parada_min = (num_trechos * getattr(Config, 'TEMPO_PARADA', 0)) / 60.0
        minutos_missao = melhor.tempo_total + tempo_recargas_min + tempo_parada_min

    print(f"   - Tempo total missão (min): {float(minutos_missao):.2f}")
    print(f"   - Dias utilizados: {melhor.dias_utilizados}")
    print(f"   - Pousos para recarga: {melhor.numero_pousos}")
    print(f"   - Custo total: R$ {melhor.custo_total:.2f}")
    print(f"   - Coordenadas visitadas: {len(melhor.coordenadas)}")
    
    # Exportar resultados
    print(f"\nExportando resultados...")
    exporter.exportar_rota_completa(melhor)
    exporter.exportar_resumo(melhor, historico)
    exporter.gerar_mapa_rota(melhor)
    
    print("\n" + "=" * 70)
    print("EXECUCAO CONCLUIDA COM SUCESSO!")
    print("=" * 70)

if __name__ == '__main__':
    main()
