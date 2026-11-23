# Detecção de Comunidades em Redes Sociais Utilizando Conectividade de Grafos

Equipe: Erik Mazzuco, Letícia Moro, Leonardo Herrero
UTFPR – Câmpus Medianeira | Ciência da Computação | Árvores e Grafos

Implementação em C (C99) de: leitura de amizades em CSV, métricas da rede, componentes
conexas (BFS), vértices de articulação, pontes e componentes biconexas (Tarjan),
conectividade por vértices e por arestas (Menger / fluxo máximo), comunidades
(Girvan–Newman com intermediação de Brandes e modularidade) e simulação de remoções
(aleatória × grau × intermediação).

## Compilar

    make                       # ou: gcc -std=c99 -O2 -o redes src/*.c -lm

## Usar

    ./redes dados/amizades.csv                         # menu interativo
    ./redes dados/amizades.csv -r resultados/amizades  # relatório completo (RF10)
    make experimentos                                  # relatórios de todas as redes

Saídas do modo relatório: `relatorio.txt`, `vertices.csv`, `arestas.csv`,
`girvan_newman.csv`, `remocao_vertices.csv`, `remocao_arestas.csv`, `grafo.svg`, `grafo.dot`.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `src/` | código-fonte em C (grafo, conectividade, comunidades, remoção, relatório, main) |
| `dados/` | `amizades.csv` (enunciado), `rede_social.csv` (fictícia), `karate.csv` (Zachary), `facebook_ego0.csv` (SNAP) |
| `resultados/` | relatórios gerados por `make experimentos` |
| `relatorio/` | relatório técnico (`.docx` e `.pdf`), figuras e scripts que os geram |
| `scripts/` | `gerar_dados.py` (karate e SNAP) e `validar.py` (comparação com NetworkX) |

Os scripts Python são auxiliares (dados, validação e figuras); o programa em C não depende deles.
