#!/usr/bin/env python3
"""ADDITION 7 — the 15-seed per-decision series on the fixed snapshot path.

Runs all six arms at the reference point (N=27, random, 5 % loss, 100 proposals)
for each of the fifteen published seeds, at snapshot_interval = 1, and writes one
row per (arm, seed) plus one row per (arm, seed, decision) to the workspace.

Deliverables a-g of the ITEM-2 order are computed from those two files by
addition7_report.py; this script only collects. Appends as it goes so a timeout
does not lose the run.

Usage:  addition7_collect.py [--force]
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
N = 27
ARMS = [  # (protocol, phy, results stem)
    ("tom_pipeline", "ci", "tom"),
    ("paxos_pipeline", "ci", "paxos"),
    ("2pc_pipeline", "ci", "2pc"),
    ("tom_ce", "ce", "tom_ce"),
    ("paxos_ce", "ce", "paxos_ce"),
    ("2pc_ce", "ce", "2pc_ce"),
]
TOML = """seed = {seed}
phy_mode = "{phy}"
protocol = "{proto}"
num_proposals = 100
snapshot_interval = 1
max_slots = 50000
abort_probability = 0.0

[network]
num_nodes = 27
topology = "random"
loss_rate = 0.05

[ci]
flood_repeats = 1

[ce]
listen_timeout = 5
max_round_slots = 300
"""


def parse_energy(stdout):
    """Listen/Flood/Sleep from the binary's own report — the authoritative tick path."""
    for line in reversed(stdout.splitlines()):
        if line.startswith("Energy profile:"):
            parts = line.split()
            return tuple(int(p.split("=")[1]) for p in parts[2:5])
    raise RuntimeError("no Energy profile line in stdout")


def run_one(proto, phy, seed):
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                     dir=f"{REPO}/results") as fh:
        fh.write(TOML.format(seed=seed, phy=phy, proto=proto))
        path = fh.name
    try:
        p = subprocess.run([BIN, path], cwd=REPO, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"{proto} seed {seed} exit {p.returncode}: {p.stderr[:300]}")
        return parse_energy(p.stdout)
    finally:
        os.unlink(path)


def collect(proto, phy, stem, seed):
    listen, flood, sleep = run_one(proto, phy, seed)
    res = pd.read_csv(f"{REPO}/results/results_{stem}.csv")
    snap = pd.read_csv(f"{REPO}/results/snapshots_{stem}.csv")
    snap = snap.sort_values("slot").reset_index(drop=True)

    slots = snap.slot.to_numpy(np.int64)
    awake = (snap.nodes_listening + snap.nodes_flooding).to_numpy(np.float64)
    starts = res.start_slot.to_numpy(np.int64)
    ends = res.end_slot.to_numpy(np.int64)

    # decision 23: the metric needs a contiguous per-slot series
    assert slots[0] == 0 and np.array_equal(slots, np.arange(len(slots))), \
        f"{proto} seed {seed}: series is not per-slot"
    total = listen + flood + sleep
    assert total == N * len(slots), \
        f"{proto} seed {seed}: {total} charged vs {N * len(slots)} in series"

    conc = np.zeros(len(slots))
    for s, e in zip(starts, ends):
        conc[(slots >= s) & (slots < e)] += 1.0

    cost = np.where(conc > 0, awake / np.where(conc > 0, conc, 1.0), 0.0)
    pref = np.concatenate([[0.0], np.cumsum(cost)])

    dec = []
    for pid, s, e, o in zip(res.proposal_id, starts, ends, res.outcome.astype(str)):
        if o != "committed":
            continue
        dec.append({"protocol": proto, "phy": phy, "seed": seed,
                    "proposal_id": int(pid), "start_slot": int(s), "end_slot": int(e),
                    "latency": int(e - s),
                    "amortised": float(pref[e] - pref[s])})

    c0 = conc == 0
    awake_in = float(awake[conc > 0].sum())
    n_c0 = int(c0.sum())
    committed = int((res.outcome == "committed").sum())
    lat = (ends - starts)[res.outcome.values == "committed"]
    end_slot = int(ends.max())

    row = {
        "protocol": proto, "phy": phy, "seed": seed,
        "listen": listen, "flood": flood, "sleep": sleep,
        "awake_tick": listen + flood,
        "simulated_slots": len(slots),
        "end_slot": end_slot,
        "drain_slots": len(slots) - end_slot,
        "proposals": len(res), "committed": committed,
        "mean_latency": float(lat.mean()) if committed else float("nan"),
        "sum_latency": int(lat.sum()) if committed else 0,
        "awake_inside_windows": awake_in,
        "awake_outside_windows": float(awake[c0].sum()),
        "n_slots_C0": n_c0,
        "n_slots_Cge2": int((conc >= 2).sum()),
        "max_Ct": int(conc.max()),
        "mean_Ct": float(conc.mean()),
        "duty_overall": (listen + flood) / (N * len(slots)),
        "duty_in_C0": (float(awake[c0].sum()) / (N * n_c0)) if n_c0 else float("nan"),
        "f_leak": 1.0 - awake_in / (listen + flood),
        "amortised_mean": float(np.mean([d["amortised"] for d in dec])),
        "cumulative_per_dec": (listen + flood) / committed if committed else float("nan"),
        "Ct_hist": json.dumps({int(k): int(v) for k, v in
                               zip(*np.unique(conc.astype(int), return_counts=True))}),
    }
    return row, dec


def main():
    os.makedirs(WORK, exist_ok=True)
    srow, sdec = f"{WORK}/runs.csv", f"{WORK}/decisions.csv"
    if "--force" in sys.argv:
        for p in (srow, sdec):
            if os.path.exists(p):
                os.unlink(p)
    done = set()
    if os.path.exists(srow):
        d = pd.read_csv(srow)
        done = set(zip(d.protocol, d.seed))

    for proto, phy, stem in ARMS:
        for seed in SEEDS:
            if (proto, seed) in done:
                continue
            row, dec = collect(proto, phy, stem, seed)
            pd.DataFrame([row]).to_csv(srow, mode="a", header=not os.path.exists(srow),
                                       index=False)
            pd.DataFrame(dec).to_csv(sdec, mode="a", header=not os.path.exists(sdec),
                                     index=False)
            print(f"{proto:16s} seed {seed:2d}  slots={row['simulated_slots']:5d} "
                  f"end={row['end_slot']:5d} f={row['f_leak']:.6f} "
                  f"maxCt={row['max_Ct']} C0={row['n_slots_C0']}", flush=True)

    r = pd.read_csv(srow)
    print(f"\nrows={len(r)} arms={r.protocol.nunique()} seeds={r.seed.nunique()}")
    print(f"decisions={len(pd.read_csv(sdec))}")


if __name__ == "__main__":
    main()
