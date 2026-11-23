/*
 * comunidades.h - Centralidade de intermediação (Brandes) e detecção de
 * comunidades pelo algoritmo de Girvan-Newman (RF08).
 */
#ifndef COMUNIDADES_H
#define COMUNIDADES_H

#include "grafo.h"

/* Centralidade de intermediação (betweenness) pelo algoritmo de Brandes.
 * cb_vertice (tamanho n) e cb_aresta (tamanho m) podem ser NULL.
 * Apenas vértices com fonte[s] != 0 são usados como origem; passe
 * fonte = NULL para usar todos. Os valores são SOMADOS aos vetores
 * (que devem ser zerados pelo chamador) e já contam cada par {s,t} uma
 * única vez (grafo não dirigido). */
void brandes(const Grafo *g, const unsigned char *fonte,
             double *cb_vertice, double *cb_aresta);

/* Modularidade Q de uma partição 'rotulo' (rótulo < 0 = ignorado),
 * calculada sobre as arestas ATIVAS de g. */
double modularidade(const Grafo *g, const int *rotulo);

/* Um nível do dendrograma do Girvan-Newman */
typedef struct {
    int arestas_removidas;   /* quantas arestas já foram retiradas     */
    int n_comunidades;       /* componentes após a remoção             */
    int maior;               /* tamanho da maior componente            */
    double q;                /* modularidade em relação ao grafo base  */
    int *rotulo;             /* partição (tamanho n)                   */
} NivelGN;

typedef struct {
    NivelGN *nivel;          /* um nível a cada divisão do grafo       */
    int n_niveis;
    int melhor;              /* índice do nível de maior modularidade  */
    int *ordem_remocao;      /* ids das arestas na ordem de remoção    */
    double *cb_removida;     /* intermediação da aresta quando removida*/
    int *maior_apos;         /* maior componente após cada remoção     */
    int n_remocoes;
} ResultadoGN;

/* Executa o Girvan-Newman até remover todas as arestas (ou até
 * 'max_comunidades' componentes, se > 0). Não altera g. 'verbose' > 0
 * imprime em f as primeiras remoções. */
ResultadoGN *girvan_newman(Grafo *g, int max_comunidades, int verbose, FILE *f);
void girvan_newman_liberar(ResultadoGN *r);

/* Rotula componentes como uma partição (para comparar com comunidades) */
int particao_numero_grupos(const int *rotulo, int n);

#endif
