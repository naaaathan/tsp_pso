# Roteiro de Slides - PSO para o TSP
## Trabalho 3 - Inteligencia Artificial (PSO)
### ~20 slides

---

## Slide 1 - Capa

- **Titulo**: Otimizacao por Enxame de Particulas (PSO) Aplicada ao Problema do Caixeiro Viajante (TSP)
- **Disciplina**: Inteligencia Artificial
- **Baseado em**: Araujo & Barboza (2025) - "Application of the Particle Swarm Optimization Method in Solving the Traveling Salesman Problem"
- **Nomes dos integrantes**
- **Data**

---

## Slide 2 - Objetivo

- Implementar e avaliar o algoritmo PSO para resolver o TSP
- Replicar os resultados do artigo de referencia
- Propor melhorias nos parametros e avaliar o impacto
- Demonstrar melhoria significativa em instancias de maior porte (eil76, kroA100, kroB100)

---

## Slide 3 - O Problema do Caixeiro Viajante (TSP)

- **Definicao**: Encontrar o menor ciclo Hamiltoniano em um grafo completo ponderado
- **Complexidade**: NP-dificil - nao existe algoritmo polinomial conhecido
- **Relevancia pratica**: Logistica, roteamento, manufatura, sequenciamento de DNA
- **Exemplo visual**: Mapa com cidades e rota otima (usar figura berlin52)

---

## Slide 4 - Por que PSO para o TSP?

- PSO e uma metaheuristica bio-inspirada (comportamento de enxames)
- Originalmente projetado para espacos continuos
- Desafio: adaptar para dominio discreto (permutacoes)
- Vantagens: simples de implementar, poucos parametros, boa convergencia
- Combinacao com busca local (2-opt) potencializa resultados

---

## Slide 5 - Descricao do Artigo Base

- **Artigo**: Araujo & Barboza (2025), arXiv:2501.15319v1
- **Proposta**: PSO discreto para TSP com operadores de swap
- **Parametros do artigo**: n=30 particulas, 100 iteracoes, w=0.8, c1=c2=2.0
- **Busca local**: 2-opt aplicado a cada particula
- **Instancia testada**: apenas 5 cidades (limitacao)

---

## Slide 6 - PSO Classico (Continuo)

- **Equacoes de atualizacao**:
  - v(t+1) = w * v(t) + c1 * r1 * (pBest - x) + c2 * r2 * (gBest - x)
  - x(t+1) = x(t) + v(t+1)
- **w**: inercia (controla exploracao vs explotacao)
- **c1**: coeficiente cognitivo (memoria individual)
- **c2**: coeficiente social (influencia do enxame)
- **Diagrama**: Ilustrar movimento de uma particula em direcao ao pBest e gBest

---

## Slide 7 - Adaptacao do PSO para o TSP (Discreto)

- **Posicao**: permutacao de cidades (ex: [3, 1, 4, 2, 5])
- **Velocidade**: lista de operacoes de swap (ex: [(1,3), (2,4)])
- **Diferenca entre permutacoes**: sequencia de swaps para transformar uma na outra
- **Multiplicacao por escalar**: manter apenas uma fracao dos swaps (baseado em w, c1*r1, c2*r2)
- **Soma de velocidades**: concatenar listas de swaps

---

## Slide 8 - Busca Local: 2-opt

- **Ideia**: Remover 2 arestas e reconectar invertendo o segmento entre elas
- **Complexidade**: O(n^2) por passada
- **Impacto**: Domina a qualidade da solucao em instancias pequenas/medias
- **Figura**: Antes e depois de um movimento 2-opt
- **Resultado chave**: Sem 2-opt, gap de ~186%; com 2-opt, gap ~0%

---

## Slide 9 - Metodologia Experimental

- **Fases do experimento**:
  1. Replicacao do artigo (validacao da implementacao)
  2. Baseline em instancias TSPLIB (berlin52, eil76, kroA100, kroB100)
  3. Analise de sensibilidade de parametros (dantzig42)
  4. Variacoes algoritmicas (inercia adaptativa, 3-opt)
  5. Benchmark otimizado em 3 instancias desafiadoras
- **Metricas**: Best, Average, Std, Gap% em relacao ao otimo conhecido
- **Execucoes**: 15-30 runs por configuracao (significancia estatistica)

---

## Slide 10 - Instancias TSPLIB Utilizadas

| Instancia | Cidades | Otimo Conhecido | Baseline Gap |
|-----------|---------|-----------------|--------------|
| berlin52 | 52 | 7542 | 0.00% (otimo) |
| eil76 | 76 | 538 | 1.96% |
| kroA100 | 100 | 21282 | 1.26% |
| kroB100 | 100 | 22141 | 1.09% |

- berlin52: otimo encontrado sempre (2-opt resolve)
- eil76, kroA100, kroB100: baseline NAO encontra o otimo -> espaço para melhoria

---

## Slide 11 - Resultado: Replicacao e Validacao

- **5 cidades (artigo)**: Otimo encontrado (15.153) em todas as execucoes
- **berlin52**: Otimo (7542) em 100% das runs com inercia adaptativa
- **Sem busca local**: gap de 186% -> busca local e indispensavel
- **3-opt**: 10x mais lento que 2-opt, sem melhoria de qualidade
- Implementacao validada e funcional

---

## Slide 12 - Descoberta: 2-opt Domina em Instancias Pequenas

- Analise de sensibilidade em dantzig42 (42 cidades):
  - 24 configuracoes testadas (variando n, iter, w, c1, c2)
  - **TODAS** convergem para a mesma solucao otima (634)
