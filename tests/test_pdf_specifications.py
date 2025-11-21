"""
Testes unitários para validar as correções implementadas conforme especificações do PDF.
Abrange: autonomia, vento, velocidades, custos de pouso e tabela de ventos.
"""
import pytest
import math
from datetime import datetime, timedelta
from src.utils import (
    get_autonomy_for_speed, 
    validate_speed, 
    get_valid_speeds,
    effective_speed_kmh,
    load_wind_table,
    NOMINAL_AUTONOMY_S,
    REF_SPEED_KMH,
    CURITIBA_FACTOR,
    MIN_SPEED_KMH,
    MAX_SPEED_KMH,
    SPEED_STEP
)
from src.drone import DroneSimulator
from src.utils import load_ceps


class TestAutonomiaFormula:
    """Testes para Item 1: Autonomia nominal com fórmula A(v) = 5000 × (36/v)² × 0.93"""
    
    def test_autonomia_constantes(self):
        """Verifica se as constantes estão corretas conforme PDF"""
        assert NOMINAL_AUTONOMY_S == 5000.0, "Autonomia nominal deve ser 5000s"
        assert REF_SPEED_KMH == 36.0, "Velocidade de referência deve ser 36 km/h"
        assert CURITIBA_FACTOR == 0.93, "Fator de Curitiba deve ser 0.93"
    
    def test_autonomia_velocidade_referencia(self):
        """Testa autonomia na velocidade de referência (36 km/h)"""
        autonomia = get_autonomy_for_speed(36.0)
        esperado = 5000.0 * (36.0 / 36.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        assert abs(autonomia - 4650.0) < 0.01, "A(36) deve ser 4650s"
    
    def test_autonomia_velocidade_maxima(self):
        """Testa autonomia na velocidade máxima (96 km/h)"""
        autonomia = get_autonomy_for_speed(96.0)
        esperado = 5000.0 * (36.0 / 96.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        # 5000 × (36/96)² × 0.93 = 5000 × 0.140625 × 0.93 = 653.90625
        assert abs(autonomia - 653.90625) < 0.1
    
    def test_autonomia_velocidade_intermediaria(self):
        """Testa autonomia em velocidade intermediária (60 km/h)"""
        autonomia = get_autonomy_for_speed(60.0)
        esperado = 5000.0 * (36.0 / 60.0) ** 2 * 0.93
        assert abs(autonomia - esperado) < 0.01
        # 5000 × (36/60)² × 0.93 = 5000 × 0.36 × 0.93 = 1674
        assert abs(autonomia - 1674.0) < 0.1
    
    def test_autonomia_formula_inversamente_proporcional(self):
        """Verifica que autonomia diminui quando velocidade aumenta"""
        a36 = get_autonomy_for_speed(36.0)
        a72 = get_autonomy_for_speed(72.0)
        a96 = get_autonomy_for_speed(96.0)
        
        assert a36 > a72 > a96, "Autonomia deve diminuir com aumento de velocidade"
    
    def test_autonomia_velocidade_invalida(self):
        """Testa comportamento com velocidade inválida"""
        autonomia = get_autonomy_for_speed(0)
        assert autonomia == 0, "Velocidade zero deve retornar autonomia zero"


class TestVentoVetorial:
    """Testes para Item 2: Cálculo vetorial de vento (soma de vetores)"""
    
    def test_vento_exemplo_pdf(self):
        """Valida cálculo vetorial com exemplo similar ao PDF"""
        # Drone a 36 km/h rumo NE (45°), vento de 15 km/h para Leste (90°)
        # Componentes drone: x=25.46, y=25.46
        # Componentes vento: x=15.0, y=0.0
        # Soma: x=40.46, y=25.46
        # Magnitude: sqrt(40.46² + 25.46²) = sqrt(1636.90 + 648.21) = sqrt(2285.11) ≈ 47.80
        v_efetiva = effective_speed_kmh(36.0, 15.0, 90.0, 45.0)
        esperado = 47.80
        assert abs(v_efetiva - esperado) < 0.1, f"Esperado ~{esperado}, obtido {v_efetiva}"
        # Validar que a soma vetorial aumenta a velocidade (vento favorável lateral)
        assert v_efetiva > 36.0, "Vento lateral favorável deve aumentar velocidade efetiva"
    
    def test_vento_tailwind_puro(self):
        """Testa vento de cauda puro (mesma direção)"""
        # Drone a 50 km/h, vento de 10 km/h, ambos para Norte (0°)
        v_efetiva = effective_speed_kmh(50.0, 10.0, 0.0, 0.0)
        assert abs(v_efetiva - 60.0) < 0.1, "Vento de cauda soma velocidades"
    
    def test_vento_headwind_puro(self):
        """Testa vento de frente puro (direções opostas)"""
        # Drone para Norte (0°) a 50 km/h, vento para Sul (180°) a 10 km/h
        v_efetiva = effective_speed_kmh(50.0, 10.0, 180.0, 0.0)
        assert abs(v_efetiva - 40.0) < 0.1, "Vento de frente subtrai velocidades"
    
    def test_vento_crosswind_puro(self):
        """Testa vento cruzado puro (perpendicular)"""
        # Drone para Norte (0°) a 40 km/h, vento para Leste (90°) a 30 km/h
        v_efetiva = effective_speed_kmh(40.0, 30.0, 90.0, 0.0)
        esperado = math.sqrt(40.0**2 + 30.0**2)  # Teorema de Pitágoras
        assert abs(v_efetiva - esperado) < 0.1, "Vento perpendicular usa Pitágoras"
        assert abs(v_efetiva - 50.0) < 0.1
    
    def test_vento_sem_vento(self):
        """Testa que sem vento, velocidade efetiva = velocidade do drone"""
        v_efetiva = effective_speed_kmh(60.0, 0.0, 0.0, 45.0)
        assert abs(v_efetiva - 60.0) < 0.1, "Sem vento, velocidade não muda"
    
    def test_vento_componentes_vetoriais(self):
        """Testa decomposição vetorial correta"""
        # Validar que componentes são calculadas corretamente
        drone_speed = 30.0
        wind_speed = 20.0
        wind_dir = 45.0  # NE
        course = 90.0    # Leste
        
        v_efetiva = effective_speed_kmh(drone_speed, wind_speed, wind_dir, course)
        
        # Componentes do drone (rumo Leste)
        v_drone_x = drone_speed * math.sin(math.radians(90.0))  # 30
        v_drone_y = drone_speed * math.cos(math.radians(90.0))  # 0
        
        # Componentes do vento (direção NE = 45°)
        v_wind_x = wind_speed * math.sin(math.radians(45.0))  # ~14.14
        v_wind_y = wind_speed * math.cos(math.radians(45.0))  # ~14.14
        
        # Soma vetorial
        v_x = v_drone_x + v_wind_x
        v_y = v_drone_y + v_wind_y
        esperado = math.sqrt(v_x**2 + v_y**2)
        
        assert abs(v_efetiva - esperado) < 0.1


class TestVelocidadesReguladas:
    """Testes para Item 3: Velocidades reguladas (36-96 km/h, múltiplos de 4)"""
    
    def test_velocidades_validas_lista(self):
        """Verifica lista de velocidades válidas"""
        velocidades = get_valid_speeds()
        esperadas = [36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96]
        assert velocidades == esperadas, f"Esperado {esperadas}, obtido {velocidades}"
        assert len(velocidades) == 16, "Deve haver 16 velocidades válidas"
    
    def test_velocidades_multiplos_de_4(self):
        """Verifica que todas são múltiplos de 4"""
        velocidades = get_valid_speeds()
        for v in velocidades:
            assert v % 4 == 0, f"Velocidade {v} deve ser múltiplo de 4"
    
    def test_velocidade_minima(self):
        """Testa validação de velocidade mínima (36 km/h)"""
        assert validate_speed(20.0) == 36.0, "Velocidade < 36 deve ser ajustada para 36"
        assert validate_speed(35.0) == 36.0
        assert validate_speed(36.0) == 36.0
    
    def test_velocidade_maxima(self):
        """Testa validação de velocidade máxima (96 km/h)"""
        assert validate_speed(100.0) == 96.0, "Velocidade > 96 deve ser ajustada para 96"
        assert validate_speed(120.0) == 96.0
        assert validate_speed(96.0) == 96.0
    
    def test_velocidade_arredondamento(self):
        """Testa arredondamento para múltiplo de 4 mais próximo"""
        assert validate_speed(37.0) == 36.0, "37 deve arredondar para 36"
        assert validate_speed(39.0) == 40.0, "39 deve arredondar para 40"
        assert validate_speed(42.0) == 40.0, "42 deve arredondar para 40"
        assert validate_speed(43.0) == 44.0, "43 deve arredondar para 44"
    
    def test_velocidades_intermediarias_validas(self):
        """Testa que velocidades válidas permanecem inalteradas"""
        for v in [36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96]:
            assert validate_speed(float(v)) == float(v), f"Velocidade válida {v} não deve mudar"
    
    def test_constantes_velocidade(self):
        """Verifica constantes de velocidade"""
        assert MIN_SPEED_KMH == 36.0, "Velocidade mínima deve ser 36 km/h (10 m/s)"
        assert MAX_SPEED_KMH == 96.0, "Velocidade máxima deve ser 96 km/h"
        assert SPEED_STEP == 4.0, "Incremento deve ser 4 km/h"


class TestCustosPouso:
    """Testes para Itens 4 e 5: Custos de pouso (R$80 + R$80 tardio)"""
    
    def test_custo_pouso_basico(self):
        """Testa que cada pouso custa R$80"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        # Criar rota que force um pouso (distância grande)
        start = datetime(2025, 11, 1, 6, 0, 0)
        # Pegar CEPs distantes para forçar recarga
        ceps_distantes = [c['cep'] for c in ceps if c['cep'] != '82821020'][:3]
        
        segs, summary = sim.simulate_route(ceps_distantes, start, speed_kmh=36.0)
        
        # Verificar que há custo monetário se houve pousos
        pousos = sum(1 for seg in segs if seg.landed)
        if pousos > 0:
            assert summary['money'] >= 80.0 * pousos, "Cada pouso deve custar pelo menos R$80"
    
    def test_late_fee_habilitado(self):
        """Verifica que apply_late_fee está True"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        assert sim.apply_late_fee == True, "apply_late_fee deve estar habilitado (True)"
    
    def test_custo_pouso_tardio(self):
        """Testa que pouso após 17:00 custa R$160 (R$80 base + R$80 tardio)"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        # Iniciar tarde no dia para forçar pouso após 17:00
        start = datetime(2025, 11, 1, 16, 0, 0)
        ceps_test = [c['cep'] for c in ceps if c['cep'] != '82821020'][:2]
        
        segs, summary = sim.simulate_route(ceps_test, start, speed_kmh=36.0)
        
        # Verificar se há pousos tardios
        pousos_tardios = sum(1 for seg in segs if seg.landed and seg.end_dt.hour >= 17)
        pousos_normais = sum(1 for seg in segs if seg.landed and seg.end_dt.hour < 17)
        
        if pousos_tardios > 0 or pousos_normais > 0:
            # Custo esperado: pousos normais × 80 + pousos tardios × 160
            custo_esperado_min = pousos_normais * 80 + pousos_tardios * 160
            assert summary['money'] >= custo_esperado_min, \
                f"Custo deve ser pelo menos R${custo_esperado_min} ({pousos_normais} normais, {pousos_tardios} tardios)"
    
    def test_sem_pouso_sem_custo(self):
        """Testa que sem pousos, custo é zero"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        # Rota muito curta que não requer recarga
        start = datetime(2025, 11, 1, 6, 0, 0)
        ceps_proximos = [c['cep'] for c in ceps if c['cep'] != '82821020'][:1]
        
        segs, summary = sim.simulate_route(ceps_proximos, start, speed_kmh=96.0)
        
        pousos = sum(1 for seg in segs if seg.landed)
        if pousos == 0:
            assert summary['money'] == 0.0, "Sem pousos, custo deve ser zero"


class TestTabelaVentos:
    """Testes para Item 7: Tabela de ventos conforme PDF"""
    
    def test_wind_table_carregamento(self):
        """Testa que wind_table.csv carrega corretamente"""
        wind = load_wind_table('data/wind_table.csv')
        assert isinstance(wind, dict), "Wind table deve ser dicionário"
        assert len(wind) > 0, "Wind table não deve estar vazia"
    
    def test_wind_table_dias_horas(self):
        """Verifica que há dados para 7 dias × 5 horários (06:00-18:00)"""
        wind = load_wind_table('data/wind_table.csv')
        
        # Horários conforme janela de voo: 6h, 9h, 12h, 15h, 18h
        # (21h está no PDF mas fora da janela operacional 06:00-19:00)
        horas_esperadas = [6, 9, 12, 15, 18]
        
        for dia in range(1, 8):  # 7 dias
            for hora in horas_esperadas:
                assert (dia, hora) in wind, f"Faltando dados para dia {dia}, hora {hora}"
    
    def test_wind_table_dia1_valores_pdf(self):
        """Valida valores específicos do Dia 1 conforme PDF"""
        wind = load_wind_table('data/wind_table.csv')
        
        # Dia 1: 17, 18, 30, 19, 20 km/h, direção E (90°)
        assert wind[(1, 6)] == (17.0, 90.0), "Dia 1, 6h: 17 km/h, 90°"
        assert wind[(1, 9)] == (18.0, 90.0), "Dia 1, 9h: 18 km/h, 90°"
        assert wind[(1, 12)] == (30.0, 90.0), "Dia 1, 12h: 30 km/h, 90°"
        assert wind[(1, 15)] == (19.0, 90.0), "Dia 1, 15h: 19 km/h, 90°"
        assert wind[(1, 18)] == (20.0, 90.0), "Dia 1, 18h: 20 km/h, 90°"
    
    def test_wind_table_dia5_valores_pdf(self):
        """Valida valores específicos do Dia 5 conforme PDF (ventos variados)"""
        wind = load_wind_table('data/wind_table.csv')
        
        # Dia 5: ventos variados em direção e intensidade
        assert wind[(5, 6)] == (3.0, 247.5), "Dia 5, 6h: 3 km/h, WSW (247.5°)"
        assert wind[(5, 9)] == (3.0, 202.5), "Dia 5, 9h: 3 km/h, SSW (202.5°)"
        assert wind[(5, 12)] == (10.0, 90.0), "Dia 5, 12h: 10 km/h, E (90°)"
        assert wind[(5, 15)] == (10.0, 67.5), "Dia 5, 15h: 10 km/h, ENE (67.5°)"
        assert wind[(5, 18)] == (21.0, 90.0), "Dia 5, 18h: 21 km/h, E (90°)"
    
    def test_wind_table_dia6_pico_velocidade(self):
        """Valida pico de velocidade do Dia 6 (28 km/h às 18h)"""
        wind = load_wind_table('data/wind_table.csv')
        
        assert wind[(6, 18)] == (28.0, 90.0), "Dia 6, 18h: pico de 28 km/h, E (90°)"
    
    def test_wind_table_direcoes_cardinais(self):
        """Verifica que direções são válidas (0-360°)"""
        wind = load_wind_table('data/wind_table.csv')
        
        for (dia, hora), (velocidade, direcao) in wind.items():
            assert 0 <= direcao < 360, f"Direção inválida: {direcao}° (dia {dia}, hora {hora})"
            assert velocidade >= 0, f"Velocidade negativa: {velocidade} (dia {dia}, hora {hora})"
    
    def test_wind_table_total_registros(self):
        """Verifica total de 35 registros (7 dias × 5 horários operacionais)"""
        wind = load_wind_table('data/wind_table.csv')
        assert len(wind) == 35, f"Deve haver 35 registros (7×5), encontrados {len(wind)}"


class TestIntegracaoCompleta:
    """Testes de integração verificando múltiplas correções juntas"""
    
    def test_simulacao_com_todas_correcoes(self):
        """Testa simulação completa usando todas as correções implementadas"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        start = datetime(2025, 11, 1, 6, 0, 0)
        order = [c['cep'] for c in ceps if c['cep'] != '82821020'][:5]
        
        segs, summary = sim.simulate_route(order, start, speed_kmh=60.0)
        
        # Verificações básicas
        assert summary['valid'] in [True, False], "Deve ter status de validade"
        assert summary['total_time_s'] >= 0, "Tempo total deve ser não-negativo"
        assert summary['money'] >= 0, "Custo monetário deve ser não-negativo"
        assert isinstance(segs, list), "Segmentos devem ser lista"
        
        # Se houve pousos, deve haver custo
        pousos = sum(1 for seg in segs if seg.landed)
        if pousos > 0:
            assert summary['money'] >= 80.0, "Com pousos, deve haver custo mínimo de R$80"
    
    def test_velocidades_em_segmentos(self):
        """Verifica que velocidades nos segmentos são válidas"""
        ceps = load_ceps('data/ceps.csv')
        wind = load_wind_table('data/wind_table.csv')
        sim = DroneSimulator(ceps, wind)
        
        start = datetime(2025, 11, 1, 6, 0, 0)
        order = [c['cep'] for c in ceps if c['cep'] != '82821020'][:3]
        
        # Testar com diferentes velocidades
        for velocidade in [36, 60, 96]:
            segs, summary = sim.simulate_route(order, start, speed_kmh=velocidade)
            
            for seg in segs:
                assert seg.speed_set_kmh in get_valid_speeds(), \
                    f"Velocidade {seg.speed_set_kmh} não está na lista de válidas"
    
    def test_autonomia_com_velocidade_variavel(self):
        """Testa que autonomia é calculada corretamente com diferentes velocidades"""
        # Velocidade baixa = mais autonomia
        autonomia_36 = get_autonomy_for_speed(36.0)
        # Velocidade alta = menos autonomia
        autonomia_96 = get_autonomy_for_speed(96.0)
        
        # A autonomia deve ser significativamente maior em velocidade baixa
        razao = autonomia_36 / autonomia_96
        # (36/96)² = 0.140625, então razão ≈ 1/0.140625 ≈ 7.11
        assert razao > 7.0 and razao < 7.2, \
            f"Razão de autonomia 36/96 deve ser ~7.11, obtido {razao}"
