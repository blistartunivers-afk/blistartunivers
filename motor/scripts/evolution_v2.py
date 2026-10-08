"""
Motor de Imaginación — Evolución CPPN con Fitness y Selección

Extiende evolution.py con:
- Evaluación de fitness (entropía, diversidad, estética)
- Selección por torneo / ruleta
- Población completa con generaciones
- Serialización JSONL para persistencia
- Estadísticas de evolución
"""
import json
import math
import random
from dataclasses import dataclass
from typing import List, Optional

ACTIVATION_NAMES = ["sin", "cos", "tanh", "gauss", "softsign"]
ACTIVATION_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tanh": math.tanh,
    "gauss": lambda v: math.exp(-v * v),
    "softsign": lambda v: v / (1.0 + abs(v)),
}

def create_random_genome(seed: Optional[int] = None) -> dict:
    if seed is not None: random.seed(seed)
    return {
        "version": 2, "seed": seed, "architecture": [4, 8, 8, 1],
        "w1": [[random.uniform(-2, 2) for _ in range(4)] for _ in range(8)],
        "act1": [random.choice(ACTIVATION_NAMES) for _ in range(8)],
        "w2": [[random.uniform(-2, 2) for _ in range(8)] for _ in range(8)],
        "act2": [random.choice(ACTIVATION_NAMES) for _ in range(8)],
        "w3": [random.uniform(-2, 2) for _ in range(8)],
        "generation": 0, "fitness": None, "metrics": {}, "parent_ids": [],
    }

def mutate_genome(genome: dict, mutation_rate: float = 0.15, weight_scale: float = 0.3, seed: Optional[int] = None) -> dict:
    if seed is not None: random.seed(seed)
    mutated = json.loads(json.dumps(genome))
    mutated["generation"] = genome.get("generation", 0) + 1
    mutated["fitness"] = None; mutated["metrics"] = {}; mutated["parent_ids"] = [genome.get("id", "unknown")]
    for i in range(len(mutated["w1"])):
        for j in range(len(mutated["w1"][i])):
            if random.random() < mutation_rate:
                mutated["w1"][i][j] += random.gauss(0, weight_scale)
                mutated["w1"][i][j] = max(-3.0, min(3.0, mutated["w1"][i][j]))
        if random.random() < (mutation_rate * 0.5):
            mutated["act1"][i] = random.choice(ACTIVATION_NAMES)
    for i in range(len(mutated["w2"])):
        for j in range(len(mutated["w2"][i])):
            if random.random() < mutation_rate:
                mutated["w2"][i][j] += random.gauss(0, weight_scale)
                mutated["w2"][i][j] = max(-3.0, min(3.0, mutated["w2"][i][j]))
        if random.random() < (mutation_rate * 0.5):
            mutated["act2"][i] = random.choice(ACTIVATION_NAMES)
    for i in range(len(mutated["w3"])):
        if random.random() < mutation_rate:
            mutated["w3"][i] += random.gauss(0, weight_scale)
            mutated["w3"][i] = max(-3.0, min(3.0, mutated["w3"][i]))
    return mutated

def crossover_genomes(parent_a: dict, parent_b: dict, seed: Optional[int] = None) -> dict:
    if seed is not None: random.seed(seed)
    child = json.loads(json.dumps(parent_a))
    child["generation"] = max(parent_a.get("generation", 0), parent_b.get("generation", 0)) + 1
    child["fitness"] = None; child["metrics"] = {}; child["parent_ids"] = [parent_a.get("id", "a"), parent_b.get("id", "b")]
    for i in range(len(child["w1"])):
        for j in range(len(child["w1"][i])):
            if random.random() < 0.5: child["w1"][i][j] = parent_b["w1"][i][j]
        if random.random() < 0.5: child["act1"][i] = parent_b["act1"][i]
    for i in range(len(child["w2"])):
        for j in range(len(child["w2"][i])):
            if random.random() < 0.5: child["w2"][i][j] = parent_b["w2"][i][j]
        if random.random() < 0.5: child["act2"][i] = parent_b["act2"][i]
    for i in range(len(child["w3"])):
        if random.random() < 0.5: child["w3"][i] = parent_b["w3"][i]
    return child

