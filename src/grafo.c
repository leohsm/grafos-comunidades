/*
 * grafo.c - Implementação da estrutura de grafo (RF01, RF02).
 */
#include "grafo.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* utilitários de memória                                              */
/* ------------------------------------------------------------------ */
void *xmalloc(size_t n) {
    void *p = malloc(n ? n : 1);
    if (!p) { fprintf(stderr, "Erro: memoria insuficiente\n"); exit(1); }
    return p;
}
void *xcalloc(size_t n, size_t s) {
    void *p = calloc(n ? n : 1, s ? s : 1);
    if (!p) { fprintf(stderr, "Erro: memoria insuficiente\n"); exit(1); }
    return p;
}
void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n ? n : 1);
    if (!q) { fprintf(stderr, "Erro: memoria insuficiente\n"); exit(1); }
    return q;
}

/* ------------------------------------------------------------------ */
/* tabela hash nome -> índice                                          */
/* ------------------------------------------------------------------ */
static unsigned long hash_str(const char *s) {
    unsigned long h = 5381;                 /* djb2 */
    while (*s) h = h * 33u + (unsigned char)*s++;
    return h;
}

static void hash_reconstruir(Grafo *g, int nova_cap) {
    free(g->hash);
    g->cap_hash = nova_cap;
    g->hash = xmalloc(sizeof(int) * (size_t)nova_cap);
    for (int i = 0; i < nova_cap; i++) g->hash[i] = -1;
    for (int v = 0; v < g->n; v++) {
        unsigned long h = hash_str(g->nome[v]) % (unsigned long)nova_cap;
        while (g->hash[h] != -1) h = (h + 1) % (unsigned long)nova_cap;
        g->hash[h] = v;
    }
}

int grafo_buscar_vertice(const Grafo *g, const char *nome) {
    unsigned long h = hash_str(nome) % (unsigned long)g->cap_hash;
    while (g->hash[h] != -1) {
        if (strcmp(g->nome[g->hash[h]], nome) == 0) return g->hash[h];
        h = (h + 1) % (unsigned long)g->cap_hash;
    }
    return -1;
}

/* ------------------------------------------------------------------ */
/* criação / destruição                                                */
/* ------------------------------------------------------------------ */
Grafo *grafo_criar(void) {
    Grafo *g = xcalloc(1, sizeof(Grafo));
    g->cap_v = 16;
    g->cap_e = 32;
    g->nome    = xmalloc(sizeof(*g->nome) * (size_t)g->cap_v);
    g->adj     = xcalloc((size_t)g->cap_v, sizeof(Adj *));
    g->v_ativo = xmalloc((size_t)g->cap_v);
    g->aresta  = xmalloc(sizeof(Aresta) * (size_t)g->cap_e);
    g->e_ativa = xmalloc((size_t)g->cap_e);
    g->hash = NULL;
    hash_reconstruir(g, 64);
    return g;
}

void grafo_destruir(Grafo *g) {
    if (!g) return;
    for (int v = 0; v < g->n; v++) {
        Adj *a = g->adj[v];
        while (a) { Adj *p = a->prox; free(a); a = p; }
    }
    free(g->nome); free(g->adj); free(g->v_ativo);
    free(g->aresta); free(g->e_ativa); free(g->hash);
    free(g);
}

int grafo_vertice(Grafo *g, const char *nome) {
    int v = grafo_buscar_vertice(g, nome);
    if (v >= 0) return v;

    if (g->n == g->cap_v) {
        g->cap_v *= 2;
        g->nome    = xrealloc(g->nome, sizeof(*g->nome) * (size_t)g->cap_v);
        g->adj     = xrealloc(g->adj, sizeof(Adj *) * (size_t)g->cap_v);
        g->v_ativo = xrealloc(g->v_ativo, (size_t)g->cap_v);
    }
    v = g->n++;
    strncpy(g->nome[v], nome, MAX_NOME - 1);
    g->nome[v][MAX_NOME - 1] = '\0';
    g->adj[v] = NULL;
    g->v_ativo[v] = 1;

    if (2 * g->n > g->cap_hash) hash_reconstruir(g, 4 * g->cap_hash);
    else {
        unsigned long h = hash_str(g->nome[v]) % (unsigned long)g->cap_hash;
        while (g->hash[h] != -1) h = (h + 1) % (unsigned long)g->cap_hash;
        g->hash[h] = v;
    }
    return v;
}

