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


def require_per_slot_series(slots, label: str, end_slot: int | None = None) -> None:
    """Guard the amortised-energy path: the snapshot series must be per-slot.

    Equation (5) integrates awake node-slots over each decision's window, so it
    needs one row per *simulated* slot, contiguous from zero. At
    ``snapshot_interval > 1`` the series is a sample, not a series: a 455-slot
    run emits 23 rows at interval 20, and the integral silently loses 95 % of
    the awake node-slots it is meant to sum. The published sweeps use 20 and
    ``config.rs:73`` defaults to 50, so a config that never intended to feed
    this path can reach it.

    The invariant ``len(snapshots) * N == listen + flood + sleep`` therefore
    holds at interval 1 only. Fail loudly rather than rescale.

    Starting at zero with step 1 is necessary but not sufficient: a series can
    satisfy both and still cover only a prefix of the run. The degenerate case
    is a single row at slot 0, which every check below accepted as originally
    written, because the ``len(s) > 1`` ternary substitutes ``step = [1]`` for a
    one-row series. ``results/snapshots_{2pc,paxos,tom}.csv`` in this repository
    are exactly that -- 78 bytes each, a header and one row -- and passed. Pass
    ``end_slot`` from the run's results CSV to require one row per simulated
    slot; without it this guard can only reject the degenerate length-1 case.
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
    if len(s) < 2:
        raise ValueError(
            f"{label}: degenerate snapshot series of {len(s)} row(s) at slot "
            f"{s[0]}. No run that commits a proposal finishes inside a single "
            f"slot, so this file is truncated or was written by a run that never "
            f"ticked. Re-run this configuration with snapshot_interval = 1."
        )
    if end_slot is not None and len(s) < int(end_slot):
        raise ValueError(
            f"{label}: amortised energy requires one row per simulated slot, got "
            f"{len(s)} rows spanning {s[0]}..{s[-1]} for a run that ended at slot "
            f"{int(end_slot)}. Equation (5) would integrate over "
            f"{len(s)}/{int(end_slot)} of the timeline. Re-run this configuration "
            f"with snapshot_interval = 1."
        )
