#!/usr/bin/env python3
"""Regenerate every paper figure, and diff the result against a saved set.

Two uses:

  python3 tools/regen_figures.py                    # run everything, write MANIFEST.sha256
  python3 tools/regen_figures.py --compare <dir>    # diff current artifacts vs a saved copy

The comparison is data-first. Numeric artifacts (CSV/TeX) are hashed byte-wise:
those are the scientific content, and the simulator is deterministic for a fixed
seed, so any difference is a real difference. PNGs are compared as decoded pixel
arrays rather than as files, because Matplotlib stamps its version into the PNG
header -- two runs of the same data on different Matplotlib versions give
different file bytes but identical pixels. PDFs embed a creation timestamp and
can never be hash-compared; they are listed but not diffed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (script, label) in dependency order. Two hard dependencies:
#   scalability/plot_scalability.py writes the sweep CSV the next two read
#   energy/plot_stacked_bar.py      writes the results/ CSVs plot_paper_energy reads
STEPS = [
    ("plots/scalability/plot_scalability.py", "scalability sweep (1800 cells, incl. N=188)"),
    ("plots/scalability/plot_efficiency.py", "efficiency vs N"),
    ("plots/scalability/plot_summary_commit.py", "commit rate + summary table"),
    ("plots/topology/plot_topology.py", "topology sensitivity sweep"),
    ("plots/progress/plot_progress.py", "progress over time (linear)"),
    ("plots/progress/plot_progress_log.py", "progress over time (log)"),
    ("plots/energy/plot_stacked_bar.py", "per-proposal energy + results/ CSVs"),
    ("plots/energy/plot_paper_energy.py", "amortized energy figures"),
    ("plots/duty_cycle/plot_kde_awake.py", "awake PMF + duty-cycle extremes"),
]

# Artifacts to fingerprint inside the repo, relative to the repo root.
GLOBS = ["plots/**/*.png", "plots/**/*.csv", "plots/**/*.tex", "results/*.csv"]

# A saved reference set may be any shape: a full repo copy, or just a folder of
# PNGs. Search it recursively and skip build/venv noise.
REF_GLOBS = ["**/*.png", "**/*.csv", "**/*.tex"]
REF_SKIP = {"target", "venv", ".git", "__pycache__", "node_modules", ".venv"}

DATA_EXT = {".csv", ".tex"}
PIXEL_EXT = {".png"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pixel_hash(path: Path) -> tuple[str, tuple]:
    """Hash a PNG's decoded pixels, ignoring file metadata."""
    import numpy as np
    from PIL import Image

    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA"))
    return sha256_bytes(arr.tobytes()), arr.shape


def fingerprint(root: Path, globs: list[str] | None = None) -> dict[str, dict]:
    """Map relative path -> fingerprint record for every artifact under root."""
    out: dict[str, dict] = {}
    for pattern in globs or GLOBS:
        for p in sorted(root.glob(pattern)):
            if not p.is_file():
                continue
            rel_parts = p.relative_to(root).parts
            if REF_SKIP.intersection(rel_parts):
                continue
            rel = str(p.relative_to(root))
            ext = p.suffix.lower()
            if ext in PIXEL_EXT:
                h, shape = pixel_hash(p)
                out[rel] = {"kind": "pixels", "sha256": h, "shape": list(shape)}
            elif ext in DATA_EXT:
                out[rel] = {
                    "kind": "data",
                    "sha256": sha256_bytes(p.read_bytes()),
                    "bytes": p.stat().st_size,
                }
    return out


def run_steps(only: list[str] | None, force: bool) -> bool:
    print(f"Building simulator (release) in {REPO}")
    subprocess.run(["cargo", "build", "--release"], cwd=REPO, check=True)

    steps = STEPS
    if only:
        steps = [(s, lbl) for s, lbl in STEPS if any(k in s for k in only)]
        if not steps:
            sys.exit(f"--only {only} matched no step")

    ok = True
    total = len(steps)
    for i, (script, label) in enumerate(steps, 1):
        cmd = [sys.executable, script] + (["--force"] if force else [])
        print(f"\n[{i}/{total}] {label}\n      {' '.join(cmd)}", flush=True)
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        dt = time.time() - t0
        if proc.returncode == 0:
            print(f"      ok  ({dt:.1f}s)", flush=True)
        else:
            ok = False
            print(f"      FAILED (exit {proc.returncode}, {dt:.1f}s)", flush=True)
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-15:]
            for line in tail:
                print(f"      | {line}")
    return ok


