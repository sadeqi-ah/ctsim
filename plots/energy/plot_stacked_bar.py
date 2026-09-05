#!/usr/bin/env python3
"""Per-proposal amortized energy — stacked histogram, and data producer.

This script runs the six protocol/PHY combinations at the reference point
(N=27, random, 5% loss, 100 proposals) and (a) writes a stacked-histogram
figure of amortized per-proposal awake cost, and (b) leaves fresh CSVs under
<repo>/results/ that plot_paper_energy.py consumes for Figs. energy-*.

Run from anywhere:  python3 plots/energy/plot_stacked_bar.py
"""

import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _common  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def generate_toml(proto, phy):
    return f"""seed = 99
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


PROTOCOLS = [
    ("paxos_pipeline", "ci", "Paxos (CI)"),
    ("2pc_pipeline", "ci", "2PC (CI)"),
    ("tom_pipeline", "ci", "TOM (CI)"),
    ("paxos_ce", "ce", "Paxos (CE)"),
    ("2pc_ce", "ce", "2PC (CE)"),
    ("tom_ce", "ce", "TOM (CE)"),
]


def run_simulation_and_extract_per_proposal():
    per_proposal_data = []

    print("Compiling Rust simulator...")
    _common.build_release()

    for proto, phy, label in PROTOCOLS:
        print(f"Running simulation for {label}...")
        _common.RESULTS_DIR.mkdir(exist_ok=True)
        toml_path = _common.RESULTS_DIR / f"sim_{proto}_per_prop.toml"
        with open(toml_path, "w") as f:
            f.write(generate_toml(proto, phy))
        _common.run_config(toml_path)

        csv_results = _common.results_csv_for(proto)
        csv_snaps = _common.snapshot_csv(proto)

        if csv_results.exists() and csv_snaps.exists():
            df_res = pd.read_csv(csv_results)
            df_snap = pd.read_csv(csv_snaps)
            # Decision 23: Eq. (5) needs a per-slot series, not a sampled one.
            _common.require_per_slot_series(df_snap["slot"], f"{label} [{csv_snaps.name}]")
            df_snap["awake"] = df_snap["nodes_listening"] + df_snap["nodes_flooding"]

            for _, row in df_res.iterrows():
                if row["outcome"] == "committed":
                    start = row["start_slot"]
                    end = row["end_slot"]
                    window = df_snap[(df_snap["slot"] >= start) & (df_snap["slot"] < end)]

                    # Amortize each awake slot across all proposals alive in it.
                    amortized_awake = 0
                    for _, snap_row in window.iterrows():
                        current_s = snap_row["slot"]
                        aw = snap_row["awake"]
                        if aw > 0:
                            alive = df_res[
                                (df_res["start_slot"] <= current_s)
                                & (df_res["end_slot"] > current_s)
                            ]
                            concurrent = len(alive)
                            if concurrent > 0:
                                amortized_awake += aw / concurrent

                    per_proposal_data.append(
                        {
                            "Protocol": label,
                            "proposal_id": row["proposal_id"],
                            "awake_slots": amortized_awake,
                        }
                    )
        else:
            print(f"  -> Warning: missing files for {proto}")

    return pd.DataFrame(per_proposal_data)


def main():
    _common.academic_style()
    plt.rcParams.update({"font.size": 14, "axes.labelsize": 16})

    df = run_simulation_and_extract_per_proposal()
    if df.empty:
        print("No data collected.")
        return

    max_awake = int(df["awake_slots"].max())
    step = max(50, (max_awake // 12) // 50 * 50)
    if step == 0:
        step = 25
    custom_bins = list(range(0, max_awake + step * 2, step))
    bin_labels = [f"{custom_bins[i]}-{custom_bins[i+1]}" for i in range(len(custom_bins) - 1)]
    df["slot_range"] = pd.cut(df["awake_slots"], bins=custom_bins, labels=bin_labels, right=False)

    stacked_data = df.groupby(["slot_range", "Protocol"], observed=False).size().unstack(fill_value=0)
    stacked_data = stacked_data.loc[(stacked_data != 0).any(axis=1)]

    plt.figure(figsize=(14, 8))
    sns.set_palette("Set2")
    stacked_data.plot(
        kind="bar",
        stacked=True,
        width=0.8,
        edgecolor="black",
        linewidth=0.7,
        ax=plt.gca(),
        colormap="Paired",
    )
    plt.xlabel("Energy Cost per Proposal (Sum of Awake Nodes in Lifespan)")
    plt.ylabel("Number of Proposals (Frequency)")
    plt.title(
        "Distribution of Per-Proposal Energy Footprint\n"
        "(27 nodes, Random, Loss = 5%, 100 Decisions)",
        pad=15,
    )
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Protocol", framealpha=0.9, loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "stacked_bar_per_proposal_energy.pdf"))
    plt.savefig(os.path.join(HERE, "stacked_bar_per_proposal_energy.png"))
    plt.close()
    print("Wrote stacked_bar_per_proposal_energy.pdf / .png")


if __name__ == "__main__":
    main()
