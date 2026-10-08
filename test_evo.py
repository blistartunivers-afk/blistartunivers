import json, math, random
from dataclasses import dataclass
from typing import List, Optional

ACTIVATION_NAMES = ['sin', 'cos', 'tanh', 'gauss', 'softsign']
ACTIVATION_FUNCS = {'sin': math.sin, 'cos': math.cos, 'tanh': math.tanh, 'gauss': lambda v: math.exp(-v*v), 'softsign': lambda v: v/(1+abs(v))}

def create_random_genome(seed=None):
    if seed: random.seed(seed)
    return {'version': 2, 'seed': seed, 'architecture': [4,8,8,1],
        'w1': [[random.uniform(-2,2) for _ in range(4)] for _ in range(8)],
        'act1': [random.choice(ACTIVATION_NAMES) for _ in range(8)],
        'w2': [[random.uniform(-2,2) for _ in range(8)] for _ in range(8)],
        'act2': [random.choice(ACTIVATION_NAMES) for _ in range(8)],
        'w3': [random.uniform(-2,2) for _ in range(8)],
        'generation': 0, 'fitness': None, 'metrics': {}, 'parent_ids': []}

def mutate_genome(genome, mutation_rate=0.15, weight_scale=0.3, seed=None):
    if seed: random.seed(seed)
    m = json.loads(json.dumps(genome))
    m['generation'] = genome.get('generation',0)+1
    m['fitness']=None; m['metrics']={}; m['parent_ids']=[genome.get('id','unknown')]
    for i in range(len(m['w1'])):
        for j in range(len(m['w1'][i])):
            if random.random() < mutation_rate:
                m['w1'][i][j] += random.gauss(0, weight_scale)
                m['w1'][i][j] = max(-3.0, min(3.0, m['w1'][i][j]))
        if random.random() < mutation_rate*0.5: m['act1'][i] = random.choice(ACTIVATION_NAMES)
    for i in range(len(m['w2'])):
        for j in range(len(m['w2'][i])):
            if random.random() < mutation_rate:
                m['w2'][i][j] += random.gauss(0, weight_scale)
                m['w2'][i][j] = max(-3.0, min(3.0, m['w2'][i][j]))
        if random.random() < mutation_rate*0.5: m['act2'][i] = random.choice(ACTIVATION_NAMES)
    for i in range(len(m['w3'])):
        if random.random() < mutation_rate:
            m['w3'][i] += random.gauss(0, weight_scale)
            m['w3'][i] = max(-3.0, min(3.0, m['w3'][i]))
    return m

def crossover_genomes(a, b, seed=None):
    if seed: random.seed(seed)
    c = json.loads(json.dumps(a))
    c['generation'] = max(a.get('generation',0), b.get('generation',0))+1
    c['fitness']=None; c['metrics']={}; c['parent_ids']=[a.get('id','a'), b.get('id','b')]
    for i in range(len(c['w1'])):
        for j in range(len(c['w1'][i])):
            if random.random()<0.5: c['w1'][i][j]=b['w1'][i][j]
        if random.random()<0.5: c['act1'][i]=b['act1'][i]
    for i in range(len(c['w2'])):
        for j in range(len(c['w2'][i])):
            if random.random()<0.5: c['w2'][i][j]=b['w2'][i][j]
        if random.random()<0.5: c['act2'][i]=b['act2'][i]
    for i in range(len(c['w3'])):
        if random.random()<0.5: c['w3'][i]=b['w3'][i]
    return c

