"""
Execução unificada de todos os experimentos PSO-TSP.

Pipeline: Paper Replication → Baseline → Phase 1 (Sensitivity) → Phase 2 (Combinations) → Phase 3 (Validation) → Visualizations
Cada fase alimenta a próxima com seus resultados.
"""

import sys
import os
import json
import time
import numpy as np
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import Swarm, PSOConfig
from pso.fitness import FitnessCalculator
from experiments.runner import ExperimentRunner
from tsplib.parser import TSPLibParser

INSTANCES_DIR = Path(__file__).parent / 'tsplib' / 'instances'
RESULTS_DIR = Path(__file__).parent / 'results'
REPORTS_DIR = Path(__file__).parent / 'reports'

TSPLIB_INSTANCES = ['fri26.tsp', 'dantzig42.tsp', 'berlin52.tsp']
SENSITIVITY_INSTANCE = 'dantzig42.tsp'

BASELINE_PARAMS = {
    'num_particles': 30,
    'max_iterations': 100,
    'w': 0.8,
    'c1': 2.0,
    'c2': 2.0,
}

SENSITIVITY = {
    'num_particles': [20, 30, 50, 100, 200],
    'max_iterations': [100, 200, 500, 1000],
    'w': [0.4, 0.6, 0.8, 0.9, 1.0],
    'c1': [1.0, 1.5, 2.0, 2.5, 3.0],
    'c2': [1.0, 1.5, 2.0, 2.5, 3.0],
}


class PhaseTimer:
    """Rastreia tempo por fase."""

    def __init__(self):
        self.phases: Dict[str, float] = {}
        self._start: float = 0
        self._current: str = ""
        self.global_start = time.time()

    def start(self, name: str):
        self._current = name
        self._start = time.time()
        print(f"\n{'#'*70}")
        print(f"# FASE: {name}")
        print(f"# Início: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'#'*70}\n")

    def stop(self):
        elapsed = time.time() - self._start
        self.phases[self._current] = elapsed
        m, s = divmod(elapsed, 60)
        print(f"\n>>> Fase '{self._current}' concluída em {int(m)}m {s:.1f}s")

    def summary(self):
        total = time.time() - self.global_start
        print(f"\n{'='*70}")
        print(f"RESUMO DE TEMPO")
        print(f"{'='*70}")
        for name, elapsed in self.phases.items():
            m, s = divmod(elapsed, 60)
            print(f"  {name:<40} {int(m):>3}m {s:>5.1f}s")
        m, s = divmod(total, 60)
        print(f"  {'TOTAL':<40} {int(m):>3}m {s:>5.1f}s")
        print(f"{'='*70}")
        return {name: round(t, 2) for name, t in self.phases.items()}, round(total, 2)


# ─────────────────────────── PHASE 0: Paper Replication ───────────────────────

def run_paper_replication(runner: ExperimentRunner) -> dict:
    coords = np.array([[0,0],[1,3],[4,3],[6,1],[3,0]], dtype=np.float64)
    n = len(coords)
    dm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dm[i][j] = np.sqrt((coords[i][0]-coords[j][0])**2 + (coords[i][1]-coords[j][1])**2)

    fc = FitnessCalculator(dm)
    results = []

    for run in range(5):
        config = PSOConfig(num_particles=30, max_iterations=100, w=0.8, c1=2.0, c2=2.0,
                           local_search_strategy='2opt', random_seed=run)
        result = Swarm(fc, config).run()
        results.append({'run': run+1, 'best_fitness': result.best_fitness,
                        'best_tour': result.best_tour, 'execution_time': result.execution_time})
        print(f"  Run {run+1}: Custo = {result.best_fitness:.4f}")

    values = [r['best_fitness'] for r in results]
    stats = {'best': min(values), 'worst': max(values),
             'average': float(np.mean(values)), 'std': float(np.std(values))}
    print(f"  Melhor={stats['best']:.4f}, Pior={stats['worst']:.4f}, Média={stats['average']:.4f}")

    output = {'experiment': 'paper_replication', 'timestamp': datetime.now().isoformat(),
              'results': results, 'statistics': stats}
    _save_json(output, 'paper_replication')
    return output


