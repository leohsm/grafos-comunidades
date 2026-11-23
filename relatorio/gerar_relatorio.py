"""Gera o relatório técnico (relatorio/Relatorio_Grafos_Comunidades.docx).

Uso (na raiz do projeto, após `make experimentos` e `relatorio/figuras.py`):
    python relatorio/gerar_relatorio.py
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent
FIG = RAIZ / "figuras"
SAIDA = RAIZ / "Relatorio_Grafos_Comunidades.docx"

doc = Document()

# ---------------------------------------------------------------- estilos
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.top_margin, sec.left_margin = Cm(3), Cm(3)
sec.bottom_margin, sec.right_margin = Cm(2), Cm(2)
sec.different_first_page_header_footer = True

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

# número de página no canto superior direito (exceto na capa)
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = hp.add_run()
for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
    if tipo:
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), tipo)
    else:
        el = OxmlElement("w:instrText")
        el.set(qn("xml:space"), "preserve")
        el.text = texto
    r._r.append(el)
r.font.size = Pt(10)

contador_fig = [0]


def runs(par, texto, size=None, cor=None):
    """Adiciona texto com marcação simples: **negrito**, *itálico*, `código`."""
    for parte in re.split(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            run = par.add_run(parte[2:-2]); run.bold = True
        elif parte.startswith("`"):
            run = par.add_run(parte[1:-1]); run.font.name = "Consolas"; run.font.size = Pt(10)
        elif parte.startswith("*"):
            run = par.add_run(parte[1:-1]); run.italic = True
        else:
            run = par.add_run(parte)
        if size:
            run.font.size = Pt(size)
        if cor:
            run.font.color.rgb = cor
    return par


def P(texto, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, depois=None):
    par = doc.add_paragraph()
    par.alignment = alinhar
    if depois is not None:
        par.paragraph_format.space_after = Pt(depois)
    return runs(par, texto, size)


def H(texto):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(14)
    par.paragraph_format.space_after = Pt(8)
    par.paragraph_format.keep_with_next = True
    run = par.add_run(texto); run.bold = True; run.font.size = Pt(16)


def H2(texto):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(8)
    par.paragraph_format.keep_with_next = True
    run = par.add_run(texto); run.bold = True


def lista(itens, numerada=False):
    for i, t in enumerate(itens, 1):
        if numerada:   # numeração manual: cada lista recomeça em 1
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Cm(1.0)
            par.paragraph_format.first_line_indent = Cm(-0.6)
            par.add_run(f"{i}.	")
            par.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
        else:
            par = doc.add_paragraph(style="List Bullet")
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.space_after = Pt(3)
        runs(par, t)


def sombrear(celula_ou_par, cor="E7E7E7"):
    alvo = celula_ou_par._tc.get_or_add_tcPr() if hasattr(celula_ou_par, "_tc") \
        else celula_ou_par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), cor)
    alvo.append(shd)


def codigo(texto, titulo=None):
    if titulo:
        par = doc.add_paragraph()
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.space_before = Pt(6)
        run = par.add_run(titulo); run.bold = True
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    sombrear(c)
    c.paragraphs[0].text = ""
    linhas = texto.strip("\n").split("\n")
    for i, ln in enumerate(linhas):
        par = c.paragraphs[0] if i == 0 else c.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.line_spacing = 1.0
        run = par.add_run(ln if ln else " ")
        run.font.name = "Consolas"; run.font.size = Pt(9)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def figura(arquivo, legenda, largura=15.5):
    contador_fig[0] += 1
    n = contador_fig[0]
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(str(FIG / arquivo), width=Cm(largura))
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.keep_with_next = True
    run = par.add_run(f"Figura {n}"); run.font.size = Pt(10)
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = par.add_run(f"Figura {n}: "); run.bold = True; run.font.size = Pt(10)
    runs(par, legenda, size=10)
    return n


def tabela(cabecalho, linhas, larguras=None, fonte=10):
    t = doc.add_table(rows=1, cols=len(cabecalho))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(cabecalho):
        c = t.rows[0].cells[j]
        sombrear(c, "D9D9D9")
        c.paragraphs[0].text = ""
        run = c.paragraphs[0].add_run(h); run.bold = True; run.font.size = Pt(fonte)
    for ln in linhas:
        cells = t.add_row().cells
        for j, v in enumerate(ln):
            cells[j].paragraphs[0].text = ""
            runs(cells[j].paragraphs[0], str(v), size=fonte)
            cells[j].paragraphs[0].paragraph_format.space_after = Pt(0)
    if larguras:
        for row in t.rows:
            for j, w in enumerate(larguras):
                row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def quebra():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ===================================================================== CAPA
def capa(texto, tam=12, negrito=True, antes=0, depois=6, cor=None, sublinhado=False, destaque=False):
    par = doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(antes); par.paragraph_format.space_after = Pt(depois)
    run = par.add_run(texto); run.bold = negrito; run.font.size = Pt(tam)
    if cor: run.font.color.rgb = cor
    if sublinhado: run.underline = True
    if destaque: run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if texto.startswith("http"):   # transforma o texto em hiperlink clicável
        rid = par.part.relate_to(texto, "http://schemas.openxmlformats.org/officeDocument/2006/"
                                 "relationships/hyperlink", is_external=True)
        link = OxmlElement("w:hyperlink")
        link.set(qn("r:id"), rid)
        par._p.remove(run._r)
        link.append(run._r)
        par._p.append(link)


capa("UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ – UTFPR", antes=0, depois=12)
capa("Campus Medianeira", depois=0)
capa("Erik Mazzuco", antes=120, depois=0)
capa("Letícia Moro", depois=0)
capa("Leonardo Herrero", depois=0)
capa("CONECTIVIDADE E DETECÇÃO DE COMUNIDADES EM GRAFOS", antes=110, depois=12)
capa("https://github.com/leohsm/grafos-comunidades", cor=RGBColor(0x05, 0x63, 0xC1), sublinhado=True,
     depois=12)
capa("Detecção de Comunidades em Redes Sociais Utilizando Conectividade de Grafos", tam=11)
capa("Medianeira", negrito=False, antes=140, depois=6)
capa("2026", negrito=False)
quebra()

# ===================================================== CONTEXTUALIZAÇÃO
H("Contextualização Histórica e Motivação")
P("Redes sociais são, antes de tudo, **grafos**. Cada pessoa é um vértice e cada relação de amizade "
  "é uma aresta que liga dois vértices. Essa representação, aparentemente simples, permite responder "
  "com rigor matemático perguntas que, de outra forma, seriam apenas intuitivas: a rede está "
  "\"inteira\" ou dividida em grupos isolados? Quais pessoas mantêm a rede unida? Quais amizades, se "
  "desfeitas, separariam grupos inteiros? Existem grupos de pessoas mais próximas entre si do que do "
  "resto da rede? E o que acontece com a rede quando usuários deixam a plataforma ou conexões deixam "
  "de existir?")
P("A Teoria dos Grafos nasceu justamente de uma pergunta de conectividade. Em 1736, Leonhard Euler "
  "analisou o problema das **sete pontes de Königsberg**, mostrando que não era possível atravessar "
  "cada ponte da cidade exatamente uma vez (EULER, 1736). Quase dois séculos depois, Karl Menger "
  "estabeleceu um dos resultados centrais da área: o número mínimo de vértices que precisam ser "
  "removidos para separar dois vértices é igual ao número máximo de caminhos independentes entre "
  "eles (MENGER, 1927). Esse teorema conecta a **robustez** de uma rede à existência de **caminhos "
  "alternativos** e é a base do cálculo da conectividade por vértices e por arestas realizado neste "
  "projeto.")
P("Do ponto de vista algorítmico, o grande marco foi a **busca em profundidade** (DFS) aplicada à "
  "conectividade. Em 1972 e 1973, Robert Tarjan e John Hopcroft mostraram que, com uma única DFS e "
  "dois números por vértice (o instante de descoberta e o menor instante alcançável, *low*), é "
  "possível encontrar em tempo linear todos os **vértices de articulação**, todas as **pontes** e "
  "todas as **componentes biconexas** de um grafo (TARJAN, 1972; HOPCROFT; TARJAN, 1973). Esses "
  "elementos são exatamente os \"pontos frágeis\" de uma rede: um vértice de articulação é um "
  "usuário cuja saída desconecta a rede, e uma ponte é uma amizade cuja remoção separa grupos.")
P("Na sociologia, a importância dessas ligações já havia sido percebida. Granovetter (1973), no "
  "clássico *The Strength of Weak Ties*, argumentou que as ligações fracas, que funcionam como pontes "
  "entre grupos coesos, são as responsáveis por levar informação nova de um grupo a outro. Freeman "
  "(1977) formalizou a ideia de que alguns vértices são centrais por estarem **entre** os demais, "
  "definindo a **centralidade de intermediação** (*betweenness*): a fração dos caminhos mínimos da "
  "rede que passa por um vértice.")
P("Em 2002, Michelle Girvan e Mark Newman inverteram essa ideia para resolver um problema diferente: "
  "a **detecção de comunidades** (GIRVAN; NEWMAN, 2002). Se as arestas que ligam grupos distintos "
  "concentram os caminhos mínimos, então elas possuem alta intermediação. Removendo progressivamente "
  "as arestas de maior intermediação, a rede se desfaz justamente nas fronteiras entre os grupos, "
  "revelando suas comunidades. Para escolher a melhor divisão, Newman e Girvan (2004) propuseram a "
  "**modularidade** Q, que compara a quantidade de arestas internas de cada grupo com a esperada em "
  "uma rede aleatória com os mesmos graus. O cálculo eficiente da intermediação, em O(nm), deve-se a "
  "Brandes (2001).")
P("Este relatório descreve a implementação, em linguagem C, de um sistema de análise de redes sociais "
  "que integra esses resultados: leitura da rede a partir de um arquivo CSV, métricas básicas, "
  "componentes conexas, vértices de articulação, pontes, componentes biconexas, conectividade por "
  "vértices e por arestas, detecção de comunidades pelo algoritmo de Girvan–Newman e simulação de "
  "remoções de usuários e amizades. O projeto busca responder às cinco questões centrais propostas:")
lista(["Quantas **componentes conexas** existem?",
       "Quais usuários mantêm a rede conectada?",
       "Quais conexões são críticas?",
       "Quais **comunidades** podem ser identificadas?",
       "Como a rede se fragmenta após remoções?"], numerada=True)

H2("Componente conexa e comunidade")
P("Antes de prosseguir, é fundamental distinguir dois conceitos que, embora relacionados, são "
  "diferentes. A diferença reside no **critério utilizado para agrupar os vértices**:")
lista(["**Componente conexa:** agrupa vértices que possuem caminhos entre si, direta ou "
       "indiretamente. É um conceito **binário** e exato: dois vértices estão ou não estão na mesma "
       "componente.",
       "**Comunidade:** agrupa vértices que apresentam uma concentração relativamente alta de "
       "conexões entre si, em comparação com suas conexões com outros grupos. É um conceito de "
       "**densidade relativa**, avaliado por medidas como a modularidade."])
P("Uma comunidade não é necessariamente uma componente conexa, e um grafo inteiramente conexo pode "
  "conter várias comunidades. Como será mostrado nos experimentos, as comunidades encontradas pelo "
  "Girvan–Newman são sempre um **refinamento** das componentes conexas: cada comunidade está contida "
  "em uma única componente, mas uma componente pode conter muitas comunidades.")

# ===================================================== ESTRUTURA
H("Estruturação da Rede")
P("A rede social é modelada como um **grafo simples não dirigido** G = (V, E), em que V é o conjunto "
  "de usuários (|V| = n) e E é o conjunto de amizades (|E| = m). A amizade é uma relação simétrica "
  "(se A é amigo de B, B é amigo de A), por isso as arestas não possuem direção. Laços (uma pessoa "
  "amiga de si mesma) e arestas repetidas são descartados na leitura.")
P("A representação escolhida é a **lista de adjacência**: cada vértice guarda uma lista encadeada com "
  "os seus vizinhos. Em redes sociais, o número de amizades de cada pessoa é muito menor que o "
  "número total de pessoas (a rede é **esparsa**), e a lista de adjacência ocupa apenas O(n + m) de "
  "memória, contra O(n²) de uma matriz de adjacência. Todos os algoritmos do projeto (BFS, DFS, "
  "Brandes) percorrem os vizinhos de cada vértice, operação natural nessa estrutura.")
P("Duas decisões de projeto merecem destaque. Primeiro, cada aresta recebe um **identificador** (id) "
  "e aparece duas vezes nas listas (u→v e v→u) com o mesmo id; isso permite associar informações à "
  "aresta (se é ponte, sua intermediação, sua componente biconexa) e distinguir, na DFS, a aresta "
  "pela qual se chegou a um vértice. Segundo, vértices e arestas possuem uma **marca de ativo**: "
  "remover um usuário ou uma amizade consiste apenas em desligar essa marca, o que torna as "
  "remoções **temporárias** e reversíveis em O(1), exatamente como exigido pela etapa de simulação. "
  "Os nomes dos usuários são mapeados para índices por uma **tabela hash** com endereçamento aberto, "
  "o que torna a leitura de redes grandes eficiente.")
codigo("""typedef struct Adj {
    int destino;          // vértice vizinho
    int id;               // identificador da aresta {u, v}
    struct Adj *prox;     // próximo vizinho na lista
} Adj;

