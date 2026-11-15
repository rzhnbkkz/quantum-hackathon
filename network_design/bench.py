import sys, json, glob, time, signal
sys.path.insert(0, '/home/claude/tools')
from v11 import *
rows = []
class TO(Exception): pass
def handler(*a): raise TO()
signal.signal(signal.SIGALRM, handler)
nets = sorted(glob.glob('/home/claude/griddata/regions/*.json'))
for H in (3, 4, 5):
    for f in nets:
        try:
            signal.alarm(240); n = Net(f, H=H); signal.alarm(0)
        except TO:
            print('build timeout', f, H, flush=True); continue
        size = dict(net=n.name, subs=n.G.number_of_nodes(), links=n.G.number_of_edges(), H=H, targets=len(n.paths),
                    paths=sum(len(v) for v in n.paths.values()), relays=len(n.relays))
        for K, T in ((8, 4), (15, 8), (25, 12), (40, 20)):
            try:
                signal.alarm(300); r = run_all(n, K, T); signal.alarm(0)
            except TO:
                print('timeout', n.name, H, K, flush=True); continue
            opt = r['milp']['value']
            rows.append(dict(size, K=K, T=T, **{f'{a}_gap': (opt - d['value']) / opt if opt > 0 else 0 for a, d in r.items()},
                             **{f'{a}_sec': d['seconds'] for a, d in r.items()}))
            print(n.name, H, K, T, size['paths'], ' '.join(f"{a}:{100*rows[-1][a+'_gap']:.1f}%/{d['seconds']:.2f}s" for a, d in r.items() if a in ('milp','lp_round','greedy','greedy_ls','anneal','genetic')), flush=True)
        json.dump(rows, open('/home/claude/bench/bench.json', 'w'))
print('DONE', flush=True)
