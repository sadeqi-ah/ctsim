#!/usr/bin/env python3
"""Paper-ready figures for Throughput and Scalability.

Generates:
  1. throughput_vs_nodes.{png,pdf} (fixed loss=0.05)
  2. latency_vs_nodes.{png,pdf}    (fixed loss=0.05)
  3. throughput_vs_loss.{png,pdf}  (fixed N=27)

Runs the sweep if the summary CSV does not exist or if forced.
"""

import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SWEEP_TOML = os.path.join(ROOT, "sweep_scalability.toml")
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

def run_sweep_if_needed():
    import sys
    if not os.path.exists(SUMMARY_CSV) or "--force" in sys.argv:
        print("Running simulator sweep for scalability... (this may take a few minutes)")
        subprocess.run(
            ["cargo", "run", "--release", "--", "sweep_scalability.toml"],
            cwd=ROOT,
            check=True
        )

def prepare_data():
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
    
    # Calculate Throughput: Decisions completed / total slots needed to finish the workload
    # We use 'end_slot' which is the max end_slot across all proposals.
    # Avoid div by 0 just in case
    df['Throughput (Decisions/Slot)'] = df['committed'] / df['end_slot'].replace(0, 1)
    
    return df

def plot_throughput_vs_nodes(df):
    academic_style()
    # Filter for standard condition: Loss = 5%
    df_sub = df[df['loss_rate'] == 0.05]
    
    fig, ax = plt.subplots(figsize=(7, 6))
    
    sns.lineplot(
        data=df_sub,
        x='nodes',
        y='Throughput (Decisions/Slot)',
        hue='Protocol',
        style='Protocol',
        markers=True,
        dashes=True,
        linewidth=2,
        markersize=8,
        palette="tab10",
        # Seaborn's default errorbar is a bootstrap CI over the 15 seeds, and the
        # bootstrap draws from NumPy's global RNG. Without a fixed seed the band
        # shifts slightly on every run, so the same data yields a different PNG.
        seed=0,
        ax=ax
    )
    
    ax.set_xticks(sorted(df_sub['nodes'].unique()))
    ax.set_xlabel("Number of Nodes ($N$)")
    ax.set_ylabel("Throughput (Decisions / Slot)")
    # ax.set_title("Throughput Scalability vs. Network Size\n(Random Topology, Loss = 5%, 100 Proposals)")
    
    ax.legend(title="Protocol", framealpha=0.9, loc="upper right", frameon=True)
    fig.tight_layout()
    
    fig.savefig(os.path.join(OUT_DIR, "throughput_vs_nodes.pdf"))
    fig.savefig(os.path.join(OUT_DIR, "throughput_vs_nodes.png"))
    plt.close(fig)
    print("Wrote throughput_vs_nodes.png")

def plot_latency_vs_nodes(df):
    academic_style()
    # Filter for standard condition: Loss = 5%
    df_sub = df[df['loss_rate'] == 0.05]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.lineplot(
        data=df_sub,
        x='nodes',
        y='avg_latency',
        hue='Protocol',
        style='Protocol',
        markers=True,
        dashes=True,
        linewidth=2,
        markersize=8,
        palette="tab10",
        seed=0,  # deterministic bootstrap CI (see plot_throughput_vs_nodes)
        ax=ax
    )
    
    ax.set_xticks(sorted(df_sub['nodes'].unique()))
    ax.set_yscale("log")  # Latency can vary wildly between CI 2PC and TOM CE
    ax.set_xlabel("Number of Nodes ($N$)")
    ax.set_ylabel("Latency per Decision (Slots) - Log Scale")
    # ax.set_ylabel("Mean Latency per Decision (Slots) - Log Scale")
    # ax.set_title("Decision Latency Scalability vs. Network Size\n(Random Topology, Loss = 5%, 100 Proposals)")
    
    ax.legend(title="Protocol", bbox_to_anchor=(1.05, 1), loc='upper left')
    # ax.legend(title="Protocol", framealpha=0.8, loc="upper left", frameon=True)

    fig.tight_layout()
    
    fig.savefig(os.path.join(OUT_DIR, "latency_vs_nodes.pdf"))
    fig.savefig(os.path.join(OUT_DIR, "latency_vs_nodes.png"))
    plt.close(fig)
    print("Wrote latency_vs_nodes.png")

def plot_throughput_vs_loss(df):
    academic_style()
    # Filter for standard condition: N = 27
    df_sub = df[df['nodes'] == 27]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.lineplot(
        data=df_sub,
        x='loss_rate',
        y='Throughput (Decisions/Slot)',
        hue='Protocol',
        style='Protocol',
        markers=True,
        dashes=True,
        linewidth=2,
        markersize=8,
        palette="tab10",
        seed=0,  # deterministic bootstrap CI (see plot_throughput_vs_nodes)
        ax=ax
    )
    
    ax.set_xticks(sorted(df_sub['loss_rate'].unique()))
    ax.set_xlabel("Link Loss Rate")
    ax.set_ylabel("Throughput (Decisions / Slot)")
    # ax.set_title("Throughput Resilience under Packet Loss\n($N=27$, Random Topology, 100 Proposals)")
    
    ax.legend(title="Protocol", bbox_to_anchor=(1.05, 1), loc='upper left')
    # ax.legend(title="Protocol", framealpha=0.8, loc="upper right", frameon=True)

    fig.tight_layout()
    
    fig.savefig(os.path.join(OUT_DIR, "throughput_vs_loss.pdf"))
    fig.savefig(os.path.join(OUT_DIR, "throughput_vs_loss.png"))
    plt.close(fig)
    print("Wrote throughput_vs_loss.png")

def main():
    run_sweep_if_needed()
    df = prepare_data()
    plot_throughput_vs_nodes(df)
    plot_latency_vs_nodes(df)
    plot_throughput_vs_loss(df)
    print("All scalability plots generated successfully.")

if __name__ == "__main__":
    main()
