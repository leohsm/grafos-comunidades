/*
 * relatorio.c - RF02 (visualização) e RF10 (relatório de métricas).
 */
#include "relatorio.h"
#include "remocao.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <direct.h>
#define MKDIR(p) _mkdir(p)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(p) mkdir(p, 0755)
#endif

#define LIMITE_LISTA 40          /* máximo de nomes listados por grupo        */
#define LIMITE_KAPPA 3000        /* kappa/lambda só para grafos moderados     */
#define LIMITE_GN    20000       /* Girvan-Newman só até este número de arestas */

int criar_diretorio(const char *dir) {
    MKDIR(dir);                  /* se já existir, o erro é ignorado */
    return 0;
}

static void linha(FILE *f) {
    fprintf(f, "----------------------------------------------------------------------\n");
}

static void titulo(FILE *f, const char *t) {
    fprintf(f, "\n======================================================================\n");
    fprintf(f, " %s\n", t);
    fprintf(f, "======================================================================\n");
}

/* imprime os nomes dos vértices v com grupo[v] == alvo */
static void listar_grupo(const Grafo *g, const int *grupo, int alvo, FILE *f) {
    int c = 0, total = 0;
    for (int v = 0; v < g->n; v++) if (grupo[v] == alvo) total++;
    fprintf(f, "{");
    for (int v = 0; v < g->n; v++) {
        if (grupo[v] != alvo) continue;
        if (c == LIMITE_LISTA) { fprintf(f, ", ... +%d", total - c); break; }
        fprintf(f, "%s%s", c ? ", " : "", g->nome[v]);
        c++;
    }
    fprintf(f, "}");
}

/* ------------------------------------------------------------------ */
/* Etapa 1 - construção da rede                                        */
/* ------------------------------------------------------------------ */
static const Grafo *g_ordem;
static int cmp_grau_desc(const void *a, const void *b) {
    int u = *(const int *)a, v = *(const int *)b;
    int du = grafo_grau(g_ordem, u), dv = grafo_grau(g_ordem, v);
    if (du != dv) return dv - du;
    return u - v;
}

void secao_rede(const Grafo *g, FILE *f) {
    titulo(f, "ETAPA 1 - CONSTRUCAO DA REDE");
    grafo_imprimir_resumo(g, f);

    int n = 0;
    int *ord = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    for (int v = 0; v < g->n; v++) if (g->v_ativo[v]) ord[n++] = v;
    g_ordem = g;
    qsort(ord, (size_t)n, sizeof(int), cmp_grau_desc);

    int mostrar = n <= 60 ? n : 15;
    fprintf(f, "\nGrau de cada vertice%s:\n", n <= 60 ? "" : " (15 maiores)");
    for (int i = 0; i < mostrar; i++)
        fprintf(f, "  %-14s %3d\n", g->nome[ord[i]], grafo_grau(g, ord[i]));

    /* distribuição de graus */
    int gmax = n ? grafo_grau(g, ord[0]) : 0;
    int *hist = xcalloc((size_t)gmax + 2, sizeof(int));
    for (int i = 0; i < n; i++) hist[grafo_grau(g, ord[i])]++;
    fprintf(f, "\nDistribuicao de graus (grau: quantidade):\n  ");
    int col = 0;
    for (int d = 0; d <= gmax; d++) {
        if (!hist[d]) continue;
        fprintf(f, "%d:%d  ", d, hist[d]);
        if (++col % 10 == 0) fprintf(f, "\n  ");
    }
    fprintf(f, "\n");
    free(hist); free(ord);
}

