# Additions 1 and 3 — consolidated patch list

**Nothing in this file has been applied.** It is the patch list only.

## Which file

The manuscript is **`paper/paper.tex`** in this repository, committed at `e0dceb1`:
2700 lines, 140,826 bytes, sha256
`039118e9c14c5f7a0f8e324e0957535b87ca9899befa1384547930e1ce694c27`. It is the file
formerly at `~/Downloads/paper (3).tex`, byte-identical.

Three near-identical copies previously shared that directory — a 502-line skeleton
confusingly named `paper.tex`, a 797-line draft, and a 2659-line draft that also
contains `tab:escape`. All three, plus the original of the tracked file, are now in
`~/Downloads/paper_superseded/`. Exactly one manuscript is reachable from a working
directory, and every line number in this document resolves against `paper/paper.tex`.


## Method and commands

```
/tmp/ctsim_validate/addition1_grep.py        -> addition1_grep.json
/tmp/ctsim_validate/addition1_values.py      -> addition1_values.json
/tmp/ctsim_validate/addition1_remaining.py   -> addition1_remaining.json
/tmp/ctsim_validate/addition1_distribution.py-> addition1_distribution.json
/tmp/ctsim_validate/addition3_zerocommit.py  -> addition3.json
/tmp/ctsim_validate/decision19b_amortised.py -> decision19b.json
```

Sources: `plots/{topology,scalability}/results/sweep_summary.csv` at commit
`51a961d` (post-decision-9, post-decision-19), and the six seed-99 per-proposal
runs for anything per-decision. No number below is hand-typed.

**Seed counts.** Every row carries one. 15 seeds means the published list
`[2,3,5,7,11,13,17,19,23,29,31,37,41,43,47]`. 1 seed means **99**, which is not in
that list — the amortised path uses it alone (`plot_stacked_bar.py:26`).

## Occurrence counts

Per the standing rule: every number proposed for change, grepped over the whole
file. The abstract's numbers repeat three to seven times, as predicted.

| number | occurrences | lines |
|---|---|---|
| `357.7` | **4** | 1438, 1460, 1813, 2077 |
| `358` (rounded, same quantity) | **1** | 1829 |
| about 60 / sixty, depth | **4** | 160, 311, 1827, 2566 |
| `60` bare, depth | 3 | 160, 311, 543 |
| `60.1` | 1 | 1813 |
| `8.2` | **5** | 160, 312, 1970, 1974, 1983 |
| `5.4` | 7 total, **2** relevant | 1970, 1973 (218/237/399/434/2455 unrelated) |
| `2.1` | **3** | 1973, 1979, 1980 |
| `76` × | **2** | 317, 2083 |
| `1.3` × | **2** | 318, 2084 |
| within `1.5 %` | **4** | 163, 314, 1298, 2575 |
| `11.7` | 2 | 1812, 2373 |
| `0.4 %` duty cycle | 2 | 407, 1316 |
| `-2.2 %` latency | 1 | 2431 |
| `127` | 2 | 2008, 2075 |
| `88` | 1 | 1948 |
| `115.8` | 1 | 1438 |
| `100.2` | 1 | 1437 |
| `126.3` / roughly 126 | 3 | 1440, 1911, 1987 |

Two corrections to my own grep: `-2.2 %` returned zero hits because the pattern
missed LaTeX math delimiters — it is at **2431** as `$-2.2$\,\%`, and it does move.
And `358` at **1829** is the same 2PC-CI latency rounded differently, so it is a
**fifth** site for that number, on neither list.

## The consolidated patch list

Legend. **B19** = value depends on the amortised metric, so it was recomputed on
the fixed series and is **1 seed (99)** until Addition 7 lands. **cum** = cumulative
metric, 15 seeds. A row marked *pending Addition 7* must not be printed yet.

### A. 2PC-CI latency and everything derived from it (decision 9)

| line | printed | corrected | delta | seeds |
|---|---|---|---|---|
| 1438 `tab:baseline` latency cell | 357.7 | **126.8** | −230.9 (−64.6 %) | 15 |
| 1460 prose "357.7 slots per decision" | 357.7 | **126.8** | −230.9 | 15 |
| 1813 `tab:depth` latency cell | 357.7 | **126.8** | −230.9 | 15 |
| 1829 prose "each decision takes 358 slots" | 358 | **127** | −231 | 15 |
| 2077 `tab:escape` latency cell | 357.7 | **126.8** | −230.9 | 15 |
| 1813 `tab:depth` depth cell | 60.1 | **21.3** | −38.8 (−64.6 %) | 15 |
| 160 abstract "about 60 for 2PC" | 60 | **21** | −39 | 15 |
| 311 intro "about 60 for 2PC" | 60 | **21** | −39 | 15 |
| 543 §II "60 for 2PC" | 60 | **21** | −39 | 15 |
| 1827 prose "about sixty" | sixty | **twenty-one** | — | 15 |
| 2373 depth-invariance "about sixty" | sixty | **twenty-one** | — | 15 |
| 2566 conclusions "about sixty" | sixty | **twenty-one** | — | 15 |

