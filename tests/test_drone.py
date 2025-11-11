from src.utils import load_ceps, load_wind_table
from src.drone import DroneSimulator
from datetime import datetime

def test_simulation_basic():
    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    sim = DroneSimulator(ceps, wind)
    start = datetime(2025,11,1,6,0,0)
    order = [c['cep'] for c in ceps if c['cep'] != '82821020']
    segs, summary = sim.simulate_route(order, start)
    assert isinstance(segs, list)
    assert 'valid' in summary
