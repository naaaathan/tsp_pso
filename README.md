# PSO Híbrido para o Problema do Caixeiro Viajante (TSP)

Implementação de Particle Swarm Optimization (PSO) híbrido com busca local (2-opt/3-opt) aplicado ao Problema do Caixeiro Viajante, baseado no artigo *"PSO and the Traveling Salesman Problem: An Intelligent Optimization Approach"* (Araújo & Barboza, 2025).

Trabalho 3 da disciplina — aplicação de PSO/PSO-híbrido a problemas de otimização NP-hard, com reprodução e comparação de resultados do artigo.

## Estrutura do Projeto

```
tsp_pso/
├── pso/                        # Algoritmo PSO principal
│   ├── particle.py             # Classe Partícula (posição, velocidade, fitness, pbest)
│   ├── fitness.py              # Cálculo de fitness (distância total do tour)
│   ├── velocity.py             # Atualização de velocidade (adaptação discreta)
│   ├── position_update.py      # Atualização de posição via sequência de swaps
│   ├── local_search.py         # Operadores de busca local 2-opt e 3-opt
│   └── swarm.py                # Orquestração do algoritmo PSO (PSOConfig, Swarm)
│
├── experiments/                # Framework de experimentação
│   ├── runner.py               # ExperimentRunner (múltiplas execuções com seeds)
│   └── statistics.py           # Cálculo de estatísticas (média, std, gap%)
│
├── tsplib/                     # Leitura de instâncias TSPLIB
│   ├── parser.py               # Parser para formato TSPLIB (.tsp, .atsp)
│   └── instances/              # Instâncias de benchmark
│       ├── berlin52.tsp        # 52 cidades
│       ├── eil76.tsp           # 76 cidades
│       ├── kroA100.tsp         # 100 cidades
│       ├── kroB100.tsp         # 100 cidades
│       ├── dantzig42.tsp       # 42 cidades
│       ├── fri26.tsp           # 26 cidades
│       ├── gr21.tsp            # 21 cidades
│       ├── st70.tsp            # 70 cidades
│       ├── ch150.tsp           # 150 cidades
│       ├── ft53.atsp           # 53 cidades (assimétrico)
│       └── ftv170.atsp         # 170 cidades (assimétrico)
│
├── results/                    # Resultados em JSON e gráficos gerados
│   └── figures/                # Plots (boxplots, convergência, gap%)
├── reports/                    # Relatórios gerados em Markdown
│
├── run_paper_replication.py    # Replica exemplo de 5 cidades do artigo
├── run_kroA100_benchmark.py    # Benchmark com 5 configurações no kroA100
├── run_multi_benchmark.py      # Comparação baseline vs otimizado em múltiplas instâncias
├── run_baseline_benchmark.py   # Benchmark baseline em instâncias padrão
├── run_phase1_sensitivity.py   # Análise de sensibilidade de parâmetros
├── run_phase2_combinations.py  # Variações algorítmicas (2-opt, 3-opt)
├── run_phase3_validation.py    # Validação em múltiplas instâncias
├── run_all_experiments.py      # Executa todos os experimentos
├── generate_visualizations.py  # Gera gráficos a partir dos resultados JSON
└── requirements.txt            # numpy, matplotlib
```

## Adaptação do PSO para o TSP

O PSO foi originalmente projetado para otimização contínua. A adaptação para o domínio discreto de permutações funciona assim:

| Conceito PSO | Domínio Contínuo | Adaptação para TSP |
|---|---|---|
| **Posição** | Vetor de reais | Permutação de cidades |
| **Velocidade** | Vetor de reais | Lista de operações de swap (i, j) |
| **Diferença entre posições** | Subtração vetorial | Sequência mínima de swaps para transformar uma permutação em outra |
| **Atualização de velocidade** | v = w·v + c1·r1·(pbest-x) + c2·r2·(gbest-x) | Swaps retidos probabilisticamente com pesos w, c1·r1 e c2·r2 |
| **Atualização de posição** | x = x + v | Aplicação sequencial dos swaps à permutação atual |

A hibridização com **busca local 2-opt** é aplicada após cada movimentação PSO, refinando localmente cada solução.

## Parâmetros

### Parâmetros do Artigo (5 cidades)

| Parâmetro | Valor |
|---|---|
| Partículas | 30 |
| Iterações | 100 |
| Inércia (w) | 0.8 (fixo) |
| c1 (cognitivo) | 2.0 |
| c2 (social) | 2.0 |
| Busca local | 2-opt |

### Parâmetros Otimizados (76-100 cidades)

| Parâmetro | Valor |
|---|---|
| Partículas | 50 |
| Iterações | 300 |
| Inércia (w) | 0.9 → 0.4 (adaptativa linear) |
| c1, c2 | 2.0 |
| Busca local | 2-opt |

A **inércia adaptativa** decresce linearmente: `w(t) = w_max - (w_max - w_min) * (t / max_iter)`, favorecendo exploração no início e convergência no final.

## Resultados

### Replicação do Artigo (5 cidades)

O exemplo de 5 cidades do artigo foi replicado com sucesso. A implementação encontra consistentemente o tour ótimo de distância 15.153 em 100% das execuções.

### Instâncias Maiores — Baseline vs Otimizado

| Instância | Ótimo | Baseline (Gap%) | Otimizado (Gap%) | Redução do Gap |
|---|---|---|---|---|
| eil76 | 538 | 1.96% | 1.20% | 39% |
| kroA100 | 21282 | 1.26% | 0.79% | 37% |
| kroB100 | 22141 | 1.09% | 0.53% | 51% |

**Redução média do gap: ~42%** com os parâmetros otimizados em relação ao baseline do artigo.

### Análise de Sensibilidade (dantzig42)

Com 2-opt habilitado, praticamente todas as variações de parâmetros convergem para o ótimo (634), demonstrando que a busca local domina a qualidade da solução em instâncias pequenas/médias. A diferenciação dos parâmetros PSO aparece em instâncias maiores (76+ cidades).

### Saídas Geradas

- **Curvas de convergência**: fitness vs iteração para cada configuração
- **Boxplots**: distribuição dos resultados entre múltiplas execuções
- **Gráficos de gap%**: comparação entre configurações
- **Relatórios Markdown**: análise detalhada em `reports/`
- **Resultados JSON**: dados completos com estatísticas em `results/`

## Como Executar

### Requisitos

```bash
pip install -r requirements.txt
```

### Executar todos os experimentos

```bash
python run_all_experiments.py
```

### Executar experimentos individuais

```bash
python run_paper_replication.py      # Replicação do artigo (5 cidades)
python run_kroA100_benchmark.py      # Benchmark kroA100
python run_multi_benchmark.py        # Múltiplas instâncias
python run_phase1_sensitivity.py     # Sensibilidade de parâmetros
python run_phase2_combinations.py    # Variações algorítmicas
python run_phase3_validation.py      # Validação
```

### Gerar visualizações

```bash
python generate_visualizations.py
```

## Referências

- Araújo, S. A. & Barboza, E. L. (2025). *PSO and the Traveling Salesman Problem: An Intelligent Optimization Approach*.
- TSPLIB — biblioteca de instâncias benchmark para o TSP: http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/