Measured depth 21.255 ± 0.218 (95 % CI, 15 seeds). Paxos-CI 11.662 ± 0.015, so
**11.7 at 1812 and 2373 stands**.

### B. `tab:escape`, lines 2075-2077 — every cell in the 2PC row moves

> **Superseded by decision 30.** The amortised column below divides a 15-seed
> `L`-derived ceiling by a one-seed energy, which decision 27 forbids. The printable
> table is the cumulative rebase under "Decision 30" at the end of this document.
> Kept here because the derived corrections were verified and the amortised version
> returns in section 7.5 once Addition 7 lands.

Ceiling is `27 L`, so it inherits the latency fix. Energy column is the amortised
metric, so it inherits decision 19.

| row | L printed → corr. | E printed → **B19** | ceiling printed → corr. | escape printed → **B19** |
|---|---|---|---|---|
| TOM (CI) | 4.7 → 4.7 | ≈59 → **86.1** | 127 → 127 | ≈2× → **1.5×** |
| Paxos (CI) | 61.4 → 61.4 | ≈69 → **96.7** | 1658 → 1658 | ≈24× → **17.1×** |
| 2PC (CI) | 357.7 → **126.8** | ≈78 → **109.0** | 9658 → **3424** | ≈124× → **31.4×** |

L: 15 seeds. E and escape: 1 seed, *pending Addition 7*. The user's derivation
reproduces to the printed digit in all six cells.

Cumulative-metric alternative, 15 seeds, if the table is re-based: E 88.0 / 100.2 /
115.8, escape 1.4× / 16.5× / 29.6×. **The escape column differs by metric at the
second digit, so the caption at 2062-2064 must keep saying which metric it uses.**

Headline consequence: "escape the ceiling by about 124×" → **about 31×**, a factor
of four.

### C. Line 2083-2084 — the second 76× site

| quantity | printed | corrected | seeds |
|---|---|---|---|
| CI latency growth TOM → 2PC | 76× | **27.0×** | 15 |
| amortised energy growth TOM → 2PC | 1.3× | **1.27×** | 1, B19 |

The 1.3 survives rounding either way (cumulative gives 1.32), which is the point of
the sentence. Line **317** carries the same 76× and line **318** the same 1.3×.

### D. Lines 1968-1983 — the 2.1 / 5.4 / 8.2 triple, five instances

| line | printed | corrected |
|---|---|---|
| 1970 "about 5.4 for Paxos and about 8.2 for 2PC" | 5.4, 8.2 | **3.8, 5.7** |
| 1973 "about 2.1 for TOM, 5.4 for Paxos and 8.2 for 2PC" | 2.1, 5.4, 8.2 | **1.4, 3.8, 5.7** |
| 1979 "the 2.1-fold saving arises entirely from duty cycling" | 2.1 | **1.4** |
| 1980 "The number 2.1 therefore marks the floor" | 2.1 | **1.4** |
| 1983 "the distance from there to 8.2 under 2PC" | 8.2 | **5.7** |
| 160 abstract "up to 8.2x better" | 8.2 | **5.7** |
| 312 intro "$8.2\times$ better amortized" | 8.2 | **5.7** |

Per decision 26 these are the **15-seed cumulative** ratios 1.4348 / 3.8277 /
5.6719, not the seed-99 amortised ones. One added sentence should state that the
amortised metric agrees to within 0.9 %.

Also at 160: **"up to 4x higher throughput"** — measured CI/CE throughput ratios are
TOM 0.995, Paxos 2.703, **2PC 4.083** (15 seeds). "Up to 4×" holds.

### E. `tab:baseline` energy and efficiency, lines 1436-1442

The energy column is the **cumulative** metric, unaffected by decision 19, and every
cell reproduces from the post-fix sweep. Reported for completeness because Addition
1's amendment asked whether Addition 6 moved them: **it did not.**

| row | printed E/dec | measured | printed Eff. | measured | seeds |
|---|---|---|---|---|---|
| TOM (CI) | 88.0 | 87.991 ✓ | 2.429 | 2.429 ✓ | 15 |
| Paxos (CI) | 100.2 | 100.215 ✓ | 1.906 | 1.906 ✓ | 15 |
| 2PC (CI) | 115.8 | 115.844 ✓ | 1.463 | 1.463 ✓ | 15 |
| TOM (CE) | 126.3 | 126.252 ✓ | 1.705 | 1.705 ✓ | 15 |
| Paxos (CE) | 383.6 | 383.598 ✓ | 0.184 | 0.184 ✓ | 15 |
| 2PC (CE) | 657.1 | 657.054 ✓ | 0.063 | 0.063 ✓ | 15 |

