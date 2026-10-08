import sys
sys.path.insert(0, 'motor/scripts')
from evolution import create_random_genome, mutate_genome, crossover_genomes
import json

# Create initial genome
genome = create_random_genome(seed=12345)
print('Gen 0:', json.dumps(genome, indent=2)[:500])

# Mutate over 5 generations
current = genome
for gen in range(1, 6):
    current = mutate_genome(current, mutation_rate=0.1, seed=gen*100)
    print(f'Gen {gen}: generation={current["generation"]}')

# Crossover
parent_a = create_random_genome(seed=111)
parent_b = create_random_genome(seed=222)
child = crossover_genomes(parent_a, parent_b, seed=999)
print('Child generation:', child['generation'])