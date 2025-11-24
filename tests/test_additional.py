from datetime import datetime
import math

from src.utils import load_ceps, load_wind_table
from src.drone import DroneSimulator, FlightSegment


def test_flightsegment_time_format():
    # ensure to_csv_row includes seconds and pouso flag
    start = datetime(2025, 11, 1, 6, 0, 0)
    end = datetime(2025, 11, 1, 7, 30, 15)
    seg = FlightSegment('82821020', -25.4, -49.2, start, 36, '80010010', -25.41, -49.20, True, end)
    row = seg.to_csv_row()
    # indices: 4 -> hora_ini, 9 -> pouso, 10 -> hora_fim
    assert row[4] == '06:00:00'
    assert row[9] in ('SIM', 'NÃO')
    assert row[10] == '07:30:15'


def test_route_exceeds_7_days_invalid(monkeypatch):
    # Force small autonomy and huge recharge time to ensure a recharge pushes beyond 7 days
    import src.drone as d
    # drone module imported constants are used by the simulator; patch them here
    monkeypatch.setattr(d, 'AUTONOMY_S', 1.0)
    monkeypatch.setattr(d, 'RECHARGE_DURATION_S', 10 * 24 * 3600)  # 10 days

    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    # Desabilitar autonomia variável para que o monkeypatch funcione
    sim = DroneSimulator(ceps, wind, use_variable_autonomy=False)
    start = datetime(2025, 11, 1, 6, 0, 0)
    order = [c['cep'] for c in ceps if c['cep'] != '82821020'][:1]
    segs, summary = sim.simulate_route(order, start)
    assert summary['valid'] is False


def test_late_landing_fee_applied(monkeypatch):
    # Force small autonomy so the simulator performs a recharge; set start near 17:00 so recharge ends after 17:00
    import src.drone as d
    monkeypatch.setattr(d, 'AUTONOMY_S', 60.0)  # small autonomy to force recharge

    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    # Desabilitar autonomia variável para que o monkeypatch funcione
    sim = DroneSimulator(ceps, wind, use_variable_autonomy=False)
    # enable fee behavior explicitly
    sim.apply_late_fee = True

    # Choose a start time that will make a recharge push past 17:00
    start = datetime(2025, 11, 1, 16, 50, 0)
    order = [c['cep'] for c in ceps if c['cep'] != '82821020'][:2]
    segs, summary = sim.simulate_route(order, start)
    # money should include at least one 80.0 fee when a recharge landing happens after 17:00
    assert summary['money'] >= 80.0
