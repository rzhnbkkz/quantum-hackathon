import sys, json, networkx as nx
sys.path.insert(0, "tools")
from v11 import Net
P = [("chattanooga_r1", "Chattanooga area (ACTIVSg70k)"), ("knoxville_r1", "Knoxville area"), ("nashville_r1", "Nashville area"),
     ("huntsville_r1", "Huntsville area"), ("memphis_r1", "Memphis area"), ("atlanta_r1", "Atlanta area"),
     ("ieee_30", "IEEE 30-bus test case"), ("ieee_118", "IEEE 118-bus test case")]
out = []
for key, title in P:
    n = Net(f"griddata/regions/{key}.json"); G = n.G
    pos = nx.kamada_kawai_layout(G, weight="km")
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    sx = lambda v: round(40 + 920 * (v - min(xs)) / (max(xs) - min(xs) or 1), 1)
    sy = lambda v: round(40 + 620 * (v - min(ys)) / (max(ys) - min(ys) or 1), 1)
    Y = n.milp(8, 4, mu=0.25) or set(); v, used, prot = n.evaluate(Y, 4)
    out.append(dict(key=key, title=title, cc=n.cc,
        nodes=[dict(id=s, mw=round(G.nodes[s]["mw"], 1), kv=G.nodes[s]["kv"], x=sx(pos[s][0]), y=sy(pos[s][1])) for s in G],
        edges=[dict(a=a, b=b, km=round(G[a][b]["km"], 2)) for a, b in G.edges],
        exact=dict(K=8, T=4, H=3, mu=0.25, db=0.35, loss=10, links=sorted([list(e) for e in Y]), trusted=sorted(used), protected=prot)))
    print(key, G.number_of_nodes(), G.number_of_edges(), len(Y), sorted(used))
json.dump(out, open("tool/presets.json", "w"))