typedef struct {
    int n, m;                    // vértices e arestas (inclui inativos)
    char (*nome)[MAX_NOME];      // rótulo de cada vértice (usuário)
    Adj **adj;                   // listas de adjacência
    Aresta *aresta;              // aresta[id] = {u, v}
    unsigned char *v_ativo;      // 1 = usuário presente na rede
    unsigned char *e_ativa;      // 1 = amizade presente na rede
    int *hash; int cap_hash;     // tabela hash nome -> índice
} Grafo;""")

H2("Importação do CSV e métricas básicas (Etapa 1)")
P("O arquivo de entrada `amizades.csv` possui uma amizade por linha, no formato `pessoa1,pessoa2`. O "
  "leitor ignora o cabeçalho, linhas vazias e comentários (`#`), aceita também `;`, tabulação ou "
  "espaço como separador (o que permite ler diretamente as listas de arestas do SNAP) e trata a "
  "marca BOM do UTF-8. Cada nome novo cria um vértice; cada linha cria uma aresta, se ela ainda não "
  "existir. A partir do grafo construído são apresentados:")
lista(["**Número de vértices e de arestas**, n e m;",
       "**Grau** de cada vértice, d(v), isto é, o número de amigos de cada usuário, além da "
       "distribuição de graus e dos graus mínimo, máximo e médio (2m/n);",
       "**Densidade**, a fração das amizades possíveis que de fato existem: "
       "D = 2m / (n(n − 1)). Uma rede completa tem D = 1; redes sociais reais costumam ter D muito "
       "pequena.",
       "**Visualização**: lista de adjacência no terminal e exportação da rede para SVG (com layout "
       "de forças de Fruchterman–Reingold calculado pelo próprio programa) e para DOT (Graphviz), com "
       "comunidades coloridas, articulações destacadas e pontes tracejadas."])
P("**Exemplo.** Para a rede do enunciado (A,B; A,C; B,C; C,D; D,E; E,F; F,G; F,H; G,H; H,I), o "
  "programa obtém n = 9, m = 10, graus d(C) = d(F) = d(H) = 3, d(A) = d(B) = d(D) = d(E) = d(G) = 2 e "
  "d(I) = 1, grau médio 2,22 e densidade D = 2·10 / (9·8) = 0,2778. A Figura 1 mostra essa rede.")
figura("fig1_rede_exemplo.png",
       "Rede do enunciado. À esquerda, o grau de cada usuário; os vértices de articulação (C, D, E, F "
       "e H) aparecem em cinza escuro com contorno grosso e as pontes ({C,D}, {D,E}, {E,F} e {H,I}) "
       "em vermelho tracejado. À direita, as seis componentes biconexas: os triângulos {A,B,C} (B6) e "
       "{F,G,H} (B2) e quatro blocos formados por uma única ponte.")

# ===================================================== CONECTIVIDADE
H("Mecanismos de Operação: Conectividade (Etapa 2)")
H2("Componentes conexas por busca em largura")
P("Um grafo é **conexo** se existe um caminho entre qualquer par de vértices. Quando não é, ele se "
  "divide em **componentes conexas**: subconjuntos maximais de vértices mutuamente alcançáveis. Para "
  "encontrá-las, aplica-se uma **busca em largura** (BFS) a partir de cada vértice ainda não "
  "visitado: tudo o que a BFS alcança pertence à mesma componente. Cada vértice e cada aresta são "
  "examinados uma única vez, o que dá custo **O(n + m)**. O grafo é conexo se e somente se houver "
  "exatamente uma componente (RF03). A mesma função devolve o tamanho de cada componente, usado na "
  "simulação para medir a **maior componente**.")
codigo("""Função ComponentesConexas(Grafo G):
    k = 0
    Para cada vértice v: comp[v] = -1
    Para cada vértice s ativo com comp[s] == -1:     // nova componente
        Fila F = {s};  comp[s] = k;  tam[k] = 0
        Enquanto F não for vazia:
            u = Remover(F);  tam[k] = tam[k] + 1
            Para cada vizinho w de u (aresta ativa):
                Se comp[w] == -1:
                    comp[w] = k;  Inserir(F, w)
        k = k + 1
    Retorne k                                         // conexo se k == 1""",
       "PSEUDOCÓDIGO DAS COMPONENTES CONEXAS (BFS)")
