#!/usr/bin/env python3
"""Charge 10 (the amortised gap) and charge 14 (max C_t per N).

Charge 10: the residual between Sigma_i E_i over COMMITTED decisions and
Sigma_{t: C_t>0} A_t is the share carried by proposals that never committed.
C_t counts every in-flight proposal, aborted ones included, so an aborted
proposal absorbs energy into the denominator and then contributes no E_i.
Quantified per seed here.

Charge 14: max C_t against N, from the scalability sweep's own N values.
C_t needs only the per-proposal windows, so no snapshot series is read.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

REPO = "/Users/amir/Projects/ctsim"
BIN = f"{REPO}/target/release/ctsim"
WORK = "/tmp/ctsim_validate/addition7"
SEEDS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
NODES = [6, 13, 27, 54, 188]
CI = [("tom_pipeline", "tom"), ("paxos_pipeline", "paxos"), ("2pc_pipeline", "2pc")]
T14 = 2.144787

TOML = """seed = {seed}
phy_mode = "ci"
protocol = "{proto}"
num_proposals = 100
snapshot_interval = 100000
max_slots = 100000
abort_probability = 0.0

[network]
num_nodes = {n}
topology = "random"
loss_rate = 0.05

[ci]
flood_repeats = 1

[ce]
listen_timeout = 5
max_round_slots = 300
"""

out = {}

# ------------------------------------------------------------------ charge 10
dec = pd.read_csv(f"{WORK}/decisions.csv")
runs = pd.read_csv(f"{WORK}/runs.csv")
c10 = {}
for arm in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline"]:
    g = runs[runs.protocol == arm].set_index("seed").sort_index()
    s = dec[dec.protocol == arm].groupby("seed").amortised.sum()
    orphan = g.awake_inside_windows - s
    share = orphan / g.awake_tick
    n_abort = g.proposals - g.committed
    c10[arm] = {
        "orphan_nodeslots_total": round(float(orphan.sum()), 4),
        "orphan_share_of_awake": round(float(orphan.sum() / g.awake_tick.sum()), 8),
        "n_noncommitting_proposals": int(n_abort.sum()),
        "seeds_with_a_noncommitter": int((n_abort > 0).sum()),
        "f_slots_only_ratio_of_sums": round(
            1.0 - float(g.awake_inside_windows.sum() / g.awake_tick.sum()), 8),
        "f_including_orphans_ratio_of_sums": round(
            1.0 - float(s.sum() / g.awake_tick.sum()), 8),
        "amortised_over_cumulative_measured": round(
            float(s.sum() / g.awake_tick.sum()), 8),
        "per_seed_orphan": {int(k): round(float(v), 4)
                            for k, v in orphan.items() if abs(v) > 1e-9},
    }
out["charge10_orphan_share"] = c10

# the reconciliation table the charge asks for, both routes named
rec = {}
for ci_arm, ce_arm in [("tom_pipeline", "tom_ce"), ("paxos_pipeline", "paxos_ce"),
                       ("2pc_pipeline", "2pc_ce")]:
    gci = runs[runs.protocol == ci_arm].set_index("seed").sort_index()
    gce = runs[runs.protocol == ce_arm].set_index("seed").sort_index()
    sci = dec[dec.protocol == ci_arm].groupby("seed").amortised.mean()
    sce = dec[dec.protocol == ce_arm].groupby("seed").amortised.mean()
    cum_ratio_of_means = float(gce.cumulative_per_dec.mean()
                               / gci.cumulative_per_dec.mean())
    am_ratio_of_means = float(sce.mean() / sci.mean())
    g_over = float(sci.sum() / gci.cumulative_per_dec.sum())  # not used, kept explicit
    f_slots = c10[ci_arm]["f_slots_only_ratio_of_sums"]
    f_all = c10[ci_arm]["f_including_orphans_ratio_of_sums"]
    rec[ci_arm] = {
        "cumulative_ratio_of_means": round(cum_ratio_of_means, 6),
        "amortised_ratio_of_means": round(am_ratio_of_means, 6),
        "predicted_from_f_slots_only": round(cum_ratio_of_means / (1.0 - f_slots), 6),
        "predicted_from_f_with_orphans": round(cum_ratio_of_means / (1.0 - f_all), 6),
        "gap_pct_f_slots_only": round(100.0 * (am_ratio_of_means
                                               / (cum_ratio_of_means / (1.0 - f_slots)) - 1), 6),
        "gap_pct_f_with_orphans": round(100.0 * (am_ratio_of_means
                                                 / (cum_ratio_of_means / (1.0 - f_all)) - 1), 6),
    }
out["charge10_reconciliation"] = rec

# ------------------------------------------------------------------ charge 9 sign test
sign = {}
for arm in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline"]:
    g = runs[runs.protocol == arm]
    k = int((g.f_leak > 0).sum())
    n = len(g)
    # exact one-sided binomial tail at p = 1/2
    from math import comb
    p = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    x = g.f_leak.to_numpy(float)
    sign[arm] = {"n_positive": k, "n": n, "sign_test_p_one_sided": float(p),
                 "relative_halfwidth_pct": round(
                     100.0 * float(T14 * x.std(ddof=1) / np.sqrt(n) / x.mean()), 4)}
out["charge9_sign_test"] = sign

# ------------------------------------------------------------------ charge 14
def run(proto, stem, n, seed):
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                     dir=f"{REPO}/results") as fh:
        fh.write(TOML.format(seed=seed, proto=proto, n=n))
        path = fh.name
    try:
        p = subprocess.run([BIN, path], cwd=REPO, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"{proto} n={n} seed={seed}: {p.stderr[:200]}")
    finally:
        os.unlink(path)
    res = pd.read_csv(f"{REPO}/results/results_{stem}.csv")
    starts = res.start_slot.to_numpy(np.int64)
    ends = res.end_slot.to_numpy(np.int64)
    end = int(ends.max())
    conc = np.zeros(end + 1)
    for s, e in zip(starts, ends):
        conc[s:e] += 1.0
    return {"protocol": proto, "nodes": n, "seed": seed,
            "max_Ct": int(conc[:end].max()), "mean_Ct": float(conc[:end].mean()),
            "committed": int((res.outcome == "committed").sum()),
            "end_slot": end}

path14 = f"{WORK}/charge14_maxCt.csv"
if "--skip14" not in sys.argv:
    done = set()
    if os.path.exists(path14):
        d = pd.read_csv(path14)
        done = set(zip(d.protocol, d.nodes, d.seed))
    for proto, stem in CI:
        for n in NODES:
            for seed in SEEDS:
                if (proto, n, seed) in done:
                    continue
                row = run(proto, stem, n, seed)
                pd.DataFrame([row]).to_csv(path14, mode="a",
                                           header=not os.path.exists(path14), index=False)
    print("charge 14 collection done", file=sys.stderr)

d14 = pd.read_csv(path14)
c14 = {}
for proto in [p for p, _ in CI]:
    g = d14[d14.protocol == proto]
    per_n = {}
    for n, gg in g.groupby("nodes"):
        per_n[int(n)] = {
            "max_Ct_max": int(gg.max_Ct.max()),
            "max_Ct_min": int(gg.max_Ct.min()),
            "max_Ct_mean": round(float(gg.max_Ct.mean()), 4),
            "equals_N_on_n_seeds": int((gg.max_Ct == n).sum()),
            "exceeds_N_on_n_seeds": int((gg.max_Ct > n).sum()),
            "mean_Ct_mean": round(float(gg.mean_Ct.mean()), 4),
            "n_seeds": int(len(gg)),
        }
    c14[proto] = {
        "per_N": per_n,
        "tracks_N": all(v["max_Ct_max"] == n for n, v in per_n.items()),
        "never_exceeds_N": all(v["exceeds_N_on_n_seeds"] == 0 for v in per_n.values()),
        "max_Ct_over_all": int(g.max_Ct.max()),
    }
out["charge14_maxCt_per_N"] = c14

print(json.dumps(out, indent=1))