# ─────────────────────────── PHASE 1: Baseline Benchmark ─────────────────────

def run_baseline_benchmark(runner: ExperimentRunner) -> List:
    config = PSOConfig(**BASELINE_PARAMS, local_search_strategy='2opt')
    all_results = []

    for filename in TSPLIB_INSTANCES:
        print(f"\n  Instância: {filename}")
        instance = runner.load_instance(filename)
        result = runner.run_experiment(instance, config, config_name='baseline_paper',
                                       num_runs=30, verbose=True)
        all_results.append(result)
        gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
        print(f"  => Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

    runner.save_results(all_results, 'baseline_benchmark')
    return all_results


# ─────────────────────────── PHASE 2: Sensitivity Analysis ───────────────────

def run_sensitivity(runner: ExperimentRunner) -> Dict[str, Any]:
    instance = runner.load_instance(SENSITIVITY_INSTANCE)
    all_results = []
    best_by_param = {}

    total_configs = sum(len(v) for v in SENSITIVITY.values())
    config_count = 0

    for param_name, values in SENSITIVITY.items():
        print(f"\n  Parâmetro: {param_name}")
        param_results = []

        for value in values:
            config_count += 1
            params = dict(BASELINE_PARAMS)
            params[param_name] = value
            config_name = f"{param_name}={value}"

            config = PSOConfig(**params, local_search_strategy='2opt')
            result = runner.run_experiment(instance, config, config_name=config_name,
                                           num_runs=10, verbose=False)
            all_results.append(result)
            param_results.append(result)

            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"    [{config_count}/{total_configs}] {config_name}: "
                  f"Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

        # Melhor valor para este parâmetro (por average)
        best = min(param_results, key=lambda r: r.average)
        best_value = best.config_name.split('=')[1]
        best_by_param[param_name] = {
            'value': best_value, 'best': best.best, 'average': best.average,
            'gap': best.gap_percentage,
        }
        print(f"    ★ Melhor: {best.config_name} (Avg={best.average:.2f})")

    runner.save_results(all_results, 'phase1_sensitivity')

    print(f"\n  Resumo dos melhores valores:")
    for p, info in best_by_param.items():
        print(f"    {p} = {info['value']} (Avg={info['average']:.2f})")

    return best_by_param


# ─────────────────────────── PHASE 3: Combinations ───────────────────────────

def run_combinations(runner: ExperimentRunner, best_by_param: Dict) -> List:
    # Extrair melhores valores
    best_n = int(float(best_by_param.get('num_particles', {}).get('value', 50)))
    best_iter = int(float(best_by_param.get('max_iterations', {}).get('value', 500)))
    best_w = float(best_by_param.get('w', {}).get('value', 0.8))
    best_c1 = float(best_by_param.get('c1', {}).get('value', 2.0))
    best_c2 = float(best_by_param.get('c2', {}).get('value', 2.0))

    print(f"  Parâmetros otimizados: n={best_n}, iter={best_iter}, "
          f"w={best_w}, c1={best_c1}, c2={best_c2}")

    combinations = [
        ('combo1_best_all', PSOConfig(
            num_particles=best_n, max_iterations=best_iter,
            w=best_w, c1=best_c1, c2=best_c2, local_search_strategy='2opt')),
        ('combo2_large_swarm', PSOConfig(
            num_particles=200, max_iterations=best_iter,
            w=best_w, c1=best_c1, c2=best_c2, local_search_strategy='2opt')),
        ('combo3_long_run', PSOConfig(
            num_particles=best_n, max_iterations=1000,
            w=best_w, c1=best_c1, c2=best_c2, local_search_strategy='2opt')),
    ]

    all_results = []
    best_combo = {}  # por instância: melhor combo

    for combo_name, config in combinations:
        print(f"\n  Combinação: {combo_name}")
        for filename in TSPLIB_INSTANCES:
            instance = runner.load_instance(filename)
            result = runner.run_experiment(instance, config, config_name=combo_name,
                                           num_runs=30, verbose=False)
            all_results.append(result)

            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"    {filename}: Best={result.best:.2f}, Avg={result.average:.2f}, Gap={gap_str}")

            # Rastrear melhor combo por instância
            key = instance.name
            if key not in best_combo or result.average < best_combo[key]['average']:
                best_combo[key] = {
                    'combo_name': combo_name, 'average': result.average,
                    'config_params': {
                        'num_particles': config.num_particles,
                        'max_iterations': config.max_iterations,
                        'w': config.w, 'c1': config.c1, 'c2': config.c2,
                    }
                }

    runner.save_results(all_results, 'phase2_combinations')

    print(f"\n  Melhor combinação por instância:")
    for inst, info in best_combo.items():
        print(f"    {inst}: {info['combo_name']} (Avg={info['average']:.2f})")

    return all_results, best_combo


