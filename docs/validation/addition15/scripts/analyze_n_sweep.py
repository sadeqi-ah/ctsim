#!/usr/bin/env python3
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "docs/validation/addition15/data"
ROWS = list(csv.DictReader((DATA / "n_sweep.csv").open()))
PROV = list(csv.DictReader((DATA / "graph_provenance_dense.csv").open()))
REFERENCES = {"2pc_ce": 100.0, "paxos_ce": 57.8}


def mean_se(values):
    values = np.asarray(values, dtype=float)
    return float(values.mean()), float(values.std(ddof=1) / math.sqrt(len(values)))


def weighted_fits(xs, ys, ses):
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    se = np.asarray(ses, dtype=float)
    w = 1.0 / np.maximum(se, 1e-12) ** 2
    out = {}
    for name, design in [("constant", np.ones((len(x), 1))), ("linear", np.column_stack([np.ones(len(x)), x]))]:
        xtwx = design.T @ (w[:, None] * design)
        beta = np.linalg.solve(xtwx, design.T @ (w * y))
        fitted = design @ beta
        residual = y - fitted
        rss = float(np.sum(w * residual**2))
        k = design.shape[1]
        aic = len(x) * math.log(max(rss / len(x), 1e-300)) + 2 * k
        weighted_mean = float(np.sum(w * y) / np.sum(w))
        tss = float(np.sum(w * (y - weighted_mean) ** 2))
        r2 = 1.0 - rss / tss if tss else 1.0
        sigma2 = rss / (len(x) - k)
        covariance = sigma2 * np.linalg.inv(xtwx)
        slope = float(beta[-1]) if k == 2 else 0.0
        slope_se = math.sqrt(float(covariance[-1, -1])) if k == 2 else 0.0
        out[name] = {"beta": beta, "aic": aic, "r2": r2, "slope": slope, "lo": slope - 1.96 * slope_se, "hi": slope + 1.96 * slope_se}
    return out


prov = {(int(r["n"]), int(r["seed"])): r for r in PROV}
groups = defaultdict(list)
for row in ROWS:
    row["n"] = int(row["n"])
    row["seed"] = int(row["seed"])
    row["mean_round_slots"] = float(row["mean_round_slots"])
    row["mean_decision_latency_slots"] = float(row["mean_decision_latency_slots"])
    row["committed"] = int(row["committed"])
    row["proposals"] = int(row["proposals"])
    groups[(row["n"], row["arm"])].append(row)

summary = []
for (n, arm), cells in sorted(groups.items()):
    rounds = [r["mean_round_slots"] for r in cells]
    decisions = [r["mean_decision_latency_slots"] for r in cells]
    round_mean, round_se = mean_se(rounds)
    latency_mean, latency_se = mean_se(decisions)
    residuals = [REFERENCES[arm] / value for value in rounds]
    residual_mean, residual_se = mean_se(residuals)
    degrees = [float(prov[(n, r["seed"])]["mean_degree"]) for r in cells]
    variances = [float(prov[(n, r["seed"])]["degree_variance"]) for r in cells]
    diameters = [int(prov[(n, r["seed"])]["diameter"]) for r in cells]
    summary.append({
        "n": n,
        "arm": arm,
        "mean_degree": np.mean(degrees),
        "mean_degree_variance": np.mean(variances),
        "mean_diameter": np.mean(diameters),
        "mean_round_slots": round_mean,
        "round_slots_se": round_se,
        "mean_decision_latency_slots": latency_mean,
        "decision_latency_se": latency_se,
        "reference_slots": REFERENCES[arm],
        "structural_residual": residual_mean,
        "structural_residual_se": residual_se,
        "commit_rate": sum(r["committed"] for r in cells) / sum(r["proposals"] for r in cells),
        "zero_commit_seeds": "|".join(str(r["seed"]) for r in cells if not r["committed"]),
    })

fields = list(summary[0])
with (DATA / "n_sweep_summary.csv").open("w", newline="") as out:
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(summary)

fits = {}
for arm in ["2pc_ce", "paxos_ce"]:
    cells = [r for r in summary if r["arm"] == arm]
    xs = [r["n"] for r in cells]
    fits[(arm, "residual")] = weighted_fits(xs, [r["structural_residual"] for r in cells], [r["structural_residual_se"] for r in cells])
    fits[(arm, "round_length")] = weighted_fits(xs, [r["mean_round_slots"] for r in cells], [r["round_slots_se"] for r in cells])

with (DATA / "fits.csv").open("w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["arm", "quantity", "model", "slope", "slope_ci95_low", "slope_ci95_high", "aic", "r_squared"])
    for (arm, quantity), models in fits.items():
        for model, fit in models.items():
            writer.writerow([arm, quantity, model, f"{fit['slope']:.9f}", f"{fit['lo']:.9f}", f"{fit['hi']:.9f}", f"{fit['aic']:.6f}", f"{fit['r2']:.6f}"])

for quantity, ykey, sekey, ylabel, filename in [
    ("residual", "structural_residual", "structural_residual_se", "Structural residual (reference / simulated)", "residual_vs_n.png"),
    ("round_length", "mean_round_slots", "round_slots_se", "Mean round length (slots)", "round_length_vs_n.png"),
]:
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for arm, label, marker in [("2pc_ce", "2PC over CE", "o"), ("paxos_ce", "Paxos over CE", "s")]:
        cells = [r for r in summary if r["arm"] == arm]
        x = np.asarray([r["n"] for r in cells], dtype=float)
        y = np.asarray([r[ykey] for r in cells], dtype=float)
        se = np.asarray([r[sekey] for r in cells], dtype=float)
        ax.errorbar(x, y, yerr=se, marker=marker, capsize=3, linestyle="none", label=label)
        grid = np.linspace(x.min(), x.max(), 100)
        linear = fits[(arm, quantity)]["linear"]["beta"]
        constant = fits[(arm, quantity)]["constant"]["beta"]
        ax.plot(grid, linear[0] + linear[1] * grid, linewidth=1.5)
        ax.plot(grid, np.full_like(grid, constant[0]), linewidth=1.0, linestyle="--")
    ax.set_xlabel("N")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT / "docs/validation/addition15" / filename, dpi=300)
    plt.close(fig)

print(f"rows={len(ROWS)} summary={len(summary)}")
for key, models in fits.items():
    print(key, models)
