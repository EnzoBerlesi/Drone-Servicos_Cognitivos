import os
from datetime import datetime
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
    start = datetime(2025,11,1,6,0,0)
    segs, summary = sim.simulate_route(best, start, speed_kmh=36.0)
    outdir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, 'flight_plan.csv')
    import csv
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['cep_ini','lat_ini','lon_ini','dia','hora_ini','vel','cep_fim','lat_fim','lon_fim','pouso','hora_fim'])
        for s in segs:
            w.writerow(s.to_csv_row())
    print('Wrote', outpath)

if __name__ == '__main__':
    main()
