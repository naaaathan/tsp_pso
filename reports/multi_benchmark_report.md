# Benchmark Multi-Instancia: Baseline do Artigo vs Configuracao Otimizada

## Configuracoes

| Config | Particulas | Iteracoes | Inercia | c1 | c2 |
|--------|------------|-----------|---------|----|----|
| baseline_artigo | 30 | 100 | 0.8 fixo | 2.0 | 2.0 |
| otimizado | 50 | 300 | 0.9->0.4 (adaptativa) | 2.0 | 2.0 |

## Resultados (15 runs por configuracao)

### Tabela Consolidada

| Instancia | Cidades | Otimo | Config | Best | Avg | Std | Gap% (avg) | Tempo/run |
|-----------|---------|-------|--------|------|-----|-----|------------|-----------|
| eil76 | ? | 538 | baseline_artigo | 545 | 549 | 2.6 | +1.96% | 25.4s |
| eil76 | ? | 538 | otimizado | 540 | 544 | 2.8 | +1.20% | 127.7s |
| kroB100 | ? | 22141 | baseline_artigo | 22282 | 22383 | 48.6 | +1.09% | 49.3s |
| kroB100 | ? | 22141 | otimizado | 22157 | 22258 | 59.6 | +0.53% | 244.0s |

### Melhoria do Otimizado sobre o Baseline

| Instancia | Gap Baseline | Gap Otimizado | Reducao Gap | Reducao Std |
|-----------|-------------|---------------|-------------|-------------|
| eil76 | 1.96% | 1.20% | 0.76pp (39%) | -0.2 |
| kroB100 | 1.09% | 0.53% | 0.56pp (52%) | -11.1 |

## Conclusao

A configuracao otimizada (n=50, iter=300, inercia adaptativa 0.9->0.4) apresenta 
melhoria consistente em todas as instancias testadas onde o baseline nao atinge o otimo.
Os resultados complementam o benchmark kroA100, demonstrando que a otimizacao de 
parametros nao e especifica a uma unica instancia.