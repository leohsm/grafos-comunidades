/*
 * remocao.h - Simulação de remoções de usuários e conexões (RF09).
 */
#ifndef REMOCAO_H
#define REMOCAO_H

#include "grafo.h"

typedef enum {
    ESTR_ALEATORIA = 0,     /* ordem aleatória                               */
    ESTR_GRAU,              /* maior grau atual primeiro (recalculado)       */
    ESTR_INTERMEDIACAO      /* maior intermediação atual primeiro (recalc.)  */
} Estrategia;

const char *estrategia_nome(Estrategia e);

/* Situação da rede em um instante da simulação */
typedef struct {
    int removidos;          /* itens removidos até aqui           */
    int n_componentes;
    int maior;              /* tamanho da maior componente        */
    int n_ativos;           /* vértices presentes                 */
    int arestas_ativas;
} Instante;

/* Remove vértices (alvo = 0) ou arestas (alvo = 1) um a um, seguindo a
 * estratégia, até 'max_passos' remoções (<= 0: todos). Para a estratégia
 * aleatória a curva é a média de 'repeticoes' execuções. A curva tem
 * max_passos + 1 posições (a posição 0 é a rede intacta). A rede é
 * restaurada ao final. Retorna o número de pontos da curva. */
int simular_remocoes(Grafo *g, int alvo, Estrategia e, int max_passos,
                     int repeticoes, unsigned semente, double *curva_maior,
                     double *curva_comp);

/* Situação atual da rede */
Instante instante_atual(const Grafo *g, int removidos);

/* gerador pseudoaleatório simples e portável (xorshift32) */
unsigned aleatorio(unsigned *estado);

#endif
