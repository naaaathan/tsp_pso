# Spec: PSO para o Problema do Caixeiro Viajante (TSP)

## Artigo Base

> **Araújo, K.S. & Barboza, F.M. (2025).** "PSO and the Traveling Salesman Problem: An Intelligent Optimization Approach". arXiv:2501.15319v1.

O artigo descreve a adaptação do Particle Swarm Optimization (PSO) para resolver o TSP, utilizando codificação por permutação, atualização de velocidade adaptada para domínio discreto e busca local (2-opt/3-opt).

### Parâmetros do Artigo

| Parâmetro | Valor |
|-----------|-------|
| Partículas (n) | 30 |
| Iterações máximas (maxIter) | 100 |
| Fator de inércia (w) | 0.8 |
| Coeficientes de aprendizado (c1, c2) | 2, 2 |
| Instância de teste | 5 cidades (coordenadas arbitrárias) |

### Limitação Crítica do Artigo

O artigo **não utiliza benchmarks TSPLIB** — apenas 5 cidades com coordenadas arbitrárias. Resultados reportados variam de 12.3 a 13.0 unidades de distância em 5 execuções. Portanto, precisamos:

1. Replicar o experimento original para validar a implementação
2. Criar nossos próprios benchmarks em instâncias TSPLIB
3. Otimizar parâmetros e comparar com o baseline

---

## Estrutura do Projeto

Espelha a organização do projeto tsp_ga:

```
tsp_pso/
├── pso/                          # Módulo principal do PSO
│   ├── __init__.py
│   ├── particle.py               # Classe Particle (posição=permutação, velocidade=swaps)
│   ├── swarm.py                  # Algoritmo PSO principal (Swarm + PSOConfig)
│   ├── fitness.py                # Calculador de fitness (distância total do tour)
│   ├── velocity.py               # Lógica de atualização de velocidade (sequências de swap)
│   ├── position_update.py        # Atualização de posição + reparo para permutação válida
│   └── local_search.py           # Operadores 2-opt e 3-opt
├── tsplib/                       # Reutilizado do tsp_ga
│   ├── parser.py
│   └── instances/                # dantzig42, fri26, berlin52, etc.
├── experiments/
│   ├── runner.py                 # Executor de experimentos (N runs, coleta estatísticas)
│   └── statistics.py             # Média, desvio padrão, melhor, pior, gap%
├── results/                      # Resultados JSON + gráficos
├── run_paper_replication.py      # Replicar experimento de 5 cidades do artigo
├── run_baseline_benchmark.py     # Parâmetros do artigo em instâncias TSPLIB (30 runs)
├── run_phase1_sensitivity.py     # Análise de sensibilidade de parâmetros
├── run_phase2_combinations.py    # Melhores combinações de parâmetros
├── run_phase3_validation.py      # Validação final com parâmetros otimizados
├── generate_visualizations.py    # Gerar tabelas e gráficos
├── reports/                      # Relatórios de análise em Markdown
│   ├── paper_replication_report.md
│   ├── baseline_benchmark_report.md
│   ├── sensitivity_report.md
│   ├── combinations_report.md
│   └── final_report.md           # Relatório consolidado com todas as fases
├── requirements.txt
├── README.md
└── spec.md                       # Este arquivo
```

---

## Fases de Implementação

### Fase 0: Scaffolding

- Criar estrutura de diretórios conforme acima
- Copiar/adaptar `tsplib/` do projeto tsp_ga (parser + instâncias)
- Criar `requirements.txt` (numpy, matplotlib)

### Fase 1: Implementação do PSO

Implementar o algoritmo exatamente como descrito no artigo.

#### 1.1 Representação da Partícula (`particle.py`)

- **Posição**: permutação de cidades (lista de inteiros)
- **Velocidade**: lista de operações de swap (pares de índices)
- **pBest**: melhor posição encontrada pela partícula
- **Fitness**: custo total do tour (distância)

#### 1.2 Atualização de Velocidade (`velocity.py`)

Adaptar a equação contínua para o domínio discreto:

```
v(t+1) = w * v(t) + c1 * r1 * (pBest - x(t)) + c2 * r2 * (gBest - x(t))
```

No domínio discreto:
- `(pBest - x)` = sequência de swaps para transformar x em pBest
- `w * v` = manter fração das swaps anteriores (controlada por w)
- `c1 * r1` e `c2 * r2` = probabilidade de aplicar cada swap da diferença