def compare(ref_root: Path) -> int:
    cur = fingerprint(REPO)
    ref = fingerprint(ref_root, REF_GLOBS)

    # A saved figure set is often a flat folder of PNGs rather than a repo copy.
    # If nothing lines up by relative path, fall back to matching on filename.
    by_path = set(cur) & set(ref)
    if not by_path and cur and ref:
        cur_base = {Path(k).name: k for k in cur}
        ref_base = {Path(k).name: k for k in ref}
        shared = sorted(set(cur_base) & set(ref_base))
        if shared:
            print(f"reference has no matching layout; matching {len(shared)} artifacts by filename\n")
            cur = {b: cur[cur_base[b]] for b in cur_base}
            ref = {b: ref[ref_base[b]] for b in ref_base}
            cur_root = {b: REPO / cur_base[b] for b in cur_base}
            ref_root_map = {b: ref_root / ref_base[b] for b in ref_base}
            return _report(cur, ref, cur_root, ref_root_map, REPO, ref_root)

    cur_root = {rel: REPO / rel for rel in cur}
    ref_root_map = {rel: ref_root / rel for rel in ref}
    return _report(cur, ref, cur_root, ref_root_map, REPO, ref_root)


def _report(cur, ref, cur_paths, ref_paths, cur_label, ref_label) -> int:
    same, diff, missing, new = [], [], [], []
    for rel in sorted(set(cur) | set(ref)):
        if rel not in ref:
            new.append(rel)
        elif rel not in cur:
            missing.append(rel)
        elif cur[rel]["sha256"] == ref[rel]["sha256"]:
            same.append(rel)
        else:
            diff.append(rel)

    print(f"reference: {ref_label}")
    print(f"current:   {cur_label}")
    print(f"\n{len(same)} identical, {len(diff)} differ, {len(missing)} missing here, {len(new)} not in reference")

    if same:
        print("\nIDENTICAL:")
        for rel in same:
            print(f"  {rel}")

    if diff:
        print("\nDIFFER:")
        for rel in diff:
            p_cur, p_ref = cur_paths[rel], ref_paths[rel]
            if cur[rel]["kind"] == "pixels" and ref[rel]["kind"] == "pixels":
                detail = _png_detail(p_cur, p_ref, cur[rel], ref[rel])
            else:
                detail = _csv_detail(p_cur, p_ref)
            print(f"  {rel}\n      {detail}")

    if missing:
        print("\nIN REFERENCE BUT NOT REGENERATED (a script did not run, or an output was renamed):")
        for rel in missing:
            print(f"  {rel}")
    if new:
        print("\nNEW (not in the reference set):")
        for rel in new:
            print(f"  {rel}")

    print("\nnote: PDFs are not compared (they embed a creation timestamp).")
    return 1 if (diff or missing) else 0


def _png_detail(p_cur: Path, p_ref: Path, rec_cur: dict, rec_ref: dict) -> str:
    if rec_cur["shape"] != rec_ref["shape"]:
        return f"different image size: {rec_cur['shape']} vs {rec_ref['shape']}"
    import numpy as np
    from PIL import Image

    with Image.open(p_cur) as a, Image.open(p_ref) as b:
        x = np.asarray(a.convert("RGBA"), dtype=np.int16)
        y = np.asarray(b.convert("RGBA"), dtype=np.int16)
    d = np.abs(x - y)
    frac = float((d.any(axis=-1)).mean())
    return f"pixels differ: {frac*100:.3f}% of pixels, max channel delta {int(d.max())}"


def _csv_detail(p_cur: Path, p_ref: Path) -> str:
    a = p_cur.read_text(errors="replace").splitlines()
    b = p_ref.read_text(errors="replace").splitlines()
    if len(a) != len(b):
        return f"different line count: {len(a)} vs {len(b)}"
    for i, (la, lb) in enumerate(zip(a, b), 1):
        if la != lb:
            return f"first difference at line {i}:\n        now: {la[:160]}\n        ref: {lb[:160]}"
    return "content matches but bytes differ (line endings?)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--compare", metavar="DIR", help="diff current artifacts against a saved copy of the repo")
    ap.add_argument("--only", nargs="+", metavar="KEY", help="run only steps whose path contains one of these")
    ap.add_argument("--force", action="store_true", help="re-run cached sweeps instead of reusing their CSV")
    ap.add_argument("--no-run", action="store_true", help="only fingerprint what is already on disk")
    args = ap.parse_args()

    if args.compare:
        ref = Path(args.compare).expanduser().resolve()
        if not ref.is_dir():
            sys.exit(f"not a directory: {ref}")
        return compare(ref)

    if not args.no_run:
        if not run_steps(args.only, args.force):
            print("\nAt least one step failed; the manifest below covers only what was produced.")

    fp = fingerprint(REPO)
    manifest = REPO / "MANIFEST.sha256"
    lines = [f"{rec['sha256']}  {rel}" for rel, rec in sorted(fp.items())]
    manifest.write_text("\n".join(lines) + "\n")
    (REPO / "MANIFEST.json").write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
    print(f"\nFingerprinted {len(fp)} artifacts -> {manifest.name}, MANIFEST.json")
    print("PNG hashes are of decoded pixels, so they are comparable across Matplotlib builds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
