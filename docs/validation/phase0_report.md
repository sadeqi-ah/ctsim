# Phase-0 validation report (read-only)

Scope: re-derive, from the result files already on disk, every quantity the
manuscript prints for the baseline table and the topology section. No simulation
was run and no simulator code was touched. The only writes were this file,
`docs/validation/phase0_tables.json`, and the annotated tag `validation-baseline`.

Statistics convention used throughout: each CSV row is one seed × topology ×
protocol. `mean` is the arithmetic mean over the 15 seeds, `stderr` is
`std(ddof=1)/sqrt(15)`. Paired figures are computed per seed first
(`100*(scale_free − random)/random` for that seed), then averaged; the 95 %
interval is `paired_mean ± t(0.975, df=14) · paired_stderr` with
`t = 2.144787` (verified by numerical quadrature of the Student-t density:
2.144775; SciPy is not installed in the project venv). Every percentage is
printed with its sign. Percent-change of a mean (unpaired) and mean of
per-seed percent-changes (paired) are different estimators and are reported
side by side, never merged.

---

## Step 1 — Provenance

```
$ git rev-parse HEAD
6d2be8cecfe27ae1f10e3952a3c74b2ee2b68b4c

$ git status --porcelain
?? report.md
```

The working tree **is dirty**, in the narrow sense that one file is untracked:

| dirty file | state | relation to this report |
|---|---|---|
| `report.md` | untracked (`??`) | the earlier Persian-language throughput report; an output, not an input |

No tracked file is modified or staged: `git diff --stat HEAD` is empty. Every
result file read below is untracked-by-design — `.gitignore` excludes
`/results`, `plots/**/results/`, `plots/**/*.csv`, `plots/**/*.tex`,
`/MANIFEST.json`, `/MANIFEST.sha256` — so the data is not, and never was,
version-controlled at this commit. Confirmed with `git check-ignore -v`.

### Files read

Sizes in bytes, mtimes in local time (+0330), SHA-256 truncated to 16 hex chars.

| path | bytes | mtime | sha256[0:16] | role |
|---|---:|---|---|---|
| `plots/topology/results/sweep_summary.csv` | 38723 | 2026-09-04T00:26:20 | `19345bffce393d3b` | primary: 450 rows, 5 topologies |
| `plots/scalability/results/sweep_summary.csv` | 146534 | 2026-09-04T00:26:04 | `9c03fb89a2b631d8` | primary: 1800 rows, random only |
| `plots/topology/table_topology_N27_loss05.csv` | 2089 | 2026-09-04T01:44:09 | `180925c1979cd4c3` | derived from the topology sweep |
| `plots/topology/table_topology_N27_loss05.tex` | 2005 | 2026-09-04T01:44:09 | `e2b3ffc368e0a85d` | derived, same numbers |
| `plots/scalability/table_summary_N27_loss05.csv` | 554 | 2026-09-04T01:44:05 | `48e903d8cd99cfbf` | derived: the baseline table |
| `plots/scalability/table_summary_N27_loss05.tex` | 615 | 2026-09-04T01:44:05 | `e6475a8e3e2008c2` | derived, same numbers |
| `plots/energy/energy_summary.csv` | 424 | 2026-09-04T01:44:31 | `1aa6b29e825f02bf` | amortized energy, single seed |
| `plots/energy/energy_per_proposal.csv` | 21652 | 2026-09-04T01:44:31 | `e979d4d0c4c1e194` | 600 per-proposal rows, single seed |
| `results/results_tom.csv` | 2290 | 2026-09-04T01:44:34 | `65779278c0e9f841` | per-proposal, seed 99 |
| `results/results_paxos.csv` | 2404 | 2026-09-04T01:44:34 | `deb52d5b35914e35` | per-proposal, seed 99 |
| `results/results_2pc.csv` | 2338 | 2026-09-04T01:44:34 | `0a443ebecf721beb` | per-proposal, seed 99 |
| `results/results_tom_ce.csv` | 2291 | 2026-09-04T01:44:35 | `bd6e95aea7f58972` | per-proposal, seed 99 |
| `results/results_paxos_ce.csv` | 2477 | 2026-09-04T01:44:34 | `6f69aaa72bdb5370` | per-proposal, seed 99 |
| `results/results_2pc_ce.csv` | 2545 | 2026-09-04T01:44:35 | `69a8f9d9dde40210` | per-proposal, seed 99 |
| `results/snapshots_*.csv` (6 files) | 6374–36215 | 2026-09-04T01:44:34–35 | see `MANIFEST.json` | per-slot radio state, seed 99 |
| `MANIFEST.json` | 7277 | 2026-09-04T01:44:37 | `fc737a62d4b7444f` | fingerprints written by `tools/regen_figures.py` |
| `MANIFEST.sha256` | 3994 | 2026-09-04T01:44:37 | `e3edc2b748122f3a` | same, flat format |

