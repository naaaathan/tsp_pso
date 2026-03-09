"""Módulo PSO para o Problema do Caixeiro Viajante."""

from .particle import Particle
from .swarm import Swarm, PSOConfig, PSOResult
from .fitness import FitnessCalculator
from .velocity import compute_swap_sequence, update_velocity
from .position_update import update_position
from .local_search import two_opt, three_opt

__all__ = [
    'Particle', 'Swarm', 'PSOConfig', 'PSOResult',
    'FitnessCalculator',
    'compute_swap_sequence', 'update_velocity',
    'update_position',
    'two_opt', 'three_opt',
]