/* ------------------------------------------------------------------ */
/* Etapa 2 - conectividade                                             */
/* ------------------------------------------------------------------ */
void secao_componentes(const Grafo *g, FILE *f) {
    titulo(f, "ETAPA 2a - COMPONENTES CONEXAS (BFS)");
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int *tam  = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int k = componentes_conexas(g, comp, tam);
    int n = grafo_n_ativos(g), maior = 0;
    for (int i = 0; i < k; i++) if (tam[i] > maior) maior = tam[i];

    fprintf(f, "O grafo %s conexo.\n", k <= 1 ? "E" : "NAO e");
    fprintf(f, "Numero de componentes conexas: %d\n", k);
    fprintf(f, "Maior componente: %d vertices (%.1f%% da rede)\n", maior,
            n ? 100.0 * maior / n : 0.0);
    int mostrar = k <= 30 ? k : 30;
    for (int i = 0; i < mostrar; i++) {
        fprintf(f, "  C%-3d (%3d vertices): ", i + 1, tam[i]);
        listar_grupo(g, comp, i, f);
        fprintf(f, "\n");
    }
    if (k > mostrar) fprintf(f, "  ... (%d componentes omitidas)\n", k - mostrar);
    free(comp); free(tam);
}

void secao_tarjan(const Grafo *g, FILE *f) {
    ResultadoTarjan *r = tarjan(g);

    titulo(f, "ETAPA 2b - VERTICES DE ARTICULACAO (usuarios criticos)");
    fprintf(f, "Total: %d\n", r->n_articulacoes);
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int k0 = componentes_conexas(g, comp, NULL);
    int c = 0;
    for (int v = 0; v < g->n; v++) {
        if (!r->articulacao[v]) continue;
        if (c++ == 60) { fprintf(f, "  ...\n"); break; }
        /* efeito da remoção isolada de v */
        Grafo *gg = (Grafo *)g;
        gg->v_ativo[v] = 0;
        int k1 = componentes_conexas(g, comp, NULL);
        gg->v_ativo[v] = 1;
        fprintf(f, "  %-14s grau %3d  -> remocao gera %d componente(s) (antes %d)\n",
                g->nome[v], grafo_grau(g, v), k1, k0);
    }

    titulo(f, "ETAPA 2c - PONTES (conexoes criticas)");
    fprintf(f, "Total: %d\n", r->n_pontes);
    c = 0;
    for (int e = 0; e < g->m; e++) {
        if (!r->ponte[e]) continue;
        if (c++ == 60) { fprintf(f, "  ...\n"); break; }
        fprintf(f, "  {%s, %s}\n", g->nome[g->aresta[e].u], g->nome[g->aresta[e].v]);
    }
    free(comp);
    tarjan_liberar(r);
}

void secao_biconexas(const Grafo *g, FILE *f) {
    ResultadoTarjan *r = tarjan(g);
    titulo(f, "ETAPA 2d - COMPONENTES BICONEXAS (por vertices)");
    fprintf(f, "Total: %d\n", r->n_bcc);
    unsigned char *marca = xmalloc((size_t)g->n + 1);
    int *grupo = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int mostrar = r->n_bcc <= 40 ? r->n_bcc : 40;
    for (int b = 0; b < mostrar; b++) {
        int nv = bcc_vertices(g, r, b, marca), ne = 0;
        for (int e = 0; e < g->m; e++) ne += (r->bcc_aresta[e] == b);
        for (int v = 0; v < g->n; v++) grupo[v] = marca[v] ? 0 : -1;
        fprintf(f, "  B%-3d (%3d vertices, %3d arestas%s): ", b + 1, nv, ne,
                ne == 1 ? ", ponte" : "");
        listar_grupo(g, grupo, 0, f);
        fprintf(f, "\n");
    }
    if (r->n_bcc > mostrar) fprintf(f, "  ... (%d omitidas)\n", r->n_bcc - mostrar);
    free(marca); free(grupo);
    tarjan_liberar(r);
}

