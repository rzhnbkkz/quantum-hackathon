"""QAOA vs. classical methods on a small QKD-placement instance (the README's Step 3 stretch goal).

Instance (simplified so it fits on a few qubits):
  - candidate links: the links on one designated path (fewest hops) for each of the top-M substations by value
  - one qubit per candidate link: y_e = 1 means the link gets QKD
  - value = sum over substations of v_s * product of y_e over its path (it counts only if every hop has QKD)
  - budget: exactly K links, enforced by the penalty lam * (sum y - K)^2
  - simplifications vs. the full model: one path per substation, no trusted-node cap, no control-center rule
The cost is a polynomial in y (degree = longest path), turned into a Pauli-Z Hamiltonian with y = (1 - Z)/2."""
import sys, itertools, math
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.circuit.library import QAOAAnsatz
from qiskit import transpile
from v11 import Net


def build_instance(path, M=9, K=5, H=3):
    n = Net(path, H=H)
    targets = [s for s in sorted(n.paths, key=lambda s: -n.value.get(s, 0)) if s != n.cc[1]][:M]
    terms, links = [], []
    for s in targets:
        e, r = min(n.paths[s], key=lambda p: (len(p[0]), len(p[1])))
        E = [n.feasible[i] for i in e]
        for x in E:
            if x not in links: links.append(x)
        terms.append((s, [links.index(x) for x in E], n.value[s]))
    vmax = max(v for *_, v in terms)
    terms = [(s, q, v / vmax) for s, q, v in terms]       # scale values to [0, 1]
    return dict(net=n.name, links=links, terms=terms, K=K, nq=len(links))


def value(inst, bits):
    return sum(v for _, q, v in inst["terms"] if all(bits[i] for i in q))


def feasible(inst, bits): return sum(bits) == inst["K"]


def brute_force(inst):
    best, arg = -1, None
    for c in itertools.combinations(range(inst["nq"]), inst["K"]):
        b = [0] * inst["nq"]
        for i in c: b[i] = 1
        v = value(inst, b)
        if v > best: best, arg = v, b
    return best, arg


def greedy(inst):
    b = [0] * inst["nq"]
    while sum(b) < inst["K"]:
        best = None
        for i in range(inst["nq"]):
            if b[i]: continue
            for j in [None] + [k for k in range(inst["nq"]) if not b[k] and k != i]:     # allow adding a pair to complete a path
                c = b.copy(); c[i] = 1
                if j is not None:
                    if sum(c) + 1 > inst["K"]: continue
                    c[j] = 1
                gain = (value(inst, c) - value(inst, b)) / (sum(c) - sum(b))
                if best is None or gain > best[0]: best = (gain, c)
        b = best[1]
    return value(inst, b), b


def hamiltonian(inst, lam=None):
    """Cost to MINIMIZE: -value + lam*(sum y - K)^2, as a Pauli-Z polynomial."""
    nq, K = inst["nq"], inst["K"]
    lam = lam if lam is not None else 1.5 * sum(v for *_, v in inst["terms"])
    poly = {}                                         # frozenset(qubits) -> coefficient, over y variables
    def add(S, c): S = frozenset(S); poly[S] = poly.get(S, 0) + c
    for _, q, v in inst["terms"]: add(q, -v)
    add([], lam * K * K)                               # (sum y - K)^2 = sum y_i + 2 sum_{i<j} y_i y_j - 2K sum y_i + K^2
    for i in range(nq): add([i], lam * (1 - 2 * K))
    for i, j in itertools.combinations(range(nq), 2): add([i, j], 2 * lam)
    pauli = {}                                        # y_i = (1 - Z_i)/2  ->  product over S expands into Z-subsets
    for S, c in poly.items():
        S = sorted(S)
        for r in range(len(S) + 1):
            for sub in itertools.combinations(S, r):
                key = frozenset(sub); pauli[key] = pauli.get(key, 0) + c * (-1) ** r / 2 ** len(S)
    labels, coefs = [], []
    for S, c in pauli.items():
        if abs(c) < 1e-12 or not S: continue
        s = ["I"] * nq
        for i in S: s[nq - 1 - i] = "Z"                # qiskit: rightmost character = qubit 0
        labels.append("".join(s)); coefs.append(c)
    return SparsePauliOp(labels, coefs), lam


def bits_of(index, nq): return [(index >> i) & 1 for i in range(nq)]   # qubit i = bit i


def cost_diagonal(inst, op=None):
    """Energy of every bitstring (index i has qubit k = bit k), straight from the polynomial: same as the Hamiltonian's diagonal."""
    nq, K = inst["nq"], inst["K"]; lam = hamiltonian(inst)[1]
    idx = np.arange(2 ** nq); bits = (idx[:, None] >> np.arange(nq)) & 1
    val = np.zeros(2 ** nq)
    for _, q, v in inst["terms"]: val += v * np.all(bits[:, q] == 1, axis=1)
    return -val + lam * (bits.sum(1) - K) ** 2


def qaoa_probs(diag, gammas, betas, nq):
    """Exact QAOA state: start in |+...+>, then per layer apply exp(-i*gamma*C) and exp(-i*beta*sum X)."""
    psi = np.full(2 ** nq, 1 / np.sqrt(2 ** nq), dtype=complex)
    for g, b in zip(gammas, betas):
        psi = psi * np.exp(-1j * g * diag)
        c, sn = np.cos(b), -1j * np.sin(b)
        for k in range(nq):
            psi = psi.reshape(-1, 2, 2 ** k)
            psi = np.stack([c * psi[:, 0] + sn * psi[:, 1], sn * psi[:, 0] + c * psi[:, 1]], axis=1).reshape(-1)
    return np.abs(psi) ** 2