P("**Exemplo.** Na rede fictícia `rede_social.csv` (37 usuários e 71 amizades, construída para os "
  "testes), a BFS encontra **3 componentes**: C1, com 30 usuários (81,1% da rede), que reúne colegas "
  "de faculdade, de trabalho e de futebol; C2, uma família de 5 pessoas (Helena, Igor, Julia, "
  "Leandro e Mirela); e C3, o par Nina–Otavio. A rede, portanto, não é conexa.")

H2("Vértices de articulação e pontes: o algoritmo de Tarjan")
P("Um **vértice de articulação** (ou vértice de corte) é um vértice cuja remoção aumenta o número de "
  "componentes conexas. Uma **ponte** é uma aresta com a mesma propriedade. Em uma rede social, são "
  "respectivamente os **usuários críticos** e as **conexões críticas**. A forma ingênua de "
  "encontrá-los, remover cada vértice (ou aresta) e recontar as componentes, custa O(n(n + m)). O "
  "algoritmo de Tarjan resolve o problema com uma única DFS, em **O(n + m)**.")
P("Durante a DFS, cada vértice u recebe dois números:")
lista(["**disc[u]**: o instante em que u foi descoberto (ordem de visita);",
       "**low[u]**: o menor instante de descoberta alcançável a partir da subárvore de u usando "
       "arestas da árvore e, no máximo, **uma aresta de retorno** (uma aresta que liga um vértice a um "
       "ancestral seu na árvore da DFS)."])
P("Intuitivamente, low[u] mede \"até onde a subárvore de u consegue voltar\" sem passar pela aresta "
  "que liga u ao seu pai. Com isso, para uma aresta de árvore p → u (p é o pai de u):")
lista(["Se **low[u] > disc[p]**, nenhum vértice da subárvore de u alcança p ou um ancestral de p por "
       "outro caminho; logo, a aresta {p, u} é uma **ponte**.",
       "Se **low[u] ≥ disc[p]** e p **não é a raiz**, a subárvore de u só se liga ao restante do "
       "grafo através de p; logo, p é um **vértice de articulação**.",
       "A **raiz** da DFS é articulação se e somente se possuir **dois ou mais filhos** na árvore, "
       "pois não há arestas entre subárvores distintas de uma DFS."])
P("A implementação em C é **iterativa**, com uma pilha explícita de quadros (vértice, aresta pela "
  "qual foi alcançado e próximo vizinho a examinar). Isso evita o estouro da pilha de chamadas em "
  "redes grandes, nas quais a DFS pode atingir milhares de níveis de profundidade. A aresta de volta "
  "ao pai é identificada pelo **id** da aresta, e não pelo vértice pai, o que torna o algoritmo "
  "correto mesmo na presença de arestas paralelas.")
codigo("""Função Tarjan(Grafo G):
    tempo = 1
    Para cada vértice r ativo ainda não visitado:     // r é raiz de uma DFS
        filhos_raiz = 0
        DFS(r, pai = NULO)
        Se filhos_raiz >= 2: articulacao[r] = VERDADEIRO

Função DFS(u, aresta_pai):
    disc[u] = low[u] = tempo;  tempo = tempo + 1
    Para cada aresta e = {u, w} ativa, e != aresta_pai:
        Se w não foi visitado:                        // aresta de árvore
            Empilhar e em PilhaArestas
            DFS(w, e)
            low[u] = min(low[u], low[w])
            Se low[w] > disc[u]:  ponte[e] = VERDADEIRO
            Se low[w] >= disc[u]:
                Se u é raiz: filhos_raiz = filhos_raiz + 1
                Senão:       articulacao[u] = VERDADEIRO
                Desempilhar arestas até e  -> nova componente biconexa
        Senão se disc[w] < disc[u]:                   // aresta de retorno
            Empilhar e em PilhaArestas
            low[u] = min(low[u], disc[w])""",
       "PSEUDOCÓDIGO DO ALGORITMO DE TARJAN")
P("**Exemplo.** Considere novamente a rede do enunciado, com a DFS iniciada em A e os vizinhos "
  "visitados em ordem alfabética. O processo decorre da seguinte forma:")
lista(["**Descida:** a DFS visita A, B, C, D, E, F, G, H e I, nessa ordem, formando um único caminho "
       "na árvore; logo disc = 1, 2, …, 9.",
       "**Arestas de retorno:** ao examinar C, encontra-se a aresta {C, A}, que volta a um ancestral: "
       "low[C] = disc[A] = 1. Da mesma forma, em H encontra-se {H, F}: low[H] = disc[F] = 6.",
       "**Retorno de I para H:** low[I] = 9 > disc[H] = 8, portanto {H, I} é ponte e H é articulação.",
       "**Retorno de H para G e de G para F:** low[G] = min(7, low[H]) = 6. Como low[G] = 6 ≥ "
       "disc[F] = 6, F é articulação; mas, como 6 não é maior que 6, {F, G} **não** é ponte: o ciclo "
       "F–G–H oferece um caminho alternativo.",
       "**Retorno até C:** low[F] = 6 > disc[E] = 5, low[E] = 5 > disc[D] = 4 e low[D] = 4 > "
       "disc[C] = 3; assim, {E, F}, {D, E} e {C, D} são pontes e E, D e C são articulações.",
       "**Raiz:** low[C] = 1 propaga-se para B e A. A raiz A tem um único filho na árvore (B), "
       "portanto **não** é articulação."])
P("O resultado, mostrado na Figura 2, são os vértices de articulação **C, D, E, F e H** e as pontes "
  "**{C,D}, {D,E}, {E,F} e {H,I}**, idênticos aos obtidos pelo programa.")
figura("fig2_tarjan.png",
       "Árvore da DFS do algoritmo de Tarjan para a rede do enunciado. Abaixo de cada vértice estão "
       "os valores disc e low. As arestas de retorno (pontilhadas, em azul) C→A e H→F reduzem os "
       "valores low e \"protegem\" as arestas dos ciclos A–B–C e F–G–H. As arestas em vermelho "
       "satisfazem low[filho] > disc[pai] e são pontes; os vértices com contorno grosso são "
       "articulações.")

H2("Componentes biconexas")
P("Uma **componente biconexa** (ou bloco) é um subgrafo maximal sem vértices de articulação "
  "próprios: dentro dele, a remoção de qualquer vértice isolado não desconecta os demais. Pelo "
  "teorema de Whitney, todo bloco com três ou mais vértices possui, entre qualquer par de vértices, "
  "dois caminhos internamente disjuntos. As componentes biconexas particionam as **arestas** do "
  "grafo (um vértice de articulação pertence a vários blocos), e cada ponte forma sozinha um bloco "
  "de dois vértices.")
P("Elas são obtidas na mesma DFS de Tarjan, com uma **pilha de arestas**: toda aresta de árvore ou de "
  "retorno é empilhada e, sempre que low[w] ≥ disc[u], as arestas são desempilhadas até a aresta "
  "{u, w}, formando um bloco (RF07). Na rede do enunciado, obtêm-se 6 blocos (Figura 1, à direita): "
  "{A,B,C}, {F,G,H} e quatro pontes isoladas. Em uma rede social, os blocos representam núcleos "
  "**robustos**: grupos em que ninguém, individualmente, consegue isolar os demais.")

H2("Conectividade por vértices e por arestas")
P("Articulações e pontes respondem se a rede pode ser desconectada pela remoção de **um** elemento. "
  "As medidas de conectividade generalizam essa pergunta:")
lista(["**Conectividade por vértices** κ(G): o menor número de vértices cuja remoção desconecta G "
       "(ou o reduz a um único vértice). κ(G) = 1 indica que existe um vértice de articulação.",
       "**Conectividade por arestas** λ(G): o menor número de arestas cuja remoção desconecta G. "
       "λ(G) = 1 indica que existe uma ponte."])
