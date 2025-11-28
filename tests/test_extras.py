"""Testes extras de funcionalidades"""
import pytest
from src.utils_custom.file_handlers import carregar_coordenadas
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento
from src.core.individuo import Individuo


def test_coordenadas_carregadas():
    """Testa que coordenadas são carregadas"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    assert len(coordenadas) > 0
    assert all(hasattr(c, 'cep') for c in coordenadas)


def test_vento_tem_7_dias():
    """Testa que vento tem previsão para 7 dias"""
    vento = GerenciadorVento()
    assert len(vento.previsao) == 7


def test_individuo_simula_rota_simples():
    """Testa simulação básica"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    rota = [coordenadas[0]] + coordenadas[1:5] + [coordenadas[0]]
    individuo = Individuo(rota, drone, vento)
    individuo.simular_rota()
    
    assert len(individuo.trechos) > 0
    assert individuo.distancia_total > 0
