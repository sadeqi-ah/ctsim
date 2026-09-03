#!/usr/bin/env python3
"""Paper-ready amortized per-decision radio energy figures.

Primary metric (fair under CI pipelining):
  E_i = sum_{t in [s_i, e_i)}  A_t / C_t
  A_t = awake nodes (Listen + Flood) at slot t
  C_t = # proposals with start_slot <= t < end_slot

Outputs (this directory):
  fig_energy_boxplot.{png,pdf}     # primary academic figure
  fig_energy_mean_ci_ce.{png,pdf}  # CI vs CE side-by-side means
  fig_latency_vs_energy.{png,pdf}  # latency–energy trade-off
  fig_energy_stacked.{png,pdf}     # optional distribution (fixed bins)
  energy_summary.csv               # table for paper
  CAPTIONS.md                      # figure captions + method blurb
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = _common.RESULTS_DIR  # <repo>/results, produced by plot_stacked_bar.py
OUT = HERE

PROTOCOLS = [
    ("paxos_pipeline", "Paxos (CI)", "CI", "results_paxos.csv", "snapshots_paxos.csv"),
    ("2pc_pipeline", "2PC (CI)", "CI", "results_2pc.csv", "snapshots_2pc.csv"),
    ("tom_pipeline", "TOM (CI)", "CI", "results_tom.csv", "snapshots_tom.csv"),
    ("paxos_ce", "Paxos (CE)", "CE", "results_paxos_ce.csv", "snapshots_paxos_ce.csv"),
    ("2pc_ce", "2PC (CE)", "CE", "results_2pc_ce.csv", "snapshots_2pc_ce.csv"),
    ("tom_ce", "TOM (CE)", "CE", "results_tom_ce.csv", "snapshots_tom_ce.csv"),
]

# Fixed order for plots (CI then CE, TOM→Paxos→2PC within family)
ORDER = [
    "TOM (CI)",
    "Paxos (CI)",
    "2PC (CI)",
    "TOM (CE)",
    "Paxos (CE)",
    "2PC (CE)",
]

STYLE = {
    "font.family": "serif",
    "font.size": 13,
    "axes.labelsize": 15,
    "axes.titlesize": 16,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11,
    "figure.dpi": 300,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def academic_style():
    plt.rcParams.update(STYLE)


def load_amortized() -> pd.DataFrame:
    """Vectorized amortization from existing result CSVs."""
    rows: list[dict] = []

    for _key, label, phy, res_name, snap_name in PROTOCOLS:
        res_p = RESULTS / res_name
        snap_p = RESULTS / snap_name
        if not res_p.exists() or not snap_p.exists():
            print(f"SKIP {label}: missing {res_p.name} or {snap_p.name}")
            continue

        df_res = pd.read_csv(res_p)
        df_snap = pd.read_csv(snap_p)
        df_snap = df_snap.sort_values("slot").reset_index(drop=True)
        awake = (
            df_snap["nodes_listening"].to_numpy(dtype=np.float64)
            + df_snap["nodes_flooding"].to_numpy(dtype=np.float64)
        )
        slots = df_snap["slot"].to_numpy(dtype=np.int64)

        starts = df_res["start_slot"].to_numpy(dtype=np.int64)
        ends = df_res["end_slot"].to_numpy(dtype=np.int64)
        outcomes = df_res["outcome"].astype(str).to_numpy()
        pids = df_res["proposal_id"].to_numpy()

        # Concurrent live proposals per snapshot slot: C_t
        concurrent = np.zeros(len(slots), dtype=np.float64)
        for s, e in zip(starts, ends):
            concurrent[(slots >= s) & (slots < e)] += 1.0

        # Avoid div-by-zero (should not happen if window non-empty)
        safe_c = np.where(concurrent > 0, concurrent, 1.0)
        cost_per_slot = np.where(concurrent > 0, awake / safe_c, 0.0)

        # Prefix sum for O(1) window sums (slots must be contiguous interval=1)
        # Map slot -> index
        slot_to_i = {int(s): i for i, s in enumerate(slots)}
        pref = np.concatenate([[0.0], np.cumsum(cost_per_slot)])

        for pid, s, e, out in zip(pids, starts, ends, outcomes):
            if out != "committed":
                continue
            # sum cost over slots in [s, e)
            # if snapshots missing some slots, sum only present ones
            idx = [slot_to_i[t] for t in range(int(s), int(e)) if t in slot_to_i]
            if not idx:
                e_cost = 0.0
            else:
                i0, i1 = idx[0], idx[-1] + 1
                e_cost = float(pref[i1] - pref[i0])

            rows.append(
                {
                    "Protocol": label,
                    "PHY": phy,
                    "proposal_id": int(pid),
                    "energy": e_cost,
                    "latency": int(e) - int(s),
                    "start_slot": int(s),
                    "end_slot": int(e),
                }
            )

        n_ok = sum(1 for r in rows if r["Protocol"] == label)
        print(f"{label:12} n_committed={n_ok} mean_E={np.mean([r['energy'] for r in rows if r['Protocol']==label]):.1f}")

    return pd.DataFrame(rows)


def save_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby("Protocol", sort=False)
        .agg(
            n=("energy", "count"),
            energy_mean=("energy", "mean"),
            energy_median=("energy", "median"),
            energy_std=("energy", "std"),
            energy_p25=("energy", lambda x: x.quantile(0.25)),
            energy_p75=("energy", lambda x: x.quantile(0.75)),
            latency_mean=("latency", "mean"),
            latency_median=("latency", "median"),
        )
        .reindex(ORDER)
        .dropna(how="all")
        .reset_index()
    )
    g = g.round(2)
    path = OUT / "energy_summary.csv"
    g.to_csv(path, index=False)
    print(f"Wrote {path}")
    return g


def plot_boxplot(df: pd.DataFrame) -> None:
    academic_style()
    # The stripplot below jitters each point using NumPy's global RNG, so the
    # figure would differ slightly on every run. Seeding here keeps the same
    # data producing the same image.
    np.random.seed(0)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    present = [p for p in ORDER if p in set(df["Protocol"])]
    sns.boxplot(
        data=df,
        x="Protocol",
        y="energy",
        order=present,
        hue="PHY",
        hue_order=["CI", "CE"],
        palette={"CI": "#4C72B0", "CE": "#DD8452"},
        dodge=False,
        width=0.55,
        fliersize=2.5,
        linewidth=1.0,
        ax=ax,
    )
    sns.stripplot(
        data=df,
        x="Protocol",
        y="energy",
        order=present,
        color="0.25",
        size=2.2,
        alpha=0.35,
        jitter=0.18,
        ax=ax,
        legend=False,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Amortized radio-on cost per decision")
    # ax.set_title(
    #     "Per-Decision Energy Footprint (Amortized)\n"
    #     "27 nodes, random topology, 5% loss, 100 committed proposals",
    #     pad=10,
    # )
    ax.tick_params(axis="x", rotation=18)
    # hue legend only
    handles, labels = ax.get_legend_handles_labels()
    # strip may pollute; keep first two CI/CE
    if handles:
        ax.legend(handles[:2], labels[:2], title="PHY", frameon=True, loc="upper left")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_energy_boxplot.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote fig_energy_boxplot.png/pdf")


def plot_mean_ci_ce(summary: pd.DataFrame) -> None:
    academic_style()
    # Pair by base name
    bases = ["TOM", "Paxos", "2PC"]
    ci_means, ce_means = [], []
    for b in bases:
        ci = summary.loc[summary["Protocol"] == f"{b} (CI)", "energy_mean"]
        ce = summary.loc[summary["Protocol"] == f"{b} (CE)", "energy_mean"]
        ci_means.append(float(ci.iloc[0]) if len(ci) else np.nan)
        ce_means.append(float(ce.iloc[0]) if len(ce) else np.nan)

    x = np.arange(len(bases))
    w = 0.36
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        x - w / 2,
        ci_means,
        w,
        label="CI (pipeline)",
        color="#4C72B0",
        edgecolor="black",
        linewidth=0.6,
    )
    ax.bar(
        x + w / 2,
        ce_means,
        w,
        label="CE (Chaos)",
        color="#DD8452",
        edgecolor="black",
        linewidth=0.6,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(bases)
    ax.set_ylabel("Mean amortized energy per decision")
    # ax.set_title(
    #     "Mean Per-Decision Energy: CI vs CE\n"
    #     "Same workload (100 proposals); energy amortized under concurrency",
    #     pad=10,
    # )
    ax.legend(frameon=True)
    # ratio annotation
    for i, (a, b) in enumerate(zip(ci_means, ce_means)):
        if a and b and a > 0:
            ax.text(i, max(a, b) * 1.03, f"CE/CI={b/a:.1f}×", ha="center", fontsize=10)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_energy_mean_ci_ce.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote fig_energy_mean_ci_ce.png/pdf")


def plot_latency_vs_energy(df: pd.DataFrame) -> None:
    academic_style()
    # per-protocol means
    g = (
        df.groupby("Protocol", sort=False)
        .agg(energy=("energy", "mean"), latency=("latency", "mean"), phy=("PHY", "first"))
        .reindex(ORDER)
        .dropna(how="all")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(9, 6))
    
    # 1. Plot the theoretical baseline E = N * L
    # We use logarithmic axes so a linear relation appears as a straight line with slope 1
    # Find latency range
    min_l = max(1, g["latency"].min() * 0.5)
    max_l = g["latency"].max() * 2.0
    l_range = np.logspace(np.log10(min_l), np.log10(max_l), 100)
    
    N = 27
    e_baseline = N * l_range
    
    ax.plot(
        l_range, e_baseline, 
        linestyle="--", color="gray", linewidth=1.5, alpha=0.8, zorder=1,
        label=r"No Amortization / No Duty-Cycle ($E = N \times L$)"
    )
    
    # Shade the "Efficiency" region (below the line)
    ax.fill_between(
        l_range, 1e-1, e_baseline, 
        color="#e6f2ff", alpha=0.4, zorder=0,
        label="Pipeline Energy Savings Region"
    )

    colors = {"CI": "#4C72B0", "CE": "#DD8452"}
    markers = {
        "TOM (CI)": "o",
        "Paxos (CI)": "s",
        "2PC (CI)": "D",
        "TOM (CE)": "^",
        "Paxos (CE)": "v",
        "2PC (CE)": "P",
    }
    for _, r in g.iterrows():
        ax.scatter(
            r["latency"],
            r["energy"],
            s=140,
            c=colors[r["phy"]],
            marker=markers.get(r["Protocol"], "o"),
            edgecolors="black",
            linewidths=1.0,
            zorder=3,
            label=r["Protocol"],
        )
        
        # Smart annotation placement to avoid overlapping the line
        xytext = (8, -12) if r["phy"] == "CE" else (8, 6)
        
        ax.annotate(
            r["Protocol"],
            (r["latency"], r["energy"]),
            textcoords="offset points",
            xytext=xytext,
            fontsize=10,
            zorder=4
        )
        
    ax.set_xlabel("Latency per Committed Decision (slots)")
    ax.set_ylabel("Amortized Energy (node-slots)")
    # ax.set_title(
    #     "Latency vs. Energy Trade-off\n"
    #     "CI pipelines break the $E = N \\times L$ barrier via duty-cycling and concurrency",
    #     pad=15,
    # )
    ax.set_xscale("log")
    ax.set_yscale("log")
    
    # Ensure limits accommodate the line and the shade
    ax.set_ylim(min(g["energy"].min() * 0.5, 40), max(g["energy"].max() * 2.0, 1000))
    ax.set_xlim(min_l, max_l)
    
    ax.legend(frameon=True, fontsize=10, loc="best")
    # ax.legend(title="Protocol", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_latency_vs_energy.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote fig_latency_vs_energy.png/pdf")

def plot_stacked_fixed(df: pd.DataFrame) -> None:
    """Cleaner stacked hist with fixed bins (optional secondary figure)."""
    academic_style()
    # fixed bins for reproducibility
    edges = [0, 50, 100, 150, 200, 300, 400, 500, 700, 1000]
    labels = [f"{edges[i]}–{edges[i+1]}" for i in range(len(edges) - 1)]
    d = df.copy()
    d["bin"] = pd.cut(d["energy"], bins=edges, labels=labels, right=False, include_lowest=True)
    # drop NaN (above max)
    d = d.dropna(subset=["bin"])
    stacked = (
        d.groupby(["bin", "Protocol"], observed=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[p for p in ORDER if p in d["Protocol"].unique()])
    )
    fig, ax = plt.subplots(figsize=(11, 5.5))
    stacked.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        width=0.85,
        edgecolor="black",
        linewidth=0.4,
        colormap="tab10",
    )
    ax.set_xlabel("Amortized energy bin (node-slots)")
    ax.set_ylabel("Number of proposals")
    # ax.set_title(
    #     "Distribution of Amortized Per-Decision Energy\n"
    #     "27 nodes, random, 5% loss, 100 proposals",
    #     pad=10,
    # )
    ax.tick_params(axis="x", rotation=30)
    ax.legend(title="Protocol", frameon=True, fontsize=9, loc="upper right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_energy_stacked.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("Wrote fig_energy_stacked.png/pdf")


def write_captions(summary: pd.DataFrame) -> None:
    # build small markdown table
    lines = [
        "# Paper figures: amortized per-decision energy",
        "",
        "## Method (put in Evaluation / caption)",
        "",
        "For each committed proposal $i$ with lifetime $[s_i, e_i)$, define",
        "",
        "$$E_i = \\sum_{t=s_i}^{e_i-1} \\frac{A_t}{C_t},$$",
        "",
        "where $A_t$ is the number of awake nodes (Listen + Flood) at slot $t$",
        "(from simulator snapshots) and $C_t$ is the number of proposals whose",
        "lifetime covers $t$. This **amortizes** radio activity across concurrent",
        "pipeline proposals and prevents double-counting under CI. CE executes",
        "proposals sequentially ($C_t \\approx 1$), so $E_i \\approx \\sum_t A_t$",
        "over the proposal window.",
        "",
        "Settings: $N{=}27$, random topology, loss rate $5\\%$, $100$ proposals,",
        "abort probability $0$, seed $99$, snapshot interval $1$ slot.",
        "",
        "## Figures",
        "",
        "### Figure: energy boxplot (`fig_energy_boxplot`)",
        "",
        "> **Figure X.** Distribution of amortized radio-on cost per committed decision",
        "> $E_i=\\sum_t A_t/C_t$. Boxes show median and IQR; points are individual proposals.",
        "> CI pipelines share radio activity across concurrent proposals, yielding lower",
        "> per-decision energy than sequential CE despite (for 2PC CI) much larger latency.",
        "",
        "### Figure: CI vs CE means (`fig_energy_mean_ci_ce`)",
        "",
        "> **Figure Y.** Mean amortized energy per decision for TOM, Paxos, and 2PC under",
        "> CI vs CE. Labels show the CE/CI ratio.",
        "",
        "### Figure: latency–energy (`fig_latency_vs_energy`)",
        "",
        "> **Figure Z.** Mean latency vs mean amortized energy (log $x$-axis).",
        "> 2PC (CI) sits far right (high latency) yet low on energy due to amortization;",
        "> 2PC (CE) is both slower-than-TOM and energy-expensive (two-phase + full radio-on).",
        "",
        "### Optional: stacked histogram (`fig_energy_stacked`)",
        "",
        "> Fixed-bin histogram of $E_i$ (secondary view of the same distribution).",
        "",
        "## Summary table (`energy_summary.csv`)",
        "",
        "```",
        summary.to_string(index=False),
        "```",
        "",
        "## Claim-safe wording",
        "",
        "- Safe: *“Under amortized radio-on cost, CI pipelines reduce energy per committed",
        "  decision relative to sequential CE for the same workload.”*",
        "- Safe: *“Latency and energy can diverge under pipelining (2PC CI).”*",
        "- Avoid: *“CI is always faster”* (progress plots show protocol-dependent crossovers).",
        "- Avoid: KDE of per-slot awake counts for CE (zero variance at $N$).",
        "",
    ]
    path = OUT / "CAPTIONS.md"
    path.write_text("\n".join(lines))
    print(f"Wrote {path}")


def main():
    if not RESULTS.is_dir():
        raise SystemExit(f"Missing results dir: {RESULTS}")

    print("Computing amortized energy from", RESULTS)
    df = load_amortized()
    if df.empty:
        raise SystemExit("No data — run plot_stacked_bar.py first to generate results/")

    # persist per-proposal for reuse
    df.to_csv(OUT / "energy_per_proposal.csv", index=False)
    print(f"Wrote {OUT / 'energy_per_proposal.csv'} ({len(df)} rows)")

    summary = save_summary(df)
    print(summary.to_string(index=False))

    plot_boxplot(df)
    plot_mean_ci_ce(summary)
    plot_latency_vs_energy(df)
    plot_stacked_fixed(df)
    write_captions(summary)
    print("Done.")


if __name__ == "__main__":
    main()
