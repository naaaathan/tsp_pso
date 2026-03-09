"""
Run only Phase 4 (Validation) + Phase 5 (Reports/Plots).
Phases 0-3 already completed.
"""

import sys
import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime

# Force UTF-8 stdout on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import PSOConfig
from experiments.runner import ExperimentRunner

INSTANCES_DIR = Path(__file__).parent / 'tsplib' / 'instances'
RESULTS_DIR = Path(__file__).parent / 'results'
REPORTS_DIR = Path(__file__).parent / 'reports'
TSPLIB_INSTANCES = ['fri26.tsp', 'dantzig42.tsp', 'berlin52.tsp']

SENSITIVITY = {
    'num_particles': [20, 30, 50, 100, 200],
    'max_iterations': [100, 200, 500, 1000],
    'w': [0.4, 0.6, 0.8, 0.9, 1.0],
    'c1': [1.0, 1.5, 2.0, 2.5, 3.0],
    'c2': [1.0, 1.5, 2.0, 2.5, 3.0],
}

BASELINE_PARAMS = {
    'num_particles': 30, 'max_iterations': 100,
    'w': 0.8, 'c1': 2.0, 'c2': 2.0,
}


def load_json(name):
    path = RESULTS_DIR / f'{name}_latest.json'
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_json(data, name):
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(RESULTS_DIR / f'{name}_{ts}.json', 'w') as f:
        json.dump(data, f, indent=2)
    with open(RESULTS_DIR / f'{name}_latest.json', 'w') as f:
        json.dump(data, f, indent=2)


def get_best_params_from_phase2():
    data = load_json('phase2_combinations')
    if not data:
        return 50, 500, 2.0, 2.0

    # Best combo on dantzig42 by average
    best = None
    for entry in data:
        if 'dantzig42' in entry.get('instance_name', '').lower():
            if best is None or entry['average'] < best['average']:
                best = entry

    if best:
        p = best['config_params']
        return (p.get('num_particles', 50), p.get('max_iterations', 500),
                p.get('c1', 2.0), p.get('c2', 2.0))
    return 50, 500, 2.0, 2.0


def run_validation(runner):
    n_particles, max_iter, c1, c2 = get_best_params_from_phase2()
    print(f"  Base params: n={n_particles}, iter={max_iter}, c1={c1}, c2={c2}")

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
        print(f"\n  Variacao: {var_name}")
        sys.stdout.flush()
        for filename in TSPLIB_INSTANCES:
            instance = runner.load_instance(filename)
            t0 = time.time()
            result = runner.run_experiment(instance, config, config_name=var_name,
                                           num_runs=30, verbose=False)
            elapsed = time.time() - t0
            all_results.append(result)
            gap_str = f"{result.gap_percentage:.2f}%" if result.gap_percentage is not None else "N/A"
            print(f"    {filename}: Best={result.best:.2f}, Avg={result.average:.2f}, "
                  f"Std={result.std:.2f}, Gap={gap_str}, T={elapsed:.1f}s")
            sys.stdout.flush()

    runner.save_results(all_results, 'phase3_validation')
    return all_results


