# Decision 19 — snapshot emission fixed

Read `addition6_energy_paths.md` first; this closes it.

Commands:

```
cargo build --release && cargo clippy --release --all-targets   # clean
for t in tom_pipeline paxos_pipeline 2pc_pipeline tom_ce paxos_ce 2pc_ce; do
    ./target/release/ctsim results/sim_${t}_per_prop.toml; done
./venv/bin/python /tmp/ctsim_validate/decision19_accept.py    # acceptance test
./venv/bin/python /tmp/ctsim_validate/decision19b_amortised.py
./target/release/ctsim sweep_topology.toml && ./target/release/ctsim sweep_scalability.toml
./venv/bin/python /tmp/ctsim_validate/gate19.py               # regression gate
cargo test --release                                          # 17 tests
```

## The three defects

| site | what it emitted | consequence |
|---|---|---|
| `phy/ci.rs:112-121` | the round-boundary slot, with the pre-`reset_round()` all-Sleep state | **displaced** the state of a row the next round also emitted, for 93 of 95 rounds; only the final round's emission was an extra row |
| `sim/pipeline.rs:161` | a trailing row for `current_slot`, the first *free* slot | one never-ticked row per CI run |
| `sim.rs:131-137` | a per-proposal catch-up loop **plus** a trailing row, both for the first free slot | one never-ticked row per CE run, emitted twice: 457 rows for 456 distinct slots |

All three are the same mistake: emitting a slot no node has been ticked for. The
next round starts at that index, calls `reset_round()`, and ticks it — so it was
already going to be emitted, by the round that actually charged it.

The fix deletes all three emissions. Every ticked slot is now emitted exactly
once, by the loop that ticked it. No RNG is drawn, no control flow changes; only
`metrics.snapshots` shrinks.

### The collision semantic the fix depends on

Row counts fell by exactly 2 per arm, not by 96, and that is the load-bearing
detail. The `ci.rs` defect did not usually *add* a row; it *suppressed the
correct one*.

The mechanism is **first-write-wins, enforced by a monotone cursor, not by the
store.** `metrics.rs:69` is an unconditional `self.snapshots.push(s)` — a `Vec`,
append-only, no key, no de-duplication, no overwrite. What prevents a second row
for the same slot is the shared cursor `next_snapshot`, threaded by `&mut` through
`sim.rs:73/108` and `sim/pipeline.rs:24/39/87` into `phy/ci.rs:38` and
`phy/ce.rs:31`. Every emission is gated by `while *next_snapshot <= slot { …;
*next_snapshot += snapshot_interval; }` (`ci.rs:66-69`, `ce.rs:50-53`). Once the
premature write advanced the cursor past slot `k`, the next round's loop — which
reaches slot `k` with the correct post-reset state — found `next_snapshot > k` and
emitted nothing. The earlier write won by moving the cursor, and the later,
correct one was silently skipped.

Two consequences worth stating plainly:

1. **The fix is only correct because of that semantic.** Deleting the premature
   emission works precisely because the correct emission was being suppressed
   rather than overwritten — remove the premature write and the round that ticks
   slot `k` finds the cursor still at `k` and emits it, with the right state. Had
   the store been last-write-wins, the correct row would already have been in the
   series and deleting the early write would have left a hole.
2. **Any future emission added anywhere reintroduces this bug.** The store cannot
   refuse a duplicate, and the cursor cannot distinguish a premature write from a
   timely one. The new test catches a row-count change, but a *displacement* that
   preserves the row count — exactly what happened for 93 of the 95 rounds here —
   is caught only by the node-slot equality assertions, not by the count. That is
   why the test asserts `awake_ticks == awake_snaps` and `sleep` equality, and not
   just contiguity.


## Acceptance test — all six ratios 1.0000

| arm | tick `L+F` | snapshot `Σ(listening+flooding)` | ratio | rows | dup | contiguous | `rows·N == L+F+S` |
|---|---|---|---|---|---|---|---|
| tom_pipeline | 8607 | 8607 | **1.0000** | 455 | 0 | yes | yes |
| paxos_pipeline | 9753 | 9753 | **1.0000** | 516 | 0 | yes | yes |
| 2pc_pipeline | 10985 | 10985 | **1.0000** | 588 | 0 | yes | yes |
| tom_ce | 12609 | 12609 | **1.0000** | 467 | 0 | yes | yes |
| paxos_ce | 37368 | 37368 | **1.0000** | 1384 | 0 | yes | yes |
| 2pc_ce | 64044 | 64044 | **1.0000** | 2372 | 0 | yes | yes |

Sleep matches too, in all six. The CE side that was 0.9957–0.9992 is now exact.