So `fig_energy_mean_ci_ce` and the mean column of `energy_summary.csv` **cannot**
stay as printed after all — they read the amortised path, which moved 41 %. It is
`tab:baseline` that stays. The Addition 1 amendment's question is answered the
opposite way round from how it was posed.

### F. The distributional prose, lines 2003-2032 — three claims break

> **Rewritten under "Section F" at the end of this document.** Not blocked on
> Addition 7: both false claims rest on extrema, and more seeds can only make an
> extremum worse in both directions.

Re-checked on the fixed series. **1 seed (99)**, so the extrema below are the least
stable statistic available — which is the point.

| line | claim | verdict |
|---|---|---|
| 2005-2007 | most expensive CI decision, incl. outliers, is cheaper than the least expensive Paxos-CE decision | **FALSE.** max CI 327.91 vs min Paxos-CE 324.00. Overlaps by 3.91 node-slots. |
| 2008 | TOM-CE median "near 127" | **135.0.** Off by 6 %; 127 is the *ceiling* `27 L`, not the median |
| 2016 | cheapest 2PC-CI decisions cost less than the median TOM-CI decision | **FALSE.** min 2PC-CI 86.44 vs median TOM-CI 84.50 |
| 2011-2012 | 2PC-CI has the widest IQR of the CI family | **TRUE.** 19.23 vs TOM 9.00, Paxos 2.77 |
| 2029-2030 | bulk of CI decisions below 100 | **TRUE**, 97 % / 86 % / 71 % |
| 2030 | TOM-CE "sits coherently between 100 and 150" | 94 % inside; range 108–270 |
| 2031-2032 | Paxos-CE and 2PC-CE lie entirely above 300 | **TRUE**, 100 % both, minima 324 and 540 |

The two false claims are both "no overlap at all" statements, and both fail by a few
node-slots at the extreme tail. They were true on the broken series because it
under-counted CI by 1.41×. Weakening them to compare medians or quartiles instead of
extrema would make them true and would still carry the argument.

### G. Sites resting on the amortised metric — 1249, 2194, 2376

| line | claim | verdict |
|---|---|---|
| 1249-1251 | "a per-decision amortised form of this metric, which is the appropriate basis for comparing architectures that complete different numbers of decisions in the same interval" | **Stands, but needs decision 23's condition.** Add that the metric is defined on a per-slot series. |
| 2193-2197 | "The ratios quoted earlier were based on the amortised metric and are therefore larger… the two differ under CI by the fixed overhead of the pipeline" | **"therefore larger" now rests on 0.86 % / 0.75 %, not 45 %.** Same falsified causal story as 1950-1951 — see the replacement text below. |
| 2376-2383 | "the amortisation factor is an architectural design parameter and not a network accident" | **Stands and strengthens.** Depth per topology, 15 seeds: 2PC-CI 21.446 ± 0.071 (full mesh), 21.455 ± 0.028 (partial), 21.255 ± 0.218 (random), 20.954 ± 0.199 (scale-free) — a 2.3 % span across a 4× diameter range. Paxos-CI 11.589 / 11.623 / 11.662 / 11.657, span 0.6 %. |

### H. Line 1899 — "confirmed empirically to two decimal places"

`C_t ≡ 1` for CE. Measured depth is **exactly 1.0000 with zero variance across all
15 seeds in all four dense topologies** — and it is **structural, not empirical**:
`sim.rs:75` iterates proposals one at a time, `:89` sets `round_start =
current_slot`, `:111` sets `current_slot = end_slot`, so windows tile the run and
`depth = Σlat / end_slot = 1` identically. One exception: `line`/2PC-CE reports
0.997 ± 0.004 because 2 of 15 seeds abort one proposal each.

The claim is true but "confirmed empirically" overstates what the measurement can
show. Recommend "which follows structurally from sequential processing and is
reproduced to four decimal places in the measurements".

### I. Lines 163, 314, 1298, 2575 and `tab:identity` — "within 1.5 %"

> **Superseded by charge 2 / decision 28.** The finding below is right about the
> mechanism and wrong about its severity: the error column is zero *by construction*
> in all fifteen rows, not merely understated in one. See "Charge 2 accepted" at the
> end of this document.

Four prose sites plus the table at 2317-2335.

The printed error column says `<10⁻¹²` for all fifteen rows. Measured:

- fourteen of fifteen cells are exact to floating point, max deviation `1.7×10⁻¹⁴` %
- **`line`/2PC-CE is not**: printed predicted 7190.926 and measured 7190.926, but
  `27 · mean L = 7172.298`. The printed "predicted" column is `E/27` fed backwards,
  not `27 · L`.
