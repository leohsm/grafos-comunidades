/*
 * remocao.c - RF09: robustez da rede frente a remoções aleatórias e
 * orientadas (por grau ou por centralidade de intermediação).
 */
#include "remocao.h"
#include "comunidades.h"
#include "conectividade.h"

#include <stdlib.h>
#include <string.h>

const char *estrategia_nome(Estrategia e) {
    switch (e) {
        case ESTR_ALEATORIA:     return "aleatoria";
        case ESTR_GRAU:          return "grau";
        case ESTR_INTERMEDIACAO: return "intermediacao";
    }
    return "?";
}

unsigned aleatorio(unsigned *x) {
    unsigned v = *x ? *x : 2463534242u;
    v ^= v << 13; v ^= v >> 17; v ^= v << 5;
    return *x = v;
}

Instante instante_atual(const Grafo *g, int removidos) {
    Instante it;
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int *tam  = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    it.removidos = removidos;
    it.n_componentes = componentes_conexas(g, comp, tam);
    it.maior = 0;
    for (int i = 0; i < it.n_componentes; i++) if (tam[i] > it.maior) it.maior = tam[i];
    it.n_ativos = grafo_n_ativos(g);
    it.arestas_ativas = grafo_m_ativas(g);
    free(comp); free(tam);
    return it;
}

/* embaralhamento de Fisher-Yates */
static void embaralhar(int *v, int n, unsigned *estado) {
    for (int i = n - 1; i > 0; i--) {
        int j = (int)(aleatorio(estado) % (unsigned)(i + 1));
        int t = v[i]; v[i] = v[j]; v[j] = t;
    }
}

/* escolhe o próximo vértice a remover pela estratégia orientada */
static int proximo_vertice(const Grafo *g, Estrategia e, double *cb) {
    int melhor = -1;
    double vmelhor = -1;
    if (e == ESTR_INTERMEDIACAO) {
        memset(cb, 0, sizeof(double) * (size_t)g->n);
        brandes(g, NULL, cb, NULL);
    }
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        double val = (e == ESTR_GRAU) ? grafo_grau(g, v) : cb[v];
        if (val > vmelhor + 1e-9) { vmelhor = val; melhor = v; }
    }
    return melhor;
}

/* escolhe a próxima aresta a remover pela estratégia orientada */
static int proxima_aresta(const Grafo *g, Estrategia e, const double *cb, const int *grau) {
    int melhor = -1;
    double vmelhor = -1;
    for (int id = 0; id < g->m; id++) {
        if (!aresta_ok(g, id)) continue;
        double val = (e == ESTR_GRAU)
                   ? (double)grau[g->aresta[id].u] * grau[g->aresta[id].v]
                   : cb[id];
        if (val > vmelhor + 1e-9) { vmelhor = val; melhor = id; }
    }
    return melhor;
}

int simular_remocoes(Grafo *g, int alvo, Estrategia e, int max_passos,
                     int repeticoes, unsigned semente, double *curva_maior,
                     double *curva_comp) {
    /* guarda o estado atual para restaurar ao final */
    unsigned char *v_salvo = xmalloc((size_t)g->n + 1);
    unsigned char *e_salvo = xmalloc((size_t)g->m + 1);
    memcpy(v_salvo, g->v_ativo, (size_t)g->n);
    memcpy(e_salvo, g->e_ativa, (size_t)g->m);

    int n0 = grafo_n_ativos(g);
    int total = (alvo == 0) ? n0 : grafo_m_ativas(g);
    if (max_passos <= 0 || max_passos > total) max_passos = total;
    if (e != ESTR_ALEATORIA || repeticoes < 1) repeticoes = 1;

    for (int k = 0; k <= max_passos; k++) curva_maior[k] = curva_comp[k] = 0;

    int *itens = xmalloc(sizeof(int) * ((size_t)(g->n > g->m ? g->n : g->m) + 1));
    double *cbv = xcalloc((size_t)g->n + 1, sizeof(double));
    double *cbe = xcalloc((size_t)g->m + 1, sizeof(double));
    int *grau = xcalloc((size_t)g->n + 1, sizeof(int));
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    unsigned char *fonte = xmalloc((size_t)g->n + 1);
    unsigned estado = semente ? semente : 12345u;

    for (int rep = 0; rep < repeticoes; rep++) {
        memcpy(g->v_ativo, v_salvo, (size_t)g->n);
        memcpy(g->e_ativa, e_salvo, (size_t)g->m);

        /* ordem aleatória (preparada uma vez por repetição) */
        int nitens = 0;
        if (e == ESTR_ALEATORIA) {
            if (alvo == 0) { for (int v = 0; v < g->n; v++) if (g->v_ativo[v]) itens[nitens++] = v; }
            else           { for (int i = 0; i < g->m; i++) if (aresta_ok(g, i)) itens[nitens++] = i; }
            embaralhar(itens, nitens, &estado);
        }
        if (alvo == 1 && e == ESTR_INTERMEDIACAO) {
            memset(cbe, 0, sizeof(double) * (size_t)g->m);
            brandes(g, NULL, NULL, cbe);
        }

        Instante it = instante_atual(g, 0);
        curva_maior[0] += (double)it.maior / n0;
        curva_comp[0]  += it.n_componentes;

        for (int k = 1; k <= max_passos; k++) {
            if (alvo == 0) {
                int v = (e == ESTR_ALEATORIA) ? itens[k - 1] : proximo_vertice(g, e, cbv);
                grafo_remover_vertice(g, v);
            } else {
                int id;
                if (e == ESTR_ALEATORIA) id = itens[k - 1];
                else {
                    if (e == ESTR_GRAU)
                        for (int v = 0; v < g->n; v++) grau[v] = grafo_grau(g, v);
                    id = proxima_aresta(g, e, cbe, grau);
                }
                grafo_remover_aresta_id(g, id);
                if (e == ESTR_INTERMEDIACAO) {
                    /* recalcula a intermediação só nas componentes afetadas */
                    componentes_conexas(g, comp, NULL);
                    int cu = comp[g->aresta[id].u], cv = comp[g->aresta[id].v];
                    for (int v = 0; v < g->n; v++) fonte[v] = (comp[v] == cu || comp[v] == cv);
                    for (int i = 0; i < g->m; i++)
                        if (aresta_ok(g, i) && fonte[g->aresta[i].u]) cbe[i] = 0;
                    brandes(g, fonte, NULL, cbe);
                }
            }
            it = instante_atual(g, k);
            curva_maior[k] += (double)it.maior / n0;
            curva_comp[k]  += it.n_componentes;
        }
    }

    for (int k = 0; k <= max_passos; k++) {
        curva_maior[k] /= repeticoes;
        curva_comp[k]  /= repeticoes;
    }

    memcpy(g->v_ativo, v_salvo, (size_t)g->n);
    memcpy(g->e_ativa, e_salvo, (size_t)g->m);
    free(v_salvo); free(e_salvo); free(itens); free(cbv); free(cbe);
    free(grau); free(comp); free(fonte);
    return max_passos + 1;
}
