"""Gera as figuras do relatório a partir dos resultados do programa em C.

Uso (na raiz do projeto, após `make experimentos`):
    python relatorio/figuras.py
"""
import csv
from pathlib import Path

import cairosvg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
OUT = RAIZ / "relatorio" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

PALETA = ["#4E79A7", "#F28E2B", "#59A14F", "#B07AA1", "#76B7B2", "#EDC948",
          "#9C755F", "#FF9DA7", "#86BCB6", "#D37295", "#8CD17D", "#A0CBE8"]
AZUL, CINZA, CINZA_ESC, VERM = "#1F5FAD", "#BDBDBD", "#555555", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def ler_grafo(nome):
    G = nx.Graph()
    with open(RAIZ / "dados" / f"{nome}.csv") as f:
        r = csv.reader(f)
        next(r)
        G.add_edges_from((a.strip(), b.strip()) for a, b in r)
    return G


def ler_vertices(nome):
    return {r["vertice"]: r for r in csv.DictReader(open(RES / nome / "vertices.csv"))}


def ler_arestas(nome):
    return list(csv.DictReader(open(RES / nome / "arestas.csv")))


def salvar(fig, nome):
    fig.savefig(OUT / nome, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("figura:", nome)


def layout_por_componente(G):
    """Layout de forças na maior componente; as pequenas ficam numa faixa abaixo."""
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    pos = nx.spring_layout(G.subgraph(comps[0]), seed=3, k=0.12, iterations=300)
    xs = [p[0] for p in pos.values()]
    x0, x1 = min(xs), max(xs)
    ybase = min(p[1] for p in pos.values()) - 0.25
    for i, c in enumerate(comps[1:]):
        cx = x0 + (x1 - x0) * (i + 0.5) / max(1, len(comps) - 1)
        for j, v in enumerate(sorted(c)):
            pos[v] = (cx + 0.06 * j, ybase)
    return pos


def desenhar(ax, G, pos, cor_no, borda, larg_borda, pontes=(), rotulos=True, tam=520,
             fonte=10, cor_aresta=CINZA, cor_rotulo="white"):
    normais = [e for e in G.edges() if frozenset(e) not in pontes]
    nx.draw_networkx_edges(G, pos, edgelist=normais, ax=ax, edge_color=cor_aresta, width=1.6)
    if pontes:
        nx.draw_networkx_edges(G, pos, edgelist=[tuple(p) for p in pontes], ax=ax,
                               edge_color=VERM, width=2.6, style="dashed")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=[cor_no[v] for v in G],
                           edgecolors=[borda[v] for v in G],
                           linewidths=[larg_borda[v] for v in G], node_size=tam)
    if rotulos:
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=fonte, font_weight="bold",
                                font_color=cor_rotulo)
    ax.set_axis_off()


# ---------------------------------------------------------------------------
# Figura 1 - rede do enunciado: graus, articulações, pontes e biconexas
# ---------------------------------------------------------------------------
G = ler_grafo("amizades")
V = ler_vertices("amizades")
E = ler_arestas("amizades")
pos_ex = {"A": (0, 0.9), "B": (0, -0.9), "C": (1.3, 0), "D": (2.6, 0), "E": (3.9, 0),
          "F": (5.2, 0), "G": (6.3, 0.9), "H": (6.3, -0.9), "I": (7.6, -0.9)}
pontes = {frozenset((e["pessoa1"], e["pessoa2"])) for e in E if e["ponte"] == "1"}
art = {v for v, r in V.items() if r["articulacao"] == "1"}

fig, axs = plt.subplots(1, 2, figsize=(12, 3.6))
ax = axs[0]
desenhar(ax, G, pos_ex, {v: CINZA_ESC if v in art else "#9E9E9E" for v in G},
         {v: "black" for v in G}, {v: 2.5 if v in art else 0.5 for v in G}, pontes)
for v, (x, y) in pos_ex.items():
    ax.text(x, y - 0.42 if y <= 0 else y + 0.33, f"grau {V[v]['grau']}", ha="center",
            fontsize=8, color="#333")
