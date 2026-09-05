# Addition 6 — the two energy paths

Read-only diagnosis. No code changed, nothing fixed. Companion to
`amortised_and_step1b.md`.

Commands:

```
./target/release/ctsim results/sim_<proto>_per_prop.toml   # x6, reads the
    # "Energy profile: Listen=.. Flood=.. Sleep=.." line off stdout
/tmp/ctsim_validate/addition6.py  > addition6.json   # Q1, Q2 shape, Q3
/tmp/ctsim_validate/addition6b.py > addition6b.json  # Q1', Q2', Q4
```

## Verdict up front

Your arithmetic is right, your CE control is right, and the gap is real. The
cause is not in either energy total. **Both energy accountings are correct; the
snapshot CSV is missing rows.** The snapshot path under-counts awake node-slots
because `phy/ci.rs` stops emitting snapshots when a flood wave ends early, while
`node.tick()` keeps charging those slots. So:

- The **tick path** (`node.slots_*` → `sweep_summary.csv` → Table III) is
  **authoritative**.
- The **snapshot path** (`snapshots_*.csv` → the amortised figures and the
  duty-cycle KDE) is **incomplete for CI** and correct for CE.
- Therefore 8.2x is the number that moves, not the Table III energy column.
  Direction: **8.2x → 5.83x**, i.e. the paper has been *overstating* CI's
  amortised advantage, not understating it.

## Q1 — does `listen + flood + sleep == N * end_slot` hold for CI?

**No, and it is not supposed to.** The identity is real but I stated its
right-hand side wrong at STOP #1, and so did the plan.

| sweep | rows | `phy=ce` max&#124;resid&#124; | `phy=ci` max&#124;resid&#124; | CI rows with resid > 0 |
|---|---|---|---|---|
| topology | 450 | 0 | 375354 | 173 of 225 |
| scalability | 1800 | 0 | 1263736 | 727 of 900 |

But the residual is never negative, and `(listen+flood+sleep)` is divisible by
`N` on **all 2250 rows**, as is the residual itself. So the correct identity is

```
listen + flood + sleep == N * (slots actually simulated)
```

and `end_slot` is not that. `run.rs:117-122` defines `end_slot` as
`max(proposal.end_slot)` — the last **decision** — whereas `tick()` runs until
the pipeline drains. The difference is a **drain tail** of complete slots:

| baseline cell (N=27, random, 0.05) | mean `end_slot` | mean simulated slots | drain tail |
|---|---|---|---|
| tom_pipeline | 469.9 | 470.3 | 0.40 (0.09 %) |
| paxos_pipeline | 526.5 | 535.4 | 8.93 (1.67 %) |
| 2pc_pipeline | 590.3 | 610.5 | 20.13 (3.30 %) |
| all three CE | — | — | 0.00 (exactly) |

CE has no tail because `sim.rs` returns the slot after the goal, so its last
proposal ends at the last simulated slot. Across all 900 CI scalability rows the
tail is a median 0.9 % of the run, mean 7.7 %, max 88.6 % — the extreme cases
being the `committed == 0` rows, where the whole run is tail (mean 68 %).

**No accounting hole.** The buckets are exact in every row of both sweeps.

## Q2 — the decisive single-run test

Same protocol, same seed (99), same config, both accountings:

| run | tick `listen+flood` | snapshot `Σ(listening+flooding)` | ratio |
|---|---|---|---|
| tom_pipeline | 8607 | 6096 | **1.4119** |
| paxos_pipeline | 9753 | 6918 | **1.4098** |
| 2pc_pipeline | 10985 | 7853 | **1.3988** |
| tom_ce | 12609 | 12663 | 0.9957 |
| paxos_ce | 37368 | 37422 | 0.9986 |
| 2pc_ce | 64044 | 64098 | 0.9992 |

**They are not equal, and the CI ratio is the 1.44x you reconstructed.**

The mechanism, and it accounts for the gap **exactly**:

```
snapshot_sleep - tick_sleep  ==  (number of all-Sleep snapshot rows) * N
    tom_pipeline    2565 == 95 * 27    exact
    paxos_pipeline  2889 == 107 * 27   exact
    2pc_pipeline    3186 == 118 * 27   exact
    all three CE       0 == 0 * 27     exact
```