Also read, as definition sources rather than data: `plots/topology/plot_topology.py`,
`plots/scalability/plot_summary_commit.py`, `plots/energy/plot_paper_energy.py`,
`sweep_topology.toml`, `sweep_scalability.toml`, `src/phy/ci.rs`, `src/node.rs`,
`src/metrics.rs`, `src/sweep_runner.rs`, `src/network.rs`, `src/run.rs`.

Integrity: every data SHA-256 on disk equals the value recorded in
`MANIFEST.json`, so the CSVs have not been touched since the figure driver last
fingerprinted them at 01:44:37.

### Attribution and the tag

The two sweep CSVs were written at 00:26, before either commit's timestamp
(`cdc81cf` committed 01:11:09, `6d2be8c` at 01:46:59), so mtime alone cannot
attribute them. Content-based attribution:

- `src/`, `Cargo.lock`, `sweep_topology.toml` and `sweep_scalability.toml` are
  **byte-identical** between `cdc81cf`, `6d2be8c` and the working tree
  (`git diff` over those paths is empty). Any of them produces the same sweep.
- The binary that ran the sweep is `target/release/ctsim`, mtime
  2026-09-04T00:17:22 — after the last `src/` edit (`src/network.rs`, 00:16:37)
  and before the sweep output at 00:26. The source tree at build time therefore
  already matched HEAD.
- The derived tables (01:44) carry the header `% N=27, loss=5%, 100 proposals,
  15 seeds (mean)`. The dynamic seed count exists **only** at `6d2be8c`;
  `cdc81cf` and every earlier commit hardcode `3 seeds`. So the table files can
  only have been produced by HEAD.
- One caveat, stated rather than smoothed over: at 00:26 `Cargo.toml` still had
  its `repository = …` line commented out (that line was added in `cdc81cf`).
  That field is package metadata and cannot influence simulator output, but it
  means the sweep ran against a tree that differed from `cdc81cf` in exactly one
  comment line of `Cargo.toml`.

Given that, the results attribute to a single commit — HEAD — and the tag was
created:

```
$ git tag -a validation-baseline 6d2be8c -m "…"
$ git rev-parse validation-baseline^{commit}
6d2be8cecfe27ae1f10e3952a3c74b2ee2b68b4c
```

It is the only tag in the repository. The message records the file list, the
attribution argument and the `Cargo.toml` caveat.

---

## Step 2 — Completeness of the source search

Three searches were run. The first is the one the earlier report implicitly
relied on, and it is **wrong for this purpose**: `rg` honours `.gitignore`, and
`.gitignore` excludes every result directory, so a default `rg` cannot see the
data files at all.

```
$ rg -l --hidden -g '!.git' -i 'scale.?free' .
./report.md
./sweep_topology.toml
./README.md
./src/network.rs
./src/run.rs
./examples/paxos_ci.toml
./docs/simulator.md
./plots/topology/plot_topology.py
```

Not one data file appears — the search silently skipped `plots/*/results/`.
Repeating it with `--no-ignore` (excluding `venv/`, `target/`, `.git/`):

