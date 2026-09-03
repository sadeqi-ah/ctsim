# Figure generation

Each script is **self-contained**: run it from anywhere and it will compile the
simulator (release mode), run the experiments it needs, and write its figures
**next to itself**. Nothing here is committed — every `.png`/`.pdf`/`.csv` and
every generated `CAPTIONS*.md` is reproduced from source and is git-ignored.

```bash
python3 -m venv venv && source venv/bin/activate   # one-time
pip install -r requirements.txt
python3 plots/<experiment>/<script>.py
```

Two data mechanisms are used:

- **Sweeps** (`scalability`, `topology`) run `sweep_*.toml` via the simulator's
  built-in parallel sweep runner and write a `results/sweep_summary.csv` inside
  the experiment folder.
- **Single runs** (`progress`, `energy`, `duty_cycle`) invoke the simulator once
  per protocol and read the per-run CSVs from the repo-level `results/` folder.

Shared helpers live in [`_common.py`](_common.py).

## Scripts → figures

| Script | Produces | Notes |
|--------|----------|-------|
| `scalability/plot_scalability.py` | throughput vs N, latency vs N, throughput vs loss | runs `sweep_scalability.toml` |
| `scalability/plot_efficiency.py` | energy efficiency vs N | reuses the scalability sweep CSV |
| `scalability/plot_summary_commit.py` | commit-rate figures + reference summary table | reuses the scalability sweep CSV |
| `topology/plot_topology.py` | throughput / latency / energy / efficiency vs topology | runs `sweep_topology.toml` |
| `progress/plot_progress.py` | cumulative decisions over time (linear axis) | 6 single runs |
| `progress/plot_progress_log.py` | cumulative decisions over time (log axis) | 6 single runs |
| `energy/plot_stacked_bar.py` | per-proposal amortized-energy histogram | also produces the CSVs used below |
| `energy/plot_paper_energy.py` | amortized-energy box/mean/stacked + latency–energy trade-off + table | run **after** `plot_stacked_bar.py` |
| `duty_cycle/plot_kde_awake.py` | awake-node PMF and duty-cycle extremes | 6 single runs |

## Order of execution

Only two dependencies exist; everything else is independent.

```bash
# sweeps (slowest first: scalability includes N=188)
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

Sweep scripts cache `results/sweep_summary.csv` and skip the sweep if it is
already present; pass `--force` to re-run it. The `scalability` sweep is
1800 cells (it includes N=188) and takes several minutes; `topology` is smaller.

Scripts that print a method blurb and per-figure caption text alongside their
output write it to a `CAPTIONS*.md` file next to the figures. Those files are
generated, not authored — they are regenerated with the numbers of the run that
produced them, so they always match the figures beside them.
