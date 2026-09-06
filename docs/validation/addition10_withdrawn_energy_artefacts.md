# Addition 10 -- the amortised-energy artefacts are withdrawn

`plots/energy/energy_per_proposal.csv` and `plots/energy/energy_summary.csv` are
removed from the working tree by this change. They stay recoverable from git
history forever:

    git show ad6788878aa8573f5b38551311c6e509bfdcdbf0:plots/energy/energy_per_proposal.csv
    git show ad6788878aa8573f5b38551311c6e509bfdcdbf0:plots/energy/energy_summary.csv

## Why

`energy_summary.csv` was published as a six-arm table with `n = 100`. That `n` is
100 *proposals of a single run*, not 15 seeds. Three independent lines of
evidence agree:

1. **It reproduces exactly from `energy_per_proposal.csv`.** All six arms match on
   mean, median and latency mean at the stored 2 dp, and that file holds
   600 rows = 6 arms x 100 proposals -- one run per arm, not fifteen.
2. **Its 2PC (CI) latency mean, 355.86, lies outside the entire fifteen-seed
   range** measured from the committed scalability sweep, `[116.61, 136.2041]`.
   The other five arms fall inside their ranges but match no published seed
   exactly. 355.86 is a pre-`629a0cd` number: that commit ("Fix 2PC-CI proposal
   start slot") moved 2PC-CI latency from 357.71 to 126.82.
3. **The repository already recorded it.** `docs/validation/phase0_tables.json`
   gives the source of the energy table as "single run seed=99, random topology;
   stderr = energy_std/sqrt(n=100) over proposals, NOT over seeds", and
   `docs/validation/phase0_report.md` labels both files "single seed". Seed 99 is
   not one of the fifteen published seeds and was retired by decision 27.

The bytes have not changed since phase 0. `energy_per_proposal.csv` at
`ad678887` is git blob `71e6a5cd7b8ad735f51331109f9c70d885cdc1d0`, 21652 bytes,
sha256 beginning `e979d4d0c4c1e194` -- exactly the size and fingerprint
`phase0_report.md` recorded for it on 2026-09-04.

## Re-running the scripts cannot fix this

There is no seed dimension to re-run over:

- `src/main.rs::export_pair` writes `results/results_<proto>.csv` and
  `results/snapshots_<proto>.csv` with **no seed and no topology in the
  filename**.
- `plots/energy/plot_stacked_bar.py` loops over
  `SEEDS = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47]`, so each seed's output
  overwrites the previous one. Only the last seed survives in `results/`.
- `plots/energy/plot_paper_energy.py` then reads whatever is in `results/`. It
  takes no seed argument and aggregates over proposals, never over seeds.

So the current code cannot produce a fifteen-seed amortised-energy table at all,
and a re-run today would silently publish a different single seed. Restoring
these artefacts needs a code change, not a re-run: seed-tagged output filenames,
and a seed loop in `plot_paper_energy.py` that aggregates across seeds.

Until that exists, no figure or table may be built from these two files. The
energy column of `tab:escape` is the reference instead -- it reproduces from the
committed sweep.

## Also in this change

### `plots/scalability/table_summary_N27_loss05.csv` -- one stale cell

Regenerated from the committed `plots/scalability/results/sweep_summary.csv`
(git blob `f1dcaea3fd999ef63dec91d4e655e7a6d20176e3`, 146414 bytes) with the
formulas in `plot_summary_commit.py`. Exactly one cell moves:

| row | column | was | now |
| --- | --- | --- | --- |
| 2PC (CI) | `latency_slots` | 357.7 | 126.8 |

The unrounded mean of `avg_latency` over the 15 seeds is 126.822000. The 71
other cells and the header reproduce byte-for-byte, which confirms both that the
file was written by `plot_summary_commit.py` and that only the `629a0cd` fix had
moved since. Old blob `85cb89c6dae69049e8f31eda081bf0369228eacc`, new blob
`b8fe0ec253c40c506bf415d4e48c94aa961a0c68`, size 554 either way.

The `.tex` twin of this table is gitignored and not committed, so nothing else
needed fixing.

### `plots/_common.py::require_per_slot_series` -- the guard had a hole

It accepted any series starting at slot 0 with step 1, and a one-row series
qualifies: the `len(s) > 1` ternary substitutes `step = [1]` when there is no
diff to take. `results/snapshots_2pc.csv`, `snapshots_paxos.csv` and
`snapshots_tom.csv` are each 78 bytes -- a header and one row -- so the three CI
arms passed a guard written specifically to catch them. The guard now rejects a
degenerate length-1 series unconditionally, and accepts an optional `end_slot`
so callers can require one row per simulated slot.

Follow-up, deliberately not done here: pass `end_slot` at both call sites, in
`plot_paper_energy.py` and `plot_stacked_bar.py`, from the run's results CSV.
The parameter is optional, so both call sites stay valid meanwhile.

## Unrelated defect noticed while reading

`plot_summary_commit.py` computes `n_seeds` correctly for the LaTeX comment, but
the titles of `commit_rate_vs_loss` and `commit_rate_vs_nodes` hardcode
"3 seeds (mean +- sd)". Both sweeps use 15 seeds. Two committed figures
therefore carry a wrong seed count in their titles. Not fixed here, to keep this
change reviewable.
