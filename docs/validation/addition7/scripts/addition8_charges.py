#!/usr/bin/env python3
"""Charges 23-28 and decision 52's excluded row.

Every aggregation is named. Decision 51: every +/- printed here is a 95 %
interval, t(0.975,14) = 2.144787 times a delete-one-seed jackknife SE.
"""
import json
import os

import numpy as np
import pandas as pd

DATA = "/Users/amir/Projects/ctsim/docs/validation/addition7/data"
T14 = 2.144787
PAIRS = [("tom_pipeline", "tom_ce"), ("paxos_pipeline", "paxos_ce"),
         ("2pc_pipeline", "2pc_ce")]
runs = pd.read_csv(os.path.join(DATA, "runs.csv"))
c14 = pd.read_csv(os.path.join(DATA, "charge14_maxCt.csv"))
seeds = sorted(runs.seed.unique())
n = len(seeds)


def col(arm, f, keep=None):
    g = runs[runs.protocol == arm].set_index("seed").sort_index()
    s = keep if keep is not None else seeds
    return g.loc[s, f].to_numpy(float)


# t(0.975, df) for the df values this script needs. Hardcoded rather than sampled:
# a bootstrap would make the interval non-reproducible, and scipy is absent.
T_TABLE = {9: 2.262157, 10: 2.228139, 11: 2.200985, 12: 2.178813, 13: 2.160369,
           14: 2.144787}


def jk(fn, m_seeds):
    k = len(m_seeds)
    t = T_TABLE[k - 1]
    full = fn(np.ones(k, dtype=bool))
    loo = np.empty(k)
    for i in range(k):
        m = np.ones(k, dtype=bool)
        m[i] = False
        loo[i] = fn(m)
    se = np.sqrt((k - 1) / k * np.sum((loo - loo.mean()) ** 2))
    return {"value": round(float(full), 6), "jackknife_se": round(float(se), 6),
            "hw95": round(float(t * se), 6), "t_used": round(t, 6), "n_seeds": k}


out = {"decision_51_note": "every hw95 is t(0.975,df) x jackknife SE, a 95 % interval"}

# ---------------------------------------------------------------- CHARGE 23
# Is E_CE instrumented or assumed? Instrumented: node.rs:70-72 increments
# slots_listen/flood/sleep per node per tick; nothing in src/ computes N*L.
# The falsifiable residual is therefore instrumented awake against N * L_ce.
c23 = {}
for _, ce in PAIRS:
    awake = col(ce, "awake_tick")
    lat = col(ce, "mean_latency")
    comm = col(ce, "committed")
    S = col(ce, "simulated_slots")
    predicted = 27.0 * lat * comm            # N * Lbar * (decisions)
    resid = awake / predicted - 1.0
    c23[ce] = {
        "instrumented_awake_per_dec": [round(float(v), 6) for v in (awake / comm)][:3],
        "N_times_Lce_per_dec": [round(float(v), 6) for v in (27.0 * lat)][:3],
        "max_abs_rel_residual_per_seed": float(np.max(np.abs(resid))),
        "residual_is_exactly_zero": bool(np.all(resid == 0.0)),
        "sleep_total": int(runs[runs.protocol == ce].sleep.sum()),
        "S_equals_end_slot_all_seeds": bool(np.all(S == col(ce, "end_slot"))),
        "slots_per_dec_equals_Lce_max_abs": float(np.max(np.abs(S / comm - lat))),
    }
out["charge23_is_E_CE_instrumented"] = c23