int grafo_buscar_aresta(const Grafo *g, int u, int v) {
    if (u < 0 || v < 0 || u >= g->n || v >= g->n) return -1;
    for (Adj *a = g->adj[u]; a; a = a->prox)
        if (a->destino == v) return a->id;
    return -1;
}

static void inserir_adj(Grafo *g, int u, int v, int id) {
    Adj *a = xmalloc(sizeof(Adj));
    a->destino = v;
    a->id = id;
    a->prox = g->adj[u];
    g->adj[u] = a;
}

/* Insere a aresta {u, v}. Laços e arestas repetidas são ignorados. */
int grafo_adicionar_aresta(Grafo *g, int u, int v) {
    if (u == v) return -1;
    if (grafo_buscar_aresta(g, u, v) >= 0) return -1;
    if (g->m == g->cap_e) {
        g->cap_e *= 2;
        g->aresta  = xrealloc(g->aresta, sizeof(Aresta) * (size_t)g->cap_e);
        g->e_ativa = xrealloc(g->e_ativa, (size_t)g->cap_e);
    }
    int id = g->m++;
    g->aresta[id].u = u;
    g->aresta[id].v = v;
    g->e_ativa[id] = 1;
    inserir_adj(g, u, v, id);
    inserir_adj(g, v, u, id);
    return id;
}

/* ------------------------------------------------------------------ */
/* RF01 - leitura do CSV                                               */
/* ------------------------------------------------------------------ */
static char *aparar(char *s) {
    while (*s && isspace((unsigned char)*s)) s++;
    char *f = s + strlen(s);
    while (f > s && isspace((unsigned char)f[-1])) *--f = '\0';
    /* remove aspas simples ou duplas em volta do campo */
    size_t L = strlen(s);
    if (L >= 2 && (s[0] == '"' || s[0] == '\'') && s[L - 1] == s[0]) {
        s[L - 1] = '\0';
        s++;
    }
    return s;
}

static int eq_ci(const char *a, const char *b) {
    while (*a && *b) {
        if (tolower((unsigned char)*a) != tolower((unsigned char)*b)) return 0;
        a++; b++;
    }
    return *a == *b;
}

/*
 * Formato aceito: uma amizade por linha, "pessoa1,pessoa2".
 * Também são aceitos ';', tabulação ou espaço como separador (o que
 * permite ler diretamente as listas de arestas do SNAP). Linhas vazias,
 * linhas iniciadas por '#' ou '%' e o cabeçalho "pessoa1,pessoa2" são
 * ignorados.
 */
Grafo *grafo_ler_csv(const char *caminho, int *linhas_ignoradas) {
    FILE *f = fopen(caminho, "r");
    if (!f) return NULL;

    Grafo *g = grafo_criar();
    char linha[1024];
    int ignoradas = 0, nlinha = 0;

    while (fgets(linha, sizeof linha, f)) {
        nlinha++;
        char *s = linha;
        if (nlinha == 1 && (unsigned char)s[0] == 0xEF &&
            (unsigned char)s[1] == 0xBB && (unsigned char)s[2] == 0xBF)
            s += 3;                                   /* BOM UTF-8 */
        s = aparar(s);
        if (*s == '\0' || *s == '#' || *s == '%') continue;

        char *sep = strpbrk(s, ",;\t ");
        if (!sep) { ignoradas++; continue; }
        *sep = '\0';
        char *p1 = aparar(s);
        char *p2 = aparar(sep + 1);
        /* se houver colunas extras (ex.: peso), descarta-as */
        char *extra = strpbrk(p2, ",;\t ");
        if (extra) { *extra = '\0'; p2 = aparar(p2); }

        if (*p1 == '\0' || *p2 == '\0') { ignoradas++; continue; }
        if (eq_ci(p1, "pessoa1") && eq_ci(p2, "pessoa2")) continue;

        int u = grafo_vertice(g, p1);
        int v = grafo_vertice(g, p2);
        if (grafo_adicionar_aresta(g, u, v) < 0) ignoradas++;
    }
    fclose(f);
    if (linhas_ignoradas) *linhas_ignoradas = ignoradas;
    return g;
}

