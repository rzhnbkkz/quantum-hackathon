"""Attack and recovery tests for a QKD placement (version 1.1).
Traffic model: a QKD-protected substation sends its control traffic over its QKD path; every other substation
uses its shortest route to the nearest control center, protected by post-quantum cryptography (PQC) only.
A tap on a QKD hop is detected by the BB84 alarm (D from 3a_bb84_grid_link.ipynb); a tap on a PQC-only hop is not."""
import sys, math, random, time, json
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import networkx as nx
from v11 import Net

D_DETECT = 0.98    # 3a: taps of >=15% of rounds caught in ~98% of 10-batch windows

def routes(net, Y, T):
    v, used, prot = net.evaluate(Y, T); qkd = dict(net.last_paths); R = {}
    for s in net.G:
        if s in net.cc and s != net.cc[1]: continue
        if s in qkd: R[s] = ([tuple(sorted(e)) for e in qkd[s][0]], qkd[s][1], True)
        else:
            best = None
            for c in net.cc:
                if c == s: continue
                try:
                    p = nx.dijkstra_path(net.G, c, s, weight="km"); L = nx.path_weight(net.G, p, "km")
                    if best is None or L < best[0]: best = (L, p)
                except nx.NetworkXNoPath: pass
            if best: R[s] = ([tuple(sorted(e)) for e in zip(best[1], best[1][1:])], [], False)
    return R, used

def mw(net, s): return net.G.nodes[s]["mw"]

def single_taps(net, R, Y):
    """For every link: MW of traffic crossing it. A tap is detected if THAT link has QKD (the alarm watches its own fiber)."""
    out = {}; Y = {tuple(sorted(e)) for e in Y}
    for e in (tuple(sorted(x)) for x in net.G.edges):
        through = sum(mw(net, s) for s, (E, _, q) in R.items() if e in E)
        und, det = (0.0, through) if e in Y else (through, 0.0)
        cc = (e not in Y) and any(e in E for s, (E, _, q) in R.items() if s == net.cc[1])
        out[e] = dict(undetected_mw=und, detected_mw=det, cc_link_undetected=cc, km=net.G.edges[e]["km"])
    return out

def random_taps(net, R, Y, trials=5000, max_taps=3, seed=0):
    """1-3 taps per trial, landing on links with probability proportional to length.
    A tap on a QKD link is caught with probability D; a substation's traffic is read undetected if any tap on its route is missed."""
    rnd = random.Random(seed); E = [tuple(sorted(x)) for x in net.G.edges]; w = [net.G.edges[e]["km"] for e in E]
    Y = {tuple(sorted(e)) for e in Y}; tot = 0.0; on_qkd = 0; n_taps = 0
    for _ in range(trials):
        taps = set(rnd.choices(E, weights=w, k=rnd.randint(1, max_taps)))
        missed = {t for t in taps if t not in Y or rnd.random() > D_DETECT}
        on_qkd += sum(1 for t in taps if t in Y); n_taps += len(taps)
        tot += sum(mw(net, s) for s, (Es, _, q) in R.items() if missed & set(Es))
    return dict(expected_undetected_mw=tot / trials, share_of_taps_on_qkd=on_qkd / max(1, n_taps))

def node_compromise(net, R):
    """A trusted node holds relayed keys in the clear: compromising it exposes every key relayed through it."""
    out = {}
    for n in {n for _, (E, rel, q) in R.items() if q for n in rel}:
        subs = [s for s, (E, rel, q) in R.items() if q and n in rel]
        out[n] = dict(exposed_mw=sum(mw(net, s) for s in subs), substations=subs, cc_link=net.cc[1] in subs)
    return out

