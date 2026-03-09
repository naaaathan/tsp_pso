"""
Gera visualizações (gráficos) a partir dos resultados dos experimentos.

1. Curvas de convergência (baseline vs otimizado)
2. Box plots (distribuição de resultados por configuração)
3. Heatmaps (análise de sensibilidade)
4. Barras de gap% (comparação entre configurações)
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

RESULTS_DIR = Path(__file__).parent / 'results'
FIGURES_DIR = RESULTS_DIR / 'figures'


def load_json(filename):
    """Carrega um arquivo JSON de resultados."""
    filepath = RESULTS_DIR / filename
    if not filepath.exists():
        print(f"Arquivo não encontrado: {filepath}")
        return None
    with open(filepath) as f:
        return json.load(f)


def plot_convergence_curves():
    """Gera curvas de convergência para baseline e otimizado."""
    baseline = load_json('baseline_benchmark_latest.json')
    phase3 = load_json('phase3_validation_latest.json')

    if not baseline:
        print("Sem dados de baseline para convergência.")
        return

    for entry in baseline:
        instance_name = entry['instance_name']

        fig, ax = plt.subplots(figsize=(10, 6))

        # Convergência média do baseline
        convergences = entry['all_convergence']
        if convergences:
            max_len = max(len(c) for c in convergences)
            padded = []
            for c in convergences:
                padded.append(c + [c[-1]] * (max_len - len(c)))
            avg_conv = np.mean(padded, axis=0)
            ax.plot(avg_conv, label='Baseline (artigo)', linewidth=2)

        # Se temos dados da fase 3, plotar as variações
        if phase3:
            phase3_inst = [e for e in phase3 if e['instance_name'] == instance_name]
            for entry3 in phase3_inst:
                convs = entry3['all_convergence']
                if convs:
                    max_len3 = max(len(c) for c in convs)
                    padded3 = []
                    for c in convs:
                        padded3.append(c + [c[-1]] * (max_len3 - len(c)))
                    avg_conv3 = np.mean(padded3, axis=0)
                    ax.plot(avg_conv3, label=entry3['config_name'], linewidth=1.5, alpha=0.8)

        ax.set_xlabel('Iteração')
        ax.set_ylabel('Melhor Fitness (Distância)')
        ax.set_title(f'Curva de Convergência - {instance_name}')
        ax.legend()
        ax.grid(True, alpha=0.3)

        filepath = FIGURES_DIR / f'convergence_{instance_name}.png'
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: {filepath}")


def plot_boxplots():
    """Gera box plots da distribuição de resultados."""
    phase3 = load_json('phase3_validation_latest.json')
    if not phase3:
        print("Sem dados da fase 3 para box plots.")
        return

    instance_names = sorted(set(e['instance_name'] for e in phase3))

    for inst_name in instance_names:
        inst_data = [e for e in phase3 if e['instance_name'] == inst_name]
        if not inst_data:
            continue

        fig, ax = plt.subplots(figsize=(12, 6))

        labels = []
        data = []
        for entry in inst_data:
            labels.append(entry['config_name'])
            data.append(entry['all_values'])

        bp = ax.boxplot(data, labels=labels, patch_artist=True)
        colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)

        # Marcar ótimo
        opt = inst_data[0].get('optimal_value')
        if opt:
            ax.axhline(y=opt, color='red', linestyle='--', label=f'Ótimo ({opt})', alpha=0.7)
            ax.legend()

        ax.set_ylabel('Fitness (Distância)')
        ax.set_title(f'Distribuição de Resultados - {inst_name}')
        ax.tick_params(axis='x', rotation=30)
        ax.grid(True, alpha=0.3, axis='y')

        filepath = FIGURES_DIR / f'boxplot_{inst_name}.png'
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Salvo: {filepath}")


def plot_sensitivity_heatmap():
    """Gera heatmaps para a análise de sensibilidade."""
    sensitivity = load_json('phase1_sensitivity_latest.json')
    if not sensitivity:
        print("Sem dados de sensibilidade para heatmap.")
        return

    # Agrupar por parâmetro
    params = {}
    for entry in sensitivity:
        config_name = entry['config_name']
        param_name, value = config_name.split('=')
        if param_name not in params:
            params[param_name] = []
        params[param_name].append((value, entry['average'], entry['best']))

    fig, axes = plt.subplots(1, len(params), figsize=(4 * len(params), 5))
    if len(params) == 1:
        axes = [axes]

    for ax, (param_name, values) in zip(axes, params.items()):
        x_labels = [v[0] for v in values]
        averages = [v[1] for v in values]
        bests = [v[2] for v in values]

        x = range(len(x_labels))
        ax.bar(x, averages, alpha=0.7, label='Average', color='steelblue')
        ax.plot(x, bests, 'ro-', label='Best', markersize=8)

        ax.set_xlabel(param_name)
        ax.set_ylabel('Fitness')
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, rotation=45)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')

    fig.suptitle('Análise de Sensibilidade - dantzig42', fontsize=14)
    fig.tight_layout()

    filepath = FIGURES_DIR / 'sensitivity_heatmap.png'
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Salvo: {filepath}")


def plot_gap_bars():
    """Gera gráfico de barras de gap% por configuração."""
    baseline = load_json('baseline_benchmark_latest.json')
    phase3 = load_json('phase3_validation_latest.json')

    all_data = []
    if baseline:
        for e in baseline:
            all_data.append(e)
    if phase3:
        for e in phase3:
            all_data.append(e)

    if not all_data:
        print("Sem dados para gráfico de gap%.")
        return

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

        for bar, gap in zip(bars, gaps):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{gap:.1f}%', ha='center', va='bottom', fontsize=8)

    fig.suptitle('Gap% ao Ótimo por Configuração', fontsize=14)
    fig.tight_layout()

    filepath = FIGURES_DIR / 'gap_comparison.png'
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Salvo: {filepath}")


def generate_final_report():
    """Gera o relatório final consolidado."""
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    baseline = load_json('baseline_benchmark_latest.json')
    phase3 = load_json('phase3_validation_latest.json')

    lines = [
        "# Relatório Final - PSO para o TSP",
        "",
        "## Resumo",
        "",
        "Este relatório consolida todos os experimentos realizados com o PSO "
        "aplicado ao Problema do Caixeiro Viajante.",
        "",
    ]

    if baseline:
        lines.extend([
            "## Baseline (Parâmetros do Artigo)",
            "",
            "| Instância | N | Ótimo | Best | Average | Gap% |",
            "|-----------|---|-------|------|---------|------|",
        ])
        for e in baseline:
            opt_str = f"{e['optimal_value']:.0f}" if e.get('optimal_value') else "N/A"
            gap_str = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
            lines.append(
                f"| {e['instance_name']} | {e['num_cities']} | {opt_str} | "
                f"{e['best']:.2f} | {e['average']:.2f} | {gap_str} |"
            )
        lines.append("")

    if phase3:
        lines.extend([
            "## Variações Algorítmicas",
            "",
        ])

        instance_names = sorted(set(e['instance_name'] for e in phase3))
        for inst_name in instance_names:
            inst_data = [e for e in phase3 if e['instance_name'] == inst_name]
            opt = inst_data[0].get('optimal_value')
            opt_str = f"{opt:.0f}" if opt else "N/A"

            lines.extend([
                f"### {inst_name} (Ótimo: {opt_str})",
                "",
                "| Variação | Best | Average | Gap% |",
                "|----------|------|---------|------|",
            ])

            for e in sorted(inst_data, key=lambda x: x['average']):
                gap_str = f"{e['gap_percentage']:.2f}" if e.get('gap_percentage') is not None else "N/A"
                lines.append(
                    f"| {e['config_name']} | {e['best']:.2f} | {e['average']:.2f} | {gap_str} |"
                )
            lines.append("")

    lines.extend([
        "## Gráficos",
        "",
        "Ver diretório `results/figures/` para:",
        "- Curvas de convergência",
        "- Box plots",
        "- Análise de sensibilidade",
        "- Comparação de gap%",
        "",
        "## Conclusões",
        "",
        "1. A busca local (2-opt) é crucial para o desempenho do PSO em instâncias TSP reais",
        "2. Os parâmetros do artigo (otimizados para 5 cidades) precisam de ajuste para instâncias maiores",
        "3. Mais partículas e iterações geralmente melhoram os resultados, com retornos decrescentes",
    ])

    report_path = reports_dir / 'final_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Relatório final gerado em {report_path}")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("Gerando visualizações...")
    print("\n1. Curvas de convergência")
    plot_convergence_curves()

    print("\n2. Box plots")
    plot_boxplots()

    print("\n3. Análise de sensibilidade")
    plot_sensitivity_heatmap()

    print("\n4. Comparação de gap%")
    plot_gap_bars()

    print("\n5. Relatório final")
    generate_final_report()

    print("\nVisualização completa!")


if __name__ == "__main__":
    main()
