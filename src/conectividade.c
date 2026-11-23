/*
 * conectividade.c - RF03 a RF07.
 *
 *  - Componentes conexas: busca em largura (BFS), O(n + m).
 *  - Pontes, articulações e componentes biconexas: algoritmo de Tarjan
 *    (Hopcroft-Tarjan), DFS iterativa com valores disc/low, O(n + m).
 *  - Conectividade por vértices e arestas: fluxo máximo (Edmonds-Karp)
 *    com capacidades unitárias, aplicando o teorema de Menger.
 */
#include "conectividade.h"

#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* RF03 / RF04 - componentes conexas (BFS)                             */
/* ------------------------------------------------------------------ */
int componentes_conexas(const Grafo *g, int *comp, int *tam) {
    int *fila = xmalloc(sizeof(int) * (size_t)(g->n + 1));
    int k = 0;
    for (int v = 0; v < g->n; v++) comp[v] = -1;

    for (int s = 0; s < g->n; s++) {
        if (!g->v_ativo[s] || comp[s] != -1) continue;
        int ini = 0, fim = 0, cont = 0;
        fila[fim++] = s;
        comp[s] = k;
        while (ini < fim) {
            int u = fila[ini++];
            cont++;
            for (Adj *a = g->adj[u]; a; a = a->prox) {
                if (!aresta_ok(g, a->id)) continue;
                int w = a->destino;
                if (comp[w] == -1) { comp[w] = k; fila[fim++] = w; }
            }
        }
        if (tam) tam[k] = cont;
        k++;
    }
    free(fila);
    return k;
}

int grafo_eh_conexo(const Grafo *g) {
    int *comp = xmalloc(sizeof(int) * (size_t)(g->n + 1));
    int k = componentes_conexas(g, comp, NULL);
    free(comp);
    return k <= 1;
}

int maior_componente(const Grafo *g) {
    int *comp = xmalloc(sizeof(int) * (size_t)(g->n + 1));
    int *tam  = xmalloc(sizeof(int) * (size_t)(g->n + 1));
    int k = componentes_conexas(g, comp, tam), maior = 0;
    for (int i = 0; i < k; i++) if (tam[i] > maior) maior = tam[i];
    free(comp); free(tam);
    return maior;
}

/* ------------------------------------------------------------------ */
/* RF05 / RF06 / RF07 - Tarjan                                         */
/* ------------------------------------------------------------------ */
typedef struct {
    int v;          /* vértice do quadro                      */
    int aresta_pai; /* id da aresta pela qual v foi alcançado */
    Adj *it;        /* próximo vizinho a examinar             */
} Quadro;

ResultadoTarjan *tarjan(const Grafo *g) {
    int n = g->n, m = g->m;
    ResultadoTarjan *r = xcalloc(1, sizeof(ResultadoTarjan));
    r->articulacao = xcalloc((size_t)n + 1, 1);
    r->ponte       = xcalloc((size_t)m + 1, 1);
    r->bcc_aresta  = xmalloc(sizeof(int) * ((size_t)m + 1));
    for (int e = 0; e < m; e++) r->bcc_aresta[e] = -1;

    int *disc = xmalloc(sizeof(int) * ((size_t)n + 1));
    int *low  = xmalloc(sizeof(int) * ((size_t)n + 1));
    for (int v = 0; v < n; v++) disc[v] = -1;

    Quadro *pilha  = xmalloc(sizeof(Quadro) * ((size_t)n + 1)); /* pilha da DFS     */
    int    *pilhaE = xmalloc(sizeof(int) * ((size_t)m + 1));    /* pilha de arestas */
    int topo = 0, topoE = 0, tempo = 0;

    for (int raiz = 0; raiz < n; raiz++) {
        if (!g->v_ativo[raiz] || disc[raiz] != -1) continue;
        int filhos_raiz = 0;
        disc[raiz] = low[raiz] = tempo++;
        pilha[topo++] = (Quadro){raiz, -1, g->adj[raiz]};

        while (topo > 0) {
            Quadro *q = &pilha[topo - 1];
            int u = q->v;

            /* avança até o próximo vizinho utilizável */
            while (q->it && !aresta_ok(g, q->it->id)) q->it = q->it->prox;

            if (q->it) {
                Adj *a = q->it;
                q->it = a->prox;
                int w = a->destino, id = a->id;
                if (id == q->aresta_pai) continue;         /* aresta de volta ao pai */
                if (disc[w] == -1) {                        /* aresta de árvore       */
                    pilhaE[topoE++] = id;
                    disc[w] = low[w] = tempo++;
                    pilha[topo++] = (Quadro){w, id, g->adj[w]};
                } else if (disc[w] < disc[u]) {             /* aresta de retorno      */
                    pilhaE[topoE++] = id;
                    if (disc[w] < low[u]) low[u] = disc[w];
                }
            } else {
                /* todos os vizinhos de u foram examinados: retrocede */
                int aresta_pai = q->aresta_pai;
                topo--;
                if (topo == 0) break;
                int p = pilha[topo - 1].v;
                if (low[u] < low[p]) low[p] = low[u];

                if (low[u] > disc[p]) {                     /* ponte */
                    r->ponte[aresta_pai] = 1;
                    r->n_pontes++;
                }
                if (low[u] >= disc[p]) {
                    /* p separa a subárvore de u: fecha uma componente biconexa */
                    if (p == raiz) filhos_raiz++;
                    else if (!r->articulacao[p]) { r->articulacao[p] = 1; r->n_articulacoes++; }
                    int e;
                    do {
                        e = pilhaE[--topoE];
                        r->bcc_aresta[e] = r->n_bcc;
                    } while (e != aresta_pai);
                    r->n_bcc++;
                }
            }
        }
        if (filhos_raiz >= 2) { r->articulacao[raiz] = 1; r->n_articulacoes++; }
    }

    free(disc); free(low); free(pilha); free(pilhaE);
    return r;
}