# ─────────────────────────── PHASE 4: Validation ─────────────────────────────

def run_validation(runner: ExperimentRunner, best_combo: Dict) -> List:
    # Usar parâmetros do melhor combo overall (dantzig42 como referência)
    ref = best_combo.get('dantzig42', best_combo.get(list(best_combo.keys())[0]))
    p = ref['config_params']
    n_particles = p['num_particles']
    max_iter = p['max_iterations']
    c1, c2 = p['c1'], p['c2']

    print(f"  Parâmetros base: n={n_particles}, iter={max_iter}, c1={c1}, c2={c2}")

    variations = [
        ('baseline_2opt', PSOConfig(
            num_particles=n_particles, max_iterations=max_iter,
            w=0.8, c1=c1, c2=c2, local_search_strategy='2opt')),
        ('adaptive_inertia', PSOConfig(
            num_particles=n_particles, max_iterations=max_iter,
            w=0.8, c1=c1, c2=c2, adaptive_inertia=True, w_max=0.9, w_min=0.4,
            local_search_strategy='2opt')),
        ('3opt_only', PSOConfig(
            num_particles=n_particles, max_iterations=max_iter,
            w=0.8, c1=c1, c2=c2, local_search_strategy='3opt')),
        ('2opt_then_3opt', PSOConfig(
            num_particles=n_particles, max_iterations=max_iter,
            w=0.8, c1=c1, c2=c2, local_search_strategy='2opt_then_3opt',
            transition_fraction=0.5)),
        ('no_local_search', PSOConfig(
            num_particles=n_particles, max_iterations=max_iter,
            w=0.8, c1=c1, c2=c2, local_search_strategy='none')),
    ]

    all_results = []

    for var_name, config in variations:
        print(f"\n  Variação: {var_name}")
        for filename in TSPLIB_INSTANCES:
            instance = runner.load_instance(filename)
            result = runner.run_experiment(instance, config, config_name=var_name,
                                           num_runs=30, verbose=False)
            all_results.append(result)

            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"    {filename}: Best={result.best:.2f}, Avg={result.average:.2f}, "
                  f"Std={result.std:.2f}, Gap={gap_str}, T={result.avg_time:.1f}s")

    runner.save_results(all_results, 'phase3_validation')
    return all_results


# ─────────────────────────── PHASE 5: Reports & Visualizations ───────────────

