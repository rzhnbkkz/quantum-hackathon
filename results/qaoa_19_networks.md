# QAOA vs classical on every network

Instance: one qubit per candidate link on the top substations' paths, sized to 6-14 qubits, budget K = half the links. Exact optimum by brute force (MILP gives the same).
Numbers = chance of sampling the optimal plan, relative to picking a random plan with exactly K links (1.0x = no better than random).

| Network | Qubits | Greedy (fraction of optimum) | Penalty QAOA p=1 / p=2 | XY-mixer QAOA p=1 / p=2 |
|---|---|---|---|---|
| atlanta_r1 | 14 | 0.99 | 0.49x / 0.60x | 1.10x / 1.26x |
| atlanta_r2 | 14 | 0.99 | 0.49x / 0.60x | 1.10x / 1.26x |
| atlanta_r3 | 14 | 0.99 | 0.49x / 0.60x | 1.10x / 1.26x |
| atlanta_r4 | 14 | 1.00 | 0.50x / 0.61x | 3.69x / 2.94x |
| chattanooga_r1 | 14 | 0.90 | 0.49x / 0.59x | 0.64x / 0.44x |
| chattanooga_r2 | 12 | 1.00 | 0.57x / 0.66x | 1.33x / 2.43x |
| huntsville_r1 | 13 | 1.00 | 0.49x / 0.59x | 3.26x / 2.25x |
| huntsville_r2 | 14 | 0.94 | 0.49x / 0.59x | 7.98x / 10.89x |
| ieee_30 | 6 | 1.00 | 0.71x / 0.74x | 1.95x / 6.10x |
| ieee_300 | 7 | 1.00 | 0.66x / 0.78x | 1.77x / 4.17x |
| ieee_57 | 9 | 1.00 | 0.62x / 0.68x | 0.78x / 0.39x |
| knoxville_r1 | 14 | 0.91 | 0.50x / 0.60x | 3.58x / 2.78x |
| knoxville_r2 | 13 | 1.00 | 0.50x / 0.59x | 2.65x / 0.66x |
| memphis_r1 | 14 | 0.74 | 0.50x / 0.60x | 2.32x / 0.87x |
| memphis_r2 | 12 | 1.00 | 0.55x / 0.64x | 2.74x / 6.72x |
| memphis_r3 | 12 | 1.00 | 0.55x / 0.64x | 2.74x / 6.72x |
| memphis_r4 | 12 | 1.00 | 0.55x / 0.64x | 2.74x / 6.72x |
| nashville_r1 | 14 | 0.97 | 0.49x / 0.59x | 1.24x / 2.71x |
| nashville_r2 | 14 | 1.00 | 0.49x / 0.60x | 2.51x / 2.98x |

- 19 networks. Penalty QAOA did worse than random on all of them (median 0.60x): most of its probability lands on plans that break the budget.
- XY-mixer QAOA beat random on 17/19 (median best 3.0x), but it never reached certainty. Exact MILP finds the optimum every time in under a second, and greedy reaches ≥ 0.90 of the optimum on 17/19.
- Conclusion: at this size the planning step stays classical. QAOA is a research benchmark here, not the tool.