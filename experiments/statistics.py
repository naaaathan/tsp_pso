"""
Análise estatística para experimentos do PSO-TSP.
"""

import numpy as np
from typing import Dict, List, Optional


class ExperimentStatistics:
    """Medidas estatísticas para resultados de experimentos."""

    @staticmethod
    def compute_statistics(values: List[float]) -> Dict[str, float]:
        """Calcula estatísticas básicas para uma lista de valores."""
        return {
            'best': min(values),
            'worst': max(values),
            'average': float(np.mean(values)),
            'std': float(np.std(values)),
            'median': float(np.median(values)),
            'q1': float(np.percentile(values, 25)),
            'q3': float(np.percentile(values, 75)),
        }

    @staticmethod
    def compute_gap(obtained: float, optimal: float) -> float:
        """Calcula o gap percentual em relação à solução ótima."""
        if optimal == 0:
            return 0.0
        return ((obtained - optimal) / optimal) * 100
