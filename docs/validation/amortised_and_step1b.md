# Amortised energy divisor, `record_proposal` audit, and Step 1b

Companion to `inventory.md`. Covers Additions 2 and 5 of the decision list and
Step 1b. Written after commit `629a0cd` (the decision-9 fix). No number below is
hand-typed: every value is emitted by a generator script in
`/tmp/ctsim_validate/` and pasted verbatim.

Commands, in order:

```
git commit -F -                                    # 629a0cd
./target/release/ctsim results/sim_<proto>_per_prop.toml   # x6, regenerates results/
/tmp/ctsim_validate/addition2.py   > addition2.json
/tmp/ctsim_validate/step1b.py      > step1b.json
```

Pristine copies for the gate: `/tmp/ctsim_validate/pristine/{topology,scalability}_sweep_summary.csv`
and `/tmp/ctsim_validate/pristine_energy/energy_{per_proposal,summary}.csv`
(SHA-256 recorded alongside).

---

## Addition 2 — the amortised-energy divisor `C_t`

### Is `C_t = 0` guarded, and how?

Yes, in both scripts, by **skip** — not substitution and not clamping.

- `plots/energy/plot_paper_energy.py:107-108`
  ```python
  safe_c       = np.where(concurrent > 0, concurrent, 1.0)
  cost_per_slot = np.where(concurrent > 0, awake / safe_c, 0.0)
  ```
  The `1.0` looks like a substitution but is dead: the outer `np.where` discards
  that branch and writes `0.0`.
- `plots/energy/plot_stacked_bar.py:97-98` — `if concurrent > 0:` guards the
  accumulation, so a `C_t = 0` slot contributes nothing.

Two spellings, identical semantics.

### The skip is provably inert

`C_t` counts proposals with `start_slot <= t < end_slot`. So `C_t = 0` means **no
proposal's window covers slot `t`**, and such a slot can never appear in
`[s_i, e_i)` for any `i`. The guard therefore zeroes only slots that no `E_i`
integrates over. Consequence, which is an identity rather than an approximation:

```
sum_i E_i  ==  sum_t A_t   over the slots where C_t > 0
```

Verified to `diff = 0.0000` for all six combinations. This is the crucial
difference from the `.replace(0, 1)` guard of Addition 3: that one fabricates a
denominator and changes published values; this one cannot.

Measured leakage — awake node-slots the guard drops, as a fraction of all awake
node-slots in the run:

| combination | snapshot slots | `C_t = 0` slots | of those, `A_t > 0` | awake node-slots dropped | fraction |
|---|---|---|---|---|---|
| TOM (CI)   | 457  | 2 | 0 | 0.0   | 0.000000 |
| Paxos (CI) | 518  | 7 | 4 | 55.0  | 0.008095 |
| 2PC (CI)   | 590  | 6 | 3 | 55.0  | 0.007004 |
| TOM (CE)   | 469  | 2 | 2 | 54.0  | 0.004264 |
| Paxos (CE) | 1386 | 2 | 2 | 54.0  | 0.001443 |
| 2PC (CE)   | 2374 | 2 | 2 | 54.0  | 0.000842 |

Under 1 % everywhere, and it is idle-tail energy outside every decision window,
not energy removed from a decision.

### Effect of the decision-9 fix on the published amortised figures

`C_t` is built from `start_slot`, so the fix reaches this path directly. Means,
recomputed from the regenerated single-seed runs against
`energy_summary.csv` as published:

| combination | published mean | recomputed mean | Δ | published median | recomputed median | published std | recomputed std |
|---|---|---|---|---|---|---|---|
| TOM (CI)   | 60.96  | 60.96  | 0.00 | 58.00  | 58.00  | 9.94  | 9.94  |
| Paxos (CI) | 68.62  | 68.62  | 0.00 | 61.92  | 61.92  | 24.25 | 24.25 |
| **2PC (CI)** | **77.98** | **77.98** | **0.00** | **60.41** | **64.04** | **59.61** | **33.10** |
| TOM (CE)   | 126.09 | 126.09 | 0.00 | 135.00 | 135.00 | 24.29 | 24.29 |
| Paxos (CE) | 373.68 | 373.68 | 0.00 | 378.00 | 378.00 | 29.66 | 29.66 |
| 2PC (CE)   | 640.44 | 640.44 | 0.00 | 621.00 | 621.00 | 62.48 | 62.48 |