/* desativa os vértices fora da maior componente; devolve cópia do estado */
static unsigned char *isolar_maior_componente(Grafo *g) {
    unsigned char *salvo = xmalloc((size_t)g->n + 1);
    memcpy(salvo, g->v_ativo, (size_t)g->n);
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int *tam  = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    int k = componentes_conexas(g, comp, tam), m = 0;
    for (int i = 1; i < k; i++) if (tam[i] > tam[m]) m = i;
    for (int v = 0; v < g->n; v++) if (comp[v] != m) g->v_ativo[v] = 0;
    free(comp); free(tam);
    return salvo;
}

void secao_kappa_lambda(Grafo *g, FILE *f) {
    titulo(f, "ETAPA 2e - CONECTIVIDADE POR VERTICES E POR ARESTAS (Menger)");
    int n = grafo_n_ativos(g);
    if (n > LIMITE_KAPPA) {
        fprintf(f, "Grafo com %d vertices: calculo omitido (limite %d).\n", n, LIMITE_KAPPA);
        return;
    }
    int gmin = -1;
    for (int v = 0; v < g->n; v++)
        if (g->v_ativo[v] && (gmin < 0 || grafo_grau(g, v) < gmin)) gmin = grafo_grau(g, v);
    fprintf(f, "Rede completa : kappa(G) = %d, lambda(G) = %d, grau minimo = %d\n",
            conectividade_vertices(g), conectividade_arestas(g), gmin);
    if (!grafo_eh_conexo(g)) {
        unsigned char *salvo = isolar_maior_componente(g);
        gmin = -1;
        for (int v = 0; v < g->n; v++)
            if (g->v_ativo[v] && (gmin < 0 || grafo_grau(g, v) < gmin)) gmin = grafo_grau(g, v);
        fprintf(f, "Maior compon. : kappa = %d, lambda = %d, grau minimo = %d (%d vertices)\n",
                conectividade_vertices(g), conectividade_arestas(g), gmin, grafo_n_ativos(g));
        memcpy(g->v_ativo, salvo, (size_t)g->n);
        free(salvo);
    }
    fprintf(f, "(kappa <= lambda <= grau minimo - desigualdade de Whitney)\n");
}

