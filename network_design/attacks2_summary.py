import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = json.load(open("attacks2/attacks2_all.json")); B = ["K4_T2", "K8_T4", "K16_T8"]
pct = lambda x, t: 100 * x / t if t else 0
rows = []
for d in D:
    T = d["total_mw"]; r = dict(net=d["net"], subs=d["substations"], qkd_ok=d["qkd_feasible_links"], links=d["links"])
    for b in B:
        p, q = d["budgets"][b]["pqc_only"], d["budgets"][b]["balanced"]
        r[b] = dict(worst_tap_cut=1 - q["worst_tap_mw"] / p["worst_tap_mw"] if p["worst_tap_mw"] else 0,
                    taps_on_qkd=q["taps_on_qkd"], secrecy=pct(q["secrecy_mw"], T),
                    blind_no_cm=pct(q["blinding"]["worst_mw_no_countermeasure"], T), blind_cm=pct(q["blinding"]["worst_expected_mw_with_countermeasure"], T),
                    dos_service=q["dos"]["service_lost_mw"], tn2_nosplit=pct(q["trusted_nodes"]["no_split"]["worst_2_nodes_mw"], T),
                    tn2_split=pct(q["trusted_nodes"]["with_split"]["worst_2_nodes_mw"], T))
    c = d["cuts"]; r["cut1_before"], r["cut1_after"] = pct(c["before_backup"]["worst_1_cut_mw"], T), pct(c["after_backup"]["worst_1_cut_mw"], T)
    r["cut2_before"], r["cut2_after"], r["backup_links"] = pct(c["before_backup"]["worst_2_cuts_mw"], T), pct(c["after_backup"]["worst_2_cuts_mw"], T), c["backup_links"]
    rows.append(r)
L = ["# Attack results across 21 networks and 3 budgets", "",
     "Budget K links / T trusted nodes. Percentages are of the network's total load (MW). 'Worst tap cut' = how much the balanced design shrinks the worst single tap vs PQC-only.", "",
     "| Network | Subs | QKD-feasible links | Worst tap cut K4/K8/K16 | Taps landing on QKD fiber (K16) | Blinding worst, no fix → with fix (K16) | 2 trusted nodes lost: no split → split (K16) | DoS service lost | 1 cut before → after backup | 2 cuts before → after |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    k = r["K16_T8"]
    L.append(f"| {r['net']} | {r['subs']} | {r['qkd_ok']}/{r['links']} | {r['K4_T2']['worst_tap_cut']:.0%} / {r['K8_T4']['worst_tap_cut']:.0%} / {k['worst_tap_cut']:.0%} | {k['taps_on_qkd']:.0%} | "
             f"{k['blind_no_cm']:.0f}% → {k['blind_cm']:.0f}% | {k['tn2_nosplit']:.0f}% → {k['tn2_split']:.0f}% | {k['dos_service']:.0f} MW | {r['cut1_before']:.0f}% → {r['cut1_after']:.0f}% | {r['cut2_before']:.0f}% → {r['cut2_after']:.0f}% |")
act = [r for r in rows if r["qkd_ok"] > 0]
med = lambda f: np.median([f(r) for r in act])
L += ["", f"**Medians over the {len(act)} networks with any QKD-feasible link:**",
      f"- Worst single tap shrinks {med(lambda r:r['K4_T2']['worst_tap_cut']):.0%} (K4), {med(lambda r:r['K8_T4']['worst_tap_cut']):.0%} (K8), {med(lambda r:r['K16_T8']['worst_tap_cut']):.0%} (K16).",
      f"- Share of random taps landing on QKD fiber (K16): {med(lambda r:r['K16_T8']['taps_on_qkd']):.0%}. Everything else needs classical fiber monitoring.",
      f"- Detector blinding, worst case (K16): {med(lambda r:r['K16_T8']['blind_no_cm']):.0f}% of load exposed with no countermeasure, {med(lambda r:r['K16_T8']['blind_cm']):.0f}% with one.",
      f"- Two trusted nodes lost (K16): {med(lambda r:r['K16_T8']['tn2_nosplit']):.0f}% → {med(lambda r:r['K16_T8']['tn2_split']):.0f}% with key splitting.",
      f"- DoS service loss: {max(r['K16_T8']['dos_service'] for r in rows):.0f} MW on every network (keys fall back to PQC).",
      f"- One fiber cut: {med(lambda r:r['cut1_before']):.0f}% → {med(lambda r:r['cut1_after']):.0f}% after backup routes. Two cuts: {med(lambda r:r['cut2_before']):.0f}% → {med(lambda r:r['cut2_after']):.0f}% (the remaining gap)."]
open("attacks2/summary.md", "w").write("\n".join(L)); print("\n".join(L))
fig, ax = plt.subplots(figsize=(7, 4)); x = np.arange(3)
for r in act: ax.plot(x, [r[b]["worst_tap_cut"] * 100 for b in B], color="#999", lw=0.8, alpha=0.6)
ax.plot(x, [np.median([r[b]["worst_tap_cut"] * 100 for r in act]) for b in B], color="#1f5fa8", lw=3, marker="o", label="median")
ax.set_xticks(x, ["4 links / 2 nodes", "8 / 4", "16 / 8"]); ax.set_ylabel("worst single tap reduced (%)")
ax.set_title(f"Balanced design vs PQC-only, {len(act)} networks"); ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("attacks2/worst_tap_by_budget.png", dpi=150)
