"""
Classe Particle para o PSO aplicado ao TSP.

A posição de cada partícula é uma permutação de cidades.
A velocidade é uma lista de operações de swap (pares de índices).
"""

import numpy as np
from typing import List, Tuple, Optional


class Particle:
    """Representa uma partícula no enxame PSO para o TSP."""

    def __init__(self, n_cities: int, rng: np.random.RandomState = None):
        self.n_cities = n_cities
        rng = rng or np.random.RandomState()

        # Posição: permutação aleatória de cidades
        self.position: List[int] = [int(x) for x in rng.permutation(n_cities)]

        # Velocidade: lista de swaps (pares de índices)
        self.velocity: List[Tuple[int, int]] = []

        # Fitness atual
        self.fitness: float = float('inf')

        # Melhor posição pessoal
        self.pbest_position: List[int] = list(self.position)
        self.pbest_fitness: float = float('inf')

    def update_pbest(self):
        """Atualiza o melhor pessoal se a posição atual for melhor."""
        if self.fitness < self.pbest_fitness:
            self.pbest_position = list(self.position)
            self.pbest_fitness = self.fitness
