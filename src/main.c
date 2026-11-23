/*
 * main.c - Programa principal: menu interativo e modo relatório.
 *
 * Detecção de Comunidades em Redes Sociais Utilizando Conectividade de Grafos
 * Equipe: Erik Mazzuco, Letícia Moro, Leonardo Herrero
 * UTFPR - Câmpus Medianeira | Ciência da Computação | Árvores e Grafos
 *
 * Uso:
 *   redes <amizades.csv>                     menu interativo
 *   redes <amizades.csv> -r <diretorio>      gera o relatório completo (RF10)
 *   opções: -s <semente>  semente das simulações aleatórias (padrão 2026)
 */
#include "comunidades.h"
#include "conectividade.h"
#include "grafo.h"
#include "relatorio.h"
#include "remocao.h"

#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#endif

static char *ler_linha(const char *msg, char *buf, int tam) {
    printf("%s", msg);
    fflush(stdout);
    if (!fgets(buf, tam, stdin)) return NULL;
    buf[strcspn(buf, "\r\n")] = '\0';
    return buf;
}

static void estado_rede(const Grafo *g, const char *rotulo) {
    Instante it = instante_atual(g, 0);
    ResultadoTarjan *r = tarjan(g);
    printf("  [%s] vertices=%d arestas=%d componentes=%d maior=%d (%.1f%%) "
           "articulacoes=%d pontes=%d\n", rotulo, it.n_ativos, it.arestas_ativas,
           it.n_componentes, it.maior, it.n_ativos ? 100.0 * it.maior / it.n_ativos : 0.0,
           r->n_articulacoes, r->n_pontes);
    tarjan_liberar(r);
}

static void menu(Grafo *g, const char *arquivo, unsigned semente) {
    char buf[256];
    for (;;) {
        printf("\n================ REDE: %s ================\n", arquivo);
        printf(" 1  Resumo da rede (vertices, arestas, graus, densidade)\n");
        printf(" 2  Lista de adjacencia\n");
        printf(" 3  Conexo? / componentes conexas\n");
        printf(" 4  Vertices de articulacao e pontes\n");
        printf(" 5  Componentes biconexas\n");
        printf(" 6  Conectividade por vertices e por arestas (kappa, lambda)\n");
        printf(" 7  Comunidades (Girvan-Newman)\n");
        printf(" 8  Remover usuario\n");
        printf(" 9  Remover amizade\n");
        printf("10  Restaurar a rede original\n");
        printf("11  Simulacao: remocoes aleatorias x orientadas\n");
        printf("12  Exportar visualizacao (SVG e DOT)\n");
        printf("13  Gerar relatorio completo\n");
        printf(" 0  Sair\n");
        if (!ler_linha("Opcao: ", buf, sizeof buf)) return;
        int op = atoi(buf);

        switch (op) {
        case 0: return;
        case 1: secao_rede(g, stdout); break;
        case 2: grafo_imprimir_adjacencia(g, stdout, 100); break;
        case 3: secao_componentes(g, stdout); break;
        case 4: secao_tarjan(g, stdout); break;
        case 5: secao_biconexas(g, stdout); break;
        case 6: secao_kappa_lambda(g, stdout); break;
        case 7: girvan_newman_liberar(secao_comunidades(g, stdout, 10)); break;
        case 8: {
            if (!ler_linha("Nome do usuario: ", buf, sizeof buf)) return;
            int v = grafo_buscar_vertice(g, buf);
            if (v < 0 || !g->v_ativo[v]) { printf("Usuario nao encontrado.\n"); break; }
            estado_rede(g, "antes ");
            grafo_remover_vertice(g, v);
            estado_rede(g, "depois");
            break;
        }
        case 9: {
            if (!ler_linha("Amizade (pessoa1,pessoa2): ", buf, sizeof buf)) return;
            char *sep = strchr(buf, ',');
            if (!sep) { printf("Formato invalido.\n"); break; }
            *sep = '\0';
            int u = grafo_buscar_vertice(g, buf), v = grafo_buscar_vertice(g, sep + 1);
            int id = grafo_buscar_aresta(g, u, v);
            if (id < 0 || !aresta_ok(g, id)) { printf("Amizade nao encontrada.\n"); break; }
            estado_rede(g, "antes ");
            grafo_remover_aresta_id(g, id);
            estado_rede(g, "depois");
            break;
        }
        case 10: grafo_restaurar(g); estado_rede(g, "restaurada"); break;
        case 11: secao_remocoes(g, stdout, NULL, semente); break;
        case 12: {
            ResultadoGN *gn = girvan_newman(g, 0, 0, NULL);
            exportar_svg(g, gn->nivel[gn->melhor].rotulo, arquivo, "grafo.svg", semente);
            exportar_dot(g, gn->nivel[gn->melhor].rotulo, "grafo.dot");
            girvan_newman_liberar(gn);
            printf("Arquivos grafo.svg e grafo.dot gerados no diretorio atual.\n");
            break;
        }
        case 13: {
            if (!ler_linha("Diretorio de saida [resultados]: ", buf, sizeof buf)) return;
            const char *dir = buf[0] ? buf : "resultados";
            if (relatorio_completo(g, arquivo, dir, semente) == 0)
                printf("Relatorio gerado em %s/ (relatorio.txt, CSVs, grafo.svg, grafo.dot)\n", dir);
            break;
        }
        default: printf("Opcao invalida.\n");
        }
    }
}

int main(int argc, char **argv) {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
#endif
    const char *arquivo = NULL, *dir = NULL;
    unsigned semente = 2026;
    for (int i = 1; i < argc; i++) {
        if ((!strcmp(argv[i], "-r") || !strcmp(argv[i], "--relatorio")) && i + 1 < argc)
            dir = argv[++i];
        else if ((!strcmp(argv[i], "-s") || !strcmp(argv[i], "--semente")) && i + 1 < argc)
            semente = (unsigned)strtoul(argv[++i], NULL, 10);
        else arquivo = argv[i];
    }
    if (!arquivo) {
        fprintf(stderr, "Uso: %s <amizades.csv> [-r diretorio_relatorio] [-s semente]\n", argv[0]);
        return 1;
    }

    int ignoradas = 0;
    Grafo *g = grafo_ler_csv(arquivo, &ignoradas);
    if (!g) { fprintf(stderr, "Erro ao abrir '%s'\n", arquivo); return 1; }
    printf("Rede carregada de '%s': %d usuarios, %d amizades", arquivo, g->n, g->m);
    if (ignoradas) printf(" (%d linhas ignoradas: repetidas, lacos ou invalidas)", ignoradas);
    printf("\n");

    if (dir) {
        int r = relatorio_completo(g, arquivo, dir, semente);
        if (r == 0) printf("Relatorio gerado em %s/\n", dir);
        grafo_destruir(g);
        return r ? 1 : 0;
    }
    menu(g, arquivo, semente);
    grafo_destruir(g);
    return 0;
}
