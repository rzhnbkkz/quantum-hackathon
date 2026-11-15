"""Extract a city's substation network from MATPOWER case_ACTIVSg70k.m (generalizes extract_chattanooga.py).
Usage: python extract_region.py case_ACTIVSg70k.m CITY RADIUS out.json
Keeps the city's substations (in its most common control area, so same-named towns elsewhere are dropped)
plus every substation within RADIUS links of them. Line length is estimated from reactance at typical ohm/km."""
import sys, json, collections, pickle, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_mp import parse

OHM_PER_KM = {765: 0.27, 500: 0.30, 345: 0.33, 230: 0.40, 161: 0.42, 138: 0.45, 115: 0.45, 100: 0.45, 69: 0.45}

def load(path):
    cache = path + ".pkl"
    if os.path.exists(cache): return pickle.load(open(cache, "rb"))
    d = parse(path); pickle.dump(d, open(cache, "wb")); return d

def extract(path, city, radius):
    bus, br, names, base = load(path)
    idx = {int(b[0]): i for i, b in enumerate(bus)}
    sub = lambda i: names[i].rsplit(" ", 1)[0]
    edges = collections.defaultdict(list)
    for b in br:
        if b[10] == 0: continue
        f, t = idx[int(b[0])], idx[int(b[1])]
        if sub(f) == sub(t) or bus[f][9] != bus[t][9]: continue
        V = bus[f][9]; km = b[3] * V * V / base / OHM_PER_KM.get(int(V), 0.42)
        edges[tuple(sorted((sub(f), sub(t))))].append((km, V))
    G = collections.defaultdict(set)
    for a, c in edges: G[a].add(c); G[c].add(a)
    hits = [i for i, n in enumerate(names) if n.startswith(city + " ") and n[len(city) + 1].isdigit()]
    area = collections.Counter(bus[i][6] for i in hits).most_common(1)[0][0]
    core = {sub(i) for i in hits if bus[i][6] == area}
    ring, frontier = set(core), set(core)
    for _ in range(radius):
        frontier = {n for s in frontier for n in G[s]} - ring; ring |= frontier
    links = [(k, min(e[0] for e in v), max(e[1] for e in v)) for k, v in edges.items() if k[0] in ring and k[1] in ring]
    load_mw, kv = collections.Counter(), collections.Counter()
    for i, b in enumerate(bus):
        if sub(i) in ring: load_mw[sub(i)] += b[2]; kv[sub(i)] = max(kv[sub(i)], b[9])
    return {"city": city, "radius": radius, "subs": sorted(ring), "core": sorted(core), "links": links, "load": load_mw, "kv": kv}

if __name__ == "__main__":
    r = extract(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    json.dump(r, open(sys.argv[4], "w"))
    print(f"{sys.argv[2]} radius {sys.argv[3]}: {len(r['subs'])} substations, {len(r['links'])} links")
