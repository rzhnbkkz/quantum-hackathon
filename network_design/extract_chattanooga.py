"""Extract the Chattanooga-area substation network from MATPOWER case_ACTIVSg70k.m.
Usage: python extract_chattanooga.py case_ACTIVSg70k.m chatt_raw.json
Substation = bus name without its last number ("CHATTANOOGA 2 3" -> "CHATTANOOGA 2").
Keeps every CHATTANOOGA substation plus its direct neighbors. Line length is estimated
from branch reactance using typical ohm/km per voltage level (an assumption)."""
import sys, json, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from parse_mp import parse
bus, br, names, base = parse(sys.argv[1])
idx = {int(b[0]): i for i, b in enumerate(bus)}
sub = lambda i: names[i].rsplit(" ", 1)[0]
OHM_PER_KM = {500: 0.30, 345: 0.33, 230: 0.40, 161: 0.42, 138: 0.45, 115: 0.45, 100: 0.45, 69: 0.45}
edges = collections.defaultdict(list)
for b in br:
    if b[10] == 0: continue                      # out of service
    f, t = idx[int(b[0])], idx[int(b[1])]
    if sub(f) == sub(t) or bus[f][9] != bus[t][9]: continue   # transformers / same site
    V = bus[f][9]; km = b[3] * V * V / base / OHM_PER_KM.get(int(V), 0.42)
    edges[tuple(sorted((sub(f), sub(t))))].append((km, V))
G = collections.defaultdict(set)
for a, c in edges: G[a].add(c); G[c].add(a)
core = {sub(i) for i, n in enumerate(names) if n.startswith("CHATTANOOGA ")}
ring = set(core)
for s in core: ring |= G[s]
links = [(k, min(e[0] for e in v), max(e[1] for e in v)) for k, v in edges.items() if k[0] in ring and k[1] in ring]
load, kv = collections.Counter(), collections.Counter()
for i, b in enumerate(bus):
    if sub(i) in ring: load[sub(i)] += b[2]; kv[sub(i)] = max(kv[sub(i)], b[9])
json.dump({"subs": sorted(ring), "core": sorted(core), "links": links, "load": load, "kv": kv}, open(sys.argv[2], "w"))
print(len(ring), "substations,", len(links), "links")
