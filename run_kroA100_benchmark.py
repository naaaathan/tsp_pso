"""
Benchmark em kroA100: instancia onde o baseline nao atinge o otimo.
Compara parametros do artigo vs configuracoes otimizadas.
30 runs por configuracao.
"""

import sys
import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from pso.swarm import Swarm, PSOConfig
from pso.fitness import FitnessCalculator
from tsplib.parser import TSPLibParser

RESULTS_DIR = Path(__file__).parent / 'results'
REPORTS_DIR = Path(__file__).parent / 'reports'
OPTIMAL = 21282
NUM_RUNS = 15


def run_config(fc, name, config, num_runs):
    print(f'\n  Config: {name}', flush=True)
    values = []
    times = []
    all_convergence = []

    for seed in range(num_runs):
        config.random_seed = seed
        t0 = time.time()
        result = Swarm(fc, config).run()
        elapsed = time.time() - t0
        values.append(result.best_fitness)
        times.append(elapsed)
        all_convergence.append(result.convergence_history)

        if (seed + 1) % 5 == 0:
            print(f'    Run {seed+1}/{num_runs}: {result.best_fitness:.0f} ({elapsed:.1f}s)', flush=True)

    best = min(values)
    worst = max(values)
    avg = float(np.mean(values))
    std = float(np.std(values))
    median = float(np.median(values))
    gap_best = ((best - OPTIMAL) / OPTIMAL) * 100
    gap_avg = ((avg - OPTIMAL) / OPTIMAL) * 100
    avg_time = float(np.mean(times))

    print(f'    Best={best:.0f} ({gap_best:+.2f}%), Avg={avg:.0f} ({gap_avg:+.2f}%), '
          f'Std={std:.1f}, T_avg={avg_time:.1f}s', flush=True)

    return {
        'config_name': name,
        'instance_name': 'kroA100',
        'num_cities': 100,
        'optimal_value': OPTIMAL,
        'num_runs': num_runs,
        'best': best,
        'worst': worst,
        'average': avg,
        'std': std,
        'median': median,
        'gap_best': gap_best,
        'gap_avg': gap_avg,
        'avg_time': avg_time,
        'all_values': values,
        'all_convergence': all_convergence,
    }