**Interval scope (decision 23).** All six runs above use `snapshot_interval = 1`,
and the invariant `rows · N == L+F+S` is defined at that interval only. At any
larger interval the series is a deliberate sample: a 455-slot run emits 23 rows at
interval 20, so `rows · N` is 621 against 12285 node-slots charged, and the
invariant fails by construction rather than because of a bug. The published sweeps
use 20 and `config.rs:73` defaults to 50, so a config that never intended to feed
the amortised path can reach it. Measured, not assumed: the same TOM-CI run at
`snapshot_interval = 20` emits 23 rows spanning slots 0..440 while `tick()` still
charges `Listen=5907 Flood=2700 Sleep=3678` — identical to the interval-1 run, which
is the point: the counters are interval-invariant and the series is not.

Closed at the reading end rather than by rescaling: `plots/_common.py::require_per_slot_series`
raises unless the series starts at slot 0 with step 1 throughout, and both consumers
call it — `plot_paper_energy.py:90-92` and `plot_stacked_bar.py:78-79`. Verified: the
real interval-1 series (455 rows) is accepted; the same series decimated to interval
20 and to interval 50 is refused, as is a series starting at slot 3. A rescaled
integral would be a plausible-looking number with no physical meaning, which is the
whole failure mode this exercise is about.

Equation (5) in the paper needs the same condition stated: it is defined on a
per-slot series, not a sampled one.


## Regression gate — passed

Gated against the **pre-decision-9** pristine copies, so the correct result is
that decision 19 reproduces the decision-9 gate exactly:

```
topology     rows=450   identical=389   moved=61  (2pc_pipeline only)  forbidden=0
scalability  rows=1800  identical=1515  moved=285 (2pc_pipeline only)  forbidden=0
only column that moved, both files: avg_latency
baseline 2PC-CI mean latency: 126.822 == post-decision-9 value  (unchanged)
```

SHA-256, so the byte-identical claim is checkable from the commit alone. The
reference row was produced by rebuilding `629a0cd` in a throwaway `git worktree`
and re-running both sweeps there, which is the only way to separate a code change
from a stale artefact (`results/` is gitignored):

```
post-decision-9 (629a0cd, rebuilt in worktree)   post-decision-19 (243b9dd, this tree)
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  topology     IDENTICAL
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  scalability  IDENTICAL
```

Both hashes match exactly, so decision 19 moved no simulated quantity at all —
stronger than the column-wise gate, which only shows that nothing forbidden moved.

`cargo test --release`: 17 passed, 0 failed.


## The test that catches it

`tests/validation.rs::snapshot_series_accounts_for_every_ticked_slot` runs all
six arms through `run_experiment` and asserts, per arm: awake node-slots equal,
sleep equal, no duplicate rows, slots contiguous from 0, and `rows·N` equals
total node-slots charged.

Validated against the bug, not just written after it: with the three source
changes stashed the test fails with

```
tom_pipeline: energy counters charged 8607 awake node-slots but the snapshot
series accounts for 6096
```

which is the exact discrepancy Addition 6 measured.

## Decision 19b — the genuinely re-integrated amortised metric

Equation (5) re-integrated over the decision windows on the fixed series,
replicating `plot_paper_energy.py:101-125` exactly (script:
`/tmp/ctsim_validate/decision19b_amortised.py`).

You were right that I had not recomputed it. 86.07 / 97.53 / 109.85 were
`tick(L+F)/100` — the cumulative metric on seed 99 — so the "2 % and 3 %
agreement" I offered was one seed against fifteen, not a confirmation. The real
amortised means come out **below** the cumulative ones by exactly `f`, as you
predicted:

| arm | amortised (re-integrated) | cumulative | ratio | `f` | median | IQR |
|---|---|---|---|---|---|---|
| tom_pipeline | **86.07** | 86.07 | 1.00000 | 0.00000 | 84.50 | 9.00 |
| paxos_pipeline | **96.70** | 97.53 | 0.99149 | 0.00851 | 86.69 | 2.77 |
| 2pc_pipeline | **109.03** | 109.85 | 0.99253 | 0.00747 | 87.93 | 19.23 |
| tom_ce | 126.09 | 126.09 | 1.00000 | 0.00000 | 135.00 | 27.00 |
| paxos_ce | 373.68 | 373.68 | 1.00000 | 0.00000 | 378.00 | 54.00 |
| 2pc_ce | 640.44 | 640.44 | 1.00000 | 0.00000 | 621.00 | 81.00 |