`phy/ci.rs:110-121`: when no node will flood next slot, the round breaks out of
the loop after emitting one snapshot of the all-Sleep state. The next round then
calls `reset_round()` (`ci.rs:50-52`), which puts every node back to `Listen`,
and the first tick of that round charges `slots_listen`. The snapshot taken at
that boundary slot, however, was captured **before** the reset, so it records
27 sleeping nodes for a slot the tick counters charge as awake. There are 95–118
such boundary slots per run — one per round — and each contributes 27 node-slots
of pure bookkeeping disagreement. Verified: all 95 all-Sleep slots in
`snapshots_tom.csv` coincide exactly with proposal `end_slot` values, and the
snapshot at `slot+1` always shows 26 awake nodes.

The CE side has a mirror-image discrepancy of the opposite sign and trivial size
(−54 node-slots, 2 rows): `sim.rs` snapshots one row past the final tick, and the
snapshot grid contains one duplicated slot at the end in every run (`slot_max`
appears twice; 457 rows for 456 distinct slots). So the CE agreement at 0.996–0.999
is not exact either, just small.

Duty cycle, both ways:

| arm | duty from ticks | duty from snapshots |
|---|---|---|
| tom_pipeline | 0.7006 | 0.4940 |
| paxos_pipeline | 0.7000 | 0.4946 |
| 2pc_pipeline | 0.6919 | 0.4930 |
| all three CE | 1.0000 | 1.0000 |

Your 0.494 was the snapshot path; Table III's 0.70 was the tick path. Your
observation that the paper's own duty-cycle KDE excludes 0.494 is the tell —
except the KDE reads `snapshots_*.csv` too (`plot_kde_awake.py:89-90`), so it
should agree with 0.494 and not with 0.72. It reports 0.58–0.92 because it
plots the **per-slot distribution over awake slots**, whose mode sits high, not
the run-mean duty cycle. Both of those are the snapshot path; neither is the
tick path. So the KDE does not corroborate Table III — it is a third, differently
conditioned statistic, and the manuscript should not present it as if it
cross-checked the energy column.

### Why the tick path is authoritative

Four reasons, in order of weight:

1. **The tick counters are the physical model.** `node.rs:68-74` charges exactly
   one bucket per node per slot, unconditionally, from the state the node is in.
   Nothing can be dropped. `metrics.rs:49-69` only records a sample when a
   snapshot is *due and the round is still running*; `ci.rs:110-121` breaks the
   loop before that check on the last slot of every round. Missing samples, not
   wrong ones.
2. **`listen+flood+sleep` is divisible by `N` on all 2250 rows** and equals
   `N x final_snapshot_slot` on all six single runs. The snapshot sum satisfies no
   such identity for CI.
3. **The CE control validates the tick path, not the snapshot path.** All three
   CE arms reconstruct `N x end_slot` exactly from ticks (12609, 37368, 64044).
   The snapshot sums are 54 node-slots higher in each — small, but wrong.
4. `snapshot_interval` is a *reporting* knob. At interval 20 (the sweep) the
   snapshot path would miss 95 % of slots outright; the amortised figures only
   look plausible because their configs use interval 1. An energy metric whose
   value depends on the sampling rate is not an energy metric.

## Q3 — the configs differ, and it matters

`results/sim_<proto>_per_prop.toml` vs `sweep_scalability.toml`, field by field:

| field | per-prop TOML | sweep | same? |
|---|---|---|---|
| num_nodes | 27 | 27 (in list) | yes |
| topology | random | random | yes |
| loss_rate | 0.05 | 0.05 (in list) | yes |
| flood_repeats | 1 | 1 | yes |
| num_proposals | 100 | 100 | yes |
| abort_probability | 0.0 | 0.0 | yes |
| listen_timeout / max_round_slots | 5 / 300 | 5 / 300 | yes |
| **snapshot_interval** | **1** | **20** | **NO** |
| **max_slots** | **50000** | **100000** | **NO** |
| **seed** | **99** | 15-seed list, no 99 | **NO** |

`round_slots` is absent from both, so `None` in both — identical.