```
$ rg -l --no-ignore --hidden -g '!.git' -g '!venv' -g '!target' -g '!__pycache__' \
     -i 'scale.?free' .
./src/network.rs                                     (code: BA generator)
./src/main.rs                                        (code: topology dispatch)
./src/run.rs                                         (code: topology dispatch)
./sweep_topology.toml                                (config: topology list)
./report.md                                          (prose: earlier report)
./examples/paxos_ci.toml                             (config: example)
./docs/simulator.md                                  (prose: docs)
./README.md                                          (prose: docs)
./plots/topology/plot_topology.py                    (code: label map)
./plots/topology/table_topology_N27_loss05.tex       ← DATA
./plots/topology/table_topology_N27_loss05.csv       ← DATA
./plots/topology/results/sweep_summary.csv           ← DATA
```

A third pass with `--binary` adds only `plots/topology/__pycache__/plot_topology.cpython-313.pyc`
(a compiled copy of the label map, not data). The file inventory:

```
$ find . -path ./.git -prune -o -path ./venv -prune -o -path ./target -prune -o \
       \( -name 'sweep_summary*' -o -name '*.csv' -o -name '*.json' -o -name '*.tex' \) -print
./MANIFEST.json
./plots/energy/energy_per_proposal.csv
./plots/energy/energy_summary.csv
./plots/scalability/results/sweep_summary.csv
./plots/scalability/table_summary_N27_loss05.csv|.tex
./plots/topology/results/sweep_summary.csv
./plots/topology/table_topology_N27_loss05.csv|.tex
./results/results_{tom,paxos,2pc}{,_ce}.csv
./results/snapshots_{tom,paxos,2pc}{,_ce}.csv
```

### Answer: no, `plots/topology/results/sweep_summary.csv` is not the only file with scale-free rows

**Three** files carry scale-free rows. The earlier report's claim is false as
stated, though the two extra files are derived from the first, not independent
measurements:

| file | scale-free content |
|---|---|
| `plots/topology/results/sweep_summary.csv` | 90 raw rows (15 seeds × 6 protocols) |
| `plots/topology/table_topology_N27_loss05.csv` | 6 aggregated rows |
| `plots/topology/table_topology_N27_loss05.tex` | the same 6 rows, LaTeX-formatted |

Cell-by-cell comparison, all 30 topology × protocol rows × 9 columns = 270
cells of the derived CSV against a re-aggregation of the raw sweep, applying the
rounding the script itself applies (`plot_topology.py:154-166`):

```
cells compared: 270    mismatches: 0
max |round(recomputed) - printed| over all cells: 0
```

`.tex` versus `.csv`: 30 rows, 0 mismatches, 6 scale-free rows present in both.
So the three files agree exactly and there is nothing to prefer between them.

### A fourth file overlaps on the random topology

`plots/scalability/results/sweep_summary.csv` has no scale-free rows (topology
column is `random` only, 1800 rows over N ∈ {6,13,27,54,188} × loss ∈
{0,0.05,0.1,0.2}), but its N=27 / loss=0.05 slice covers the same 90 raw rows as
the topology sweep's `random` block. That overlap is a genuine cross-check and it
is exact:

```
rows compared: 90   columns compared: 13
(diameter, edges, committed, aborted, timed_out, avg_latency, listen, flood,
 sleep, nacks, piggybacks, ce_timeouts, end_slot)
result: identical in every compared cell
```

Two independently launched sweeps reproduce each other bit-for-bit at the raw
level, per seed. That is the strongest available evidence that the numbers below
are not artefacts of one run.

---

## Step 3 — Energy and efficiency on the random → scale-free transition

### Which column was read

Neither energy nor efficiency is stored. Both are derived, with the same
definitions the figure scripts use:

