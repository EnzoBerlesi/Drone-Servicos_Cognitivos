import os
from datetime import datetime

from src.utils import load_ceps, load_wind_table
from src.ga import GeneticOptimizer
from src.drone import DroneSimulator


def test_csv_header_in_main_matches_enunciado():
    # Ensure the header written by src/main.py contains the exact labels required
    import inspect
    import src.main as main_mod
    src = inspect.getsource(main_mod)
    expected = [
        'CEP inicial',
        'Latitude inicial',
        'Longitude inicial',
        'Dia do voo',
        'Hora inicial',
        'Velocidade',
        'CEP final',
        'Latitude final',
        'Longitude final',
        'Pouso',
        'Hora final'
    ]
    # check that each expected label appears in the source file (robust against formatting)
    for label in expected:
        assert label in src


def test_speeds_are_quantized_in_initial_population():
    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    ga = GeneticOptimizer(ceps, wind, pop_size=10, generations=1)
    pop = ga.initial_population()
    for ind in pop:
        for s in ind['speeds']:
            assert 4 <= s <= 96
            assert s % 4 == 0


def test_matricula_min_speed_and_rounding():
    # create two simple points to test behavior
    ceps = [
        {'cep': '82821020', 'lat': 0.0, 'lon': 0.0},
        {'cep': '90000000', 'lat': 0.0, 'lon': 0.01},
    ]
    wind = {}

    # simulator without matricula rules
    sim_plain = DroneSimulator(ceps, wind, matricula='1XYZ')
    start = datetime(2025, 11, 1, 6, 0, 0)
    segs_plain, summary_plain = sim_plain.simulate_route(['90000000'], start, speeds=[20.0, 20.0])

    # simulator with matricula rules (starts with '2')
    sim_mat = DroneSimulator(ceps, wind, matricula='2ABC')
    segs_mat, summary_mat = sim_mat.simulate_route(['90000000'], start, speeds=[20.0, 20.0])

    # when matricula rules apply, recorded set speed should be at least 36.0
    assert segs_mat[0].speed_set_kmh >= 36.0

    # flight durations: with matricula rules, duration must be integral number of seconds
    dur_plain = (segs_plain[0].end_dt - segs_plain[0].start_dt).total_seconds()
    dur_mat = (segs_mat[0].end_dt - segs_mat[0].start_dt).total_seconds()
    assert abs(dur_mat - round(dur_mat)) < 1e-6
    # plain simulation may produce non-integer seconds (fractional)
    assert abs(dur_plain - round(dur_plain)) > 1e-6 or dur_plain != dur_mat


def test_fitness_penalizes_money(monkeypatch):
    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    ga = GeneticOptimizer(ceps, wind, pop_size=4, generations=1)

    # create a dummy individual
    ind = ga.initial_population()[0]

    # monkeypatch simulate_route to return same time/stops but different money
    def sim_no_money(order, start, speeds=None):
        return [], {'valid': True, 'total_time_s': 1000.0, 'money': 0.0, 'stops': 0}

    def sim_with_money(order, start, speeds=None):
        return [], {'valid': True, 'total_time_s': 1000.0, 'money': 80.0, 'stops': 0}

    monkeypatch.setattr(ga, 'sim', ga.sim)
    monkeypatch.setattr(ga.sim, 'simulate_route', sim_no_money)
    s0 = ga.fitness(ind)
    monkeypatch.setattr(ga.sim, 'simulate_route', sim_with_money)
    s1 = ga.fitness(ind)

    assert s1 < s0