The distribution — the metric's only independent content — is strongly
right-skewed for both pipelined CI arms: Paxos-CI median 86.69 against mean 96.70
with an IQR of 2.77 but a max of 277.30; 2PC-CI median 87.93 against mean 109.03,
IQR 19.23, max 327.91. So most decisions cost near the floor and a few early ones
carry the fill cost. The CE arms are near-symmetric (median above mean for
Paxos-CE and TOM-CE). Reporting only the mean hides this, which is the argument
for keeping the boxplot — on the fixed series.


`Σᵢ Eᵢ = Σ_{t : C_t > 0} Aₜ` over the in-window slots holds to `0.000000` in all
six, so the integration is exact.

**Notation (decision 24).** The unqualified form `Σᵢ Eᵢ = Σₜ Aₜ` that I wrote at
STOP #2 and STOP #3 is false whenever `f > 0`; it is only true restricted to the
covered slots. The correct statement and its residual:

```
Sum_i E_i  =  Sum_{t : C_t > 0} A_t          residual = Sum_{t : C_t = 0} A_t
```

| arm | residual (node-slots) | ÷ N (slots) | `f` |
|---|---|---|---|
| TOM-CI | 0 | 0.00 | 0.00000 |
| Paxos-CI | 83 | 3.07 | 0.00851 |
| 2PC-CI | 82 | 3.04 | 0.00747 |
| all three CE | 0 | 0.00 | 0.00000 |

The paper must write the restricted form too — a reviewer checking the unqualified
one finds it false.

TOM-CI has `f = 0` exactly: at depth 1 the windows tile the whole run, so no awake
slot falls outside one. That is another consequence of the structural depth-1
property, not a coincidence.


## Decision 20 — the bound holds to six decimals

| pair | amortised ratio | cumulative ratio | excess | predicted `(1−f_CE)/(1−f_CI)` | measured | exact? |
|---|---|---|---|---|---|---|
| TOM | 1.4650 | 1.4650 | +0.0000 % | 1.000000 | 1.000000 | yes |
| Paxos | 3.8643 | 3.8314 | +0.8583 % | 1.008583 | 1.008583 | yes |
| 2PC | **5.8740** | 5.8301 | **+0.7521 %** | 1.007521 | 1.007521 | yes |

Your identity is exact, not approximate — it is an algebraic consequence of
`Σᵢ Eᵢ = Σₜ Aₜ`, and `f` is measured, not bounded. The measured excess is 0.75 %
for 2PC, inside your 1 % threshold, so nothing else is going on.

Applying it to the 15-seed cumulative ratios:

| pair | 15-seed cumulative | × (1 + excess) | headline |
|---|---|---|---|
| TOM | 1.4352 | 1.4352 | 1.4x |
| Paxos | 3.8283 | 3.8612 | 3.8x |
| **2PC** | **5.6744** | **5.7171** | **5.7x** |

**Decision 26: print the measured 15-seed cumulative triple, 1.4 / 3.8 / 5.7.**
Not 3.9 for Paxos. The 3.9 exists only because a 15-seed cumulative ratio was
multiplied by an `f` measured on one seed, and for Paxos that composite changes the
printed digit (3.8283 → 3.8612). That is precisely the kind of mixed-provenance
number this exercise removes. One sentence covers the rest: the amortised metric
agrees with the cumulative triple to within 0.9 %, because the two share a mean
over the covered slots and differ only by `f`.

**Print 5.7x.** Not 5.8x (seed 99, not in the published seed list) and not 8.2x.

`f` is the only quantity in the identity that is measured rather than derived, and
its verification currently rests on a single seed. Addition 7 must report `f` per
seed with a standard error.

## Decision 25 — the median, on one seed, pending Addition 7

| protocol | median CI | median CE | median ratio | mean ratio |
|---|---|---|---|---|
| TOM | 84.50 | 135.00 | 1.598 | 1.465 |
| Paxos | 86.69 | 378.00 | 4.360 | 3.864 |
| 2PC | 87.93 | 621.00 | 7.062 | 5.874 |

The three CI medians span **4.1 %** — 84.50, 86.69, 87.93 — while the three CE
medians span a factor of 4.6. The typical decision under CI costs very nearly the
same energy whichever protocol produced it, and the whole spread in the CI means
comes from a small number of expensive early decisions. That is the decoupling
claim in its sharpest form, and it is harder to argue away than a statement about
means, since a mean can always be attributed to a tail.

Seed 99 only. Must be re-checked over the 15 published seeds in Addition 7 before
it goes anywhere near the paper.

**Refused in advance:** the median ratios are *larger* than the mean ratios and
7.062 sits close to the discredited 8.2. The median ratio is not a headline and
does not go in the abstract. It is a differently conditioned statistic — a ratio of
medians is not the median of ratios and has no `f`-identity behind it — and its
place is beside the distribution, defined explicitly, in the boxplot's caption
argument.



