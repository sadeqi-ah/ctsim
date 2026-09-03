# Figure generation

Each script is **self-contained**: run it from anywhere and it will compile the
simulator (release mode), run the experiments it needs, and write its figures
**next to itself**. Nothing here is committed — every `.png`, `.pdf`, `.csv` and
`.tex` is reproduced from source and is git-ignored.

## Regenerate everything

```bash
python3 -m venv venv && source venv/bin/activate   # one-time
pip install -r requirements.txt

python3 tools/regen_figures.py
```

That runs all nine scripts in dependency order and writes `MANIFEST.sha256`
listing every artifact it produced. Useful flags:

| Flag | Effect |
|------|--------|
| `--only progress energy` | run just those experiment groups |
| `--force` | re-run the sweeps instead of reusing cached `results/sweep_summary.csv` |
| `--list` | print the plan and exit |
| `--no-run` | skip generation, just fingerprint what is on disk |
| `--compare DIR` | diff the current artifacts against a saved copy |

`--compare` hashes PNGs by **decoded pixels**, not file bytes, because
Matplotlib records its version in the PNG header — a byte comparison reports
differences that are not visible. CSV and `.tex` are compared byte-for-byte;
PDFs are skipped because they embed a creation timestamp.

## One script at a time

```bash
python3 plots/<experiment>/<script>.py
```

Two data mechanisms are used:

- **Sweeps** (`scalability`, `topology`) run `sweep_*.toml` via the simulator's
  built-in parallel sweep runner and write a `results/sweep_summary.csv` inside
  the experiment folder. They reuse that CSV if it exists; `--force` re-runs.
- **Single runs** (`progress`, `energy`, `duty_cycle`) invoke the simulator once
  per protocol and read the per-run CSVs from the repo-level `results/` folder.

Shared helpers live in [`_common.py`](_common.py).

## Scripts → outputs

| Script | Produces | Notes |
|--------|----------|-------|
| `scalability/plot_scalability.py` | throughput vs N, latency vs N, throughput vs loss | runs `sweep_scalability.toml` |
| `scalability/plot_efficiency.py` | energy efficiency vs N | reuses the scalability sweep CSV |
| `scalability/plot_summary_commit.py` | commit-rate figures, baseline summary table (`.csv`/`.tex`) | reuses the scalability sweep CSV |
| `topology/plot_topology.py` | throughput / latency / energy / efficiency vs topology, topology table (`.csv`/`.tex`) | runs `sweep_topology.toml` |
| `progress/plot_progress.py` | cumulative decisions over time (linear axis) | 6 single runs |
| `progress/plot_progress_log.py` | cumulative decisions over time (log axis) | 6 single runs |
| `energy/plot_stacked_bar.py` | per-proposal amortized-energy histogram | also produces the CSVs used below |
| `energy/plot_paper_energy.py` | amortized-energy box/mean/stacked, latency–energy trade-off, energy table | run **after** `plot_stacked_bar.py` |
| `duty_cycle/plot_kde_awake.py` | awake-node PMF and duty-cycle extremes | 6 single runs |

Tables are written as both `.csv` (for inspection) and `.tex` (a bare
`tabular` block, ready to `\input`). The scripts also print each table to
stdout, so a run doubles as a readable report.

## Dependency order

Only two orderings matter; `tools/regen_figures.py` already encodes them.

```bash
# sweeps (slowest first: scalability is 1800 cells and includes N=188)
python3 plots/scalability/plot_scalability.py      # writes the sweep CSV
python3 plots/scalability/plot_efficiency.py       # needs that CSV
python3 plots/scalability/plot_summary_commit.py   # needs that CSV
python3 plots/topology/plot_topology.py

# single runs
python3 plots/progress/plot_progress.py
python3 plots/progress/plot_progress_log.py
python3 plots/energy/plot_stacked_bar.py           # writes results/ CSVs
python3 plots/energy/plot_paper_energy.py          # needs those CSVs
python3 plots/duty_cycle/plot_kde_awake.py
```

## Reproducibility

The same command produces byte-identical output on the same machine. Two RNGs
have to be pinned for that to hold, and both already are:

- The simulator is seeded from the TOML (`seed`), and graph construction sorts
  every set before use — an unsorted `HashSet` would make the topology depend on
  per-process hash order.
- Seaborn's default `errorbar` is a bootstrap that draws from NumPy's global
  RNG, and `stripplot`'s jitter does too. Scripts using them pass `seed=0` /
  call `np.random.seed(0)`. `errorbar="sd"` is closed-form and needs neither.