/* ------------------------------------------------------------------ */
/* Etapa 3 - comunidades                                               */
/* ------------------------------------------------------------------ */
ResultadoGN *secao_comunidades(Grafo *g, FILE *f, int verbose) {
    titulo(f, "ETAPA 3 - COMUNIDADES (Girvan-Newman)");
    if (grafo_m_ativas(g) > LIMITE_GN) {
        fprintf(f, "Rede com mais de %d arestas: Girvan-Newman omitido (O(m^2 n)).\n", LIMITE_GN);
        return NULL;
    }
    if (verbose) fprintf(f, "Primeiras remocoes (aresta de maior intermediacao):\n");
    ResultadoGN *r = girvan_newman(g, 0, verbose, f);

    fprintf(f, "\nNiveis do dendrograma (cada divisao da rede):\n");
    fprintf(f, "  %-10s %-12s %-14s %s\n", "removidas", "comunidades", "maior grupo", "modularidade Q");
    for (int i = 0; i < r->n_niveis; i++) {
        if (i >= 25 && i != r->melhor && i < r->n_niveis - 1) {
            if (i == 25) fprintf(f, "  ...\n");
            continue;
        }
        fprintf(f, "  %-10d %-12d %-14d %.4f%s\n", r->nivel[i].arestas_removidas,
                r->nivel[i].n_comunidades, r->nivel[i].maior, r->nivel[i].q,
                i == r->melhor ? "   <== maior Q" : "");
    }

    NivelGN *b = &r->nivel[r->melhor];
    int n = g->n;
    int *comp = xmalloc(sizeof(int) * ((size_t)n + 1));
    int kc = componentes_conexas(g, comp, NULL);

    fprintf(f, "\nMelhor particao: %d comunidades, Q = %.4f (apos remover %d arestas)\n",
            b->n_comunidades, b->q, b->arestas_removidas);
    linha(f);
    fprintf(f, "  %-5s %-6s %-9s %-9s %-9s %-10s %s\n", "Com.", "tam.", "internas",
            "de corte", "dens.int", "componente", "membros");
    int k = b->n_comunidades;
    int *tam = xcalloc((size_t)k + 1, sizeof(int));
    int *ints = xcalloc((size_t)k + 1, sizeof(int));
    int *cort = xcalloc((size_t)k + 1, sizeof(int));
    int *cmp_de = xmalloc(sizeof(int) * ((size_t)k + 1));
    for (int v = 0; v < n; v++)
        if (b->rotulo[v] >= 0) { tam[b->rotulo[v]]++; cmp_de[b->rotulo[v]] = comp[v]; }
    for (int e = 0; e < g->m; e++) {
        if (!aresta_ok(g, e)) continue;
        int cu = b->rotulo[g->aresta[e].u], cv = b->rotulo[g->aresta[e].v];
        if (cu == cv) ints[cu]++;
        else { cort[cu]++; cort[cv]++; }
    }
    int mostrar = k <= 40 ? k : 40;
    for (int c = 0; c < mostrar; c++) {
        double dens = tam[c] > 1 ? 2.0 * ints[c] / (tam[c] * (tam[c] - 1.0)) : 0.0;
        fprintf(f, "  K%-4d %-6d %-9d %-9d %-9.3f C%-9d ", c + 1, tam[c], ints[c], cort[c],
                dens, cmp_de[c] + 1);
        listar_grupo(g, b->rotulo, c, f);
        fprintf(f, "\n");
    }
    if (k > mostrar) fprintf(f, "  ... (%d comunidades omitidas)\n", k - mostrar);

    /* comparação com as componentes conexas */
    fprintf(f, "\nComparacao comunidades x componentes conexas:\n");
    fprintf(f, "  Componentes conexas do grafo original: %d\n", kc);
    fprintf(f, "  Comunidades (maior modularidade)      : %d\n", k);
    int *por_comp = xcalloc((size_t)kc + 1, sizeof(int));
    for (int c = 0; c < k; c++) por_comp[cmp_de[c]]++;
    for (int i = 0; i < kc && i < 30; i++)
        fprintf(f, "  Componente C%-3d contem %d comunidade(s)\n", i + 1, por_comp[i]);
    double q_comp = modularidade(g, comp);
    fprintf(f, "  Modularidade da particao por componentes: Q = %.4f\n", q_comp);
    fprintf(f, "  Toda comunidade esta contida em uma unica componente (as arestas\n"
               "  removidas pelo Girvan-Newman so podem dividir componentes).\n");

    free(comp); free(tam); free(ints); free(cort); free(cmp_de); free(por_comp);
    return r;
}

/* ------------------------------------------------------------------ */
/* Etapa 4 - simulação de remoções                                     */
/* ------------------------------------------------------------------ */
static int fracao_critica(const double *curva, int pontos, int total) {
    for (int k = 0; k < pontos; k++) if (curva[k] < 0.5) return k;
    (void)total;
    return -1;
}

