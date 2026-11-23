# Detecção de Comunidades em Redes Sociais - Teoria dos Grafos (UTFPR-MD)
CC      ?= gcc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra -pedantic
LDLIBS  = -lm
SRC     = src/main.c src/grafo.c src/conectividade.c src/comunidades.c \
          src/remocao.c src/relatorio.c
EXE     = redes

all: $(EXE)

$(EXE): $(SRC) src/*.h
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDLIBS)

# gera os relatórios de todos os conjuntos de dados
experimentos: $(EXE)
	./$(EXE) dados/amizades.csv        -r resultados/amizades
	./$(EXE) dados/rede_social.csv     -r resultados/rede_social
	./$(EXE) dados/karate.csv          -r resultados/karate
	./$(EXE) dados/facebook_ego0.csv   -r resultados/facebook_ego0

clean:
	rm -f $(EXE) $(EXE).exe

.PHONY: all experimentos clean