**Every mean is unchanged, exactly.** Not approximately — to all printed digits.
The reason is the identity above. The bug moved the individual windows but not
their union: proposal 0 started at slot 0 either way, and the windows tile
forward, so the set `{t : C_t > 0}` is bit-identical before and after
(verified: `True`), and `sum_t A_t` over it is `7798.0` in both cases. Dividing
the same total by the same 100 committed proposals gives the same 77.98.

What the bug *did* corrupt is the **distribution**: 2PC-CI median rises
60.41 → 64.04 and the standard deviation nearly halves, 59.61 → 33.10, because
the buggy windows all started at 0 and so overlapped far more than they should
(`C_t` max 100 → 27, mean over active slots 60.93 → 21.58). So
`fig_energy_boxplot`, `fig_energy_stacked` and `fig_latency_vs_energy` are wrong
in shape for the 2PC-CI series, while `fig_energy_mean_ci_ce` and
`energy_summary.csv`'s mean column are correct.

### Does the 8.2x claim survive?

**Yes, unchanged.** Matched per-protocol ratios of amortised mean energy,
CE over CI:

| pair | ratio |
|---|---|
| TOM CE / TOM CI | 2.068 |
| Paxos CE / Paxos CI | 5.446 |
| **2PC CE / 2PC CI** | **8.213** |

The manuscript's `8.2x` (abstract line 156, introduction line 274) is the 2PC
pair, and it is 8.213 before the fix and 8.213 after it. Direction: no movement,
zero magnitude.

Two caveats the manuscript should carry regardless, both independent of the bug:

1. **The claim rests on one seed.** `plot_stacked_bar.py:26` hardcodes
   `seed = 99`, and the whole amortised-energy figure set is that single run.
   There are no error bars on 8.2x and no seed variance behind it, unlike the
   15-seed table. `up to 8.2x` is defensible as a point measurement; it should
   not be read as a mean over configurations.
2. The unqualified maximum over all pairs is `worst CE / best CI` =
   640.44 / 60.96 = **10.506x**, which the paper does not claim. The stated 8.2x
   is the matched-protocol figure, which is the conservative and correct choice.

---

## Addition 5 — every `record_proposal` call site

Eight sites; `metrics.rs:73` is the definition, seven are calls.

| site | protocol / path | start-slot source | classification |
|---|---|---|---|
| `sim.rs:116` | CE, all three protocols, normal completion | `round_start`, captured at `sim.rs:89` as `self.current_slot` before the round runs | **recorded directly** |
| `sim.rs:78` | CE, `max_slots` exhausted | `self.current_slot` passed as *both* start and end | **degenerate**: latency identically 0 |
| `paxos_pipeline.rs:125` | Paxos/CI, quorum commit | `self.proposal_starts`, inserted at `:108` with `core.current_slot` | **recorded directly** |
| `paxos_pipeline.rs:181` | Paxos/CI, commit learned from a received `last_accepted_term` | same map | **recorded directly** |
| `tom_pipeline.rs:205` | TOM/CI, in-order delivery | `self.msg_starts`, inserted at `:89` with `core.current_slot` | **recorded directly** |
| `two_pc_pipeline.rs:149` | 2PC/CI, unanimity resolve | `self.tx_starts`, inserted at `:119` | **recorded directly** (was derived; fixed in `629a0cd`) |
| `two_pc_pipeline.rs:251` | 2PC/CI, fast abort | `self.tx_starts` | **recorded directly** (was hardcoded `0`; fixed in `629a0cd`) |

No remaining site derives its start slot. Two observations that are suspect in
shape but do not affect any published number — reported, not fixed:

- **`sim.rs:78` sets start = end.** Every timed-out CE proposal exports
  `latency = 0` in `results_*.csv`. Harmless for the tables because
  `run.rs:95-105` and `metrics.rs:101-107` both average over `Committed` only,
  and the baseline cell has zero timeouts. It would silently deflate any future
  metric that averaged over all outcomes.
- **`unwrap_or(0)` on all three CI start-slot lookups** (`paxos_pipeline.rs:124`,
  `:180`, `tom_pipeline.rs:204`, `two_pc_pipeline.rs:148`, `:250`) is the same
  failure mode as the bug just fixed, one step away: a term recorded without a
  matching insertion would report `start = 0` silently. Currently unreachable —
  the protocol object is shared, so every term passes through its own insert —
  and confirmed empirically: exactly one proposal per run has `start_slot = 0`
  (proposal 0), and all 100 start slots are distinct in all three CI arms. A
  `debug_assert!` would close it; not done without authorisation.

### Line-number inconsistency in my own reports — resolved

