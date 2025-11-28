"""Testes do Algoritmo Genético"""
from src.utils_custom.file_handlers import carregar_coordenadas
from src.algorithms.genetico import AlgoritmoGenetico
from src.core.populacao import Populacao
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento


def test_algoritmo_genetico_executa_geracoes():
    """Verifica que o GA executa múltiplas gerações"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    # População pequena para testes rápidos
    populacao = Populacao(coordenadas[:20], drone, vento, tamanho=10)
    algoritmo = AlgoritmoGenetico(populacao)
    
    # Executar 3 gerações
    for _ in range(3):
        stats = algoritmo.executar_geracao()
        assert 'melhor_fitness' in stats
        assert 'fitness_medio' in stats
    
    historico = algoritmo.get_historico()
    assert len(historico) == 3


def test_algoritmo_genetico_melhora_fitness():
    """Verifica que o fitness tende a melhorar (diminuir) ao longo das gerações"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    populacao = Populacao(coordenadas[:20], drone, vento, tamanho=15)
    algoritmo = AlgoritmoGenetico(populacao)
    
    # Executar 5 gerações
    for _ in range(5):
        algoritmo.executar_geracao()
    
    historico = algoritmo.get_historico()
    primeiro_fitness = historico[0]['melhor_fitness']
    ultimo_fitness = historico[-1]['melhor_fitness']
    
    # Fitness deve melhorar ou estabilizar (menor é melhor)
    assert ultimo_fitness <= primeiro_fitness * 1.1  # Tolerância de 10%


def test_melhor_individuo_eh_viavel():
    """Verifica que o melhor indivíduo encontrado é viável"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    populacao = Populacao(coordenadas[:15], drone, vento, tamanho=10)
    algoritmo = AlgoritmoGenetico(populacao)
    
    # Executar algumas gerações
    for _ in range(3):
        algoritmo.executar_geracao()
    
    melhor = algoritmo.get_melhor_individuo()
    assert melhor is not None
    assert melhor.viabilidade == True
    assert len(melhor.coordenadas) >= 2
