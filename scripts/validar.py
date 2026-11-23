"""Confere os resultados do programa em C com a biblioteca networkx."""
import csv
import re
import sys
from pathlib import Path

import networkx as nx
from networkx.algorithms import community as nxc

ok_total = True

def checa(nome, a, b):
    global ok_total
    ok = a == b if not isinstance(a, float) else abs(a - b) < 1e-6
    ok_total &= ok
    print(f"  [{'OK' if ok else 'FALHA'}] {nome}: C={a}  networkx={b}")

for nome in ["amizades", "rede_social", "karate", "facebook_ego0"]:
    print(f"== {nome}")
    G = nx.Graph()
    with open(f"dados/{nome}.csv") as f:
        r = csv.reader(f); next(r)
        G.add_edges_from((a.strip(), b.strip()) for a, b in r)
    res = Path("resultados") / nome
    V = {row["vertice"]: row for row in csv.DictReader(open(res / "vertices.csv"))}
    E = list(csv.DictReader(open(res / "arestas.csv")))
    txt = (res / "relatorio.txt").read_text()

    checa("vertices", len(V), G.number_of_nodes())
    checa("arestas", len(E), G.number_of_edges())
    checa("componentes", len({v["componente"] for v in V.values()}),
          nx.number_connected_components(G))
    checa("articulacoes", {k for k, v in V.items() if v["articulacao"] == "1"},
          set(nx.articulation_points(G)))
    checa("pontes", {frozenset((e["pessoa1"], e["pessoa2"])) for e in E if e["ponte"] == "1"},
          {frozenset(e) for e in nx.bridges(G)})
    checa("n. biconexas", len({e["biconexa"] for e in E}),
          sum(1 for _ in nx.biconnected_components(G)))
    bc = nx.betweenness_centrality(G, normalized=False)
    checa("intermediacao vertices", max(abs(float(V[k]["intermediacao"]) - bc[k]) for k in G) < 1e-4, True)
    ebc = nx.edge_betweenness_centrality(G, normalized=False)
    ebc = {frozenset(k): v for k, v in ebc.items()}
    checa("intermediacao arestas",
          max(abs(float(e["intermediacao"]) - ebc[frozenset((e["pessoa1"], e["pessoa2"]))]) for e in E) < 1e-4, True)

    m = re.search(r"Rede completa : kappa\(G\) = (\d+), lambda\(G\) = (\d+)", txt)
    checa("kappa(G)", int(m.group(1)), nx.node_connectivity(G))
    checa("lambda(G)", int(m.group(2)), nx.edge_connectivity(G))
    m = re.search(r"Maior compon. : kappa = (\d+), lambda = (\d+)", txt)
    if m:
        H = G.subgraph(max(nx.connected_components(G), key=len))
        checa("kappa(maior comp.)", int(m.group(1)), nx.node_connectivity(H))
        checa("lambda(maior comp.)", int(m.group(2)), nx.edge_connectivity(H))

    # modularidade da melhor partição do C, recalculada pelo networkx
    grupos = {}
    for k, v in V.items():
        grupos.setdefault(v["comunidade"], set()).add(k)
    q_c = float(re.search(r"Melhor particao: \d+ comunidades, Q = ([-\d.]+)", txt).group(1))
    checa("Q da particao (recalculado)", round(nxc.modularity(G, grupos.values()), 4), q_c)
    if G.number_of_edges() < 200:
        melhor = max((nxc.modularity(G, p) for p in nxc.girvan_newman(G)), default=0)
        checa("Q maximo Girvan-Newman (networkx)", round(melhor, 4), q_c)

print("\nRESULTADO:", "TODOS OK" if ok_total else "HA FALHAS")
