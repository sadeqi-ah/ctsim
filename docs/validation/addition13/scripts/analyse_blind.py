#!/usr/bin/env python3
"""
Estimator and ms conversion for blind predictions (addition 13, step 2.5).

Python 3 standard library only: csv, math, statistics.
"""

import csv
import math
import os
import statistics

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DATA = os.path.join(REPO_ROOT, "docs", "validation", "addition13", "data", "blind_predictions.csv")

T_975_14 = 2.1447866879169273  # t(0.975, df=14)

# T_slot components
T_IFS = 150.0  # microseconds
# L = ceil(N/8) + 22 octets
# T_air = 44.0 + 4.0 * L us

def t_air(n_nodes):
    L = (n_nodes + 7) // 8 + 22
    return 44.0 + 4.0 * L

def t_slot_us(n_nodes, t_guard):
    return t_air(n_nodes) + T_IFS + 2.0 * t_guard

SYSTEMS = {
    "a2_sensys17": {"n": 180, "target_ms": 475.0, "slot_lo": 828, "slot_hi": 1205},
    "wpaxos_ewsn19": {"n": 188, "target_ms": 289.0, "slot_lo": 500, "slot_hi": 726},
}

T_GUARDS = [10, 20, 50, 100]

def load_data():
    with open(DATA) as f:
        reader = csv.DictReader(f)
        return list(reader)

def main():
    rows = load_data()

    # Group by (system, arm, loss_rate)
    from collections import defaultdict
    cells = defaultdict(list)
    for r in rows:
        key = (r["system"], r["arm"], r["loss_rate"])
        cells[key].append(float(r["mean_latency_slots"]))

    print("=" * 90)
    print("STEP E — ESTIMATOR (per-graph mean latency in slots)")
    print("=" * 90)
    print()
    print(f"{'system':>18} {'arm':>12} {'loss':>6}  {'n':>3}  {'mean':>10}  {'sd':>10}  {'SE':>10}  {'CI_lo':>10}  {'CI_hi':>10}")

    results = {}
    for key in sorted(cells.keys()):
        system, arm, loss = key
        vals = cells[key]
        assert len(vals) == 15, f"{key}: expected 15, got {len(vals)}"
        mean_val = statistics.mean(vals)
        sd_val = statistics.stdev(vals)
        se = sd_val / math.sqrt(15)
        hw = T_975_14 * se
        ci_lo = mean_val - hw
        ci_hi = mean_val + hw
        n = SYSTEMS[system]["n"]
        print(f"{system:>18} {arm:>12} {loss:>6}  {n:>3}  {mean_val:>10.3f}  {sd_val:>10.3f}  {se:>10.3f}  {ci_lo:>10.3f}  {ci_hi:>10.3f}")
        results[key] = {"mean": mean_val, "sd": sd_val, "se": se, "hw": hw, "ci_lo": ci_lo, "ci_hi": ci_hi}

    print()
    print("=" * 90)
    print("STEP F — CONVERSION TO MILLISECONDS")
    print("=" * 90)
    print()

    # Primary comparison: base arm, loss 0.05
    for system in ["a2_sensys17", "wpaxos_ewsn19"]:
        info = SYSTEMS[system]
        n = info["n"]
        target_ms = info["target_ms"]
        slot_lo = info["slot_lo"]
        slot_hi = info["slot_hi"]

        key = (system, "base", "0.05")
        if key not in results:
            print(f"  {system} base 0.05: NO DATA")
            continue

        r = results[key]
        mean_slots = r["mean"]
        hw_slots = r["hw"]

        print(f"\n  {system}  (N={n}, target={target_ms} ms)")
        print(f"  mean latency = {mean_slots:.3f} slots  [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]")
        print(f"  slot-equivalent interval for target: [{slot_lo}, {slot_hi}] slots")
        in_slot_interval = slot_lo <= mean_slots <= slot_hi
        print(f"  mean IN slot interval: {'YES' if in_slot_interval else 'NO'} ({mean_slots:.1f} vs [{slot_lo}, {slot_hi}])")
        print()

        print(f"  {'T_guard':>8}  {'T_slot_us':>10}  {'pred_ms':>10}  {'CI_lo_ms':>10}  {'CI_hi_ms':>10}  {'target':>10}  {'rel_err':>10}  {'|err|<20%':>10}")
        for tg in T_GUARDS:
            ts = t_slot_us(n, tg)
            pred_ms = mean_slots * ts / 1000.0
            ci_lo_ms = r["ci_lo"] * ts / 1000.0
            ci_hi_ms = r["ci_hi"] * ts / 1000.0
            rel_err = (pred_ms - target_ms) / target_ms
            within = abs(rel_err) < 0.20
            print(f"  {tg:>8}  {ts:>10.1f}  {pred_ms:>10.3f}  {ci_lo_ms:>10.3f}  {ci_hi_ms:>10.3f}  {target_ms:>10.1f}  {rel_err:>+10.4f}  {'YES' if within else 'NO':>10}")

    # Also show the 0.06 and robustness arms
    print()
    print("=" * 90)
    print("ALL CELLS (slots)")
    print("=" * 90)
    print()
    print(f"{'system':>18} {'arm':>12} {'loss':>6}  {'mean':>10}  {'sd':>10}  {'CI_lo':>10}  {'CI_hi':>10}")
    for key in sorted(results.keys()):
        system, arm, loss = key
        r = results[key]
        print(f"{system:>18} {arm:>12} {loss:>6}  {r['mean']:>10.3f}  {r['sd']:>10.3f}  {r['ci_lo']:>10.3f}  {r['ci_hi']:>10.3f}")


if __name__ == "__main__":
    main()