def generate_all_reports(timer: PhaseTimer):
    """Gera todos os relatórios e gráficos a partir dos JSONs salvos."""
    REPORTS_DIR.mkdir(exist_ok=True)

    baseline_data = _load_json('baseline_benchmark_latest.json')
    sensitivity_data = _load_json('phase1_sensitivity_latest.json')
    combinations_data = _load_json('phase2_combinations_latest.json')
    validation_data = _load_json('phase3_validation_latest.json')
    paper_data = _load_json('paper_replication_latest.json')

    # ── Sensitivity Report ──
    if sensitivity_data:
        _generate_sensitivity_report(sensitivity_data)

    # ── Combinations Report ──
    if combinations_data:
        _generate_combinations_report(combinations_data, baseline_data)

    # ── Validation Report ──
    if validation_data:
        _generate_validation_report(validation_data)

    # ── Final Consolidated Report ──
    _generate_final_report(paper_data, baseline_data, sensitivity_data,
                           combinations_data, validation_data, timer)

    # ── Gráficos ──
    _generate_plots(baseline_data, sensitivity_data, validation_data)


def _generate_sensitivity_report(data):
    lines = [
        "# Relatório de Análise de Sensibilidade",
        "",
        f"- **Instância**: {SENSITIVITY_INSTANCE}",
        f"- **Runs por config**: 10",
        f"- **Baseline**: n={BASELINE_PARAMS['num_particles']}, iter={BASELINE_PARAMS['max_iterations']}, "
        f"w={BASELINE_PARAMS['w']}, c1={BASELINE_PARAMS['c1']}, c2={BASELINE_PARAMS['c2']}",
        "",
    ]

    for param_name in SENSITIVITY:
        param_results = [e for e in data if e['config_name'].startswith(param_name + '=')]
        if not param_results:
            continue

        lines.extend([f"## Parâmetro: {param_name}", "",
                      "| Valor | Best | Average | Std | Gap% |",
                      "|-------|------|---------|-----|------|"])

        best_entry = min(param_results, key=lambda e: e['average'])
        for e in param_results:
            val = e['config_name'].split('=')[1]
            gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            marker = " ★" if e is best_entry else ""
            lines.append(f"| {val}{marker} | {e['best']:.2f} | {e['average']:.2f} | "
                         f"{e['std']:.2f} | {gap} |")
        lines.append("")

    _write_report('sensitivity_report.md', lines)


def _generate_combinations_report(data, baseline_data):
    lines = ["# Relatório de Combinações de Parâmetros", "", "## Resultados por Instância", ""]

    instance_names = sorted(set(e['instance_name'] for e in data))
    for inst_name in instance_names:
        inst_results = [e for e in data if e['instance_name'] == inst_name]
        opt = inst_results[0].get('optimal_value')
        opt_str = f"{opt:.0f}" if opt else "N/A"

        # Incluir baseline para comparação
        baseline_entry = None
        if baseline_data:
            baseline_entry = next((e for e in baseline_data if e['instance_name'] == inst_name), None)

        lines.extend([f"### {inst_name} (Ótimo: {opt_str})", "",
                      "| Rank | Configuração | Best | Average | Worst | Std | Gap% |",
                      "|------|-------------|------|---------|-------|-----|------|"])

        all_entries = list(inst_results)
        if baseline_entry:
            all_entries.append(baseline_entry)

        for rank, e in enumerate(sorted(all_entries, key=lambda x: x['average']), 1):
            gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            lines.append(f"| {rank} | {e['config_name']} | {e['best']:.2f} | "
                         f"{e['average']:.2f} | {e['worst']:.2f} | {e['std']:.2f} | {gap} |")
        lines.append("")

    _write_report('combinations_report.md', lines)


def _generate_validation_report(data):
    lines = [
        "# Relatório de Validação - Variações Algorítmicas", "",
        "| Variação | Descrição |",
        "|----------|-----------|",
        "| baseline_2opt | PSO padrão com 2-opt |",
        "| adaptive_inertia | w decrescendo de 0.9 a 0.4 |",
        "| 3opt_only | Substituir 2-opt por 3-opt |",
        "| 2opt_then_3opt | 2-opt nas primeiras iterações, 3-opt nas finais |",
        "| no_local_search | Sem busca local |",
        "", "## Resultados por Instância", "",
    ]

    instance_names = sorted(set(e['instance_name'] for e in data))
    for inst_name in instance_names:
        inst_results = [e for e in data if e['instance_name'] == inst_name]
        opt = inst_results[0].get('optimal_value')
        opt_str = f"{opt:.0f}" if opt else "N/A"

        lines.extend([f"### {inst_name} (Ótimo: {opt_str})", "",
                      "| Variação | Best | Average | Worst | Std | Gap% | Tempo (s) |",
                      "|----------|------|---------|-------|-----|------|-----------|"])

        for e in sorted(inst_results, key=lambda x: x['average']):
            gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            lines.append(f"| {e['config_name']} | {e['best']:.2f} | {e['average']:.2f} | "
                         f"{e['worst']:.2f} | {e['std']:.2f} | {gap} | {e['avg_time']:.2f} |")
        lines.append("")

    _write_report('validation_report.md', lines)


