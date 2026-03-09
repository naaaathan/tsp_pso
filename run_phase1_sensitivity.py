"""
Fase 3.1: Análise de sensibilidade de parâmetros.

Varia um parâmetro por vez, mantendo os demais no baseline.
10 execuções por configuração. Instância de teste: dantzig42.
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import product

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import PSOConfig
from experiments.runner import ExperimentRunner


INSTANCE_FILE = 'dantzig42.tsp'
NUM_RUNS = 10

# Baseline
BASELINE = {
    'num_particles': 30,
    'max_iterations': 100,
    'w': 0.8,
    'c1': 2.0,
    'c2': 2.0,
}

# Valores a testar para cada parâmetro
SENSITIVITY = {
    'num_particles': [20, 30, 50, 100, 200],
    'max_iterations': [100, 200, 500, 1000],
    'w': [0.4, 0.6, 0.8, 0.9, 1.0],
    'c1': [1.0, 1.5, 2.0, 2.5, 3.0],
    'c2': [1.0, 1.5, 2.0, 2.5, 3.0],
}


def main():
    print("=" * 60)
    print("ANÁLISE DE SENSIBILIDADE DE PARÂMETROS")
    print(f"Instância: {INSTANCE_FILE}, {NUM_RUNS} runs por config")
    print("=" * 60)

    instances_dir = str(Path(__file__).parent / 'tsplib' / 'instances')
    results_dir = str(Path(__file__).parent / 'results')
    runner = ExperimentRunner(instances_dir, results_dir)

    instance = runner.load_instance(INSTANCE_FILE)
    all_results = []
    total_configs = sum(len(v) for v in SENSITIVITY.values())
    config_count = 0

    for param_name, values in SENSITIVITY.items():
        print(f"\n{'='*60}")
        print(f"Parâmetro: {param_name}")
        print('='*60)

        for value in values:
            config_count += 1
            # Criar config variando apenas este parâmetro
            params = dict(BASELINE)
            params[param_name] = value

            config_name = f"{param_name}={value}"
            print(f"\n  [{config_count}/{total_configs}] {config_name}")

            config = PSOConfig(
                num_particles=params['num_particles'],
                max_iterations=params['max_iterations'],
                w=params['w'],
                c1=params['c1'],
                c2=params['c2'],
                local_search_strategy='2opt',
            )

            result = runner.run_experiment(
                instance, config,
                config_name=config_name,
                num_runs=NUM_RUNS,
                verbose=True,
            )
            all_results.append(result)

            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"    Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

    # Salvar resultados
    if all_results:
        runner.save_results(all_results, 'phase1_sensitivity')
        generate_report(all_results)


def generate_report(results):
    """Gera o relatório de sensibilidade."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    lines = [
        "# Relatório de Análise de Sensibilidade",
        "",
        "## Configuração",
        "",
        f"- **Instância**: {INSTANCE_FILE}",
        f"- **Execuções por configuração**: {NUM_RUNS}",
        f"- **Baseline**: n={BASELINE['num_particles']}, iter={BASELINE['max_iterations']}, "
        f"w={BASELINE['w']}, c1={BASELINE['c1']}, c2={BASELINE['c2']}",
        "",
    ]

    # Agrupar por parâmetro
    for param_name in SENSITIVITY:
        param_results = [r for r in results if r.config_name.startswith(param_name)]
        if not param_results:
            continue

        lines.extend([
            f"## Parâmetro: {param_name}",
            "",
            "| Valor | Best | Average | Std | Gap% |",
            "|-------|------|---------|-----|------|",
        ])

        best_config = min(param_results, key=lambda r: r.average)

        for r in param_results:
            gap_str = f"{r.gap_percentage:.2f}" if r.gap_percentage is not None else "N/A"
            marker = " **" if r == best_config else ""
            lines.append(
                f"| {r.config_name.split('=')[1]}{marker} | "
                f"{r.best:.2f} | {r.average:.2f} | {r.std:.2f} | {gap_str} |"
            )

        lines.extend([
            "",
            f"**Melhor valor**: {best_config.config_name} "
            f"(Avg={best_config.average:.2f})",
            "",
        ])

    # Resumo
    lines.extend([
        "## Resumo",
        "",
        "| Parâmetro | Melhor Valor | Best | Average | Gap% |",
        "|-----------|-------------|------|---------|------|",
    ])

    for param_name in SENSITIVITY:
        param_results = [r for r in results if r.config_name.startswith(param_name)]
        if param_results:
            best = min(param_results, key=lambda r: r.average)
            gap_str = f"{best.gap_percentage:.2f}" if best.gap_percentage is not None else "N/A"
            lines.append(
                f"| {param_name} | {best.config_name.split('=')[1]} | "
                f"{best.best:.2f} | {best.average:.2f} | {gap_str} |"
            )

    report_path = reports_dir / 'sensitivity_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório gerado em {report_path}")


if __name__ == "__main__":
    main()