ax.set_title("Rede do enunciado: articulações (escuro) e pontes (tracejado)", fontsize=10)
ax.set_ylim(-1.6, 1.5)

ax = axs[1]
bcc = {frozenset((e["pessoa1"], e["pessoa2"])): int(e["biconexa"]) for e in E}
cores_b = {b: PALETA[i % len(PALETA)] for i, b in enumerate(sorted(set(bcc.values())))}
for (u, v) in G.edges():
    b = bcc[frozenset((u, v))]
    nx.draw_networkx_edges(G, pos_ex, edgelist=[(u, v)], ax=ax, edge_color=cores_b[b], width=4)
    (x1, y1), (x2, y2) = pos_ex[u], pos_ex[v]
nx.draw_networkx_nodes(G, pos_ex, ax=ax, node_color="white", edgecolors=CINZA_ESC,
                       linewidths=1.5, node_size=520)
nx.draw_networkx_labels(G, pos_ex, ax=ax, font_size=10, font_weight="bold")
for b, cor in cores_b.items():
    membros = sorted({x for k, bb in bcc.items() if bb == b for x in k})
    cx = sum(pos_ex[m][0] for m in membros) / len(membros)
    cy = sum(pos_ex[m][1] for m in membros) / len(membros)
    ax.text(cx, cy + (0.28 if len(membros) == 2 else 0.0), f"B{b}", color=cor, fontsize=9,
            fontweight="bold", ha="center", va="center")
ax.set_title("Componentes biconexas (cada cor é um bloco)", fontsize=10)
ax.set_ylim(-1.6, 1.5)
ax.set_axis_off()
salvar(fig, "fig1_rede_exemplo.png")

# ---------------------------------------------------------------------------
# Figura 2 - árvore da DFS de Tarjan com disc/low
# ---------------------------------------------------------------------------
ordem = "ABCDEFGHI"
disc = {v: i + 1 for i, v in enumerate(ordem)}
low = {"A": 1, "B": 1, "C": 1, "D": 4, "E": 5, "F": 6, "G": 6, "H": 6, "I": 9}
pos_t = {v: (i * 1.25, 0) for i, v in enumerate(ordem)}
fig, ax = plt.subplots(figsize=(12, 2.6))
T = nx.Graph([(ordem[i], ordem[i + 1]) for i in range(len(ordem) - 1)])
pontes_t = {frozenset(p) for p in [("C", "D"), ("D", "E"), ("E", "F"), ("H", "I")]}
for (u, v) in T.edges():
    eh_ponte = frozenset((u, v)) in pontes_t
    ax.annotate("", xy=pos_t[v], xytext=pos_t[u],
                arrowprops=dict(arrowstyle="-|>", color=VERM if eh_ponte else CINZA_ESC,
                                lw=2.4 if eh_ponte else 1.6, linestyle="--" if eh_ponte else "-",
                                shrinkA=14, shrinkB=14))
for (u, v) in [("C", "A"), ("H", "F")]:
    ax.annotate("", xy=pos_t[v], xytext=pos_t[u],
                arrowprops=dict(arrowstyle="-|>", color=AZUL, lw=1.6, linestyle=":",
                                connectionstyle="arc3,rad=0.45", shrinkA=14, shrinkB=14))
nx.draw_networkx_nodes(T, pos_t, ax=ax, node_size=700,
                       node_color=[CINZA_ESC if v in art else "#9E9E9E" for v in ordem],
                       edgecolors="black", linewidths=[2.5 if v in art else 0.5 for v in ordem])
nx.draw_networkx_labels(T, pos_t, ax=ax, font_color="white", font_weight="bold")
for v in ordem:
    x, y = pos_t[v]
    ax.text(x, y - 0.5, f"disc={disc[v]}\nlow={low[v]}", ha="center", va="top", fontsize=9)
