"""Step 3 v0: hybrid QKD/PQC design on the Chattanooga-area synthetic grid (ACTIVSg70k subset)."""
import json, math, sys, networkx as nx
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
raw = json.load(open(sys.argv[1])); out = sys.argv[2]
diagram_path = sys.argv[3] if len(sys.argv) > 3 else f"{out}/network_diagram.png"
DB_PER_KM = 0.35          # EPB field test: 7.3 dB over 21.9 km (Evans et al. 2021)
MAX_LOSS_DB = 10.0        # assumption: QKD link loss budget for metro BB84 systems
QKD_BUDGET_LINKS = 8      # v0 budget: number of QKD links the utility can afford
MAX_HOPS = 3              # EPB tested a 3-hop trusted-node chain (Evans et al. 2021)
G = nx.Graph()
for (a, b), km, kv in raw["links"]:
    if G.has_edge(a, b): km = min(km, G[a][b]["km"])
    G.add_edge(a, b, km=km, kv=kv, loss=km * DB_PER_KM)
for s in G: G.nodes[s]["kv"] = raw["kv"].get(s, 0); G.nodes[s]["load"] = raw["load"].get(s, 0)
# control-center proxies: the two highest-voltage, most central substations (assumption, labeled)
bc = nx.betweenness_centrality(G, weight="km")
core = set(raw["core"])
cc1 = max([s for s in G if s in core], key=lambda s: (G.nodes[s]["kv"], bc[s]))
near = nx.single_source_shortest_path_length(G, cc1, cutoff=MAX_HOPS)
cc2 = max([s for s in near if s in core and s != cc1], key=lambda s: bc[s])
cc = [cc1, cc2]
# value tiers (v0): 4 = control center, 3 = >=161 kV, 2 = load >= 50 MW, 1 = other
def tier(s):
    if s in cc: return 4
    if G.nodes[s]["kv"] >= 161: return 3
    if G.nodes[s]["load"] >= 50: return 2
    return 1
for s in G: G.nodes[s]["tier"] = tier(s)
feasible = {tuple(sorted(e)) for e in G.edges if G.edges[e]["loss"] <= MAX_LOSS_DB}
F = G.edge_subgraph(feasible).copy()
# v0 rule: link the two control centers, then protect highest-tier substations by shortest feasible path,
# adding links until the budget is spent. Every link keeps hybrid PQC regardless.
qkd = set(); protected = {}
targets = [cc[1]] + sorted([s for s in G if s not in cc], key=lambda s: (-G.nodes[s]["tier"], -G.nodes[s]["load"]))
for t in targets:
    best = None
    for c in cc:
        if c == t or c not in F or t not in F or not nx.has_path(F, c, t): continue
        p = nx.shortest_path(F, c, t, weight=lambda u, v, d: 1 + d["km"] / 1000)  # fewest hops (fewest trusted nodes), then shortest
        if len(p) - 1 > MAX_HOPS: continue
        new = {tuple(sorted(e)) for e in zip(p, p[1:])} - qkd
        if best is None or len(new) < len(best[1]): best = (p, new)
    if best and len(qkd) + len(best[1]) <= QKD_BUDGET_LINKS:
        qkd |= best[1]; protected[t] = best[0]
# availability: node-disjoint paths from each substation to the control-center set
H = G.copy(); H.add_node("CCSET")
for c in cc: H.add_edge("CCSET", c)
avail = {s: nx.node_connectivity(H, s, "CCSET") for s in G if s not in cc}
weak = sorted(s for s, k in avail.items() if k < 2)
trusted = sorted({n for p in protected.values() for n in p[1:-1]})
summary = dict(substations=G.number_of_nodes(), links=G.number_of_edges(), control_centers=cc,
    link_km=dict(min=round(min(d["km"] for *_, d in G.edges(data=True)),1),
                 median=round(sorted(d["km"] for *_, d in G.edges(data=True))[G.number_of_edges()//2],1),
                 max=round(max(d["km"] for *_, d in G.edges(data=True)),1)),
    qkd_feasible_links=len(feasible), qkd_links=sorted(map(list, qkd)), qkd_protected={k: v for k, v in protected.items()},
    trusted_nodes=trusted, substations_with_lt2_disjoint_paths=weak,
    assumptions=dict(db_per_km=DB_PER_KM, max_loss_db=MAX_LOSS_DB, qkd_budget_links=QKD_BUDGET_LINKS, max_hops=MAX_HOPS,
        lengths="estimated from branch reactance at typical ohm/km per voltage", control_centers="proxy: CC1 = highest-kV, most central Chattanooga substation; CC2 (backup) = most central Chattanooga substation within 3 hops"))
json.dump(summary, open(f"{out}/v0_summary.json", "w"), indent=1)
# diagram (schematic layout weighted by length; not geographic)
pos = nx.kamada_kawai_layout(G, weight="km")
plt.figure(figsize=(13, 10))
col = {4: "#2b2d42", 3: "#8d5a97", 2: "#4a7c59", 1: "#9aa5b1"}
for (a, b, d) in G.edges(data=True):
    e = tuple(sorted((a, b)))
    if e in qkd: c, w, st = "#e07a1f", 3.5, "-"
    elif e in feasible: c, w, st = "#4c6ef5", 1.2, "-"
    else: c, w, st = "#4c6ef5", 1.2, "--"
    nx.draw_networkx_edges(G, pos, [(a, b)], edge_color=c, width=w, style=st)
nx.draw_networkx_nodes(G, pos, node_color=[col[G.nodes[s]["tier"]] for s in G],
    node_size=[420 if s in cc else 170 for s in G], edgecolors=["#e07a1f" if s in trusted else "white" for s in G], linewidths=2)
nx.draw_networkx_labels(G, pos, {s: s.replace("CHATTANOOGA", "CHA").title().replace("Cha", "CHA") for s in G}, font_size=6.5)
from matplotlib.lines import Line2D
leg = [Line2D([], [], color="#e07a1f", lw=3.5, label="QKD + PQC (chosen)"),
       Line2D([], [], color="#4c6ef5", lw=1.2, label="PQC (QKD-feasible)"),
       Line2D([], [], color="#4c6ef5", lw=1.2, ls="--", label="PQC (too long for QKD)"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#2b2d42", ms=11, label="Control-center proxy"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#8d5a97", ms=8, label="≥161 kV substation"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#4a7c59", ms=8, label="Load ≥50 MW"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#9aa5b1", markeredgecolor="#e07a1f", ms=8, label="Trusted node (orange ring)")]
plt.legend(handles=leg, loc="lower left", fontsize=8, frameon=False)
plt.title("Step 3 v0: hybrid QKD/PQC design, Chattanooga-area synthetic grid (ACTIVSg70k subset, 49 substations)", fontsize=10)
plt.axis("off"); plt.tight_layout(); plt.savefig(diagram_path, dpi=170)
print(json.dumps({k: v for k, v in summary.items() if k != "qkd_protected"}, indent=1)); print("protected:", {k: len(v)-1 for k, v in protected.items()})
