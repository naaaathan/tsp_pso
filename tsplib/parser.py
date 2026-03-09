"""
Parser para arquivos no formato TSPLIB.

TSPLIB e uma biblioteca de instancias de exemplo para o TSP e problemas relacionados.
Este parser lida com instancias de TSP simetrico e assimetrico.

Referencia: http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple
import re


class TSPInstance:
    """
    Representa uma instancia TSP da TSPLIB.
    """

    def __init__(self):
        self.name: str = ""
        self.comment: str = ""
        self.type: str = ""  # TSP, ATSP, etc.
        self.dimension: int = 0
        self.edge_weight_type: str = ""
        self.edge_weight_format: str = ""
        self.coordinates: Optional[np.ndarray] = None
        self.distance_matrix: Optional[np.ndarray] = None
        self.optimal_value: Optional[float] = None

    def get_distance_matrix(self) -> np.ndarray:
        """
        Obtem a matriz de distancias para esta instancia.
        Calcula a partir das coordenadas se nao foi fornecida explicitamente.
        """
        if self.distance_matrix is not None:
            return self.distance_matrix

        if self.coordinates is not None:
            return self._compute_distance_matrix()

        raise ValueError("Nenhuma informacao de distancia disponivel")

    def _compute_distance_matrix(self) -> np.ndarray:
        """Calcula a matriz de distancias a partir das coordenadas."""
        n = self.dimension
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self._compute_distance(
                        self.coordinates[i],
                        self.coordinates[j]
                    )

        self.distance_matrix = matrix
        return matrix

    def _compute_distance(self, coord1: np.ndarray, coord2: np.ndarray) -> float:
        """Calcula a distancia entre duas cidades com base no edge_weight_type."""
        if self.edge_weight_type == 'EUC_2D':
            dx = coord1[0] - coord2[0]
            dy = coord1[1] - coord2[1]
            return round(np.sqrt(dx**2 + dy**2))

        elif self.edge_weight_type == 'CEIL_2D':
            dx = coord1[0] - coord2[0]
            dy = coord1[1] - coord2[1]
            return int(np.ceil(np.sqrt(dx**2 + dy**2)))

        elif self.edge_weight_type == 'ATT':
            dx = coord1[0] - coord2[0]
            dy = coord1[1] - coord2[1]
            rij = np.sqrt((dx**2 + dy**2) / 10.0)
            tij = int(np.round(rij))
            if tij < rij:
                return tij + 1
            return tij

        elif self.edge_weight_type == 'GEO':
            return self._geo_distance(coord1, coord2)

        else:
            # Padrao: Euclidiana arredondada
            dx = coord1[0] - coord2[0]
            dy = coord1[1] - coord2[1]
            return round(np.sqrt(dx**2 + dy**2))

    def _geo_distance(self, coord1: np.ndarray, coord2: np.ndarray) -> int:
        """Calcula a distancia geografica."""
        PI = 3.141592
        RRR = 6378.388

        def to_radians(val):
            deg = int(val)
            min_val = val - deg
            return PI * (deg + 5.0 * min_val / 3.0) / 180.0

        lat1 = to_radians(coord1[0])
        lon1 = to_radians(coord1[1])
        lat2 = to_radians(coord2[0])
        lon2 = to_radians(coord2[1])

        q1 = np.cos(lon1 - lon2)
        q2 = np.cos(lat1 - lat2)
        q3 = np.cos(lat1 + lat2)

        return int(RRR * np.arccos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0)

    def __repr__(self) -> str:
        return f"TSPInstance(name='{self.name}', dimension={self.dimension}, type='{self.type}')"


class TSPLibParser:
    """
    Parser para arquivos no formato TSPLIB (.tsp e .atsp).
    """

    # Valores otimos conhecidos para instancias de benchmark
    OPTIMAL_VALUES = {
        'gr21': 2707,
        'fri26': 937,
        'dantzig42': 699,
        'ftv33': 1286,
        'ftv38': 1530,
        'ft53': 6905,
        'kro124p': 36230,
        'ftv170': 2755,
        'rbg323': 1326,
        'rbg358': 1163,
        'rbg403': 2465,
        'rbg443': 2720,
        'att48': 10628,
        'berlin52': 7542,
        'eil51': 426,
        'eil76': 538,
        'eil101': 629,
        'st70': 675,
        'pr76': 108159,
        'kroA100': 21282,
        'kroB100': 22141,
        'kroC100': 20749,
        'kroD100': 21294,
        'kroE100': 22068,
    }

    def __init__(self):
        self.instance: Optional[TSPInstance] = None

    def parse(self, filepath: str) -> TSPInstance:
        """
        Faz o parsing de um arquivo no formato TSPLIB.

        Args:
            filepath: Caminho para o arquivo .tsp ou .atsp.

        Returns:
            Objeto TSPInstance.
        """
        self.instance = TSPInstance()
        filepath = Path(filepath)

        with open(filepath, 'r') as f:
            content = f.read()

        lines = content.strip().split('\n')

        # Fazer parsing do cabecalho
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('NAME'):
                self.instance.name = self._parse_value(line)
            elif line.startswith('COMMENT'):
                self.instance.comment = self._parse_value(line)
            elif line.startswith('TYPE'):
                self.instance.type = self._parse_value(line)
            elif line.startswith('DIMENSION'):
                self.instance.dimension = int(self._parse_value(line))
            elif line.startswith('EDGE_WEIGHT_TYPE'):
                self.instance.edge_weight_type = self._parse_value(line)
            elif line.startswith('EDGE_WEIGHT_FORMAT'):
                self.instance.edge_weight_format = self._parse_value(line)
            elif line.startswith('NODE_COORD_SECTION'):
                i = self._parse_coordinates(lines, i + 1)
                continue
            elif line.startswith('EDGE_WEIGHT_SECTION'):
                i = self._parse_edge_weights(lines, i + 1)
                continue
            elif line == 'EOF':
                break

            i += 1

        # Definir valor otimo se conhecido
        name_lower = self.instance.name.lower()
        if name_lower in self.OPTIMAL_VALUES:
            self.instance.optimal_value = self.OPTIMAL_VALUES[name_lower]

        return self.instance

    def _parse_value(self, line: str) -> str:
        """Extrai o valor de uma linha do cabecalho."""
        if ':' in line:
            return line.split(':', 1)[1].strip()
        return line.split(None, 1)[1].strip() if len(line.split()) > 1 else ""

    def _parse_coordinates(self, lines: list, start_idx: int) -> int:
        """Faz o parsing da secao NODE_COORD_SECTION."""
        coords = []
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()
            if line == 'EOF' or line.startswith('EDGE_WEIGHT_SECTION') or not line:
                break

            parts = line.split()
            if len(parts) >= 3:
                # Formato: id_no x y
                x = float(parts[1])
                y = float(parts[2])
                coords.append([x, y])

            i += 1

        self.instance.coordinates = np.array(coords)
        return i

    def _parse_edge_weights(self, lines: list, start_idx: int) -> int:
        """Faz o parsing da secao EDGE_WEIGHT_SECTION."""
        n = self.instance.dimension
        format_type = self.instance.edge_weight_format

        # Coletar todos os numeros da secao
        numbers = []
        i = start_idx

        while i < len(lines):
            line = lines[i].strip()
            if line == 'EOF' or line.startswith('DISPLAY_DATA_SECTION') or not line:
                break

            # Extrair numeros da linha
            parts = line.split()
            for part in parts:
                try:
                    numbers.append(float(part))
                except ValueError:
                    break

            i += 1

        # Construir matriz de distancias com base no formato
        matrix = np.zeros((n, n))

        if format_type == 'FULL_MATRIX':
            idx = 0
            for row in range(n):
                for col in range(n):
                    matrix[row][col] = numbers[idx]
                    idx += 1

        elif format_type == 'UPPER_ROW':
            idx = 0
            for row in range(n):
                for col in range(row + 1, n):
                    matrix[row][col] = numbers[idx]
                    matrix[col][row] = numbers[idx]
                    idx += 1

        elif format_type == 'LOWER_ROW':
            idx = 0
            for row in range(1, n):
                for col in range(row):
                    matrix[row][col] = numbers[idx]
                    matrix[col][row] = numbers[idx]
                    idx += 1

        elif format_type == 'UPPER_DIAG_ROW':
            idx = 0
            for row in range(n):
                for col in range(row, n):
                    matrix[row][col] = numbers[idx]
                    if row != col:
                        matrix[col][row] = numbers[idx]
                    idx += 1

        elif format_type == 'LOWER_DIAG_ROW':
            idx = 0
            for row in range(n):
                for col in range(row + 1):
                    matrix[row][col] = numbers[idx]
                    if row != col:
                        matrix[col][row] = numbers[idx]
                    idx += 1

        else:
            # Tentar detectar automaticamente o formato para problemas assimetricos
            if len(numbers) == n * n:
                idx = 0
                for row in range(n):
                    for col in range(n):
                        matrix[row][col] = numbers[idx]
                        idx += 1

        self.instance.distance_matrix = matrix
        return i

    @staticmethod
    def create_manual_instance(distance_matrix: np.ndarray, name: str = "manual") -> TSPInstance:
        """
        Cria uma instancia TSP a partir de uma matriz de distancias manual.

        Args:
            distance_matrix: Matriz de distancias NxN.
            name: Nome para a instancia.

        Returns:
            Objeto TSPInstance.
        """
        instance = TSPInstance()
        instance.name = name
        instance.type = "TSP"
        instance.dimension = len(distance_matrix)
        instance.edge_weight_type = "EXPLICIT"
        instance.edge_weight_format = "FULL_MATRIX"
        instance.distance_matrix = distance_matrix.astype(np.float64)
        return instance