- group error there is **0.2597 %**; worst single seed is **1.9362 %**, which is
  outside the claimed 1.5 % band

Cause: seeds 23 and 37 commit 99 of 100 proposals, so `E/dec` divides by 99 while
`avg_latency` averages over 99 — the mismatch is the one aborted proposal's
node-slots. All thirteen fully committing seeds are exact.

So: the 1.5 % claim survives **as a statement about group means** (max 0.26 %), fails
as a statement about individual measurements (max 1.94 %), and the `<10⁻¹²` column
is not recoverable as printed. Recommend recomputing the predicted column as
`27 · L` and printing the real per-cell errors, with a footnote on the two aborting
seeds.

### J. Lines 407 and 1316 — the 0.4 % duty cycle

Decision 2 dropped this target. Measured CI duty cycle (awake node-slots / total),
15 seeds, loss 0.05: full mesh 0.738, partial mesh 0.774, random 0.694, scale-free
0.717, line 0.599. **Three orders of magnitude away from 0.4 %.**

Line 407 is a literature citation of BlueFlood's measurement and is fine. Line
1311-1318 is not: it says the simulator's parameters are *calibrated* to reproduce
99.9 % PDR at 0.4 % duty cycle. Neither quantity is computed anywhere in the
simulator — PDR is never derived (see `inventory.md`), and the duty cycle is 0.6–0.8.
**That paragraph describes a calibration that has not been performed.** It is
Steps 2-5 of this validation, still pending, and until they land the claim is
unsupported rather than wrong.

### K. `tab:degree`, lines 2429-2435 — the random → scale-free table

Recomputed as the caption defines it, "the mean of the fifteen per-seed relative
differences", 15 seeds throughout:

| row | lat printed | lat measured | Δlat printed | Δlat measured (±95 %) | Δthr printed | Δthr measured |
|---|---|---|---|---|---|---|
| TOM (CI) | 4.6 | 4.6 | −2.8 % | **−2.53 %** ± 3.85 | +3.0 % | **+3.33 %** |
| Paxos (CI) | 59.6 | 59.6 | −2.9 % | **−2.60 %** ± 4.19 | +2.9 % | **+3.16 %** |
| **2PC (CI)** | **350.0** | **124.7** | **−2.2 %** | **−1.34 %** ± 4.03 | +0.1 % | **+0.51 %** |
| TOM (CE) | 4.6 | 4.6 | −1.3 % | **−1.07 %** ± 3.84 | +1.3 % | **+1.53 %** |
| Paxos (CE) | 15.9 | 15.9 | +11.9 % | **+11.97 %** ± 2.10 | −10.7 % | **−10.60 %** |
| 2PC (CE) | 33.3 | 33.3 | +36.9 % | **+37.15 %** ± 7.03 | −26.7 % | **−26.52 %** |

The 2PC-CI latency cell moves 350.0 → **124.7**. The four CI/TOM-CE Δlat cells all
have CI half-widths larger than the point estimates, so "indifferent to within about
3 %" at 2440-2441 is better stated as "not distinguishable from zero at 95 %" — which
is a stronger claim, not a weaker one, and the paired-sign evidence at 2442-2445
already supports it.

### L. `tab:diameter`, lines 2237-2243 — unaffected

Percentages printed as `+72 / +72 / +73 / +70 / −7 / −21`; measured (prior accepted
result, not recomputed) `+72.50 ± 2.10 / +72.22 ± 2.04 / +73.94 ± 2.80 / +70.80 ±
2.07 / −6.99 ± 0.59 / −21.24 ± 0.85`, 15 paired seeds. All six printed values stand.
Throughput only, so decision 9 and decision 19 do not reach it.

## Addition 3 / decision 10 — the zero-commit cells

Guard `.replace(0, 1)` removed. Where `committed = 0` the per-decision quantity is
**undefined and propagates as a missing value, never a number**. Every cell below is
a triple: commit rate, contributing seeds, and a mean explicitly labelled
**conditional**. Never a bare per-decision energy.

Four cells, 29 zero-commit rows, all `2pc_pipeline/ci`:

| cell | seeds | commit rate | published | **conditional** ± 95 % | inflation |
|---|---|---|---|---|---|
| `line` N=27 loss 0.05 | **1 / 15** | 0.200 % | 190180.8 | **81940.0**, n = 1, no CI | 2.32× |
| `random` N=188 loss 0.05 | 14 / 15 | 86.400 % | 40902.3 | 8211.0 ± 7986.4 | 4.98× |
| `random` N=188 loss 0.10 | 11 / 15 | 62.467 % | 195641.5 | 15934.9 ± 18858.0 | 12.28× |
| `random` N=188 loss 0.20 | 5 / 15 | 23.200 % | 709687.4 | 22139.5 ± 20138.1 | 32.06× |

