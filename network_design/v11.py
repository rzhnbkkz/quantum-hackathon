"""Version 1.1: QKD placement with only the parameters the Sobol screen kept.

Value of protecting substation s = MW_s x route_km_s
    MW_s       consequence (load at s; CIP-002 rates cyber impact by MW)
    route_km_s exposure (km of fiber from s to its nearest control center; Sobol: beta ST 0.25)
s is protected only if every hop of a path from a control center to s has QKD.
Feasible QKD link: km x alpha <= loss_limit   (alpha 0.35 dB/km measured on EPB fiber)
Policy inputs (not guessed probabilities): K = QKD links, T = trusted nodes allowed, H = max hops.
Rule (CIP-012): the control-center chain gets QKD first.
Dropped after Sobol: tap rate (ST 0.03), alarm catch rate (ST 0.00), trusted-node compromise chance and
control-center weight (ST 0.08 each, replaced by the T cap and the CIP-012 rule), dollar prices (replaced by K, T).
"""
import json, math, random, time
import numpy as np, networkx as nx
from scipy.optimize import milp, LinearConstraint, Bounds


class Net:
    def __init__(self, path, alpha=0.35, loss_limit=10.0, H=3, drop=(), cc=None):
        raw = json.load(open(path)); self.name = path.rsplit("/", 1)[-1].replace(".json", "")
        G = nx.Graph()
        drop = {tuple(sorted(e)) for e in drop}
        for (a, b), km, kv in raw["links"]:
            if tuple(sorted((a, b))) in drop: continue
            if G.has_edge(a, b): km = min(km, G[a][b]["km"])
            G.add_edge(a, b, km=km)
        if cc is None or not drop: G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
        for s in G: G.nodes[s]["mw"] = raw["load"].get(s, 0.0); G.nodes[s]["kv"] = raw["kv"].get(s, 0.0)
        self.G, self.H = G, H
        if cc is None:
            core = [s for s in raw["core"] if s in G]
            bc = nx.betweenness_centrality(G, weight="km")
            cc1 = max(core, key=lambda s: (G.nodes[s]["kv"], bc[s]))
            near = nx.single_source_shortest_path_length(G, cc1, cutoff=H)
            cc2 = max([s for s in near if s in core and s != cc1] or [s for s in near if s != cc1], key=lambda s: bc[s])
            cc = [cc1, cc2]
        self.cc = list(cc); cc1, cc2 = self.cc
        self.feasible = sorted(tuple(sorted(e)) for e in G.edges if G.edges[e]["km"] * alpha <= loss_limit)
        self.eidx = {e: i for i, e in enumerate(self.feasible)}
        F = G.edge_subgraph(self.feasible).copy()
        dist = {}
        for c in self.cc:
            if c not in G: continue
            for s, d in nx.single_source_dijkstra_path_length(G, c, weight="km").items(): dist[s] = min(dist.get(s, math.inf), d)
        self.value = {s: G.nodes[s]["mw"] * dist[s] for s in G if s not in self.cc and s in dist}   # MW x route km
        self.paths = {}   # target -> list of (edge ids, relay nodes)
        for s in list(self.value) + [cc2]:
            if s not in F: continue
            out = []
            for c in self.cc:
                if c == s or c not in F: continue
                for p in nx.all_simple_paths(F, c, s, cutoff=H):
                    if s == cc2 and c != cc1: continue
                    out.append(([self.eidx[tuple(sorted(e))] for e in zip(p, p[1:])], [n for n in p[1:-1] if n not in self.cc]))
            if out: self.paths[s] = out
        self.cc_reachable = cc2 in self.paths
        self.relays = sorted({n for ps in self.paths.values() for _, r in ps for n in r})
        self.ridx = {n: i for i, n in enumerate(self.relays)}
        self.max_value = sum(v for s, v in self.value.items() if s in self.paths)

    # ---------------------------------------------------------------- evaluation shared by all heuristics
    def evaluate(self, Y, T):
        """Links Y fixed: protect the control-center chain, then substations by value, using paths inside Y
        that add the fewest new trusted nodes, never exceeding T. Returns (value, trusted nodes, protected)."""
        Yi = {self.eidx[e] for e in Y if e in self.eidx}; used, prot, val = set(), [], 0.0
        self.last_paths = {}
        order = ([self.cc[1]] if self.cc_reachable else []) + sorted((s for s in self.paths if s != self.cc[1]), key=lambda s: -self.value[s])
        for s in order:
            best = None
            for edges, relays in self.paths[s]:
                if all(e in Yi for e in edges):
                    new = set(relays) - used
                    if len(used) + len(new) <= T and (best is None or len(new) < len(best[0])): best = (new, edges, relays)
            if best is not None:
                used |= best[0]; prot.append(s); val += self.value.get(s, 0.0)
                self.last_paths[s] = ([self.feasible[i] for i in best[1]], list(best[2]))
        cc_ok = (not self.cc_reachable) or (self.cc[1] in prot)
        return (val if cc_ok else -1.0), used, prot

    # ---------------------------------------------------------------- 1. exact: integer program
    def traffic(self):
        """MW of control traffic crossing each feasible link when every substation uses its shortest route (PQC baseline)."""
        f = {e: 0.0 for e in self.feasible}
        for s in self.G:
            if s in self.cc: continue
            best = None
            for c in self.cc:
                try:
                    p = nx.dijkstra_path(self.G, c, s, weight="km"); L = nx.path_weight(self.G, p, "km")
                    if best is None or L < best[0]: best = (L, p)
                except nx.NetworkXNoPath: pass
            if best:
                for e in zip(best[1], best[1][1:]):
                    e = tuple(sorted(e))
                    if e in f: f[e] += self.G.nodes[s]["mw"]
        return f

    def milp(self, K, T, relax=False, time_limit=120, mu=0.0):
        """mu = weight on tap detection: each QKD link also earns (MW of traffic crossing it) x (its km),
        scaled so mu = 1 makes the two goals equally large in total."""
        items = [(s, e, r) for s, ps in self.paths.items() for e, r in ps]
        nE, nR, nP = len(self.feasible), len(self.relays), len(items)
        N = nE + nR + nP; c = np.zeros(N)
        c[nE + nR:] = [-self.value.get(s, 0.0) for s, _, _ in items]
        if mu > 0:
            f = self.traffic(); d = {e: f[e] * self.G.edges[e]["km"] for e in self.feasible}
            scale = self.max_value / max(1e-9, sum(d.values()))
            c[:nE] = [-mu * scale * d[e] for e in self.feasible]
        A, lo, hi = [], [], []
        def add(coefs, l, h):
            r = np.zeros(N)
            for i, v in coefs: r[i] += v
            A.append(r); lo.append(l); hi.append(h)
        add([(i, 1) for i in range(nE)], -np.inf, K)
        add([(nE + i, 1) for i in range(nR)], -np.inf, T)
        by = {}
        for k, (s, e, r) in enumerate(items):
            z = nE + nR + k; by.setdefault(s, []).append(z)
            for ei in e: add([(z, 1), (ei, -1)], -np.inf, 0)
            for n in r: add([(z, 1), (nE + self.ridx[n], -1)], -np.inf, 0)
        for s, zs in by.items(): add([(z, 1) for z in zs], -np.inf, 1)
        if self.cc_reachable: add([(z, 1) for z in by[self.cc[1]]], 1, np.inf)
        res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.zeros(N) if relax else np.ones(N),
                   bounds=Bounds(0, 1), options={"time_limit": time_limit})
        if res.x is None: return None
        if relax: return res.x[:nE]
        return {self.feasible[i] for i in range(nE) if res.x[i] > 0.5}

    # ---------------------------------------------------------------- 2. LP relaxation + rounding
    def lp_round(self, K, T):
        x = self.milp(K, T, relax=True)
        Y = set()
        for i in np.argsort(-x):
            if x[i] < 1e-6 or len(Y) >= K: break
            cand = Y | {self.feasible[i]}
            if self.evaluate(cand, T)[0] >= self.evaluate(Y, T)[0]: Y = cand
        return Y

    # ---------------------------------------------------------------- 3. greedy (value per resource)
    def greedy(self, K, T, start=None):
        Y = set(start or ())
        if self.cc_reachable and not start:
            e, r = min(self.paths[self.cc[1]], key=lambda p: (len(p[0]) + len(p[1])))
            Y = {self.feasible[i] for i in e}
        while True:
            v0, used, _ = self.evaluate(Y, T); best = None
            for s, ps in self.paths.items():
                for e, r in ps:
                    new = {self.feasible[i] for i in e} - Y
                    if not new or len(Y) + len(new) > K: continue
                    v1, used1, _ = self.evaluate(Y | new, T)
                    gain = (v1 - v0) / (len(new) + len(used1 - used))
                    if gain > 1e-9 and (best is None or gain > best[0]): best = (gain, new)
            if best is None: return Y
            Y |= best[1]

    # ---------------------------------------------------------------- 4. greedy + local search
    def greedy_ls(self, K, T):
        Y = self.greedy(K, T); v = self.evaluate(Y, T)[0]; improved = True
        while improved:
            improved = False
            for e in sorted(Y):
                cand = self.greedy(K, T, start=Y - {e})
                vc = self.evaluate(cand, T)[0]
                if vc > v + 1e-9: Y, v, improved = cand, vc, True; break
        return Y

    # ---------------------------------------------------------------- 5. simulated annealing
    def anneal(self, K, T, iters=4000, seed=0):
        rnd = random.Random(seed); Y = self.greedy(K, T); v = self.evaluate(Y, T)[0]
        best, bv = set(Y), v; temp0 = max(1.0, 0.05 * self.max_value)
        for k in range(iters):
            temp = temp0 * (0.001 ** (k / iters)); cand = set(Y)
            move = rnd.random()
            if move < 0.4 and cand: cand.remove(rnd.choice(sorted(cand)))
            if move > 0.3 and len(cand) < K: cand.add(rnd.choice(self.feasible))
            if len(cand) > K: continue
            vc = self.evaluate(cand, T)[0]
            if vc >= v or rnd.random() < math.exp((vc - v) / temp):
                Y, v = cand, vc
                if v > bv: best, bv = set(Y), v
        return best

    # ---------------------------------------------------------------- 6. genetic algorithm
    def genetic(self, K, T, pop=40, gens=60, seed=0):
        rnd = random.Random(seed)
        def repair(Y):
            Y = set(Y)
            while len(Y) > K: Y.remove(rnd.choice(sorted(Y)))
            return Y
        P = [self.greedy(K, T)] + [repair(set(rnd.sample(self.feasible, rnd.randint(1, K)))) for _ in range(pop - 1)]
        fit = lambda Y: self.evaluate(Y, T)[0]
        for _ in range(gens):
            P.sort(key=fit, reverse=True); elite = P[:pop // 4]; kids = []
            while len(kids) < pop - len(elite):
                a, b = rnd.sample(elite, 2)
                child = {e for e in a | b if rnd.random() < 0.6 or (e in a and e in b)}
                if rnd.random() < 0.5 and child: child.remove(rnd.choice(sorted(child)))
                if rnd.random() < 0.5: child.add(rnd.choice(self.feasible))
                kids.append(repair(child))
            P = elite + kids
        return max(P, key=fit)

    # ---------------------------------------------------------------- naive baselines
    def busiest(self, K, T):
        eb = nx.edge_betweenness_centrality(self.G, weight="km")
        return set(sorted(self.feasible, key=lambda e: -eb.get(e, eb.get(e[::-1], 0)))[:K])

    def random_links(self, K, T, seed=0):
        return set(random.Random(seed).sample(self.feasible, min(K, len(self.feasible))))


ALGORITHMS = ["milp", "lp_round", "greedy", "greedy_ls", "anneal", "genetic", "busiest", "random_links"]
LABELS = dict(milp="Integer program (exact)", lp_round="LP relaxation + rounding", greedy="Greedy (value per resource)",
              greedy_ls="Greedy + local search", anneal="Simulated annealing", genetic="Genetic algorithm",
              busiest="Busiest links first", random_links="Random links")


def run_all(net, K, T, algs=ALGORITHMS):
    out = {}
    for a in algs:
        t = time.time(); Y = getattr(net, a)(K, T); dt = time.time() - t
        v, used, prot = net.evaluate(Y, T)
        out[a] = dict(value=max(v, 0.0), seconds=round(dt, 4), links=len(Y), trusted=len(used), protected=len(prot),
                      cc_linked=net.cc[1] in prot, valid=v >= 0)
    return out
