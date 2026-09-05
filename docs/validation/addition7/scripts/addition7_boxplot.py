#!/usr/bin/env python3
"""ADDITION 7 deliverable c — the boxplot, 15 seeds pooled.

Reads /tmp/ctsim_validate/addition7/decisions.csv and writes the figure into the
repository's energy plot directory. Log y, because the CE arms are an order of
magnitude above the CI arms and a linear axis flattens the CI boxes to lines.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUT = "/Users/amir/Projects/ctsim/plots/energy"
LABEL = {"tom_pipeline": "TOM (CI)", "paxos_pipeline": "Paxos (CI)",
         "2pc_pipeline": "2PC (CI)", "tom_ce": "TOM (CE)",
         "paxos_ce": "Paxos (CE)", "2pc_ce": "2PC (CE)"}
ORDER = [LABEL[k] for k in ["tom_pipeline", "paxos_pipeline", "2pc_pipeline",
                            "tom_ce", "paxos_ce", "2pc_ce"]]

d = pd.read_csv(f"{WORK}/decisions.csv")
d["Protocol"] = d.protocol.map(LABEL)
n_seeds = d.seed.nunique()

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 12,
    "axes.labelsize": 13, "axes.titlesize": 14, "figure.dpi": 300,
    "axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--",
    "axes.spines.top": False, "axes.spines.right": False,
})
fig, ax = plt.subplots(figsize=(8, 5))
# errorbar-free: boxplot quantiles are closed form, no bootstrap, no RNG.
sns.boxplot(data=d, x="Protocol", y="amortised", order=ORDER, ax=ax,
            palette="Set2", showfliers=True, fliersize=1.5, linewidth=1.0,
            whis=(1, 99), hue="Protocol", legend=False)
ax.set_yscale("log")
# Only 10^2 and 10^3 get labelled by default, and the whole CI cluster sits between
# them — label the decade subdivisions so the boxes can be read off the axis.
ax.set_yticks([80, 100, 150, 200, 300, 400, 600, 800, 1200], minor=False)
ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.set_xlabel("")
# Decision 38c: this is the DECOMPOSITION, not the paper's headline metric. The
# headline ratios come from the cumulative metric (total energy over committed count),
# which is a per-run scalar and has no per-decision distribution at all.
ax.set_ylabel("Per-decision energy, amortised\ndecomposition (node-slots)")
counts = " ".join(f"{k.split()[0]}{'-CI' if '(CI)' in k else '-CE'}={(d.Protocol == k).sum()}"
                  for k in ORDER)
ax.set_title(f"Per-decision energy decomposition, {n_seeds} seeds pooled\n"
             "(27 nodes, random, 5 % loss, 100 proposals; box = q25/q75,\n"
             "whiskers = p1/p99, points = outer 1 % each side)\n"
             f"n: {counts}", fontsize=9)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
plt.tight_layout()
for ext in ("pdf", "png"):
    plt.savefig(f"{OUT}/energy_boxplot_15seed.{ext}")
plt.close()

print(f"wrote {OUT}/energy_boxplot_15seed.pdf / .png")
print(f"n_decisions={len(d)} n_seeds={n_seeds}")
for k in ORDER:
    x = d[d.Protocol == k].amortised.to_numpy(float)
    q = np.percentile(x, [1, 25, 50, 75, 99])
    print(f"  {k:12s} n={len(x):5d} p01={q[0]:8.2f} q25={q[1]:8.2f} "
          f"med={q[2]:8.2f} q75={q[3]:8.2f} p99={q[4]:8.2f}")
