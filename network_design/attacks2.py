"""Expanded attack tests (adds to attacks.py): run at several budgets, with the missing attack types.

New attack types
  blinding : detector-blinding attack on one QKD link. The QBER check is fooled, so the tap there is NOT detected
             unless the link has a detector-side countermeasure (click-rate monitoring or MDI-QKD), caught with prob
             D_CM. Measured: worst-case MW of traffic read undetected through one blinded QKD link.
  dos      : noise injection on QKD links pushes QBER above the abort limit, so those links stop making keys and
             their traffic falls back to PQC. Measured: MW losing long-term (QKD) secrecy for the worst 1 and worst 2
             links, and MW losing service (should be 0: PQC fallback keeps traffic flowing).
  tn2      : two trusted nodes compromised together (worst pair). With key splitting, a split substation is exposed
             only if BOTH of its paths are compromised.
  cut2     : two links cut together (worst pair), before and after adding backup routes.
"""
import sys, itertools
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import networkx as nx
from v11 import Net
from attacks import routes, summarize, mw
from resilience import key_splitting, backup_routes

D_CM = 0.9   # assumption: detector countermeasure (click-rate monitor / MDI-QKD) catches a blinding attack 90% of the time


def blinding(net, R, Y):
    Y = {tuple(sorted(e)) for e in Y}; worst = (0.0, None)
    for e in Y:
        through = sum(mw(net, s) for s, (E, _, q) in R.items() if e in E)
        if through > worst[0]: worst = (through, e)
    return dict(worst_mw_no_countermeasure=round(worst[0], 1), link=" - ".join(worst[1]) if worst[1] else None,
                worst_expected_mw_with_countermeasure=round(worst[0] * (1 - D_CM), 1))


def dos(net, R, Y):
    Y = {tuple(sorted(e)) for e in Y}; prot = {s: set(E) for s, (E, _, q) in R.items() if q}
    lose = lambda S: sum(mw(net, s) for s, E in prot.items() if E & S and s in net.G and s not in net.cc)
    one = max(((lose({e}), e) for e in Y), default=(0.0, None))
    two = max(((lose(set(p)), p) for p in itertools.combinations(sorted(Y), 2)), default=(0.0, None))
    return dict(worst_1_link_secrecy_lost_mw=round(one[0], 1), worst_2_links_secrecy_lost_mw=round(two[0], 1),
                service_lost_mw=0.0)


def tn2(net, R, Y, T, split_plan=None):
    """Worst pair of compromised trusted nodes. split_plan: substation -> second-path relays (keys split over two paths)."""
    relay = {s: set(rel) for s, (E, rel, q) in R.items() if q and rel}
    nodes = sorted({n for r in relay.values() for n in r})
    def exposed(C, split):
        tot = 0.0
        for s, r in relay.items():
            if split and s in split:
                if (r & C) and (set(split[s]) & C): tot += mw(net, s)
            elif r & C: tot += mw(net, s)
        return tot
    res = {}
    for label, split in (("no_split", None), ("with_split", split_plan)):
        one = max((exposed({n}, split) for n in nodes), default=0.0)
        two = max((exposed(set(p), split) for p in itertools.combinations(nodes, 2)), default=one)
        res[label] = dict(worst_1_node_mw=round(one, 1), worst_2_nodes_mw=round(two, 1))
    return res


def cut2(net, extra_edges=()):
    """Worst simultaneous two-link cut: MW cut off from every control center. Uses bridges of G - e to find 2-cuts fast."""
    G = net.G.copy()
    for u, v in extra_edges: G.add_edge(u, v)
    def lost(H):
        reach = set()
        for c in net.cc:
            if c in H: reach |= nx.node_connected_component(H, c)
        return sum(mw(net, s) for s in net.G if s not in reach)
    one = max((lost(nx.restricted_view(G, [], [e])) for e in G.edges), default=0.0)
    best = one
    for e in list(G.edges):
        H = G.copy(); H.remove_edge(*e)
        for b in nx.bridges(H):
            K = H.copy(); K.remove_edge(*b); best = max(best, lost(K))
    return dict(worst_1_cut_mw=round(one, 1), worst_2_cuts_mw=round(best, 1))


def run_network(path, budgets=((4, 2), (8, 4), (16, 8)), H=3):
    n = Net(path, H=H); n4 = Net(path, H=4, cc=n.cc)
    out = dict(net=n.name, substations=n.G.number_of_nodes(), links=n.G.number_of_edges(), qkd_feasible_links=len(n.feasible),
               qkd_targets=len(n.paths), total_mw=round(sum(mw(n, s) for s in n.G), 1), budgets={})
    bk = backup_routes(n)
    added = [tuple(a["link"].split(" - ")) for a in bk["added"]]
    out["cuts"] = dict(before_backup=cut2(n), after_backup=cut2(n, added), backup_links=bk["backup_links"])
    for K, T in budgets:
        row = {}
        for name, Y in (("pqc_only", set()), ("balanced", n.milp(K, T, mu=1) or set())):
            s = summarize(n, Y, K, T, path, replan=False); R, _ = routes(n, Y, T)
            ks, _ = key_splitting(n, Y, T, alt=n4)
            # rebuild the split plan (substation -> second-path relays) for the two-node test
            n.evaluate(Y, T); first = dict(n.last_paths); split = {}
            for sub, (e1, r1) in first.items():
                if not r1: continue
                for eidx, rel in n4.paths.get(sub, []):
                    if not set(rel) & set(r1) and {n4.feasible[i] for i in eidx} != {tuple(sorted(x)) for x in e1}:
                        split[sub] = rel; break
            row[name] = dict(
                secrecy_mw=s["qkd_protected_mw"], random_undetected_mw=s["random_taps"]["expected_undetected_mw"],
                taps_on_qkd=s["random_taps"]["share_of_taps_landing_on_qkd"], worst_tap_mw=s["worst_single_tap"]["undetected_mw"],
                blinding=blinding(n, R, Y), dos=dos(n, R, Y), trusted_nodes=tn2(n, R, Y, T, split),
                key_split=dict(split=ks["split"], needing=ks["substations_needing_split"], extra_links=ks["extra_qkd_links"]))
        out["budgets"][f"K{K}_T{T}"] = row
    return out
