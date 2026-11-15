import json, sys, networkx as nx
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
raw = json.load(open(sys.argv[1])); out = sys.argv[2]; DB = 0.35
G = nx.Graph()
for (a, b), km, kv in raw["links"]:
    if G.has_edge(a, b): km = min(km, G[a][b]["km"])
    G.add_edge(a, b, km=km)
load = {s: raw["load"].get(s, 0) for s in G}; kv = {s: raw["kv"].get(s, 0) for s in G}
bc = nx.betweenness_centrality(G, weight="km"); core = set(raw["core"])
def v0(budget=8, max_loss=10.0, hops=3):
    cc1 = max([s for s in G if s in core], key=lambda s: (kv[s], bc[s]))
    near = nx.single_source_shortest_path_length(G, cc1, cutoff=3)
    cc2 = max([s for s in near if s in core and s != cc1], key=lambda s: bc[s]); cc = [cc1, cc2]
    tier = lambda s: 4 if s in cc else 3 if kv[s] >= 161 else 2 if load[s] >= 50 else 1
    F = G.edge_subgraph([e for e in G.edges if G.edges[e]["km"] * DB <= max_loss]).copy()
    qkd, prot = set(), {}
    for t in [cc2] + sorted([s for s in G if s not in cc], key=lambda s: (-tier(s), -load[s])):
        best = None
        for c in cc:
            if c == t or c not in F or t not in F or not nx.has_path(F, c, t): continue
            p = nx.shortest_path(F, c, t, weight=lambda u, v, d: 1 + d["km"] / 1000)
            if len(p) - 1 > hops: continue
            new = {tuple(sorted(e)) for e in zip(p, p[1:])} - qkd
            if best is None or len(new) < len(best[1]): best = (p, new)
        if best and len(qkd) + len(best[1]) <= budget: qkd |= best[1]; prot[t] = best[0]
    subs = [s for s in prot if s not in cc]
    tn = {n for p in prot.values() for n in p[1:-1]}
    feas = sum(1 for e in G.edges if G.edges[e]["km"] * DB <= max_loss)
    return dict(links=len(qkd), subs=len(subs), mw=round(sum(load[s] for s in subs), 1), tn=len(tn), feasible=feas, cc_linked=cc2 in prot)
R = {"budget": {b: v0(budget=b) for b in range(0, 41, 2)},
     "loss_limit_db": {L: v0(max_loss=L) for L in (3, 5, 7.5, 10, 15, 20)},
     "max_hops": {h: v0(hops=h) for h in (1, 2, 3, 4, 5)}}
json.dump(R, open(f"{out}/v0_sensitivity.json", "w"), indent=1)
for k, v in R.items():
    print("==", k)
    for x, r in v.items(): print(f"  {x}: {r}")
B = sorted(R["budget"]); tot = sum(load[s] for s in G) 
fig, ax = plt.subplots(figsize=(6.5, 4))
ax.plot(B, [R["budget"][b]["mw"] for b in B], "o-", label="load behind full-QKD paths (MW)")
ax2 = ax.twinx(); ax2.plot(B, [R["budget"][b]["tn"] for b in B], "s--", color="tab:red", label="trusted nodes")
ax.set_xlabel("QKD budget (links)"); ax.set_ylabel("MW protected"); ax2.set_ylabel("trusted nodes", color="tab:red")
ax.axvline(8, color="gray", ls=":"); ax.text(8.3, ax.get_ylim()[1]*0.05, "v0 budget", fontsize=8, color="gray")
ax.set_title("v0 rule: protection vs QKD budget (Chattanooga-area grid)", fontsize=10)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1+h2, l1+l2, fontsize=8, loc="upper left")
plt.tight_layout(); plt.savefig(f"{out}/v0_budget_curve.png", dpi=150)
