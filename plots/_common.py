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


def require_per_slot_series(slots, label: str) -> None:
    """Guard the amortised-energy path: the snapshot series must be per-slot.

    Equation (5) integrates awake node-slots over each decision's window, so it
    needs one row per *simulated* slot, contiguous from zero. At
    ``snapshot_interval > 1`` the series is a SAMPLE, not a series: a 455-slot
    run emits 23 rows at interval 20, and the integral silently loses 95 % of
    the awake node-slots it is supposed to sum. The published sweeps use 20 and
    ``config.rs:73`` defaults to 50, so a config that never intended to feed
    this path can reach it.

    The invariant ``len(snapshots) * N == listen + flood + sleep`` therefore
    holds at interval 1 only. Fail loudly rather than rescale: a rescaled
    integral would be a plausible-looking number with no physical meaning.
    """
    import numpy as np

    s = np.asarray(slots, dtype=np.int64)
    if len(s) == 0:
        raise ValueError(f"{label}: empty snapshot series")
    step = np.unique(np.diff(s)) if len(s) > 1 else np.array([1])
    if s[0] != 0 or step.tolist() not in ([1], []):
        raise ValueError(
            f"{label}: amortised energy requires a per-slot snapshot series "
            f"(snapshot_interval = 1), got slots starting at {s[0]} with step(s) "
            f"{step.tolist()} over {len(s)} rows spanning {s[0]}..{s[-1]}. "
            f"Re-run this configuration with snapshot_interval = 1."
        )
