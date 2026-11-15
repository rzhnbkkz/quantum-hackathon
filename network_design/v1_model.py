"""Version 1: risk-based QKD placement on a hybrid QKD/PQC utility network.

Every link carries hybrid post-quantum cryptography. QKD is added where it reduces the most risk per dollar.

Risk reduced by protecting substation s through path p (all hops QKD):
    value(s, p) = I_s * P_s * D * (1 - q) ** TN(p)
  I_s   consequence: MW of load at s (the backup control center counts as the whole system's load)
  P_s   chance s's traffic is tapped: 1 - exp(-lam * L_s), L_s = km of s's shortest route to a control center
  D     chance the BB84 alarm catches a tap (from 3a_bb84_grid_link.ipynb)
  q     chance a trusted node is itself compromised; TN(p) = relay substations on p
Cost: C_qkd per QKD link + C_tn per trusted node used.
The exact optimizer is an integer program (scipy.optimize.milp, HiGHS).
"""
import json, math, random, itertools
import numpy as np, networkx as nx
from scipy.optimize import milp, LinearConstraint, Bounds

DEFAULTS = dict(db_per_km=0.35, max_loss_db=10.0, max_hops=3, lam=0.01, D=0.95, q=0.05,
                C_qkd=150_000, C_tn=30_000, cc_weight=1.0, beta=1.0, gamma=1.0)
# beta: exposure grows as (route km)^beta (0 = route length irrelevant, 1 = proportional)
# gamma: consequence grows as (MW)^gamma (0 = every substation equal, 1 = proportional to MW)
RANGES = dict(lam=(0.002, 0.03), D=(0.5, 0.98), q=(0.01, 0.10), C_qkd=(100_000, 200_000),
              C_tn=(10_000, 50_000), cc_weight=(0.25, 1.0))


# ---------------------------------------------------------------- network
def load_network(path):
    raw = json.load(open(path))
    G = nx.Graph()
    for (a, b), km, kv in raw["links"]:
        if G.has_edge(a, b): km = min(km, G[a][b]["km"])
        G.add_edge(a, b, km=km)
    for s in G:
        G.nodes[s]["load"] = raw["load"].get(s, 0.0); G.nodes[s]["kv"] = raw["kv"].get(s, 0.0)
    return G, raw


def control_centers(G, core, max_hops=3):
    """Proxies, same as version 0: CC1 = highest-kV, most central core substation; CC2 = most central core within max_hops."""
    bc = nx.betweenness_centrality(G, weight="km")
    cc1 = max([s for s in G if s in core], key=lambda s: (G.nodes[s]["kv"], bc[s]))
    near = nx.single_source_shortest_path_length(G, cc1, cutoff=max_hops)
    cc2 = max([s for s in near if s in core and s != cc1], key=lambda s: bc[s])
    return [cc1, cc2]


