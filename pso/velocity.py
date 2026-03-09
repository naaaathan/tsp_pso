"""
Atualização de velocidade para o PSO discreto aplicado ao TSP.

A equação contínua v(t+1) = w*v(t) + c1*r1*(pBest - x) + c2*r2*(gBest - x)
é adaptada para o domínio de permutações:
- (pBest - x) = sequência de swaps que transforma x em pBest
- w * v = manter uma fração das swaps anteriores
- c1*r1 e c2*r2 = probabilidade de aplicar cada swap da diferença
"""

import numpy as np
from typing import List, Tuple


def compute_swap_sequence(source: List[int], target: List[int]) -> List[Tuple[int, int]]:
    """
    Calcula a sequência de swaps necessária para transformar source em target.

    Usa o algoritmo: para cada posição i, se source[i] != target[i],
    encontra onde target[i] está em source e faz o swap.
    """
    current = list(source)
    swaps = []
    n = len(current)

    for i in range(n):
        if current[i] != target[i]:
            # Encontra onde target[i] está em current
            for j in range(i + 1, n):
                if current[j] == target[i]:
                    swaps.append((i, j))
                    current[i], current[j] = current[j], current[i]
                    break

    return swaps


def update_velocity(
    current_velocity: List[Tuple[int, int]],
    position: List[int],
    pbest: List[int],
    gbest: List[int],
    w: float,
    c1: float,
    c2: float,
    rng: np.random.RandomState
) -> List[Tuple[int, int]]:
    """
    Atualiza a velocidade da partícula no domínio discreto.

    Args:
        current_velocity: Velocidade atual (lista de swaps).
        position: Posição atual (permutação).
        pbest: Melhor posição pessoal.
        gbest: Melhor posição global.
        w: Fator de inércia.
        c1: Coeficiente cognitivo.
        c2: Coeficiente social.
        rng: Gerador de números aleatórios.

    Returns:
        Nova velocidade (lista de swaps).
    """
    new_velocity = []

    # Componente de inércia: manter fração w das swaps anteriores
    for swap in current_velocity:
        if rng.random() < w:
            new_velocity.append(swap)

    # Componente cognitivo: swaps para ir em direção ao pBest
    cognitive_swaps = compute_swap_sequence(position, pbest)
    r1 = rng.random()
    for swap in cognitive_swaps:
        if rng.random() < c1 * r1:
            new_velocity.append(swap)

    # Componente social: swaps para ir em direção ao gBest
    social_swaps = compute_swap_sequence(position, gbest)
    r2 = rng.random()
    for swap in social_swaps:
        if rng.random() < c2 * r2:
            new_velocity.append(swap)

    return new_velocity
