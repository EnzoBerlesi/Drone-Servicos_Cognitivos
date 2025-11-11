from src.utils import load_ceps, load_wind_table
from src.ga import GeneticOptimizer

def test_ga_returns_sequence():
    ceps = load_ceps('data/ceps.csv')
    wind = load_wind_table('data/wind_table.csv')
    ga = GeneticOptimizer(ceps, wind, pop_size=10, generations=10, elite=1, mut_rate=0.2)
    best, score = ga.run()
    # best is now a dict containing order, speeds, start_day and start_hour
    assert isinstance(best, dict)
    ceplist = [c['cep'] for c in ceps if c['cep'] != '82821020']
    assert set(best['order']) == set(ceplist)
    # speeds length should equal legs (n+1)
    assert len(best['speeds']) == len(ceplist) + 1
    assert 1 <= best['start_day'] <= 7
    assert 6 <= best['start_hour'] <= 19