| quantity | definition | file:line |
|---|---|---|
| per-decision energy | `(listen + flood) / committed` | `plots/topology/plot_topology.py:95`; identically `plots/scalability/plot_summary_commit.py:64` |
| efficiency | `throughput / energy_per_dec * 1000` | `plots/topology/plot_topology.py:96`; identically `plots/scalability/plot_summary_commit.py:65` |
| throughput (input to the above) | `committed / end_slot` | `plots/topology/plot_topology.py:94` |
| cumulative energy | `listen + flood` | derived here from the stored columns |

`listen`, `flood`, `sleep` are stored per row and are network-wide node-slot
totals: `src/sweep_runner.rs:130-132` writes `s.total_listen` etc., which
`src/metrics.rs:112-114` sums over all nodes from the per-node counters
incremented one-per-slot in `src/node.rs:68-74`. So the natural unit is
node-slots, and `energy_per_dec` is node-slots per committed decision. The
factor 1000 in efficiency is a display scale only.

Every value below is recoverable; nothing is estimated.

### Per-decision energy, node-slots per committed decision

Sign convention: positive % = scale-free consumes **more** energy per decision.

| combo | random (mean ± SE) | scale-free (mean ± SE) | Δ unpaired | Δ paired ± SE | 95 % CI |
|---|---|---|---|---|---|
| TOM (CI) | 87.9913 ± 0.6946 | 88.8060 ± 0.3652 | **+0.93 %** | +1.03 ± 1.02 | [−1.15, +3.21] |
| Paxos (CI) | 100.2153 ± 1.2678 | 106.4533 ± 0.8658 | **+6.22 %** | +6.44 ± 1.52 | [+3.19, +9.69] |
| 2PC (CI) | 115.8438 ± 2.3545 | 121.6841 ± 2.3342 | **+5.04 %** | +5.60 ± 2.84 | [−0.49, +11.70] |
| TOM (CE) | 126.2520 ± 1.5470 | 124.5780 ± 1.2288 | **−1.33 %** | −1.07 ± 1.79 | [−4.91, +2.77] |
| Paxos (CE) | 383.5980 ± 2.4440 | 429.2820 ± 2.5873 | **+11.91 %** | +11.97 ± 0.98 | [+9.87, +14.07] |
| 2PC (CE) | 657.0540 ± 7.2210 | 899.4960 ± 18.6590 | **+36.90 %** | +37.15 ± 3.28 | [+30.12, +44.19] |

Every combination except TOM (CE) gets **worse** (more energy) on scale-free.
Only Paxos (CE), 2PC (CE) and Paxos (CI) have intervals excluding zero.

### Efficiency (throughput per unit energy × 1000)

Sign convention: positive % = scale-free is **more** efficient.

| combo | random (mean ± SE) | scale-free (mean ± SE) | Δ unpaired | Δ paired ± SE | 95 % CI |
|---|---|---|---|---|---|
| TOM (CI) | 2.428646 ± 0.048146 | 2.475920 ± 0.033353 | **+1.95 %** | +2.67 ± 2.89 | [−3.52, +8.87] |
| Paxos (CI) | 1.906237 ± 0.042766 | 1.841368 ± 0.025962 | **−3.40 %** | −2.57 ± 2.92 | [−8.83, +3.68] |
| 2PC (CI) | 1.462919 ± 0.046952 | 1.391270 ± 0.036346 | **−4.90 %** | −3.32 ± 4.30 | [−12.55, +5.91] |
| TOM (CE) | 1.704537 ± 0.041414 | 1.746907 ± 0.034810 | **+2.49 %** | +3.54 ± 3.64 | [−4.25, +11.34] |
| Paxos (CE) | 0.183803 ± 0.002347 | 0.146736 ± 0.001754 | **−20.17 %** | −19.99 ± 1.36 | [−22.91, −17.07] |
| 2PC (CE) | 0.062858 ± 0.001379 | 0.033937 ± 0.001297 | **−46.01 %** | −45.60 ± 2.49 | [−50.93, −40.26] |