void tarjan_liberar(ResultadoTarjan *r) {
    if (!r) return;
    free(r->articulacao); free(r->ponte); free(r->bcc_aresta); free(r);
}

int bcc_vertices(const Grafo *g, const ResultadoTarjan *r, int b, unsigned char *marca) {
    memset(marca, 0, (size_t)g->n);
    int c = 0;
    for (int e = 0; e < g->m; e++) {
        if (r->bcc_aresta[e] != b) continue;
        int u = g->aresta[e].u, v = g->aresta[e].v;
        if (!marca[u]) { marca[u] = 1; c++; }
        if (!marca[v]) { marca[v] = 1; c++; }
    }
    return c;
}

/* ------------------------------------------------------------------ */
/* Fluxo máximo (Edmonds-Karp) para o teorema de Menger                */
/* ------------------------------------------------------------------ */
typedef struct {
    int nn, na, cap_a;
    int *cab;          /* primeiro arco de cada nó  */
    int *prox, *para;  /* lista encadeada de arcos  */
    int *cap, *cap0;   /* capacidade residual / original */
} Rede;

static Rede *rede_criar(int nn, int cap_a) {
    Rede *r = xcalloc(1, sizeof(Rede));
    r->nn = nn; r->cap_a = cap_a;
    r->cab  = xmalloc(sizeof(int) * (size_t)nn);
    for (int i = 0; i < nn; i++) r->cab[i] = -1;
    r->prox = xmalloc(sizeof(int) * (size_t)cap_a);
    r->para = xmalloc(sizeof(int) * (size_t)cap_a);
    r->cap  = xmalloc(sizeof(int) * (size_t)cap_a);
    r->cap0 = xmalloc(sizeof(int) * (size_t)cap_a);
    return r;
}

static void rede_liberar(Rede *r) {
    free(r->cab); free(r->prox); free(r->para); free(r->cap); free(r->cap0); free(r);
}

/* cria o par de arcos u->v (capacidade c) e v->u (capacidade c_rev);
 * o arco i tem como reverso o arco i^1 */
static void rede_arco(Rede *r, int u, int v, int c, int c_rev) {
    int i = r->na;
    r->para[i] = v; r->cap0[i] = c;     r->prox[i] = r->cab[u]; r->cab[u] = i;
    r->para[i + 1] = u; r->cap0[i + 1] = c_rev; r->prox[i + 1] = r->cab[v]; r->cab[v] = i + 1;
    r->na += 2;
}

/* fluxo máximo de s a t, interrompido quando atinge 'limite' */
static int rede_fluxo(Rede *r, int s, int t, int limite, int *fila, int *arco_pai) {
    memcpy(r->cap, r->cap0, sizeof(int) * (size_t)r->na);
    int fluxo = 0;
    while (fluxo < limite) {
        for (int i = 0; i < r->nn; i++) arco_pai[i] = -2;
        arco_pai[s] = -1;
        int ini = 0, fim = 0;
        fila[fim++] = s;
        while (ini < fim && arco_pai[t] == -2) {
            int u = fila[ini++];
            for (int a = r->cab[u]; a != -1; a = r->prox[a]) {
                int w = r->para[a];
                if (r->cap[a] > 0 && arco_pai[w] == -2) {
                    arco_pai[w] = a;
                    fila[fim++] = w;
                }
            }
        }
        if (arco_pai[t] == -2) break;            /* não há caminho aumentante */
        int gargalo = 1 << 30;
        for (int v = t; v != s; v = r->para[arco_pai[v] ^ 1])
            if (r->cap[arco_pai[v]] < gargalo) gargalo = r->cap[arco_pai[v]];
        for (int v = t; v != s; v = r->para[arco_pai[v] ^ 1]) {
            r->cap[arco_pai[v]] -= gargalo;
            r->cap[arco_pai[v] ^ 1] += gargalo;
        }
        fluxo += gargalo;
    }
    return fluxo < limite ? fluxo : limite;
}

