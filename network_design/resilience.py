"""Resilience add-ons for a QKD placement.

1. Key splitting: for each QKD-protected substation whose key passes through trusted nodes, add a second
   all-QKD path whose relays share no node with the first. The key is split (XOR) across both paths, so
   compromising any single trusted node reveals nothing. Each second path is chosen to need the fewest new QKD links.
2. Backup routes: links whose cut isolates substations (bridges) are removed by adding backup links between
   the isolated parts and the rest. These are PQC-protected alternates (leased line, licensed microwave, private LTE),
   not QKD. Without coordinates, each backup's length is estimated from the existing route between its endpoints
   (an over-estimate of the straight-line distance)."""
import sys, itertools
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import networkx as nx


def key_splitting(net, Y, T, alt=None):
    """alt: a Net built with a larger hop limit, used only to search for second paths (same links, same control centers)."""
    alt = alt or net
    v, used, prot = net.evaluate(Y, T); first = dict(net.last_paths)
    Y2 = {tuple(sorted(e)) for e in Y}; plan, no_option = {}, []
    for s, (edges1, relays1) in first.items():
        if not relays1: continue                       # direct link from a control center: no trusted node to split around
        e1 = {tuple(sorted(e)) for e in edges1}; best = None
        for eidx, relays in alt.paths.get(s, []):
            if set(relays) & set(relays1): continue
            E = {alt.feasible[i] for i in eidx}
            if E == e1: continue
            cost = (len(E - Y2), len(set(relays) - set(used)))
            if best is None or cost < best[0]: best = (cost, E, relays)
        if best is None: no_option.append(s); continue
        Y2 |= best[1]; plan[s] = dict(second_path_relays=best[2], new_links=best[0][0])
    extra = len(Y2) - len({tuple(sorted(e)) for e in Y})
    split_mw = sum(net.G.nodes[s]["mw"] for s in plan if s in net.G)
    relayed_mw = sum(net.G.nodes[s]["mw"] for s, (_, r) in first.items() if r)
    return dict(substations_needing_split=len(plan) + len(no_option), split=len(plan), no_second_path=no_option,
                extra_qkd_links=extra, split_mw=round(split_mw, 1), relayed_mw=round(relayed_mw, 1)), Y2


def backup_routes(net):
    """Greedy bridge-removal: repeatedly join the two leaf blocks of the bridge tree that are farthest apart."""
    G = net.G.copy(); G.add_node("_CC_")
    for c in net.cc: G.add_edge("_CC_", c, km=0.0)
    added = []
    def isolated_mw(H):
        tot = 0.0
        for a, b in nx.bridges(H):
            K = H.copy(); K.remove_edge(a, b)
            tot = max(tot, sum(net.G.nodes[s]["mw"] for s in net.G if not nx.has_path(K, s, "_CC_")))
        return tot
    before_bridges = sum(1 for _ in nx.bridges(G)); before_worst = isolated_mw(G)
    leaves0 = None
    for _ in range(500):
        br = list(nx.bridges(G))
        if not br: break
        K = G.copy(); K.remove_edges_from(br)
        comp = {n: i for i, cc in enumerate(nx.connected_components(K)) for n in cc}
        T = nx.Graph(); T.add_nodes_from(set(comp.values()))
        for a, b in br: T.add_edge(comp[a], comp[b])
        leaves = [x for x in T if T.degree(x) == 1]
        if leaves0 is None: leaves0 = len(leaves)
        if len(leaves) < 2: break
        dist = dict(nx.all_pairs_shortest_path_length(T)); choice = None
        members = lambda c: [n for n in comp if comp[n] == c and n != "_CC_"]
        for la, lb in sorted(itertools.combinations(leaves, 2), key=lambda p: -dist[p[0]][p[1]]):
            pairs = [(u, v) for u in members(la) for v in members(lb) if u != v and not G.has_edge(u, v)]
            if pairs:
                u, v = min(pairs, key=lambda p: nx.dijkstra_path_length(net.G, p[0], p[1], weight="km")); choice = (u, v); break
        if choice is None: break
        u2, v2 = choice; km = nx.dijkstra_path_length(net.G, u2, v2, weight="km")
        G.add_edge(u2, v2, km=km, backup=True); added.append(dict(link=f"{u2} - {v2}", km_estimate=round(km, 1)))
    return dict(bridges_before=before_bridges, worst_cut_mw_before=round(before_worst, 1),
                lower_bound_links=(leaves0 + 1) // 2 if leaves0 else 0, backup_links=len(added),
                bridges_after=sum(1 for _ in nx.bridges(G)), worst_cut_mw_after=round(isolated_mw(G), 1),
                backup_km_total=round(sum(a["km_estimate"] for a in added), 1), added=added)