/* ------------------------------------------------------------------ */
/* métricas básicas                                                    */
/* ------------------------------------------------------------------ */
int grafo_grau(const Grafo *g, int v) {
    if (!g->v_ativo[v]) return 0;
    int d = 0;
    for (Adj *a = g->adj[v]; a; a = a->prox)
        if (aresta_ok(g, a->id)) d++;
    return d;
}

int grafo_n_ativos(const Grafo *g) {
    int c = 0;
    for (int v = 0; v < g->n; v++) c += g->v_ativo[v];
    return c;
}

int grafo_m_ativas(const Grafo *g) {
    int c = 0;
    for (int e = 0; e < g->m; e++) c += aresta_ok(g, e);
    return c;
}

/* densidade de um grafo simples não dirigido: 2|E| / (|V| (|V| - 1)) */
double grafo_densidade(const Grafo *g) {
    double n = grafo_n_ativos(g);
    if (n < 2) return 0.0;
    return 2.0 * grafo_m_ativas(g) / (n * (n - 1.0));
}

/* ------------------------------------------------------------------ */
/* remoção temporária                                                  */
/* ------------------------------------------------------------------ */
void grafo_remover_vertice(Grafo *g, int v) { if (v >= 0 && v < g->n) g->v_ativo[v] = 0; }
void grafo_remover_aresta_id(Grafo *g, int id) { if (id >= 0 && id < g->m) g->e_ativa[id] = 0; }
void grafo_restaurar(Grafo *g) {
    memset(g->v_ativo, 1, (size_t)g->n);
    memset(g->e_ativa, 1, (size_t)g->m);
}

/* ------------------------------------------------------------------ */
/* RF02 - visualização textual                                         */
/* ------------------------------------------------------------------ */
void grafo_imprimir_resumo(const Grafo *g, FILE *f) {
    int n = grafo_n_ativos(g), m = grafo_m_ativas(g);
    int gmin = -1, gmax = 0;
    long soma = 0;
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        int d = grafo_grau(g, v);
        soma += d;
        if (gmin < 0 || d < gmin) gmin = d;
        if (d > gmax) gmax = d;
    }
    fprintf(f, "Vertices (usuarios) ......: %d\n", n);
    fprintf(f, "Arestas  (amizades) ......: %d\n", m);
    fprintf(f, "Densidade ................: %.4f\n", grafo_densidade(g));
    fprintf(f, "Grau minimo / maximo .....: %d / %d\n", gmin < 0 ? 0 : gmin, gmax);
    fprintf(f, "Grau medio ...............: %.2f\n", n ? (double)soma / n : 0.0);
}

void grafo_imprimir_adjacencia(const Grafo *g, FILE *f, int limite) {
    int impressos = 0;
    for (int v = 0; v < g->n; v++) {
        if (!g->v_ativo[v]) continue;
        if (limite > 0 && impressos == limite) {
            fprintf(f, "  ... (%d vertices omitidos)\n", grafo_n_ativos(g) - limite);
            break;
        }
        fprintf(f, "  %-12s (grau %2d): ", g->nome[v], grafo_grau(g, v));
        int primeiro = 1;
        /* imprime os vizinhos em ordem de índice para ficar legível */
        for (int w = 0; w < g->n; w++) {
            int id = grafo_buscar_aresta(g, v, w);
            if (id >= 0 && aresta_ok(g, id)) {
                fprintf(f, "%s%s", primeiro ? "" : ", ", g->nome[w]);
                primeiro = 0;
            }
        }
        fprintf(f, "\n");
        impressos++;
    }
}