The `line` cell rests on **one seed**, which committed 3 of 100 proposals. The
conditional value 81940.0 is recoverable and printed; what it lacks is a confidence
interval, which is a different statement. Published 190180.8 is that seed's whole-run
energy divided by 1 under the guard.

The three `random` cells have 95 % half-widths at or above their own means, so even
the conditional mean is not separable from zero. Survivorship bias is severe by
construction: at 20 % loss only the 5 easiest seeds enter the average.

Affected artefacts: `table_topology_N27_loss05.{csv,tex}` (the `line` row), all four
`*_vs_topology` figures, and `throughput_vs_nodes`, `latency_vs_nodes`,
`efficiency_vs_nodes`, `commit_rate_vs_nodes` (the N=188 rows). **`tab:baseline` /
Table III is unaffected** — no zero-commit seed at N=27 random.

### A second defect in the same cell, not previously reported

`table_topology_N27_loss05.tex:8` prints **latency 108.1** for `line`/2PC-CI. That is
`mean(avg_latency)` over 15 seeds where **14 export `avg_latency = 0.00` because they
commit nothing**. It is a mean over fourteen zeros and one real value.

- pre-decision-9: fourteen zeros and 1621.33 → mean **108.1** = the printed value
- post-decision-9: fourteen zeros and 346.67 → mean **23.11**
- conditional on the one committing seed: **346.67**

This is the only group in either sweep where some seeds export zero latency and
others do not — checked exhaustively. So the `line` cell needs the triple treatment
on **latency as well as energy**, and the printed 108.1 is doubly wrong: it is a
diluted mean of a quantity that is undefined for 14 of 15 seeds, computed from the
pre-fix latency.

## Regeneration list

Blocked on Addition 7, not to be run yet: `fig_energy_boxplot`,
`fig_energy_stacked`, `fig_latency_vs_energy`, `fig_energy_mean_ci_ce`, the
duty-cycle KDE, and `energy_{per_proposal,summary}.csv`. All read the amortised path
on seed 99.

Must be recomputed under decision 28, independently of decisions 9 and 19:
**`tab:identity`** — unaffected by those two decisions is not the same as correct.

Not blocked and correct as printed: `tab:baseline`, `tab:diameter`, `tab:topologies`,
and every throughput-only figure.

## The falsified paragraph — one correction to the replacement argument first

Decision 24 proposes the drain tail is "substantial when measured in SLOTS but nearly
free when measured in ENERGY, **because the nodes are asleep during it**". The first
half holds. **The mechanism does not, and for 2PC-CI it is backwards.**

Measured on the one run where both sides exist (seed 99, per-slot series):

| arm | `C_t = 0` slots | % of slots | awake node-slots | % of energy | duty *inside* the tail | duty overall | ratio |
|---|---|---|---|---|---|---|---|
| TOM-CI | 0 | 0.000 | 0 | 0.000 | — | 0.7006 | — |
| Paxos-CI | 5 | 0.969 | 83 | 0.851 | 0.6148 | 0.7000 | **0.88** |
| 2PC-CI | 4 | 0.680 | 82 | 0.747 | 0.7593 | 0.6919 | **1.10** |
| all three CE | 0 | 0.000 | 0 | 0.000 | — | 1.0000 | — |

Paxos-CI nodes are 12 % *more* asleep in the tail than on average. **2PC-CI nodes are
10 % more awake.** The tail is cheap because it is **four or five slots long**, not
because the radios are off. Proportionality, not duty cycling.

Second correction, and it is the same class of error decision 26 rejects: the pairing
"1.67 % and 3.30 % of slots against under 0.9 % of energy" combines a **15-seed**
slots figure with a **1-seed** energy figure. The 15-seed slot shares are 0.0850 % /
1.6685 % / 3.2980 % (aggregate) and the energy shares are seed 99 only. **They cannot
be printed as a contrast until Addition 7 produces 15-seed energy shares.** On the
one run where both are measured the two shares are nearly equal.

Third: **there is no fill cost at all.** Every `C_t = 0` slot in all six arms lies
*after* the last decision commits — verified, not assumed. The first proposal starts
at slot 0, so the pipeline is never empty at the front. The overhead is a drain tail
only, and "filling the pipeline at the start of the run" at line 1949 describes
something that does not happen.

Fourth: **"it shrinks for larger workloads" is untestable with the existing data.**
`proposals = 100` in every row of both sweeps — 2250 rows, one workload. Drop it, as
instructed; it cannot be shown, not merely unshown.

### Replacement text for lines 1943-1954

