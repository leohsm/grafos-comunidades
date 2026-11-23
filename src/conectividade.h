/*
 * conectividade.h - Componentes conexas, pontes, vértices de articulação,
 * componentes biconexas e conectividade por vértices/arestas
 * (RF03 a RF07).
 */
#ifndef CONECTIVIDADE_H
#define CONECTIVIDADE_H

#include "grafo.h"

/* RF03/RF04 - componentes conexas via BFS.
 * comp[v] recebe o índice da componente (0..k-1) ou -1 se v está inativo.
 * tam (opcional, tamanho >= n) recebe o tamanho de cada componente.
 * Retorna o número k de componentes. */
int componentes_conexas(const Grafo *g, int *comp, int *tam);
int grafo_eh_conexo(const Grafo *g);
int maior_componente(const Grafo *g);   /* tamanho da maior componente */

/* RF05/RF06/RF07 - algoritmo de Tarjan (DFS com low-link). */
typedef struct {
    unsigned char *articulacao; /* [n] 1 se o vértice é de articulação   */
    unsigned char *ponte;       /* [m] 1 se a aresta é ponte             */
    int *bcc_aresta;            /* [m] componente biconexa de cada aresta*/
    int  n_articulacoes;
    int  n_pontes;
    int  n_bcc;                 /* número de componentes biconexas       */
} ResultadoTarjan;

ResultadoTarjan *tarjan(const Grafo *g);
void tarjan_liberar(ResultadoTarjan *r);

/* Vértices (marcados em 'marca', tamanho n) da componente biconexa b.
 * Retorna quantos vértices a componente possui. */
int bcc_vertices(const Grafo *g, const ResultadoTarjan *r, int b,
                 unsigned char *marca);

/* Conectividade por arestas lambda(G) e por vértices kappa(G), via fluxo
 * máximo (teorema de Menger). Recomendado para grafos moderados. */
int conectividade_arestas(const Grafo *g);
int conectividade_vertices(const Grafo *g);

/* Fluxo máximo / caminhos disjuntos entre dois vértices específicos */
int caminhos_arestas_disjuntos(const Grafo *g, int s, int t);
int caminhos_vertices_disjuntos(const Grafo *g, int s, int t);

#endif
