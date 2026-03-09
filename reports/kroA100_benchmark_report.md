# Benchmark kroA100: Baseline do Artigo vs Configuracoes Otimizadas

## Instancia

- **Nome**: kroA100 (Krolak/Felts/Nelson)
- **Cidades**: 100
- **Otimo conhecido**: 21282
- **Tipo**: EUC_2D (distancia Euclidiana arredondada)

## Por que kroA100?

As instancias menores (fri26, dantzig42, berlin52) sao resolvidas otimamente pelo 2-opt 
com qualquer configuracao de parametros PSO. O kroA100, com 100 cidades, e a menor 
instancia TSPLIB onde o baseline do artigo **nao atinge o otimo**, permitindo 
demonstrar o impacto da otimizacao de parametros.

## Configuracoes Testadas

| Config | Particulas | Iteracoes | Inercia | c1 | c2 | Diferenca vs Artigo |
|--------|------------|-----------|---------|----|----|---------------------|
| baseline_artigo | 30 | 100 | w=0.8 fixo | 2.0 | 2.0 | -- (referencia) |
| mais_particulas | **100** | 100 | w=0.8 fixo | 2.0 | 2.0 | +particulas |
| mais_iteracoes | 30 | **300** | w=0.8 fixo | 2.0 | 2.0 | +iteracoes |
| adaptive_inertia | 30 | **300** | **0.9->0.4** | 2.0 | 2.0 | +iter +inercia adaptativa |
| otimizado_completo | **50** | **300** | **0.9->0.4** | 2.0 | 2.0 | todas as melhorias |

## Resultados (15 runs por configuracao)

| Config | Best | Worst | Average | Std | Median | Gap% (best) | Gap% (avg) | Tempo/run |
|--------|------|-------|---------|-----|--------|-------------|------------|-----------|
| baseline_artigo | 21398 | 21765 | 21551 | 96.7 | 21549 | +0.55% | +1.26% | 44.3s |
| mais_particulas | 21425 | 21616 | 21483 | 60.0 | 21488 | +0.67% | +0.94% | 147.7s |
| mais_iteracoes | 21398 | 21583 | 21484 | 53.6 | 21498 | +0.55% | +0.95% | 133.1s |
| adaptive_inertia | 21415 | 21546 | 21478 | 42.6 | 21476 | +0.62% | +0.92% | 132.5s |
| otimizado_completo | 21381 | 21572 | 21451 | 49.6 | 21442 | +0.47% | +0.79% | 221.6s |

## Melhoria sobre o Baseline do Artigo

| Config | Melhoria Best | Melhoria Avg | Reducao Std |
|--------|--------------|-------------|-------------|
| mais_particulas | -27 (-0.13%) | +68 (+0.32%) | +36.7 |
| mais_iteracoes | +0 (+0.00%) | +67 (+0.31%) | +43.1 |
| adaptive_inertia | -17 (-0.08%) | +74 (+0.34%) | +54.0 |
| otimizado_completo | +17 (+0.08%) | +100 (+0.46%) | +47.1 |

## Analise do Impacto de Cada Melhoria

### Mais particulas (30 -> 100)

Aumentar o numero de particulas de 30 para 100 (mantendo demais parametros do artigo) 
reduz o gap medio de 1.26% para 0.94% (melhoria de 68 unidades na media).

### Mais iteracoes (100 -> 500)

Aumentar iteracoes de 100 para 500 reduz o gap medio de 1.26% para 0.95% (melhoria de 67 unidades na media).

### Inercia adaptativa (w fixo 0.8 -> w 0.9 a 0.4)

Adicionar inercia adaptativa (sobre mais_iteracoes) vai de gap 0.95% para 0.92%. A inercia alta no inicio favorece exploracao; baixa no final favorece convergencia.

### Otimizado completo (todas as melhorias)

Combinando todas as melhorias: gap medio cai de **1.26%** para **0.79%**, uma reducao de **0.5%** na media.

- Best: 21398 -> 21381 (melhoria de 17)
- Average: 21551 -> 21451 (melhoria de 100)
- Std: 96.7 -> 49.6

## Tempo de Execucao

| Config | Tempo total | Tempo/run |
|--------|------------|-----------|
| baseline_artigo | 11m 5s | 44.3s |
| mais_particulas | 36m 56s | 147.7s |
| mais_iteracoes | 33m 17s | 133.1s |
| adaptive_inertia | 33m 8s | 132.5s |
| otimizado_completo | 55m 24s | 221.6s |
| **TOTAL** | **169m 49s** | |

## Conclusao

O PSO com parametros do artigo (n=30, iter=100, w=0.8) nao atinge o otimo em kroA100, 
apresentando gap medio de 1.26%. Atraves de otimizacao sistematica:

1. **Mais particulas** (100): maior diversidade de solucoes iniciais para o 2-opt refinar
2. **Mais iteracoes** (500): mais oportunidades de recombinacao via velocidade PSO
3. **Inercia adaptativa** (0.9->0.4): exploracao ampla no inicio, convergencia no final

Conseguimos reduzir o gap medio para 0.79%, demonstrando que a 
otimizacao de parametros e significativa em instancias de maior porte.