The physics is the same. `max_slots` differs but binds in neither (longest CE run
2374 slots). So the amortised set and Table III do describe the same experiment,
with two exceptions the paper must state: **a different seed, not drawn from the
published list**, and **a different snapshot rate**, which is exactly the knob the
snapshot-path metric is sensitive to.

## Q4 — what moves

Recomputing the amortised mean from the authoritative numerator. The corollary
you derived is correct and I use it: `mean amortised = (Σₜ Aₜ) / committed`.

| arm | published amortised | corrected (seed 99) | Table III cumulative (15 seeds) |
|---|---|---|---|
| tom_pipeline | 60.96 | **86.07** | 88.0 |
| paxos_pipeline | 68.62 | **97.53** | 100.2 |
| 2pc_pipeline | 77.98 | **109.85** | 115.8 |
| tom_ce | 126.09 | 126.09 | 126.3 |
| paxos_ce | 373.68 | 373.68 | 383.6 |
| 2pc_ce | 640.44 | 640.44 | 657.1 |

Every CE figure is unchanged (no all-Sleep rows, so nothing was missing). Every
CI figure rises by the 1.40–1.41x factor. The residual gap to Table III (86.07 vs
88.0) is the seed difference plus the drain tail, both of order a few percent, and
in the direction expected.

Matched ratios:

| pair | published amortised | corrected amortised (seed 99) | Table III cumulative (15 seeds) |
|---|---|---|---|
| TOM | 2.0684 | **1.4650** | 1.4352 |
| Paxos | 5.4456 | **3.8314** | 3.8283 |
| **2PC** | **8.2129** | **5.8301** | **5.6744** |

The corrected amortised ratios agree with the cumulative ratios to 2 % for Paxos
and 3 % for 2PC — which is what your corollary predicts they must, since the two
metrics share a mean by construction. That agreement is the confirmation that the
correction is the right one.

### Published numbers that move

Seed counts included per your Addition-1 amendment.

| manuscript location | printed | corrected | delta | seeds |
|---|---|---|---|---|
| abstract:156 `up to 8.2x better amortized per-decision energy` | 8.2x | **5.8x** | −2.4x | 1 |
| intro:274 `$8.2\times$ better amortized per-decision energy` | 8.2x | **5.8x** | −2.4x | 1 |
| intro:279 `amortized energy varies by only about $1.3\times$` | 1.3x | 1.28x | −0.02x | 1 |
| `fig_energy_boxplot` (all 6 series) | — | all 3 CI series shift up 1.40x | — | 1 |
| `fig_energy_stacked` (all 6 series) | — | same | — | 1 |
| `fig_latency_vs_energy` | — | CI points move right and up | — | 1 |
| `fig_energy_mean_ci_ce` | — | CI bars rise 1.40x | — | 1 |
| `energy_summary.csv` mean column, 3 CI rows | 60.96 / 68.62 / 77.98 | 86.07 / 97.53 / 109.85 | +41 % | 1 |
| duty-cycle KDE, CI panels | 0.58–0.92 | recompute from ticks | — | 1 |

**Table III's energy and efficiency columns do not move.** They were always on the
tick path. My STOP #2 answer that "8.2x survives unchanged" was correct about the
*bug* and wrong about the *metric*: the decision-9 fix does not touch it, but the
snapshot under-count does.

So of your two possible outcomes, it is the first: **8.2x becomes 5.8x and the
abstract changes.** The paper was overstating CI's amortised advantage by 41 % on
the CI side. The conservative reading is that the honest headline is the
cumulative ratio the 15-seed table already supports, **5.67x**, and the amortised
metric should be cited for its *distribution* only, which is its sole independent
content.

## One further correction to the manuscript, found while doing this

`intro:279` claims CI per-decision latency varies by `roughly $76\times$`. That
figure is the buggy 2PC latency: 357.71 / 4.699 = 76.12. With the corrected
latency it is 126.822 / 4.699 = **26.99x**. Over the topology sweep instead of
the baseline cell it is 226x including the `line` topology and 46.6x excluding it.
The `76x` must go regardless of which denominator you choose; add it to the
Addition-1 list. Seeds: 15.