> **HELD under decision 29.** Structure kept, numbers deferred to Addition 7. The
> draft below still contains the forbidden composite — "$0.9\,\%$ for Paxos" is
> seed 99 while "$1.7\,\%$ of the slots" is 15 seeds — and the "better than one per
> cent" sentence that the 15-seed projection contradicts. **Do not apply it.** It is
> retained only so the structure survives to Addition 7; every figure in it is
> replaced there. See "Charge 1 accepted" below.

Replaces the paragraph beginning "The relationship between the two is instructively
architecture-dependent."

> The relationship between the two is instructively architecture-dependent. Under
> \CE, strict sequentiality means that no slot falls outside the lifetime of some
> active proposal, so the two metrics coincide identically and both reduce to
> $\Nnodes \cdot L$. Under \CI{} the two can differ, because a slot in which no
> proposal is in flight is charged by the cumulative metric and not by the amortised
> one. Measured, that difference is small: it is exactly zero for TOM, whose unit
> depth makes the decision windows tile the run, and it is $0.9\,\%$ for Paxos and
> $0.7\,\%$ for 2PC. The two metrics therefore agree to better than one per cent
> under every combination measured here.
>
> The slots responsible are worth identifying, because they are the pipeline's real
> overhead and they are not where one would expect. They all fall \emph{after} the
> last decision commits: the pipeline drains at the end of the run, but it is never
> empty at the start, since the first proposal is admitted in slot zero. There is no
> fill cost. The drain accounts for $1.7\,\%$ of the slots of a Paxos run and
> $3.3\,\%$ of a 2PC run, and it carries $0.9\,\%$ and $0.7\,\%$ of the energy
> respectively---a tail whose energy cost is roughly proportional to its length, and
> which is small because it is short rather than because the radios are idle within
> it. Under either definition the relative ordering of the combinations is unchanged.

Two sentences deleted deliberately: **"The gap between the two metrics under \CI{} is
itself a measure of the fixed overhead of the pipeline"** — it measured snapshot
bookkeeping, not overhead — and **"it shrinks for larger workloads"**, which the data
cannot address. The "roughly 59 against 88" figure goes with them: the corrected pair
is 86.07 against 86.07.

### Replacement text for lines 2190-2197

> **HELD under decision 29.** Same defect: "agree to within one per cent" is a
> seed-99 statement, and the projection puts 2PC at 3.6 %. Structure kept, figure
> deferred to Addition 7.

Replaces "One remark on the energy metric is needed before the results." through
"the relative ordering of the combinations is the same under either."

> One remark on the energy metric is needed before the results. This subsection uses
> the \emph{cumulative} metric of Section~\ref{sec:results-energy}, the same quantity
> reported in Table~\ref{tab:baseline}. The ratios quoted earlier were based on the
> \emph{amortised} metric of Equation~\eqref{eq:amortized}; the two agree to within
> one per cent, since they differ only over the slots in which no proposal is in
> flight, and the ordering of the combinations is identical under either.

The printed clause "and are therefore larger" is arithmetically still true — 0.86 %
and 0.75 % larger — but it invited the reader to expect a gap of tens of per cent and
attributed it to a mechanism that does not exist. The clause "differ under \CI{} by
the fixed overhead of the pipeline" is the same falsified causal story as line 1950
and must go with it.

---

# Amendments under decisions 27-30

## Charge 1 accepted — my replacement text committed the defect it diagnosed

The paragraph paired a 15-seed slot share with a seed-99 energy share, one section
after I identified that as the forbidden composite. It also argued proportionality
and printed a 4× discount in the same breath. Withdrawn.

The identity you state reproduces exactly:

```
energy share = slot share × (duty inside tail / duty overall)
0.9690 % × 0.8783 = 0.8510 %      Paxos-CI
0.6803 % × 1.0973 = 0.7465 %      2PC-CI
```

Projected onto the 15-seed slot shares — **a projection, not a measurement**, since
the duty ratio is still seed 99:

| arm | slot share (15 seeds, aggregate) | × duty ratio (1 seed) | projected `f` | projected excess |
|---|---|---|---|---|
| TOM | 0.0850 % | 1.0000 | 0.0850 % | 1.000851 |
| Paxos | 1.6685 % | 0.8783 | 1.4655 % | 1.014873 |
| 2PC | 3.2980 % | 1.0973 | 3.6189 % | 1.037548 |

Consequence confirmed: projected amortised ratios are 1.436 / 3.885 / 5.885, printing
**1.4 / 3.9 / 5.9**. So the metric choice moves the printed digit for 2PC as well as
Paxos, and decision 26 is load-bearing for both. Held for Addition 7.

Per-seed slot shares carry 95 % half-widths of 0.1702 / 1.5726 / 2.8666 against
means of 0.0794 / 1.5319 / 2.9973 — every one wider than its own estimate, because
the drain tail is present in only some seeds. Another reason not to print the pairing
until `f` is measured per seed.

