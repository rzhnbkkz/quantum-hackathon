"""Convert a MATPOWER IEEE case into the substation-network format used by v11.Net.
Buses joined by a transformer (branch tap ratio != 0, or different base kV) are merged into one substation.
Line length is estimated from reactance at typical ohm/km for its voltage; cases with no base kV (IEEE 14, 57)
are assumed to be 138 kV. Every substation counts as 'core' (the control-center proxies are picked from all of them).
Usage: python extract_ieee.py case118.m out.json"""
import sys, json, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re

OHM_PER_KM = {765: 0.27, 500: 0.30, 345: 0.33, 230: 0.40, 161: 0.42, 138: 0.45, 135: 0.45, 115: 0.45, 100: 0.45, 69: 0.45}

def mat(txt, name):
    m = re.search(r"mpc\." + name + r"\s*=\s*\[(.*?)\];", txt, re.S); rows = []
    for line in m.group(1).split("\n"):
        line = line.split("%")[0].strip().rstrip(";")
        if line: rows.append([float(v) for v in line.split()])
    return rows

def convert(path):
    txt = open(path).read(); base = float(re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)", txt).group(1))
    bus, br = mat(txt, "bus"), mat(txt, "branch")
    kv = {int(b[0]): (b[9] if b[9] > 0 else 138.0) for b in bus}
    load = {int(b[0]): b[2] for b in bus}
    parent = {b: b for b in kv}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for b in br:
        f, t = int(b[0]), int(b[1])
        if b[10] == 0: continue
        if b[8] != 0 or kv[f] != kv[t]: parent[find(f)] = find(t)      # transformer: same substation
    name = lambda b: f"S{find(b)}"
    edges = collections.defaultdict(list)
    for b in br:
        f, t = int(b[0]), int(b[1])
        if b[10] == 0 or name(f) == name(t): continue
        V = kv[f]; km = max(0.5, b[3] * V * V / base / OHM_PER_KM.get(int(V), 0.45))
        edges[tuple(sorted((name(f), name(t))))].append((km, V))
    subs = sorted({name(b) for b in kv})
    L, K = collections.Counter(), collections.Counter()
    for b in kv: L[name(b)] += load[b]; K[name(b)] = max(K[name(b)], kv[b])
    links = [(k, min(e[0] for e in v), max(e[1] for e in v)) for k, v in edges.items()]
    return {"city": os.path.basename(path).replace(".m", ""), "subs": subs, "core": subs, "links": links, "load": L, "kv": K}

if __name__ == "__main__":
    r = convert(sys.argv[1]); json.dump(r, open(sys.argv[2], "w"))
    km = sorted(l[1] for l in r["links"])
    print(f"{r['city']}: {len(r['subs'])} substations, {len(r['links'])} links, median {km[len(km)//2]:.1f} km, max {km[-1]:.1f} km")