Efficiency compounds the throughput and energy moves, so the CE penalty is
roughly twice the throughput penalty: 2PC (CE) loses **−46.0 %** of its
efficiency, Paxos (CE) **−20.2 %**. The four CI/TOM rows sit within noise
(intervals straddle zero).

### Cumulative energy, for completeness

`listen + flood` in node-slots, no division by `committed`. Note this makes 2PC
(CI) move differently from its per-decision figure, because its commit rate also
drops (98.93 % → 97.27 %):

| combo | random | scale-free | Δ unpaired | Δ paired ± SE | 95 % CI |
|---|---|---|---|---|---|
| TOM (CI) | 8799.1 ± 69.5 | 8880.6 ± 36.5 | **+0.93 %** | +1.03 ± 1.02 | [−1.15, +3.21] |
| Paxos (CI) | 10021.5 ± 126.8 | 10645.3 ± 86.6 | **+6.22 %** | +6.44 ± 1.52 | [+3.19, +9.69] |
| 2PC (CI) | 11448.9 ± 191.3 | 11828.0 ± 199.9 | **+3.31 %** | +3.69 ± 2.39 | [−1.43, +8.81] |
| TOM (CE) | 12625.2 ± 154.7 | 12457.8 ± 122.9 | **−1.33 %** | −1.07 ± 1.79 | [−4.91, +2.77] |
| Paxos (CE) | 38359.8 ± 244.4 | 42928.2 ± 258.7 | **+11.91 %** | +11.97 ± 0.98 | [+9.87, +14.07] |
| 2PC (CE) | 65705.4 ± 722.1 | 89949.6 ± 1865.9 | **+36.90 %** | +37.15 ± 3.28 | [+30.12, +44.19] |

### Not recoverable

The amortized per-decision energy of `plots/energy/energy_summary.csv` (the
`E_i = Σ_t A_t/C_t` definition at `plots/energy/plot_paper_energy.py:5-7`) is
**not recoverable for scale-free**: that file holds a single run on the random
topology at seed 99 (`results/sim_*_per_prop.toml`), with no scale-free rows and
no seed dimension. Its random-topology values are recorded in the JSON for
reference; no scale-free counterpart is estimated.

### Mechanism, from the same file

The move is entirely a time-stretch, not a correctness failure. Per-seed means,
random → scale-free:

| combo | `ce_timeouts` | `end_slot` | `committed` |
|---|---|---|---|
| TOM (CI) | 0.00 → 0.00 | 469.9 → 455.7 | 100.00 → 100.00 |
| Paxos (CI) | 0.00 → 0.00 | 526.5 → 511.5 | 100.00 → 100.00 |
| 2PC (CI) | 0.00 → 0.00 | 590.3 → 579.1 | 98.93 → 97.27 |
| TOM (CE) | 0.07 → 0.47 | 467.6 → 461.4 | 100.00 → 100.00 |
| Paxos (CE) | 5.40 → 30.00 | 1420.7 → 1589.9 | 100.00 → 100.00 |
| 2PC (CE) | 336.67 → 2049.47 | 2433.5 → 3331.5 | 100.00 → 100.00 |

CE listen-timeouts rise 6× for 2PC and 5.6× for Paxos; CI never times out (the
column is 0 in all 90 CI rows). CI recovery traffic rises instead: `nacks`
0.53 → 2.67 and `piggybacks` 0.47 → 2.53 for TOM (CI), 12.0 → 38.3 for
Paxos (CI), 24.1 → 81.1 for 2PC (CI) — which is where Paxos (CI)'s +6.2 % energy
comes from even though its throughput improved.

---

## Step 4 — Paired uncertainty

The design is paired: `sweep_topology.toml:5` fixes
`seeds = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]`, and all 30
(topology, protocol) groups have exactly 15 unique seeds — verified, min = max =
15 over all 30 groups, 450 rows total with no gaps. So per-seed differencing is
legitimate.

