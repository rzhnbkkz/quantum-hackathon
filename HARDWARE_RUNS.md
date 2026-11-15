# qBraid runs: what was run, and how to rerun it

Every job ID is in the Run Record at the end of `WRITEUP.md`. Open notebooks in qBraid Lab from this folder (kernel: **qBraid-SDK**). They expect `network_design/` next to them.

## Done

| Run | Device | Result |
|---|---|---|
| BB84, no eavesdropper (Step 1) | IonQ Forte 1 (QPU) | QBER 0.004 |
| Attacks: full tap, partial tap; blinding scored from the tap job (3f) | **IonQ Forte 1 (QPU)** | 0.171 / 0.085 / 0.003 with 67% click yield. Noise-free prediction for the same key: 0.167 / 0.084 / 0.000 |
| Five attacks (3f) | IonQ simulator (noise), Quantinuum H2 emulator, QIR simulator | Tap 0.24–0.26; blinding 0.000 QBER at 50% yield; jamming about 0.87 |
| Whole design, 8 QKD links in one 27-qubit circuit (3h) | **qBraid GPU simulator** | 7 quiet links 0.000; tapped link 0.331 (expected 0.333) |
| E91 Bell test, six-state, entanglement swapping (3j) | **qBraid GPU simulator** | E91: S 2.78 quiet, 1.40 tapped; six-state tap 0.329 vs BB84 0.253; swapping S 2.80 (1 relay), 2.86 (2 relays) |
| QAOA, 10 qubits (3e) | QIR simulator, IonQ simulator | Best plan in 0.10% of shots |
| Grid link quiet/tapped (3a) | QIR simulator, IonQ simulator | 0.000 / 0.419–0.425 |

## Rerunning

- **3f on hardware:** in section 3, set `BACKENDS` to the device you want. Open Quantum devices need your Open Quantum account linked under qBraid Account → Profile → Integrations, and they bill Open Quantum credits. Don't rerun the random-bits cell between submissions, or the key changes.
- **3h:** export a design from `qkd_grid_optimizer.html` (*Download design JSON*), put `grid_design.json` next to the notebook, and run all cells. Without it, the notebook uses `network_design/grid_design_default.json`. Cost: about 0.25 qBraid credits.
- **3i:** needs your qBraid API key for the AI Gateway.
- **3j:** runs on the GPU simulator by default. In `BACKENDS`, uncomment the IonQ simulator line for Forte noise, or Forte itself (real hardware: check with your team first). Every circuit fits in 24 qubits.
- Long hardware queues: note the job ID, then fetch the result later with `from qbraid.runtime import QbraidJob; QbraidJob("<id>").result()`.
