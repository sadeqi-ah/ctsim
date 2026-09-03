#!/usr/bin/env python3
"""Cumulative decisions over time (logarithmic x-axis).

Same experiment as plot_progress.py, but with a log-scaled time axis that
exposes the early-startup ordering of the protocols.

Run from anywhere:  python3 plots/progress/plot_progress_log.py
Figures are written next to this script; CSV data lands in <repo>/results/.
"""

import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import LogFormatterMathtext

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
            # Drop slot=0 so it is representable on a log axis.
            df_snap = df_snap[df_snap["slot"] > 0].copy()
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
    plt.xscale("log")
    plt.xlabel("Time (Slots) - Log Scale")
    plt.ylabel("Decisions Reached")
    plt.ylim(0, 105)
    plt.gca().xaxis.set_major_formatter(LogFormatterMathtext())
    plt.legend(title="Protocol", framealpha=0.9, loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "progress_over_time_log.pdf"))
    plt.savefig(os.path.join(HERE, "progress_over_time_log.png"))
    plt.close()
    print("Wrote progress_over_time_log.pdf / .png")


if __name__ == "__main__":
    main()