# ---------------------------------------------------------------- CHARGE 24/25
# closure of the four-factor and two-factor products, both aggregations named.
clo = {}
for ci, ce in PAIRS:
    duty = col(ci, "duty_overall")
    l_ci, l_ce = col(ci, "mean_latency"), col(ce, "mean_latency")
    dep = (col(ci, "committed") / col(ci, "end_slot")) * l_ci
    tail = col(ci, "end_slot") / col(ci, "simulated_slots")
    spd_ci = col(ci, "simulated_slots") / col(ci, "committed")
    spd_ce = col(ce, "simulated_slots") / col(ce, "committed")
    meas_rom = col(ce, "cumulative_per_dec").mean() / col(ci, "cumulative_per_dec").mean()

    four_pom = (1 / duty).mean() * (l_ce / l_ci).mean() * dep.mean() * tail.mean()
    four_mop = ((1 / duty) * (l_ce / l_ci) * dep * tail).mean()
    two_pom = (1 / duty).mean() * (spd_ce / spd_ci).mean()
    two_mop = ((1 / duty) * (spd_ce / spd_ci)).mean()
    clo[ci] = {
        "measured_ratio_of_means": round(float(meas_rom), 6),
        "four_factor_product_of_means": round(float(four_pom), 6),
        "four_factor_closure_pct": round(100.0 * float(four_pom / meas_rom - 1), 4),
        "four_factor_mean_of_products": round(float(four_mop), 6),
        "four_factor_mop_closure_pct": round(100.0 * float(four_mop / meas_rom - 1), 4),
        "two_factor_product_of_means": round(float(two_pom), 6),
        "two_factor_closure_pct": round(100.0 * float(two_pom / meas_rom - 1), 4),
        "two_factor_mean_of_products": round(float(two_mop), 6),
        "two_factor_mop_closure_pct": round(100.0 * float(two_mop / meas_rom - 1), 4),
        "spd_ci": round(float(spd_ci.mean()), 4),
        "spd_ce": round(float(spd_ce.mean()), 4),
    }
out["charge24_closure"] = clo

# charge 25: the floor, three quantities named separately
duty_t = col("tom_pipeline", "duty_overall")
lat_fac = (col("tom_ce", "mean_latency") * col("tom_pipeline", "committed")
           / col("tom_pipeline", "simulated_slots"))
meas_floor = col("tom_ce", "cumulative_per_dec").mean() / col("tom_pipeline",
                                                             "cumulative_per_dec").mean()
out["charge25_floor"] = {
    "measured_floor_ratio_of_means": round(float(meas_floor), 6),
    "one_over_duty_mean_of_per_seed": round(float((1 / duty_t).mean()), 6),
    "duty_over_explains_floor_pct": round(100.0 * float((1 / duty_t).mean() / meas_floor - 1), 4),
    "latency_factor_mean": round(float(lat_fac.mean()), 6),
    "latency_shortfall_pct": round(100.0 * float(1.0 / lat_fac.mean() - 1), 4),
    "product_of_means": round(float((1 / duty_t).mean() * lat_fac.mean()), 6),
    "closure_error_pp": round(100.0 * float((1 / duty_t).mean() * lat_fac.mean()
                                            / meas_floor - 1), 4),
    "mean_of_products": round(float(((1 / duty_t) * lat_fac).mean()), 6),
    "mean_of_products_closure_pct": round(100.0 * float(((1 / duty_t) * lat_fac).mean()
                                                        / meas_floor - 1), 4),
}

# ---------------------------------------------------------------- CHARGE 26
# endpoint slope and residual only; OLS deleted per decision 50. Report the
# residual under BOTH normalisations and name which separates.
def endpoint(m, what):
    r = {}
    for ci, ce in PAIRS:
        r[ci] = col(ce, "cumulative_per_dec")[m].mean() / col(ci, "cumulative_per_dec")[m].mean()
    d = {}
    for ci, _ in PAIRS:
        d[ci] = ((col(ci, "committed") / col(ci, "end_slot")) * col(ci, "mean_latency"))[m].mean()
    slope = ((r["2pc_pipeline"] - r["tom_pipeline"])
             / (d["2pc_pipeline"] - d["tom_pipeline"]))
    resid = r["paxos_pipeline"] - (r["tom_pipeline"]
                                  + slope * (d["paxos_pipeline"] - d["tom_pipeline"]))
    if what == "slope":
        return slope
    if what == "residual":
        return resid
    return resid / (r["2pc_pipeline"] - r["tom_pipeline"])


c26 = {"endpoint_slope": jk(lambda m: endpoint(m, "slope"), seeds),
       "paxos_residual_absolute": jk(lambda m: endpoint(m, "residual"), seeds),
       "paxos_residual_as_share_of_span": jk(lambda m: endpoint(m, "share"), seeds)}
