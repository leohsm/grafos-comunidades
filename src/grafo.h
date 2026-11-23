/*
 * grafo.h - Estrutura de grafo não dirigido para redes sociais.
 *
 * Projeto: Detecção de Comunidades em Redes Sociais Utilizando
 *          Conectividade de Grafos
 * Equipe : Erik Mazzuco, Letícia Moro, Leonardo Herrero
 * UTFPR - Câmpus Medianeira | Ciência da Computação | Árvores e Grafos
 *
 * O grafo é armazenado em listas de adjacência. Cada aresta possui um
 * identificador (id) e aparece duas vezes nas listas (u->v e v->u), ambas
 * com o mesmo id. Vértices e arestas possuem marcas de "ativo", o que
 * permite remoções temporárias (simulação) sem destruir a estrutura.
 */
#ifndef GRAFO_H
#define GRAFO_H

#include <stdio.h>

#define MAX_NOME 64

typedef struct Adj {
    int destino;          /* vértice vizinho                     */
    int id;               /* identificador da aresta {u, v}      */
    struct Adj *prox;     /* próximo vizinho na lista            */
} Adj;

typedef struct {
    int u, v;             /* extremidades (u < v não é exigido)  */
} Aresta;

typedef struct {
    int n;                /* número de vértices (inclui inativos)   */
    int m;                /* número de arestas  (inclui inativas)   */
    int cap_v, cap_e;     /* capacidades alocadas                   */

    char  (*nome)[MAX_NOME]; /* nome (rótulo) de cada vértice       */
    Adj   **adj;          /* listas de adjacência                   */
    Aresta *aresta;       /* aresta[id] = {u, v}                    */

    unsigned char *v_ativo;  /* 1 = vértice presente na rede        */
    unsigned char *e_ativa;  /* 1 = aresta presente na rede         */

    /* tabela hash nome -> índice (endereçamento aberto) */
    int *hash;
    int  cap_hash;
} Grafo;

/* ---------- construção / destruição ---------- */
Grafo *grafo_criar(void);
void   grafo_destruir(Grafo *g);
int    grafo_vertice(Grafo *g, const char *nome);        /* busca ou cria  */
int    grafo_buscar_vertice(const Grafo *g, const char *nome); /* -1 se não */
int    grafo_adicionar_aresta(Grafo *g, int u, int v);   /* id ou -1       */
int    grafo_buscar_aresta(const Grafo *g, int u, int v);/* id ou -1       */
Grafo *grafo_ler_csv(const char *caminho, int *linhas_ignoradas);

/* ---------- métricas básicas (consideram apenas itens ativos) ---------- */
int    grafo_grau(const Grafo *g, int v);
int    grafo_n_ativos(const Grafo *g);
int    grafo_m_ativas(const Grafo *g);
double grafo_densidade(const Grafo *g);

/* ---------- remoção temporária ---------- */
void grafo_remover_vertice(Grafo *g, int v);
void grafo_remover_aresta_id(Grafo *g, int id);
void grafo_restaurar(Grafo *g);

/* aresta id está utilizável (ativa e com as duas pontas ativas)? */
static inline int aresta_ok(const Grafo *g, int id) {
    return g->e_ativa[id] && g->v_ativo[g->aresta[id].u] &&
           g->v_ativo[g->aresta[id].v];
}

/* ---------- visualização ---------- */
void grafo_imprimir_resumo(const Grafo *g, FILE *f);
void grafo_imprimir_adjacencia(const Grafo *g, FILE *f, int limite);

/* utilitário: aloca memória ou encerra o programa */
void *xmalloc(size_t n);
void *xcalloc(size_t n, size_t s);
void *xrealloc(void *p, size_t n);

#endif
