#!/usr/bin/env python3
r"""Collect the figure PDFs the paper needs into paper/figures/.

The plot scripts under plots/** write their output next to themselves, and
every *.pdf is git-ignored (see .gitignore), so no figure is ever committed.
paper/paper.tex declares \graphicspath{{figures/}} and includes each figure
by bare file name, so the PDFs have to appear under paper/figures/ before
pdflatex runs.

This script is the single place where the mapping between a generated file
and the name the paper expects is written down. It only copies; it never
runs a simulation and never generates a figure. Run tools/regen_figures.py
(or the individual plot scripts) first.

Usage:
  python3 tools/collect_paper_figures.py            # copy whatever exists
  python3 tools/collect_paper_figures.py --check    # report only, no writes
  python3 tools/collect_paper_figures.py --list     # print the mapping
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEST_DIR = REPO_ROOT / "paper" / "figures"

# Name used by \includegraphics  ->  path of the generated file, repo-relative.
MAPPING: dict[str, str] = {
    "throughput_vs_nodes.pdf": "plots/scalability/throughput_vs_nodes.pdf",
    "latency_vs_nodes.pdf": "plots/scalability/latency_vs_nodes.pdf",
    "throughput_vs_loss.pdf": "plots/scalability/throughput_vs_loss.pdf",
    "efficiency_vs_nodes.pdf": "plots/scalability/efficiency_vs_nodes.pdf",
    "progress_over_time.pdf": "plots/progress/progress_over_time.pdf",
    "progress_over_time_log.pdf": "plots/progress/progress_over_time_log.pdf",
    "energy_mean_ci_ce.pdf": "plots/energy/fig_energy_mean_ci_ce.pdf",
    "energy_boxplot.pdf": "plots/energy/fig_energy_boxplot.pdf",
    "latency_vs_energy.pdf": "plots/energy/fig_latency_vs_energy.pdf",
    "throughput_vs_topology.pdf": "plots/topology/thr_vs_topology.pdf",
    "latency_vs_topology.pdf": "plots/topology/lat_vs_topology.pdf",
}

# Figures the paper includes that no script generates: hand-drawn diagrams.
# They are git-ignored too, so they have to be placed in paper/figures/ by
# hand until a source for them exists.
DIAGRAMS: tuple[str, ...] = (
    "pipeline_mechanism.pdf",
    "message_frame.pdf",
    "paxos_ci_example.pdf",
)


def cmd_list() -> int:
    print(f"{'paper/figures/<name>':<30} <- generated file")
    for dest, src in MAPPING.items():
        print(f"{dest:<30} <- {src}")
    for dest in DIAGRAMS:
        print(f"{dest:<30} <- (hand-drawn, no generator)")
    print(
        f"\n{len(MAPPING)} generated + {len(DIAGRAMS)} hand-drawn = "
        f"{len(MAPPING) + len(DIAGRAMS)} figures"
    )
    return 0


def cmd_check() -> int:
    missing_src: list[str] = []
    for dest, src in MAPPING.items():
        if (REPO_ROOT / src).is_file():
            print(f"OK      {dest:<30} <- {src}")
        else:
            print(f"MISSING {dest:<30} <- {src}")
            missing_src.append(dest)

    missing_diag: list[str] = []
    for dest in DIAGRAMS:
        if (DEST_DIR / dest).is_file():
            print(f"OK      {dest:<30} (hand-drawn, already in place)")
        else:
            print(f"MISSING {dest:<30} (hand-drawn, no generator)")
            missing_diag.append(dest)

    if not missing_src and not missing_diag:
        print("\nAll figures accounted for.")
        return 0
    if missing_src:
        print("\nNot generated yet: " + ", ".join(missing_src))
        print("Run tools/regen_figures.py (or the plot scripts) first.")
    if missing_diag:
        print(
            "\nHand-drawn diagrams absent from paper/figures/: "
            + ", ".join(missing_diag)
        )
    return 1


def cmd_copy() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing: list[str] = []
    for dest, src in MAPPING.items():
        src_path = REPO_ROOT / src
        if not src_path.is_file():
            print(f"MISSING {dest:<30} <- {src}")
            missing.append(dest)
            continue
        shutil.copy2(src_path, DEST_DIR / dest)
        print(f"COPIED  {dest:<30} <- {src}")
        copied += 1

    for dest in DIAGRAMS:
        if (DEST_DIR / dest).is_file():
            print(f"KEPT    {dest:<30} (hand-drawn, already in place)")
        else:
            print(f"MISSING {dest:<30} (hand-drawn, no generator)")
            missing.append(dest)

    print(
        f"\n{copied}/{len(MAPPING)} generated figures copied into "
        f"{DEST_DIR.relative_to(REPO_ROOT)}/"
    )
    if missing:
        print("Still missing: " + ", ".join(missing))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy generated figure PDFs into paper/figures/."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="report what is present or missing; write nothing",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="print the figure mapping and exit",
    )
    args = parser.parse_args()

    if args.list:
        return cmd_list()
    if args.check:
        return cmd_check()
    return cmd_copy()


if __name__ == "__main__":
    sys.exit(main())