P("Vale a **desigualdade de Whitney**: κ(G) ≤ λ(G) ≤ δ(G), em que δ(G) é o grau mínimo. Para "
  "calculá-las, usa-se o **teorema de Menger**: o número mínimo de arestas (vértices) que separam s "
  "de t é igual ao número máximo de caminhos aresta-disjuntos (internamente vértice-disjuntos) entre "
  "s e t. Esse número é um **fluxo máximo** em uma rede com capacidades unitárias, calculado pelo "
  "algoritmo de Edmonds–Karp (caminhos aumentantes encontrados por BFS).")
lista(["Para λ(G), cada aresta {u, v} vira dois arcos de capacidade 1. Fixando um vértice s qualquer, "
       "λ(G) = min_t fluxo(s, t), pois todo corte mínimo separa s de algum t.",
       "Para κ(G), cada vértice v é **dividido** em v_in e v_out, ligados por um arco de capacidade 1 "
       "(é ele que \"conta\" a remoção do vértice); as arestas viram arcos de capacidade infinita. "
       "Pelo algoritmo de Even (EVEN; TARJAN, 1975), basta testar pares (v_i, v_j) não adjacentes com i ≤ κ atual, "
       "o que reduz muito o número de fluxos calculados.",
       "Os fluxos são interrompidos assim que atingem o melhor valor já conhecido (inicialmente, o "
       "grau mínimo), pois não podem mais melhorar a resposta."])
codigo("""Função ConectividadeArestas(Grafo G):
    Se G não for conexo: Retorne 0
    melhor = grau mínimo de G                 // lambda <= delta
    s = um vértice qualquer
    Para cada vértice t != s:
        melhor = min(melhor, FluxoMaximo(s, t, limite = melhor))
    Retorne melhor

Função ConectividadeVertices(Grafo G):         // algoritmo de Even
    Se G não for conexo: Retorne 0
    melhor = min(n - 1, grau mínimo de G)
    Para i = 1, 2, ... enquanto i <= melhor:
        Para j = i + 1 até n:
            Se v_i e v_j não forem adjacentes:
                // rede com vértices divididos: v_in -> v_out (cap. 1)
                melhor = min(melhor, FluxoMaximo(v_i_out, v_j_in, limite = melhor))
    Retorne melhor""", "PSEUDOCÓDIGO DA CONECTIVIDADE (TEOREMA DE MENGER)")
P("Como o custo cresce com o tamanho da rede, essas medidas são indicadas para **grafos moderados**, "
  "conforme o enunciado; o programa as calcula para redes de até 3.000 vértices. Quando a rede é "
  "desconexa, κ = λ = 0 por definição, e o programa informa também os valores da **maior "
  "componente**, que são mais informativos.")

# ===================================================== COMUNIDADES
H("Mecanismos de Operação: Comunidades (Etapa 3)")
H2("Centralidade de intermediação das arestas")
P("A **intermediação** de uma aresta e é a soma, sobre todos os pares de vértices {s, t}, da fração "
  "dos caminhos mínimos entre s e t que passam por e:")
P("C_B(e) = Σ_{s<t} σ_st(e) / σ_st,", alinhar=WD_ALIGN_PARAGRAPH.CENTER)
P("em que σ_st é o número de caminhos mínimos entre s e t e σ_st(e) é quantos deles usam a aresta e. "
  "Arestas que ligam grupos diferentes concentram esses caminhos, pois quase toda comunicação entre "
  "os grupos precisa atravessá-las. O cálculo direto exigiria enumerar caminhos; o **algoritmo de "
  "Brandes** (2001) obtém todos os valores em O(nm) com duas fases para cada origem s:")
lista(["**BFS a partir de s**, calculando a distância d(v) e o número de caminhos mínimos σ(v): "
       "σ(s) = 1 e σ(w) = Σ σ(v) sobre os predecessores v de w (vizinhos com d(v) = d(w) − 1).",
       "**Acumulação reversa**, percorrendo os vértices em ordem decrescente de distância: cada "
       "predecessor v de w recebe a dependência c = σ(v)/σ(w)·(1 + δ(w)), que é somada à aresta {v, w} "
       "e a δ(v)."], numerada=True)
P("Como o grafo é não dirigido, cada par é contado duas vezes (a partir de s e a partir de t), e os "
  "valores são divididos por 2. A mesma passagem produz a intermediação dos **vértices**, usada na "
  "simulação de ataques orientados.")
codigo("""Função Brandes(Grafo G):
    Para cada aresta e: CB[e] = 0
    Para cada vértice s:
        // fase 1: BFS
        Para cada v: d[v] = -1; sigma[v] = 0; delta[v] = 0
        d[s] = 0; sigma[s] = 1; Ordem = []
        Fila F = {s}
        Enquanto F não vazia:
            v = Remover(F); Ordem.adicionar(v)
            Para cada vizinho w de v:
                Se d[w] < 0: d[w] = d[v] + 1; Inserir(F, w)
                Se d[w] == d[v] + 1: sigma[w] = sigma[w] + sigma[v]
        // fase 2: acumulação em ordem decrescente de distância
        Para cada w em Ordem, do último ao primeiro:
            Para cada vizinho v de w com d[v] == d[w] - 1:
                c = sigma[v] / sigma[w] * (1 + delta[w])
                CB[{v, w}] = CB[{v, w}] + c / 2
                delta[v] = delta[v] + c
    Retorne CB""", "PSEUDOCÓDIGO DO ALGORITMO DE BRANDES")

H2("O algoritmo de Girvan–Newman")
P("O algoritmo de Girvan–Newman é **divisivo**: começa com a rede inteira e a divide removendo, uma "
  "a uma, as arestas que mais provavelmente ligam comunidades diferentes:")
lista(["Calcular a intermediação de todas as arestas.",
       "Remover a aresta de **maior** intermediação (em caso de empate, a de menor id, para que o "
       "resultado seja determinístico).",
       "**Recalcular** a intermediação das arestas restantes. O recálculo é essencial: depois que "
       "uma ponte entre grupos é removida, os caminhos mínimos se redistribuem e outra aresta passa a "
       "concentrá-los.",
       "Sempre que a remoção divide uma componente em duas, registrar a nova partição (um nível do "
       "**dendrograma**) e a sua modularidade.",
       "Repetir até que não restem arestas e escolher o nível de **maior modularidade**."],
      numerada=True)
P("Uma otimização importante foi implementada no passo 3. A intermediação de uma aresta depende "
  "apenas dos caminhos dentro da sua componente; portanto, após remover {u, v}, só é preciso "
  "recalcular as componentes que contêm u e v, executando o Brandes apenas a partir dos vértices "
  "dessas componentes. Quando a rede já está fragmentada, isso reduz drasticamente o custo de cada "
  "iteração.")
P("A **modularidade** de uma partição em grupos c é dada por")
P("Q = Σ_c [ L_c / m − ( D_c / 2m )² ],", alinhar=WD_ALIGN_PARAGRAPH.CENTER)
P("em que L_c é o número de arestas internas ao grupo c e D_c é a soma dos graus dos seus vértices, "
  "ambos medidos no grafo **original**. O primeiro termo é a fração de arestas que ficam dentro dos "
  "grupos; o segundo é essa mesma fração esperada se as arestas fossem distribuídas ao acaso "
  "preservando os graus. Q próximo de 0 indica que a divisão não é melhor que o acaso; em redes reais, "
  "valores entre 0,3 e 0,7 indicam estrutura de comunidades significativa (NEWMAN; GIRVAN, 2004).")
codigo("""Função GirvanNewman(Grafo G):
    base = arestas de G                       // Q é sempre medido no grafo original
    k = ComponentesConexas(G);  Registrar(nível 0, Q)
    CB = Brandes(G)
    Enquanto houver arestas ativas:
        e = aresta ativa de maior CB          // empate: menor id
        Remover e de G
        novo_k = ComponentesConexas(G)
        Se novo_k > k: Registrar(partição atual, Q(partição, base))
        k = novo_k
        // recálculo apenas nas componentes que continham e
        Zerar CB das arestas das componentes de u e v
        CB = CB + Brandes(G, origens = vértices dessas componentes)
    Restaurar as arestas removidas
    Retorne o nível de maior Q""", "PSEUDOCÓDIGO DO GIRVAN–NEWMAN")
P("**Exemplo.** Na rede do enunciado, a intermediação inicial das arestas é mostrada na Figura 3. As "
  "arestas {D,E} e {E,F} empatam com o maior valor, 20: cada uma é usada por todos os 4 × 5 = 20 "
  "pares que separam {A,B,C,D} de {E,F,G,H,I} (ou {A,…,E} de {F,…,I}). Pelo critério de desempate, "
  "{D,E} é removida, a rede se divide em {A,B,C,D} e {E,F,G,H,I} e a modularidade passa de 0 para")
