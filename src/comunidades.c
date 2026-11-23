/*
 * comunidades.c - RF08: Girvan-Newman com centralidade de intermediação
 * de arestas calculada pelo algoritmo de Brandes (2001).
 */
#include "comunidades.h"
#include "conectividade.h"

#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* Brandes: O(n m) para grafos não ponderados                          */
/* ------------------------------------------------------------------ */
void brandes(const Grafo *g, const unsigned char *fonte,
             double *cb_vertice, double *cb_aresta) {
    int n = g->n;
    int    *dist  = xmalloc(sizeof(int) * ((size_t)n + 1));
    double *sigma = xmalloc(sizeof(double) * ((size_t)n + 1));
    double *delta = xmalloc(sizeof(double) * ((size_t)n + 1));
    int    *ordem = xmalloc(sizeof(int) * ((size_t)n + 1)); /* fila BFS = pilha S */

    for (int s = 0; s < n; s++) {
        if (!g->v_ativo[s] || (fonte && !fonte[s])) continue;

        /* 1) BFS a partir de s: distâncias e número de caminhos mínimos */
        for (int v = 0; v < n; v++) { dist[v] = -1; sigma[v] = 0; delta[v] = 0; }
        dist[s] = 0; sigma[s] = 1;
        int ini = 0, fim = 0;
        ordem[fim++] = s;
        while (ini < fim) {
            int v = ordem[ini++];
            for (Adj *a = g->adj[v]; a; a = a->prox) {
                if (!aresta_ok(g, a->id)) continue;
                int w = a->destino;
                if (dist[w] < 0) { dist[w] = dist[v] + 1; ordem[fim++] = w; }
                if (dist[w] == dist[v] + 1) sigma[w] += sigma[v];
            }
        }

        /* 2) acumulação das dependências em ordem decrescente de distância */
        for (int i = fim - 1; i > 0; i--) {
            int w = ordem[i];
            for (Adj *a = g->adj[w]; a; a = a->prox) {
                if (!aresta_ok(g, a->id)) continue;
                int v = a->destino;
                if (dist[v] == dist[w] - 1) {          /* v é predecessor de w */
                    double c = sigma[v] / sigma[w] * (1.0 + delta[w]);
                    if (cb_aresta) cb_aresta[a->id] += c / 2.0;
                    delta[v] += c;
                }
            }
            if (cb_vertice) cb_vertice[w] += delta[w] / 2.0;
        }
    }
    free(dist); free(sigma); free(delta); free(ordem);
}

/* ------------------------------------------------------------------ */
/* Modularidade de Newman-Girvan                                       */
/*   Q = soma_c [ L_c / m  -  (D_c / 2m)^2 ]                           */
/* ------------------------------------------------------------------ */
static double modularidade_mascara(const Grafo *g, const unsigned char *usar,
                                   const int *rotulo) {
    int n = g->n;
    double *L = xcalloc((size_t)n + 1, sizeof(double)); /* arestas internas */
    double *D = xcalloc((size_t)n + 1, sizeof(double)); /* soma dos graus   */
    double m = 0;
    for (int e = 0; e < g->m; e++) {
        if (!usar[e]) continue;
        int u = g->aresta[e].u, v = g->aresta[e].v;
        if (rotulo[u] < 0 || rotulo[v] < 0) continue;
        m += 1;
        D[rotulo[u]] += 1;
        D[rotulo[v]] += 1;
        if (rotulo[u] == rotulo[v]) L[rotulo[u]] += 1;
    }
    double q = 0;
    if (m > 0)
        for (int c = 0; c < n; c++)
            q += L[c] / m - (D[c] / (2 * m)) * (D[c] / (2 * m));
    free(L); free(D);
    return q;
}

double modularidade(const Grafo *g, const int *rotulo) {
    unsigned char *usar = xmalloc((size_t)g->m + 1);
    for (int e = 0; e < g->m; e++) usar[e] = (unsigned char)aresta_ok(g, e);
    double q = modularidade_mascara(g, usar, rotulo);
    free(usar);
    return q;
}

int particao_numero_grupos(const int *rotulo, int n) {
    int mx = -1;
    for (int v = 0; v < n; v++) if (rotulo[v] > mx) mx = rotulo[v];
    return mx + 1;
}