The unpaired figures are repeated here beside the paired ones, not replaced.
`Δ unpaired` = `100·(mean_sf − mean_rand)/mean_rand`. `Δ paired` = mean over
seeds of `100·(sf_i − rand_i)/rand_i`. "n↓" counts seeds where scale-free is
numerically lower than random (whatever "lower" means for that metric).

### Throughput — `committed/end_slot`

Positive = scale-free is faster.

| combo | Δ unpaired | Δ paired ± SE | 95 % CI | n↓ |
|---|---|---|---|---|
| TOM (CI) | +3.0382 % | +3.3277 ± 1.9146 | [−0.779, +7.434] | 4/15 |
| Paxos (CI) | +2.8676 % | +3.1571 ± 1.9345 | [−0.992, +7.306] | 4/15 |
| 2PC (CI) | +0.0772 % | +0.5122 ± 2.1845 | [−4.173, +5.197] | 7/15 |
| TOM (CE) | +1.2706 % | +1.5330 ± 1.8004 | [−2.329, +5.395] | 7/15 |
| Paxos (CE) | −10.6476 % | −10.5980 ± 0.7682 | [−12.246, −8.950] | 15/15 |
| 2PC (CE) | −26.6584 % | −26.5195 ± 1.7073 | [−30.181, −22.858] | 15/15 |

This reproduces the accepted result (+3.0, +2.9, +0.1, +1.3, −10.7, −26.7) to
within rounding, and the pairing sharpens the reading considerably: the four
near-zero rows have intervals spanning zero and split their seeds roughly evenly
(4–7 of 15 go the "wrong" way), so their sign is **not** established by this
data. The two CE regressions are unanimous — 15 of 15 seeds worse — so those are
systematic, not sampling noise.

### Latency — `avg_latency`

Positive = scale-free is slower.

| combo | Δ unpaired | Δ paired ± SE | 95 % CI | n↓ |
|---|---|---|---|---|
| TOM (CI) | −2.7947 % | −2.5335 ± 1.7929 | [−6.379, +1.312] | 10/15 |
| Paxos (CI) | −2.8895 % | −2.5952 ± 1.9524 | [−6.783, +1.592] | 9/15 |
| 2PC (CI) | −2.1474 % | −1.8252 ± 1.9505 | [−6.009, +2.358] | 9/15 |
| TOM (CE) | −1.3259 % | −1.0666 ± 1.7901 | [−4.906, +2.773] | 8/15 |
| Paxos (CE) | +11.9093 % | +11.9721 ± 0.9793 | [+9.872, +14.073] | 0/15 |
| 2PC (CE) | +36.8983 % | +37.1540 ± 3.2793 | [+30.121, +44.187] | 0/15 |

Same structure: CI rows indistinguishable from zero, CE rows unanimous in the
adverse direction (0 of 15 seeds improved).

### Energy — `(listen+flood)/committed`

Positive = scale-free uses more energy per decision.

| combo | Δ unpaired | Δ paired ± SE | 95 % CI | n↓ |
|---|---|---|---|---|
| TOM (CI) | +0.9258 % | +1.0295 ± 1.0185 | [−1.155, +3.214] | 8/15 |
| Paxos (CI) | +6.2246 % | +6.4399 ± 1.5164 | [+3.188, +9.692] | 2/15 |
| 2PC (CI) | +5.0415 % | +5.6042 ± 2.8429 | [−0.493, +11.702] | 5/15 |
| TOM (CE) | −1.3259 % | −1.0666 ± 1.7901 | [−4.906, +2.773] | 8/15 |
| Paxos (CE) | +11.9093 % | +11.9721 ± 0.9793 | [+9.872, +14.073] | 0/15 |
| 2PC (CE) | +36.8983 % | +37.1540 ± 3.2793 | [+30.121, +44.187] | 0/15 |

Paxos (CI) is the one CI row whose energy penalty is real (13 of 15 seeds worse,
interval clear of zero) even though its throughput improved — the recovery
traffic noted in Step 3.

