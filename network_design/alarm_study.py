"""Improving the BB84 alarm: window size, and Kalman + CUSUM on drifting line noise.

Error model for one sifted bit (intercept-resend on a fraction f of rounds, line noise p):
    e = f/4 + p(1 - f/2)
  (Eve picks the wrong basis half the time -> Bob's bit is random; otherwise only line noise flips it.)
Check against 3a_bb84_grid_link.ipynb (Aer circuits): p = 0.025, f = 0.5 -> formula 0.144, circuits 0.143.
"""
import numpy as np

def qber(p, f): return f / 4 + p * (1 - f / 2)

# ---------------------------------------------------------------- 1. window size
def window_sweep(p=0.025, Ns=(60, 250, 1000, 4000, 16000, 64000, 256000), z_fa=3.0, target=0.95, trials=4000, seed=0):
    rng = np.random.default_rng(seed); rows = []
    fs = np.concatenate([np.linspace(0, 0.02, 41), np.linspace(0.025, 1, 196)])
    for N in Ns:
        quiet = rng.binomial(N, qber(p, 0), trials) / N
        thr = quiet.mean() + z_fa * quiet.std()
        fmin = None
        for f in fs:
            det = np.mean(rng.binomial(N, qber(p, f), trials) / N > thr)
            if det >= target: fmin = f; break
        sigma = np.sqrt(p * (1 - p) / N)
        predicted = 4 * (z_fa + 1.645) * sigma / (1 - 2 * p)     # alarm margin + 95% detection margin, slope (1-2p)/4
        rows.append(dict(N=N, threshold=thr, false_alarm=float(np.mean(quiet > thr)), f_min=fmin, f_min_formula=predicted))
    return rows

# ---------------------------------------------------------------- 2. drifting noise + small persistent tap
def baseline_path(T, rng, p0=0.025, gusts=True):
    """Line noise that drifts: slow daily-style swing, random walk, and (optionally) wind spikes on aerial fiber."""
    t = np.arange(T)
    walk = np.cumsum(rng.normal(0, 0.00015, T))
    p = p0 + 0.008 * np.sin(2 * np.pi * t / 600 + rng.uniform(0, 6.28)) + walk - walk.mean()
    for s in (rng.choice(T, size=rng.poisson(3), replace=False) if gusts else []):   # wind gusts: short spikes
        p[s:s + 15] += rng.uniform(0.01, 0.02)
    return np.clip(p, 0.005, 0.08)

def detectors(z, N, calib=100, z_fixed=4.0, Q=4e-8, k_sigma=0.5, h_sigma=8.0, freeze_frac=0.5):
    """Alarm arrays (True = alarm raised at that batch) for three detectors.
    fixed        : baseline = mean of the first `calib` quiet batches; alarm if a batch > baseline + z_fixed * sd.
    kalman       : Kalman filter tracks the baseline (random-walk model, Q matched to the drift); alarm if a batch's
                   innovation > z_fixed * predicted sd.
    kalman_cusum : same Kalman baseline; CUSUM adds up standardized excess error, alarm when it passes h_sigma.
                   While CUSUM is building, the baseline is frozen so a slow tap is not absorbed. After an alarm,
                   the link falls back to PQC keys and both are reset (re-learned from the next batches)."""
    T = len(z); out = {k: np.zeros(T, bool) for k in ("fixed", "kalman", "kalman_cusum")}
    m0, s0 = z[:calib].mean(), z[:calib].std()
    out["fixed"] = z > m0 + z_fixed * s0
    R = m0 * (1 - m0) / N
    x, P = m0, R
    xs, Ps, S = m0, R, 0.0
    for t in range(T):
        P += Q; innov = z[t] - x
        out["kalman"][t] = innov > z_fixed * np.sqrt(P + R)
        K = P / (P + R); x += K * innov; P *= (1 - K)
        Ps += Q; sd = np.sqrt(Ps + R); innov = z[t] - xs
        S = max(0.0, S + innov / sd - k_sigma)
        if S > h_sigma:
            out["kalman_cusum"][t] = True; S = 0.0; xs, Ps = z[t], R      # alarm: fall back to PQC, re-learn baseline
        elif S < freeze_frac * h_sigma:
            K = Ps / (Ps + R); xs += K * innov; Ps *= (1 - K)
    return out

