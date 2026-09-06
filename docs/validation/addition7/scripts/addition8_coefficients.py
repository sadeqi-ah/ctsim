#!/usr/bin/env python3
"""ADDITION 8 — the decomposition coefficients: floor, slope per unit depth,
Paxos residual, each with a standard error.

Decision 42 convention throughout:
  - a SHARE is a ratio of sums (pooled numerator over pooled denominator)
  - a RATIO between two arms is a ratio of means over seeds
  - the uncertainty on a ratio of means is a delete-one-seed JACKKNIFE
    (decision 43); the half-width of a mean of per-seed ratios is never
    printed beside a ratio of means

The manuscript's claim under test (paper/paper.tex:1973-1983): the ascending
CE/CI energy ratios track depth; the smallest of them is a "floor ... available
even in the complete absence of concurrency" arising "entirely from duty
cycling"; and the distance from the floor to the largest is "the additional
contribution of amortisation".

Reads only the committed Addition 7 artefacts plus the published sweeps.
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
REPO = "/Users/amir/Projects/ctsim"
N = 27
T14 = 2.144787
PAIRS = [("tom_pipeline", "tom_ce"), ("paxos_pipeline", "paxos_ce"),
         ("2pc_pipeline", "2pc_ce")]

runs = pd.read_csv(os.path.join(DATA, "runs.csv"))
dec = pd.read_csv(os.path.join(DATA, "decisions.csv"))
seeds = sorted(runs.seed.unique())
n = len(seeds)

# per-seed arrays, seed-aligned, one column per arm
def col(arm, field):
    g = runs[runs.protocol == arm].set_index("seed").sort_index()
    return g.loc[seeds, field].to_numpy(float)


E = {a: col(a, "cumulative_per_dec") for a, _ in PAIRS}
E.update({b: col(b, "cumulative_per_dec") for _, b in PAIRS})
LAT = {a: col(a, "mean_latency") for a, _ in PAIRS}
LAT.update({b: col(b, "mean_latency") for _, b in PAIRS})
DUTY = {a: col(a, "duty_overall") for a, _ in PAIRS}
DUTY.update({b: col(b, "duty_overall") for _, b in PAIRS})
COMMIT = {a: col(a, "committed") for a, _ in PAIRS}
COMMIT.update({b: col(b, "committed") for _, b in PAIRS})
SLOTS = {a: col(a, "simulated_slots") for a, _ in PAIRS}
SLOTS.update({b: col(b, "simulated_slots") for _, b in PAIRS})
ENDSLOT = {a: col(a, "end_slot") for a, _ in PAIRS}
ENDSLOT.update({b: col(b, "end_slot") for _, b in PAIRS})
AWAKE = {a: col(a, "awake_tick") for a, _ in PAIRS}
AWAKE.update({b: col(b, "awake_tick") for _, b in PAIRS})
INSIDE = {a: col(a, "awake_inside_windows") for a, _ in PAIRS}
DEPTH = {a: (COMMIT[a] / ENDSLOT[a]) * LAT[a] for a in E}


def jackknife(fn):
    """Delete-one-seed jackknife of a statistic computed on a boolean mask.

    Returns (point estimate on the full sample, jackknife SE, t-based
    half-width, the fifteen leave-one-out values).
    """
    keep = np.ones(n, dtype=bool)
    full = fn(keep)
    loo = np.empty(n, dtype=float)
    for i in range(n):
        m = keep.copy()
        m[i] = False
        loo[i] = fn(m)
    se = np.sqrt((n - 1) / n * np.sum((loo - loo.mean()) ** 2))
    return float(full), float(se), float(T14 * se), loo


out = {"convention": {
    "share": "ratio of sums",
    "arm_to_arm_ratio": "ratio of means over the fifteen seeds",
    "interval": "delete-one-seed jackknife, t_{0.975,14} = 2.144787",
    "n_seeds": n,
}}

# ------------------------------------------------------- the ratio triple, decision 42/43
triple = {}
for ci, ce in PAIRS:
    p, se, hw, loo = jackknife(lambda m, ci=ci, ce=ce: E[ce][m].mean() / E[ci][m].mean())
    mean_of_ratios = (E[ce] / E[ci])
    triple[ci] = {
        "ratio_of_means": round(p, 6),
        "jackknife_se": round(se, 6),
        "jackknife_halfwidth": round(hw, 6),
        "printed_digit": round(p, 1),
        "mean_of_per_seed_ratios": round(float(mean_of_ratios.mean()), 6),
        "mean_of_ratios_halfwidth_NOT_PRINTED": round(
            float(T14 * mean_of_ratios.std(ddof=1) / np.sqrt(n)), 6),
    }
out["ratio_triple"] = triple

# ------------------------------------------------------- depth, mean of per-seed
depth = {}
for ci, _ in PAIRS:
    x = DEPTH[ci]
    depth[ci] = {"mean_of_per_seed": round(float(x.mean()), 6),
                 "halfwidth": round(float(T14 * x.std(ddof=1) / np.sqrt(n)), 6),
                 "min": round(float(x.min()), 6), "max": round(float(x.max()), 6)}
out["depth"] = depth

# ------------------------------------------------------- FLOOR
# The floor is the ratio at unit depth, i.e. TOM. Its claimed origin is duty
# cycling alone. Exact algebra: E_ce/dec = N*L_ce and E_ci/dec = duty_ci*N*S_ci/c,
# so the ratio factorises as (1/duty_ci) * (L_ce * c / S_ci) with no residue.
floor = {}
p, se, hw, _ = jackknife(lambda m: E["tom_ce"][m].mean() / E["tom_pipeline"][m].mean())
floor["measured"] = {"value": round(p, 6), "se": round(se, 6), "halfwidth": round(hw, 6)}
p2, se2, hw2, _ = jackknife(lambda m: 1.0 / DUTY["tom_pipeline"][m].mean())
floor["duty_cycling_factor_1_over_duty"] = {
    "value": round(p2, 6), "se": round(se2, 6), "halfwidth": round(hw2, 6)}
p3, se3, hw3, _ = jackknife(
    lambda m: (LAT["tom_ce"][m] * COMMIT["tom_pipeline"][m]
               / SLOTS["tom_pipeline"][m]).mean())
floor["latency_factor_Lce_c_over_S"] = {
    "value": round(p3, 6), "se": round(se3, 6), "halfwidth": round(hw3, 6)}
p4, se4, hw4, _ = jackknife(
    lambda m: (1.0 / DUTY["tom_pipeline"][m].mean())
    * (LAT["tom_ce"][m] * COMMIT["tom_pipeline"][m] / SLOTS["tom_pipeline"][m]).mean())
floor["product_of_the_two_factors"] = {
    "value": round(p4, 6), "se": round(se4, 6), "halfwidth": round(hw4, 6)}
floor["product_minus_measured_pct"] = round(100.0 * (p4 / p - 1.0), 6)
floor["duty_only_error_pct"] = round(100.0 * (p2 / p - 1.0), 6)
# exact per-seed factorisation check
lhs = E["tom_ce"] / E["tom_pipeline"]
rhs = (1.0 / DUTY["tom_pipeline"]) * (LAT["tom_ce"] * COMMIT["tom_pipeline"]
                                      / SLOTS["tom_pipeline"])
floor["per_seed_factorisation_max_abs_rel_dev"] = float(np.max(np.abs(lhs / rhs - 1.0)))
out["floor"] = floor

# ------------------------------------------------------- SLOPE per unit depth
# Two estimators, both named. (i) endpoint slope through TOM and 2PC, which is
# what the manuscript's "distance from the floor" sentence implies. (ii) ordinary
# least squares on all three arms, which also yields the Paxos residual.
slope = {}


def endpoint_slope(m):
    r_t = E["tom_ce"][m].mean() / E["tom_pipeline"][m].mean()
    r_p = E["2pc_ce"][m].mean() / E["2pc_pipeline"][m].mean()
    return (r_p - r_t) / (DEPTH["2pc_pipeline"][m].mean() - DEPTH["tom_pipeline"][m].mean())


p, se, hw, _ = jackknife(endpoint_slope)
slope["endpoint_TOM_to_2PC"] = {"value": round(p, 6), "se": round(se, 6),
                                "halfwidth": round(hw, 6)}


def ols(m, which):
    x = np.array([DEPTH[a][m].mean() for a, _ in PAIRS])
    y = np.array([E[b][m].mean() / E[a][m].mean() for a, b in PAIRS])
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    if which == "intercept":
        return coef[0]
    if which == "slope":
        return coef[1]
    return y[1] - (coef[0] + coef[1] * x[1])       # Paxos residual


for key, name in [("intercept", "ols_intercept"), ("slope", "ols_slope")]:
    p, se, hw, _ = jackknife(lambda m, k=key: ols(m, k))
    slope[name] = {"value": round(p, 6), "se": round(se, 6), "halfwidth": round(hw, 6)}
out["slope"] = slope

# ------------------------------------------------------- PAXOS RESIDUAL
res = {}
p, se, hw, loo = jackknife(lambda m: ols(m, "residual"))
res["ols_three_point"] = {"value": round(p, 6), "se": round(se, 6),
                          "halfwidth": round(hw, 6),
                          "excludes_zero": bool(abs(p) > hw)}


def endpoint_residual(m):
    r_t = E["tom_ce"][m].mean() / E["tom_pipeline"][m].mean()
    r_p = E["paxos_ce"][m].mean() / E["paxos_pipeline"][m].mean()
    r_2 = E["2pc_ce"][m].mean() / E["2pc_pipeline"][m].mean()
    d_t = DEPTH["tom_pipeline"][m].mean()
    d_p = DEPTH["paxos_pipeline"][m].mean()
    d_2 = DEPTH["2pc_pipeline"][m].mean()
    return r_p - (r_t + (r_2 - r_t) * (d_p - d_t) / (d_2 - d_t))


p, se, hw, _ = jackknife(endpoint_residual)
res["endpoint_interpolation"] = {"value": round(p, 6), "se": round(se, 6),
                                 "halfwidth": round(hw, 6),
                                 "excludes_zero": bool(abs(p) > hw)}
# as a share of the floor-to-2PC span
p, se, hw, _ = jackknife(
    lambda m: endpoint_residual(m) / (E["2pc_ce"][m].mean() / E["2pc_pipeline"][m].mean()
                                      - E["tom_ce"][m].mean() / E["tom_pipeline"][m].mean()))
res["as_fraction_of_span"] = {"value": round(p, 6), "se": round(se, 6),
                              "halfwidth": round(hw, 6)}
out["paxos_residual"] = res

# ------------------------------------------------------- is the ratio linear in depth at all?
lin = {}
x = np.array([DEPTH[a].mean() for a, _ in PAIRS])
y = np.array([E[b].mean() / E[a].mean() for a, b in PAIRS])
lin["depth_points"] = [round(float(v), 4) for v in x]
lin["ratio_points"] = [round(float(v), 6) for v in y]
lin["three_points_two_parameters"] = "one degree of freedom; the Paxos residual IS the test"
# amortisation's own contribution, per decision 42's share convention
amo = {}
for ci, ce in PAIRS:
    f_full = 1.0 - dec[dec.protocol == ci].amortised.sum() / AWAKE[ci].sum()
    amo[ci] = {"f_share_ratio_of_sums": round(float(f_full), 6),
               "excess_1_over_1_minus_f": round(float(1.0 / (1.0 - f_full)), 6)}
lin["amortisation_share"] = amo
out["linearity"] = lin

# ------------------------------------------------------- charge 22: the cross-N picture
c14 = pd.read_csv(os.path.join(DATA, "charge14_maxCt.csv"))
cross = {}
for arm in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline"]:
    per_n = {}
    for nn, g in c14[c14.protocol == arm].groupby("nodes"):
        per_n[int(nn)] = {
            "committed_min": int(g.committed.min()),
            "committed_max": int(g.committed.max()),
            "committed_mean": round(float(g.committed.mean()), 4),
            "zero_commit_seeds": int((g.committed == 0).sum()),
            "incomplete_seeds": int((g.committed < 100).sum()),
            "max_Ct": int(g.max_Ct.max()),
            "bound_binds_on": ("num_proposals" if int(g.max_Ct.max()) >= 100
                               else "N"),
        }
    cross[arm] = per_n
out["charge22_cross_N"] = cross

# ------------------------------------------------------- decision 47's free result
c47 = {}
for ci, _ in PAIRS:
    g = runs[runs.protocol == ci]
    c47[ci] = {"slots_Cge2": int(g.n_slots_Cge2.sum()),
               "slots_total": int(g.simulated_slots.sum()),
               "share_pct": round(100.0 * float(g.n_slots_Cge2.sum()
                                                / g.simulated_slots.sum()), 4)}
out["decision47_Cge2_share"] = c47

# ------------------------------------------------------- THE EXACT DECOMPOSITION
# The cumulative ratio factorises with no residue and no fitting. CE never
# sleeps, so E_ce/dec = N * S_ce / c_ce; CI's is duty * N * S_ci / c_ci. Hence
#
#   ratio = (1/duty_ci) * (L_ce / L_ci) * depth_ci * (end_slot_ci / S_ci)
#
# every factor measured, no free parameter. This is what "the ratio tracks
# depth" has to be tested against: depth is one of four factors, and two of the
# others move in the opposite direction.
fac = {}
for ci, ce in PAIRS:
    duty = col(ci, "duty_overall")
    l_ci, l_ce = LAT[ci], LAT[ce]
    dep = DEPTH[ci]
    tail = ENDSLOT[ci] / SLOTS[ci]
    meas = E[ce] / E[ci]
    pred = (1.0 / duty) * (l_ce / l_ci) * dep * tail
    parts = {}
    for name, arr in [("duty_factor_1_over_duty", 1.0 / duty),
                      ("latency_ratio_Lce_over_Lci", l_ce / l_ci),
                      ("depth", dep),
                      ("tail_factor_endslot_over_S", tail)]:
        p, se, hw, _ = jackknife(lambda m, a=arr: a[m].mean())
        parts[name] = {"value": round(p, 6), "se": round(se, 6), "halfwidth": round(hw, 6)}
    parts["per_seed_exactness_max_abs_rel_dev"] = float(np.max(np.abs(meas / pred - 1.0)))
    # aggregation gap: the product of the four seed-means against the mean of the
    # per-seed products. Named because decision 42 requires it named.
    prod_of_means = (parts["duty_factor_1_over_duty"]["value"]
                     * parts["latency_ratio_Lce_over_Lci"]["value"]
                     * parts["depth"]["value"]
                     * parts["tail_factor_endslot_over_S"]["value"])
    parts["product_of_means"] = round(float(prod_of_means), 6)
    parts["mean_of_products_ratio_of_means"] = round(float(meas.mean()), 6)
    parts["product_of_means_vs_ratio_of_means_pct"] = round(
        100.0 * float(prod_of_means / (E[ce].mean() / E[ci].mean()) - 1.0), 6)
    # the floor claim, for TOM: everything except duty cycling
    parts["non_duty_factors_product"] = round(float(
        parts["latency_ratio_Lce_over_Lci"]["value"] * parts["depth"]["value"]
        * parts["tail_factor_endslot_over_S"]["value"]), 6)
    # spd_ce == L_ce is the CE round-length identity; check it rather than assume
    parts["spd_ce_minus_Lce_max_abs"] = float(
        np.max(np.abs(SLOTS[ce] / COMMIT[ce] - l_ce)))
    fac[ci] = parts
out["exact_decomposition"] = fac

# and the growth each factor contributes across the three arms, TOM -> 2PC
growth = {}
for name in ["duty_factor_1_over_duty", "latency_ratio_Lce_over_Lci", "depth",
             "tail_factor_endslot_over_S"]:
    v = [fac[ci][name]["value"] for ci, _ in PAIRS]
    growth[name] = {"tom": v[0], "paxos": v[1], "2pc": v[2],
                    "tom_to_2pc_multiplier": round(v[2] / v[0], 6)}
growth["measured_ratio"] = {
    "tom": triple["tom_pipeline"]["ratio_of_means"],
    "paxos": triple["paxos_pipeline"]["ratio_of_means"],
    "2pc": triple["2pc_pipeline"]["ratio_of_means"],
    "tom_to_2pc_multiplier": round(triple["2pc_pipeline"]["ratio_of_means"]
                                   / triple["tom_pipeline"]["ratio_of_means"], 6)}
out["factor_growth_tom_to_2pc"] = growth

# ------------------------------------------------------- charge 20's falsifiable part
c20 = {}
for ci, _ in PAIRS:
    awake = AWAKE[ci].sum()
    f_full = 1.0 - dec[dec.protocol == ci].amortised.sum() / awake
    f_drain = runs[runs.protocol == ci].awake_outside_windows.sum() / awake
    c20[ci] = {"f_full": round(float(f_full), 8),
               "f_drain": round(float(f_drain), 8),
               "difference_orphan_share": round(float(f_full - f_drain), 8)}
out["charge20_decomposition_test"] = c20

# ------------------------------------------------------- charge 18/19 restatements
c18 = {}
for ci, _ in PAIRS:
    g = runs[runs.protocol == ci]
    f_slot_ros = float(g.drain_slots.sum() / g.simulated_slots.sum())
    f_energy_ros = float(1.0 - g.awake_inside_windows.sum() / g.awake_tick.sum())
    per_seed = (g.set_index("seed").sort_index().loc[seeds, "f_leak"].to_numpy(float)
                / (g.set_index("seed").sort_index().loc[seeds, "drain_slots"].to_numpy(float)
                   / g.set_index("seed").sort_index().loc[seeds,
                                                          "simulated_slots"].to_numpy(float)
                   + 1e-300))
    c18[ci] = {
        "f_slot_ratio_of_sums": round(f_slot_ros, 8),
        "f_energy_ratio_of_sums": round(f_energy_ros, 8),
        "pooled_density_ratio": round(f_energy_ros / f_slot_ros, 6),
        "ratio_of_means_density": round(float(
            (g.f_leak.to_numpy(float)).mean()
            / (g.drain_slots.to_numpy(float) / g.simulated_slots.to_numpy(float)).mean()), 6),
        "mean_of_per_seed_density_item_b": round(float(
            per_seed[np.isfinite(per_seed) & (per_seed > 0)].mean()), 6),
        "tail_is_pooled_denser": bool(f_energy_ros > f_slot_ros),
    }
out["charge18_density"] = c18

# charge 19: the precision comparison under the ratio-of-sums / jackknife convention
c19 = {}
for ci, ce in PAIRS:
    _, se_cum, hw_cum, _ = jackknife(
        lambda m, ci=ci, ce=ce: E[ce][m].mean() / E[ci][m].mean())
    amo_ci = dec[dec.protocol == ci].groupby("seed").amortised.mean()
    amo_ce = dec[dec.protocol == ce].groupby("seed").amortised.mean()
    a_ci = amo_ci.loc[seeds].to_numpy(float)
    a_ce = amo_ce.loc[seeds].to_numpy(float)
    _, se_amo, hw_amo, _ = jackknife(lambda m, a=a_ci, b=a_ce: b[m].mean() / a[m].mean())
    c19[ci] = {"cumulative_halfwidth_jackknife": round(hw_cum, 6),
               "amortised_halfwidth_jackknife": round(hw_amo, 6),
               "amortised_is_more_precise_by": round(hw_cum / hw_amo, 4)}
out["charge19_precision"] = c19

# charge 17: the Paxos bound
c17 = {}
for nn, g in c14[c14.protocol == "paxos_pipeline"].groupby("nodes"):
    nn = int(nn)
    c17[nn] = {"observed_max_Ct": int(g.max_Ct.max()),
               "ceil_N_over_2": -(-nn // 2),
               "floor_N_over_2_plus_1_majority": nn // 2 + 1,
               "majority_holds": bool(g.max_Ct.max() <= nn // 2 + 1),
               "majority_attained": bool(g.max_Ct.max() == nn // 2 + 1),
               "ceil_holds": bool(g.max_Ct.max() <= -(-nn // 2))}
out["charge17_paxos_bound"] = c17

print(json.dumps(out, indent=1))
