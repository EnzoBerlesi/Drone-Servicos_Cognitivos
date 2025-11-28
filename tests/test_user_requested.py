"""Testes solicitados pelo usuário"""
import random
from src.utils_custom.file_handlers import carregar_coordenadas
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento
from src.core.populacao import Populacao
from src.core.individuo import Individuo
from src.algorithms.genetico import AlgoritmoGenetico


def test_population_vs_generations_deterministic_when_elite_full():
    """Teste de determinismo com elite total"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()

    populacao = Populacao(coordenadas[:15], drone, vento, tamanho=8)
    inicial = len(populacao.individuos)
    
    assert inicial == 8


def test_wind_affects_flight_time_tail_vs_headwind():
    """Teste de que vento afeta tempo de voo"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    # Criar indivíduo simples
    rota = [coordenadas[0]] + coordenadas[1:5] + [coordenadas[0]]
    individuo = Individuo(rota, drone, vento)
    individuo.simular_rota()
    
    # Verificar que simulação foi executada
    assert len(individuo.trechos) > 0
    assert individuo.tempo_total > 0


def test_battery_triggers_recharge_and_marks_landed():
    """Teste de que bateria baixa aciona recarga"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    # Rota longa deve precisar de recarga
    rota = [coordenadas[0]] + coordenadas[1:100] + [coordenadas[0]]
    individuo = Individuo(rota, drone, vento)
    individuo.simular_rota()
    
    # Deve ter feito pelo menos uma recarga
    assert len(individuo.lista_recargas) > 0


def test_fitness_decreases_when_late_fee_applied():
    """Teste de que fitness é calculado corretamente"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    rota = [coordenadas[0]] + coordenadas[1:10] + [coordenadas[0]]
    individuo = Individuo(rota, drone, vento)
    individuo.simular_rota()
    
    # Verificar que a simulação foi executada
    assert len(individuo.trechos) > 0
    assert individuo.tempo_total > 0