static void tabela_remocao(Grafo *g, FILE *f, const char *dir, int alvo, unsigned semente) {
    int total = alvo == 0 ? grafo_n_ativos(g) : grafo_m_ativas(g);
    double *S[3], *C[3];
    int pontos = 0;
    for (int e = 0; e < 3; e++) {
        S[e] = xmalloc(sizeof(double) * ((size_t)total + 2));
        C[e] = xmalloc(sizeof(double) * ((size_t)total + 2));
        pontos = simular_remocoes(g, alvo, (Estrategia)e, total,
                                  e == ESTR_ALEATORIA ? 50 : 1, semente, S[e], C[e]);
    }
    int n0 = grafo_n_ativos(g);

    fprintf(f, "\nRemocao de %s (S = maior componente / %d vertices; aleatoria = media de 50)\n",
            alvo == 0 ? "USUARIOS (vertices)" : "AMIZADES (arestas)", n0);
    fprintf(f, "  %-9s %-9s | %-10s %-10s %-10s | %-8s %-8s %-8s\n", "removidos", "fracao",
            "S aleat.", "S grau", "S interm.", "C aleat", "C grau", "C interm");
    /* marcos: 0, 1 e 2 itens e depois 5%, 10%, ..., 100% (sem repetições) */
    int pct[] = {5, 10, 15, 20, 30, 40, 50, 60, 80, 100};
    int marcos[16], nm = 0;
    marcos[nm++] = 0;
    if (total >= 1) marcos[nm++] = 1;
    if (total >= 2) marcos[nm++] = 2;
    for (int i = 0; i < 10; i++) {
        int k = (int)floor(pct[i] / 100.0 * total + 0.5);
        if (k > marcos[nm - 1] && k <= total) marcos[nm++] = k;
    }
    for (int i = 0; i < nm; i++) {
        int k = marcos[i];
        fprintf(f, "  %-9d %-9.3f | %-10.3f %-10.3f %-10.3f | %-8.1f %-8.0f %-8.0f\n", k,
                (double)k / total, S[0][k], S[1][k], S[2][k], C[0][k], C[1][k], C[2][k]);
    }
    for (int e = 0; e < 3; e++) {
        int fc = fracao_critica(S[e], pontos, total);
        if (fc >= 0)
            fprintf(f, "  %-13s: S < 0,5 apos %d remocoes (%.1f%%)\n",
                    estrategia_nome((Estrategia)e), fc, 100.0 * fc / total);
    }

    if (dir) {
        char caminho[1024];
        snprintf(caminho, sizeof caminho, "%s/remocao_%s.csv", dir,
                 alvo == 0 ? "vertices" : "arestas");
        FILE *o = fopen(caminho, "w");
        if (o) {
            fprintf(o, "removidos,fracao,S_aleatoria,S_grau,S_intermediacao,"
                       "comp_aleatoria,comp_grau,comp_intermediacao\n");
            for (int k = 0; k < pontos; k++)
                fprintf(o, "%d,%.6f,%.6f,%.6f,%.6f,%.4f,%.0f,%.0f\n", k, (double)k / total,
                        S[0][k], S[1][k], S[2][k], C[0][k], C[1][k], C[2][k]);
            fclose(o);
        }
    }
    for (int e = 0; e < 3; e++) { free(S[e]); free(C[e]); }
}

void secao_remocoes(Grafo *g, FILE *f, const char *dir, unsigned semente) {
    titulo(f, "ETAPA 4 - SIMULACAO DE REMOCOES (aleatoria x grau x intermediacao)");
    tabela_remocao(g, f, dir, 0, semente);
    tabela_remocao(g, f, dir, 1, semente);
}

/* ------------------------------------------------------------------ */
/* RF02 - visualização: SVG com layout de forças (Fruchterman-Reingold) */
/* ------------------------------------------------------------------ */
static const char *PALETA[] = {
    "#4E79A7", "#F28E2B", "#59A14F", "#B07AA1", "#76B7B2", "#EDC948",
    "#9C755F", "#FF9DA7", "#86BCB6", "#D37295", "#8CD17D", "#A0CBE8"};
#define NPALETA 12