Two structural notes visible in the numbers. First, the CE energy and CE latency
columns are **identical percentages** (e.g. both +37.1540 ± 3.2793 for 2PC (CE)).
That is not a copy error: for CE, energy per decision equals 27 × latency
exactly (Step 6d), so their relative changes must coincide. Second, TOM (CE)
shows the same identity, which is why its energy row repeats its latency row.

---

## Step 5 — Full reproduction of the baseline table

Configuration: random topology, N = 27, loss 0.05, 100 proposals, 15 seeds. Read
from `plots/scalability/results/sweep_summary.csv` (its N=27/loss=0.05 slice, 90
rows). The topology sweep's `random` block gives byte-identical values (Step 2),
so both sources agree and neither is preferred.

### Reproduced cells (mean over 15 seeds, ± standard error)

| combo | commit % | throughput | latency | E/dec | efficiency | cumulative E | flood | sleep | listen | end_slot |
|---|---|---|---|---|---|---|---|---|---|---|
| TOM (CI) | 100.0000 | 0.213240 | 4.6993 | 87.9913 | 2.428646 | 8799.1 | 2701.27 | 3899.87 | 6097.87 | 469.93 |
| Paxos (CI) | 100.0000 | 0.190329 | 61.3940 | 100.2153 | 1.906237 | 10021.5 | 3075.40 | 4434.27 | 6946.13 | 526.47 |
| 2PC (CI) | 98.9333 | 0.168067 | 357.7100 | 115.8438 | 1.462919 | 11448.9 | 3513.93 | 5033.73 | 7934.93 | 590.33 |
| TOM (CE) | 100.0000 | 0.214306 | 4.6760 | 126.2520 | 1.704537 | 12625.2 | 3845.67 | 0.00 | 8779.53 | 467.60 |
| Paxos (CE) | 100.0000 | 0.070426 | 14.2073 | 383.5980 | 0.183803 | 38359.8 | 15362.33 | 0.00 | 22997.47 | 1420.73 |
| 2PC (CE) | 100.0000 | 0.041162 | 24.3353 | 657.0540 | 0.062858 | 65705.4 | 26087.93 | 0.00 | 39617.47 | 2433.53 |

Standard errors for these are in the JSON (`metric: "baseline:*"`).

### The "count of CI transmissions" column cannot be mapped to `flood`

The manuscript's sixth column prints 3900 / 4434 / 5034 for the three CI rows and
0 for the three CE rows. Nine candidate fields were scanned against those six
printed values:

| candidate field | TOM(CI) | Paxos(CI) | 2PC(CI) | TOM(CE) | Paxos(CE) | 2PC(CE) | worst rel. error |
|---|---|---|---|---|---|---|---|
| **`sleep`** | **3899.87** | **4434.27** | **5033.73** | **0.00** | **0.00** | **0.00** | **0.006 %** |
| `flood` | 2701.27 | 3075.40 | 3513.93 | 3845.67 | 15362.33 | 26087.93 | unmappable (CE ≠ 0) |
| `listen` | 6097.87 | 6946.13 | 7934.93 | 8779.53 | 22997.47 | 39617.47 | unmappable |
| `listen+flood` | 8799.13 | 10021.53 | 11448.87 | 12625.20 | 38359.80 | 65705.40 | unmappable |
| `flood/committed` | 27.01 | 30.75 | 35.55 | 38.46 | 153.62 | 260.88 | unmappable |
| `nacks` | 0.53 | 0.47 | 2.00 | 0.00 | 0.00 | 0.00 | ~100 % |
| `piggybacks` | 0.47 | 12.00 | 24.07 | 0.00 | 0.00 | 0.00 | ~100 % |
| `ce_timeouts` | 0.00 | 0.00 | 0.00 | 0.07 | 5.40 | 336.67 | unmappable |
| `end_slot` | 469.93 | 526.47 | 590.33 | 467.60 | 1420.73 | 2433.53 | unmappable |

