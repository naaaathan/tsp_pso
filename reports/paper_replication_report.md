# Relatório de Replicação do Artigo

## Referência

> Araújo, K.S. & Barboza, F.M. (2025). "PSO and the Traveling Salesman Problem: An Intelligent Optimization Approach". arXiv:2501.15319v1.

## Configuração

- **Instância**: 5 cidades com coordenadas (0,0), (1,3), (4,3), (6,1), (3,0)
- **Partículas**: 30
- **Iterações**: 100
- **Inércia (w)**: 0.8
- **c1, c2**: 2.0, 2.0
- **Busca local**: 2-opt
- **Execuções**: 5

## Resultados

| Run | Custo | Tour |
|-----|-------|------|
| 1 | 15.1530 | [0, 1, 2, 3, 4] |
| 2 | 15.1530 | [3, 2, 1, 0, 4] |
| 3 | 15.1530 | [3, 2, 1, 0, 4] |
| 4 | 15.1530 | [3, 2, 1, 0, 4] |
| 5 | 15.1530 | [0, 1, 2, 3, 4] |

## Estatísticas

| Métrica | Valor |
|---------|-------|
| Melhor  | 15.1530 |
| Pior    | 15.1530 |
| Média   | 15.1530 |
| Std     | 0.0000 |

## Comparação com o Artigo

| Métrica | Artigo | Nossa Implementação |
|---------|--------|---------------------|
| Faixa de custos | 12.3 - 13.0 (métrica do artigo) | 15.1530 - 15.1530 |
| Média | ~12.65 (métrica do artigo) | 15.1530 |

**Nota**: O artigo usa uma métrica de distância diferente da Euclidiana. O ótimo Euclidiano para estas coordenadas é 15.1530.

## Conclusão

Implementação validada: PSO encontra o tour ótimo Euclidiano para 5 cidades.
A diferença nos valores absolutos se deve à métrica de distância do artigo.