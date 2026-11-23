/*
 * relatorio.h - Impressão de resultados, relatório de métricas e
 * exportação de visualizações (RF02, RF10).
 */
#ifndef RELATORIO_H
#define RELATORIO_H

#include "grafo.h"
#include "comunidades.h"
#include "conectividade.h"

/* Seções reutilizadas pelo menu interativo e pelo relatório */
void secao_rede(const Grafo *g, FILE *f);
void secao_componentes(const Grafo *g, FILE *f);
void secao_tarjan(const Grafo *g, FILE *f);
void secao_biconexas(const Grafo *g, FILE *f);
void secao_kappa_lambda(Grafo *g, FILE *f);
ResultadoGN *secao_comunidades(Grafo *g, FILE *f, int verbose);
void secao_remocoes(Grafo *g, FILE *f, const char *dir, unsigned semente);

/* Visualizações: SVG (layout de forças) e DOT (Graphviz).
 * 'rotulo' (pode ser NULL) colore os vértices por comunidade. */
int exportar_svg(const Grafo *g, const int *rotulo, const char *titulo,
                 const char *caminho, unsigned semente);
int exportar_dot(const Grafo *g, const int *rotulo, const char *caminho);

/* RF10 - gera relatorio.txt, CSVs e visualizações no diretório 'dir' */
int relatorio_completo(Grafo *g, const char *origem, const char *dir, unsigned semente);

int criar_diretorio(const char *dir);

#endif
