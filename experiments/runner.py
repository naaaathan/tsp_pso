"""
Executor de experimentos para o PSO aplicado ao TSP.

Executa múltiplas runs com diferentes seeds, coleta estatísticas
e salva resultados em JSON para reprodutibilidade.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from pso.swarm import Swarm, PSOConfig, PSOResult
from pso.fitness import FitnessCalculator
from tsplib.parser import TSPLibParser, TSPInstance


@dataclass
class RunResult:
    """Resultado de uma única run do PSO."""
    best_fitness: float
    best_tour: List[int]
    convergence_history: List[float]
    execution_time: float
    iterations_run: int


@dataclass
class ExperimentResult:
    """Resultados agregados de múltiplas runs."""
    instance_name: str
    config_name: str
    num_cities: int
    optimal_value: Optional[float]
    num_runs: int
    best: float
    worst: float
    average: float
    std: float
    median: float
    gap_percentage: Optional[float]
    avg_time: float
    all_values: List[float]
    all_convergence: List[List[float]]
    best_tour: List[int]
    config_params: Dict[str, Any]


class ExperimentRunner:
    """Executa experimentos do PSO em instâncias TSP."""

    def __init__(self, instances_dir: str, results_dir: str):
        self.instances_dir = Path(instances_dir)
        self.results_dir = Path(results_dir)
        self.parser = TSPLibParser()
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def load_instance(self, filename: str) -> TSPInstance:
        """Carrega uma instância TSPLIB."""
        filepath = self.instances_dir / filename
        return self.parser.parse(str(filepath))

    def run_experiment(
        self,
        instance: TSPInstance,
        config: PSOConfig,
        config_name: str,
        num_runs: int = 30,
        verbose: bool = False,
    ) -> ExperimentResult:
        """Executa múltiplas runs do PSO em uma instância."""
        distance_matrix = instance.get_distance_matrix()
        fitness_calc = FitnessCalculator(distance_matrix)

        all_values = []
        all_times = []
        all_convergence = []
        best_result = None

        for run in range(num_runs):
            # Criar config com seed específica
            run_config = PSOConfig(
                num_particles=config.num_particles,
                max_iterations=config.max_iterations,
                w=config.w,
                c1=config.c1,
                c2=config.c2,
                use_2opt=config.use_2opt,
                use_3opt=config.use_3opt,
                adaptive_inertia=config.adaptive_inertia,
                w_max=config.w_max,
                w_min=config.w_min,
                local_search_strategy=config.local_search_strategy,
                transition_fraction=config.transition_fraction,
                random_seed=run,
            )

            swarm = Swarm(fitness_calc, run_config)
            result = swarm.run(verbose=False)

            all_values.append(result.best_fitness)
            all_times.append(result.execution_time)
            all_convergence.append(result.convergence_history)

            if best_result is None or result.best_fitness < best_result.best_fitness:
                best_result = result

            if verbose:
                print(f"  Run {run + 1}/{num_runs}: {result.best_fitness:.2f} "
                      f"({result.execution_time:.2f}s)")

        stats = {
            'best': min(all_values),
            'worst': max(all_values),
            'average': float(np.mean(all_values)),
            'std': float(np.std(all_values)),
            'median': float(np.median(all_values)),
        }

        gap = None
        if instance.optimal_value and instance.optimal_value > 0:
            gap = ((stats['best'] - instance.optimal_value) / instance.optimal_value) * 100

        config_params = {
            'num_particles': config.num_particles,
            'max_iterations': config.max_iterations,
            'w': config.w,
            'c1': config.c1,
            'c2': config.c2,
            'local_search_strategy': config.local_search_strategy,
            'adaptive_inertia': config.adaptive_inertia,
        }

        return ExperimentResult(
            instance_name=instance.name,
            config_name=config_name,
            num_cities=instance.dimension,
            optimal_value=instance.optimal_value,
            num_runs=num_runs,
            best=stats['best'],
            worst=stats['worst'],
            average=stats['average'],
            std=stats['std'],
            median=stats['median'],
            gap_percentage=gap,
            avg_time=float(np.mean(all_times)),
            all_values=all_values,
            all_convergence=all_convergence,
            best_tour=best_result.best_tour,
            config_params=config_params,
        )

    def save_results(self, results: List[ExperimentResult], experiment_name: str):
        """Salva resultados em JSON."""
        data = []
        for r in results:
            data.append({
                'instance_name': r.instance_name,
                'config_name': r.config_name,
                'num_cities': r.num_cities,
                'optimal_value': r.optimal_value,
                'num_runs': r.num_runs,
                'best': r.best,
                'worst': r.worst,
                'average': r.average,
                'std': r.std,
                'median': r.median,
                'gap_percentage': r.gap_percentage,
                'avg_time': r.avg_time,
                'all_values': r.all_values,
                'all_convergence': r.all_convergence,
                'best_tour': r.best_tour,
                'config_params': r.config_params,
            })

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.results_dir / f'{experiment_name}_{timestamp}.json'
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        latest_path = self.results_dir / f'{experiment_name}_latest.json'
        with open(latest_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Resultados salvos em {filepath}")
        return filepath
