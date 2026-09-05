#!/usr/bin/env python3
"""ADDITION 7 — deliverables a-g from the 15-seed fixed series.

Reads /tmp/ctsim_validate/addition7/{runs,decisions}.csv (written by
addition7_collect.py) and emits one JSON with every quantity the ITEM-2 order
asks for. No number is hand-typed and no seed is dropped.
"""
import json

import numpy as np
import pandas as pd

WORK = "/tmp/ctsim_validate/addition7"
T14 = 2.144787  # t_{0.975,14}
N = 27
ARMS = ["tom_pipeline", "paxos_pipeline", "2pc_pipeline", "tom_ce", "paxos_ce", "2pc_ce"]
CI_ARMS = ARMS[:3]

r = pd.read_csv(f"{WORK}/runs.csv")
d = pd.read_csv(f"{WORK}/decisions.csv")
out = {"n_runs": len(r), "n_decisions": len(d),
       "seeds": sorted(r.seed.unique().tolist())}


def hw(x):
    """t-based 95 % half-width on the mean."""
    x = np.asarray(x, float)
    return float(T14 * x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else float("nan")


def summ(x):
    x = np.asarray(x, float)
    return {"mean": round(float(x.mean()), 6), "hw95": round(hw(x), 6),
            "min": round(float(x.min()), 6), "max": round(float(x.max()), 6),
            "n": int(len(x))}


# ---------------------------------------------------------------- a. f, both estimators
fa = {}
for a in ARMS:
    g = r[r.protocol == a]
    ratio_of_sums = 1.0 - g.awake_inside_windows.sum() / g.awake_tick.sum()
    per_seed = g.f_leak.to_numpy(float)
    fa[a] = {
        "estimator_1_ratio_of_sums": round(float(ratio_of_sums), 8),
        "estimator_2_mean_of_per_seed": summ(per_seed),
        "n_seeds_with_f_gt_0": int((per_seed > 0).sum()),
        "per_seed": {int(s): round(float(v), 8) for s, v in zip(g.seed, per_seed)},
    }
out["a_f_both_estimators"] = fa

# ---------------------------------------------------------------- b. duty ratio per seed
db = {}
for a in ARMS:
    g = r[r.protocol == a]
    have = g[g.n_slots_C0 > 0]
    ratio = (have.duty_in_C0 / have.duty_overall).to_numpy(float)
    db[a] = {
        "n_seeds_with_a_tail": int(len(have)),
        "seeds_with_a_tail": have.seed.tolist(),
        "duty_overall": summ(g.duty_overall.to_numpy(float)),
        "duty_ratio": summ(ratio) if len(ratio) > 1 else (
            {"single_value": round(float(ratio[0]), 6), "n": 1} if len(ratio) == 1 else
            {"n": 0, "note": "no seed has an uncovered slot"}),
        "duty_ratio_per_seed": {int(s): round(float(v), 6)
                                for s, v in zip(have.seed, ratio)},
    }
out["b_duty_ratio"] = db

# ---------------------------------------------------------------- c. distributions
QS = [1, 25, 50, 75, 99]
dc = {}
for a in ARMS:
    x = d[d.protocol == a].amortised.to_numpy(float)
    q = np.percentile(x, QS)
    dc[a] = {"n_decisions": int(len(x)),
             "min": round(float(x.min()), 4), "p01": round(float(q[0]), 4),
             "q25": round(float(q[1]), 4), "median": round(float(q[2]), 4),
             "q75": round(float(q[3]), 4), "p99": round(float(q[4]), 4),
             "max": round(float(x.max()), 4),
             "IQR": round(float(q[3] - q[1]), 4),
             "mean": round(float(x.mean()), 4)}
out["c_distributions"] = dc

# ---------------------------------------------------------------- d. section F stats
pooled = d[d.protocol.isin(CI_ARMS)].amortised.to_numpy(float)
pce = d[d.protocol == "paxos_ce"].amortised.to_numpy(float)
tce = d[d.protocol == "tom_ce"].amortised.to_numpy(float)
tci = d[d.protocol == "tom_pipeline"].amortised.to_numpy(float)
p2c = d[d.protocol == "2pc_pipeline"].amortised.to_numpy(float)
pci = d[d.protocol == "paxos_pipeline"].amortised.to_numpy(float)
tce_L = r[r.protocol == "tom_ce"].mean_latency.to_numpy(float)

out["d_sectionF"] = {
    "quartiles": {
        "pooled_CI_q25": round(float(np.percentile(pooled, 25)), 4),
        "pooled_CI_q75": round(float(np.percentile(pooled, 75)), 4),
        "paxos_ce_q25": round(float(np.percentile(pce, 25)), 4),
        "paxos_ce_q75": round(float(np.percentile(pce, 75)), 4),
        "ratio_paxosCE_q25_over_pooledCI_q75":
            round(float(np.percentile(pce, 25) / np.percentile(pooled, 75)), 4),
        "gap_nodeslots": round(float(np.percentile(pce, 25)
                                     - np.percentile(pooled, 75)), 4),
        "interquartile_overlap": bool(np.percentile(pooled, 75)
                                      > np.percentile(pce, 25)),
    },
    "percentile_vs_percentile": {
        "pooled_CI_p99": round(float(np.percentile(pooled, 99)), 4),
        "paxos_ce_p01": round(float(np.percentile(pce, 1)), 4),
        "separated": bool(np.percentile(pooled, 99) < np.percentile(pce, 1)),
        "ratio": round(float(np.percentile(pce, 1) / np.percentile(pooled, 99)), 4),
        "extremum_form_for_comparison": {
            "pooled_CI_max": round(float(pooled.max()), 4),
            "paxos_ce_min": round(float(pce.min()), 4),
            "extrema_overlap": bool(pooled.max() > pce.min()),
            "pct_CI_below_paxosCE_min": round(100.0 * float((pooled < pce.min()).mean()), 4),
        },
    },
    "CI_family_ordering": {
        "tom_median": round(float(np.median(tci)), 4),
        "paxos_median": round(float(np.median(pci)), 4),
        "2pc_median": round(float(np.median(p2c)), 4),
        "tom_q75": round(float(np.percentile(tci, 75)), 4),
        "2pc_min": round(float(p2c.min()), 4),
        "2pc_p01": round(float(np.percentile(p2c, 1)), 4),
        "2pc_q25": round(float(np.percentile(p2c, 25)), 4),
        "2pc_p01_above_tom_median": bool(np.percentile(p2c, 1) > np.median(tci)),
        "pct_tom_below_2pc_p01": round(100.0 * float((tci < np.percentile(p2c, 1)).mean()), 4),
        "medians_ordered_tom_lt_paxos_lt_2pc":
            bool(np.median(tci) < np.median(pci) < np.median(p2c)),
    },
    "tom_ce_median_vs_ceiling": {
        "median_amortised": round(float(np.median(tce)), 4),
        "median_over_N": round(float(np.median(tce)) / N, 6),
        "mean_latency_15seed": round(float(tce_L.mean()), 6),
        "mean_latency_hw95": round(hw(tce_L), 6),
        "ceiling_N_times_Lbar": round(N * float(tce_L.mean()), 4),
        "ceiling_hw95": round(N * hw(tce_L), 4),
    },
}

# ---------------------------------------------------------------- e. C_t histograms
de = {}
for a in ARMS:
    g = r[r.protocol == a]
    merged = {}
    for h in g.Ct_hist:
        for k, v in json.loads(h).items():
            merged[int(k)] = merged.get(int(k), 0) + int(v)
    de[a] = {
        "pooled_hist": dict(sorted(merged.items())),
        "max_Ct_over_seeds": int(g.max_Ct.max()),
        "n_seeds_with_Cge2": int((g.n_slots_Cge2 > 0).sum()),
        "n_seeds_with_C0": int((g.n_slots_C0 > 0).sum()),
        "slots_C0_total": int(g.n_slots_C0.sum()),
        "slots_Cge2_total": int(g.n_slots_Cge2.sum()),
        "per_seed_max_Ct": {int(s): int(v) for s, v in zip(g.seed, g.max_Ct)},
        "per_seed_C0": {int(s): int(v) for s, v in zip(g.seed, g.n_slots_C0)},
        "mean_Ct": summ(g.mean_Ct.to_numpy(float)),
    }
out["e_Ct"] = de

# ---------------------------------------------------------------- f. S vs end_slot
df_ = {}
for a in ARMS:
    g = r[r.protocol == a]
    df_[a] = {
        "n_rows_S_eq_end": int((g.simulated_slots == g.end_slot).sum()),
        "n_rows_S_gt_end": int((g.simulated_slots > g.end_slot).sum()),
        "drain_slots_total": int(g.drain_slots.sum()),
        "max_drain_slots": int(g.drain_slots.max()),
        "S_over_end_max": round(float((g.simulated_slots / g.end_slot).max()), 6),
        "rows": [{"seed": int(s), "S": int(S), "end_slot": int(e), "drain": int(D)}
                 for s, S, e, D in zip(g.seed, g.simulated_slots, g.end_slot,
                                       g.drain_slots)],
    }
out["f_S_vs_end_slot"] = df_

# ---------------------------------------------------------------- g. identity residual
dg = {}
for a in ["tom_ce", "paxos_ce", "2pc_ce"]:
    g = r[r.protocol == a].copy()
    g["depth"] = (g.committed / g.end_slot) * g.mean_latency
    g["res_depth"] = 1.0 / g.depth - 1.0                       # depth route
    g["E_per_dec"] = g.awake_tick / g.committed
    g["res_energy"] = g.E_per_dec / (N * g.mean_latency) - 1.0  # energy route
    g["S_over_end"] = g.simulated_slots / g.end_slot
    dg[a] = {
        "agree_to_6dp": bool(np.allclose(g.res_depth, g.res_energy, atol=1e-6)),
        "max_abs_difference": float(np.max(np.abs(g.res_depth - g.res_energy))),
        "group_mean_residual_pct": round(100.0 * float(g.res_energy.mean()), 6),
        "worst_seed_residual_pct": round(100.0 * float(g.res_energy.max()), 6),
        "worst_seed": int(g.loc[g.res_energy.idxmax(), "seed"]),
        "n_seeds_committing_all": int((g.committed == g.proposals).sum()),
        "rows": [{"seed": int(s), "committed": int(c), "depth": round(float(dp), 6),
                  "res_depth_pct": round(100.0 * float(rd), 6),
                  "res_energy_pct": round(100.0 * float(re_), 6),
                  "S_over_end": round(float(so), 8)}
                 for s, c, dp, rd, re_, so in zip(g.seed, g.committed, g.depth,
                                                  g.res_depth, g.res_energy,
                                                  g.S_over_end)],
    }
out["g_identity_residual"] = dg

# ---------------------------------------------- amortised vs cumulative, 15 seeds
dr = {}
for a in ARMS:
    g = r[r.protocol == a]
    dec_mean = d[d.protocol == a].groupby("seed").amortised.mean()
    cum = g.set_index("seed").cumulative_per_dec
    ratio = (dec_mean / cum).to_numpy(float)
    dr[a] = {"amortised_mean_of_seed_means": summ(dec_mean.to_numpy(float)),
             "cumulative": summ(cum.to_numpy(float)),
             "ratio": summ(ratio)}
out["amortised_vs_cumulative"] = dr

ce_over_ci = {}
for ci, ce in [("tom_pipeline", "tom_ce"), ("paxos_pipeline", "paxos_ce"),
               ("2pc_pipeline", "2pc_ce")]:
    for label, col in [("cumulative", "cumulative_per_dec")]:
        a_ci = r[r.protocol == ci].set_index("seed")[col]
        a_ce = r[r.protocol == ce].set_index("seed")[col]
        ce_over_ci[f"{ci}_{label}"] = summ((a_ce / a_ci).to_numpy(float))
    m_ci = d[d.protocol == ci].groupby("seed").amortised.mean()
    m_ce = d[d.protocol == ce].groupby("seed").amortised.mean()
    ce_over_ci[f"{ci}_amortised"] = summ((m_ce / m_ci).to_numpy(float))
out["headline_CE_over_CI"] = ce_over_ci

print(json.dumps(out, indent=1))
