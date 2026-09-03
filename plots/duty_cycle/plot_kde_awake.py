#!/usr/bin/env python3
"""Distribution of awake nodes per slot (from snapshots).

KDE is a bad fit here:
  - CE: awake == N every slot (zero variance) → Dirac spike
  - CI: mass at 0 (post-wave sleep) and at N (full flood)

Use discrete PMF (normalized histogram) instead.
"""

import os
import subprocess
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
N_NODES = 27

PROTOCOLS = [
    ("paxos_pipeline", "ci", "Paxos (CI)"),
    ("2pc_pipeline", "ci", "2PC (CI)"),
    ("tom_pipeline", "ci", "TOM (CI)"),
    ("paxos_ce", "ce", "Paxos (CE)"),
    ("2pc_ce", "ce", "2PC (CE)"),
    ("tom_ce", "ce", "TOM (CE)"),
]


def generate_toml(proto, phy):
    return f"""seed = 99
phy_mode = "{phy}"
protocol = "{proto}"
num_proposals = 100
snapshot_interval = 1
max_slots = 50000
abort_probability = 0.0

[network]
num_nodes = {N_NODES}
topology = "random"
loss_rate = 0.05

[ci]
flood_repeats = 1

[ce]
listen_timeout = 5
max_round_slots = 512
"""


def snap_path(proto: str) -> str:
    if proto == "paxos_pipeline":
        return os.path.join(ROOT, "results", "snapshots_paxos.csv")
    if proto == "2pc_pipeline":
        return os.path.join(ROOT, "results", "snapshots_2pc.csv")
    if proto == "tom_pipeline":
        return os.path.join(ROOT, "results", "snapshots_tom.csv")
    return os.path.join(ROOT, "results", f"snapshots_{proto}.csv")


def collect(run_sims: bool) -> pd.DataFrame:
    rows = []
    if run_sims:
        subprocess.run(["cargo", "build", "--release"], cwd=ROOT, check=True)

    for proto, phy, label in PROTOCOLS:
        path = snap_path(proto)
        if run_sims:
            print(f"Running {label}...")
            toml_path = os.path.join(OUT_DIR, f"sim_{proto}_awake.toml")
            with open(toml_path, "w") as f:
                f.write(generate_toml(proto, phy))
            subprocess.run(
                ["cargo", "run", "--release", "--", toml_path],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        if not os.path.exists(path):
            print(f"  missing {path}")
            continue

        df = pd.read_csv(path)
        awake = (df["nodes_listening"] + df["nodes_flooding"]).astype(int)
        part = pd.DataFrame({"awake": awake, "Protocol": label})
        rows.append(part)
        z = (awake == 0).mean() * 100
        f = (awake == N_NODES).mean() * 100
        print(
            f"  {label}: slots={len(part)} mean={awake.mean():.1f} "
            f"%sleep_all={z:.0f} %all_awake={f:.0f}"
        )

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 13,
            "axes.labelsize": 15,
            "axes.titlesize": 16,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 10,
            "figure.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linestyle": "--",
        }
    )

    run_sims = "--no-run" not in sys.argv
    df = collect(run_sims)
    if df.empty:
        print("No data.")
        return

    # Empirical PMF: P(awake = k) for k = 0..N
    pmf_rows = []
    for proto, g in df.groupby("Protocol", sort=False):
        counts = g["awake"].value_counts(normalize=True)
        for k in range(N_NODES + 1):
            pmf_rows.append(
                {"Protocol": proto, "awake": k, "prob": float(counts.get(k, 0.0))}
            )
    pmf = pd.DataFrame(pmf_rows)

    # --- Figure: discrete PMF (step / stem-friendly line) ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    ci_labels = [p[2] for p in PROTOCOLS if p[1] == "ci"]
    ce_labels = [p[2] for p in PROTOCOLS if p[1] == "ce"]
    palette = sns.color_palette("Set1", n_colors=6)
    color_map = {PROTOCOLS[i][2]: palette[i] for i in range(6)}

    for ax, labels, title in [
        (axes[0], ci_labels, "CI (Pipeline)"),
        (axes[1], ce_labels, "CE (Chaos)"),
    ]:
        for lab in labels:
            sub = pmf[pmf["Protocol"] == lab]
            ax.plot(
                sub["awake"],
                sub["prob"],
                drawstyle="steps-mid",
                linewidth=2.2,
                label=lab,
                color=color_map[lab],
            )
            ax.fill_between(
                sub["awake"],
                sub["prob"],
                step="mid",
                alpha=0.15,
                color=color_map[lab],
            )
        ax.set_xlim(-0.5, N_NODES + 0.5)
        ax.set_xlabel("Awake nodes (Listen + Flood)")
        ax.set_title(title)
        ax.legend(frameon=True, framealpha=0.9, loc="upper center")

    axes[0].set_ylabel("Fraction of slots  $P(\\mathrm{awake}=k)$")
    fig.suptitle(
        "Per-Slot Radio Activity Distribution\n"
        f"({N_NODES} nodes, random topology, loss = 5%)",
        fontsize=16,
        y=1.02,
    )
    fig.tight_layout()
    pdf = os.path.join(OUT_DIR, "pmf_awake_nodes.pdf")
    png = os.path.join(OUT_DIR, "pmf_awake_nodes.png")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {png}")

    # --- Summary bar: mean awake + % all-sleep / % all-awake ---
    summary = []
    for proto, g in df.groupby("Protocol", sort=False):
        aw = g["awake"]
        summary.append(
            {
                "Protocol": proto,
                "mean_awake": aw.mean(),
                "frac_all_sleep": (aw == 0).mean(),
                "frac_all_awake": (aw == N_NODES).mean(),
            }
        )
    sm = pd.DataFrame(summary)

    fig2, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(sm))
    w = 0.35
    ax.bar(
        x - w / 2,
        sm["frac_all_sleep"] * 100,
        w,
        label="% slots all Sleep",
        color="#4C72B0",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.bar(
        x + w / 2,
        sm["frac_all_awake"] * 100,
        w,
        label="% slots all Awake",
        color="#DD8452",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(sm["Protocol"], rotation=20, ha="right")
    ax.set_ylabel("Fraction of slots (%)")
    ax.set_title(
        "Duty-Cycle Extremes: Fully Off vs Fully On\n"
        f"({N_NODES} nodes, random, loss = 5%)"
    )
    ax.legend(frameon=True)
    # annotate mean awake
    for i, row in sm.iterrows():
        ax.text(
            i,
            max(row["frac_all_sleep"], row["frac_all_awake"]) * 100 + 3,
            f"μ={row['mean_awake']:.1f}",
            ha="center",
            fontsize=9,
        )
    fig2.tight_layout()
    p2 = os.path.join(OUT_DIR, "duty_cycle_extremes.png")
    fig2.savefig(p2, bbox_inches="tight")
    fig2.savefig(os.path.join(OUT_DIR, "duty_cycle_extremes.pdf"), bbox_inches="tight")
    plt.close(fig2)
    print(f"Wrote {p2}")


if __name__ == "__main__":
    main()