#### 1.3 Atualização de Posição (`position_update.py`)

- Aplicar sequência de swaps à posição atual
- Garantir que o resultado é uma permutação válida

#### 1.4 Busca Local (`local_search.py`)

- **2-opt**: inverter segmento do tour se reduzir a distância
- **3-opt**: rearranjar 3 segmentos do tour (melhoria mais agressiva)
- Aplicada após atualização de posição em cada iteração

#### 1.5 Algoritmo Principal (`swarm.py`)

```python
class PSOConfig:
    num_particles: int = 30
    max_iterations: int = 100
    w: float = 0.8              # inércia
    c1: float = 2.0             # cognitivo
    c2: float = 2.0             # social
    use_2opt: bool = True
    use_3opt: bool = False
    random_seed: int = None

class PSOResult:
    best_fitness: float
    best_tour: list
    convergence_history: list   # melhor fitness por iteração
    execution_time: float
    iterations_run: int
```

Pseudocódigo:
1. Inicializar n partículas com permutações aleatórias
2. Calcular fitness de cada partícula
3. Definir pBest de cada partícula e gBest do enxame
4. Para cada iteração:
   a. Para cada partícula: atualizar velocidade, atualizar posição, aplicar busca local
   b. Atualizar pBest e gBest
   c. (Opcional) atualizar w
5. Retornar gBest

#### 1.6 Fitness (`fitness.py`)

- Recebe matriz de distâncias
- Calcula custo total do tour (soma das distâncias entre cidades consecutivas + retorno à origem)

---

### Fase 2: Replicação e Benchmark Baseline

#### 2.1 Replicar Experimento do Artigo (`run_paper_replication.py`)

Validar implementação com o experimento original:
- 5 cidades com coordenadas: (0,0), (1,3), (4,3), (6,1), (3,0)
- Parâmetros: n=30, maxIter=100, w=0.8, c1=c2=2
- 5 execuções
- **Resultado esperado**: custos entre 12.3 e 13.0

#### 2.2 Benchmark Baseline em TSPLIB (`run_baseline_benchmark.py`)

Usando os mesmos parâmetros do artigo em instâncias reais:

| Instância | Cidades | Ótimo Conhecido | Categoria |
|-----------|---------|-----------------|-----------|
| fri26 | 26 | 937 | Pequena |
| dantzig42 | 42 | 699 | Média |
| berlin52 | 52 | 7542 | Grande |

- **30 execuções** por instância
- Métricas coletadas: best, worst, average, std, median, gap%
- Salvar convergence history para gráficos

---

### Fase 3: Otimização de Parâmetros

#### 3.1 Análise de Sensibilidade (`run_phase1_sensitivity.py`)

Variar um parâmetro por vez, mantendo os demais fixos no baseline:

| Parâmetro | Valores Testados |
|-----------|-----------------|
| Partículas (n) | 20, 30, 50, 100, 200 |
| Iterações (maxIter) | 100, 200, 500, 1000 |
| Inércia (w) | 0.4, 0.6, 0.8, 0.9, 1.0 |
| c1 | 1.0, 1.5, 2.0, 2.5, 3.0 |
| c2 | 1.0, 1.5, 2.0, 2.5, 3.0 |

- 10 execuções por configuração (para viabilidade de tempo)
- Instância de teste: dantzig42

#### 3.2 Melhores Combinações (`run_phase2_combinations.py`)

Com base nos resultados da Fase 3.1, combinar os melhores valores de cada parâmetro:
- Top 3 combinações identificadas na análise de sensibilidade
- 30 execuções por combinação
- Testar em todas as instâncias (fri26, dantzig42, berlin52)

#### 3.3 Melhorias Avançadas (`run_phase3_validation.py`)

Testar variações algorítmicas:

| Variação | Descrição |
|----------|-----------|
| Inércia adaptativa | w decrescendo linearmente de 0.9 a 0.4 ao longo das iterações |
| 3-opt | Substituir 2-opt por 3-opt na busca local |
| 2-opt + 3-opt | Usar 2-opt nas primeiras iterações e 3-opt nas finais |
| Sem busca local | Avaliar contribuição da busca local |

- 30 execuções por variação
- Testar em todas as instâncias