ax.text(1.25, 0.95, "retorno C→A", color=AZUL, fontsize=9, ha="center")
ax.text(7.5 * 1.0 + 0.6, 0.95, "retorno H→F", color=AZUL, fontsize=9, ha="center")
ax.legend(handles=[Line2D([], [], color=CINZA_ESC, lw=1.6, label="aresta de árvore"),
                   Line2D([], [], color=VERM, lw=2.4, ls="--", label="ponte (low[filho] > disc[pai])"),
                   Line2D([], [], color=AZUL, lw=1.6, ls=":", label="aresta de retorno")],
          loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False, fontsize=9)
ax.set_xlim(-0.6, 10.6)
ax.set_ylim(-1.75, 1.15)
ax.set_axis_off()
salvar(fig, "fig2_tarjan.png")

# ---------------------------------------------------------------------------
# Figura 3 - Girvan-Newman no exemplo: intermediação das arestas e partição
# ---------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12, 3.6))
ax = axs[0]
ebc = {frozenset((e["pessoa1"], e["pessoa2"])): float(e["intermediacao"]) for e in E}
mx = max(ebc.values())
for (u, v) in G.edges():
    val = ebc[frozenset((u, v))]
    nx.draw_networkx_edges(G, pos_ex, edgelist=[(u, v)], ax=ax, width=1 + 5 * val / mx,
                           edge_color=VERM if val == mx else CINZA_ESC)
nx.draw_networkx_edge_labels(G, pos_ex, ax=ax, font_size=8,
                             edge_labels={(u, v): f"{ebc[frozenset((u, v))]:.0f}" for u, v in G.edges()},
                             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
nx.draw_networkx_nodes(G, pos_ex, ax=ax, node_color="#9E9E9E", node_size=520, edgecolors="black",
                       linewidths=0.5)
nx.draw_networkx_labels(G, pos_ex, ax=ax, font_color="white", font_weight="bold")
ax.set_title("Intermediação das arestas: {D,E} e {E,F} empatam em 20;\nremove-se {D,E} (menor índice)", fontsize=10)
ax.set_ylim(-1.6, 1.5)
ax.set_axis_off()

ax = axs[1]
H = G.copy()
H.remove_edge("D", "E")
cor = {v: PALETA[0] if v in "ABCD" else PALETA[1] for v in G}
nx.draw_networkx_edges(G, pos_ex, edgelist=[("D", "E")], ax=ax, edge_color=VERM, style="dotted",
                       width=1.5)
desenhar(ax, H, pos_ex, cor, {v: "white" for v in G}, {v: 1 for v in G})
ax.text(3.25, 0.35, "removida", color=VERM, fontsize=8, ha="center")
ax.set_title("Partição obtida: {A,B,C,D} e {E,F,G,H,I}, Q = 0,395", fontsize=10)
ax.set_ylim(-1.6, 1.5)
salvar(fig, "fig3_gn_exemplo.png")

# ---------------------------------------------------------------------------
# Figura 4 - Karate Club: partição de maior modularidade e curva de Q
# ---------------------------------------------------------------------------
G = ler_grafo("karate")
V = ler_vertices("karate")
gn = list(csv.DictReader(open(RES / "karate" / "girvan_newman.csv")))
pos = nx.spring_layout(G, seed=4, k=0.35, iterations=200)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})
desenhar(axs[0], G, pos, {v: PALETA[int(V[v]["comunidade"]) - 1] for v in G},
         {v: "black" if V[v]["articulacao"] == "1" else "white" for v in G},
         {v: 2.5 if V[v]["articulacao"] == "1" else 1 for v in G},
         pontes={frozenset(("1", "12"))}, tam=330, fonte=8)
