#!/usr/bin/env python3
"""DECISION 40 — reconcile Addition 7's runs.csv against sweep_summary.csv.

Row for row, on the ten columns the order names: seed, protocol, phy, committed,
aborted, avg_latency, listen, flood, sleep, end_slot. The reference point
(N=27, random, 5 % loss) appears in BOTH published sweeps, so all three sources
are compared against each other and every differing cell is printed.

Also resolves charge 16's four moved numbers by naming the estimator behind each.
"""
import json

import numpy as np
import pandas as pd

WORK = "/tmp/ctsim_validate/addition7"
REPO = "/Users/amir/Projects/ctsim"
N = 27
T14 = 2.144787
ARMS = ["tom_pipeline", "paxos_pipeline", "2pc_pipeline",
        "tom_ce", "paxos_ce", "2pc_ce"]

r = pd.read_csv(f"{WORK}/runs.csv")
r["aborted_plus_timedout"] = r.proposals - r.committed
r["avg_latency_2dp"] = r.mean_latency.round(2)

out = {}


def slice_sweep(path):
    d = pd.read_csv(path)
    d = d[(d.nodes == N) & (d.topology == "random") & (d.loss_rate == 0.05)].copy()
    d["aborted_plus_timedout"] = d.aborted + d.timed_out
    d["simulated_slots"] = (d.listen + d.flood + d.sleep) // d.nodes
    d["drain_slots"] = d.simulated_slots - d.end_slot
    return d


sw = {n: slice_sweep(f"{REPO}/plots/{n}/results/sweep_summary.csv")
      for n in ("scalability", "topology")}

# ---------------------------------------------------------------- the row-for-row diff
COLS = ["committed", "aborted_plus_timedout", "avg_latency_2dp",
        "listen", "flood", "sleep", "end_slot"]
diff = {}
for name, d in sw.items():
    a = r.set_index(["protocol", "seed"]).sort_index()
    b = d.set_index(["protocol", "seed"]).sort_index()
    b["avg_latency_2dp"] = b.avg_latency.round(2)
    common = a.index.intersection(b.index)
    cells, ncmp = [], 0
    for col in COLS:
        x, y = a.loc[common, col], b.loc[common, col]
        ncmp += len(common)
        for idx in common:
            u, v = x.loc[idx], y.loc[idx]
            if not np.isclose(float(u), float(v), rtol=0, atol=1e-9):
                cells.append({"protocol": idx[0], "seed": int(idx[1]), "column": col,
                              "runs_csv": float(u), "sweep": float(v),
                              "delta": float(u) - float(v)})
    # phy must agree too
    phy_bad = [(p, int(s)) for (p, s) in common
               if a.loc[(p, s), "phy"] != b.loc[(p, s), "phy"]]
    diff[name] = {
        "rows_compared": int(len(common)),
        "cells_compared": ncmp,
        "cells_differing": len(cells),
        "phy_mismatches": phy_bad,
        "differing": cells[:60],
        "CLEAN": len(cells) == 0 and not phy_bad,
    }
out["row_for_row_diff"] = diff

# the two published sweeps against each other at the shared point
a = sw["scalability"].set_index(["protocol", "seed"]).sort_index()
b = sw["topology"].set_index(["protocol", "seed"]).sort_index()
common = a.index.intersection(b.index)
inter = []
for col in ["committed", "aborted_plus_timedout", "listen", "flood", "sleep",
            "end_slot", "avg_latency"]:
    for idx in common:
        u, v = float(a.loc[idx, col]), float(b.loc[idx, col])
        if u != v:
            inter.append({"protocol": idx[0], "seed": int(idx[1]), "column": col,
                          "scalability": u, "topology": v})
out["sweep_vs_sweep"] = {"rows_compared": int(len(common)),
                         "cells_differing": len(inter),
                         "differing": inter[:40],
                         "CLEAN": len(inter) == 0}

# derived quantities that are not columns of either file
der = {}
for arm in ARMS:
    gr = r[r.protocol == arm].set_index("seed").sort_index()
    gs = sw["scalability"][sw["scalability"].protocol == arm].set_index("seed").sort_index()
    der[arm] = {
        "simulated_slots_agree": bool((gr.simulated_slots.values
                                       == gs.simulated_slots.values).all()),
        "drain_slots_agree": bool((gr.drain_slots.values == gs.drain_slots.values).all()),
        "runs_drain_total": int(gr.drain_slots.sum()),
        "sweep_drain_total": int(gs.drain_slots.sum()),
    }
out["derived_from_columns"] = der