def generate_reports(phase4_time):
    REPORTS_DIR.mkdir(exist_ok=True)

    paper = load_json('paper_replication')
    baseline = load_json('baseline_benchmark')
    sensitivity = load_json('phase1_sensitivity')
    combinations = load_json('phase2_combinations')
    validation = load_json('phase3_validation')

    # === Sensitivity Report ===
    if sensitivity:
        lines = ["# Relatorio de Analise de Sensibilidade", "",
                 f"- **Instancia**: dantzig42.tsp",
                 f"- **Runs por config**: 10", ""]
        for param_name in SENSITIVITY:
            entries = [e for e in sensitivity if e['config_name'].startswith(param_name + '=')]
            if not entries:
                continue
            best_e = min(entries, key=lambda e: e['average'])
            lines.extend([f"## Parametro: {param_name}", "",
                          "| Valor | Best | Average | Std | Gap% |",
                          "|-------|------|---------|-----|------|"])
            for e in entries:
                val = e['config_name'].split('=')[1]
                gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                mark = " *" if e is best_e else ""
                lines.append(f"| {val}{mark} | {e['best']:.2f} | {e['average']:.2f} | {e['std']:.2f} | {gap} |")
            lines.append("")
        _write_report('sensitivity_report.md', lines)

    # === Combinations Report ===
    if combinations:
        lines = ["# Relatorio de Combinacoes de Parametros", ""]
        for inst in sorted(set(e['instance_name'] for e in combinations)):
            ie = [e for e in combinations if e['instance_name'] == inst]
            opt = ie[0].get('optimal_value')
            opt_s = f"{opt:.0f}" if opt else "N/A"
            # Add baseline for comparison
            if baseline:
                be = next((e for e in baseline if e['instance_name'] == inst), None)
                if be:
                    ie.append(be)
            lines.extend([f"### {inst} (Otimo: {opt_s})", "",
                          "| Rank | Config | Best | Average | Worst | Std | Gap% |",
                          "|------|--------|------|---------|-------|-----|------|"])
            for rank, e in enumerate(sorted(ie, key=lambda x: x['average']), 1):
                gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                lines.append(f"| {rank} | {e['config_name']} | {e['best']:.2f} | "
                             f"{e['average']:.2f} | {e['worst']:.2f} | {e['std']:.2f} | {gap} |")
            lines.append("")
        _write_report('combinations_report.md', lines)

    # === Validation Report ===
    if validation:
        lines = ["# Relatorio de Validacao - Variacoes Algoritmicas", "",
                 "| Variacao | Descricao |",
                 "|----------|-----------|",
                 "| baseline_2opt | PSO padrao com 2-opt |",
                 "| adaptive_inertia | w decrescendo de 0.9 a 0.4 |",
                 "| 3opt_only | Substituir 2-opt por 3-opt |",
                 "| 2opt_then_3opt | 2-opt + 3-opt hibrido |",
                 "| no_local_search | Sem busca local |", ""]
        for inst in sorted(set(e['instance_name'] for e in validation)):
            ie = [e for e in validation if e['instance_name'] == inst]
            opt = ie[0].get('optimal_value')
            opt_s = f"{opt:.0f}" if opt else "N/A"
            lines.extend([f"### {inst} (Otimo: {opt_s})", "",
                          "| Variacao | Best | Average | Worst | Std | Gap% | Tempo (s) |",
                          "|----------|------|---------|-------|-----|------|-----------|"])
            for e in sorted(ie, key=lambda x: x['average']):
                gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                lines.append(f"| {e['config_name']} | {e['best']:.2f} | {e['average']:.2f} | "
                             f"{e['worst']:.2f} | {e['std']:.2f} | {gap} | {e['avg_time']:.2f} |")
            lines.append("")
        _write_report('validation_report.md', lines)

    # === Final Report ===
    lines = ["# Relatorio Final - PSO para o TSP", ""]

    if paper:
        stats = paper.get('statistics', {})
        lines.extend(["## 1. Replicacao do Artigo", "",
                       f"- 5 cidades: Melhor = {stats.get('best', 'N/A')}, "
                       f"Media = {stats.get('average', 'N/A')}", ""])

    if baseline:
        lines.extend(["## 2. Baseline (Parametros do Artigo em TSPLIB)", "",
                       "| Instancia | N | Otimo | Best | Average | Std | Gap% |",
                       "|-----------|---|-------|------|---------|-----|------|"])
        for e in baseline:
            opt = f"{e['optimal_value']:.0f}" if e.get('optimal_value') else "N/A"
            gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            lines.append(f"| {e['instance_name']} | {e['num_cities']} | {opt} | "
                         f"{e['best']:.2f} | {e['average']:.2f} | {e['std']:.2f} | {gap} |")
        lines.append("")

    if sensitivity:
        lines.extend(["## 3. Analise de Sensibilidade", "",
                       "| Parametro | Melhor Valor | Average |",
                       "|-----------|-------------|---------|"])
        for param_name in SENSITIVITY:
            entries = [e for e in sensitivity if e['config_name'].startswith(param_name + '=')]
            if entries:
                best = min(entries, key=lambda e: e['average'])
                val = best['config_name'].split('=')[1]
                lines.append(f"| {param_name} | {val} | {best['average']:.2f} |")
        lines.append("")

    if combinations:
        lines.extend(["## 4. Melhores Combinacoes", ""])
        for inst in sorted(set(e['instance_name'] for e in combinations)):
            ie = [e for e in combinations if e['instance_name'] == inst]
            best = min(ie, key=lambda e: e['average'])
            gap = f"{best['gap_percentage']:.2f}%" if best.get('gap_percentage') is not None else "N/A"
            lines.append(f"- **{inst}**: {best['config_name']} -> "
                         f"Best={best['best']:.2f}, Avg={best['average']:.2f}, Gap={gap}")
        lines.append("")

    if validation:
        lines.extend(["## 5. Variacoes Algoritmicas", ""])
        for inst in sorted(set(e['instance_name'] for e in validation)):
            ie = [e for e in validation if e['instance_name'] == inst]
            lines.extend([f"### {inst}", "",
                          "| Variacao | Best | Average | Gap% |",
                          "|----------|------|---------|------|"])
            for e in sorted(ie, key=lambda x: x['average']):
                gap = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                lines.append(f"| {e['config_name']} | {e['best']:.2f} | {e['average']:.2f} | {gap} |")
            lines.append("")

    # Comparison: baseline vs best optimized
    if baseline and validation:
        lines.extend(["## 6. Comparacao Final: Baseline vs Melhor Otimizado", "",
                       "| Instancia | Baseline Avg | Otimizado Avg | Melhoria |",
                       "|-----------|-------------|---------------|----------|"])
        for be in baseline:
            inst = be['instance_name']
            vi = [e for e in validation if e['instance_name'] == inst]
            if vi:
                bv = min(vi, key=lambda e: e['average'])
                imp = be['average'] - bv['average']
                pct = (imp / be['average'] * 100) if be['average'] > 0 else 0
                lines.append(f"| {inst} | {be['average']:.2f} | "
                             f"{bv['average']:.2f} ({bv['config_name']}) | {pct:+.2f}% |")
        lines.append("")

    # Time
    lines.extend(["## 7. Tempo de Execucao", "",
                   f"- Fase 4 (Validacao): {phase4_time:.1f}s ({phase4_time/60:.1f}min)", ""])

    _write_report('final_report.md', lines)

    # === Plots ===
    _generate_plots(baseline, sensitivity, validation)


