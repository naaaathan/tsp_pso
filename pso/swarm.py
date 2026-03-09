"""
Algoritmo PSO principal para o TSP.

Implementa o Particle Swarm Optimization adaptado para o domínio
de permutações, conforme descrito no artigo de Araújo & Barboza (2025).
"""

import numpy as np
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .particle import Particle
from .fitness import FitnessCalculator
from .velocity import update_velocity
from .position_update import update_position
from .local_search import two_opt, three_opt


@dataclass
class PSOConfig:
    """Configuração do algoritmo PSO."""
    num_particles: int = 30
    max_iterations: int = 100
    w: float = 0.8          # fator de inércia
    c1: float = 2.0         # coeficiente cognitivo
    c2: float = 2.0         # coeficiente social
    use_2opt: bool = True
    use_3opt: bool = False
    adaptive_inertia: bool = False  # w decrescente linear de w_max a w_min
    w_max: float = 0.9
    w_min: float = 0.4
    # Estratégia de busca local: 'none', '2opt', '3opt', '2opt_then_3opt'
    local_search_strategy: str = '2opt'
    # Para '2opt_then_3opt': iteração de transição (fração do total)
    transition_fraction: float = 0.5
    random_seed: Optional[int] = None


@dataclass
class PSOResult:
    """Resultado da execução do PSO."""
    best_fitness: float
    best_tour: List[int]
    convergence_history: List[float]  # melhor fitness por iteração
    execution_time: float
    iterations_run: int


class Swarm:
    """Implementação do PSO para o TSP."""

    def __init__(self, fitness_calculator: FitnessCalculator, config: PSOConfig):
        self.fitness_calc = fitness_calculator
        self.config = config
        self.n_cities = fitness_calculator.n_cities

        if config.random_seed is not None:
            self.rng = np.random.RandomState(config.random_seed)
        else:
            self.rng = np.random.RandomState()

    def run(self, verbose: bool = False) -> PSOResult:
        """Executa o algoritmo PSO."""
        start_time = time.time()
        config = self.config
        dm = self.fitness_calc.distance_matrix

        # 1. Inicializar partículas
        particles = [Particle(self.n_cities, self.rng) for _ in range(config.num_particles)]

        # 2. Calcular fitness inicial
        for p in particles:
            p.fitness = self.fitness_calc.calculate(p.position)
            p.pbest_fitness = p.fitness
            p.pbest_position = list(p.position)

        # 3. Encontrar gBest
        gbest_particle = min(particles, key=lambda p: p.pbest_fitness)
        gbest_position = list(gbest_particle.pbest_position)
        gbest_fitness = gbest_particle.pbest_fitness

        convergence_history = [gbest_fitness]

        # 4. Loop principal
        for iteration in range(config.max_iterations):
            # Calcular w para esta iteração
            if config.adaptive_inertia:
                w = config.w_max - (config.w_max - config.w_min) * (iteration / config.max_iterations)
            else:
                w = config.w

            # Determinar busca local para esta iteração
            use_2opt = False
            use_3opt = False
            strategy = config.local_search_strategy
            if strategy == '2opt':
                use_2opt = True
            elif strategy == '3opt':
                use_3opt = True
            elif strategy == '2opt_then_3opt':
                transition_iter = int(config.transition_fraction * config.max_iterations)
                if iteration < transition_iter:
                    use_2opt = True
                else:
                    use_3opt = True

            for p in particles:
                # a. Atualizar velocidade
                p.velocity = update_velocity(
                    p.velocity, p.position, p.pbest_position, gbest_position,
                    w, config.c1, config.c2, self.rng
                )

                # b. Atualizar posição
                p.position = update_position(p.position, p.velocity)

                # c. Busca local
                if use_2opt:
                    p.position = two_opt(p.position, dm)
                elif use_3opt:
                    p.position = three_opt(p.position, dm)

                # d. Calcular fitness
                p.fitness = self.fitness_calc.calculate(p.position)

                # e. Atualizar pBest
                p.update_pbest()

                # f. Atualizar gBest
                if p.pbest_fitness < gbest_fitness:
                    gbest_position = list(p.pbest_position)
                    gbest_fitness = p.pbest_fitness

            convergence_history.append(gbest_fitness)

            if verbose and (iteration + 1) % 10 == 0:
                print(f"  Iteração {iteration + 1}/{config.max_iterations}: gBest = {gbest_fitness:.2f}")

        execution_time = time.time() - start_time

        return PSOResult(
            best_fitness=float(gbest_fitness),
            best_tour=[int(x) for x in gbest_position],
            convergence_history=[float(x) for x in convergence_history],
            execution_time=execution_time,
            iterations_run=config.max_iterations,
        )
