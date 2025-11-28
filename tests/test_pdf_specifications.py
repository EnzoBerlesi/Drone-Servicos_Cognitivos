"""
Testes unitários para validar especificações do PDF.
Abrange: autonomia, vento, velocidades, custos de pouso.
"""
import pytest
import math
from datetime import datetime
from src.core.entities.drone import Drone
from src.core.entities.vento import GerenciadorVento
from src.core.settings import Config
from src.utils_custom.calculos import calcular_velocidade_efetiva, distancia_haversine


class TestAutonomiaFormula:
    """Testes para Item 1: Autonomia nominal com fórmula A(v) = 5000 × (36/v)² × 0.93"""
    
    def test_autonomia_constantes(self):
        """Verifica se as constantes estão corretas conforme PDF"""
        assert Config.AUTONOMIA_REFERENCIA == 5000.0
        assert Config.VELOCIDADE_REFERENCIA == 36.0
        assert Config.FATOR_CORRECAO == 0.93
    
    def test_autonomia_velocidade_referencia(self):
        """Testa autonomia na velocidade de referência (36 km/h)"""
        drone = Drone()
        autonomia = drone.calcular_autonomia(36.0)
        esperado = 5000.0 * (36.0 / 36.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        assert abs(autonomia - 4650.0) < 0.01
    
    def test_autonomia_velocidade_maxima(self):
        """Testa autonomia na velocidade máxima (96 km/h)"""
        drone = Drone()
        autonomia = drone.calcular_autonomia(96.0)
        esperado = 5000.0 * (36.0 / 96.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        assert abs(autonomia - 653.90625) < 0.1
    
    def test_autonomia_velocidade_intermediaria(self):
        """Testa autonomia em velocidade intermediária (60 km/h)"""
        drone = Drone()
        autonomia = drone.calcular_autonomia(60.0)
        esperado = 5000.0 * (36.0 / 60.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        assert abs(autonomia - 1674.0) < 0.1
    
    def test_autonomia_formula_inversamente_proporcional(self):
        """Verifica que autonomia diminui quando velocidade aumenta"""
        drone = Drone()
        a36 = drone.calcular_autonomia(36.0)
        a72 = drone.calcular_autonomia(72.0)
        a96 = drone.calcular_autonomia(96.0)
        
        assert a36 > a72 > a96
    
    def test_autonomia_velocidade_invalida(self):
        """Testa comportamento com velocidade inválida"""
        drone = Drone()
        with pytest.raises(ValueError):
            drone.calcular_autonomia(35)  # Não múltiplo de 4


class TestVentoVetorial:
    """Testes para cálculo vetorial de vento"""
    
    def test_vento_exemplo_pdf(self):
        """Valida cálculo vetorial"""
        v_efetiva = calcular_velocidade_efetiva(36.0, 15.0, 90.0, 45.0)
        assert v_efetiva > 36.0
    
    def test_vento_tailwind_puro(self):
        """Testa vento de cauda"""
        # velocidade_drone, direcao_voo, vento_vel, vento_dir
        v_efetiva = calcular_velocidade_efetiva(50.0, 0.0, 10.0, 0.0)
        # Vento na mesma direção deve somar
        assert v_efetiva > 50.0
    
    def test_vento_headwind_puro(self):
        """Testa vento de frente"""
        # velocidade_drone, direcao_voo, vento_vel, vento_dir
        v_efetiva = calcular_velocidade_efetiva(50.0, 0.0, 10.0, 180.0)
        # Vento contrário deve reduzir velocidade
        assert v_efetiva < 50.0
    
    def test_vento_crosswind_puro(self):
        """Testa vento cruzado"""
        # velocidade_drone, direcao_voo, vento_vel, vento_dir
        v_efetiva = calcular_velocidade_efetiva(40.0, 0.0, 30.0, 90.0)
        # Vento perpendicular aumenta velocidade resultante
        assert v_efetiva > 40.0
    
    def test_vento_sem_vento(self):
        """Testa sem vento"""
        v_efetiva = calcular_velocidade_efetiva(60.0, 0.0, 0.0, 45.0)
        assert abs(v_efetiva - 60.0) < 0.1
    
    def test_vento_componentes_vetoriais(self):
        """Testa decomposição vetorial"""
        v_efetiva = calcular_velocidade_efetiva(30.0, 20.0, 45.0, 90.0)
        assert v_efetiva > 0


class TestVelocidades:
    """Testes para Item 3: Velocidades válidas (36-96 km/h, passo de 4)"""
    
    def test_velocidades_validas_range(self):
        """Verifica range de velocidades"""
        drone = Drone()
        velocidades = drone.get_velocidades_validas()
        assert min(velocidades) == 36
        assert max(velocidades) == 96
    
    def test_velocidades_multiplos_de_4(self):
        """Verifica que todas são múltiplas de 4"""
        drone = Drone()
        velocidades = drone.get_velocidades_validas()
        assert all(v % 4 == 0 for v in velocidades)
    
    def test_velocidade_invalida_rejeita(self):
        """Testa que velocidades inválidas são rejeitadas"""
        drone = Drone()
        assert not drone.velocidade_valida(35)
        assert not drone.velocidade_valida(37)
        assert not drone.velocidade_valida(100)


class TestCustoPouso:
    """Testes para Item 4: Custos de pouso (R$80 base + R$80 após 18:00)"""
    
    def test_custo_base_recarga(self):
        """Verifica custo base de recarga"""
        assert Config.CUSTO_RECARGA == 80.0
    
    def test_taxa_tarde_valor(self):
        """Verifica taxa adicional tardia"""
        assert Config.TAXA_TARDE == 80.0
    
    def test_hora_limite_taxa(self):
        """Verifica hora limite para taxa"""
        assert Config.HORA_LIMITE_TAXA == 1080  # 18:00 em minutos


class TestTabelaVentos:
    """Testes para Item 5: Tabela de ventos (7 dias × 6 horários)"""
    
    def test_tabela_vento_7_dias(self):
        """Verifica que há previsão para 7 dias"""
        vento = GerenciadorVento()
        assert len(vento.previsao) == 7
    
    def test_tabela_vento_6_horarios(self):
        """Verifica 6 horários por dia"""
        vento = GerenciadorVento()
        for dia in range(1, 8):
            assert len(vento.previsao[dia]) == 6
    
    def test_vento_interpolacao_funciona(self):
        """Verifica que interpolação retorna valores válidos"""
        vento = GerenciadorVento()
        info = vento.get_vento(1, 420)  # Dia 1, 07:00
        assert info['velocidade'] >= 0
        assert 0 <= info['angulo'] < 360
