"""
Benchmark baseline: parâmetros do artigo em instâncias TSPLIB.

Instâncias: fri26 (937), dantzig42 (699), berlin52 (7542)
Parâmetros: n=30, maxIter=100, w=0.8, c1=c2=2
30 execuções por instância
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import PSOConfig
from experiments.runner import ExperimentRunner


INSTANCES = [
    ('fri26.tsp', 'Pequena'),
    ('dantzig42.tsp', 'Média'),
    ('berlin52.tsp', 'Grande'),
]

NUM_RUNS = 30


def main():
    print("=" * 60)
    print("BENCHMARK BASELINE - Parâmetros do Artigo em TSPLIB")
    print("=" * 60)

    instances_dir = str(Path(__file__).parent / 'tsplib' / 'instances')
    results_dir = str(Path(__file__).parent / 'results')
    runner = ExperimentRunner(instances_dir, results_dir)

    config = PSOConfig(
        num_particles=30,
        max_iterations=100,
        w=0.8,
        c1=2.0,
        c2=2.0,
        local_search_strategy='2opt',
    )

    all_results = []

    for filename, category in INSTANCES:
        print(f"\n{'='*60}")
        print(f"Instância: {filename} ({category})")
        print('='*60)

        try:
            instance = runner.load_instance(filename)
            result = runner.run_experiment(
                instance, config,
                config_name='baseline_paper',
                num_runs=NUM_RUNS,
                verbose=True,
            )
            all_results.append(result)

            opt_str = f"{result.optimal_value:.0f}" if result.optimal_value else "N/A"
            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"\n  Resumo: Best={result.best:.2f}, Avg={result.average:.2f}, "
                  f"Worst={result.worst:.2f}, Std={result.std:.2f}")
            print(f"  Ótimo={opt_str}, Gap={gap_str}, Tempo médio={result.avg_time:.2f}s")

        except Exception as e:
            print(f"  ERRO: {e}")
            import traceback
            traceback.print_exc()

    # Salvar resultados
    if all_results:
        runner.save_results(all_results, 'baseline_benchmark')
        generate_report(all_results)


def generate_report(results):
    """Gera o relatório de benchmark baseline."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    lines = [
        "# Relatório de Benchmark Baseline",
        "",
        "## Configuração",
        "",
        "Parâmetros do artigo aplicados a instâncias TSPLIB:",
        "",
        "- **Partículas**: 30",
        "- **Iterações**: 100",
        "- **Inércia (w)**: 0.8",
        "- **c1, c2**: 2.0, 2.0",
        "- **Busca local**: 2-opt",
        f"- **Execuções**: {results[0].num_runs}",
        "",
        "## Resultados",
        "",
        "| Instância | N | Ótimo | Best | Worst | Average | Std | Median | Gap% | Tempo (s) |",
        "|-----------|---|-------|------|-------|---------|-----|--------|------|-----------|",
    ]

    for r in results:
        opt_str = f"{r.optimal_value:.0f}" if r.optimal_value else "N/A"
        gap_str = f"{r.gap_percentage:.2f}" if r.gap_percentage is not None else "N/A"
        lines.append(
            f"| {r.instance_name} | {r.num_cities} | {opt_str} | "
            f"{r.best:.2f} | {r.worst:.2f} | {r.average:.2f} | "
            f"{r.std:.2f} | {r.median:.2f} | {gap_str} | {r.avg_time:.2f} |"
        )

    lines.extend([
        "",
        "## Análise",
        "",
        "O PSO com parâmetros do artigo (projetados para 5 cidades) aplicado a instâncias "
        "reais da TSPLIB. Os gaps indicam o desempenho relativo ao ótimo conhecido.",
    ])

    report_path = reports_dir / 'baseline_benchmark_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório gerado em {report_path}")


if __name__ == "__main__":
    main()
