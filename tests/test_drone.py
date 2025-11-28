"""Testes das funcionalidades do Drone"""
from src.core.entities.drone import Drone
from src.core.settings import Config


def test_drone_velocidades_validas():
    """Verifica que todas as velocidades válidas são múltiplas de 4"""
    drone = Drone()
    velocidades = drone.get_velocidades_validas()
    
    assert len(velocidades) > 0
    assert all(v % 4 == 0 for v in velocidades)
    assert min(velocidades) == 36
    assert max(velocidades) == 96


def test_drone_autonomia_inversamente_proporcional():
    """Verifica que autonomia diminui com aumento de velocidade"""
    drone = Drone()
    
    autonomia_36 = drone.calcular_autonomia(36)
    autonomia_48 = drone.calcular_autonomia(48)
    autonomia_96 = drone.calcular_autonomia(96)
    
    # Quanto maior a velocidade, menor a autonomia
    assert autonomia_36 > autonomia_48 > autonomia_96


def test_drone_velocidade_invalida_levanta_erro():
    """Verifica que velocidades inválidas levantam ValueError"""
    drone = Drone()
    
    try:
        drone.calcular_autonomia(35)  # Não é múltiplo de 4
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass
    
    try:
        drone.calcular_autonomia(100)  # Acima do máximo
        assert False, "Deveria ter levantado ValueError"
    except ValueError:
        pass