/* rede para caminhos aresta-disjuntos: cada aresta não dirigida vira um
 * par de arcos de capacidade 1 que são reversos um do outro */
static Rede *rede_arestas(const Grafo *g) {
    Rede *r = rede_criar(g->n, 2 * g->m + 2);
    for (int e = 0; e < g->m; e++)
        if (aresta_ok(g, e)) rede_arco(r, g->aresta[e].u, g->aresta[e].v, 1, 1);
    return r;
}

/* rede para caminhos vértice-disjuntos: cada vértice v vira v_in = 2v e
 * v_out = 2v+1 ligados por um arco de capacidade 1 */
static Rede *rede_vertices(const Grafo *g) {
    int INF = g->n + 1;
    Rede *r = rede_criar(2 * g->n, 2 * g->n + 4 * g->m + 2);
    for (int v = 0; v < g->n; v++)
        if (g->v_ativo[v]) rede_arco(r, 2 * v, 2 * v + 1, 1, 0);
    for (int e = 0; e < g->m; e++) {
        if (!aresta_ok(g, e)) continue;
        int u = g->aresta[e].u, v = g->aresta[e].v;
        rede_arco(r, 2 * u + 1, 2 * v, INF, 0);
        rede_arco(r, 2 * v + 1, 2 * u, INF, 0);
    }
    return r;
}

int caminhos_arestas_disjuntos(const Grafo *g, int s, int t) {
    if (s == t) return 0;
    Rede *r = rede_arestas(g);
    int *fila = xmalloc(sizeof(int) * (size_t)r->nn);
    int *pai  = xmalloc(sizeof(int) * (size_t)r->nn);
    int f = rede_fluxo(r, s, t, 1 << 30, fila, pai);
    free(fila); free(pai); rede_liberar(r);
    return f;
}

int caminhos_vertices_disjuntos(const Grafo *g, int s, int t) {
    if (s == t) return 0;
    if (grafo_buscar_aresta(g, s, t) >= 0 &&
        aresta_ok(g, grafo_buscar_aresta(g, s, t)))
        return -1;      /* adjacentes: nenhum conjunto de vértices os separa */
    Rede *r = rede_vertices(g);
    int *fila = xmalloc(sizeof(int) * (size_t)r->nn);
    int *pai  = xmalloc(sizeof(int) * (size_t)r->nn);
    int f = rede_fluxo(r, 2 * s + 1, 2 * t, 1 << 30, fila, pai);
    free(fila); free(pai); rede_liberar(r);
    return f;
}

/* lambda(G) = min_{t != s} fluxo(s, t), para um s fixo qualquer */
int conectividade_arestas(const Grafo *g) {
    int n = grafo_n_ativos(g);
    if (n <= 1 || !grafo_eh_conexo(g)) return 0;

    int s = -1, melhor = 1 << 30;
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        if (s < 0) s = v;
        int d = grafo_grau(g, v);
        if (d < melhor) melhor = d;          /* lambda <= grau mínimo */
    }
    Rede *r = rede_arestas(g);
    int *fila = xmalloc(sizeof(int) * (size_t)r->nn);
    int *pai  = xmalloc(sizeof(int) * (size_t)r->nn);
    for (int t = 0; t < g->n && melhor > 0; t++) {
        if (t == s || !g->v_ativo[t]) continue;
        int f = rede_fluxo(r, s, t, melhor, fila, pai);
        if (f < melhor) melhor = f;
    }
    free(fila); free(pai); rede_liberar(r);
    return melhor;
}

/* kappa(G) pelo algoritmo de Even (1975): basta testar pares (v_i, v_j)
 * não adjacentes com i <= kappa atual. Para grafo completo, n - 1. */
int conectividade_vertices(const Grafo *g) {
    int n = grafo_n_ativos(g);
    if (n <= 1) return 0;
    if (!grafo_eh_conexo(g)) return 0;

    int *lista = xmalloc(sizeof(int) * (size_t)n);
    int k = 0, melhor = n - 1;
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        lista[k++] = v;
        int d = grafo_grau(g, v);
        if (d < melhor) melhor = d;          /* kappa <= lambda <= grau mínimo */
    }

    Rede *r = rede_vertices(g);
    int *fila = xmalloc(sizeof(int) * (size_t)r->nn);
    int *pai  = xmalloc(sizeof(int) * (size_t)r->nn);
    for (int i = 0; i < n && i <= melhor; i++) {
        for (int j = i + 1; j < n && melhor > 0; j++) {
            int s = lista[i], t = lista[j];
            int id = grafo_buscar_aresta(g, s, t);
            if (id >= 0 && aresta_ok(g, id)) continue;   /* adjacentes */
            int f = rede_fluxo(r, 2 * s + 1, 2 * t, melhor, fila, pai);
            if (f < melhor) melhor = f;
        }
    }
    free(fila); free(pai); rede_liberar(r); free(lista);
    return melhor;
}