P("Q = (4/10 − (9/20)²) + (5/10 − (11/20)²) = 0,1975 + 0,1975 = 0,395.",
  alinhar=WD_ALIGN_PARAGRAPH.CENTER)
P("Esse é o máximo do dendrograma. As remoções seguintes ({E,F}, {C,D}, {H,I}, …) apenas isolam "
  "vértices e reduzem Q até −0,12, quando todas as arestas foram removidas. Observe que a escolha "
  "da outra aresta empatada produziria a partição {A,…,E} e {F,…,I}, também com Q = 0,395: o "
  "vértice E está igualmente ligado aos dois grupos.")
figura("fig3_gn_exemplo.png",
       "Girvan–Newman na rede do enunciado. À esquerda, a intermediação de cada aresta (a espessura "
       "é proporcional ao valor); as pontes do \"corredor\" C–D–E–F concentram os caminhos mínimos. À "
       "direita, a partição obtida após a primeira remoção, que é também a de maior modularidade "
       "(Q = 0,395).")
P("**Exemplo clássico: o clube de caratê de Zachary.** Zachary (1977) observou durante dois anos as "
  "amizades entre os 34 membros de um clube universitário de caratê, que acabou se dividindo em dois "
  "após um conflito entre o instrutor (vértice 1) e o presidente (vértice 34). Essa rede (78 "
  "arestas) é o teste padrão de algoritmos de comunidades e foi usada no artigo original do "
  "Girvan–Newman. O programa remove primeiro as arestas {1,32}, {1,3} e {1,9}, que ligam o "
  "instrutor ao grupo do presidente. Após 11 remoções, a rede se divide em dois grupos (Q = 0,360), "
  "e a maior modularidade, **Q = 0,4013**, é obtida com **5 comunidades** após 24 remoções, "
  "exatamente o valor relatado na literatura para o Girvan–Newman nessa rede (Figura 4).")
figura("fig4_karate.png",
       "Clube de caratê de Zachary. À esquerda, as 5 comunidades da partição de maior modularidade "
       "(o vértice 1, instrutor, é o único vértice de articulação, e {1,12} é a única ponte). À "
       "direita, a modularidade Q ao longo das 78 remoções do Girvan–Newman: o máximo (0,4013) é "
       "atingido com 5 comunidades.")

# ===================================================== REMOÇÕES
H("Mecanismos de Operação: Simulação de Remoções (Etapa 4)")
P("A última etapa estuda a **robustez** da rede: como ela se fragmenta quando usuários deixam a "
  "plataforma ou amizades deixam de existir. Graças às marcas de ativo, o programa permite, no menu "
  "interativo, **remover temporariamente** um usuário ou uma amizade escolhidos pelo usuário e "
  "mostra a situação antes e depois (componentes, tamanho da maior componente, número de "
  "articulações e de pontes); a opção \"restaurar\" devolve a rede original. Por exemplo, na "
  "`rede_social.csv`, remover o usuário Tiago, articulação entre o grupo do trabalho e o grupo do "
  "futebol, faz a rede passar de 3 para 4 componentes e a maior componente cair de 30 para 19 "
  "usuários; remover em seguida a amizade {Caio, Davi} isola Davi e Eduardo (5 componentes).")
P("Além das remoções manuais, o programa executa uma **simulação sistemática**, removendo vértices ou "
  "arestas um a um até esvaziar a rede e medindo, a cada passo, o número de componentes e a métrica "
  "S = (tamanho da maior componente) / n₀, em que n₀ é o número inicial de vértices. São comparadas "
  "três estratégias:")
lista(["**Aleatória:** a ordem de remoção é sorteada (embaralhamento de Fisher–Yates com gerador "
       "xorshift e semente fixa). Representa falhas ao acaso; a curva é a média de 50 repetições.",
       "**Orientada por grau:** remove-se, a cada passo, o vértice de maior grau **atual** (para "
       "arestas, a de maior produto de graus d(u)·d(v)). Representa um ataque aos usuários mais "
       "populares.",
       "**Orientada por intermediação:** remove-se, a cada passo, o vértice (ou aresta) de maior "
       "intermediação, **recalculada** após cada remoção. Para arestas, é exatamente a sequência do "
       "Girvan–Newman."])
codigo("""Função SimularRemocoes(Grafo G, alvo, estratégia):
    Salvar o estado de G;  n0 = vértices ativos
    Se estratégia == ALEATÓRIA: L = itens ativos embaralhados
    Para k = 1 até o número de itens:
        Se estratégia == ALEATÓRIA:  x = L[k]
        Senão se estratégia == GRAU: x = item de maior grau atual
        Senão:                       x = item de maior intermediação atual
        Remover x (desligar a marca de ativo)
        comp, tam = ComponentesConexas(G)
        S[k] = max(tam) / n0;  C[k] = comp
    Restaurar o estado de G
    Retorne as curvas S e C""", "PSEUDOCÓDIGO DA SIMULAÇÃO DE REMOÇÕES")
P("Para resumir cada curva, o relatório informa a **fração crítica**: a menor fração de itens "
  "removidos para que a maior componente fique com menos da metade dos vértices (S < 0,5).")

# ===================================================== EXPERIMENTOS
H("Experimentos e Resultados")
P("Foram utilizados quatro conjuntos de dados, todos incluídos no diretório `dados/` do projeto:")
lista(["`amizades.csv`: a rede de exemplo do enunciado (9 vértices, 10 arestas);",
       "`rede_social.csv`: rede fictícia, construída para os testes, com três grupos de amigos "
       "(faculdade, trabalho e futebol) ligados por poucas amizades, uma família isolada e um casal "
       "isolado (37 vértices, 71 arestas);",
       "`karate.csv`: o clube de caratê de Zachary (34 vértices, 78 arestas);",
       "`facebook_ego0.csv`: a ego-rede do usuário 0 do conjunto *ego-Facebook* do SNAP (LESKOVEC; "
       "MCAULEY, 2012), ou seja, as amizades entre os amigos do usuário 0, sem o próprio usuário (333 "
       "vértices com ao menos uma amizade e 2.519 arestas), sugerida como extensão no enunciado."])
P("Todos os experimentos são reproduzidos pelo comando `make experimentos`, que executa o programa "
  "em modo relatório para cada rede. A Tabela 1 resume as métricas obtidas.")
P("**Tabela 1:** Resumo das métricas de cada rede.", size=10, depois=2)
tabela(["Métrica", "Enunciado", "Rede social", "Karate", "Facebook ego-0"], [
    ["Vértices / arestas", "9 / 10", "37 / 71", "34 / 78", "333 / 2.519"],
    ["Densidade", "0,2778", "0,1066", "0,1390", "0,0456"],
    ["Grau mín. / médio / máx.", "1 / 2,22 / 3", "1 / 3,84 / 6", "1 / 4,59 / 17", "1 / 15,13 / 77"],
    ["Componentes conexas", "1", "3", "1", "5"],
    ["Maior componente", "9 (100%)", "30 (81,1%)", "34 (100%)", "324 (97,3%)"],
    ["Vértices de articulação", "5", "4", "1", "25"],
    ["Pontes", "4", "4", "1", "31"],
    ["Componentes biconexas", "6", "7", "3", "37"],
    ["κ(G) / λ(G)", "1 / 1", "0 / 0 (maior: 1 / 1)", "1 / 1", "0 / 0 (maior: 1 / 1)"],
    ["Comunidades (Girvan–Newman)", "2", "5", "5", "36"],
    ["Modularidade máxima Q", "0,395", "0,6877", "0,4013", "0,4161"],
], larguras=[4.6, 2.4, 3.2, 2.4, 3.4], fonte=9)

H2("Experimento 1: componentes conexas")
P("A rede do enunciado e o clube de caratê são conexos. A rede social fictícia possui 3 "
  "componentes, como esperado pela sua construção, e a ego-rede do Facebook possui 5: uma "
  "**componente gigante** com 324 usuários (97,3%) e quatro grupos minúsculos (três pares e um "
  "trio) sem amigos em comum com o restante. Esse padrão, uma componente gigante e poucas "
  "componentes pequenas, é típico de redes sociais reais. Em todas as redes, os valores de κ e λ "
  "da maior componente são iguais a 1, o que confirma a existência de articulações e pontes.")