## Charge 2 accepted — `tab:identity` is vacuous, not understated

`predicted = 27 · (E/27) = E` identically, so the error column is **zero by
construction in all fifteen rows**. The fourteen "exact" rows are tautological. The
table never computes `27 · L`, so it cannot be evidence for the identity — it assumes
what it reports as verified. My "understates by twelve orders of magnitude" was too
kind and hid the finding.

### The cross-check holds, and it is one mechanism

`line`/2PC-CE per seed: **thirteen seeds commit 100/100 and give depth exactly
1.000000. Seeds 23 and 37 commit 99/100 and give 0.981079 and 0.981006.** Mean
0.997472, std 0.006671 — which is the published 0.997 ± 0.004.

The orphan's length: `end_slot − Σlat` is 512.34 and 512.22 slots against a mean
decision length of 267.78, so the orphan occupies **1.913×** the mean decision, not
2.3×. Depth for those seeds is 0.981, not 0.977. Both figures are close enough that
your mechanism is confirmed: **seeds 23 and 37 explain the identity residual and the
sub-unit depth simultaneously.** The aborted proposal's slots are charged to the run
and to `end_slot` but divide into no decision, so they depress depth and inflate
`E/dec` by the same node-slots. Neither is an anomaly.

## Charge 3 refuted — all three hold, and the reason is which denominator

You are right that `depth = 1` does not *imply* tiling; mean 1 permits `C_t = 2` here
and `0` there. But the three facts do not conflict, because **the published depth
divides by `end_slot`, not by simulated slots.**

TOM seed 99, measured directly: `C_t` histogram is `{1: 455}` — every slot has
exactly one proposal in flight, 0 slots at `C_t = 0`, max `C_t = 1`, 0 overlapping
pairs among 100 proposals, `Σlat / end_slot = 1.000000`.

Across 15 seeds: **depth is exactly 1.000000 with std 0.0**, min = max = 1. And
`Σlat = end_slot` to the slot in all fifteen. So `C_t ≤ 1` everywhere and the windows
tile `[0, end_slot)` with no gaps — measured, on every seed.

The drain tail lives **beyond** `end_slot`. Only **1 of 15 seeds** (seed 41) has one:
`end_slot = 498`, simulated 504, drain 6 slots. Its depth over `end_slot` is still
1.0000; over simulated slots it is 0.988095. The 0.085 % aggregate drain share is
that single seed spread over fifteen.

So: `depth = 1.0000` ✓, windows tile `[0, end_slot)` ✓, drain tail 0.085 % ✓ — no
contradiction, because the tail is outside the depth denominator. Your alternative
`469.9/470.3 = 0.99915` is depth over *simulated* slots, a different and equally
defensible statistic that the paper does not use.

**Where you are right anyway:** `C_t ≤ 1` for TOM is **not structurally guaranteed.**
`tom_pipeline.rs:84-89` publishes at most one message per round and `:199` delivers
in order, so windows are non-decreasing in both endpoints — but if two terms complete
in the same slot at `:203-210`, both windows end together while the later one starts
later, giving `C_t = 2`. Recovery can do this. It did not on any of these 15 seeds.
So "unit depth makes the windows tile the run" is not printable as a structural
claim; the printable version is that it is measured to hold on every seed. And
**TOM's `f = 0` is a property of the 14 seeds with no drain tail, not of the
protocol** — seed 41 has `f > 0`. Both concessions stand.

## Decision 27 — seed hygiene, applied

Withdrawn from the list above: the `tab:escape` amortised column (15-seed ceiling ÷
1-seed energy), the slots-versus-energy pairing, "agree to better than one per cent",
and section F's extrema. Every table above already carries its seed count; seed 99 is
now marked "one run" wherever it survives, and it survives only as an illustration.

## Decision 30 — `tab:escape` rebased on the cumulative metric, 15 seeds throughout

| row | L | E (cumulative) | ceiling `27 L` | escape | printed escape |
|---|---|---|---|---|---|
| TOM (CI) | 4.699 | 87.991 | 126.882 | **1.44×** | ≈2× |
| Paxos (CI) | 61.394 | 100.215 | 1657.638 | **16.54×** | ≈24× |
| 2PC (CI) | 126.822 | 115.844 | 3424.194 | **29.56×** | ≈124× |

15 seeds in every cell. Headline "escape the ceiling by about 124×" → **about 30×**.
Caption must name the metric. One escape factor per table; the amortised version goes
beside the distribution in 7.5 once Addition 7 lands.

## Decision 28 — regeneration list corrected

`tab:identity` was listed under "unaffected by decisions 9 and 19", which is true and
irrelevant. It **must be recomputed** under decision 28. Moved.

## Addition 3 — the `line` cell contradiction resolved