class Problem:
    def __init__(self, G, cc, **params):
        self.G, self.cc = G, cc
        self.p = dict(DEFAULTS, **params)
        P = self.p
        self.feasible = sorted(tuple(sorted(e)) for e in G.edges
                               if G.edges[e]["km"] * P["db_per_km"] <= P["max_loss_db"])
        self.eidx = {e: i for i, e in enumerate(self.feasible)}
        F = G.edge_subgraph(self.feasible).copy()
        P["max_hops"] = int(P["max_hops"])
        loads = [G.nodes[s]["load"] for s in G if s not in cc]
        mw_ref = sum(loads) / len(loads)
        cons = {s: mw_ref * (G.nodes[s]["load"] / mw_ref) ** P["gamma"] if G.nodes[s]["load"] > 0 or P["gamma"] == 0
                else 0.0 for s in G}
        total = sum(cons[s] for s in G if s not in cc)
        # route length of each substation's traffic: shortest km to any control center (on the full network)
        dist = {}
        for c in cc:
            for s, d in nx.single_source_dijkstra_path_length(G, c, weight="km").items():
                dist[s] = min(dist.get(s, math.inf), d)
        dist[cc[1]] = nx.dijkstra_path_length(G, cc[0], cc[1], weight="km")
        self.targets = [s for s in G if s != cc[0]]
        self.I = {s: (P["cc_weight"] * total if s == cc[1] else cons[s]) for s in self.targets}
        L_ref = sorted(dist[s] for s in self.targets)[len(self.targets) // 2]
        self.Ps = {s: 1 - math.exp(-P["lam"] * L_ref * (dist[s] / L_ref) ** P["beta"]) for s in self.targets}
        # candidate paths: simple paths over QKD-feasible links from a control center, at most max_hops
        self.paths = []          # (s, path_nodes, edge_ids, relay_nodes, value)
        for s in self.targets:
            if s not in F: continue
            seen = set()
            for c in cc:
                if c == s or c not in F: continue
                for p in nx.all_simple_paths(F, c, s, cutoff=P["max_hops"]):
                    key = tuple(p)
                    if key in seen: continue
                    seen.add(key)
                    edges = [self.eidx[tuple(sorted(e))] for e in zip(p, p[1:])]
                    relays = [n for n in p[1:-1] if n not in cc]
                    v = self.I[s] * self.Ps[s] * P["D"] * (1 - P["q"]) ** len(relays)
                    if v > 0: self.paths.append((s, p, edges, relays, v))
        self.relay_nodes = sorted({n for *_, r, _ in self.paths for n in r})
        self.ridx = {n: i for i, n in enumerate(self.relay_nodes)}

    # ------------------------------------------------------------ exact optimizer
    def solve(self, budget):
        nE, nR, nP = len(self.feasible), len(self.relay_nodes), len(self.paths)
        N = nE + nR + nP                       # variables: y_e (QKD link), t_n (trusted node), z_p (path used)
        c = np.zeros(N); c[nE + nR:] = [-v for *_, v in self.paths]      # maximize value
        rows, lo, hi = [], [], []
        def row(): return np.zeros(N)
        r = row(); r[:nE] = self.p["C_qkd"]; r[nE:nE + nR] = self.p["C_tn"]; rows.append(r); lo.append(-np.inf); hi.append(budget)
        by_sub = {}
        for k, (s, p, edges, relays, v) in enumerate(self.paths):
            z = nE + nR + k; by_sub.setdefault(s, []).append(z)
            for e in edges:
                r = row(); r[z] = 1; r[e] = -1; rows.append(r); lo.append(-np.inf); hi.append(0)
            for n in relays:
                r = row(); r[z] = 1; r[nE + self.ridx[n]] = -1; rows.append(r); lo.append(-np.inf); hi.append(0)
        for s, zs in by_sub.items():
            r = row(); r[zs] = 1; rows.append(r); lo.append(-np.inf); hi.append(1)
        res = milp(c, constraints=LinearConstraint(np.array(rows), lo, hi),
                   integrality=np.ones(N), bounds=Bounds(0, 1), options={"time_limit": 60})
        x = np.round(res.x).astype(int)
        Y = {self.feasible[i] for i in range(nE) if x[i]}
        return self.evaluate(Y)

    # ------------------------------------------------------------ evaluation (shared by every method)
    def evaluate(self, Y):
        """Given QKD links Y, each target uses its best all-QKD path. Returns value, cost and details."""
        Yi = {self.eidx[e] for e in Y if e in self.eidx}
        best = {}
        for s, p, edges, relays, v in self.paths:
            if all(e in Yi for e in edges) and v > best.get(s, (0,))[0]:
                best[s] = (v, p, relays)
        relays = sorted({n for v, p, r in best.values() for n in r})
        cost = len(Y) * self.p["C_qkd"] + len(relays) * self.p["C_tn"]
        loads = sum(self.G.nodes[s]["load"] for s in best if s not in self.cc)
        return dict(links=sorted(Y), value=sum(v for v, *_ in best.values()), cost=cost,
                    protected={s: p for s, (v, p, r) in best.items()}, trusted_nodes=relays,
                    mw=loads, cc_linked=self.cc[1] in best)

    # ------------------------------------------------------------ baselines
    def greedy(self, budget):
        """Add the path with the best extra value per extra dollar, until nothing affordable helps."""
        Y = set()
        while True:
            cur = self.evaluate(Y); best = None
            for s, p, edges, relays, v in self.paths:
                new = Y | {self.feasible[e] for e in edges}
                if new == Y: continue
                ev = self.evaluate(new)
                if ev["cost"] > budget: continue
                gain = (ev["value"] - cur["value"]) / (ev["cost"] - cur["cost"] or 1)
                if gain > 0 and (best is None or gain > best[0]): best = (gain, new)
            if best is None: return cur
            Y = best[1]

    def busiest_first(self, budget):
        """Rank QKD-feasible links by how many shortest routes cross them (traffic proxy); add while affordable."""
        eb = nx.edge_betweenness_centrality(self.G, weight="km")
        Y = set()
        for e in sorted(self.feasible, key=lambda e: -eb.get(e, eb.get(e[::-1], 0))):
            if self.evaluate(Y | {e})["cost"] <= budget: Y.add(e)
        return self.evaluate(Y)

    def random_links(self, budget, trials=30, seed=0):
        rnd = random.Random(seed); vals = []
        for _ in range(trials):
            Y = set()
            for e in rnd.sample(self.feasible, len(self.feasible)):
                if self.evaluate(Y | {e})["cost"] <= budget: Y.add(e)
            vals.append(self.evaluate(Y))
        return dict(value=float(np.mean([v["value"] for v in vals])), mw=float(np.mean([v["mw"] for v in vals])),
                    cost=float(np.mean([v["cost"] for v in vals])))

    def everywhere(self):
        return self.evaluate(set(self.feasible))


def v0_links(G, cc, budget_links=8, max_loss=10.0, hops=3, db=0.35):
    """The version 0 rule, reproduced for comparison."""
    kv = {s: G.nodes[s]["kv"] for s in G}; load = {s: G.nodes[s]["load"] for s in G}
    tier = lambda s: 4 if s in cc else 3 if kv[s] >= 161 else 2 if load[s] >= 50 else 1
    F = G.edge_subgraph([e for e in G.edges if G.edges[e]["km"] * db <= max_loss]).copy()
    qkd = set()
    for t in [cc[1]] + sorted([s for s in G if s not in cc], key=lambda s: (-tier(s), -load[s])):
        best = None
        for c in cc:
            if c == t or c not in F or t not in F or not nx.has_path(F, c, t): continue
            p = nx.shortest_path(F, c, t, weight=lambda u, v, d: 1 + d["km"] / 1000)
            if len(p) - 1 > hops: continue
            new = {tuple(sorted(e)) for e in zip(p, p[1:])} - qkd
            if best is None or len(new) < len(best[1]): best = (p, new)
        if best and len(qkd) + len(best[1]) <= budget_links: qkd |= best[1]
    return qkd


def smaa(G, cc, budget, samples=300, seed=1):
    """Draw parameters from RANGES, solve exactly each time, report how often each link is chosen."""
    rnd = random.Random(seed); count, n = {}, 0
    for _ in range(samples):
        prm = {k: rnd.uniform(*r) for k, r in RANGES.items()}
        ev = Problem(G, cc, **prm).solve(budget)
        for e in ev["links"]: count[e] = count.get(e, 0) + 1
        n += 1
    return {f"{a} - {b}": round(k / n, 3) for (a, b), k in sorted(count.items(), key=lambda kv: -kv[1])}
