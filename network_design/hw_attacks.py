"""BB84 attack circuits for real or emulated quantum backends (one circuit per attack, so one job each).

Each round k uses qubit k (the link) and, if Eve is present, qubit R + k (Eve's copy, made with a CNOT in her basis:
for Bob this is the same as Eve measuring and resending). Attacks:
  quiet     : no Eve
  tap       : intercept-resend on every round
  partial   : intercept-resend on a fraction of rounds
  blinding  : Eve taps every round AND controls Bob's detectors: Bob only gets a result when his basis equals Eve's
              (otherwise no click). Emulated by dropping those rounds in post-processing. QBER stays near 0,
              but the share of rounds that click falls: that drop is what a click-rate monitor catches.
  dos       : Eve scrambles every qubit (random X and Z), forcing QBER near 50% so the link aborts and falls back to PQC.
"""
import numpy as np
from qiskit import QuantumCircuit

def make_round_choices(R, seed=None, bits=None):
    rng = np.random.default_rng(seed)
    if bits is None: bits = rng.integers(0, 2, (3, R))
    a, ab, bb = (np.array(x) for x in bits)
    eb = rng.integers(0, 2, R); xs = rng.integers(0, 2, R); zs = rng.integers(0, 2, R)
    return dict(a=a, ab=ab, bb=bb, eb=eb, xs=xs, zs=zs)

def circuit(ch, attack="quiet", frac=1.0, seed=0):
    R = len(ch["a"]); rng = np.random.default_rng(seed)
    eve = attack in ("tap", "partial", "blinding")
    if attack == "partial":
        # exactly round(frac*R) tapped rounds; with only 12 rounds, force one onto a sifted round
        # so the short demo isn't empty (on a real link thousands of rounds make this automatic)
        k = max(1, round(frac * R)); sifted = np.flatnonzero(ch["ab"] == ch["bb"])
        first = rng.choice(sifted) if len(sifted) else rng.integers(R)
        rest = rng.permutation([q for q in range(R) if q != first])[:k - 1]
        tapped = np.zeros(R, bool); tapped[[first, *rest]] = True
    else:
        tapped = np.full(R, eve)
    # Eve's copy qubits only for tapped rounds, so no qubit sits idle (Open Quantum rejects circuits with unused qubits)
    eve_q = {q: R + i for i, q in enumerate(np.flatnonzero(tapped))}
    qc = QuantumCircuit(R + len(eve_q), R)
    for q in range(R):
        used = False
        if ch["a"][q]: qc.x(q); used = True
        if ch["ab"][q]: qc.h(q); used = True
        if tapped[q]:
            if ch["eb"][q]: qc.h(q)
            qc.cx(q, eve_q[q]); used = True
            if ch["eb"][q]: qc.h(q)
        if attack == "dos":
            if ch["xs"][q]: qc.x(q); used = True
            if ch["zs"][q]: qc.z(q); used = True
            if ch["xs"][q] ^ ch["zs"][q]: qc.h(q); used = True
        if ch["bb"][q]: qc.h(q); used = True
        if not used: qc.id(q)          # same fix as Step 1's hardware run: every qubit gets a gate
    qc.measure(range(R), range(R))
    return qc, tapped

def score(counts, ch, attack, tapped):
    """QBER on sifted rounds, and the share of matched-basis rounds that produce a click (yield)."""
    R = len(ch["a"]); keep = [q for q in range(R) if ch["ab"][q] == ch["bb"][q]]
    if attack == "blinding":   # no click when Bob's basis differs from Eve's (Eve controls the detector)
        clicks = [q for q in keep if not tapped[q] or ch["bb"][q] == ch["eb"][q]]
    else: clicks = keep
    err = tot = 0
    for bs, c in counts.items():
        bob = bs.replace(" ", "").zfill(R)[::-1]
        for q in clicks: err += c * (int(bob[q]) != ch["a"][q]); tot += c
    return dict(qber=err / tot if tot else float("nan"), click_yield=len(clicks) / max(1, len(keep)), sifted_rounds=len(clicks))

def qrng_bits(counts, R):
    """Turn the outcomes of an H-then-measure circuit into Alice's bits and bases and Bob's bases (3 x R bits)."""
    stream = []
    for bs, c in counts.items(): stream += [int(b) for b in bs.replace(" ", "")] * c
    stream = (stream * ((3 * R) // max(1, len(stream)) + 1))[:3 * R]
    return np.array(stream).reshape(3, R)
