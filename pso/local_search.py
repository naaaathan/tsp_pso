"""
Operadores de busca local para o PSO aplicado ao TSP.

- 2-opt: inverte um segmento do tour se isso reduzir a distancia.
- 3-opt: rearranjo de 3 segmentos do tour (single-pass, capped).
"""

import numpy as np
from typing import List


def two_opt(tour: List[int], distance_matrix: np.ndarray) -> List[int]:
    """
    Aplica busca local 2-opt ao tour (first-improvement, full convergence).
    """
    n = len(tour)
    improved = True

    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue

                c1 = tour[i]
                c2 = tour[i + 1]
                c3 = tour[j]
                c4 = tour[(j + 1) % n]

                old_cost = distance_matrix[c1][c2] + distance_matrix[c3][c4]
                new_cost = distance_matrix[c1][c3] + distance_matrix[c2][c4]

                if new_cost < old_cost:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    improved = True

    return tour


def three_opt(tour: List[int], distance_matrix: np.ndarray, max_passes: int = 1) -> List[int]:
    """
    Aplica busca local 3-opt ao tour.

    Limitado a max_passes passagens completas para evitar tempo excessivo.
    Aplica 2-opt primeiro para reduzir o trabalho do 3-opt.
    """
    # Primeiro aplica 2-opt para chegar a um bom ponto de partida
    tour = two_opt(tour, distance_matrix)

    n = len(tour)

    for _pass in range(max_passes):
        improved = False
        for i in range(n - 4):
            for j in range(i + 2, n - 2):
                for k in range(j + 2, n):
                    c_i = tour[i]
                    c_i1 = tour[i + 1]
                    c_j = tour[j]
                    c_j1 = tour[j + 1]
                    c_k = tour[k]
                    c_k1 = tour[(k + 1) % n]

                    old_cost = (distance_matrix[c_i][c_i1] +
                                distance_matrix[c_j][c_j1] +
                                distance_matrix[c_k][c_k1])

                    # Rearranjo 1: reverter segmento [i+1..j]
                    new_cost1 = (distance_matrix[c_i][c_j] +
                                 distance_matrix[c_i1][c_j1] +
                                 distance_matrix[c_k][c_k1])
                    if new_cost1 < old_cost:
                        tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                        improved = True
                        continue

                    # Rearranjo 2: reverter segmento [j+1..k]
                    new_cost2 = (distance_matrix[c_i][c_i1] +
                                 distance_matrix[c_j][c_k] +
                                 distance_matrix[c_j1][c_k1])
                    if new_cost2 < old_cost:
                        tour[j + 1:k + 1] = tour[j + 1:k + 1][::-1]
                        improved = True
                        continue

                    # Rearranjo 3: reverter ambos segmentos
                    new_cost3 = (distance_matrix[c_i][c_j] +
                                 distance_matrix[c_i1][c_k] +
                                 distance_matrix[c_j1][c_k1])
                    if new_cost3 < old_cost:
                        tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                        tour[j + 1:k + 1] = tour[j + 1:k + 1][::-1]
                        improved = True
                        continue

        if not improved:
            break

    return tour
