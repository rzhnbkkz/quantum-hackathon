# Hardware runs: what to run and where

Open the notebooks on qBraid Lab from this folder (they look for `network_design/` next to them). Kernel: **qBraid-SDK (v0.12.2)**. Every job ID a cell prints goes in the Run Record in `WRITEUP.md`, failed jobs included.

## 1. Free runs (do these)

| Notebook | Cell | Devices | Jobs | What it adds |
|---|---|---|---|---|
| `3f_attacks_on_hardware.ipynb` | Run all | qBraid QIR sim, IonQ sim (noise), Quantinuum H2 emulator | 1 QRNG + 4 per device (blinding reuses the tap job) | Attack table across 3 backends. **Accept Quantinuum's terms first** (Devices → Quantinuum H2 emulator). |
| `3e_qaoa_vs_classical.ipynb` | "Run the 10-qubit circuit through qBraid" | qBraid QIR sim, IonQ sim | 2 | QAOA job IDs for the Stretch |
| `3a_bb84_grid_link.ipynb` | Section 4 | qBraid QIR sim, IonQ sim | 4 | Already run (job IDs in the run record). Rerun only if you want fresh ones. |

The last cell of 3f prints run-record rows ready to paste.

## 2. Real hardware (pick one, ask a mentor first)

In `3f_attacks_on_hardware.ipynb`, section 3, uncomment **one** QPU line in `BACKENDS`. Circuits that don't fit a device are skipped automatically.

| Device | Qubits | Fits | Why pick it |
|---|---|---|---|
| `openquantum:ionq:qpu:forte-1` | 36 | all 5 attacks | **Best choice.** Same machine as Step 1's no-Eve run (QBER 0.004), so the attack results compare directly. |
| `openquantum:iqm:qpu:emerald` | 54 | all 5 | Superconducting: a second noise profile to compare with Forte |
| `openquantum:iqm:qpu:garnet` | 20 | quiet, partial, dos | |
| `openquantum:aqt:qpu:ibex-q1` | 12 | quiet, dos | |

- Use the **account that ran Step 1's Forte job**: it has Open Quantum connected and the terms accepted. Earlier Forte jobs failed because those steps weren't done (see the run record).
- Open Quantum rejected a circuit with an idle qubit before. `hw_attacks.py` now gives every qubit a gate and only adds Eve qubits for tapped rounds.
- qBraid lists Open Quantum devices at 0 qBraid credits. Billing goes through the Open Quantum hackathon access, so confirm with a mentor. For comparison, Rigetti on AWS (`aws:rigetti:qpu:cepheus-1-108q`) is about 39 credits per 200-shot job.
- Hardware jobs can sit in a queue. If `job.result()` waits too long, stop the cell, note the job ID, and fetch it later with `from qbraid.runtime import QbraidJob; QbraidJob("<job id>").result()`.

## 3. After running

1. Paste the printed rows into the Run Record in `WRITEUP.md`, replacing the `[FILL]` rows.
2. Replace `[FILL: real-QPU result from 3f if run.]` in Step 3, Part 3 with one sentence, e.g. "On IonQ Forte 1 the quiet link gave QBER X and the full tap Y; blinding kept QBER at Z with click yield W."
3. If no QPU run happened, delete that `[FILL]` sentence.

## What's in `network_design/`

Tools used by the notebooks (`hw_attacks.py`, `v1_model.py`, `v11.py`, `final_design.py`, `qaoa_study.py`, `alarm_study.py`, ...), the Chattanooga grid extract (`chatt_raw.json`), and the 21 test networks (`regions/`). Cross-network results are summarized in `results/`.
