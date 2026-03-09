"""
Atualização de posição para o PSO discreto aplicado ao TSP.

Aplica a sequência de swaps (velocidade) à posição atual.
O resultado é sempre uma permutação válida, pois swaps preservam permutações.
"""

from typing import List, Tuple


def update_position(position: List[int], velocity: List[Tuple[int, int]]) -> List[int]:
    """
    Aplica a sequência de swaps à posição atual.

    Args:
        position: Posição atual (permutação de cidades).
        velocity: Lista de swaps a aplicar.

    Returns:
        Nova posição (permutação válida).
    """
    new_position = list(position)
    n = len(new_position)

    for i, j in velocity:
        # Garante índices válidos
        if 0 <= i < n and 0 <= j < n:
            new_position[i], new_position[j] = new_position[j], new_position[i]

    return new_position