static void layout_forcas(const Grafo *g, double *x, double *y, unsigned semente) {
    int n = g->n;
    unsigned est = semente ? semente : 7u;
    double W = 1000, H = 1000, k = sqrt(W * H / (grafo_n_ativos(g) + 1));
    double *dx = xmalloc(sizeof(double) * ((size_t)n + 1));
    double *dy = xmalloc(sizeof(double) * ((size_t)n + 1));
    for (int v = 0; v < n; v++) {
        x[v] = (aleatorio(&est) % 10000) / 10.0;
        y[v] = (aleatorio(&est) % 10000) / 10.0;
    }
    int iters = n > 1500 ? 60 : (n > 500 ? 150 : 400);
    double t = W / 8;
    for (int it = 0; it < iters; it++) {
        for (int v = 0; v < n; v++) dx[v] = dy[v] = 0;
        for (int u = 0; u < n; u++) {                    /* repulsão */
            if (!g->v_ativo[u]) continue;
            for (int v = u + 1; v < n; v++) {
                if (!g->v_ativo[v]) continue;
                double ddx = x[u] - x[v], ddy = y[u] - y[v];
                double d = sqrt(ddx * ddx + ddy * ddy) + 0.01;
                double fr = k * k / d;
                dx[u] += ddx / d * fr; dy[u] += ddy / d * fr;
                dx[v] -= ddx / d * fr; dy[v] -= ddy / d * fr;
            }
        }
        for (int e = 0; e < g->m; e++) {                 /* atração */
            if (!aresta_ok(g, e)) continue;
            int u = g->aresta[e].u, v = g->aresta[e].v;
            double ddx = x[u] - x[v], ddy = y[u] - y[v];
            double d = sqrt(ddx * ddx + ddy * ddy) + 0.01;
            double fa = d * d / k;
            dx[u] -= ddx / d * fa; dy[u] -= ddy / d * fa;
            dx[v] += ddx / d * fa; dy[v] += ddy / d * fa;
        }
        for (int v = 0; v < n; v++) {                    /* gravidade + passo */
            if (!g->v_ativo[v]) continue;
            dx[v] -= 0.08 * k * (x[v] - W / 2) / 50.0;
            dy[v] -= 0.08 * k * (y[v] - H / 2) / 50.0;
            double d = sqrt(dx[v] * dx[v] + dy[v] * dy[v]) + 1e-9;
            double passo = d < t ? d : t;
            x[v] += dx[v] / d * passo;
            y[v] += dy[v] / d * passo;
        }
        t = t * 0.97 + 0.5;
    }
    free(dx); free(dy);
}