axs[0].set_title("Karate Club: 5 comunidades (Q = 0,4013)", fontsize=10)
xs = [int(r["arestas_removidas"]) for r in gn]
qs = [float(r["modularidade"]) for r in gn]
ks = [int(r["comunidades"]) for r in gn]
ax = axs[1]
ax.step(xs, qs, where="post", color=AZUL, lw=2)
ib = max(range(len(qs)), key=lambda i: qs[i])
ax.plot(xs[ib], qs[ib], "o", color=VERM)
ax.annotate(f"máximo: {ks[ib]} comunidades\nQ = {qs[ib]:.4f}", (xs[ib], qs[ib]),
            xytext=(xs[ib] + 12, qs[ib] - 0.02), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#333"))
ax.set_xlabel("arestas removidas pelo Girvan–Newman")
ax.set_ylabel("modularidade Q")
ax.grid(alpha=0.3)
ax.set_title("Modularidade ao longo do dendrograma", fontsize=10)
salvar(fig, "fig4_karate.png")

# ---------------------------------------------------------------------------
# Figura 6 - ego-rede do Facebook (SNAP): comunidades
# ---------------------------------------------------------------------------
G = ler_grafo("facebook_ego0")
V = ler_vertices("facebook_ego0")
tam_com = {}
for r in V.values():
    tam_com[r["comunidade"]] = tam_com.get(r["comunidade"], 0) + 1
maiores = sorted(tam_com, key=lambda c: -tam_com[c])[:8]
cor_com = {c: PALETA[i] for i, c in enumerate(maiores)}
pos = layout_por_componente(G)
fig, ax = plt.subplots(figsize=(10, 8))
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#CFCFCF", width=0.4)
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=[18 + 1.2 * int(V[v]["grau"]) for v in G],
                       node_color=[cor_com.get(V[v]["comunidade"], "#9E9E9E") for v in G],
                       edgecolors=["black" if V[v]["articulacao"] == "1" else "white" for v in G],
                       linewidths=[1.5 if V[v]["articulacao"] == "1" else 0.3 for v in G])
ax.legend(handles=[Line2D([], [], marker="o", ls="", mfc=cor_com[c], mec="white", ms=9,
                          label=f"K{c} ({tam_com[c]})") for c in maiores] +
          [Line2D([], [], marker="o", ls="", mfc="#9E9E9E", mec="white", ms=9,
                  label="demais (≤ 5 membros)")],
          loc="upper left", bbox_to_anchor=(0.98, 1.0), fontsize=9, frameon=False, ncol=1)
ax.set_axis_off()
salvar(fig, "fig6_facebook.png")

# ---------------------------------------------------------------------------
# Figura 7 - curvas de robustez (remoções aleatórias x orientadas)
# ---------------------------------------------------------------------------
fig, axs = plt.subplots(2, 2, figsize=(12, 8))
estilos = [("S_aleatoria", "aleatória (média de 50)", CINZA_ESC, "-"),
           ("S_grau", "orientada por grau", "#F28E2B", "--"),
           ("S_intermediacao", "orientada por intermediação", AZUL, "-")]
for j, (nome, titulo_rede) in enumerate([("karate", "Karate Club"),
                                         ("facebook_ego0", "Facebook ego-0 (SNAP)")]):
    for i, alvo in enumerate(["vertices", "arestas"]):
        rows = list(csv.DictReader(open(RES / nome / f"remocao_{alvo}.csv")))
        ax = axs[i][j]
        fr = [float(r["fracao"]) for r in rows]
        for col, rot, cor, ls in estilos:
            ax.plot(fr, [float(r[col]) for r in rows], ls, color=cor, lw=2, label=rot)
        ax.axhline(0.5, color="#999", lw=0.8, ls=":")
        ax.set_title(f"{titulo_rede} – remoção de {'usuários' if alvo == 'vertices' else 'amizades'}",
                     fontsize=10)
        ax.set_xlabel(f"fração de {"vértices removidos" if alvo == "vertices" else "arestas removidas"}")
        ax.set_ylabel("S = maior componente / n")
        ax.set_ylim(0, 1.03)
        ax.grid(alpha=0.3)
axs[0][0].legend(fontsize=9)
fig.tight_layout()
salvar(fig, "fig7_remocoes.png")

# ---------------------------------------------------------------------------
# Figura 8 - visualização SVG gerada pelo próprio programa em C (RF02)
# ---------------------------------------------------------------------------
cairosvg.svg2png(url=str(RES / "rede_social" / "grafo.svg"),
                 write_to=str(OUT / "fig8_svg_programa.png"), output_width=1100)
print("figura: fig8_svg_programa.png")
