"""Gera dados/karate.csv (Zachary, 1977) e dados/facebook_ego0.csv (SNAP).

A ego-rede 0 é o subgrafo induzido pelos amigos do usuário 0 no arquivo
facebook_combined.txt do SNAP (o próprio ego é excluído, como nos arquivos
*.edges do conjunto original).
"""
import gzip
import sys
import urllib.request
from pathlib import Path

import networkx as nx

dados = Path(sys.argv[1] if len(sys.argv) > 1 else "dados")

k = nx.karate_club_graph()
with open(dados / "karate.csv", "w", newline="\n") as f:
    f.write("pessoa1,pessoa2\n")
    for u, v in sorted(k.edges()):
        f.write(f"{u + 1},{v + 1}\n")

url = "https://snap.stanford.edu/data/facebook_combined.txt.gz"
bruto = gzip.decompress(urllib.request.urlopen(url, timeout=60).read()).decode()
fb = nx.parse_edgelist(bruto.splitlines(), nodetype=int)
ego = 0
amigos = set(fb.neighbors(ego))
sub = fb.subgraph(amigos)
with open(dados / "facebook_ego0.csv", "w", newline="\n") as f:
    f.write("pessoa1,pessoa2\n")
    for u, v in sorted(tuple(sorted(e)) for e in sub.edges()):
        f.write(f"{u},{v}\n")
print("karate:", k.number_of_nodes(), k.number_of_edges())
print("ego0  :", sub.number_of_nodes(), sub.number_of_edges(),
      "componentes:", nx.number_connected_components(sub))