int exportar_svg(const Grafo *g, const int *rotulo, const char *titulo_svg,
                 const char *caminho, unsigned semente) {
    FILE *f = fopen(caminho, "w");
    if (!f) return -1;
    int n = g->n;
    double *x = xmalloc(sizeof(double) * ((size_t)n + 1));
    double *y = xmalloc(sizeof(double) * ((size_t)n + 1));
    layout_forcas(g, x, y, semente);

    /* normaliza para a área de desenho */
    double minx = 1e18, maxx = -1e18, miny = 1e18, maxy = -1e18;
    for (int v = 0; v < n; v++) {
        if (!g->v_ativo[v]) continue;
        if (x[v] < minx) minx = x[v];
        if (x[v] > maxx) maxx = x[v];
        if (y[v] < miny) miny = y[v];
        if (y[v] > maxy) maxy = y[v];
    }
    double W = 900, H = 900, M = 50;
    double sx = (maxx - minx) > 1e-9 ? (W - 2 * M) / (maxx - minx) : 1;
    double sy = (maxy - miny) > 1e-9 ? (H - 2 * M) / (maxy - miny) : 1;
    for (int v = 0; v < n; v++) {
        x[v] = M + (x[v] - minx) * sx;
        y[v] = M + 30 + (y[v] - miny) * sy;
    }

    ResultadoTarjan *r = tarjan(g);
    int na = grafo_n_ativos(g);
    double raio = na <= 40 ? 14 : (na <= 150 ? 8 : 4);
    int rotular = na <= 80;

    fprintf(f, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"%.0f\" height=\"%.0f\" "
               "viewBox=\"0 0 %.0f %.0f\" font-family=\"Helvetica, Arial, sans-serif\">\n",
            W, H + 80, W, H + 80);
    fprintf(f, "<rect width=\"100%%\" height=\"100%%\" fill=\"white\"/>\n");
    fprintf(f, "<text x=\"%.0f\" y=\"30\" font-size=\"20\" text-anchor=\"middle\">%s</text>\n",
            W / 2, titulo_svg ? titulo_svg : "Rede social");

    for (int e = 0; e < g->m; e++) {
        if (!aresta_ok(g, e)) continue;
        int u = g->aresta[e].u, v = g->aresta[e].v;
        if (r->ponte[e])
            fprintf(f, "<line x1=\"%.1f\" y1=\"%.1f\" x2=\"%.1f\" y2=\"%.1f\" stroke=\"#C0392B\" "
                       "stroke-width=\"3\" stroke-dasharray=\"8,4\"/>\n", x[u], y[u], x[v], y[v]);
        else {
            int inter = rotulo && rotulo[u] != rotulo[v];
            fprintf(f, "<line x1=\"%.1f\" y1=\"%.1f\" x2=\"%.1f\" y2=\"%.1f\" stroke=\"%s\" "
                       "stroke-width=\"%s\" stroke-opacity=\"%s\"/>\n", x[u], y[u], x[v], y[v],
                    inter ? "#7F7F7F" : "#9AA0A6", na > 150 ? "0.6" : "1.5",
                    inter ? "0.9" : "0.7");
        }
    }
    for (int v = 0; v < n; v++) {
        if (!g->v_ativo[v]) continue;
        const char *cor = rotulo && rotulo[v] >= 0 ? PALETA[rotulo[v] % NPALETA] : "#4E79A7";
        fprintf(f, "<circle cx=\"%.1f\" cy=\"%.1f\" r=\"%.1f\" fill=\"%s\" stroke=\"%s\" "
                   "stroke-width=\"%s\"><title>%s (grau %d)</title></circle>\n",
                x[v], y[v], raio, cor, r->articulacao[v] ? "#000000" : "#FFFFFF",
                r->articulacao[v] ? "3.5" : "1.5", g->nome[v], grafo_grau(g, v));
        if (rotular)
            fprintf(f, "<text x=\"%.1f\" y=\"%.1f\" font-size=\"12\" text-anchor=\"middle\">%s</text>\n",
                    x[v], y[v] - raio - 4, g->nome[v]);
    }
    fprintf(f, "<text x=\"20\" y=\"%.0f\" font-size=\"13\" fill=\"#333\">Cores: comunidades | "
               "contorno preto: vertice de articulacao | vermelho tracejado: ponte</text>\n",
            H + 60);
    fprintf(f, "</svg>\n");
    fclose(f);
    tarjan_liberar(r);
    free(x); free(y);
    return 0;
}

int exportar_dot(const Grafo *g, const int *rotulo, const char *caminho) {
    FILE *f = fopen(caminho, "w");
    if (!f) return -1;
    ResultadoTarjan *r = tarjan(g);
    fprintf(f, "graph rede {\n  layout=neato; overlap=false; node [style=filled];\n");
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        fprintf(f, "  \"%s\" [fillcolor=\"%s\"%s];\n", g->nome[v],
                rotulo && rotulo[v] >= 0 ? PALETA[rotulo[v] % NPALETA] : "#4E79A7",
                r->articulacao[v] ? ", penwidth=3" : "");
    }
    for (int e = 0; e < g->m; e++) {
        if (!aresta_ok(g, e)) continue;
        fprintf(f, "  \"%s\" -- \"%s\"%s;\n", g->nome[g->aresta[e].u], g->nome[g->aresta[e].v],
                r->ponte[e] ? " [color=red, style=dashed, penwidth=2]" : "");
    }
    fprintf(f, "}\n");
    fclose(f);
    tarjan_liberar(r);
    return 0;
}

