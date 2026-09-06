#!/usr/bin/env python3
"""Charges 24 and 25 settled: every aggregation named, closure computed against
the matching aggregation on both sides.

Decision 49 requires a multiplicative table to carry its closure error or be
recomputed under a consistent aggregation. This does the second: the two-factor
identity is exact when both sides use the same aggregation, and the only residue
is the ratio-of-means / ratio-of-sums gap, which is nonzero on exactly the arm
whose committed count varies across seeds.
"""
import json

import numpy as np
import pandas as pd

DATA = "/Users/amir/Projects/ctsim/docs/validation/addition7/data"
N = 27
T14 = 2.144787
PAIRS = [("tom_pipeline", "tom_ce"), ("paxos_pipeline", "paxos_ce"),
         ("2pc_pipeline", "2pc_ce")]
runs = pd.read_csv(f"{DATA}/runs.csv")
seeds = sorted(runs.seed.unique())


def col(arm, f):
    g = runs[runs.protocol == arm].set_index("seed").sort_index()
    return g.loc[seeds, f].to_numpy(float)


out = {}
tab = {}
for ci, ce in PAIRS:
    aw_ci, aw_ce = col(ci, "awake_tick"), col(ce, "awake_tick")
    S_ci, S_ce = col(ci, "simulated_slots"), col(ce, "simulated_slots")
    c_ci, c_ce = col(ci, "committed"), col(ce, "committed")

    # the measured ratio, under both aggregations
    rom = (aw_ce / c_ce).mean() / (aw_ci / c_ci).mean()
    ros = (aw_ce.sum() / c_ce.sum()) / (aw_ci.sum() / c_ci.sum())

    # the two-factor identity, each aggregation applied consistently on BOTH sides
    duty_ros = aw_ci.sum() / (N * S_ci.sum())
    two_ros = (1.0 / duty_ros) * ((S_ce.sum() / c_ce.sum()) / (S_ci.sum() / c_ci.sum()))
    duty_pm = (col(ci, "duty_overall")).mean()
    two_mop = ((1.0 / col(ci, "duty_overall"))
               * ((S_ce / c_ce) / (S_ci / c_ci))).mean()

    tab[ci] = {
        "measured_ratio_of_means": round(float(rom), 6),
        "measured_ratio_of_sums": round(float(ros), 6),
        "rom_vs_ros_pct": round(100.0 * float(rom / ros - 1), 4),
        "committed_varies_across_seeds": bool(c_ci.std() > 0),
        "n_incomplete_seeds": int((c_ci < 100).sum()),
        "two_factor_ratio_of_sums": round(float(two_ros), 6),
        "closure_vs_ros_pct": round(100.0 * float(two_ros / ros - 1), 8),
        "two_factor_mean_of_products": round(float(two_mop), 6),
        "closure_vs_rom_pct": round(100.0 * float(two_mop / rom - 1), 6),
        "duty_ratio_of_sums": round(float(duty_ros), 6),
        "one_over_duty_ros": round(float(1.0 / duty_ros), 6),
        "spd_factor_ros": round(float((S_ce.sum() / c_ce.sum())
                                      / (S_ci.sum() / c_ci.sum())), 6),
        "duty_mean_of_per_seed": round(float(duty_pm), 6),
        "slots_per_dec_ci_ros": round(float(S_ci.sum() / c_ci.sum()), 4),
        "slots_per_dec_ce_ros": round(float(S_ce.sum() / c_ce.sum()), 4),
    }
out["charge24_two_factor_consistent"] = tab

# ------------------------------------------------------------- charge 25, the floor
duty = col("tom_pipeline", "duty_overall")
aw_ci, S_ci, c_ci = (col("tom_pipeline", "awake_tick"),
                     col("tom_pipeline", "simulated_slots"),
                     col("tom_pipeline", "committed"))
aw_ce, S_ce, c_ce = (col("tom_ce", "awake_tick"),
                     col("tom_ce", "simulated_slots"),
                     col("tom_ce", "committed"))
duty_ros = aw_ci.sum() / (N * S_ci.sum())
lat_ros = (S_ce.sum() / c_ce.sum()) / (S_ci.sum() / c_ci.sum())
floor_rom = (aw_ce / c_ce).mean() / (aw_ci / c_ci).mean()
floor_ros = (aw_ce.sum() / c_ce.sum()) / (aw_ci.sum() / c_ci.sum())
out["charge25_floor"] = {
    "measured_floor_ratio_of_means": round(float(floor_rom), 6),
    "measured_floor_ratio_of_sums": round(float(floor_ros), 6),
    "identical_because_committed_constant": bool(np.all(c_ci == c_ci[0])),
    "one_over_duty_ratio_of_sums": round(float(1.0 / duty_ros), 6),
    "one_over_duty_mean_of_per_seed": round(float((1.0 / duty).mean()), 6),
    "one_over_mean_duty": round(float(1.0 / duty.mean()), 6),
    "duty_alone_over_explains_pct_ros": round(100.0 * float((1.0 / duty_ros) / floor_ros - 1), 4),
    "slots_per_dec_factor_ros": round(float(lat_ros), 6),
    "slots_per_dec_shortfall_pct": round(100.0 * float(1.0 / lat_ros - 1), 4),
    "product_ros": round(float((1.0 / duty_ros) * lat_ros), 6),
    "closure_ros_pct": round(100.0 * float((1.0 / duty_ros) * lat_ros / floor_ros - 1), 8),
}

# ------------------------------------------------------------- printed duty, decision 41
d41 = {}
for ci, _ in PAIRS:
    aw, S = col(ci, "awake_tick"), col(ci, "simulated_slots")
    d41[ci] = {"duty_ratio_of_sums": round(float(aw.sum() / (N * S.sum())), 6)}
allaw = sum(col(ci, "awake_tick").sum() for ci, _ in PAIRS)
allS = sum(col(ci, "simulated_slots").sum() for ci, _ in PAIRS)
d41["all_three_arms_pooled"] = {"duty_ratio_of_sums": round(float(allaw / (N * allS)), 6)}
out["decision41_duty"] = d41

print(json.dumps(out, indent=1))
