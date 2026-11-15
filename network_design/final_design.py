"""Final Step 3 design (v1.2) for the Chattanooga-area grid: 8 QKD links, at most 4 trusted nodes, balanced objective
(mu = 0.25: secrecy behind QKD + tap detection on busy links), plus backup routes. Draws network_diagram.png.
Usage: python final_design.py <region.json> <out.png> <out.json>"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import networkx as nx, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from v11 import Net
from resilience import backup_routes
path, out_png, out_json = sys.argv[1:4]
K, T, MU = 8, 4, 0.25
net = Net(path); Y = net.milp(K, T, mu=MU); val, used, prot = net.evaluate(Y, T)
bk = backup_routes(net); G = net.G
short = lambda s: s.replace("CHATTANOOGA", "CHA").replace("ROSSVILLE", "Rossv.").replace("SIGNAL MOUNTAIN", "Signal Mtn").title().replace("Cha", "CHA").replace("Rossv.", "Rossv.")
summary = dict(network=net.name, substations=G.number_of_nodes(), links=G.number_of_edges(), qkd_feasible_links=len(net.feasible),
               control_centers=net.cc, qkd_links=sorted(f"{a} - {b}" for a, b in Y),
               qkd_link_km={f"{a} - {b}": round(G[a][b]["km"], 1) for a, b in sorted(Y)},
               trusted_nodes=sorted(used), protected_substations=prot, mw_behind_qkd=round(sum(G.nodes[s]["mw"] for s in prot if s in G), 1),
               total_mw=round(sum(G.nodes[s]["mw"] for s in G), 1),
               routes={s: " > ".join([net.cc[0] if p[0][0][0] in net.cc else ""] and []) for s, p in net.last_paths.items()},
               backup=bk)
summary["routes"] = {s: [f"{a} - {b}" for a, b in p[0]] for s, p in net.last_paths.items()}
json.dump(summary, open(out_json, "w"), indent=1)
pos = nx.kamada_kawai_layout(G, weight="km")
fig, ax = plt.subplots(figsize=(13, 10))
feas = set(net.feasible)
for a, b in G.edges:
    e = tuple(sorted((a, b)))
    if e in Y: continue
    nx.draw_networkx_edges(G, pos, [(a, b)], edge_color="#4c6ef5", width=1, style="-" if e in feas else "--", alpha=0.7, ax=ax)
nx.draw_networkx_edges(G, pos, list(Y), edge_color="#e07a1f", width=4.5, ax=ax)
for b_ in bk["added"]:
    u, v = b_["link"].split(" - ")
    ax.plot(*zip(pos[u], pos[v]), color="#2f9e44", lw=2, ls=(0, (4, 2)))
colors = ["#111" if s in net.cc else "#e07a1f" if s in used else "#4a7c59" if s in prot else "#adb5bd" for s in G]
shapes = {"o": [s for s in G if s not in used], "s": [s for s in G if s in used]}
for m, nodes in shapes.items():
    nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_shape=m, node_color=[colors[list(G).index(s)] for s in nodes],
                           node_size=[110 + 2.2 * G.nodes[s]["mw"] for s in nodes], edgecolors="white", ax=ax)
lp = {s: (x, y + 0.025) for s, (x, y) in pos.items()}
nx.draw_networkx_labels(G, lp, {s: short(s) for s in G}, font_size=6.5, ax=ax)
nx.draw_networkx_labels(G, lp, {s: short(s) for s in net.cc}, font_size=8, font_weight="bold", ax=ax)
ax.legend(handles=[Line2D([], [], color="#e07a1f", lw=4.5, label=f"QKD + PQC ({len(Y)} links)"),
                   Line2D([], [], color="#4c6ef5", lw=1, label="PQC only"),
                   Line2D([], [], color="#4c6ef5", lw=1, ls="--", label="PQC only: too long for QKD (>10 dB)"),
                   Line2D([], [], color="#2f9e44", lw=2, ls=(0, (4, 2)), label=f"New backup route, PQC ({bk['backup_links']})"),
                   Line2D([], [], marker="o", ls="", color="#111", label="Control center", ms=9),
                   Line2D([], [], marker="s", ls="", color="#e07a1f", label=f"Trusted node ({len(used)})", ms=9),
                   Line2D([], [], marker="o", ls="", color="#4a7c59", label="QKD on every hop to a control center", ms=9),
                   Line2D([], [], marker="o", ls="", color="#adb5bd", label="PQC only (node size = MW load)", ms=9)],
          loc="lower left", fontsize=8.5, frameon=False)
ax.set_title(f"Chattanooga-area grid (ACTIVSg70k synthetic): PQC everywhere, QKD on {len(Y)} links, {bk['backup_links']} backup routes", fontsize=11)
ax.axis("off"); fig.tight_layout(); fig.savefig(out_png, dpi=170)
print(json.dumps({k: summary[k] for k in ("qkd_links", "qkd_link_km", "trusted_nodes", "protected_substations", "mw_behind_qkd", "total_mw")}, indent=1))
print("backup:", {k: bk[k] for k in ("bridges_before", "worst_cut_mw_before", "backup_links", "worst_cut_mw_after", "backup_km_total")}, bk["added"])