H2("Experimento 2: vértices de articulação (usuários críticos)")
P("Na rede social fictícia, os 4 usuários críticos são **Tiago** e **Vitor**, que ligam o grupo do "
  "trabalho ao grupo do futebol, e **Caio** e **Davi**, que ligam Eduardo ao restante da rede. A "
  "remoção de qualquer um deles aumenta o número de componentes de 3 para 4. No clube de caratê, o "
  "único vértice de articulação é o **instrutor (1)**: sua saída gera 3 componentes, isolando o "
  "membro 12, que só tinha amizade com ele. Na ego-rede do Facebook, há 25 articulações; a maioria "
  "liga pequenos grupos periféricos à componente gigante, e o vértice 239, com grau 58, é o de maior "
  "grau entre elas. Isso mostra que ser crítico não depende de ser popular: um usuário de grau 2, "
  "como Davi, pode ser tão crítico quanto um de grau 58.")

H2("Experimento 3: pontes (conexões críticas)")
P("Na rede social fictícia, as 4 pontes são {Tiago, Vitor}, {Caio, Davi}, {Davi, Eduardo} e "
  "{Nina, Otavio}. A primeira é a mais importante: é a única ligação entre os grupos do trabalho e do "
  "futebol e, por isso, tem a maior intermediação da rede (200, pois liga 20 × 10 pares). Já as "
  "duas amizades entre os grupos da faculdade e do trabalho ({Joao, Karina} e {Isabela, Lucas}) "
  "**não** são pontes, pois uma pode substituir a outra: a ligação entre esses grupos é frágil, mas "
  "não crítica. No caratê, a única ponte é {1, 12}, e no Facebook há 31 pontes, quase todas ligando "
  "usuários de grau 1 ou pequenos grupos ao restante da rede.")

H2("Experimento 4: comunidades (Girvan–Newman × componentes conexas)")
P("Este é o experimento que melhor evidencia a diferença entre os dois conceitos. Na rede social "
  "fictícia (Figura 5), as 3 componentes conexas dão modularidade de apenas Q = 0,2246, porque a "
  "componente C1 mistura três grupos diferentes. O Girvan–Newman remove primeiro a ponte {Tiago, "
  "Vitor} (intermediação 200) e depois as amizades {Joao, Karina} e {Isabela, Lucas}; com apenas 3 "
  "remoções, encontra **5 comunidades** com **Q = 0,6877**: os grupos da faculdade (K1), do trabalho "
  "(K2) e do futebol (K3, que inclui Davi e Eduardo), a família (K4) e o casal (K5). A componente C1 "
  "contém 3 comunidades, enquanto C2 e C3 coincidem com uma comunidade cada uma.")
figura("fig8_svg_programa.png",
       "Visualização gerada pelo próprio programa em C (arquivo `grafo.svg`, RF02) para a rede social "
       "fictícia, com layout de forças calculado na implementação. As cores indicam as 5 comunidades "
       "do Girvan–Newman; os vértices com contorno preto são articulações e as arestas vermelhas "
       "tracejadas são pontes. Observe que a componente conexa maior contém três comunidades.",
       largura=13.5)
P("No clube de caratê, a rede é conexa (uma componente), mas contém 5 comunidades (Q = 0,4013). O "
  "nível de 2 comunidades (Q = 0,360) separa os vértices aproximadamente como na divisão real "
  "observada por Zachary; os níveis seguintes subdividem esses dois grupos. Na ego-rede do "
  "Facebook (Figura 6), as 5 componentes geram Q = 0,0040, praticamente zero, pois a componente "
  "gigante concentra quase todas as arestas. O Girvan–Newman encontra **36 comunidades** com "
  "**Q = 0,4161**: algumas grandes (140, 39, 27, 22 e 13 membros) e muitas pequenas ou unitárias, "
  "formadas por usuários periféricos. A componente gigante, sozinha, contém 32 dessas comunidades; "
  "as quatro componentes pequenas correspondem a uma comunidade cada.")
figura("fig6_facebook.png",
       "Ego-rede 0 do Facebook (SNAP), com 333 usuários. As cores indicam as 8 maiores comunidades da "
       "partição de maior modularidade (Q = 0,4161), e o tamanho dos vértices é proporcional ao "
       "grau. Os vértices com contorno preto são articulações. As quatro componentes pequenas "
       "aparecem na faixa inferior.", largura=14.5)
P("Em todas as redes, confirmou-se que **toda comunidade está contida em uma única componente "
  "conexa**. Isso é uma consequência direta do algoritmo: como ele apenas remove arestas, nunca une "
  "vértices de componentes diferentes. Portanto, as comunidades são um refinamento das componentes: "
  "a componente responde se existe caminho, e a comunidade responde onde a rede é mais densa.")

H2("Experimento 5: fragmentação após remoções")
P("A Figura 7 compara as três estratégias de remoção no clube de caratê e no Facebook, e a "
  "Tabela 2 resume as frações críticas obtidas em cada rede.")
figura("fig7_remocoes.png",
       "Tamanho relativo da maior componente (S) em função da fração de itens removidos. Na linha de "
       "cima, remoção de usuários; na de baixo, de amizades. A linha pontilhada marca S = 0,5. As "
       "remoções orientadas por intermediação fragmentam a rede muito mais rápido que as aleatórias.")
P("**Tabela 2:** Fração de itens removidos até que S < 0,5 (fração crítica).", size=10, depois=2)
tabela(["Rede", "Itens", "Aleatória", "Por grau", "Por intermediação"], [
    ["Enunciado", "usuários", "33,3%", "22,2%", "11,1%"],
    ["Enunciado", "amizades", "50,0%", "50,0%", "20,0%"],
    ["Rede social", "usuários", "24,3%", "10,8%", "5,4%"],
    ["Rede social", "amizades", "50,7%", "35,2%", "4,2%"],
    ["Karate", "usuários", "44,1%", "11,8%", "11,8%"],
    ["Karate", "amizades", "71,8%", "62,8%", "30,8%"],
    ["Facebook ego-0", "usuários", "39,6%", "17,1%", "9,3%"],
    ["Facebook ego-0", "amizades", "85,9%", "87,0%", "6,3%"],
], larguras=[3.4, 2.4, 2.6, 2.6, 3.4], fonte=9)
P("Três conclusões se destacam. Primeiro, as redes são **robustas a falhas aleatórias e frágeis a "
  "ataques direcionados**, como observado por Albert, Jeong e Barabási (2000): no Facebook, é preciso "
  "remover ao acaso 39,6% dos usuários para partir a componente gigante, mas bastam 9,3% quando os "
  "usuários de maior intermediação são removidos primeiro. Segundo, a **intermediação é melhor "
  "critério de ataque que o grau**: os usuários mais populares estão, em geral, no centro de grupos "
  "densos e têm amigos redundantes, enquanto os de alta intermediação são os que ligam grupos. Isso "
  "é ainda mais evidente nas amizades: no Facebook, remover as arestas de maior produto de graus é "
  "**tão ineficaz quanto remover ao acaso** (87,0% contra 85,9%), pois elas estão dentro do núcleo "
  "denso; já as arestas de maior intermediação (a sequência do Girvan–Newman) partem a rede com "
  "apenas 6,3% das remoções. Terceiro, a fragmentação por intermediação acontece em **saltos**: cada "
  "queda brusca da curva corresponde à separação de uma comunidade inteira, o que mostra a ligação "
  "direta entre a estrutura de comunidades e a vulnerabilidade da rede.")

H2("Validação dos resultados")
P("Para verificar a correção da implementação, os resultados do programa em C foram comparados "
  "automaticamente (script `scripts/validar.py`) com os da biblioteca **NetworkX** (HAGBERG; SCHULT; "
  "SWART, 2008), uma implementação de referência em Python. Para as quatro redes, coincidiram "
  "exatamente: o número de vértices, arestas e componentes; o conjunto de vértices de articulação e "
  "de pontes; o número de componentes biconexas; κ(G) e λ(G), inclusive da maior componente; a "
  "intermediação de todos os vértices e de todas as arestas (diferença menor que 10⁻⁴); e a "
  "modularidade da melhor partição. Nas redes menores, a modularidade máxima do Girvan–Newman da "
  "NetworkX também coincidiu com a do programa.")

# ===================================================== COMPLEXIDADE
H("Complexidade das Operações")
P("Na tabela a seguir, n é o número de vértices, m o número de arestas, κ e λ as conectividades e R "
  "o número de repetições da simulação aleatória. Todas as estruturas auxiliares ocupam O(n + m) de "
  "memória, exceto o histórico do Girvan–Newman, que guarda uma partição (n inteiros) por nível do "
  "dendrograma, no máximo O(n²).")