The printed column is the **`sleep`** column of
`plots/scalability/table_summary_N27_loss05.csv` — total node-slots spent with
the radio off — to within 0.006 %. It is not a transmission count. Naming it "CI
transmissions" is a mislabel: `flood` is the field that counts transmit slots,
and `flood` is 2701 / 3075 / 3514 for the CI rows, i.e. **−30.7 % / −30.6 % /
−30.2 %** away from the printed numbers, and non-zero (3846 / 15362 / 26088) for
the CE rows where the manuscript prints 0.

The CE zeros are consistent with `sleep` and only with `sleep`: CE nodes never
sleep (`src/phy/ce.rs` keeps the radio on for the whole round), so `sleep = 0`
exactly in all 45 CE rows — while CE `flood` is large. Both mappings are recorded
in the JSON (`manuscript_rel_error:ci_transmissions_as_sleep` and
`…_as_flood`); the report takes no side beyond what the numbers show, but the
column as printed cannot be a transmission count.

### Relative error per cell, manuscript vs data

`rel.err = 100·(data − printed)/printed`. Signs are as computed.

| combo | commit % | throughput | latency | E/dec | efficiency | col-6 as `sleep` | col-6 as `flood` |
|---|---|---|---|---|---|---|---|
| TOM (CI) | +0.0000 % | +0.0187 % | −0.0142 % | −0.0098 % | −0.0557 % | −0.0034 % | −30.7368 % |
| Paxos (CI) | +0.0000 % | +0.0152 % | −0.0098 % | +0.0153 % | −0.1970 % | +0.0060 % | −30.6405 % |
| 2PC (CI) | +0.0337 % | −0.0199 % | +0.0028 % | +0.0378 % | +0.1999 % | −0.0053 % | −30.1960 % |
| TOM (CE) | +0.0000 % | +0.0027 % | −0.5106 % | −0.0380 % | +0.2669 % | printed 0, data 0 | printed 0, data 3845.67 |
| Paxos (CE) | +0.0000 % | +0.0373 % | +0.0516 % | −0.0005 % | **+2.1129 %** | printed 0, data 0 | printed 0, data 15362.33 |
| 2PC (CE) | +0.0000 % | −0.0924 % | +0.1454 % | −0.0070 % | **+4.7631 %** | printed 0, data 0 | printed 0, data 26087.93 |

Reading of the four columns that were the real work:

- **Commit rate**: exact for five rows; 2PC (CI) prints 98.9 against 98.9333
  (+0.0337 %), a rounding artefact.
- **Cumulative energy**: the printed energy column is **per-decision**, not
  cumulative. Taken as cumulative (`listen+flood`) the errors are +9899 % to
  +9902 % — four orders of magnitude — so that reading is wrong. Taken as
  `(listen+flood)/committed` every cell lands within ±0.04 %. The manuscript
  column is per-decision energy; the genuinely cumulative values are in the table
  above (8799 … 65705 node-slots) and are recorded separately in the JSON.
- **Efficiency**: the three CI rows and TOM (CE) are within ±0.27 %, but the two
  small-valued CE rows are visibly off: **Paxos (CE) +2.11 %** (printed 0.18,
  data 0.183803) and **2PC (CE) +4.76 %** (printed 0.06, data 0.062858). Both are
  pure two-decimal truncation of a number near 0.06–0.18, where two decimals
  cannot carry the value; they are not independent errors. Neither figure was
  rounded here toward the printed one — the primary numbers are 0.183803 and
  0.062858.
- **CI transmissions**: as above, not mappable to a transmission count. Best
  mapping is `sleep` at ≤0.006 %; the transmit-slot column `flood` is off by
  −30 % and contradicts the CE zeros.

A further check: all five labelled columns of the manuscript row are **bit-equal**
to the corresponding cells of `plots/scalability/table_summary_N27_loss05.csv`.
The manuscript table was transcribed from that file, so the sub-0.1 % errors above
are exactly the file's own rounding (`plot_summary_commit.py:92-105`), not
transcription mistakes — with the two CE efficiency cells the visible cost of
rounding to two decimals.

<!--NEXT-->