def eval_intensity(g, w=64, h=64):
    w1, a1 = g['w1'], [ACTIVATION_FUNCS[x] for x in g['act1']]
    w2, a2 = g['w2'], [ACTIVATION_FUNCS[x] for x in g['act2']]
    w3 = g['w3']
    I = [[0.0]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            nx, ny = (x/w)*2-1, (y/h)*2-1
            r = math.sqrt(nx*nx+ny*ny)
            inp = [nx, ny, r, 1.0]
            h1 = [a1[ni](sum(inp[k]*w1[ni][k] for k in range(4))) for ni in range(8)]
            h2 = [a2[ni](sum(h1[k]*w2[ni][k] for k in range(8))) for ni in range(8)]
            out = sum(h2[k]*w3[k] for k in range(8))
            I[y][x] = (math.tanh(out)+1)/2
    return I

def fitness_metrics(I):
    h, w = len(I), len(I[0])
    flat = [I[y][x] for y in range(h) for x in range(w)]
    total = w*h
    hist = [0]*256
    for v in flat: hist[min(255,int(v*255))]+=1
    shannon = sum(-(c/total)*math.log2(c/total) for c in hist if c>0)
    sp = sum(math.sqrt((I[y][x+1]-I[y][x-1])**2+(I[y+1][x]-I[y-1][x])**2) for y in range(1,h-1) for x in range(1,w-1))
    spatial = sp/((h-2)*(w-2)) if h>2 and w>2 else 0
    mean = sum(flat)/total
    contrast = math.sqrt(sum((v-mean)**2 for v in flat)/total)
    unique = len(set(min(255,int(v*255)) for v in flat))
    diversity = unique/256.0
    sym = sum(abs(I[y][x]-I[y][w-1-x]) for y in range(h) for x in range(w//2))
    symmetry = 1.0 - sym/(h*(w//2)) if w>1 else 1.0
    return {'shannon_entropy':shannon,'spatial_entropy':spatial,'contrast':contrast,'diversity':diversity,'symmetry':symmetry,'unique_values':unique}

def fitness_func(m, weights=None):
    if weights is None: weights={'shannon_entropy':0.30,'spatial_entropy':0.25,'contrast':0.20,'diversity':0.15,'symmetry':0.10}
    n = {'shannon_entropy':min(m['shannon_entropy']/8,1),'spatial_entropy':min(m['spatial_entropy']/2,1),'contrast':min(m['contrast']/0.5,1),'diversity':m['diversity'],'symmetry':m['symmetry']}
    return sum(weights[k]*n[k] for k in weights)

def eval_genome(g, w=64, h=64):
    I = eval_intensity(g,w,h)
    m = fitness_metrics(I)
    return {'fitness':fitness_func(m), 'metrics':m, 'intensity':I}

@dataclass
class Ind:
    genome: dict
    fitness: float=0.0
    metrics: dict=None
    intensity: List=None
    def __post_init__(self):
        if self.metrics is None: self.metrics={}

def create_pop(size, seed=None):
    if seed: random.seed(seed)
    return [Ind(genome={**create_random_genome(seed=seed+i if seed else None), 'id':f'gen0_{i}'}) for i in range(size)]

def eval_pop(pop, w=64, h=64):
    for ind in pop:
        r = eval_genome(ind.genome,w,h)
        ind.fitness, ind.metrics, ind.intensity = r['fitness'], r['metrics'], r['intensity']
        ind.genome['fitness'], ind.genome['metrics'] = r['fitness'], r['metrics']

def tourney(pop, k=3):
    return max(random.sample(pop, min(k,len(pop))), key=lambda x: x.fitness)

def roulette(pop):
    tot = sum(x.fitness for x in pop)
    if tot<=0: return random.choice(pop)
    pick, cur = random.uniform(0,tot), 0
    for x in pop:
        cur += x.fitness
        if cur>=pick: return x
    return pop[-1]

def evolve(pop, elite=2, mut=0.15, cross=0.7, sel='tournament'):
    pop.sort(key=lambda x: x.fitness, reverse=True)
    new = []
    for i in range(min(elite,len(pop))):
        e = json.loads(json.dumps(pop[i].genome))
        e['id']=f"gen{e['generation']}_elite_{i}"
        new.append(Ind(genome=e, fitness=pop[i].fitness, metrics=pop[i].metrics, intensity=pop[i].intensity))
    fn = tourney if sel=='tournament' else roulette
    while len(new)<len(pop):
        if random.random()<cross and len(pop)>=2:
            cg = crossover_genomes(fn(pop).genome, fn(pop).genome)
        else:
            cg = json.loads(json.dumps(fn(pop).genome))
        cg = mutate_genome(cg, mutation_rate=mut)
        cg['id']=f"gen{cg['generation']}_{len(new)}"
        new.append(Ind(genome=cg))
    return new

def run_evo(gens=10, psize=20, seed=None, w=64, h=64):
    if seed: random.seed(seed)
    pop = create_pop(psize, seed)
    eval_pop(pop, w, h)
    hist = []
    for gen in range(gens):
        pop.sort(key=lambda x: x.fitness, reverse=True)
        best = pop[0]
        avg = sum(x.fitness for x in pop)/len(pop)
        hist.append({'generation':gen,'best_fitness':best.fitness,'avg_fitness':avg,'best_metrics':best.metrics,'best_genome':best.genome})
        print(f'Gen {gen}: best={best.fitness:.4f} avg={avg:.4f} shannon={best.metrics.get("shannon_entropy",0):.3f} spatial={best.metrics.get("spatial_entropy",0):.3f}')
        if gen < gens-1:
            pop = evolve(pop, mut=0.15, cross=0.7)
            eval_pop(pop, w, h)
    return {'history':hist, 'final_population':[x.genome for x in pop]}

result = run_evo(gens=5, psize=10, seed=42)
print('\nDone. Best final:', result['history'][-1]['best_fitness'])