---

### Fase 4: Resultados e Comparações

#### 4.1 Tabelas

**Tabela principal** (por instância):

| Configuração | Best | Worst | Average | Std | Gap% |
|--------------|------|-------|---------|-----|------|
| Artigo (5 cidades) | — | — | — | — | — |
| Baseline (params artigo) | — | — | — | — | — |
| Otimizado | — | — | — | — | — |

#### 4.2 Gráficos (`generate_visualizations.py`)

1. **Curvas de convergência**: melhor fitness por iteração (baseline vs otimizado)
2. **Box plots**: distribuição de resultados por configuração
3. **Heatmaps**: análise de sensibilidade (parâmetro vs fitness)
4. **Barras de gap%**: comparação entre configurações para cada instância

#### 4.3 Métricas Estatísticas

Para cada configuração e instância, reportar:
- Melhor (Best)
- Pior (Worst)
- Média (Average)
- Desvio padrão (Std)
- Mediana (Median)
- Gap% ao ótimo conhecido: `((best - optimal) / optimal) * 100`
- Tempo médio de execução

---

## Execução dos Experimentos

### Execução em Background

Os experimentos (especialmente Fases 2 e 3) podem ser demorados — dezenas de minutos a horas dependendo das configurações e instâncias. Cada script `run_*.py` deve ser executado em background e monitorado:

- Executar via `run_in_background` no Bash, recebendo notificação ao concluir
- Cada script imprime progresso no stdout (run atual, configuração, tempo parcial)
- Resultados intermediários são salvos em JSON incrementalmente para não perder progresso em caso de interrupção
- Ao final de cada script, gerar automaticamente o report correspondente

### Ordem de Execução

1. `run_paper_replication.py` — rápido (< 1 min), validar implementação
2. `run_baseline_benchmark.py` — moderado (vários minutos), 30 runs x 3 instâncias
3. `run_phase1_sensitivity.py` — demorado, 10 runs x muitas configurações
4. `run_phase2_combinations.py` — demorado, 30 runs x combinações x 3 instâncias
5. `run_phase3_validation.py` — demorado, 30 runs x variações x 3 instâncias
6. `generate_visualizations.py` — rápido, gerar gráficos a partir dos JSONs

---

## Reports

Após cada fase de experimentos, gerar um relatório Markdown em `reports/` com análise dos resultados (seguindo o padrão do tsp_ga com `ft53_benchmark_report.md` e `results_table.md`).

### `reports/paper_replication_report.md`
- Resultados das 5 execuções na instância de 5 cidades
- Comparação direta com a Tabela 2 do artigo (custos 12.3-13.0)
- Validação: implementação está correta? Resultados compatíveis?

### `reports/baseline_benchmark_report.md`
- Tabela de resultados (30 runs) por instância TSPLIB com parâmetros do artigo
- Formato: Instance | N | Optimal | Best | Worst | Average | Std | Median | Gap%
- Curvas de convergência médias por instância
- Análise: como o PSO com parâmetros do artigo se comporta em instâncias reais?

### `reports/sensitivity_report.md`
- Tabela por grupo de parâmetro: qual valor teve melhor desempenho
- Formato: Grupo | Melhor Config | Best | Average | Gap%
- Identificação dos parâmetros mais impactantes
- Tempo de execução total da fase

### `reports/combinations_report.md`
- Ranking das combinações testadas
- Formato: Rank | Configuração | Best | Average | Worst | Std | Gap%
- Comparação com baseline
- Melhoria percentual sobre o baseline

### `reports/final_report.md`
- Relatório consolidado com todas as fases
- Tabela comparativa final (por instância): Artigo vs Baseline vs Otimizado
- Gráficos de referência (convergência, box plots)
- Conclusões: conseguimos melhorar? Em quanto? Quais parâmetros mais importam?
- Tempo total de execução de todos os experimentos

---

## Dependências

```
numpy
matplotlib
```

---

## Notas

- O tsplib/ pode ser reutilizado diretamente do tsp_ga com mínimas adaptações
- Cada run script salva resultados em JSON em `results/` para reprodutibilidade
- Nomenclatura de arquivos de resultado segue padrão: `{experiment}_{timestamp}.json` + `{experiment}_latest.json`
- Todos os experimentos usam seeds determinísticas para reprodutibilidade
