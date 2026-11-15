"""Sobol screening: which candidate parameters change the QKD placement decision?
Usage: python sobol_screen.py chatt_raw.json OUTDIR [N] [budget]
Outputs are the decision itself (one 0/1 output per link: does it get QKD?), plus summary outputs.
Decision indices are aggregated over links, weighted by each link's variance (Gamboa et al. 2014)."""
import sys, json, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np
from multiprocessing import Pool
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze
from v1_model import load_network, control_centers, Problem

NET, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
BUDGET = int(sys.argv[4]) if len(sys.argv) > 4 else 1_200_000
SPACE = {  # every candidate parameter, with a range wide enough to include "this factor is irrelevant"
    "db_per_km":   (0.20, 0.45, "fiber loss per km: 0.2 = good buried fiber, 0.35 = EPB aerial (measured)"),
    "max_loss_db": (6.0, 15.0, "loss a QKD link can tolerate"),
    "max_hops":    (1.0, 4.999, "longest trusted-node chain (rounded down to 1-4)"),
    "lam":         (0.002, 0.03, "tap rate per km of route"),
    "beta":        (0.0, 1.0, "how exposure grows with route length (0 = length irrelevant)"),
    "D":           (0.5, 0.98, "chance the BB84 alarm catches a tap"),
    "q":           (0.0, 0.2, "chance a trusted node is compromised"),
    "gamma":       (0.0, 1.0, "how consequence grows with MW (0 = all substations equal)"),
    "cc_weight":   (0.0, 1.0, "control-center link value, as a share of system load"),
    "C_qkd":       (100_000, 200_000, "cost per QKD link ($)"),
    "C_tn":        (0, 60_000, "cost per trusted node ($)"),
}
NAMES = list(SPACE)
PROBLEM = {"num_vars": len(NAMES), "names": NAMES, "bounds": [[SPACE[k][0], SPACE[k][1]] for k in NAMES]}
G, RAW = load_network(NET); CC = control_centers(G, set(RAW["core"]))
EDGES = sorted(tuple(sorted(e)) for e in G.edges)

def run(x):
    prm = dict(zip(NAMES, x))
    P = Problem(G, CC, **prm)
    ev = P.solve(BUDGET); full = P.everywhere()
    chosen = set(ev["links"])
    return [1.0 if e in chosen else 0.0 for e in EDGES] + [
        float(len(ev["links"])), float(len(ev["trusted_nodes"])), float(ev["cc_linked"]),
        ev["mw"], ev["value"] / full["value"] if full["value"] > 0 else 0.0]

if __name__ == "__main__":
    X = sobol_sample.sample(PROBLEM, N, calc_second_order=False, seed=7)
    t = time.time()
    with Pool(2) as pool: Y = np.array(pool.map(run, X, chunksize=64))
    print(f"{len(X)} runs in {time.time() - t:.0f} s")
    nE = len(EDGES)
    # decision indices: aggregate per-link first-order and total indices, weighted by each link's variance
    num1, numT, den, per_link = np.zeros(len(NAMES)), np.zeros(len(NAMES)), 0.0, {}
    for j in range(nE):
        y = Y[:, j]; v = y.var()
        if v < 1e-9: continue
        r = sobol_analyze.analyze(PROBLEM, y, calc_second_order=False, seed=7)
        num1 += v * np.nan_to_num(r["S1"]); numT += v * np.nan_to_num(r["ST"]); den += v
        per_link[f"{EDGES[j][0]} - {EDGES[j][1]}"] = dict(chosen_share=round(float(y.mean()), 3),
            ST={k: round(float(s), 3) for k, s in zip(NAMES, r["ST"])})
    decision = {k: dict(S1=round(float(a / den), 3), ST=round(float(b / den), 3), meaning=SPACE[k][2])
                for k, a, b in zip(NAMES, num1, numT)}
    scalars = {}
    for i, lab in enumerate(["qkd_links", "trusted_nodes", "control_centers_linked", "mw_protected", "share_of_max_value"]):
        y = Y[:, nE + i]
        if y.var() < 1e-12: scalars[lab] = "constant"; continue
        r = sobol_analyze.analyze(PROBLEM, y, calc_second_order=False, seed=7)
        scalars[lab] = {k: dict(S1=round(float(a), 3), ST=round(float(b), 3), ST_conf=round(float(c), 3))
                        for k, a, b, c in zip(NAMES, r["S1"], r["ST"], r["ST_conf"])}
    res = dict(network=NET, budget=BUDGET, N=N, runs=len(X), ranges={k: SPACE[k][:2] for k in NAMES},
               decision_indices=dict(sorted(decision.items(), key=lambda kv: -kv[1]["ST"])),
               output_indices=scalars, links_that_vary=len(per_link), per_link=per_link)
    json.dump(res, open(f"{OUT}/sobol_results.json", "w"), indent=1)
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    order = sorted(NAMES, key=lambda k: decision[k]["ST"])
    plt.figure(figsize=(7.5, 4.6))
    yy = np.arange(len(order))
    plt.barh(yy + 0.2, [decision[k]["ST"] for k in order], 0.4, color="#e07a1f", label="total effect (ST, with interactions)")
    plt.barh(yy - 0.2, [decision[k]["S1"] for k in order], 0.4, color="#4c6ef5", label="alone (S1)")
    plt.yticks(yy, order); plt.xlabel("share of variation in which links get QKD")
    plt.title(f"Sobol sensitivity of the QKD placement decision (${BUDGET/1e6:.1f}M budget, {len(X):,} runs)", fontsize=9.5)
    plt.legend(fontsize=8, loc="lower right"); plt.tight_layout(); plt.savefig(f"{OUT}/sobol_decision.png", dpi=150)
    for k in sorted(NAMES, key=lambda k: -decision[k]["ST"]):
        print(f"{k:12s} ST {decision[k]['ST']:.3f}  S1 {decision[k]['S1']:.3f}   {SPACE[k][2]}")