P("**Tabela 3:** Complexidade das operações implementadas.", size=10, depois=2)
tabela(["Operação", "Algoritmo", "Tempo"], [
    ["Leitura do CSV e construção", "tabela hash + listas de adjacência", "O(n + m) esperado ¹"],
    ["Graus e densidade", "varredura das listas", "O(n + m)"],
    ["Componentes conexas / grafo conexo", "BFS", "O(n + m)"],
    ["Articulações, pontes e biconexas", "Tarjan (DFS iterativa)", "O(n + m)"],
    ["Conectividade por arestas λ(G)", "Menger + Edmonds–Karp", "O(n · λ · m)"],
    ["Conectividade por vértices κ(G)", "Menger + Even + Edmonds–Karp", "O(κ · n · κ · m) ²"],
    ["Intermediação (vértices e arestas)", "Brandes", "O(n · m)"],
    ["Girvan–Newman completo", "Brandes a cada remoção", "O(m² · n) ³"],
    ["Modularidade de uma partição", "varredura das arestas", "O(n + m)"],
    ["Remoção / restauração temporária", "marcas de ativo", "O(1) / O(n + m)"],
    ["Simulação aleatória", "Fisher–Yates + BFS por passo", "O(R · k · (n + m))"],
    ["Simulação por grau", "grau atual + BFS por passo", "O(k · (n + m))"],
    ["Simulação por intermediação", "Brandes + BFS por passo", "O(k · n · m)"],
    ["Visualização SVG", "Fruchterman–Reingold", "O(I · (n² + m))"],
], larguras=[5.6, 5.4, 4.6], fonte=9)
P("¹ Com a verificação de arestas repetidas, cada inserção custa O(d(u)) no pior caso. ² O número "
  "de pares testados pelo algoritmo de Even é O(κ · n), e cada fluxo é interrompido após κ caminhos "
  "aumentantes de custo O(n + m). ³ O pior caso ocorre enquanto a rede continua conexa; com o "
  "recálculo restrito às componentes afetadas, o custo real é bem menor quando a rede já está "
  "fragmentada. Na prática, o relatório completo da ego-rede do Facebook (333 vértices e 2.519 "
  "arestas), incluindo o Girvan–Newman completo e todas as simulações, foi gerado em cerca de 9 "
  "segundos. k é o número de remoções simuladas e I o número de iterações do layout.",
  size=10)

# ===================================================== IMPLEMENTAÇÃO
H("Implementação e Utilização")
P("O código foi escrito em C99, sem bibliotecas externas além da biblioteca padrão e da `libm`, e "
  "está dividido em módulos:")
tabela(["Arquivo", "Conteúdo", "Requisitos"], [
    ["`grafo.h/.c`", "estrutura do grafo, leitura do CSV, graus, densidade, remoções", "RF01, RF02"],
    ["`conectividade.h/.c`", "BFS, Tarjan, componentes biconexas, κ e λ por fluxo", "RF03 a RF07"],
    ["`comunidades.h/.c`", "Brandes, modularidade e Girvan–Newman", "RF08"],
    ["`remocao.h/.c`", "simulação de remoções aleatórias e orientadas", "RF09"],
    ["`relatorio.h/.c`", "seções do relatório, CSVs, SVG e DOT", "RF02, RF10"],
    ["`main.c`", "menu interativo e modo relatório", "todos"],
], larguras=[3.8, 9.2, 2.6], fonte=9)
P("A compilação é feita com `make` (ou `gcc -std=c99 -O2 -o redes src/*.c -lm`). O programa pode ser "
  "usado de duas formas:")
lista(["`./redes dados/amizades.csv` abre o **menu interativo**, com opções para exibir o resumo, a "
       "lista de adjacência, as componentes, as articulações e pontes, as componentes biconexas, κ e "
       "λ, as comunidades, remover usuários ou amizades, restaurar a rede, simular remoções, exportar "
       "a visualização e gerar o relatório;",
       "`./redes dados/amizades.csv -r resultados/amizades` gera diretamente o **relatório de "
       "métricas** (RF10): `relatorio.txt` com todas as etapas, `vertices.csv` (grau, componente, "
       "comunidade, articulação e intermediação de cada usuário), `arestas.csv` (ponte, bloco, "
       "intermediação e ordem de remoção no Girvan–Newman), `girvan_newman.csv` (dendrograma), "
       "`remocao_vertices.csv` e `remocao_arestas.csv` (curvas de robustez), `grafo.svg` e `grafo.dot`."])

# ===================================================== APLICAÇÕES
H("Aplicações")
P("Os conceitos de conectividade e de comunidades são aplicados em praticamente todas as áreas em "
  "que os dados formam uma rede. Em **redes sociais online**, as comunidades são usadas para "
  "recomendar amizades e conteúdo (pessoas da mesma comunidade tendem a compartilhar interesses), "
  "para segmentar campanhas e para identificar bolhas de opinião. Os usuários de alta intermediação "
  "e as articulações são os **conectores** entre grupos, importantes para a difusão de informação e, "
  "do outro lado, alvos prioritários no combate à desinformação.")
P("Em **epidemiologia**, a rede de contatos determina como uma doença se espalha. Vacinar ou isolar "
  "os vértices de maior intermediação, e não os escolhidos ao acaso, fragmenta a rede com muito "
  "menos intervenções, exatamente o efeito observado no Experimento 5. Em **infraestrutura** (redes "
  "elétricas, de telecomunicações, de transporte e a própria Internet), articulações e pontes são "
  "pontos únicos de falha: um roteador ou um cabo cuja falha desconecta uma região. Medir κ e λ "
  "indica quantas falhas simultâneas a rede suporta, e projetos tolerantes a falhas buscam κ ≥ 2 "
  "(redes biconexas).")
P("Em **biologia**, as comunidades de redes de interação entre proteínas correspondem a complexos e "
  "módulos funcionais, e as articulações podem indicar proteínas essenciais. Em **engenharia de "
  "software**, o grafo de dependências entre módulos pode ser analisado da mesma forma: comunidades "
  "sugerem uma divisão em componentes, e pontes indicam dependências que, se quebradas, isolam "
  "partes do sistema. Em **segurança**, a detecção de comunidades em redes de transações ajuda a "
  "identificar grupos de contas que agem em conjunto, como em fraudes e redes de robôs.")

# ===================================================== COMPARAÇÃO
H("Comparação com Outros Métodos de Detecção de Comunidades")
P("O Girvan–Newman foi o primeiro método a popularizar a detecção de comunidades baseada em "
  "intermediação, e o seu custo motivou uma série de alternativas (FORTUNATO, 2010). A tabela a "
  "seguir compara o algoritmo implementado com os métodos mais conhecidos.")
P("**Tabela 4:** Comparação entre métodos de detecção de comunidades.", size=10, depois=2)
tabela(["Característica", "Girvan–Newman", "Louvain", "Propagação de rótulos", "Espectral"], [
    ["Estratégia", "Divisiva: remove arestas de maior intermediação",
     "Aglomerativa: une grupos que aumentam Q", "Cada vértice adota o rótulo mais comum dos vizinhos",
     "Autovetores da matriz laplaciana ou de modularidade"],
    ["Custo", "O(m² n)", "≈ O(m) por passagem", "≈ O(m) por iteração", "O(n³) (ou iterativo)"],
    ["Escala prática", "Centenas a poucos milhares de vértices", "Milhões de vértices",
     "Milhões de vértices", "Milhares de vértices"],
    ["Número de grupos", "Escolhido pela maior Q no dendrograma", "Automático (máximo local de Q)",
     "Automático", "Precisa ser informado (k)"],
    ["Determinismo", "Sim (com desempate fixo)", "Depende da ordem dos vértices", "Não (aleatório)",
     "Sim"],
    ["Produz hierarquia", "Sim (dendrograma)", "Sim (níveis de agregação)", "Não", "Não"],
], larguras=[2.8, 3.3, 3.2, 3.2, 3.1], fonte=8)
P("O método de **Louvain** (BLONDEL et al., 2008) é hoje o mais usado na prática: move cada vértice "
  "para a comunidade vizinha que mais aumenta a modularidade e depois agrega cada comunidade em um "
  "supervértice, repetindo o processo. Ele encontra, em geral, valores de Q mais altos que o "
  "Girvan–Newman em uma fração do tempo. A **propagação de rótulos** é ainda mais rápida, mas não "
  "otimiza nenhuma medida explicitamente e pode produzir resultados diferentes a cada execução. Os "
  "métodos **espectrais** têm boa fundamentação matemática, mas exigem informar o número de grupos.")
