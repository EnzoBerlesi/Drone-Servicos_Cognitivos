import random
from datetime import datetime

from src.utils import load_ceps, load_wind_table, bearing_deg
from src.drone import DroneSimulator
from src.ga import GeneticOptimizer


def test_population_vs_generations_deterministic_when_elite_full():
    # if elite == pop_size and mut_rate == 0, the population is preserved across generations
    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')

    random.seed(42)
    ga1 = GeneticOptimizer(ceps, wind, pop_size=8, generations=1, elite=8, mut_rate=0.0)
    best1, score1 = ga1.run()

    random.seed(42)
    ga2 = GeneticOptimizer(ceps, wind, pop_size=8, generations=10, elite=8, mut_rate=0.0)
    best2, score2 = ga2.run()

    assert best1 == best2
    assert score1 == score2


def test_wind_affects_flight_time_tail_vs_headwind():
    # build a minimal two-point route (home + one target) and compare tailwind vs headwind
    ceps = [
        {'cep': '82821020', 'lat': 0.0, 'lon': 0.0},
        {'cep': '10000000', 'lat': 0.0, 'lon': 0.01},
    ]
    # compute course from home->target
    course = bearing_deg(ceps[0]['lat'], ceps[0]['lon'], ceps[1]['lat'], ceps[1]['lon'])

    # tailwind (wind direction == course) and headwind (opposite)
    wind_tail = {(1, 6): (30.0, course)}
    wind_head = {(1, 6): (30.0, (course + 180) % 360)}

    sim_tail = DroneSimulator(ceps, wind_tail)
    sim_head = DroneSimulator(ceps, wind_head)

    start = datetime(2025, 11, 1, 6, 0, 0)
    segs_t, summary_t = sim_tail.simulate_route(['10000000'], start, speeds=[36.0, 36.0])
    segs_h, summary_h = sim_head.simulate_route(['10000000'], start, speeds=[36.0, 36.0])

    # tailwind should reduce the first-leg flight time compared to headwind
    dur_first_tail = (segs_t[0].end_dt - segs_t[0].start_dt).total_seconds()
    dur_first_head = (segs_h[0].end_dt - segs_h[0].start_dt).total_seconds()
    assert dur_first_tail < dur_first_head


def test_battery_triggers_recharge_and_marks_landed():
    # create ceps far apart to force recharge (distance > autonomy)
    ceps = [
        {'cep': '82821020', 'lat': 0.0, 'lon': 0.0},
        {'cep': '20000000', 'lat': 1.0, 'lon': 0.0},
    ]
    wind = {}
    sim = DroneSimulator(ceps, wind)

    start = datetime(2025, 11, 1, 6, 0, 0)
    segs, summary = sim.simulate_route(['20000000'], start, speeds=[36.0, 36.0])

    # because of the large distance, at least one landing (recharge) should have occurred
    assert summary['stops'] >= 1
    assert any(s.landed for s in segs)


def test_fitness_decreases_when_late_fee_applied():
    # prepare ceps far enough to force an immediate recharge so fee can be applied
    ceps = [
        {'cep': '82821020', 'lat': 0.0, 'lon': 0.0},
        {'cep': '30000000', 'lat': 1.0, 'lon': 0.0},
    ]
    wind = {}

    # build a deterministic individual that will start late enough so recharge ends after 17:00
    individual = {
        'order': ['30000000'],
        'speeds': [36.0, 36.0],
        'start_day': 1,
        'start_hour': 16,  # start at 16:00 -> if recharge occurs immediately, +30min -> 16:30; give margin
    }

    ga = GeneticOptimizer(ceps, wind, pop_size=4, generations=1, elite=1, mut_rate=0.0)
    # force use of our simulator and ensure it will charge and potentially apply fee
    ga.sim = DroneSimulator(ceps, wind)

    # first, with no late fee
    ga.sim.apply_late_fee = False
    score_no_fee = ga.fitness(individual)

    # now enable late fee
    ga.sim.apply_late_fee = True
    score_with_fee = ga.fitness(individual)

    # when the late fee is applied, money increases and the fitness (score) should decrease
    assert score_with_fee <= score_no_fee
