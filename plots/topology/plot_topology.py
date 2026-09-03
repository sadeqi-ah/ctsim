#!/usr/bin/env python3
"""Topology sensitivity analysis (CI vs CE).

Generates:
  1. thr_vs_topology.{png,pdf}
  2. lat_vs_topology.{png,pdf}
  3. energy_vs_topology.{png,pdf}
  4. efficiency_vs_topology.{png,pdf}
  5. table_topology_N27_loss05.csv / .tex
  6. CAPTIONS.md

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
    (OUT / "table_topology_N27_loss05.tex").write_text(
        "% N=27, loss=5%, 100 proposals, 3 seeds (mean)\n"
        "% Thr=committed/end_slot; Energy/dec=(listen+flood)/committed\n"
        + "\n".join(lines)
    )
    print("Wrote table_topology_N27_loss05.csv / .tex")
    return g


def write_captions(g: pd.DataFrame):
    text = f"""# Topology sensitivity captions

**Settings:** $N{{=}}27$, loss $5\\%$, $100$ proposals, seeds $\\{{99,12345,42\\}}$.
Topologies ordered sparse$\\to$dense: Line, Partial mesh, Random, Scale-free, Full mesh.

## What to look for

| Expectation | Why |
|-------------|-----|
| Line worst thr / highest lat | Diameter $N-1$; floods take many slots |
| Full mesh best thr / lowest lat | Diameter 1; one hop |
| CE more sensitive to diameter | Goal-based rounds stretch with hop count; always-on radio |
| CI less sensitive on thr | Fixed flood rounds + pipeline amortize diameter cost |
| Energy: CE $\\approx N\\cdot L$ still | Topology changes $L$, thus $E$ |
| Energy: CI stays lower | Duty-cycle after flood wave |

## Figure: thr_vs_topology

> **Figure T1.** Throughput versus topology at $N{{=}}27$ and $5\\%$ loss (mean $\\pm$ s.d. over three seeds).
> Sparse graphs (line) reduce throughput for all protocols; dense graphs (full mesh) raise it.
> CI pipelines for Paxos/2PC remain competitive with, or above, their CE counterparts across topologies.
> TOM (CE) often leads on dense graphs where short dissemination rounds dominate.

## Figure: lat_vs_topology

> **Figure T2.** Mean decision latency versus topology (log scale if needed).
> Latency grows with diameter: line $\\gg$ random $\\approx$ partial mesh $\\gtrsim$ scale-free $>$ full mesh.
> 2PC (CI) remains highest latency (pipeline + unanimity) but still completes under all topologies tested.
> CE latencies track diameter closely (goal-based round length).

## Figure: energy_vs_topology

> **Figure T3.** Mean radio-on energy per committed decision, $(\\mathrm{{Listen}}+\\mathrm{{Flood}})/\\mathrm{{committed}}$.
> CE energy scales with round length and thus with diameter; CI energy stays lower via duty-cycling.
> Topology does not reverse the CI energy advantage.

## Figure: efficiency_vs_topology

> **Figure T4.** Energy efficiency $\\propto$ Throughput / Energy-per-decision.
> CI protocols keep the highest efficiency across topologies; the gap widens on sparse graphs where CE rounds become long and fully awake.

## Table

`table_topology_N27_loss05.csv` / `.tex` — means over seeds.

### Snapshot means

```
{g.to_string(index=False)}
```

## Placement

After scalability-vs-$N$ (or as a short subsection **Topology sensitivity**).
One paragraph: *results are qualitatively robust; diameter shifts absolute thr/lat but not CI vs CE energy ranking.*
"""
    (OUT / "CAPTIONS.md").write_text(text)
    print("Wrote CAPTIONS.md")


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
    write_captions(g)
    print("Topology analysis done.")


if __name__ == "__main__":
    main()