You are right: the inflation factor was computed from a denominator the same row
called unavailable. Both columns are now filled and labelled **n = 1**. Having no
confidence interval is not the same as not being recoverable.

| cell | seeds | commit rate | published | conditional (n=1) | inflation |
|---|---|---|---|---|---|
| `line` N=27 loss .05, energy | 1 / 15 | 0.200 % | 190180.8 | **81940.0** | 2.32× |
| `line` N=27 loss .05, latency | 1 / 15 | 0.200 % | **108.1** | **346.67** | — |

Latency triple in full: published **108.1**, post-decision-9 diluted mean **23.11**,
conditional **346.67**, n = 1. Fourteen seeds export `avg_latency = 0.00`; this is the
only such group in either sweep. Belongs in the paper as a footnote to the zero-commit
discussion.

## Section F rewritten — lines 2003-2032

Both false claims are no-overlap-at-all statements resting on extrema, and an
extremum is the least stable statistic available: more seeds can only raise the CI
maximum and lower the Paxos-CE minimum. Addition 7 cannot rescue either sentence, so
they are replaced now with median and quartile statements, which the data supports.

Quartiles, seed 99, one run:

| arm | min | q25 | median | q75 | max | IQR |
|---|---|---|---|---|---|---|
| TOM-CI | 78.00 | 81.00 | 84.50 | 90.00 | 107.00 | 9.00 |
| Paxos-CI | 83.46 | 85.52 | 86.69 | 88.29 | 277.30 | 2.77 |
| 2PC-CI | 86.44 | 87.32 | 87.93 | 106.56 | 327.91 | 19.23 |
| TOM-CE | 108.00 | 108.00 | 135.00 | 135.00 | 270.00 | 27.00 |
| Paxos-CE | 324.00 | 351.00 | 378.00 | 405.00 | 459.00 | 54.00 |
| 2PC-CE | 540.00 | 594.00 | 621.00 | 675.00 | 864.00 | 81.00 |

Pooled CI upper quartile 91.00 against Paxos-CE's lower quartile 351.00 — a factor of
**3.86** with 260 node-slots of clear air. That is the separation the extremum
sentence was reaching for, and it survives resampling.

On 2008: TOM-CE's median is **135.0**, and `135.0 / 27 = 5.0000` slots exactly — the
median decision takes five slots. The 15-seed mean latency is 4.676, so `27 L =
126.25`; seed 99's own mean is 4.67, giving 126.09. **127 is a ceiling computed from a
mean, not a central tendency**, and the paper prints it where a median belongs.

### Replacement text for lines 2003-2009

> The distributional view adds two further observations. First, the \CI{} and the
> vote-based \CE{} families occupy separate regions of the cost axis: the upper
> quartile of the pooled \CI{} decisions lies at 91 node-slots, while the lower
> quartile of Paxos over \CE{} lies at 351, a factor of $3.9$ apart with no
> interquartile overlap. The extreme tails do touch---the most expensive \CI{}
> decision observed in a single run costs slightly more than the cheapest Paxos
> decision over \CE---but $99\,\%$ of \CI{} decisions fall below the whole of the
> Paxos-over-\CE{} range. TOM over \CE{} occupies an intermediate position: its median
> decision costs 135 node-slots, exactly five slots of network-wide radio time, above
> every \CI{} median and far below the two vote-based \CE{} protocols. That median
> should not be confused with the ceiling $\Nnodes \cdot L = 126$ predicted by
> Equation~\eqref{eq:ece} from the mean latency; the two are different statistics of
> the same distribution.

### Replacement text for lines 2011-2021

Keep the paragraph. One sentence changes — the extremum claim at 2016-2017:

> ...so much so that the lower quartile of 2PC decisions under \CI{} sits below the
> median TOM decision under \CE---whereas proposals at the end of the run, as the
> pipeline drains, find less concurrency to share with and end up more expensive.

The IQR ordering it rests on is verified: 19.23 for 2PC-CI against 2.77 for Paxos-CI
and 9.00 for TOM-CI, so 2PC does have the widest box of the \CI{} family. Only the
"cheapest 2PC beats median TOM-CI" comparison was false (86.44 against 84.50); against
TOM over **CE** the same shape of claim holds with room to spare, and at the quartile
rather than the extremum it is stable.

### Unchanged

2011-2012 (2PC-CI has the widest IQR), 2029-2030 (bulk of CI below 100: 97 % / 86 % /
71 %; TOM-CE 94 % inside 100-150), and 2031-2032 (Paxos-CE and 2PC-CE entirely above
300: 100 % of both, minima 324 and 540). All verified true. Note 2031-2032 is also an
extremum claim, but it holds with 100 % of the mass on the correct side rather than
by a margin of 3.91 node-slots, so it is not fragile in the same way.







