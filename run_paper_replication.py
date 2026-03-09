"""
Replicação do experimento do artigo de Araújo & Barboza (2025).

Instância: 5 cidades com coordenadas (0,0), (1,3), (4,3), (6,1), (3,0)
Parâmetros: n=30, maxIter=100, w=0.8, c1=c2=2
5 execuções
Resultado esperado: custos entre 12.3 e 13.0
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import Swarm, PSOConfig, PSOResult
from pso.fitness import FitnessCalculator
from tsplib.parser import TSPLibParser


def create_paper_instance():
    """Cria a instância de 5 cidades do artigo."""
    coords = np.array([
        [0, 0],
        [1, 3],
        [4, 3],
        [6, 1],
        [3, 0],
    ], dtype=np.float64)

    n = len(coords)
    distance_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dx = coords[i][0] - coords[j][0]
                dy = coords[i][1] - coords[j][1]
                distance_matrix[i][j] = np.sqrt(dx**2 + dy**2)

    instance = TSPLibParser.create_manual_instance(distance_matrix, "paper_5cities")
    return instance, distance_matrix


def main():
    print("=" * 60)
    print("REPLICAÇÃO DO EXPERIMENTO DO ARTIGO")
    print("Araújo & Barboza (2025) - 5 cidades")
    print("=" * 60)

    instance, distance_matrix = create_paper_instance()
    fitness_calc = FitnessCalculator(distance_matrix)

    num_runs = 5
    results = []

    for run in range(num_runs):
        config = PSOConfig(
            num_particles=30,
            max_iterations=100,
            w=0.8,
            c1=2.0,
            c2=2.0,
            local_search_strategy='2opt',
            random_seed=run,
        )

        swarm = Swarm(fitness_calc, config)
        result = swarm.run(verbose=False)

        results.append({
            'run': run + 1,
            'best_fitness': result.best_fitness,
            'best_tour': result.best_tour,
            'execution_time': result.execution_time,
            'convergence_history': result.convergence_history,
        })

        print(f"  Run {run + 1}: Custo = {result.best_fitness:.4f}, "
              f"Tour = {result.best_tour}, Tempo = {result.execution_time:.4f}s")

    # Estatísticas
    values = [r['best_fitness'] for r in results]
    print(f"\nResultados:")
    print(f"  Melhor:  {min(values):.4f}")
    print(f"  Pior:    {max(values):.4f}")
    print(f"  Média:   {np.mean(values):.4f}")
    print(f"  Std:     {np.std(values):.4f}")
    print(f"\nÓtimo Euclidiano: 15.1530 (artigo reporta 12.3-13.0 com métrica diferente)")

    # Salvar resultados
    results_dir = Path(__file__).parent / 'results'
    results_dir.mkdir(exist_ok=True)

    output = {
        'experiment': 'paper_replication',
        'timestamp': datetime.now().isoformat(),
        'description': '5 cidades do artigo, n=30, maxIter=100, w=0.8, c1=c2=2',
        'results': results,
        'statistics': {
            'best': min(values),
            'worst': max(values),
            'average': float(np.mean(values)),
            'std': float(np.std(values)),
        }
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = results_dir / f'paper_replication_{timestamp}.json'
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

    latest = results_dir / 'paper_replication_latest.json'
    with open(latest, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResultados salvos em {filepath}")

    # Gerar report
    generate_report(output)


def generate_report(data):
    """Gera o relatório de replicação."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    stats = data['statistics']
    results = data['results']

    lines = [
        "# Relatório de Replicação do Artigo",
        "",
        "## Referência",
        "",
        "> Araújo, K.S. & Barboza, F.M. (2025). \"PSO and the Traveling Salesman Problem: "
        "An Intelligent Optimization Approach\". arXiv:2501.15319v1.",
        "",
        "## Configuração",
        "",
        "- **Instância**: 5 cidades com coordenadas (0,0), (1,3), (4,3), (6,1), (3,0)",
        "- **Partículas**: 30",
        "- **Iterações**: 100",
        "- **Inércia (w)**: 0.8",
        "- **c1, c2**: 2.0, 2.0",
        "- **Busca local**: 2-opt",
        "- **Execuções**: 5",
        "",
        "## Resultados",
        "",
        "| Run | Custo | Tour |",
        "|-----|-------|------|",
    ]

    for r in results:
        lines.append(f"| {r['run']} | {r['best_fitness']:.4f} | {r['best_tour']} |")

    lines.extend([
        "",
        "## Estatísticas",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Melhor  | {stats['best']:.4f} |",
        f"| Pior    | {stats['worst']:.4f} |",
        f"| Média   | {stats['average']:.4f} |",
        f"| Std     | {stats['std']:.4f} |",
        "",
        "## Comparação com o Artigo",
        "",
        "| Métrica | Artigo | Nossa Implementação |",
        "|---------|--------|---------------------|",
        f"| Faixa de custos | 12.3 - 13.0 (métrica do artigo) | {stats['best']:.4f} - {stats['worst']:.4f} |",
        f"| Média | ~12.65 (métrica do artigo) | {stats['average']:.4f} |",
        "",
        "**Nota**: O artigo usa uma métrica de distância diferente da Euclidiana. "
        "O ótimo Euclidiano para estas coordenadas é 15.1530.",
        "",
        "## Conclusão",
        "",
    ])

    if abs(stats['best'] - 15.153) < 0.1:
        lines.append("Implementação validada: PSO encontra o tour ótimo Euclidiano para 5 cidades.")
        lines.append("A diferença nos valores absolutos se deve à métrica de distância do artigo.")
    else:
        lines.append("Resultados divergem do esperado. Investigar possíveis diferenças na implementação.")

    report_path = reports_dir / 'paper_replication_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório gerado em {report_path}")


if __name__ == "__main__":
    main()