# ---------------------------------------------------------------- charge 16, item by item
c16 = {}
for arm, patch_slot_mean, patch_slot_hw in [
        ("tom_pipeline", 0.000794, 0.001702),
        ("paxos_pipeline", 0.015319, 0.015726),
        ("2pc_pipeline", 0.029973, 0.028666)]:
    gs = sw["scalability"][sw["scalability"].protocol == arm]
    gr = r[r.protocol == arm]
    slot_share_ps = (gs.drain_slots / gs.simulated_slots).to_numpy(float)
    energy_f_ps = gr.f_leak.to_numpy(float)
    c16[arm] = {
        "A_slot_share_mean_of_per_seed_from_sweep": round(float(slot_share_ps.mean()), 8),
        "A_hw95": round(float(T14 * slot_share_ps.std(ddof=1) / np.sqrt(len(slot_share_ps))), 8),
        "A_quoted_in_patch_list": patch_slot_mean,
        "A_hw_quoted": patch_slot_hw,
        "B_energy_f_mean_of_per_seed_from_runs": round(float(energy_f_ps.mean()), 8),
        "B_hw95": round(float(T14 * energy_f_ps.std(ddof=1) / np.sqrt(len(energy_f_ps))), 8),
        "ratio_B_over_A": round(float(energy_f_ps.mean() / slot_share_ps.mean()), 6),
        "slot_share_ratio_of_sums_sweep": round(
            float(gs.drain_slots.sum() / gs.simulated_slots.sum()), 8),
        "energy_f_ratio_of_sums_runs": round(
            1.0 - float(gr.awake_inside_windows.sum() / gr.awake_tick.sum()), 8),
    }
out["charge16_f"] = c16

# the CE/CI cumulative ratio: two estimators of it
c16r = {}
for ci, ce, quoted in [("tom_pipeline", "tom_ce", 1.4348),
                       ("paxos_pipeline", "paxos_ce", 3.8277),
                       ("2pc_pipeline", "2pc_ce", 5.6719)]:
    d = sw["scalability"]
    eci = ((d[d.protocol == ci].set_index("seed").listen
            + d[d.protocol == ci].set_index("seed").flood)
           / d[d.protocol == ci].set_index("seed").committed).sort_index()
    ece = ((d[d.protocol == ce].set_index("seed").listen
            + d[d.protocol == ce].set_index("seed").flood)
           / d[d.protocol == ce].set_index("seed").committed).sort_index()
    ratio_of_means = float(ece.mean() / eci.mean())
    mean_of_ratios = float((ece / eci).mean())
    c16r[ci] = {
        "quoted_in_patch_list": quoted,
        "ratio_of_means_from_sweep": round(ratio_of_means, 6),
        "mean_of_ratios_from_sweep": round(mean_of_ratios, 6),
        "mean_of_ratios_from_runs_csv": round(float(
            (r[r.protocol == ce].set_index("seed").cumulative_per_dec.sort_index()
             / r[r.protocol == ci].set_index("seed").cumulative_per_dec.sort_index()).mean()), 6),
        "which_matches_quote": ("ratio_of_means" if abs(ratio_of_means - quoted) < 5e-4
                                else "mean_of_ratios" if abs(mean_of_ratios - quoted) < 5e-4
                                else "NEITHER"),
    }
out["charge16_ratio"] = c16r

# ---------------------------------------------------------------- charge 10 reconciliation
c10 = {}
for arm in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline"]:
    g = r[r.protocol == arm]
    dec = pd.read_csv(f"{WORK}/decisions.csv")
    dec = dec[dec.protocol == arm]
    # amortised total actually integrated, per seed, vs awake charged inside windows
    per_seed = dec.groupby("seed").amortised.agg(["sum", "count", "mean"])
    j = g.set_index("seed").join(per_seed)
    c10[arm] = {
        "sum_Ei_equals_awake_inside": bool(np.allclose(
            j["sum"], j.awake_inside_windows, rtol=0, atol=1e-6)),
        "max_abs_gap_nodeslots": round(float(np.max(np.abs(
            j["sum"] - j.awake_inside_windows))), 8),
        "n_decisions_counted": int(j["count"].sum()),
        "n_committed": int(j.committed.sum()),
        "count_equals_committed": bool((j["count"] == j.committed).all()),
        # the two paths to the amortised mean
        "path1_mean_of_seed_means": round(float(j["mean"].mean()), 6),
        "path2_cumulative_over_1_minus_f_perseed": round(float(
            (j.cumulative_per_dec * (1.0 - j.f_leak)).mean()), 6),
        "identity_holds_per_seed": bool(np.allclose(
            j["mean"], j.cumulative_per_dec * (1.0 - j.f_leak), rtol=1e-9, atol=1e-9)),
    }
out["charge10_amortised_identity"] = c10

print(json.dumps(out, indent=1))
