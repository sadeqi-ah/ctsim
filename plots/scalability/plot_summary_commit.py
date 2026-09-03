#!/usr/bin/env python3
"""P0 paper assets:
  1) Summary table (N=27, loss=5%) → CSV + LaTeX
  2) Commit rate vs loss (N=27) and vs N (loss=5%) → PNG/PDF
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

HERE = Path(__file__).resolve().parent
CSV = HERE / "results" / "sweep_summary.csv"
OUT = HERE

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


def academic_style():
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


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["Protocol"] = df["protocol"].map(LABELS)
    df["PHY"] = df["phy"].str.upper()
    df["commit_rate"] = df["committed"] / df["proposals"].replace(0, 1) * 100.0
    df["abort_rate"] = df["aborted"] / df["proposals"].replace(0, 1) * 100.0
    df["throughput"] = df["committed"] / df["end_slot"].replace(0, 1)
    df["energy_per_dec"] = (df["listen"] + df["flood"]) / df["committed"].replace(0, 1)
    df["efficiency"] = (df["throughput"] / df["energy_per_dec"].replace(0, np.nan)) * 1000.0
    return df


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Baseline: N=27, loss=5% — mean over seeds."""
    sub = df[(df["nodes"] == 27) & (df["loss_rate"] == 0.05)].copy()
    g = (
        sub.groupby("Protocol", sort=False)
        .agg(
            seeds=("seed", "nunique"),
            commit_rate_pct=("commit_rate", "mean"),
            abort_rate_pct=("abort_rate", "mean"),
            throughput=("throughput", "mean"),
            latency_slots=("avg_latency", "mean"),
            energy_per_dec=("energy_per_dec", "mean"),
            efficiency=("efficiency", "mean"),
            end_slot=("end_slot", "mean"),
            listen=("listen", "mean"),
            flood=("flood", "mean"),
            sleep=("sleep", "mean"),
        )
        .reindex(ORDER)
        .dropna(how="all")
        .reset_index()
    )
    # round for paper
    g = g.round(
        {
            "commit_rate_pct": 1,
            "abort_rate_pct": 1,
            "throughput": 4,
            "latency_slots": 1,
            "energy_per_dec": 1,
            "efficiency": 2,
            "end_slot": 0,
            "listen": 0,
            "flood": 0,
            "sleep": 0,
        }
    )
    g.to_csv(OUT / "table_summary_N27_loss05.csv", index=False)

    # compact LaTeX without jinja2/styler
    lines = [
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Protocol & Commit (\%) & Thr. & Lat. & Energy/dec & Eff. \\",
        r"\hline",
    ]
    for _, r in g.iterrows():
        lines.append(
            f"{r['Protocol']} & {r['commit_rate_pct']:.1f} & {r['throughput']:.4f} & "
            f"{r['latency_slots']:.1f} & {r['energy_per_dec']:.1f} & {r['efficiency']:.2f} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}", ""]
    n_seeds = int(sub["seed"].nunique())
    (OUT / "table_summary_N27_loss05.tex").write_text(
        f"% Baseline: N=27, loss=5%, random topo, 100 proposals, {n_seeds} seeds (mean)\n"
        "% Thr. = committed/end_slot; Lat. = mean slots/decision;\n"
        "% Energy/dec = (listen+flood)/committed; Eff. ∝ thr/energy\n"
        + "\n".join(lines)
    )
    print("Wrote table_summary_N27_loss05.csv / .tex")
    print(g.to_string(index=False))
    return g


def plot_commit_rate_vs_loss(df: pd.DataFrame) -> None:
    academic_style()
    sub = df[df["nodes"] == 27].copy()
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.lineplot(
        data=sub,
        x="loss_rate",
        y="commit_rate",
        hue="Protocol",
        style="Protocol",
        hue_order=ORDER,
        style_order=ORDER,
        markers=True,
        dashes=False,
        linewidth=2.2,
        markersize=8,
        palette="Set1",
        # "sd" is a closed-form spread, not a bootstrap: no RNG, so this figure
        # is already reproducible without seeding.
        errorbar=("sd", 1),
        ax=ax,
    )
    ax.set_ylim(0, 105)
    ax.set_xticks(sorted(sub["loss_rate"].unique()))
    ax.set_xlabel("Link loss rate")
    ax.set_ylabel("Commit rate (\\% of proposals)")
    ax.set_title(
        "Decision Success Rate under Packet Loss\n"
        r"$N{=}27$, random topology, 100 proposals, 3 seeds (mean $\pm$ sd)"
    )
    ax.legend(title="Protocol", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"commit_rate_vs_loss.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote commit_rate_vs_loss.png/pdf")


def plot_commit_rate_vs_nodes(df: pd.DataFrame) -> None:
    academic_style()
    sub = df[df["loss_rate"] == 0.05].copy()
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.lineplot(
        data=sub,
        x="nodes",
        y="commit_rate",
        hue="Protocol",
        style="Protocol",
        hue_order=ORDER,
        style_order=ORDER,
        markers=True,
        dashes=False,
        linewidth=2.2,
        markersize=8,
        palette="Set1",
        errorbar=("sd", 1),
        ax=ax,
    )
    ax.set_ylim(0, 105)
    ax.set_xticks(sorted(sub["nodes"].unique()))
    ax.set_xlabel("Number of nodes ($N$)")
    ax.set_ylabel("Commit rate (\\% of proposals)")
    ax.set_title(
        "Decision Success Rate vs. Network Size\n"
        r"Loss $=5\%$, random topology, 100 proposals, 3 seeds (mean $\pm$ sd)"
    )
    ax.legend(title="Protocol", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"commit_rate_vs_nodes.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote commit_rate_vs_nodes.png/pdf")


def main():
    if not CSV.exists():
        raise SystemExit(f"Missing {CSV}")
    df = load()
    summary_table(df)
    plot_commit_rate_vs_loss(df)
    plot_commit_rate_vs_nodes(df)
    print("P0 done.")


if __name__ == "__main__":
    main()