/* ------------------------------------------------------------------ */
/* Girvan-Newman                                                       */
/* ------------------------------------------------------------------ */
static void gn_registrar(ResultadoGN *r, const Grafo *g, const unsigned char *base,
                         const int *comp, int k, int removidas, int *cap) {
    if (r->n_niveis == *cap) {
        *cap *= 2;
        r->nivel = xrealloc(r->nivel, sizeof(NivelGN) * (size_t)*cap);
    }
    NivelGN *nv = &r->nivel[r->n_niveis++];
    nv->arestas_removidas = removidas;
    nv->n_comunidades = k;
    nv->rotulo = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    memcpy(nv->rotulo, comp, sizeof(int) * (size_t)g->n);
    nv->q = modularidade_mascara(g, base, comp);
    int *tam = xcalloc((size_t)g->n + 1, sizeof(int));
    nv->maior = 0;
    for (int v = 0; v < g->n; v++)
        if (comp[v] >= 0 && ++tam[comp[v]] > nv->maior) nv->maior = tam[comp[v]];
    free(tam);
}

ResultadoGN *girvan_newman(Grafo *g, int max_comunidades, int verbose, FILE *f) {
    int n = g->n, m = g->m;
    ResultadoGN *r = xcalloc(1, sizeof(ResultadoGN));
    int cap = 16;
    r->nivel = xmalloc(sizeof(NivelGN) * (size_t)cap);
    r->ordem_remocao = xmalloc(sizeof(int) * ((size_t)m + 1));
    r->cb_removida   = xmalloc(sizeof(double) * ((size_t)m + 1));
    r->maior_apos    = xmalloc(sizeof(int) * ((size_t)m + 1));

    /* arestas do grafo base (estado atual da rede) */
    unsigned char *base = xmalloc((size_t)m + 1);
    for (int e = 0; e < m; e++) base[e] = (unsigned char)aresta_ok(g, e);

    double *cb = xcalloc((size_t)m + 1, sizeof(double));
    int *comp  = xmalloc(sizeof(int) * ((size_t)n + 1));
    int *tam   = xmalloc(sizeof(int) * ((size_t)n + 1));
    unsigned char *fonte = xmalloc((size_t)n + 1);

    int k = componentes_conexas(g, comp, tam);
    gn_registrar(r, g, base, comp, k, 0, &cap);
    brandes(g, NULL, NULL, cb);

    for (;;) {
        if (max_comunidades > 0 && k >= max_comunidades) break;

        /* 1) aresta de maior intermediação (empate: menor id) */
        int alvo = -1;
        for (int e = 0; e < m; e++)
            if (aresta_ok(g, e) && (alvo < 0 || cb[e] > cb[alvo] + 1e-9)) alvo = e;
        if (alvo < 0) break;                    /* não restam arestas */

        /* 2) remove a aresta */
        g->e_ativa[alvo] = 0;
        r->ordem_remocao[r->n_remocoes] = alvo;
        r->cb_removida[r->n_remocoes] = cb[alvo];
        int removidas = ++r->n_remocoes;
        if (verbose > 0 && removidas <= verbose && f)
            fprintf(f, "  remocao %3d: {%s, %s}  intermediacao = %.2f\n", removidas,
                    g->nome[g->aresta[alvo].u], g->nome[g->aresta[alvo].v], cb[alvo]);

        /* 3) recalcula componentes; registra um nível se o grafo se dividiu */
        int novo_k = componentes_conexas(g, comp, tam);
        int maior = 0;
        for (int i = 0; i < novo_k; i++) if (tam[i] > maior) maior = tam[i];
        r->maior_apos[removidas - 1] = maior;
        if (novo_k > k) gn_registrar(r, g, base, comp, novo_k, removidas, &cap);
        k = novo_k;

        /* 4) recalcula a intermediação apenas nas componentes afetadas */
        int cu = comp[g->aresta[alvo].u], cv = comp[g->aresta[alvo].v];
        for (int v = 0; v < n; v++) fonte[v] = (comp[v] == cu || comp[v] == cv);
        for (int e = 0; e < m; e++)
            if (aresta_ok(g, e) && fonte[g->aresta[e].u]) cb[e] = 0;
        brandes(g, fonte, NULL, cb);
    }

    /* restaura as arestas retiradas */
    for (int i = 0; i < r->n_remocoes; i++) g->e_ativa[r->ordem_remocao[i]] = 1;

    r->melhor = 0;
    for (int i = 1; i < r->n_niveis; i++)
        if (r->nivel[i].q > r->nivel[r->melhor].q + 1e-12) r->melhor = i;

    free(base); free(cb); free(comp); free(tam); free(fonte);
    return r;
}

void girvan_newman_liberar(ResultadoGN *r) {
    if (!r) return;
    for (int i = 0; i < r->n_niveis; i++) free(r->nivel[i].rotulo);
    free(r->nivel); free(r->ordem_remocao); free(r->cb_removida);
    free(r->maior_apos); free(r);
}
