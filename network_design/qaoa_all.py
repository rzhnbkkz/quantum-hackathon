"""QAOA vs greedy vs random on every grid network. Instance size kept to 10-14 qubits (M grown until it fits)."""
import sys, json, glob, os, time
sys.path.insert(0, "tools")
from qaoa_study import *

def vals_all(inst):
    nq = inst["nq"]; idx = np.arange(2 ** nq); bits = (idx[:, None] >> np.arange(nq)) & 1
    val = np.zeros(2 ** nq)
    for _, q, v in inst["terms"]: val += v * np.all(bits[:, q] == 1, axis=1)
    return val, bits.sum(1)

def stats(P, val, w, K, opt, shots=1000, seed=1):
    P = P / P.sum(); feas = w == K; isopt = feas & (np.abs(val - opt) < 1e-9)
    idx = np.random.default_rng(seed).choice(len(P), size=shots, p=P)
    best = max([val[i] for i in idx if feas[i]], default=0)
    return dict(p_opt=float(P[isopt].sum()), p_feas=float(P[feas].sum()), best_ratio=float(best / opt))

out = {}
for path in sorted(glob.glob("griddata/regions/*.json")):
    name = os.path.basename(path)[:-5]; inst = None
    for M in range(3, 15):
        try: c = build_instance(path, M=M, K=1)
        except Exception as e: break
        if c["nq"] > 14: break
        inst = c
    if inst is None or inst["nq"] < 6: print(name, "skip (too few candidate links within 3 hops / 10 dB)", flush=True); continue
    inst["K"] = K = inst["nq"] // 2
    t = time.time(); val, w = vals_all(inst); opt = val[w == K].max(); g, _ = greedy(inst)
    rf = stats((w == K).astype(float), val, w, K, opt)
    row = dict(nq=inst["nq"], K=K, targets=len(inst["terms"]), greedy_ratio=g / opt, random_feasible=rf)
    for reps in (1, 2):
        row[f"std_p{reps}"] = stats(run_qaoa(inst, reps=reps, starts=4)["probs"], val, w, K, opt)
        row[f"xy_p{reps}"] = stats(run_qaoa_xy(inst, reps=reps, starts=4)["probs"], val, w, K, opt)
    out[name] = row
    f = lambda k: row[k]["p_opt"] / rf["p_opt"]
    print(f"{name:15s} {inst['nq']:2d}q K={K} greedy {row['greedy_ratio']:.2f} | P(opt) vs random-feasible: "
          f"std p1 {f('std_p1'):.2f}x p2 {f('std_p2'):.2f}x | XY p1 {f('xy_p1'):.2f}x p2 {f('xy_p2'):.2f}x  ({time.time()-t:.0f}s)", flush=True)
    os.makedirs("qaoa_all", exist_ok=True); json.dump(out, open("qaoa_all/qaoa_all.json", "w"), indent=1)
print("DONE", flush=True)