def events(a):
    """Rising edges: an alarm event starts when the alarm turns on."""
    return np.flatnonzero(a & ~np.concatenate([[False], a[:-1]]))

def drift_study(f_tap=0.05, N=4000, T=1500, t_tap=900, runs=400, seed=1, gusts=False):
    """Each run: T batches of N sifted bits each. Tap of fraction f_tap starts at t_tap and stays.
    Reports false alarms per 1,000 quiet batches, share of runs where the tap is caught, and median delay (batches)."""
    rng = np.random.default_rng(seed); res = {k: dict(fa=0, detected=0, delays=[]) for k in ("fixed", "kalman", "kalman_cusum")}
    example = None
    for r in range(runs):
        p = baseline_path(T, rng, gusts=gusts)
        f = np.where(np.arange(T) >= t_tap, f_tap, 0.0)
        z = rng.binomial(N, qber(p, f)) / N
        al = detectors(z, N)
        for k, a in al.items():
            ev = events(a)
            res[k]["fa"] += int(((ev >= 100) & (ev < t_tap)).sum())
            after = ev[(ev >= t_tap) & (ev < t_tap + 300)] - t_tap
            if f_tap > 0 and after.size: res[k]["detected"] += 1; res[k]["delays"].append(int(after[0]))
        if example is None: example = dict(p=p, z=z, f=f, alarms={k: v.copy() for k, v in al.items()})
    out = {}
    for k, v in res.items():
        out[k] = dict(false_alarms_per_1000=1000 * v["fa"] / (runs * (t_tap - 100)), detected_share=v["detected"] / runs,  # caught within 300 batches
                      median_delay_batches=float(np.median(v["delays"])) if v["delays"] else None)
    return out, example


def fa_rate(alarm_fn, runs, N, T, rng, gusts):
    tot = 0
    for _ in range(runs):
        p = baseline_path(T, rng, gusts=gusts); z = rng.binomial(N, qber(p, 0.0)) / N
        ev = events(alarm_fn(z)); tot += int((ev >= 100).sum())
    return 1000 * tot / (runs * (T - 100))

def calibrate(N=4000, T=1500, runs=60, target=1.0, gusts=False, seed=5):
    """Find each detector's setting that gives `target` false alarms per 1,000 batches on a quiet drifting link."""
    rng = np.random.default_rng(seed); cfg = {}
    for name, key, grid in [("fixed", "z_fixed", np.arange(3, 20.5, 0.5)), ("kalman", "z_fixed", np.arange(3, 8.1, 0.25)),
                            ("kalman_cusum", "h_sigma", np.arange(6, 40.1, 1.0))]:
        for v in grid:
            r = fa_rate(lambda z: detectors(z, N, **{key: v})[name], runs, N, T, np.random.default_rng(seed), gusts)
            if r <= target: cfg[name] = {key: float(v)}; break
        else: cfg[name] = {key: float(grid[-1])}
    return cfg

def study_calibrated(cfg, f_taps=(0.005, 0.01, 0.02, 0.05), N=4000, T=1500, t_tap=900, runs=200, gusts=False, seed=11):
    rng = np.random.default_rng(seed); out = {}
    for f in f_taps:
        res = {k: dict(fa=0, det=0, d=[]) for k in cfg}
        for _ in range(runs):
            p = baseline_path(T, rng, gusts=gusts); fv = np.where(np.arange(T) >= t_tap, f, 0.0)
            z = rng.binomial(N, qber(p, fv)) / N
            for k, kw in cfg.items():
                ev = events(detectors(z, N, **kw)[k])
                res[k]["fa"] += int(((ev >= 100) & (ev < t_tap)).sum())
                after = ev[(ev >= t_tap) & (ev < t_tap + 300)] - t_tap
                if after.size: res[k]["det"] += 1; res[k]["d"].append(int(after[0]))
        out[f] = {k: dict(false_alarms_per_1000=round(1000 * v["fa"] / (runs * (t_tap - 100)), 2), caught=round(v["det"] / runs, 3),
                          median_delay=float(np.median(v["d"])) if v["d"] else None) for k, v in res.items()}
    return out