def link_cuts(net, R, Y, K, T, path, replan=True):
    """Cut each link in turn: who loses connection, who loses QKD, and what a re-solved plan recovers."""
    out = {}; base_prot = {s for s, (_, _, q) in R.items() if q}
    for e in (tuple(sorted(x)) for x in net.G.edges):
        H = net.G.copy(); H.remove_edge(*e)
        reach = set()
        for c in net.cc: reach |= nx.node_connected_component(H, c)
        disc = [s for s in net.G if s not in reach]
        lost_qkd = [s for s in base_prot if e in R[s][0]]
        row = dict(disconnected_mw=sum(mw(net, s) for s in disc), disconnected=disc,
                   qkd_lost_mw=sum(mw(net, s) for s in lost_qkd if s not in net.cc), cc_link_lost=net.cc[1] in lost_qkd)
        if replan and lost_qkd:
            t = time.time(); n2 = Net(path, H=net.H, drop=[e], cc=net.cc); Y2 = n2.milp(K, T); dt = time.time() - t
            v2, u2, p2 = n2.evaluate(Y2 or set(), T)
            row.update(replan_seconds=round(dt, 3), replan_protected_mw=sum(mw(net, s) for s in p2 if s not in net.cc and s in net.G),
                       replan_cc_linked=net.cc[1] in p2)
        out[e] = row
    return out

def disjoint_backup(net, Y, T):
    """Which QKD-protected substations have a second, node-disjoint QKD-feasible path (for key splitting)?"""
    v, used, prot = net.evaluate(Y, T); F = net.G.edge_subgraph(net.feasible).copy(); res = {}
    for s in prot:
        if s in net.cc and s != net.cc[1]: continue
        k = 0
        for c in net.cc:
            if c != s and c in F and s in F:
                try: k = max(k, nx.node_connectivity(F, c, s))
                except Exception: pass
        res[s] = k
    return res

def summarize(net, Y, K, T, path, replan=True):
    R, used = routes(net, Y, T)
    st = single_taps(net, R, Y); rt = random_taps(net, R, Y); nc = node_compromise(net, R); lc = link_cuts(net, R, Y, K, T, path, replan)
    worst_tap = max(st.items(), key=lambda kv: kv[1]["undetected_mw"])
    worst_node = max(nc.items(), key=lambda kv: kv[1]["exposed_mw"]) if nc else (None, dict(exposed_mw=0, substations=[]))
    worst_cut = max(lc.items(), key=lambda kv: kv[1]["disconnected_mw"])
    cuts_qkd = [r for r in lc.values() if r["qkd_lost_mw"] > 0 or r["cc_link_lost"]]
    total = sum(mw(net, s) for s in net.G)
    return dict(
        total_mw=round(total, 1), qkd_protected_mw=round(sum(mw(net, s) for s, (_, _, q) in R.items() if q and s not in net.cc), 1),
        random_taps=dict(expected_undetected_mw=round(rt["expected_undetected_mw"], 1), share_of_taps_landing_on_qkd=round(rt["share_of_taps_on_qkd"], 3)),
        worst_single_tap=dict(link=" - ".join(worst_tap[0]), undetected_mw=round(worst_tap[1]["undetected_mw"], 1)),
        links_where_cc_link_tap_is_undetected=sum(1 for r in st.values() if r["cc_link_undetected"]),
        worst_trusted_node=dict(node=worst_node[0], exposed_mw=round(worst_node[1]["exposed_mw"], 1), substations=worst_node[1]["substations"]),
        worst_single_cut=dict(link=" - ".join(worst_cut[0]), disconnected_mw=round(worst_cut[1]["disconnected_mw"], 1), substations=worst_cut[1]["disconnected"]),
        links_whose_cut_disconnects_something=sum(1 for r in lc.values() if r["disconnected_mw"] > 0),
        cuts_that_remove_qkd=len(cuts_qkd),
        replan=dict(mean_seconds=round(sum(r.get("replan_seconds", 0) for r in cuts_qkd) / max(1, len(cuts_qkd)), 3),
                    cc_link_restored_share=round(sum(1 for r in cuts_qkd if r.get("replan_cc_linked")) / max(1, len(cuts_qkd)), 3)) if replan else None,
        key_splitting_ready=disjoint_backup(net, Y, T))
