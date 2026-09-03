"""Shared helpers for the figure-generation scripts.

Every plot script is self-contained: it (re)runs the Rust simulator to produce
fresh CSV data under ``<repo>/results`` and writes its figures next to itself.
These helpers make that work regardless of the current working directory.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Repo root is two levels up from this file: <repo>/plots/_common.py
REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"


def academic_style():
    """Consistent, paper-ready Matplotlib defaults."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
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
        }
    )


def build_release():
    """Compile the simulator in release mode (once per script run)."""
    subprocess.run(["cargo", "build", "--release"], cwd=REPO_ROOT, check=True)


def run_config(toml_path) -> None:
    """Run one simulation config. Output CSVs land in ``<repo>/results``."""
    subprocess.run(
        ["cargo", "run", "--release", "--", str(toml_path)],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_sweep(toml_path) -> None:
    """Run a parameter sweep config (writes its own output_dir)."""
    subprocess.run(
        ["cargo", "run", "--release", "--", str(toml_path)],
        cwd=REPO_ROOT,
        check=True,
    )


def results_csv(name: str) -> Path:
    """Absolute path to a file inside ``<repo>/results``."""
    return RESULTS_DIR / name


# CLI shortens pipeline protocol names when writing CSVs
# (e.g. ``paxos_pipeline`` -> ``results/snapshots_paxos.csv``).
_PIPELINE_STEM = {
    "paxos_pipeline": "paxos",
    "2pc_pipeline": "2pc",
    "tom_pipeline": "tom",
}


def snapshot_csv(protocol: str) -> Path:
    return results_csv(f"snapshots_{_PIPELINE_STEM.get(protocol, protocol)}.csv")


def results_csv_for(protocol: str) -> Path:
    return results_csv(f"results_{_PIPELINE_STEM.get(protocol, protocol)}.csv")
