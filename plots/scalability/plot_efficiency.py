#!/usr/bin/env python3
"""Paper-ready figure for Throughput-per-Energy Efficiency.

Metric:
  Efficiency = Throughput / Mean Amortized Energy per Decision
             = (Decisions / Slot) / (Awake Node-Slots / Decision)
             = (Decisions^2) / (Total Slots * Total Amortized Awake Node-Slots)

This emphasizes protocols that are BOTH fast (high throughput) AND energy-efficient (low radio-on time).
"""

import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SUMMARY_CSV = os.path.join(OUT_DIR, "results", "sweep_summary.csv")

def academic_style():
    plt.rcParams.update({
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
    })

def prepare_data():
    if not os.path.exists(SUMMARY_CSV):
        raise FileNotFoundError(f"Missing {SUMMARY_CSV}. Run plot_scalability.py first.")
    
    df = pd.read_csv(SUMMARY_CSV)
    
    # Prettier protocol labels
    labels = {
        'paxos_pipeline': 'Paxos (CI)',
        '2pc_pipeline': '2PC (CI)',
        'tom_pipeline': 'TOM (CI)',
        'paxos_ce': 'Paxos (CE)',
        '2pc_ce': '2PC (CE)',
        'tom_ce': 'TOM (CE)'
    }
    df['Protocol'] = df['protocol'].map(labels)
    
    # 1. Throughput: Decisions / Total Wall-clock Slots
    df['Throughput'] = df['committed'] / df['end_slot'].replace(0, 1)
    
    # 2. Average Energy per Decision
    # Total radio-on slots (Listen + Flood) divided by number of decisions.
    # Note: In a pipeline, this mathematically equals the amortized cost per decision.
    df['Energy_per_Decision'] = (df['listen'] + df['flood']) / df['committed'].replace(0, 1)
    
    # 3. Energy Efficiency: Throughput per Unit of Energy
    # Higher is better: gets many decisions done quickly, using little energy.
    # To make the numbers readable on a chart (avoiding 0.0000x), we multiply by 10^3 or 10^4.
    # Let's scale it to "Decisions per 1000 Node-Slots of Energy per Wall-clock Slot"
    df['Efficiency'] = (df['Throughput'] / df['Energy_per_Decision']) * 1000
    
    return df

def plot_efficiency_vs_nodes(df):
    academic_style()
    # Filter for standard condition: Loss = 5%
    df_sub = df[df['loss_rate'] == 0.05]
    
    fig, ax = plt.subplots(figsize=(7, 6))
    
    sns.lineplot(
        data=df_sub,
        x='nodes',
        y='Efficiency',
        hue='Protocol',
        style='Protocol',
        markers=True,
        dashes=True,
        linewidth=2.5,
        markersize=9,
        palette="tab10",
        # Seaborn's default errorbar bootstraps over the 15 seeds using NumPy's
        # global RNG; a fixed seed keeps the band identical across runs.
        seed=0,
        ax=ax
    )
    
    ax.set_xticks(sorted(df_sub['nodes'].unique()))
    ax.set_yscale("log") # Log scale shows the magnitude of CI dominance clearly
    ax.set_xlabel("Number of Nodes ($N$)")
    ax.set_ylabel("Energy Efficiency (Score) - Log Scale\n$\\propto$ Throughput / Energy per Decision")
    # ax.set_title("Throughput-to-Energy Efficiency vs. Network Size\n(Random Topology, Loss = 5%, 100 Proposals)")
    
    # ax.legend(title="Protocol", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.legend(title="Protocol", framealpha=0.9, loc="upper right", frameon=True)
    fig.tight_layout()
    
    fig.savefig(os.path.join(OUT_DIR, "efficiency_vs_nodes.pdf"))
    fig.savefig(os.path.join(OUT_DIR, "efficiency_vs_nodes.png"))
    plt.close(fig)
    print("Wrote efficiency_vs_nodes.png")

def main():
    df = prepare_data()
    plot_efficiency_vs_nodes(df)
    print("Efficiency plot generated successfully.")

if __name__ == "__main__":
    main()