def _generate_plots(baseline, sensitivity, validation):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib nao disponivel, pulando graficos.")
        return

    fig_dir = RESULTS_DIR / 'figures'
    fig_dir.mkdir(exist_ok=True)

    def avg_conv(convergences):
        ml = max(len(c) for c in convergences)
        padded = [c + [c[-1]] * (ml - len(c)) for c in convergences]
        return np.mean(padded, axis=0)

    # Convergence
    if baseline and validation:
        for inst in sorted(set(e['instance_name'] for e in baseline)):
            fig, ax = plt.subplots(figsize=(10, 6))
            be = next((e for e in baseline if e['instance_name'] == inst), None)
            if be and be.get('all_convergence'):
                ax.plot(avg_conv(be['all_convergence']), label='Baseline', linewidth=2)
            for ve in [e for e in validation if e['instance_name'] == inst]:
                if ve.get('all_convergence'):
                    ax.plot(avg_conv(ve['all_convergence']), label=ve['config_name'], linewidth=1.5, alpha=0.8)
            ax.set_xlabel('Iteracao'); ax.set_ylabel('Melhor Fitness')
            ax.set_title(f'Convergencia - {inst}'); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
            fig.savefig(fig_dir / f'convergence_{inst}.png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"  Salvo: convergence_{inst}.png")

    # Box plots
    if validation:
        for inst in sorted(set(e['instance_name'] for e in validation)):
            ie = [e for e in validation if e['instance_name'] == inst]
            fig, ax = plt.subplots(figsize=(12, 6))
            labels = [e['config_name'] for e in ie]
            data = [e['all_values'] for e in ie]
            bp = ax.boxplot(data, labels=labels, patch_artist=True)
            colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            opt = ie[0].get('optimal_value')
            if opt:
                ax.axhline(y=opt, color='red', linestyle='--', label=f'Otimo ({opt})', alpha=0.7)
                ax.legend()
            ax.set_ylabel('Fitness'); ax.set_title(f'Distribuicao - {inst}')
            ax.tick_params(axis='x', rotation=30); ax.grid(True, alpha=0.3, axis='y')
            fig.savefig(fig_dir / f'boxplot_{inst}.png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"  Salvo: boxplot_{inst}.png")

    # Sensitivity
    if sensitivity:
        param_names = list(SENSITIVITY.keys())
        fig, axes = plt.subplots(1, len(param_names), figsize=(4 * len(param_names), 5))
        if len(param_names) == 1:
            axes = [axes]
        for ax, pn in zip(axes, param_names):
            entries = [e for e in sensitivity if e['config_name'].startswith(pn + '=')]
            if not entries:
                continue
            xl = [e['config_name'].split('=')[1] for e in entries]
            avgs = [e['average'] for e in entries]
            bests = [e['best'] for e in entries]
            x = range(len(xl))
            ax.bar(x, avgs, alpha=0.7, label='Average', color='steelblue')
            ax.plot(x, bests, 'ro-', label='Best', markersize=8)
            ax.set_xlabel(pn); ax.set_ylabel('Fitness')
            ax.set_xticks(list(x)); ax.set_xticklabels(xl, rotation=45)
            ax.legend(fontsize=8); ax.grid(True, alpha=0.3, axis='y')
        fig.suptitle('Analise de Sensibilidade - dantzig42', fontsize=14)
        fig.tight_layout()
        fig.savefig(fig_dir / 'sensitivity.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: sensitivity.png")

    # Gap comparison
    all_data = (baseline or []) + (validation or [])
    if all_data:
        insts = sorted(set(e['instance_name'] for e in all_data))
        fig, axes = plt.subplots(1, len(insts), figsize=(6 * len(insts), 6))
        if len(insts) == 1:
            axes = [axes]
        for ax, inst in zip(axes, insts):
            ie = [e for e in all_data if e['instance_name'] == inst and e.get('gap_percentage') is not None]
            if not ie:
                continue
            labels = [e['config_name'] for e in ie]
            gaps = [e['gap_percentage'] for e in ie]
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(gaps)))
            ax.bar(range(len(labels)), gaps, color=colors)
            ax.set_ylabel('Gap%'); ax.set_title(inst)
            ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
        fig.suptitle('Gap% ao Otimo', fontsize=14); fig.tight_layout()
        fig.savefig(fig_dir / 'gap_comparison.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: gap_comparison.png")


def _write_report(filename, lines):
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"  Relatorio: {path}")


def main():
    print("=" * 60)
    print("  PSO-TSP: Fases 4+5 (Validacao + Relatorios)")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    sys.stdout.flush()

    runner = ExperimentRunner(str(INSTANCES_DIR), str(RESULTS_DIR))

    # Phase 4: Validation
    print("\n>>> FASE 4: Validacao (Variacoes Algoritmicas)")
    sys.stdout.flush()
    t0 = time.time()
    run_validation(runner)
    phase4_time = time.time() - t0
    m, s = divmod(phase4_time, 60)
    print(f"\n>>> Fase 4 concluida em {int(m)}m {s:.1f}s")
    sys.stdout.flush()

    # Phase 5: Reports
    print("\n>>> FASE 5: Relatorios e Graficos")
    sys.stdout.flush()
    t1 = time.time()
    generate_reports(phase4_time)
    phase5_time = time.time() - t1
    print(f"\n>>> Fase 5 concluida em {phase5_time:.1f}s")

    total = phase4_time + phase5_time
    m, s = divmod(total, 60)
    print(f"\n>>> TOTAL: {int(m)}m {s:.1f}s")
    print("Concluido!")


if __name__ == "__main__":
    main()
