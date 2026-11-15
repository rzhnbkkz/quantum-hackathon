# Attack results across 21 networks and 3 budgets

Budget K links / T trusted nodes. Percentages are of the network's total load (MW). 'Worst tap cut' = how much the balanced design shrinks the worst single tap vs PQC-only.

| Network | Subs | QKD-feasible links | Worst tap cut K4/K8/K16 | Taps landing on QKD fiber (K16) | Blinding worst, no fix → with fix (K16) | 2 trusted nodes lost: no split → split (K16) | DoS service lost | 1 cut before → after backup | 2 cuts before → after |
|---|---|---|---|---|---|---|---|---|---|
| atlanta_r1 | 73 | 103/103 | 28% / 56% / 56% | 18% | 55% → 6% | 12% → 8% | 0 MW | 9% → 0% | 17% → 13% |
| atlanta_r2 | 92 | 125/129 | 34% / 61% / 64% | 11% | 52% → 5% | 8% → 5% | 0 MW | 8% → 0% | 14% → 11% |
| atlanta_r3 | 135 | 193/210 | 35% / 70% / 72% | 4% | 58% → 6% | 8% → 4% | 0 MW | 2% → 0% | 4% → 3% |
| atlanta_r4 | 204 | 289/318 | 0% / 49% / 49% | 3% | 64% → 6% | 4% → 4% | 0 MW | 2% → 0% | 3% → 2% |
| chattanooga_r1 | 49 | 58/65 | 0% / 48% / 48% | 16% | 46% → 5% | 24% → 18% | 0 MW | 5% → 0% | 10% → 9% |
| chattanooga_r2 | 76 | 82/99 | 38% / 55% / 55% | 9% | 34% → 3% | 16% → 15% | 0 MW | 5% → 0% | 10% → 6% |
| huntsville_r1 | 43 | 51/55 | 22% / 22% / 76% | 19% | 34% → 3% | 19% → 18% | 0 MW | 6% → 0% | 8% → 7% |
| huntsville_r2 | 73 | 78/88 | 61% / 66% / 67% | 11% | 46% → 5% | 16% → 13% | 0 MW | 9% → 0% | 13% → 6% |
| ieee_118 | 107 | 51/167 | 0% / 0% / 0% | 4% | 23% → 2% | 1% → 1% | 0 MW | 2% → 0% | 4% → 4% |
| ieee_14 | 11 | 2/16 | 0% / 0% / 0% | 2% | 7% → 1% | 0% → 0% | 0 MW | 0% → 0% | 36% → 36% |
| ieee_30 | 30 | 8/41 | 28% / 28% / 28% | 4% | 19% → 2% | 1% → 1% | 0 MW | 2% → 0% | 16% → 16% |
| ieee_300 | 171 | 133/258 | 0% / 1% / 1% | 2% | 46% → 5% | 2% → 2% | 0 MW | 7% → 0% | 26% → 11% |
| ieee_57 | 42 | 19/62 | 30% / 30% / 30% | 7% | 39% → 4% | 7% → 7% | 0 MW | 0% → 0% | 3% → 3% |
| knoxville_r1 | 59 | 65/73 | 41% / 47% / 50% | 15% | 52% → 5% | 17% → 10% | 0 MW | 5% → 0% | 15% → 10% |
| knoxville_r2 | 81 | 85/100 | 0% / 47% / 50% | 9% | 44% → 4% | 12% → 7% | 0 MW | 8% → 0% | 16% → 7% |
| memphis_r1 | 84 | 117/124 | 6% / 42% / 65% | 11% | 40% → 4% | 11% → 9% | 0 MW | 2% → 0% | 7% → 4% |
| memphis_r2 | 114 | 149/164 | 1% / 63% / 63% | 8% | 67% → 7% | 9% → 7% | 0 MW | 3% → 0% | 6% → 3% |
| memphis_r3 | 146 | 185/206 | 1% / 63% / 63% | 6% | 66% → 7% | 8% → 6% | 0 MW | 1% → 0% | 3% → 3% |
| memphis_r4 | 183 | 219/249 | 0% / 64% / 64% | 4% | 65% → 6% | 6% → 6% | 0 MW | 2% → 0% | 4% → 3% |
| nashville_r1 | 59 | 67/73 | 4% / 19% / 25% | 14% | 47% → 5% | 12% → 9% | 0 MW | 7% → 0% | 14% → 14% |
| nashville_r2 | 85 | 91/103 | 3% / 3% / 23% | 11% | 41% → 4% | 8% → 7% | 0 MW | 6% → 0% | 12% → 9% |

**Medians over the 21 networks with any QKD-feasible link:**
- Worst single tap shrinks 4% (K4), 47% (K8), 50% (K16).
- Share of random taps landing on QKD fiber (K16): 9%. Everything else needs classical fiber monitoring.
- Detector blinding, worst case (K16): 46% of load exposed with no countermeasure, 5% with one.
- Two trusted nodes lost (K16): 8% → 7% with key splitting.
- DoS service loss: 0 MW on every network (keys fall back to PQC).
- One fiber cut: 5% → 0% after backup routes. Two cuts: 10% → 7% (the remaining gap).