"""E91 (CHSH), six-state QKD and entanglement swapping: circuit builders and scorers.
Each circuit packs several independent rounds side by side, so one job covers every setting.
Bit order: qiskit/qBraid count strings are little-endian (clbit 0 is the rightmost character)."""
import math, json
PI = math.pi
# CHSH settings: Alice angle a, Bob angle b (measurement axis in the X-Z plane)
CHSH = [(0, PI/4), (0, -PI/4), (PI/2, PI/4), (PI/2, -PI/4)]
SIGN = [1, 1, 1, -1]

def _hdr(nq, nc): return ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{nq}];', f'creg c[{nc}];']

def e91(mode="quiet"):
    """mode: quiet | tap (Eve copies Bob's qubit in Z) | blind (Eve measures in Bob's own basis, as a blinding attack does)."""
    nq = 8 + (4 if mode != "quiet" else 0); L = _hdr(nq, nq)
    for k, (a, b) in enumerate(CHSH):
        A, B, E = 2*k, 2*k+1, 8+k
        L += [f'h q[{A}];', f'cx q[{A}],q[{B}];']
        if mode == "tap": L += [f'cx q[{B}],q[{E}];']
        if mode == "blind": L += [f'ry({-b}) q[{B}];', f'cx q[{B}],q[{E}];', f'ry({b}) q[{B}];']
        L += [f'ry({-a}) q[{A}];', f'ry({-b}) q[{B}];']
    L += [f'measure q[{i}] -> c[{i}];' for i in range(nq)]
    return "\n".join(L)

def _bits(key, n): return [int(ch) for ch in key[::-1][:n]]   # clbit i

def corr(counts, ia, ib):
    tot = sum(counts.values()); s = 0
    for k, v in counts.items():
        b = _bits(k, max(ia, ib)+1); s += v * (1 if b[ia] == b[ib] else -1)
    return s / tot

def mean_bit(counts, i):
    tot = sum(counts.values()); return sum(v * (1 - 2*_bits(k, i+1)[i]) for k, v in counts.items()) / tot

def chsh(counts, pairs=None, yield_=1.0):
    """S = E00 + E01 + E10 - E11. pairs: list of (alice clbit, bob clbit) per setting.
    yield_<1: the missing rounds give no click; Bob records +1 for them (detection-loophole-free counting)."""
    pairs = pairs or [(2*k, 2*k+1) for k in range(4)]
    E = []
    for k, (ia, ib) in enumerate(pairs):
        e = corr(counts, ia, ib)
        E.append(yield_ * e + (1 - yield_) * mean_bit(counts, ia))
    return sum(s*e for s, e in zip(SIGN, E)), E

def eve_match(counts, k):
    tot = sum(counts.values()); return sum(v for key, v in counts.items() if _bits(key, 12)[2*k+1] == _bits(key, 12)[8+k]) / tot

# ---------------- six-state vs BB84 (sifted rounds only: Bob always uses Alice's basis)
ROT_IN = {"Z": [], "X": ["h"], "Y": ["h", "s"]}          # |bit> -> state in basis
ROT_OUT = {"Z": [], "X": ["h"], "Y": ["sdg", "h"]}       # basis -> Z
def prep_measure(bases, bits, eve=None):
    n = len(bases); nq = n + (n if eve else 0); L = _hdr(nq, nq)
    for r, (B, x) in enumerate(zip(bases, bits)):
        if x: L.append(f'x q[{r}];')
        L += [f'{g} q[{r}];' for g in ROT_IN[B]]
        if eve:
            e = eve[r]; L += [f'{g} q[{r}];' for g in ROT_OUT[e]]; L.append(f'cx q[{r}],q[{n+r}];')
            L += [f'{g} q[{r}];' for g in ROT_IN[e]]          # Eve resends in her basis (copy model)
        L += [f'{g} q[{r}];' for g in ROT_OUT[B]]
    L += [f'measure q[{i}] -> c[{i}];' for i in range(nq)]
    return "\n".join(L)

def qber(counts, bits):
    n = len(bits); tot = sum(counts.values()); err = 0
    for k, v in counts.items():
        b = _bits(k, n); err += v * sum(b[i] != bits[i] for i in range(n))
    return err / (tot * n)

# ---------------- entanglement swapping: Alice - relay(s) - Bob, then CHSH across the chain
def swap_chsh(relays=1):
    per = 2 + 2*relays; nq = 4*per; L = _hdr(nq, nq)
    for k, (a, b) in enumerate(CHSH):
        o = k*per; q = list(range(o, o+per))        # pairs (q0,q1), (q2,q3), ...
        for j in range(0, per, 2): L += [f'h q[{q[j]}];', f'cx q[{q[j]}],q[{q[j+1]}];']
        for r in range(relays):                     # relay r holds q[2r+1], q[2r+2]; swap pair ends onto q[0] and q[2r+3]
            r1, r2, far = q[2*r+1], q[2*r+2], q[2*r+3]
            L += [f'cx q[{r1}],q[{r2}];', f'h q[{r1}];', f'cx q[{r2}],q[{far}];', f'cz q[{r1}],q[{far}];']   # Bell measurement + corrections (deferred)
        L += [f'ry({-a}) q[{q[0]}];', f'ry({-b}) q[{q[-1]}];']
    L += [f'measure q[{i}] -> c[{i}];' for i in range(nq)]
    return "\n".join(L), [(k*per, k*per+per-1) for k in range(4)], [[k*per+j for j in range(1, per-1)] for k in range(4)]

def relay_info(counts, alice_bits, relay_bits):
    """Mutual information (bits) between Alice's key bit and everything the relays saw: ~0 means the relays learn nothing."""
    from collections import Counter
    tot = sum(counts.values()); I = 0
    for ia, rb in zip(alice_bits, relay_bits):
        j = Counter()
        for key, v in counts.items():
            b = _bits(key, max([ia]+rb)+1); j[(b[ia], tuple(b[i] for i in rb))] += v
        pa = Counter(); pr = Counter()
        for (x, r), v in j.items(): pa[x] += v; pr[r] += v
        I += sum(v/tot * math.log2((v/tot) / (pa[x]/tot * pr[r]/tot)) for (x, r), v in j.items())
    return I / len(alice_bits)