for k in ["paxos_residual_absolute", "paxos_residual_as_share_of_span"]:
    v = c26[k]
    v["ci95"] = [round(v["value"] - v["hw95"], 6), round(v["value"] + v["hw95"], 6)]
    v["excludes_zero"] = bool(abs(v["value"]) > v["hw95"])
c26["ols_deleted_per_decision_50"] = True
out["charge26_endpoint_only"] = c26

# ---------------------------------------------------------------- CHARGE 27 / DECISION 52
c27 = {}
# (i) does Addition 8 pool N = 188 at all?
c27["addition8_inputs"] = {
    "runs_csv_rows": int(len(runs)),
    "runs_csv_nodes": "N = 27 only; runs.csv has no nodes column because every row is the reference point",
    "charge14_csv_rows": int(len(c14)),
    "charge14_used_for": "max C_t per N and the charge-17 bound only",
    "coefficients_pool_N188": False,
}
# (ii) zero-commit and incomplete runs, by N, from charge14
z = {}
for arm in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline"]:
    z[arm] = {int(nn): {"zero_commit": int((g.committed == 0).sum()),
                        "incomplete": int((g.committed < 100).sum()),
                        "max_Ct": int(g.max_Ct.max())}
              for nn, g in c14[c14.protocol == arm].groupby("nodes")}
c27["by_N"] = z
# (iii) at N = 27, which seeds are incomplete, and the triple with them dropped
inc = runs[(runs.protocol == "2pc_pipeline") & (runs.committed < 100)].seed.tolist()
c27["N27_2pc_incomplete_seeds"] = [int(s) for s in inc]
c27["N27_zero_commit_seeds"] = [int(s) for s in
                                runs[(runs.protocol == "2pc_pipeline")
                                     & (runs.committed == 0)].seed.tolist()]
keep = [s for s in seeds if s not in inc]
sub = {}
for ci, ce in PAIRS:
    a = col(ci, "cumulative_per_dec", keep)
    b = col(ce, "cumulative_per_dec", keep)
    sub[ci] = jk(lambda m, a=a, b=b: b[m].mean() / a[m].mean(), keep)
    d = ((col(ci, "committed", keep) / col(ci, "end_slot", keep))
         * col(ci, "mean_latency", keep))
    sub[ci]["depth"] = jk(lambda m, d=d: d[m].mean(), keep)


def endpoint_sub(m, what):
    r, dd = {}, {}
    for ci, ce in PAIRS:
        r[ci] = col(ce, "cumulative_per_dec", keep)[m].mean() / col(ci, "cumulative_per_dec",
                                                                   keep)[m].mean()
        dd[ci] = ((col(ci, "committed", keep) / col(ci, "end_slot", keep))
                  * col(ci, "mean_latency", keep))[m].mean()
    slope = (r["2pc_pipeline"] - r["tom_pipeline"]) / (dd["2pc_pipeline"] - dd["tom_pipeline"])
    resid = r["paxos_pipeline"] - (r["tom_pipeline"] + slope * (dd["paxos_pipeline"]
                                                               - dd["tom_pipeline"]))
    return slope if what == "slope" else resid


c27["decision52_row_fully_committing_seeds_only"] = {
    "seeds_kept": [int(s) for s in keep],
    "n_seeds": len(keep),
    "triple": {k: {kk: vv for kk, vv in v.items() if kk != "depth"} for k, v in sub.items()},
    "depths": {k: v["depth"] for k, v in sub.items()},
    "endpoint_slope": jk(lambda m: endpoint_sub(m, "slope"), keep),
    "paxos_residual": jk(lambda m: endpoint_sub(m, "residual"), keep),
}
out["charge27_saturation"] = c27

# ---------------------------------------------------------------- CHARGE 28
out["charge28"] = {
    "printed_span_amortised_metric": [2.1, 8.2],
    "measured_span_cumulative_metric": [1.434823, 5.671896],
    "verdict": "void: the printed span is the retired metric's; no error factor is computable",
}
print(json.dumps(out, indent=1))
