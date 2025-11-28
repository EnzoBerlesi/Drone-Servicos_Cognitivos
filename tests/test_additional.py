"""Testes adicionais de funcionalidades específicas"""
from src.utils_custom.file_handlers import carregar_coordenadas
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento
from src.core.individuo import Individuo


def test_drone_autonomia_calculo():
    """Verifica se a autonomia é calculada corretamente"""
    drone = Drone()
    autonomia_36 = drone.calcular_autonomia(36)
    autonomia_72 = drone.calcular_autonomia(72)
    
    # Velocidade menor = autonomia maior
    assert autonomia_36 > autonomia_72
    # Autonomia a 36 km/h deve ser aproximadamente 4650s (5000 * 0.93)
    assert 4600 < autonomia_36 < 4700


def test_coordenadas_unicas_exceto_unibrasil():
    """Verifica que não há duplicação de coordenadas (exceto Unibrasil)"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    # Criar rota válida: Unibrasil -> coordenadas -> Unibrasil
    rota = [coordenadas[0]] + coordenadas[1:10] + [coordenadas[0]]
    individuo = Individuo(rota, drone, vento)
    
    assert individuo.viabilidade == True


def test_individuo_requer_inicio_e_fim_unibrasil():
    """Verifica que rotas devem começar e terminar no Unibrasil"""
    coordenadas = carregar_coordenadas('data/coordenadas.csv')
    drone = Drone()
    vento = GerenciadorVento()
    
    # Rota inválida: não começa no Unibrasil
    rota_invalida = coordenadas[1:10]
    individuo = Individuo(rota_invalida, drone, vento)
    
    assert individuo.viabilidade == False
    assert individuo.penalidades > 0