/* ------------------------------------------------------------------ */
/* RF10 - relatório completo                                           */
/* ------------------------------------------------------------------ */
int relatorio_completo(Grafo *g, const char *origem, const char *dir, unsigned semente) {
    criar_diretorio(dir);
    char caminho[1024];

    snprintf(caminho, sizeof caminho, "%s/relatorio.txt", dir);
    FILE *f = fopen(caminho, "w");
    if (!f) { fprintf(stderr, "Nao foi possivel criar %s\n", caminho); return -1; }

    fprintf(f, "RELATORIO DE METRICAS - DETECCAO DE COMUNIDADES EM REDES SOCIAIS\n");
    fprintf(f, "Arquivo de entrada: %s\n", origem);

    secao_rede(g, f);
    secao_componentes(g, f);
    secao_tarjan(g, f);
    secao_biconexas(g, f);
    secao_kappa_lambda(g, f);
    ResultadoGN *gn = secao_comunidades(g, f, 10);
    secao_remocoes(g, f, dir, semente);
    fclose(f);

    /* ---- CSVs ---- */
    ResultadoTarjan *r = tarjan(g);
    int *comp = xmalloc(sizeof(int) * ((size_t)g->n + 1));
    componentes_conexas(g, comp, NULL);
    double *cbv = xcalloc((size_t)g->n + 1, sizeof(double));
    double *cbe = xcalloc((size_t)g->m + 1, sizeof(double));
    brandes(g, NULL, cbv, cbe);
    const int *rot = gn ? gn->nivel[gn->melhor].rotulo : NULL;

    snprintf(caminho, sizeof caminho, "%s/vertices.csv", dir);
    FILE *o = fopen(caminho, "w");
    if (o) {
        fprintf(o, "vertice,grau,componente,comunidade,articulacao,intermediacao\n");
        for (int v = 0; v < g->n; v++)
            if (g->v_ativo[v])
                fprintf(o, "%s,%d,%d,%d,%d,%.6f\n", g->nome[v], grafo_grau(g, v), comp[v] + 1,
                        rot ? rot[v] + 1 : 0, r->articulacao[v], cbv[v]);
        fclose(o);
    }

    int *ordem_gn = xmalloc(sizeof(int) * ((size_t)g->m + 1));
    for (int e = 0; e < g->m; e++) ordem_gn[e] = 0;
    if (gn) for (int i = 0; i < gn->n_remocoes; i++) ordem_gn[gn->ordem_remocao[i]] = i + 1;

    snprintf(caminho, sizeof caminho, "%s/arestas.csv", dir);
    o = fopen(caminho, "w");
    if (o) {
        fprintf(o, "pessoa1,pessoa2,ponte,biconexa,intermediacao,ordem_girvan_newman\n");
        for (int e = 0; e < g->m; e++)
            if (aresta_ok(g, e))
                fprintf(o, "%s,%s,%d,%d,%.6f,%d\n", g->nome[g->aresta[e].u],
                        g->nome[g->aresta[e].v], r->ponte[e], r->bcc_aresta[e] + 1, cbe[e],
                        ordem_gn[e]);
        fclose(o);
    }

    if (gn) {
        snprintf(caminho, sizeof caminho, "%s/girvan_newman.csv", dir);
        o = fopen(caminho, "w");
        if (o) {
            fprintf(o, "arestas_removidas,comunidades,maior_grupo,modularidade\n");
            for (int i = 0; i < gn->n_niveis; i++)
                fprintf(o, "%d,%d,%d,%.6f\n", gn->nivel[i].arestas_removidas,
                        gn->nivel[i].n_comunidades, gn->nivel[i].maior, gn->nivel[i].q);
            fclose(o);
        }
    }

    /* ---- visualizações ---- */
    snprintf(caminho, sizeof caminho, "%s/grafo.svg", dir);
    exportar_svg(g, rot, "Rede social - comunidades (Girvan-Newman)", caminho, semente);
    snprintf(caminho, sizeof caminho, "%s/grafo.dot", dir);
    exportar_dot(g, rot, caminho);

    free(comp); free(cbv); free(cbe); free(ordem_gn);
    tarjan_liberar(r);
    girvan_newman_liberar(gn);
    return 0;
}