def _generate_final_report(paper, baseline, sensitivity, combinations, validation, timer: PhaseTimer):
    lines = [
        "# Relatório Final - PSO para o TSP", "",
        "## 1. Replicação do Artigo", "",
    ]

    if paper:
        stats = paper.get('statistics', paper) if isinstance(paper, dict) else {}
        if stats:
            lines.extend([
                f"- 5 cidades: Melhor = {stats.get('best', 'N/A')}, "
                f"Média = {stats.get('average', 'N/A')}", ""
            ])

    # Baseline
    if baseline:
        lines.extend([
            "## 2. Baseline (Parâmetros do Artigo em TSPLIB)", "",
            "| Instância | N | Ótimo | Best | Average | Std | Gap% |",
            "|-----------|---|-------|------|---------|-----|------|",
        ])
        for e in baseline:
            opt = f"{e['optimal_value']:.0f}" if e.get('optimal_value') else "N/A"
            gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            lines.append(f"| {e['instance_name']} | {e['num_cities']} | {opt} | "
                         f"{e['best']:.2f} | {e['average']:.2f} | {e['std']:.2f} | {gap} |")
        lines.append("")

    # Sensitivity summary
    if sensitivity:
        lines.extend(["## 3. Análise de Sensibilidade", "",
                      "| Parâmetro | Melhor Valor | Average |",
                      "|-----------|-------------|---------|"])
        for param_name in SENSITIVITY:
            param_entries = [e for e in sensitivity if e['config_name'].startswith(param_name + '=')]
            if param_entries:
                best = min(param_entries, key=lambda e: e['average'])
                val = best['config_name'].split('=')[1]
                lines.append(f"| {param_name} | {val} | {best['average']:.2f} |")
        lines.append("")

    # Combinations summary
    if combinations:
        lines.extend(["## 4. Melhores Combinações", ""])
        instance_names = sorted(set(e['instance_name'] for e in combinations))
        for inst_name in instance_names:
            inst_results = [e for e in combinations if e['instance_name'] == inst_name]
            best = min(inst_results, key=lambda e: e['average'])
            gap = f"{best['gap_percentage']:.2f}%" if best.get('gap_percentage') is not None else "N/A"
            lines.append(f"- **{inst_name}**: {best['config_name']} → "
                         f"Best={best['best']:.2f}, Avg={best['average']:.2f}, Gap={gap}")
        lines.append("")

    # Validation summary
    if validation:
        lines.extend(["## 5. Variações Algorítmicas", ""])
        instance_names = sorted(set(e['instance_name'] for e in validation))
        for inst_name in instance_names:
            inst_results = [e for e in validation if e['instance_name'] == inst_name]
            lines.append(f"### {inst_name}")
            lines.extend(["", "| Variação | Best | Average | Gap% |",
                          "|----------|------|---------|------|"])
            for e in sorted(inst_results, key=lambda x: x['average']):
                gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                lines.append(f"| {e['config_name']} | {e['best']:.2f} | "
                             f"{e['average']:.2f} | {gap} |")
            lines.append("")

    # Comparação final: Baseline vs Melhor Otimizado
    if baseline and validation:
        lines.extend(["## 6. Comparação Final: Baseline vs Melhor Otimizado", "",
                      "| Instância | Baseline Avg | Otimizado Avg | Melhoria |",
                      "|-----------|-------------|---------------|----------|"])
        for be in baseline:
            inst = be['instance_name']
            val_inst = [e for e in validation if e['instance_name'] == inst]
            if val_inst:
                best_val = min(val_inst, key=lambda e: e['average'])
                improvement = be['average'] - best_val['average']
                pct = (improvement / be['average'] * 100) if be['average'] > 0 else 0
                lines.append(f"| {inst} | {be['average']:.2f} | "
                             f"{best_val['average']:.2f} ({best_val['config_name']}) | "
                             f"{pct:+.2f}% |")
        lines.append("")

    # Tempo
    phase_times, total = timer.summary()
    lines.extend(["## 7. Tempo de Execução", "",
                  "| Fase | Tempo |",
                  "|------|-------|"])
    for name, elapsed in timer.phases.items():
        m, s = divmod(elapsed, 60)
        lines.append(f"| {name} | {int(m)}m {s:.1f}s |")
    m, s = divmod(total, 60)
    lines.append(f"| **TOTAL** | **{int(m)}m {s:.1f}s** |")

    _write_report('final_report.md', lines)