def run_qaoa(inst, reps=1, starts=10, seed=0):
    op, lam = hamiltonian(inst); diag = cost_diagonal(inst)
    scale = np.max(np.abs(diag)); d = diag / scale                       # normalize so gamma ranges are comparable
    rng = np.random.default_rng(seed); nq = inst["nq"]
    f = lambda x: float(np.dot(qaoa_probs(d, x[:reps], x[reps:], nq), d))
    best = None
    for _ in range(starts):
        x0 = np.concatenate([rng.uniform(0, 2 * np.pi, reps), rng.uniform(0, np.pi, reps)])
        r = minimize(f, x0, method="COBYLA", options={"maxiter": 500})
        if best is None or r.fun < best.fun: best = r
    gammas, betas = best.x[:reps] / scale, best.x[reps:]                 # gamma in units of the unnormalized Hamiltonian
    probs = qaoa_probs(diag, gammas, betas, nq)
    ans = QAOAAnsatz(op, reps=reps)
    vals = {p.name: v for p, v in zip(sorted(ans.parameters, key=lambda p: p.name), list(betas) + list(gammas))}
    circ = ans.assign_parameters(vals)
    t = transpile(circ, basis_gates=["cx", "rz", "sx", "x"], optimization_level=1)
    return dict(gammas=gammas, betas=betas, probs=probs, two_qubit_gates=t.count_ops().get("cx", 0), depth=t.depth(), circuit=circ)


def summarize(inst, probs, opt, shots=1000, seed=1):
    """Sample like hardware would: `shots` bitstrings; report best found and chance of sampling the optimum."""
    nq = inst["nq"]; rng = np.random.default_rng(seed)
    idx = rng.choice(len(probs), size=shots, p=probs / probs.sum())
    vals = [value(inst, bits_of(i, nq)) if sum(bits_of(i, nq)) == inst["K"] else -1 for i in idx]
    P = probs / probs.sum()
    p_opt = sum(p for i, p in enumerate(P) if sum(bits_of(i, nq)) == inst["K"] and abs(value(inst, bits_of(i, nq)) - opt) < 1e-9)
    p_feas = sum(p for i, p in enumerate(P) if sum(bits_of(i, nq)) == inst["K"])
    return dict(best_found_ratio=max(vals) / opt, p_optimal=p_opt, p_feasible=p_feas)


def random_baseline(inst, opt, shots=1000, seed=1):
    nq = inst["nq"]; p = np.ones(2 ** nq) / 2 ** nq
    return summarize(inst, p, opt, shots, seed)


def qaoa_xy_probs(val, gammas, betas, nq, K):
    """Constraint-preserving QAOA: start in the equal superposition of all exactly-K strings (Dicke state);
    mixer = ring of XY gates exp(-i*beta*(XX+YY)/2), which only swaps 01 <-> 10 and so keeps K links on. Cost = -value."""
    idx = np.arange(2 ** nq); w = np.array([bin(i).count("1") for i in idx])
    psi = np.where(w == K, 1.0, 0.0).astype(complex); psi /= np.linalg.norm(psi)
    pairs = [(k, (k + 1) % nq) for k in range(nq)]
    for g, b in zip(gammas, betas):
        psi = psi * np.exp(1j * g * val)                         # minimize -value  <=>  phase exp(+i*g*value)
        for (a, c) in pairs:
            ba, bc = (idx >> a) & 1, (idx >> c) & 1
            src = np.flatnonzero((ba == 0) & (bc == 1)); dst = src ^ ((1 << a) | (1 << c))
            p01, p10 = psi[src].copy(), psi[dst].copy()
            psi[src] = np.cos(b) * p01 - 1j * np.sin(b) * p10
            psi[dst] = np.cos(b) * p10 - 1j * np.sin(b) * p01
    return np.abs(psi) ** 2


def run_qaoa_xy(inst, reps=1, starts=10, seed=0):
    nq, K = inst["nq"], inst["K"]; idx = np.arange(2 ** nq); bits = (idx[:, None] >> np.arange(nq)) & 1
    val = np.zeros(2 ** nq)
    for _, q, v in inst["terms"]: val += v * np.all(bits[:, q] == 1, axis=1)
    scale = val.max(); vn = val / scale; rng = np.random.default_rng(seed)
    f = lambda x: -float(np.dot(qaoa_xy_probs(vn, x[:reps], x[reps:], nq, K), vn))
    best = None
    for _ in range(starts):
        r = minimize(f, np.concatenate([rng.uniform(0, 2 * np.pi, reps), rng.uniform(0, np.pi, reps)]), method="COBYLA", options={"maxiter": 500})
        if best is None or r.fun < best.fun: best = r
    return dict(probs=qaoa_xy_probs(vn, best.x[:reps], best.x[reps:], nq, K))


def random_feasible_baseline(inst, opt, shots, seed=1):
    """Random answers that respect the budget (exactly K links): the fair baseline for the XY version."""
    nq, K = inst["nq"], inst["K"]; idx = np.arange(2 ** nq)
    p = np.array([1.0 if bin(i).count("1") == K else 0.0 for i in idx]); return summarize(inst, p, opt, shots, seed)
