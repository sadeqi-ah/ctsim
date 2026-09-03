#!/usr/bin/env python3
"""Topology sensitivity analysis (CI vs CE).

Generates:
  1. thr_vs_topology.{png,pdf}
  2. lat_vs_topology.{png,pdf}
  3. energy_vs_topology.{png,pdf}
  4. efficiency_vs_topology.{png,pdf}
  5. table_topology_N27_loss05.csv / .tex

Runs cargo sweep if CSV missing or --force.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SWEEP_TOML = ROOT / "sweep_topology.toml"
CSV = OUT / "results" / "sweep_summary.csv"

LABELS = {
    "paxos_pipeline": "Paxos (CI)",
    "2pc_pipeline": "2PC (CI)",
    "tom_pipeline": "TOM (CI)",
    "paxos_ce": "Paxos (CE)",
    "2pc_ce": "2PC (CE)",
    "tom_ce": "TOM (CE)",
}
ORDER = [
    "TOM (CI)",
    "Paxos (CI)",
    "2PC (CI)",
    "TOM (CE)",
    "Paxos (CE)",
    "2PC (CE)",
]
# Diameter-ish order: sparse → dense
TOPO_ORDER = ["line", "partial_mesh", "random", "scale_free", "full_mesh"]
TOPO_NICE = {
    "line": "Line",
    "partial_mesh": "Partial mesh",
    "random": "Random",
    "scale_free": "Scale-free",
    "full_mesh": "Full mesh",
}


def academic_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 13,
            "axes.labelsize": 14,
            "axes.titlesize": 15,
            "xtick.labelsize": 11,
            "ytick.labelsize": 12,
            "legend.fontsize": 9,
            "figure.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linestyle": "--",
        }
    )


def run_sweep_if_needed():
    if CSV.exists() and "--force" not in sys.argv:
        print(f"Using existing {CSV}")
        return
    print("Running topology sweep (may take a few minutes)...")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cargo", "run", "--release", "--", str(SWEEP_TOML)],
        cwd=ROOT,
        check=True,
    )


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["Protocol"] = df["protocol"].map(LABELS)
    df["PHY"] = df["phy"].str.upper()
    df["topology_label"] = df["topology"].map(TOPO_NICE).fillna(df["topology"])
    df["throughput"] = df["committed"] / df["end_slot"].replace(0, 1)
    df["energy_per_dec"] = (df["listen"] + df["flood"]) / df["committed"].replace(0, 1)
    df["efficiency"] = df["throughput"] / df["energy_per_dec"].replace(0, np.nan) * 1000.0
    df["commit_rate"] = df["committed"] / df["proposals"].replace(0, 1) * 100.0
    # categorical order
    present = [t for t in TOPO_ORDER if t in set(df["topology"])]
    df["topology"] = pd.Categorical(df["topology"], categories=present, ordered=True)
    df["topology_label"] = pd.Categorical(
        df["topology"].map(TOPO_NICE),
        categories=[TOPO_NICE[t] for t in present],
        ordered=True,
    )
    return df


def bar_metric(df: pd.DataFrame, y: str, ylabel: str, fname: str, logy: bool = False):
    academic_style()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.barplot(
        data=df,
        x="topology_label",
        y=y,
        hue="Protocol",
        hue_order=[p for p in ORDER if p in set(df["Protocol"])],
        palette="tab10",
        errorbar="sd",
        capsize=0.08,
        edgecolor="black",
        linewidth=0.5,
        ax=ax,
    )
    ax.set_xlabel("Topology")
    ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale("log")
    ax.legend(title="Protocol",  loc="best")
    # ax.legend(title="Protocol", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{fname}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {fname}.png/pdf")


def table(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby(["topology", "Protocol"], observed=True)
        .agg(
            diameter=("diameter", "mean"),
            thr=("throughput", "mean"),
            thr_std=("throughput", "std"),
            lat=("avg_latency", "mean"),
            lat_std=("avg_latency", "std"),
            eng=("energy_per_dec", "mean"),
            eng_std=("energy_per_dec", "std"),
            eff=("efficiency", "mean"),
            commit=("commit_rate", "mean"),
        )
        .reset_index()
    )
    g = g.round(
        {
            "diameter": 1,
            "thr": 4,
            "thr_std": 4,
            "lat": 1,
            "lat_std": 1,
            "eng": 1,
            "eng_std": 1,
            "eff": 2,
            "commit": 1,
        }
    )
    g.to_csv(OUT / "table_topology_N27_loss05.csv", index=False)

    lines = [
        r"\begin{tabular}{llrrrrr}",
        r"\hline",
        r"Topology & Protocol & Diam. & Thr. & Lat. & Energy/dec & Eff. \\",
        r"\hline",
    ]
    for _, r in g.iterrows():
        topo = TOPO_NICE.get(str(r["topology"]), str(r["topology"]))
        lines.append(
            f"{topo} & {r['Protocol']} & {r['diameter']:.0f} & {r['thr']:.4f} & "
            f"{r['lat']:.1f} & {r['eng']:.1f} & {r['eff']:.2f} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}", ""]
    n_seeds = df["seed"].nunique() if "seed" in df.columns else 0
    (OUT / "table_topology_N27_loss05.tex").write_text(
        f"% N=27, loss=5%, 100 proposals, {n_seeds} seeds (mean)\n"
        "% Thr=committed/end_slot; Energy/dec=(listen+flood)/committed\n"
        + "\n".join(lines)
    )
    print("Wrote table_topology_N27_loss05.csv / .tex")
    return g


def main():
    run_sweep_if_needed()
    if not CSV.exists():
        raise SystemExit(f"Missing {CSV}")
    df = load()
    # only N=27 loss 0.05 if extra rows
    if "nodes" in df.columns:
        df = df[df["nodes"] == 27]
    if "loss_rate" in df.columns:
        df = df[df["loss_rate"] == 0.05]

    bar_metric(df, "throughput", "Throughput (decisions/slot)", "thr_vs_topology")
    bar_metric(df, "avg_latency", "Mean latency (slots)", "lat_vs_topology", logy=True)
    bar_metric(df, "energy_per_dec", "Energy per decision (node-slots)", "energy_vs_topology", logy=True)
    bar_metric(df, "efficiency", "Energy efficiency (score)", "efficiency_vs_topology", logy=True)
    g = table(df)
    print(g.to_string(index=False))
    print("Topology analysis done.")


if __name__ == "__main__":
    main()
