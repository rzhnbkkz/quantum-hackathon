"""Run version 1 on one network: budget sweep for every method, SMAA robustness, map and charts.
Usage: python v1_run.py chatt_raw.json OUTDIR [budget_dollars]"""
import sys, json
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from v1_model import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

net, out = sys.argv[1], sys.argv[2]
B_DESIGN = int(sys.argv[3]) if len(sys.argv) > 3 else 1_200_000
G, raw = load_network(net); cc = control_centers(G, set(raw["core"])); P = Problem(G, cc)

# 1. budget sweep, every method scored with the same evaluation
step = P.p["C_qkd"]; rows = []
for k in range(0, 31):
    B = k * step
    o, g, b, r = P.solve(B), P.greedy(B), P.busiest_first(B), P.random_links(B, trials=20)
    v0 = 0.0
    for n in range(40):
        ev = P.evaluate(v0_links(G, cc, budget_links=n))
        if ev["cost"] <= B: v0 = ev["value"]
    rows.append(dict(budget=B, optimal=o["value"], greedy=g["value"], v0_rule=v0, busiest_first=b["value"],
                     random=r["value"], optimal_mw=o["mw"], optimal_links=len(o["links"]), optimal_trusted=len(o["trusted_nodes"])))
top = max(r["optimal"] for r in rows)

# 2. the design at the chosen budget, and SMAA robustness
design = P.solve(B_DESIGN)
freq = smaa(G, cc, B_DESIGN, samples=400)
summary = dict(network=net, control_centers=cc, parameters=P.p, parameter_ranges=RANGES, design_budget=B_DESIGN,
    design=dict(links=[f"{a} - {b}" for a, b in design["links"]], cost=design["cost"], value=round(design["value"], 2),
                share_of_max_value=round(design["value"] / top, 3), mw_behind_qkd=round(design["mw"], 1),
                trusted_nodes=design["trusted_nodes"], control_centers_linked=design["cc_linked"],
                protected={s: " > ".join(p) for s, p in design["protected"].items()}),
    max_value=round(top, 2),
    max_gap_vs_optimal=dict(greedy=round(max((r["optimal"] - r["greedy"]) / r["optimal"] for r in rows if r["optimal"]), 3),
                            v0_rule=round(max((r["optimal"] - r["v0_rule"]) / r["optimal"] for r in rows if r["optimal"]), 3)),
    smaa_link_frequency=freq, sweep=rows)
json.dump(summary, open(f"{out}/v1_summary.json", "w"), indent=1)

# chart 1: budget curves
plt.figure(figsize=(7.5, 4.5))
st = dict(optimal=("Optimal (integer program)", "-", "o", "#e07a1f"), greedy=("Greedy, best value per unit of budget", "--", None, "#2b2d42"),
          v0_rule=("Version 0 rule", "-", "s", "#8d5a97"), busiest_first=("Busiest links first", "-", "^", "#4c6ef5"),
          random=("Random links", ":", None, "#9aa5b1"))
U = P.p["C_qkd"]          # budget unit: one QKD link (a trusted node counts as C_tn / C_qkd of a link)
x = [r["budget"] / U for r in rows]
for k, (lab, ls, mk, c) in st.items():
    plt.plot(x, [100 * r[k] / top for r in rows], ls=ls, marker=mk, ms=4, color=c, label=lab)
plt.axvline(B_DESIGN / U, color="gray", ls=":"); plt.text(B_DESIGN / U + 0.3, 45, "design budget", fontsize=8, color="gray")
plt.xlabel(f"QKD budget, in links (a trusted node counts as {P.p['C_tn'] / P.p['C_qkd']:.1f} link)"); plt.ylabel("risk reduced (% of the most achievable)")
plt.title("Risk reduced vs. budget, Chattanooga-area grid", fontsize=10); plt.legend(fontsize=8, loc="lower right")
plt.tight_layout(); plt.savefig(f"{out}/v1_budget_curves.png", dpi=150); plt.close()

# chart 2: SMAA link frequency
items = list(freq.items())[:12]
plt.figure(figsize=(7.5, 4))
plt.barh([k for k, _ in items][::-1], [100 * v for _, v in items][::-1], color="#e07a1f")
plt.xlabel("% of 400 parameter draws in which the link gets QKD"); plt.xlim(0, 100)
plt.title(f"Robustness (SMAA) at a budget of {B_DESIGN / P.p['C_qkd']:.0f} links", fontsize=10); plt.tight_layout()
plt.savefig(f"{out}/v1_smaa.png", dpi=150); plt.close()

# chart 3: map, QKD links shaded by how often SMAA picks them
pos = nx.kamada_kawai_layout(G, weight="km")
plt.figure(figsize=(13, 10))
fq = {tuple(sorted(k.split(" - "))): v for k, v in freq.items()}
feas = set(P.feasible)
for a, b in G.edges:
    e = tuple(sorted((a, b))); f = fq.get(e, 0)
    if f > 0: nx.draw_networkx_edges(G, pos, [(a, b)], edge_color="#e07a1f", width=1 + 4 * f, alpha=0.35 + 0.65 * f)
    else: nx.draw_networkx_edges(G, pos, [(a, b)], edge_color="#4c6ef5", width=1, style="-" if e in feas else "--")
tn = set(design["trusted_nodes"]); prot = set(design["protected"])
nx.draw_networkx_nodes(G, pos, node_color=["#2b2d42" if s in cc else "#4a7c59" if s in prot else "#9aa5b1" for s in G],
    node_size=[420 if s in cc else 60 + 2.2 * G.nodes[s]["load"] for s in G],
    edgecolors=["#e07a1f" if s in tn else "white" for s in G], linewidths=2)
nx.draw_networkx_labels(G, pos, {s: s.replace("CHATTANOOGA", "CHA").title().replace("Cha", "CHA") for s in G}, font_size=6.5)
leg = [Line2D([], [], color="#e07a1f", lw=5, label="QKD, chosen in nearly every draw"),
       Line2D([], [], color="#e07a1f", lw=2, alpha=.5, label="QKD, chosen in some draws"),
       Line2D([], [], color="#4c6ef5", lw=1, label="PQC only"), Line2D([], [], color="#4c6ef5", lw=1, ls="--", label="PQC only (too long for QKD)"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#2b2d42", ms=11, label="Control-center proxy"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#4a7c59", ms=8, label="QKD on every hop (size = MW)"),
       Line2D([], [], marker="o", color="w", markerfacecolor="#9aa5b1", markeredgecolor="#e07a1f", ms=8, label="Trusted node")]
plt.legend(handles=leg, loc="lower left", fontsize=8, frameon=False)
plt.title(f"Version 1 design at a budget of {B_DESIGN / P.p['C_qkd']:.0f} links: optimal QKD placement, shaded by robustness", fontsize=10)
plt.axis("off"); plt.tight_layout(); plt.savefig(f"{out}/v1_network_map.png", dpi=170); plt.close()
print(json.dumps({k: v for k, v in summary.items() if k not in ("sweep", "parameters", "parameter_ranges")}, indent=1))
