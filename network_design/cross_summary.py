"""Rebuild the cross-network QAOA and Sobol tables (rerun when more Sobol cities finish)."""
import json, glob, os, numpy as np
Q = json.load(open("qaoa_all/qaoa_all.json"))
r = lambda row, k: row[k]["p_opt"] / row["random_feasible"]["p_opt"]
L = ["# QAOA vs classical on every network", "",
     "Instance: one qubit per candidate link on the top substations' paths, sized to 6-14 qubits, budget K = half the links. Exact optimum by brute force (MILP gives the same).",
     "Numbers = chance of sampling the optimal plan, relative to picking a random plan with exactly K links (1.0x = no better than random).", "",
     "| Network | Qubits | Greedy (fraction of optimum) | Penalty QAOA p=1 / p=2 | XY-mixer QAOA p=1 / p=2 |", "|---|---|---|---|---|"]
for n, row in Q.items():
    L.append(f"| {n} | {row['nq']} | {row['greedy_ratio']:.2f} | {r(row,'std_p1'):.2f}x / {r(row,'std_p2'):.2f}x | {r(row,'xy_p1'):.2f}x / {r(row,'xy_p2'):.2f}x |")
xy = [max(r(v, 'xy_p1'), r(v, 'xy_p2')) for v in Q.values()]
L += ["", f"- {len(Q)} networks. Penalty QAOA did worse than random on all of them (median {np.median([r(v,'std_p2') for v in Q.values()]):.2f}x): most of its probability lands on plans that break the budget.",
      f"- XY-mixer QAOA beat random on {sum(x > 1 for x in xy)}/{len(Q)} (median best {np.median(xy):.1f}x), but it never reached certainty. Exact MILP finds the optimum every time in under a second, and greedy reaches ≥ 0.90 of the optimum on {sum(v['greedy_ratio'] >= .9 for v in Q.values())}/{len(Q)}.",
      "- Conclusion: at this size the planning step stays classical. QAOA is a research benchmark here, not the tool."]
open("qaoa_all/summary.md", "w").write("\n".join(L))
S = {"chattanooga": "sobol/sobol_results.json", **{os.path.basename(os.path.dirname(f)): f for f in glob.glob("sobol_multi/*/sobol_results.json")}}
params = list(json.load(open(S["chattanooga"]))["decision_indices"])
M = ["# Sobol total-effect index (ST) by city", "", "Higher ST = changing that parameter changes which links get QKD more (including interactions).", "",
     "| Parameter | " + " | ".join(S) + " |", "|---|" + "---|" * len(S)]
D = {c: json.load(open(f))["decision_indices"] for c, f in S.items()}
for p in params: M.append(f"| {p} | " + " | ".join(f"{D[c].get(p, {}).get('ST', float('nan')):.2f}" for c in S) + " |")
tops = {c: max(D[c], key=lambda p: D[c][p]["ST"]) for c in S}
M += ["", "Top parameter per city: " + ", ".join(f"{c} = {t}" for c, t in tops.items())]
open("sobol_multi/summary.md", "w").write("\n".join(M)); print("\n".join(L)); print(); print("\n".join(M))
