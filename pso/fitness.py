"""
Cálculo de fitness para o PSO aplicado ao TSP.

O fitness é a distância total do tour (soma das distâncias entre cidades
consecutivas + retorno à origem). Queremos MINIMIZAR.
"""

import numpy as np
from typing import List


class FitnessCalculator:
    """Calcula o custo total de um tour TSP."""

    def __init__(self, distance_matrix: np.ndarray):
        self.distance_matrix = distance_matrix
        self.n_cities = len(distance_matrix)

    def calculate(self, tour: List[int]) -> float:
        """Calcula a distância total do tour."""
        total = 0.0
        for i in range(len(tour) - 1):
            total += self.distance_matrix[tour[i]][tour[i + 1]]
        total += self.distance_matrix[tour[-1]][tour[0]]
        return total
