import os
from datetime import datetime, timedelta
from .utils import load_ceps, load_wind_table
from .ga import GeneticOptimizer

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DATA_DIR = os.path.abspath(DATA_DIR)

def main():
    ceps = load_ceps(os.path.join(DATA_DIR, 'ceps.csv'))
    wind = load_wind_table(os.path.join(DATA_DIR, 'wind_table.csv'))
    ga = GeneticOptimizer(ceps, wind, pop_size=40, generations=100, elite=2, mut_rate=0.15)
    best, score = ga.run()
    print('Best sequence score', score)
    # simulate and write CSV
    sim = ga.sim
    start = datetime(2025, 11, 1, best['start_hour'], 0, 0) + timedelta(days=best['start_day'] - 1)
    segs, summary = sim.simulate_route(best['order'], start, speeds=best['speeds'])
    outdir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, 'flight_plan.csv')
    import csv
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        # Header exactly as specified in the enunciado
        w.writerow([
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
        ])
        for s in segs:
            w.writerow(s.to_csv_row())
    print('Wrote', outpath)

if __name__ == '__main__':
    main()
