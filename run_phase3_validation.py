"""
Fase 3.3: Validação com variações algorítmicas.

Testa variações: inércia adaptativa, 3-opt, 2-opt+3-opt, sem busca local.
30 execuções por variação, em todas as instâncias.
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
    'fri26.tsp',
    'dantzig42.tsp',
    'berlin52.tsp',
]

NUM_RUNS = 30


def get_best_params():
    """Carrega melhores parâmetros da fase 2, ou usa defaults."""
    results_path = Path(__file__).parent / 'results' / 'phase2_combinations_latest.json'

    if results_path.exists():
        with open(results_path) as f:
            data = json.load(f)

        # Encontrar a config com melhor average na instância dantzig42
        best = None
        for entry in data:
            if entry['instance_name'].lower() in ('dantzig42', 'dantzig42.tsp'):
                if best is None or entry['average'] < best['average']:
                    best = entry

        if best:
            p = best['config_params']
            return p.get('num_particles', 50), p.get('max_iterations', 500), \
                   p.get('c1', 2.0), p.get('c2', 2.0)

    return 50, 500, 2.0, 2.0


def main():
    print("=" * 60)
    print("VALIDAÇÃO - Variações Algorítmicas")
    print(f"{NUM_RUNS} runs por variação, {len(INSTANCES)} instâncias")
    print("=" * 60)

    instances_dir = str(Path(__file__).parent / 'tsplib' / 'instances')
    results_dir = str(Path(__file__).parent / 'results')
    runner = ExperimentRunner(instances_dir, results_dir)

    n_particles, max_iter, c1, c2 = get_best_params()
    print(f"Parâmetros base: n={n_particles}, iter={max_iter}, c1={c1}, c2={c2}")

    variations = [
        {
            'name': 'baseline_2opt',
            'config': PSOConfig(
                num_particles=n_particles, max_iterations=max_iter,
                w=0.8, c1=c1, c2=c2,
                local_search_strategy='2opt',
            ),
        },
        {
            'name': 'adaptive_inertia',
            'config': PSOConfig(
                num_particles=n_particles, max_iterations=max_iter,
                w=0.8, c1=c1, c2=c2,
                adaptive_inertia=True, w_max=0.9, w_min=0.4,
                local_search_strategy='2opt',
            ),
        },
        {
            'name': '3opt_only',
            'config': PSOConfig(
                num_particles=n_particles, max_iterations=max_iter,
                w=0.8, c1=c1, c2=c2,
                local_search_strategy='3opt',
            ),
        },
        {
            'name': '2opt_then_3opt',
            'config': PSOConfig(
                num_particles=n_particles, max_iterations=max_iter,
                w=0.8, c1=c1, c2=c2,
                local_search_strategy='2opt_then_3opt',
                transition_fraction=0.5,
            ),
        },
        {
            'name': 'no_local_search',
            'config': PSOConfig(
                num_particles=n_particles, max_iterations=max_iter,
                w=0.8, c1=c1, c2=c2,
                local_search_strategy='none',
            ),
        },
    ]

    all_results = []

    for var in variations:
        print(f"\n{'='*60}")
        print(f"Variação: {var['name']}")
        print('='*60)

        for filename in INSTANCES:
            print(f"\n  Instância: {filename}")
            try:
                instance = runner.load_instance(filename)
                result = runner.run_experiment(
                    instance, var['config'],
                    config_name=var['name'],
                    num_runs=NUM_RUNS,
                    verbose=True,
                )
                all_results.append(result)

                gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
                print(f"    Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

            except Exception as e:
                print(f"    ERRO: {e}")

    if all_results:
        runner.save_results(all_results, 'phase3_validation')
        generate_report(all_results)


def generate_report(results):
    """Gera o relatório de validação."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    lines = [
        "# Relatório de Validação - Variações Algorítmicas",
        "",
        "## Variações Testadas",
        "",
        "| Variação | Descrição |",
        "|----------|-----------|",
        "| baseline_2opt | PSO padrão com 2-opt |",
        "| adaptive_inertia | w decrescendo de 0.9 a 0.4 |",
        "| 3opt_only | Substituir 2-opt por 3-opt |",
        "| 2opt_then_3opt | 2-opt nas primeiras iterações, 3-opt nas finais |",
        "| no_local_search | Sem busca local |",
        "",
        "## Resultados por Instância",
        "",
    ]

    instance_names = sorted(set(r.instance_name for r in results))
    for inst_name in instance_names:
        inst_results = [r for r in results if r.instance_name == inst_name]
        if not inst_results:
            continue

        opt = inst_results[0].optimal_value
        opt_str = f"{opt:.0f}" if opt else "N/A"

        lines.extend([
            f"### {inst_name} (Ótimo: {opt_str})",
            "",
            "| Variação | Best | Average | Worst | Std | Gap% | Tempo (s) |",
            "|----------|------|---------|-------|-----|------|-----------|",
        ])

        sorted_results = sorted(inst_results, key=lambda r: r.average)
        for r in sorted_results:
            gap_str = f"{r.gap_percentage:.2f}" if r.gap_percentage is not None else "N/A"
            lines.append(
                f"| {r.config_name} | {r.best:.2f} | {r.average:.2f} | "
                f"{r.worst:.2f} | {r.std:.2f} | {gap_str} | {r.avg_time:.2f} |"
            )

        lines.append("")

    # Análise
    lines.extend([
        "## Análise",
        "",
        "### Contribuição da Busca Local",
        "",
        "Comparar 'no_local_search' com as variantes que usam busca local "
        "para avaliar a contribuição da busca local.",
        "",
        "### Inércia Adaptativa",
        "",
        "Comparar 'adaptive_inertia' com 'baseline_2opt' para avaliar se "
        "a redução linear da inércia melhora a convergência.",
        "",
        "### 3-opt vs 2-opt",
        "",
        "Comparar '3opt_only' e '2opt_then_3opt' com 'baseline_2opt' para "
        "avaliar o trade-off qualidade vs tempo.",
    ])

    report_path = reports_dir / 'validation_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório gerado em {report_path}")


if __name__ == "__main__":
    main()
