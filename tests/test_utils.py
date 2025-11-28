import pytest
from src.utils_custom.calculos import distancia_haversine, calcular_direcao

def test_haversine_zero():
    d = distancia_haversine(-25.0, -49.0, -25.0, -49.0)
    assert abs(d) < 1e-6

def test_haversine_known():
    # approximate distance between two close points
    d = distancia_haversine(-25.428, -49.273, -25.431, -49.260)
    assert d > 0 and d < 2.0

def test_bearing_range():
    b = calcular_direcao(-25.428, -49.273, -25.431, -49.260)
    assert 0 <= b < 360