def _generate_plots(baseline, sensitivity, validation):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib não disponível, pulando gráficos.")
        return

    fig_dir = RESULTS_DIR / 'figures'
    fig_dir.mkdir(exist_ok=True)

    # 1. Convergência: baseline vs validation
    if baseline and validation:
        instance_names = sorted(set(e['instance_name'] for e in baseline))
        for inst_name in instance_names:
            fig, ax = plt.subplots(figsize=(10, 6))

            be = next((e for e in baseline if e['instance_name'] == inst_name), None)
            if be and be.get('all_convergence'):
                avg_conv = _avg_convergence(be['all_convergence'])
                ax.plot(avg_conv, label='Baseline (artigo)', linewidth=2)

            val_inst = [e for e in validation if e['instance_name'] == inst_name]
            for ve in val_inst:
                if ve.get('all_convergence'):
                    avg_conv = _avg_convergence(ve['all_convergence'])
                    ax.plot(avg_conv, label=ve['config_name'], linewidth=1.5, alpha=0.8)

            ax.set_xlabel('Iteração')
            ax.set_ylabel('Melhor Fitness')
            ax.set_title(f'Convergência - {inst_name}')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            fig.savefig(fig_dir / f'convergence_{inst_name}.png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"  Salvo: convergence_{inst_name}.png")

    # 2. Box plots
    if validation:
        instance_names = sorted(set(e['instance_name'] for e in validation))
        for inst_name in instance_names:
            inst_data = [e for e in validation if e['instance_name'] == inst_name]
            if not inst_data:
                continue

            fig, ax = plt.subplots(figsize=(12, 6))
            labels = [e['config_name'] for e in inst_data]
            data = [e['all_values'] for e in inst_data]
            bp = ax.boxplot(data, labels=labels, patch_artist=True)
            colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)

            opt = inst_data[0].get('optimal_value')
            if opt:
                ax.axhline(y=opt, color='red', linestyle='--', label=f'Ótimo ({opt})', alpha=0.7)
                ax.legend()

            ax.set_ylabel('Fitness')
            ax.set_title(f'Distribuição - {inst_name}')
            ax.tick_params(axis='x', rotation=30)
            ax.grid(True, alpha=0.3, axis='y')
            fig.savefig(fig_dir / f'boxplot_{inst_name}.png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"  Salvo: boxplot_{inst_name}.png")

    # 3. Sensitivity bar chart
    if sensitivity:
        param_names = list(SENSITIVITY.keys())
        fig, axes = plt.subplots(1, len(param_names), figsize=(4 * len(param_names), 5))
        if len(param_names) == 1:
            axes = [axes]

        for ax, param_name in zip(axes, param_names):
            entries = [e for e in sensitivity if e['config_name'].startswith(param_name + '=')]
            if not entries:
                continue
            x_labels = [e['config_name'].split('=')[1] for e in entries]
            averages = [e['average'] for e in entries]
            bests = [e['best'] for e in entries]

            x = range(len(x_labels))
            ax.bar(x, averages, alpha=0.7, label='Average', color='steelblue')
            ax.plot(x, bests, 'ro-', label='Best', markersize=8)
            ax.set_xlabel(param_name)
            ax.set_ylabel('Fitness')
            ax.set_xticks(list(x))
            ax.set_xticklabels(x_labels, rotation=45)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3, axis='y')

        fig.suptitle('Análise de Sensibilidade - dantzig42', fontsize=14)
        fig.tight_layout()
        fig.savefig(fig_dir / 'sensitivity.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: sensitivity.png")

    # 4. Gap% comparison bars
    all_data = []
    if baseline:
        all_data.extend(baseline)
    if validation:
        all_data.extend(validation)

    if all_data:
        instance_names = sorted(set(e['instance_name'] for e in all_data))
        fig, axes = plt.subplots(1, len(instance_names), figsize=(6 * len(instance_names), 6))
        if len(instance_names) == 1:
            axes = [axes]

        for ax, inst_name in zip(axes, instance_names):
            inst_data = [e for e in all_data if e['instance_name'] == inst_name
                         and e.get('gap_percentage') is not None]
            if not inst_data:
                continue
            labels = [e['config_name'] for e in inst_data]
            gaps = [e['gap_percentage'] for e in inst_data]
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(gaps)))
            bars = ax.bar(range(len(labels)), gaps, color=colors)
            ax.set_ylabel('Gap%')
            ax.set_title(inst_name)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')

        fig.suptitle('Gap% ao Ótimo', fontsize=14)
        fig.tight_layout()
        fig.savefig(fig_dir / 'gap_comparison.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: gap_comparison.png")


def _avg_convergence(convergences):
    max_len = max(len(c) for c in convergences)
    padded = [c + [c[-1]] * (max_len - len(c)) for c in convergences]
    return np.mean(padded, axis=0)


# ─────────────────────────── Helpers ─────────────────────────────────────────

def _save_json(data, name):
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(RESULTS_DIR / f'{name}_{ts}.json', 'w') as f:
        json.dump(data, f, indent=2)
    with open(RESULTS_DIR / f'{name}_latest.json', 'w') as f:
        json.dump(data, f, indent=2)


def _load_json(filename):
    path = RESULTS_DIR / filename
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _write_report(filename, lines):
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Relatório: {path}")


# ─────────────────────────── Main ────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  PSO-TSP: EXECUÇÃO COMPLETA DE TODOS OS EXPERIMENTOS")
    print(f"  Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    timer = PhaseTimer()
    runner = ExperimentRunner(str(INSTANCES_DIR), str(RESULTS_DIR))

    # Phase 0: Paper Replication
    timer.start("0. Replicação do Artigo")
    run_paper_replication(runner)
    timer.stop()

    # Phase 1: Baseline Benchmark
    timer.start("1. Baseline Benchmark (TSPLIB)")
    run_baseline_benchmark(runner)
    timer.stop()

    # Phase 2: Sensitivity Analysis
    timer.start("2. Análise de Sensibilidade")
    best_by_param = run_sensitivity(runner)
    timer.stop()

    # Phase 3: Combinations (uses sensitivity output)
    timer.start("3. Melhores Combinações")
    _, best_combo = run_combinations(runner, best_by_param)
    timer.stop()

    # Phase 4: Validation (uses combinations output)
    timer.start("4. Validação (Variações Algorítmicas)")
    run_validation(runner, best_combo)
    timer.stop()

    # Phase 5: Reports & Visualizations
    timer.start("5. Relatórios e Gráficos")
    generate_all_reports(timer)
    timer.stop()

    # Final summary
    timer.summary()
    print(f"\nFim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Todos os experimentos concluídos!")


if __name__ == "__main__":
    main()
