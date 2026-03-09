"""
Fase 3.2: Melhores combinações de parâmetros.

Combina os melhores valores identificados na análise de sensibilidade.
30 execuções por combinação, testando em todas as instâncias.
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import PSOConfig
from experiments.runner import ExperimentRunner
from experiments.statistics import ExperimentStatistics


INSTANCES = [
    'fri26.tsp',
    'dantzig42.tsp',
    'berlin52.tsp',
]

NUM_RUNS = 30


def load_sensitivity_results():
    """Carrega resultados da fase de sensibilidade para determinar melhores valores."""
    results_path = Path(__file__).parent / 'results' / 'phase1_sensitivity_latest.json'

    if not results_path.exists():
        print("Resultados da Fase 1 não encontrados. Usando valores padrão otimizados.")
        return None

    with open(results_path) as f:
        data = json.load(f)

    # Encontrar melhores valores por parâmetro
    best_by_param = {}
    for entry in data:
        config_name = entry['config_name']
        param_name, value_str = config_name.split('=')
        avg = entry['average']

        if param_name not in best_by_param or avg < best_by_param[param_name][1]:
            best_by_param[param_name] = (value_str, avg)

    return best_by_param


def get_combinations():
    """Define as combinações a testar."""
    sensitivity = load_sensitivity_results()

    if sensitivity:
        # Usar melhores valores da sensibilidade
        best_n = int(float(sensitivity.get('num_particles', ('50', 0))[0]))
        best_iter = int(float(sensitivity.get('max_iterations', ('500', 0))[0]))
        best_w = float(sensitivity.get('w', ('0.8', 0))[0])
        best_c1 = float(sensitivity.get('c1', ('2.0', 0))[0])
        best_c2 = float(sensitivity.get('c2', ('2.0', 0))[0])

        print(f"Melhores valores da sensibilidade: n={best_n}, iter={best_iter}, "
              f"w={best_w}, c1={best_c1}, c2={best_c2}")
    else:
        best_n, best_iter, best_w, best_c1, best_c2 = 50, 500, 0.8, 2.0, 2.0

    combinations = [
        {
            'name': 'combo1_best_all',
            'num_particles': best_n,
            'max_iterations': best_iter,
            'w': best_w,
            'c1': best_c1,
            'c2': best_c2,
        },
        {
            'name': 'combo2_large_swarm',
            'num_particles': 200,
            'max_iterations': best_iter,
            'w': best_w,
            'c1': best_c1,
            'c2': best_c2,
        },
        {
            'name': 'combo3_long_run',
            'num_particles': best_n,
            'max_iterations': 1000,
            'w': best_w,
            'c1': best_c1,
            'c2': best_c2,
        },
    ]

    return combinations


def main():
    print("=" * 60)
    print("MELHORES COMBINAÇÕES DE PARÂMETROS")
    print(f"{NUM_RUNS} runs por combinação, {len(INSTANCES)} instâncias")
    print("=" * 60)

    instances_dir = str(Path(__file__).parent / 'tsplib' / 'instances')
    results_dir = str(Path(__file__).parent / 'results')
    runner = ExperimentRunner(instances_dir, results_dir)

    combinations = get_combinations()
    all_results = []

    for combo in combinations:
        print(f"\n{'='*60}")
        print(f"Combinação: {combo['name']}")
        print(f"  n={combo['num_particles']}, iter={combo['max_iterations']}, "
              f"w={combo['w']}, c1={combo['c1']}, c2={combo['c2']}")
        print('='*60)

        config = PSOConfig(
            num_particles=combo['num_particles'],
            max_iterations=combo['max_iterations'],
            w=combo['w'],
            c1=combo['c1'],
            c2=combo['c2'],
            local_search_strategy='2opt',
        )

        for filename in INSTANCES:
            print(f"\n  Instância: {filename}")
            try:
                instance = runner.load_instance(filename)
                result = runner.run_experiment(
                    instance, config,
                    config_name=combo['name'],
                    num_runs=NUM_RUNS,
                    verbose=True,
                )
                all_results.append(result)

                gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
                print(f"    Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

            except Exception as e:
                print(f"    ERRO: {e}")

    if all_results:
        runner.save_results(all_results, 'phase2_combinations')
        generate_report(all_results)


def generate_report(results):
    """Gera o relatório de combinações."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    lines = [
        "# Relatório de Combinações de Parâmetros",
        "",
        "## Configuração",
        "",
        f"- **Execuções por combinação**: {NUM_RUNS}",
        f"- **Instâncias**: {', '.join(INSTANCES)}",
        "",
        "## Resultados por Instância",
        "",
    ]

    # Agrupar por instância
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
            "| Rank | Configuração | Best | Average | Worst | Std | Gap% |",
            "|------|-------------|------|---------|-------|-----|------|",
        ])

        sorted_results = sorted(inst_results, key=lambda r: r.average)
        for rank, r in enumerate(sorted_results, 1):
            gap_str = f"{r.gap_percentage:.2f}" if r.gap_percentage is not None else "N/A"
            lines.append(
                f"| {rank} | {r.config_name} | {r.best:.2f} | {r.average:.2f} | "
                f"{r.worst:.2f} | {r.std:.2f} | {gap_str} |"
            )

        lines.append("")

    # Comparação com baseline
    lines.extend([
        "## Comparação com Baseline",
        "",
        "Os resultados acima devem ser comparados com o baseline_benchmark_report.md",
        "para avaliar a melhoria obtida com a otimização de parâmetros.",
    ])

    report_path = reports_dir / 'combinations_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório gerado em {report_path}")


if __name__ == "__main__":
    main()
