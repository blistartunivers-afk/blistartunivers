"""
Motor de Imaginación — Operadores de Genética, Crossover y Mutación para CPPNs.
"""
import json
import math
import random

ACTIVATION_NAMES = ["sin", "cos", "tanh", "gauss", "softsign"]

def create_random_genome(seed=None):
    """Crea un genoma aleatorio serializable para la CPPN."""
    if seed is not None:
        random.seed(seed)
        
    # Arquitectura estándar: 4 inputs (x, y, r, 1) -> 8 -> 8 -> 1 output
    w1 = [[random.uniform(-2, 2) for _ in range(4)] for _ in range(8)]
    act1 = [random.choice(ACTIVATION_NAMES) for _ in range(8)]
    
    w2 = [[random.uniform(-2, 2) for _ in range(8)] for _ in range(8)]
    act2 = [random.choice(ACTIVATION_NAMES) for _ in range(8)]
    
    w3 = [random.uniform(-2, 2) for _ in range(8)]
    
    return {
        "version": 1,
        "seed": seed,
        "architecture": [4, 8, 8, 1],
        "w1": w1,
        "act1": act1,
        "w2": w2,
        "act2": act2,
        "w3": w3,
        "generation": 0
    }

def mutate_genome(genome, mutation_rate=0.15, weight_scale=0.3, seed=None):
    """Aplica mutaciones suaves a los pesos y opcionalmente a las funciones de activación."""
    if seed is not None:
        random.seed(seed)
        
    mutated = json.loads(json.dumps(genome))
    mutated["generation"] = genome.get("generation", 0) + 1
    
    # Mutación w1
    for i in range(len(mutated["w1"])):  # Corregido paréntesis
        for j in range(len(mutated["w1"][i])):
            if random.random() < mutation_rate:
                mutated["w1"][i][j] += random.gauss(0, weight_scale)
                mutated["w1"][i][j] = max(-3.0, min(3.0, mutated["w1"][i][j]))
        if random.random() < (mutation_rate * 0.5):
            mutated["act1"][i] = random.choice(ACTIVATION_NAMES)
            
    # Mutación w2
    for i in range(len(mutated["w2"])):  # Corregido paréntesis
        for j in range(len(mutated["w2"][i])):
            if random.random() < mutation_rate:
                mutated["w2"][i][j] += random.gauss(0, weight_scale)
                mutated["w2"][i][j] = max(-3.0, min(3.0, mutated["w2"][i][j]))
        if random.random() < (mutation_rate * 0.5):
            mutated["act2"][i] = random.choice(ACTIVATION_NAMES)
            
    # Mutación w3
    for i in range(len(mutated["w3"])):  # Corregido paréntesis
        if random.random() < mutation_rate:
            mutated["w3"][i] += random.gauss(0, weight_scale)
            mutated["w3"][i] = max(-3.0, min(3.0, mutated["w3"][i]))
            
    return mutated

def crossover_genomes(parent_a, parent_b, seed=None):
    """Combina genéticamente dos genomas padres."""
    if seed is not None:
        random.seed(seed)
        
    child = json.loads(json.dumps(parent_a))
    child["generation"] = max(parent_a.get("generation", 0), parent_b.get("generation", 0)) + 1
    
    # Cruce w1 & act1
    for i in range(len(child["w1"])):  # Corregido paréntesis
        if random.random() < 0.5:
            child["w1"][i] = list(parent_b["w1"][i])
            child["act1"][i] = parent_b["act1"][i]
            
    # Cruce w2 & act2
    for i in range(len(child["w2"])):  # Corregido paréntesis
        if random.random() < 0.5:
            child["w2"][i] = list(parent_b["w2"][i])
            child["act2"][i] = parent_b["act2"][i]
            
    # Cruce w3
    for i in range(len(child["w3"])):  # Corregido paréntesis
        if random.random() < 0.5:
            child["w3"][i] = parent_b["w3"][i]
            
    return child