def evaluate_cppn_intensity(genome: dict, width: int = 64, height: int = 64) -> List[List[float]]:
    w1, act1 = genome["w1"], [ACTIVATION_FUNCS[a] for a in genome["act1"]]
    w2, act2 = genome["w2"], [ACTIVATION_FUNCS[a] for a in genome["act2"]]
    w3 = genome["w3"]
    intensity = [[0.0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            nx = (x / width) * 2 - 1
            ny = (y / height) * 2 - 1
            r = math.sqrt(nx*nx + ny*ny)
            inputs = [nx, ny, r, 1.0]
            h1 = [act1[ni](sum(inputs[k] * w1[ni][k] for k in range(4))) for ni in range(8)]
            h2 = [act2[ni](sum(h1[k] * w2[ni][k] for k in range(8))) for ni in range(8)]
            out = sum(h2[k] * w3[k] for k in range(8))
            intensity[y][x] = (math.tanh(out) + 1) / 2
    return intensity

def compute_fitness_metrics(intensity: List[List[float]]) -> dict:
    height, width = len(intensity), len(intensity[0])
    total = width * height
    flat = [intensity[y][x] for y in range(height) for x in range(width)]
    hist = [0] * 256
    for v in flat: hist[min(255, int(v * 255))] += 1
    shannon = sum(-(c/total) * math.log2(c/total) for c in hist if c > 0)
    spatial_sum = sum(math.sqrt((intensity[y][x+1]-intensity[y][x-1])**2 + (intensity[y+1][x]-intensity[y-1][x])**2) for y in range(1,height-1) for x in range(1,width-1))
    spatial_entropy = spatial_sum / ((height-2)*(width-2)) if height>2 and width>2 else 0.0
    mean = sum(flat) / total
    contrast = math.sqrt(sum((v - mean) ** 2 for v in flat) / total)
    unique = len(set(min(255, int(v * 255)) for v in flat))
    diversity = unique / 256.0
    sym_sum = sum(abs(intensity[y][x] - intensity[y][width - 1 - x]) for y in range(height) for x in range(width // 2))
    symmetry = 1.0 - (sym_sum / (height * (width // 2))) if width > 1 else 1.0
    return {"shannon_entropy": shannon, "spatial_entropy": spatial_entropy, "contrast": contrast, "diversity": diversity, "symmetry": symmetry, "unique_values": unique}

def fitness_function(metrics: dict, weights: Optional[dict] = None) -> float:
    if weights is None: weights = {"shannon_entropy": 0.30, "spatial_entropy": 0.25, "contrast": 0.20, "diversity": 0.15, "symmetry": 0.10}
    norm = {
        "shannon_entropy": min(metrics["shannon_entropy"] / 8.0, 1.0),
        "spatial_entropy": min(metrics["spatial_entropy"] / 2.0, 1.0),
        "contrast": min(metrics["contrast"] / 0.5, 1.0),
        "diversity": metrics["diversity"],
        "symmetry": metrics["symmetry"],
    }
    return sum(weights[k] * norm[k] for k in weights)

def evaluate_genome(genome: dict, width: int = 64, height: int = 64) -> dict:
    intensity = evaluate_cppn_intensity(genome, width, height)
    metrics = compute_fitness_metrics(intensity)
    return {"fitness": fitness_function(metrics), "metrics": metrics, "intensity": intensity}

@dataclass
class Individual:
    genome: dict
    fitness: float = 0.0
    metrics: dict = None
    intensity: List[List[float]] = None
    def __post_init__(self):
        if self.metrics is None: self.metrics = {}

def create_population(size: int, seed: Optional[int] = None) -> List[Individual]:
    if seed is not None: random.seed(seed)
    return [Individual(genome={**create_random_genome(seed=seed + i if seed else None), "id": f"gen0_{i}"}) for i in range(size)]

def evaluate_population(population: List[Individual], width: int = 64, height: int = 64) -> None:
    for ind in population:
        result = evaluate_genome(ind.genome, width, height)
        ind.fitness, ind.metrics, ind.intensity = result["fitness"], result["metrics"], result["intensity"]
        ind.genome["fitness"], ind.genome["metrics"] = result["fitness"], result["metrics"]

def tournament_selection(population: List[Individual], tournament_size: int = 3) -> Individual:
    return max(random.sample(population, min(tournament_size, len(population))), key=lambda ind: ind.fitness)

def roulette_selection(population: List[Individual]) -> Individual:
    total_fitness = sum(ind.fitness for ind in population)
    if total_fitness <= 0: return random.choice(population)
    pick = random.uniform(0, total_fitness)
    current = 0
    for ind in population:
        current += ind.fitness
        if current >= pick: return ind
    return population[-1]

def evolve_population(population: List[Individual], elite_size: int = 2, mutation_rate: float = 0.15, crossover_rate: float = 0.7, selection: str = "tournament") -> List[Individual]:
    population.sort(key=lambda ind: ind.fitness, reverse=True)
    new_population = []
    for i in range(min(elite_size, len(population))):
        elite = json.loads(json.dumps(population[i].genome))
        elite["id"] = f"gen{elite['generation']}_elite_{i}"
        new_population.append(Individual(genome=elite, fitness=population[i].fitness, metrics=population[i].metrics, intensity=population[i].intensity))
    select_fn = tournament_selection if selection == "tournament" else roulette_selection
    while len(new_population) < len(population):
        if random.random() < crossover_rate and len(population) >= 2:
            child_genome = crossover_genomes(select_fn(population).genome, select_fn(population).genome)
        else:
            child_genome = json.loads(json.dumps(select_fn(population).genome))
        child_genome = mutate_genome(child_genome, mutation_rate=mutation_rate)
        child_genome["id"] = f"gen{child_genome['generation']}_{len(new_population)}"
        new_population.append(Individual(genome=child_genome))
    return new_population

def run_evolution(generations: int = 10, pop_size: int = 20, seed: Optional[int] = None, width: int = 64, height: int = 64) -> dict:
    if seed is not None: random.seed(seed)
    population = create_population(pop_size, seed)
    evaluate_population(population, width, height)
    history = []
    for gen in range(generations):
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        best = population[0]
        avg_fitness = sum(ind.fitness for ind in population) / len(population)
        history.append({"generation": gen, "best_fitness": best.fitness, "avg_fitness": avg_fitness, "best_metrics": best.metrics, "best_genome": best.genome})
        print(f"Gen {gen}: best={best.fitness:.4f} avg={avg_fitness:.4f} shannon={best.metrics.get('shannon_entropy',0):.3f} spatial={best.metrics.get('spatial_entropy',0):.3f}")
        if gen < generations - 1:
            population = evolve_population(population, mutation_rate=0.15, crossover_rate=0.7)
            evaluate_population(population, width, height)
    return {"history": history, "final_population": [ind.genome for ind in population]}

if __name__ == "__main__":
    result = run_evolution(generations=15, pop_size=30, seed=42)
    print("\nEvolución completada.")
    print(f"Mejor fitness final: {result['history'][-1]['best_fitness']:.4f}")