- **Conclusao**: parametros PSO sao irrelevantes quando 2-opt resolve
- **Motivacao**: buscar instancias maiores onde os parametros importam

---

## Slide 13 - Configuracao Otimizada Proposta

| Parametro | Artigo (baseline) | Otimizado | Justificativa |
|-----------|-------------------|-----------|---------------|
| Particulas | 30 | **50** | Mais diversidade inicial |
| Iteracoes | 100 | **300** | Mais recombinacao PSO |
| Inercia | 0.8 fixo | **0.9 -> 0.4** | Exploracao -> convergencia |
| c1, c2 | 2.0 | 2.0 | Mantidos |
| Busca local | 2-opt | 2-opt | Essencial |

---

## Slide 14 - Resultados kroA100 (100 cidades, 15 runs)

| Config | Best | Avg | Std | Gap% (avg) |
|--------|------|-----|-----|------------|
| baseline_artigo | 21398 | 21551 | 96.7 | **1.26%** |
| +particulas (n=100) | 21425 | 21483 | 60.0 | 0.94% |
| +iteracoes (i=300) | 21398 | 21484 | 53.6 | 0.95% |
| +inercia adaptativa | 21415 | 21478 | 42.6 | 0.92% |
| **otimizado completo** | **21381** | **21451** | **49.6** | **0.79%** |

- Gap reduzido de 1.26% para 0.79% (**reducao de 37%**)
- *(Incluir kroA100_boxplot.png)*

---

## Slide 15 - Resultados eil76 e kroB100 (15 runs)

### eil76 (76 cidades, otimo=538)

| Config | Best | Avg | Gap% (avg) |
|--------|------|-----|------------|
| baseline | 545 | 549 | **1.96%** |
| otimizado | 540 | 544 | **1.20%** |

Gap reduzido em **39%**

### kroB100 (100 cidades, otimo=22141)

| Config | Best | Avg | Gap% (avg) |
|--------|------|-----|------------|
| baseline | 22282 | 22383 | **1.09%** |
| otimizado | 22157 | 22258 | **0.53%** |

Gap reduzido em **51%**. Best a apenas 0.07% do otimo!

---

## Slide 16 - Comparacao Multi-Instancia

| Instancia | Cidades | Gap Baseline | Gap Otimizado | Reducao |
|-----------|---------|-------------|---------------|---------|
| eil76 | 76 | 1.96% | 1.20% | **39%** |
| kroA100 | 100 | 1.26% | 0.79% | **37%** |
| kroB100 | 100 | 1.09% | 0.53% | **51%** |
| **Media** | | **1.44%** | **0.84%** | **~42%** |

- *(Incluir multi_instance_gap_comparison.png)*
- Melhoria consistente em TODAS as instancias testadas

---

## Slide 17 - Graficos de Convergencia e Distribuicao

- **Boxplots**: Distribuicao dos resultados por instancia
  - *(eil76_boxplot.png, kroA100_boxplot.png, kroB100_boxplot.png)*
- **Curvas de convergencia**: Evolucao do gBest ao longo das iteracoes
  - *(kroA100_convergence.png, kroB100_convergence.png)*
- **Gap comparativo**: Todas as instancias lado a lado
  - *(multi_instance_gap_comparison.png)*

---

## Slide 18 - Impacto de Cada Melhoria (kroA100)

| Melhoria | Gap Avg | Reducao | Mecanismo |
|----------|---------|---------|-----------|
| Baseline (artigo) | 1.26% | -- | Referencia |
| +Particulas (30->100) | 0.94% | -0.32pp | Maior diversidade inicial |
| +Iteracoes (100->300) | 0.95% | -0.31pp | Mais recombinacao PSO |
| +Inercia adaptativa | 0.92% | -0.34pp | Exploracao -> convergencia |
| **Todas combinadas** | **0.79%** | **-0.47pp** | Efeito sinergico |

- Cada melhoria contribui incrementalmente
- O efeito combinado e maior que a soma das partes

---

## Slide 19 - Conclusoes

1. **PSO discreto + 2-opt** e eficaz para TSP de pequeno/medio porte (otimo em berlin52)
2. **2-opt domina** em instancias pequenas - parametros PSO sao irrelevantes
3. Em instancias maiores (76-100 cidades), **otimizacao de parametros e significativa**:
   - Reducao media de **~42% no gap** ao otimo em 3 instancias
   - kroB100: solucao a **0.07% do otimo**
4. **Inercia adaptativa** (0.9->0.4) melhora o balanco exploracao/explotacao
5. **Mais particulas e iteracoes** aumentam diversidade e refinamento
6. Trade-off: melhor qualidade custa ~5x mais tempo computacional

---

## Slide 20 - Referencias e Codigo

### Referencias
- Araujo, S. A. & Barboza, E. C. (2025). "Application of the Particle Swarm Optimization Method in Solving the Traveling Salesman Problem". arXiv:2501.15319v1
- Kennedy, J. & Eberhart, R. (1995). "Particle Swarm Optimization"
- Reinelt, G. (1991). "TSPLIB - A Traveling Salesman Problem Library"
- Croes, G. A. (1958). "A method for solving traveling-salesman problems"

### Codigo
- **Linguagem**: Python 3
- **Estrutura**: Modular (pso/, experiments/, tsplib/, reports/)
- **Repositorio**: *(link do repositorio)*
- **Modulos principais**: particle.py, swarm.py, velocity.py, local_search.py