TOM has **one** `record_proposal` site, not two. `tom_pipeline.rs:205` is the
call; `:89` is where `msg_starts` is populated. The inventory's `:204` was an
off-by-one on the call site (it cited the enclosing `for` line), and the STOP #1
report cited the insertion site. Same single mechanism, two different lines of
it. No second instance of the defect in TOM.

---

## Step 1b — Table III reproduced from the regenerated data

Table read from `plots/scalability/table_summary_N27_loss05.tex`; data from the
regenerated `plots/scalability/results/sweep_summary.csv`; slice N = 27,
`random`, loss 0.05; 15 seeds per row, asserted in the script.

30 cells checked, printed value / recomputed value:

| protocol | Commit (%) | Thr. | Lat. | Energy/dec | Eff. |
|---|---|---|---|---|---|
| TOM (CI)   | 100.0 / 100.0 | 0.2132 / 0.2132 | 4.7 / 4.7 | 88.0 / 88.0 | 2.43 / 2.43 |
| Paxos (CI) | 100.0 / 100.0 | 0.1903 / 0.1903 | 61.4 / 61.4 | 100.2 / 100.2 | 1.91 / 1.91 |
| 2PC (CI)   | 98.9 / 98.9 | 0.1681 / 0.1681 | **357.7 / 126.8** | 115.8 / 115.8 | 1.46 / 1.46 |
| TOM (CE)   | 100.0 / 100.0 | 0.2143 / 0.2143 | 4.7 / 4.7 | 126.3 / 126.3 | 1.70 / 1.70 |
| Paxos (CE) | 100.0 / 100.0 | 0.0704 / 0.0704 | 14.2 / 14.2 | 383.6 / 383.6 | 0.18 / 0.18 |
| 2PC (CE)   | 100.0 / 100.0 | 0.0412 / 0.0412 | 24.3 / 24.3 | 657.1 / 657.1 | 0.06 / 0.06 |

**29 of 30 cells match to the last printed digit. The single mismatch is the
pre-authorised one**: 2PC (CI) latency, printed 357.7, corrected 126.8,
Δ = −230.878. Zero unauthorised mismatches, so nothing moved that the
byte-identical gate did not already account for.

### Derived pipeline depth, and the tautology question

Depth `= throughput x latency` (Little's law), computed post hoc from the CSVs.
**Derived, never measured** — no depth code exists in `src/`, `plots/`, `tools/`
or `docs/`.

| combination | mean | std | min | max |
|---|---|---|---|---|
| TOM (CI)   | 1.0000  | 0.0000 | 1.0000  | 1.0000  |
| Paxos (CI) | 11.6615 | 0.0276 | 11.6133 | 11.7030 |
| 2PC (CI)   | 21.2547 | 0.3940 | 20.3710 | 21.6068 |
| TOM (CE)   | 1.0000  | 0.0000 | 1.0000  | 1.0000  |
| Paxos (CE) | 1.0000  | 0.0000 | 1.0000  | 1.0000  |
| 2PC (CE)   | 1.0000  | 0.0000 | 1.0000  | 1.0000  |

**CE depth = 1.00 is STRUCTURAL. It is a tautology and must not be reported as a
finding.** The file and line that settle it: `src/sim.rs:75` iterates
`for proposal_id in 0..num_proposals`; `:89` sets `round_start = self.current_slot`;
`:111` sets `self.current_slot = end_slot`. Each proposal therefore starts exactly
where its predecessor ended, so the windows tile the timeline without overlap and

```
depth = (C / end_slot) * (sum_i lat_i / C) = sum_i lat_i / end_slot = 1
```

identically. Confirmed: `max|sum_i lat_i - end_slot| = 0.000000` across all 15
seeds of all three CE protocols, and the per-proposal chain is exactly contiguous
(`start_{i+1} == end_i` for all i, 0 overlapping pairs). One proposal per round is
enforced by the loop, not observed.

**TOM (CI) depth = 1.0000 is also structural**, for a different reason, and this
one matters more because it sits on the proposed architecture's side. TOM/CI
delivers each message in the round that floats it, so its windows are contiguous
too (0 overlapping pairs, `sum lat = 455 = max_end`), giving exactly 1 to
machine precision on every seed. It is not evidence of pipelining; it is evidence
that TOM/CI does not pipeline at this operating point.

Paxos/CI (11.66) and 2PC/CI (21.25) are the only genuinely measured depths: their
windows overlap 99 pairs out of 99, `sum lat / end_slot` is 11.61–11.70 and
20.37–21.61 respectively, and the value varies across seeds. The manuscript's
`about 12` for Paxos survives; `about 60` for 2PC does not (see the STOP #1
table).
