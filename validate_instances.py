"""Quick validation: run baseline on new instances to check coordinates are correct."""
import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import Swarm, PSOConfig
from pso.fitness import FitnessCalculator
from tsplib.parser import TSPLibParser

INSTANCES = {
    'eil76': 538,
    'st70': 675,
    'kroB100': 22141,
}

parser = TSPLibParser()
config = PSOConfig(
    num_particles=30, max_iterations=100,
    w=0.8, c1=2.0, c2=2.0,
    local_search_strategy='2opt',
    random_seed=0,
)

for name, optimal in INSTANCES.items():
    path = Path(__file__).parent / 'tsplib' / 'instances' / f'{name}.tsp'
    instance = parser.parse(str(path))
    dm = instance.get_distance_matrix()
    fc = FitnessCalculator(dm)

    # Run 3 seeds
    results = []
    for seed in range(3):
        config.random_seed = seed
        result = Swarm(fc, config).run()
        results.append(result.best_fitness)

    best = min(results)
    gap = ((best - optimal) / optimal) * 100
    status = "OK" if gap >= 0 else "BAD COORDS (negative gap!)"
    print(f'{name}: best={best:.0f}, optimal={optimal}, gap={gap:+.2f}% => {status}', flush=True)