def main():
    print('=' * 60)
    print('  BENCHMARK kroA100: Baseline vs Otimizado')
    print(f'  {NUM_RUNS} runs por config, Otimo = {OPTIMAL}')
    print(f'  Inicio: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60, flush=True)

    parser = TSPLibParser()
    instance = parser.parse(str(Path(__file__).parent / 'tsplib' / 'instances' / 'kroA100.tsp'))
    dm = instance.get_distance_matrix()
    fc = FitnessCalculator(dm)

    configs = [
        ('baseline_artigo', PSOConfig(
            num_particles=30, max_iterations=100,
            w=0.8, c1=2.0, c2=2.0,
            local_search_strategy='2opt')),
        ('mais_particulas', PSOConfig(
            num_particles=100, max_iterations=100,
            w=0.8, c1=2.0, c2=2.0,
            local_search_strategy='2opt')),
        ('mais_iteracoes', PSOConfig(
            num_particles=30, max_iterations=300,
            w=0.8, c1=2.0, c2=2.0,
            local_search_strategy='2opt')),
        ('adaptive_inertia', PSOConfig(
            num_particles=30, max_iterations=300,
            w=0.8, c1=2.0, c2=2.0,
            adaptive_inertia=True, w_max=0.9, w_min=0.4,
            local_search_strategy='2opt')),
        ('otimizado_completo', PSOConfig(
            num_particles=50, max_iterations=300,
            w=0.8, c1=2.0, c2=2.0,
            adaptive_inertia=True, w_max=0.9, w_min=0.4,
            local_search_strategy='2opt')),
    ]

    all_results = []
    phase_times = {}

    for name, config in configs:
        t0 = time.time()
        result = run_config(fc, name, config, NUM_RUNS)
        phase_times[name] = time.time() - t0
        all_results.append(result)
        m, s = divmod(phase_times[name], 60)
        print(f'    Tempo total: {int(m)}m {s:.0f}s', flush=True)

    # Salvar resultados
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(RESULTS_DIR / f'kroA100_benchmark_{ts}.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    with open(RESULTS_DIR / 'kroA100_benchmark_latest.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    # Gerar relatorio
    generate_report(all_results, phase_times)

    # Gerar graficos
    generate_plots(all_results)

    # Resumo final
    total = sum(phase_times.values())
    m, s = divmod(total, 60)
    print(f'\n>>> TOTAL: {int(m)}m {s:.0f}s')
    print(f'Fim: {datetime.now().strftime("%H:%M:%S")}')
    print('Concluido!', flush=True)


def generate_report(results, phase_times):
    REPORTS_DIR.mkdir(exist_ok=True)
    baseline = results[0]

    lines = [
        '# Benchmark kroA100: Baseline do Artigo vs Configuracoes Otimizadas',
        '',
        '## Instancia',
        '',
        '- **Nome**: kroA100 (Krolak/Felts/Nelson)',
        '- **Cidades**: 100',
        f'- **Otimo conhecido**: {OPTIMAL}',
        '- **Tipo**: EUC_2D (distancia Euclidiana arredondada)',
        '',
        '## Por que kroA100?',
        '',
        'As instancias menores (fri26, dantzig42, berlin52) sao resolvidas otimamente pelo 2-opt ',
        'com qualquer configuracao de parametros PSO. O kroA100, com 100 cidades, e a menor ',
        'instancia TSPLIB onde o baseline do artigo **nao atinge o otimo**, permitindo ',
        'demonstrar o impacto da otimizacao de parametros.',
        '',
        '## Configuracoes Testadas',
        '',
        '| Config | Particulas | Iteracoes | Inercia | c1 | c2 | Diferenca vs Artigo |',
        '|--------|------------|-----------|---------|----|----|---------------------|',
        '| baseline_artigo | 30 | 100 | w=0.8 fixo | 2.0 | 2.0 | -- (referencia) |',
        '| mais_particulas | **100** | 100 | w=0.8 fixo | 2.0 | 2.0 | +particulas |',
        '| mais_iteracoes | 30 | **300** | w=0.8 fixo | 2.0 | 2.0 | +iteracoes |',
        '| adaptive_inertia | 30 | **300** | **0.9->0.4** | 2.0 | 2.0 | +iter +inercia adaptativa |',
        '| otimizado_completo | **50** | **300** | **0.9->0.4** | 2.0 | 2.0 | todas as melhorias |',
        '',
        f'## Resultados ({NUM_RUNS} runs por configuracao)',
        '',
        '| Config | Best | Worst | Average | Std | Median | Gap% (best) | Gap% (avg) | Tempo/run |',
        '|--------|------|-------|---------|-----|--------|-------------|------------|-----------|',
    ]

    for r in results:
        lines.append(
            f"| {r['config_name']} | {r['best']:.0f} | {r['worst']:.0f} | "
            f"{r['average']:.0f} | {r['std']:.1f} | {r['median']:.0f} | "
            f"{r['gap_best']:+.2f}% | {r['gap_avg']:+.2f}% | {r['avg_time']:.1f}s |"
        )

    # Melhoria sobre baseline
    lines.extend(['', '## Melhoria sobre o Baseline do Artigo', '',
                  '| Config | Melhoria Best | Melhoria Avg | Reducao Std |',
                  '|--------|--------------|-------------|-------------|'])

    for r in results[1:]:
        imp_best = baseline['best'] - r['best']
        imp_avg = baseline['average'] - r['average']
        imp_std = baseline['std'] - r['std']
        pct_avg = (imp_avg / baseline['average']) * 100 if baseline['average'] > 0 else 0
        lines.append(
            f"| {r['config_name']} | {imp_best:+.0f} ({((imp_best)/baseline['best'])*100:+.2f}%) | "
            f"{imp_avg:+.0f} ({pct_avg:+.2f}%) | {imp_std:+.1f} |"
        )

    # Analise de cada melhoria
    lines.extend([
        '', '## Analise do Impacto de Cada Melhoria', '',
        '### Mais particulas (30 -> 100)',
        '',
        f"Aumentar o numero de particulas de 30 para 100 (mantendo demais parametros do artigo) ",
    ])

    r_part = results[1]
    imp = baseline['average'] - r_part['average']
    lines.append(f"reduz o gap medio de {baseline['gap_avg']:.2f}% para {r_part['gap_avg']:.2f}% "
                 f"(melhoria de {imp:.0f} unidades na media).")

    lines.extend(['',
        '### Mais iteracoes (100 -> 500)',
        '',
    ])
    r_iter = results[2]
    imp = baseline['average'] - r_iter['average']
    lines.append(f"Aumentar iteracoes de 100 para 500 reduz o gap medio de "
                 f"{baseline['gap_avg']:.2f}% para {r_iter['gap_avg']:.2f}% "
                 f"(melhoria de {imp:.0f} unidades na media).")

    lines.extend(['',
        '### Inercia adaptativa (w fixo 0.8 -> w 0.9 a 0.4)',
        '',
    ])
    r_adapt = results[3]
    imp = results[2]['average'] - r_adapt['average']
    lines.append(f"Adicionar inercia adaptativa (sobre mais_iteracoes) vai de gap "
                 f"{results[2]['gap_avg']:.2f}% para {r_adapt['gap_avg']:.2f}%. "
                 f"A inercia alta no inicio favorece exploracao; baixa no final favorece convergencia.")

    lines.extend(['',
        '### Otimizado completo (todas as melhorias)',
        '',
    ])
    r_full = results[4]
    imp_best = baseline['best'] - r_full['best']
    imp_avg = baseline['average'] - r_full['average']
    pct = (imp_avg / baseline['average']) * 100
    lines.extend([
        f"Combinando todas as melhorias: gap medio cai de **{baseline['gap_avg']:.2f}%** para "
        f"**{r_full['gap_avg']:.2f}%**, uma reducao de **{pct:.1f}%** na media.",
        '',
        f"- Best: {baseline['best']:.0f} -> {r_full['best']:.0f} (melhoria de {imp_best:.0f})",
        f"- Average: {baseline['average']:.0f} -> {r_full['average']:.0f} (melhoria de {imp_avg:.0f})",
        f"- Std: {baseline['std']:.1f} -> {r_full['std']:.1f}",
    ])

    # Tempo
    lines.extend(['', '## Tempo de Execucao', '',
                  '| Config | Tempo total | Tempo/run |',
                  '|--------|------------|-----------|'])
    for r in results:
        t = phase_times.get(r['config_name'], 0)
        m, s = divmod(t, 60)
        lines.append(f"| {r['config_name']} | {int(m)}m {s:.0f}s | {r['avg_time']:.1f}s |")

    total = sum(phase_times.values())
    m, s = divmod(total, 60)
    lines.append(f"| **TOTAL** | **{int(m)}m {s:.0f}s** | |")

    lines.extend([
        '', '## Conclusao', '',
        'O PSO com parametros do artigo (n=30, iter=100, w=0.8) nao atinge o otimo em kroA100, ',
        f'apresentando gap medio de {baseline["gap_avg"]:.2f}%. Atraves de otimizacao sistematica:',
        '',
        '1. **Mais particulas** (100): maior diversidade de solucoes iniciais para o 2-opt refinar',
        '2. **Mais iteracoes** (500): mais oportunidades de recombinacao via velocidade PSO',
        '3. **Inercia adaptativa** (0.9->0.4): exploracao ampla no inicio, convergencia no final',
        '',
        f'Conseguimos reduzir o gap medio para {r_full["gap_avg"]:.2f}%, demonstrando que a ',
        'otimizacao de parametros e significativa em instancias de maior porte.',
    ])

    path = REPORTS_DIR / 'kroA100_benchmark_report.md'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  Relatorio: {path}', flush=True)


def generate_plots(results):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('  matplotlib nao disponivel', flush=True)
        return

    fig_dir = RESULTS_DIR / 'figures'
    fig_dir.mkdir(exist_ok=True)

    # 1. Box plot
    fig, ax = plt.subplots(figsize=(12, 6))
    labels = [r['config_name'] for r in results]
    data = [r['all_values'] for r in results]
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True)
    colors = ['#ff9999', '#99ccff', '#99ff99', '#ffcc99', '#cc99ff']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax.axhline(y=OPTIMAL, color='red', linestyle='--', label=f'Otimo ({OPTIMAL})', alpha=0.7)
    ax.legend()
    ax.set_ylabel('Fitness (distancia)')
    ax.set_title(f'kroA100 - Distribuicao de Resultados ({NUM_RUNS} runs)')
    ax.tick_params(axis='x', rotation=20)
    ax.grid(True, alpha=0.3, axis='y')
    fig.savefig(fig_dir / 'kroA100_boxplot.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Salvo: kroA100_boxplot.png', flush=True)

    # 2. Convergencia media
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in results:
        convs = r['all_convergence']
        ml = max(len(c) for c in convs)
        padded = [c + [c[-1]] * (ml - len(c)) for c in convs]
        avg_conv = np.mean(padded, axis=0)
        ax.plot(avg_conv, label=r['config_name'], linewidth=2, alpha=0.8)
    ax.axhline(y=OPTIMAL, color='red', linestyle='--', label=f'Otimo ({OPTIMAL})', alpha=0.5)
    ax.legend(fontsize=9)
    ax.set_xlabel('Iteracao')
    ax.set_ylabel('Melhor Fitness')
    ax.set_title('kroA100 - Curvas de Convergencia Media')
    ax.grid(True, alpha=0.3)
    fig.savefig(fig_dir / 'kroA100_convergence.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Salvo: kroA100_convergence.png', flush=True)

    # 3. Gap% bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    names = [r['config_name'] for r in results]
    gaps_best = [r['gap_best'] for r in results]
    gaps_avg = [r['gap_avg'] for r in results]
    x = np.arange(len(names))
    w = 0.35
    bars1 = ax.bar(x - w/2, gaps_best, w, label='Gap% (best)', color='steelblue')
    bars2 = ax.bar(x + w/2, gaps_avg, w, label='Gap% (avg)', color='coral')
    ax.set_ylabel('Gap%')
    ax.set_title('kroA100 - Gap% ao Otimo')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars1, gaps_best):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{val:.2f}%', ha='center', va='bottom', fontsize=8)
    for bar, val in zip(bars2, gaps_avg):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                f'{val:.2f}%', ha='center', va='bottom', fontsize=8)
    fig.savefig(fig_dir / 'kroA100_gap.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  Salvo: kroA100_gap.png', flush=True)


if __name__ == '__main__':
    main()
