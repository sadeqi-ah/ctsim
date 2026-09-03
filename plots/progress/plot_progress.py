#!/usr/bin/env python3
"""Cumulative decisions over time (linear x-axis).

Runs all six protocol/PHY combinations at the reference operating point
(N=27, random, 5% loss, 100 proposals) and plots how many decisions each
combination has finalized network-wide as a function of slot time.

Run from anywhere:  python3 plots/progress/plot_progress.py
Figures are written next to this script; CSV data lands in <repo>/results/.
"""

import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _common  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

PROTOCOLS = [
    ("paxos_pipeline", "Paxos (CI)"),
    ("2pc_pipeline", "2PC (CI)"),
    ("tom_pipeline", "TOM (CI)"),
    ("paxos_ce", "Paxos (CE)"),
    ("2pc_ce", "2PC (CE)"),
    ("tom_ce", "TOM (CE)"),
]


def run_simulation_and_collect_snapshots():
    dfs = []
    print("Compiling Rust simulator...")
    _common.build_release()

    for proto, label in PROTOCOLS:
        print(f"Running simulation for {label}...")
        _common.run_config(os.path.join(HERE, f"sim_{proto}_progress.toml"))

        csv_snaps = _common.snapshot_csv(proto)
        if csv_snaps.exists():
            df_snap = pd.read_csv(csv_snaps)
            # progress_count is already the network-unified decision count.
            df_snap["Decisions"] = df_snap["progress_count"]
            df_snap["Protocol"] = label
            dfs.append(df_snap)
        else:
            print(f"  -> Warning: missing snapshot file for {proto}")

    return pd.concat(dfs, ignore_index=True)


def main():
    _common.academic_style()
    df = run_simulation_and_collect_snapshots()
    if df.empty:
        print("No data collected.")
        return

    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df,
        x="slot",
        y="Decisions",
        hue="Protocol",
        style="Protocol",
        linewidth=2.5,
        palette="tab10",
    )
    plt.xlabel("Time (Slots)")
    plt.ylabel("Decisions Reached")
    plt.xlim(0, df["slot"].max() * 1.05)
    plt.ylim(0, 105)
    plt.legend(title="Protocol", framealpha=0.9, loc="lower right", frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "progress_over_time.pdf"))
    plt.savefig(os.path.join(HERE, "progress_over_time.png"))
    plt.close()
    print("Wrote progress_over_time.pdf / .png")


if __name__ == "__main__":
    main()
