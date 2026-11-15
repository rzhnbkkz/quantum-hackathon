"""Quantify the Step 3 v0 design: network structure, coverage, key rates, sensitivity, gaps."""
import json, sys, math, statistics as st, networkx as nx
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
raw = json.load(open(sys.argv[1])); s0 = json.load(open(sys.argv[2])); out = sys.argv[3]
DB = 0.35
G = nx.Graph()
for (a, b), km, kv in raw["links"]:
    if G.has_edge(a, b): km = min(km, G[a][b]["km"])
    G.add_edge(a, b, km=km, kv=kv)
load = {s: raw["load"].get(s, 0) for s in G}; kv = {s: raw["kv"].get(s, 0) for s in G}
cc = s0["control_centers"]; R = {}
km = sorted(d["km"] for *_, d in G.edges(data=True))
R["network"] = dict(substations=G.number_of_nodes(), links=G.number_of_edges(),
    independent_loops=G.number_of_edges() - G.number_of_nodes() + nx.number_connected_components(G),
    total_fiber_km=round(sum(km), 1), km_quartiles=[round(x, 1) for x in st.quantiles(km, n=4)],
    degree_one_substations=sum(1 for n in G if G.degree(n) == 1),
    mean_degree=round(2 * G.number_of_edges() / G.number_of_nodes(), 2),
    diameter_hops=nx.diameter(G), total_load_mw=round(sum(load.values()), 1),
    voltage_levels_kv=sorted({int(v) for v in kv.values()}))
infeasible = sorted([(round(d["km"], 1), a, b) for a, b, d in G.edges(data=True) if d["km"] * DB > 10], reverse=True)
R["feasibility"] = dict(feasible=s0["qkd_feasible_links"], infeasible=[f"{a} - {b} ({k} km, {k*DB:.1f} dB)" for k, a, b in infeasible])
# key-rate model: R = R0 * 10^(-loss/10), R0 from EPB's two reported links (A-B 3.1 dB -> 1310 bps; B-C 2.9 dB -> 1892 bps)
R0s = [1310 / 10 ** (-0.31), 1892 / 10 ** (-0.29)]; R0 = sum(R0s) / 2
q = [tuple(sorted(e)) for e in s0["qkd_links"]]
links = []
for a, b in q:
    d = G[a][b]["km"]; L = d * DB
    links.append(dict(link=f"{a} - {b}", km=round(d, 1), loss_db=round(L, 2), est_key_rate_bps=round(R0 * 10 ** (-L / 10))))
R["qkd_links"] = sorted(links, key=lambda x: -x["km"])
R["key_rate_model"] = dict(R0_bps_range=[round(x) for x in R0s], R0_used=round(R0),
    aes256_rekey_every_60s_bps=round(256 / 60, 1),
    note="EPB's 3-hop network delivered 115 bps end to end vs ~1300-1900 bps per hop: relaying overhead about 10x")
prot = s0["qkd_protected"]
sub_nodes = [n for n in G if n not in cc]
prot_subs = [n for n in prot if n not in cc]
R["coverage"] = dict(substations_protected=f"{len(prot_subs)} of {len(sub_nodes)}",
    load_protected_mw=round(sum(load[n] for n in prot_subs), 1),
    load_share=round(sum(load[n] for n in prot_subs) / max(1e-9, sum(load[n] for n in sub_nodes)), 3),
    control_center_link=" > ".join(prot.get(cc[1], [])),
    hops=dict(sorted({k: sum(1 for p in prot.values() if len(p) - 1 == k) for k in (1, 2, 3)}.items())),
    trusted_nodes=s0["trusted_nodes"], qkd_fiber_km=round(sum(x["km"] for x in links), 1))
weak = s0["substations_with_lt2_disjoint_paths"]
R["availability"] = dict(single_path_substations=len(weak), their_load_mw=round(sum(load[n] for n in weak), 1),
    detail=[f"{n} ({load[n]:.0f} MW, degree {G.degree(n)})" for n in weak])
# what the v0 tier rule picked vs ranked by MW
tierpick = sorted(prot_subs, key=lambda n: -load[n])
top_mw = sorted(sub_nodes, key=lambda n: -load[n])[:len(prot_subs)]
R["rule_check"] = dict(v0_protected_by_mw=[f"{n} {load[n]:.0f} MW" for n in tierpick],
    top_substations_by_mw=[f"{n} {load[n]:.0f} MW" for n in top_mw],
    overlap=len(set(tierpick) & set(top_mw)))
json.dump(R, open(f"{out}/v0_results.json", "w"), indent=1)
# figure 1: link length histogram with QKD limit
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].hist(km, bins=list(range(0, 90, 5)), color="#4c6ef5", edgecolor="white")
ax[0].axvline(10 / DB, color="tab:red", ls="--", label=f"QKD limit ({10/DB:.0f} km at 10 dB)")
ax[0].axvspan(3.4, 10.2, color="orange", alpha=.2, label="EPB field-test links (3.4-10.2 km)")
ax[0].set_xlabel("estimated link length (km)"); ax[0].set_ylabel("links"); ax[0].legend(fontsize=8)
ax[0].set_title("65 links, Chattanooga-area grid")
# figure 2: estimated key rate vs distance
d = [x / 10 for x in range(0, 400)]
ax[1].semilogy(d, [R0 * 10 ** (-x * DB / 10) for x in d], label="model R0·10^(-αd/10)")
ax[1].scatter([10.2, 8.3], [1310, 1892], color="tab:orange", zorder=3, label="EPB measured")
ax[1].scatter([x["km"] for x in links], [x["est_key_rate_bps"] for x in links], color="#e07a1f", marker="s", s=18, label="v0 QKD links")
ax[1].axhline(256 / 60, color="gray", ls=":", label="AES-256 rekey every 60 s")
ax[1].set_xlabel("link length (km)"); ax[1].set_ylabel("secret key rate (bps)"); ax[1].legend(fontsize=8)
ax[1].set_title("Estimated key rate (single-hop, before relay overhead)")
plt.tight_layout(); plt.savefig(f"{out}/v0_links_keyrate.png", dpi=150)
print(json.dumps(R, indent=1))