# ---------------------------------------------------------------- 3. fusing a classical fiber monitor
def gusty_path(T, rng, p0=0.025, gust_rate=3):
    """Drifting noise plus wind gusts; also returns the true gust mask."""
    t = np.arange(T); walk = np.cumsum(rng.normal(0, 0.00015, T))
    p = p0 + 0.008 * np.sin(2 * np.pi * t / 600 + rng.uniform(0, 6.28)) + walk - walk.mean()
    g = np.zeros(T, bool)
    for s in rng.choice(np.arange(100, T - 20), size=rng.poisson(gust_rate), replace=False):
        L = 15; p[s:s + L] += rng.uniform(0.01, 0.02); g[s:s + L] = True
    return np.clip(p, 0.005, 0.08), g

def monitor(gust, tap_start, T, rng, p_see_gust=0.9, p_see_tap=0.5, p_false_env=0.002):
    """Classical fiber monitor (vibration/polarization + OTDR).
    env[t]  : 'environmental disturbance' flag. Sees a real gust with prob p_see_gust (per gust), plus rare false flags.
    otdr[t] : 'loss step' event. Sees a tap being installed with prob p_see_tap (a careful low-loss tap can avoid it)."""
    env = np.zeros(T, bool); i = 0
    while i < T:
        if gust[i]:
            j = i
            while j < T and gust[j]: j += 1
            if rng.random() < p_see_gust: env[max(0, i - 2):min(T, j + 5)] = True   # flag slightly wider than the gust
            i = j
        else: i += 1
    env |= rng.random(T) < p_false_env
    otdr = np.zeros(T, bool)
    if tap_start is not None and tap_start < T and rng.random() < p_see_tap: otdr[tap_start] = True
    return env, otdr

def fused_cusum(z, N, env, otdr, calib=100, Q=4e-8, k_sigma=0.5, h_sigma=15.0, freeze_frac=0.5, boost=0.4, boost_len=200, hold=True):
    """Kalman + CUSUM with the monitor: hold during flagged disturbances; lower the alarm level after an OTDR loss step."""
    T = len(z); a = np.zeros(T, bool); m0 = z[:calib].mean(); R = m0 * (1 - m0) / N
    x, P, S, boost_until = m0, R, 0.0, -1
    for t in range(T):
        if otdr[t]: boost_until = t + boost_len
        h = h_sigma * (boost if t <= boost_until else 1.0)
        P += Q
        if hold and env[t]: continue                      # disturbance flagged: no evidence, no baseline update
        sd = np.sqrt(P + R); innov = z[t] - x
        S = max(0.0, S + innov / sd - k_sigma)
        if S > h: a[t] = True; S = 0.0; x, P = z[t], R
        elif S < freeze_frac * h:
            K = P / (P + R); x += K * innov; P *= (1 - K)
    return a

def fusion_study(f_tap=0.02, N=4000, T=1500, t_tap=900, runs=300, seed=21, gusts_only_attacker=False, p_see_tap=0.5):
    rng = np.random.default_rng(seed)
    names = ["QBER only (Kalman + CUSUM)", "+ gust hold", "+ gust hold + OTDR boost"]
    res = {n: dict(fa=0, det=0, d=[]) for n in names}
    for _ in range(runs):
        p, g = gusty_path(T, rng)
        if gusts_only_attacker:
            fv = np.where(g & (np.arange(T) >= t_tap), f_tap, 0.0); start = None
            idx = np.flatnonzero(fv > 0); start = int(idx[0]) if idx.size else None
        else:
            fv = np.where(np.arange(T) >= t_tap, f_tap, 0.0); start = t_tap if f_tap > 0 else None
        z = rng.binomial(N, qber(p, fv)) / N
        env, otdr = monitor(g, start, T, rng, p_see_tap=p_see_tap)
        al = {names[0]: detectors(z, N, h_sigma=15.0)["kalman_cusum"],
              names[1]: fused_cusum(z, N, env, np.zeros(T, bool)),
              names[2]: fused_cusum(z, N, env, otdr)}
        for n, a in al.items():
            ev = events(a)
            res[n]["fa"] += int(((ev >= 100) & (ev < t_tap)).sum())
            after = ev[(ev >= t_tap) & (ev < t_tap + 300)] - t_tap
            if f_tap > 0 and after.size: res[n]["det"] += 1; res[n]["d"].append(int(after[0]))
    return {n: dict(false_alarms_per_1000=round(1000 * v["fa"] / (runs * (t_tap - 100)), 2), caught=round(v["det"] / runs, 3),
                    median_delay=float(np.median(v["d"])) if v["d"] else None) for n, v in res.items()}
