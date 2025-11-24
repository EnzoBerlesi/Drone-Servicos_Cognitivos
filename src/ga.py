import random
import math
from copy import deepcopy
from .drone import DroneSimulator
from .utils import load_wind_table, load_ceps, AUTONOMY_S, get_valid_speeds
from datetime import datetime, timedelta

class GeneticOptimizer:
    def __init__(self, ceps, wind_table, pop_size=50, generations=200, elite=2, mut_rate=0.2, matricula: str = None):
        self.ceps = ceps
        self.wind = wind_table
        self.pop_size = pop_size
        self.generations = generations
        self.elite = elite
        self.mut_rate = mut_rate
        self.matricula = matricula or ''
        self.sim = DroneSimulator(ceps, wind_table, matricula=self.matricula)

    def initial_population(self):
        # individuals are permutations of intermediate ceps (exclude home)
        ceplist = [c['cep'] for c in self.ceps if c['cep'] != '82821020']
        n = len(ceplist)
        legs = n + 1  # number of legs including return to home
        pop = []
        for _ in range(self.pop_size):
            seq = ceplist[:]
            random.shuffle(seq)
            # speeds per leg: múltiplos de 4 entre 36 e 96 km/h (conforme PDF)
            # Velocidades válidas: 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96
            valid_speeds = get_valid_speeds()
            speeds = [random.choice(valid_speeds) for _ in range(legs)]
            # start day/hour (day 1..7, hour 6..19)
            start_day = random.randint(1, 7)
            start_hour = random.randint(6, 19)
            pop.append({'order': seq, 'speeds': speeds, 'start_day': start_day, 'start_hour': start_hour})
        return pop

    def fitness(self, individual):
        # build start datetime from individual's start_day/start_hour
        start = datetime(2025, 11, 1, individual['start_hour'], 0, 0) + (individual['start_day'] - 1) * (datetime(2025,11,2,0,0,0) - datetime(2025,11,1,0,0,0))
        # simpler: anchor day offset
        start = datetime(2025,11,1, individual['start_hour'], 0, 0) + (individual['start_day'] - 1) * timedelta(days=1)
        segs, summary = self.sim.simulate_route(individual['order'], start, speeds=individual['speeds'])
        if not summary['valid']:
            return 1e-9
        # objective: minimize total_time and stops. Combine as weighted sum
        score = 1.0 / (1.0 + summary['total_time_s'] + summary['stops'] * 3600.0 + summary['money']*100.0)
        return score

    def select(self, pop, scores):
        # tournament selection (works with dict individuals)
        selected = []
        for _ in range(len(pop)):
            a, b = random.sample(range(len(pop)), 2)
            selected.append(deepcopy(pop[a]) if scores[a] > scores[b] else deepcopy(pop[b]))
        return selected

    def crossover(self, p1, p2):
        # parents are dicts with 'order', 'speeds', 'start_day', 'start_hour'
        parent1 = p1['order']
        parent2 = p2['order']
        n = len(parent1)
        a, b = sorted(random.sample(range(n), 2))
        child_order = [None]*n
        child_order[a:b+1] = parent1[a:b+1]
        ptr = 0
        for gene in parent2:
            if gene not in child_order:
                while child_order[ptr] is not None:
                    ptr += 1
                child_order[ptr] = gene

        # speeds: uniform crossover
        speeds = []
        for s1, s2 in zip(p1['speeds'], p2['speeds']):
            speeds.append(s1 if random.random() < 0.5 else s2)

        # start day/hour: inherit randomly from parents
        start_day = p1['start_day'] if random.random() < 0.5 else p2['start_day']
        start_hour = p1['start_hour'] if random.random() < 0.5 else p2['start_hour']

        return {'order': child_order, 'speeds': speeds, 'start_day': start_day, 'start_hour': start_hour}

    def mutate(self, individual):
        # mutate order (swap) or speeds or start
        # order mutation
        if random.random() < self.mut_rate:
            i, j = random.sample(range(len(individual['order'])), 2)
            individual['order'][i], individual['order'][j] = individual['order'][j], individual['order'][i]
        # speeds mutation: randomly change one speed to another múltiplo de 4 válido (36-96)
        if random.random() < self.mut_rate:
            idx = random.randrange(len(individual['speeds']))
            valid_speeds = get_valid_speeds()
            individual['speeds'][idx] = random.choice(valid_speeds)
        # start mutation
        if random.random() < self.mut_rate * 0.5:
            individual['start_day'] = random.randint(1, 7)
        if random.random() < self.mut_rate * 0.5:
            individual['start_hour'] = random.randint(6, 19)

    def run(self):
        pop = self.initial_population()
        best = None
        best_score = -1
        for g in range(self.generations):
            scores = [self.fitness(ind) for ind in pop]
            # track best
            for ind, sc in zip(pop, scores):
                if sc > best_score:
                    best = deepcopy(ind)
                    best_score = sc
            
            # Mostrar progresso a cada 20 geracoes
            if (g + 1) % 20 == 0 or g == 0:
                avg_score = sum(scores) / len(scores)
                print(f"Geracao {g+1:3d}/{self.generations}: Melhor score = {best_score:.8f}, Media = {avg_score:.8f}")
            
            # selection
            selected = self.select(pop, scores)
            # create next generation
            next_pop = []
            # elitism
            elite_inds = sorted(zip(pop, scores), key=lambda x: x[1], reverse=True)[:self.elite]
            for ind, sc in elite_inds:
                next_pop.append(deepcopy(ind))
            while len(next_pop) < self.pop_size:
                p1, p2 = random.sample(selected, 2)
                child = self.crossover(p1, p2)
                self.mutate(child)
                next_pop.append(child)
            pop = next_pop
        return best, best_score