P("O Girvan–Newman, porém, tem vantagens didáticas e analíticas: é **determinístico**, produz a "
  "**hierarquia completa** de divisões (é possível observar como a rede se divide passo a passo) e "
  "se relaciona diretamente com a conectividade estudada nas etapas anteriores, pois as primeiras "
  "arestas que ele remove são, com frequência, as pontes e as ligações frágeis entre grupos. Também "
  "convém lembrar uma limitação conhecida da modularidade, o **limite de resolução** (FORTUNATO; "
  "BARTHÉLEMY, 2007): em redes grandes, comunidades pequenas podem ficar ocultas dentro de outras "
  "maiores, e, no outro extremo, a partição do Facebook mostrou muitas comunidades unitárias de "
  "usuários periféricos.")

# ===================================================== CONSIDERAÇÕES
H("Considerações Finais")
P("Este projeto mostrou como um conjunto de algoritmos clássicos da Teoria dos Grafos, todos "
  "construídos sobre buscas em largura e em profundidade, responde às principais perguntas sobre a "
  "estrutura de uma rede social. Retomando as questões centrais:")
lista(["**Quantas componentes conexas existem?** A BFS responde em tempo linear: 1 na rede do "
       "enunciado e no caratê, 3 na rede fictícia e 5 na ego-rede do Facebook, que possui uma "
       "componente gigante com 97,3% dos usuários.",
       "**Quais usuários mantêm a rede conectada?** Os vértices de articulação, obtidos pelo "
       "algoritmo de Tarjan, como o instrutor do clube de caratê ou Tiago e Vitor na rede fictícia. "
       "A conectividade κ = 1 da maior componente de todas as redes confirma que cada uma delas pode "
       "ser desconectada pela saída de um único usuário.",
       "**Quais conexões são críticas?** As pontes, também obtidas pelo Tarjan; a de maior impacto é "
       "a de maior intermediação, como {Tiago, Vitor}, única ligação entre dois grupos.",
       "**Quais comunidades podem ser identificadas?** O Girvan–Newman encontrou divisões com "
       "modularidade entre 0,40 e 0,69, sempre como refinamento das componentes conexas: uma única "
       "componente pode conter várias comunidades.",
       "**Como a rede se fragmenta após remoções?** Lentamente diante de remoções aleatórias e "
       "rapidamente diante de remoções orientadas por intermediação, que no Facebook partiram a "
       "componente gigante com 9,3% dos usuários ou 6,3% das amizades."], numerada=True)
P("A principal lição do trabalho é a relação entre **conectividade e comunidades**. As arestas que "
  "ligam comunidades são as de maior intermediação e, frequentemente, as pontes da rede; por isso, o "
  "mesmo cálculo que revela as comunidades revela também os pontos mais vulneráveis à fragmentação. "
  "Do ponto de vista da implementação, destacam-se a DFS iterativa, que torna o Tarjan seguro em "
  "redes grandes, a representação com marcas de ativo, que torna as remoções temporárias triviais, "
  "e o recálculo da intermediação restrito às componentes afetadas, que acelera o Girvan–Newman. "
  "Todos os resultados foram validados contra uma biblioteca de referência. Como trabalhos futuros, "
  "seria possível implementar o método de Louvain para analisar a rede completa do Facebook (4.039 "
  "usuários e 88.234 amizades) e comparar as comunidades encontradas com os círculos sociais "
  "rotulados disponíveis no conjunto do SNAP.")
P("O funcionamento das operações descritas neste relatório pode ser observado na implementação em C "
  "entregue junto a este documento.")

# ===================================================== REFERÊNCIAS
quebra()
H("REFERÊNCIAS")
refs = [
    "ALBERT, Réka; JEONG, Hawoong; BARABÁSI, Albert-László. Error and attack tolerance of complex "
    "networks. **Nature**, v. 406, p. 378–382, 2000. DOI: https://doi.org/10.1038/35019019.",
    "BLONDEL, Vincent D.; GUILLAUME, Jean-Loup; LAMBIOTTE, Renaud; LEFEBVRE, Etienne. Fast unfolding "
    "of communities in large networks. **Journal of Statistical Mechanics: Theory and Experiment**, "
    "v. 2008, n. 10, P10008, 2008. DOI: https://doi.org/10.1088/1742-5468/2008/10/P10008.",
    "BRANDES, Ulrik. A faster algorithm for betweenness centrality. **Journal of Mathematical "
    "Sociology**, v. 25, n. 2, p. 163–177, 2001. DOI: https://doi.org/10.1080/0022250X.2001.9990249.",
    "EDMONDS, Jack; KARP, Richard M. Theoretical improvements in algorithmic efficiency for network "
    "flow problems. **Journal of the ACM**, v. 19, n. 2, p. 248–264, 1972. DOI: "
    "https://doi.org/10.1145/321694.321699.",
    "EULER, Leonhard. Solutio problematis ad geometriam situs pertinentis. **Commentarii Academiae "
    "Scientiarum Petropolitanae**, v. 8, p. 128–140, 1736.",
    "EVEN, Shimon; TARJAN, Robert Endre. Network flow and testing graph connectivity. **SIAM Journal "
    "on Computing**, v. 4, n. 4, p. 507–518, 1975. DOI: https://doi.org/10.1137/0204043.",
    "FORTUNATO, Santo. Community detection in graphs. **Physics Reports**, v. 486, n. 3–5, "
    "p. 75–174, 2010. DOI: https://doi.org/10.1016/j.physrep.2009.11.002.",
    "FORTUNATO, Santo; BARTHÉLEMY, Marc. Resolution limit in community detection. **Proceedings of "
    "the National Academy of Sciences**, v. 104, n. 1, p. 36–41, 2007. DOI: "
    "https://doi.org/10.1073/pnas.0605965104.",
    "FREEMAN, Linton C. A set of measures of centrality based on betweenness. **Sociometry**, v. 40, "
    "n. 1, p. 35–41, 1977. DOI: https://doi.org/10.2307/3033543.",
    "FRUCHTERMAN, Thomas M. J.; REINGOLD, Edward M. Graph drawing by force-directed placement. "
    "**Software: Practice and Experience**, v. 21, n. 11, p. 1129–1164, 1991. DOI: "
    "https://doi.org/10.1002/spe.4380211102.",
    "GIRVAN, Michelle; NEWMAN, Mark E. J. Community structure in social and biological networks. "
    "**Proceedings of the National Academy of Sciences**, v. 99, n. 12, p. 7821–7826, 2002. DOI: "
    "https://doi.org/10.1073/pnas.122653799.",
    "GRANOVETTER, Mark S. The strength of weak ties. **American Journal of Sociology**, v. 78, n. 6, "
    "p. 1360–1380, 1973. DOI: https://doi.org/10.1086/225469.",
    "HAGBERG, Aric A.; SCHULT, Daniel A.; SWART, Pieter J. Exploring network structure, dynamics, and "
    "function using NetworkX. In: PYTHON IN SCIENCE CONFERENCE (SciPy), 7., 2008, Pasadena. "
    "**Proceedings** [...]. Pasadena: SciPy, 2008. p. 11–15.",
    "HOPCROFT, John; TARJAN, Robert. Algorithm 447: efficient algorithms for graph manipulation. "
    "**Communications of the ACM**, v. 16, n. 6, p. 372–378, 1973. DOI: "
    "https://doi.org/10.1145/362248.362272.",
    "LESKOVEC, Jure; MCAULEY, Julian. Learning to discover social circles in ego networks. In: "
    "ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS (NIPS), 25., 2012, Lake Tahoe. "
    "**Proceedings** [...]. 2012. p. 539–547. Dados disponíveis em: "
    "https://snap.stanford.edu/data/ego-Facebook.html. Acesso em: 23 nov. 2026.",
    "MENGER, Karl. Zur allgemeinen Kurventheorie. **Fundamenta Mathematicae**, v. 10, p. 96–115, "
    "1927.",
    "NEWMAN, Mark E. J.; GIRVAN, Michelle. Finding and evaluating community structure in networks. "
    "**Physical Review E**, v. 69, n. 2, 026113, 2004. DOI: https://doi.org/10.1103/PhysRevE.69.026113.",
    "TARJAN, Robert. Depth-first search and linear graph algorithms. **SIAM Journal on Computing**, "
    "v. 1, n. 2, p. 146–160, 1972. DOI: https://doi.org/10.1137/0201010.",
    "ZACHARY, Wayne W. An information flow model for conflict and fission in small groups. **Journal "
    "of Anthropological Research**, v. 33, n. 4, p. 452–473, 1977. DOI: "
    "https://doi.org/10.1086/jar.33.4.3629752.",
]
for ref in refs:
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    par.paragraph_format.line_spacing = 1.0
    par.paragraph_format.space_after = Pt(10)
    runs(par, ref, size=11)

doc.save(SAIDA)
print("relatório salvo em", SAIDA)
