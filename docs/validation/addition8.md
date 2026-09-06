# Addition 8 — the decomposition coefficients

Inputs: `addition7/data/runs.csv` (90 rows, N = 27 reference point, fifteen seeds)
and `addition7/data/charge14_maxCt.csv` (225 rows, five values of N). Scripts:
`addition7/scripts/addition8_coefficients.py`, `addition8_charges.py`,
`addition8_closure.py`. Nothing here is hand-typed.

Conventions, fixed by decisions 42, 43, 49 and 51 and applied without exception:

- a **share** is a ratio of sums; a **ratio** is a ratio of means; the aggregation
  is named in every sentence that prints one
- every `±` is a **95 % interval**, `t(0.975,14) = 2.144787` times a delete-one-seed
  jackknife standard error. Never an SE, never used interchangeably with one
- any multiplicative relation is closed under **one** aggregation on both sides, or
  its closure error is printed beside it

---

## The triple, decision 42

| arm | ratio of means | 95 % CI | jackknife SE | prints |
|---|---|---|---|---|
| TOM | 1.434823 | ± 0.018025 | 0.008404 | **1.4** |
| Paxos | 3.827738 | ± 0.075337 | 0.035126 | **3.8** |
| 2PC | 5.671896 | ± 0.298615 | 0.139228 | **5.7** |

The mean of per-seed ratios — 1.434281 / 3.832605 / 5.704037, ± 0.017905 /
0.067094 / 0.273692 — is recorded here and printed nowhere.

### The cost of decision 36, stated before a referee states it

The retired amortised metric is **2.8257×** more precise than the cumulative one on
Paxos and **2.3161×** on 2PC (half-widths 0.026661 and 0.128929 against 0.075337
and 0.298615). On TOM the cumulative metric is 0.11 % more precise, which is noise.
Amortising divides out exactly the tail-length variance that makes the cumulative
metric noisy, so this is expected — and it means decision 36 is paid for in
precision. The three grounds it is bought with are all non-statistical: the
mechanism is dead (charge 15 and item (b) of Addition 7), the magnitude of the
correction is not known to a printable digit (relative half-widths 99.2 % and
95.6 %), and `f` itself moves between definitions of the same series (charge 16).

---

## The floor — charge 25 resolved by fixing the aggregation

Charge 25 is upheld: the earlier report printed `1.441953 × 0.994353 = 1.433810`
against a measured 1.434823 and called the −0.071 pp difference a residue, when it
was a closure error between two aggregations. Under decision 49 the fix is not to
print the error but to remove it, by using one aggregation on both sides.

Ratio of sums throughout:

| quantity | value |
|---|---|
| measured floor | **1.434823** |
| `1/duty`, duty as a ratio of sums | 1.443210 |
| slots-per-decision factor, CE over CI | 0.994189 |
| product | **1.434823** |
| closure error | **0.0 %, exactly** |

The identity is exact because both factors and the measured ratio are now the same
kind of average. TOM commits 100 of 100 on all fifteen seeds, so its ratio of means
and ratio of sums coincide to machine precision, and the floor is unambiguous.

The two effects, each named once:

- duty cycling alone would predict **1.443210**, over-explaining the floor by
  **+0.5845 %**
- TOM-CE spends **0.994189** as many slots per decision as TOM-CI, a shortfall of
  **+0.5845 %** the other way

These are the same number with opposite signs, which is what an exact two-factor
product requires. The earlier report's "+0.497 % and +0.567 % and a 0.07 pp residue"
was three numbers where there is one.

**The floor is duty cycling, to within six tenths of a per cent, and nothing else.**
The manuscript's claim at 1979-1980 is correct in mechanism. Its number, 2.1, is not:
the measured floor is 1.4348.

---

## Slope and the Paxos residual — decision 50

OLS across the three arms is **deleted**. The reasons are in charge 26 and all
three hold:

1. the OLS intercept's 95 % interval, `[1.213036, 1.340272]`, **excludes** the
   measured floor 1.434823, so a fit anchored nowhere contradicts a floor derived
   independently
2. the OLS residual and the endpoint residual are not two estimators — their ratio
   is `0.666049`, a fixed constant of the three-point x-grid. One test, reported twice
3. three arms is not a curve; the pre-committed rule was no law fitted to three points

What remains is anchored at the floor and reports one interpolation:

| quantity | value | 95 % CI | separates from zero |
|---|---|---|---|
| endpoint slope per unit depth | 0.209190 | ± 0.013620 | — |
| Paxos residual, absolute | +0.162630 | ± 0.156234 → [+0.006396, +0.318864] | **yes** |
| Paxos residual, share of span | +0.038383 | ± 0.038617 → [−0.000234, +0.077000] | **no** |

Charge 26's first fault is upheld and it is the sharpest of the eight: the earlier
report said "excludes zero by 4 %" and then printed "fifteen seeds cannot separate
it from zero", choosing the one normalisation of three that gave the wanted answer.
Both rows above are the same measurement. The absolute residual separates; the
normalised one does not, because the span carries its own uncertainty into the
denominator.

**No linearity claim is printed.** The printable sentence names the normalisation:
Paxos sits **+0.1627 ± 0.1562** above the TOM–2PC interpolation, which is
**3.8 ± 3.9 %** of the span — separable from zero as an absolute displacement,
not separable as a fraction of the span.

---

## Charge 23 — the identity has falsifiable content, and it passes

The four-factor relation is an identity, as charged. `N` and the per-node energy
constant cancel, Little's law substitutes `D = depth · end_slot / L`, and the four
factors follow with nothing left to measure. **It is never printed as a finding and
the phrase "no free parameter" is withdrawn.**

But `E_CE` is **instrumented, not assumed.** `src/node.rs:70-72` increments
`slots_listen`, `slots_flood` and `slots_sleep` once per node per tick from the
node's own state; nothing anywhere in `src/` computes `N · L`. So
`E_CE = N · L̄ · c` is a falsifiable prediction about the instrument, and this is
its residual:

| arm | `sleep` total | `S = end_slot` | max abs relative residual |
|---|---|---|---|
| tom_ce | 0 | all 15 seeds | 2.2 × 10⁻¹⁶ |
| paxos_ce | 0 | all 15 seeds | 2.2 × 10⁻¹⁶ |
| 2pc_ce | 0 | all 15 seeds | 2.2 × 10⁻¹⁶ |

Machine epsilon on all 45 rows, with `slots_per_decision = L̄` exact to 0.0. That is
the content of decision 32 and it is worth one sentence: the instrument agrees with
the architecture's prediction to the last bit it can represent.

---

## The printed form — charge 24, decisions 48 and 49

The four-factor table is confined to this document. Its columns, ratio of means,
each with a 95 % interval:

| factor | TOM | Paxos | 2PC | TOM → 2PC |
|---|---|---|---|---|
| `1/duty` | 1.442567 ± 0.017091 | 1.441460 ± 0.017195 | 1.438619 ± 0.019235 | ×0.9973 |
| `L_ce/L_ci` | 0.995118 ± 0.007628 | 0.231659 ± 0.003465 | 0.192172 ± 0.005360 | ×0.1931 |
| depth | 1.000000 ± 0.000000 | 11.661524 ± 0.015311 | 21.254664 ± 0.218137 | ×21.2547 |
| `end_slot/S` | 0.999206 ± 0.001702 | 0.984681 ± 0.015726 | 0.970027 ± 0.028666 | ×0.9708 |
| measured ratio | 1.434823 | 3.827738 | 5.671896 | ×3.9530 |

Charge 24 upheld: multiplying that column gives 1.434385 / 3.834452 / 5.699995,
closing to −0.031 / +0.175 / +0.495 % — a product of ratios of means is not a ratio
of means of products, and the error grows monotonically with depth. A referee
multiplying the column would get 5.700 beside a stated 5.672.

**The printed form is the two-factor one, and under a consistent aggregation it is
exact.** Ratio of sums on both sides:

| arm | measured (RoS) | `1/duty` | slots/dec CE ÷ CI | product | closure |
|---|---|---|---|---|---|
| TOM | 1.434823 | 1.443210 | 0.994189 | 1.434824 | **0.0 %** |
| Paxos | 3.827738 | 1.442474 | 2.653592 | 3.827737 | **0.0 %** |
| 2PC | 5.677815 | 1.439671 | 3.943828 | 5.677815 | **0.0 %** |

Slots per decision: **4.7033 / 5.3540 / 6.1705** under CI against
**4.6760 / 14.2073 / 24.3353** under CE. Two measured numbers per arm, exact
closure, and it makes the point in one line.

One consequence to carry: 2PC's ratio of sums is **5.677815** against its ratio of
means **5.671896**, a gap of −0.1042 %, and 2PC is the only arm whose committed
count varies across seeds (five incomplete). TOM and Paxos commit 100 of 100 on
every seed, so both aggregations coincide there to machine precision. Decision 42
prints the ratio of means, 5.671896; the two-factor identity closes on the ratio of
sums. Both digits round to 5.7.

---

## Charge 28 — the sentence at 1981-1983 is void

The manuscript's span runs 2.1 → 8.2 under the amortised metric. The measured span
runs 1.434823 → 5.671896 under the cumulative one. Computing the error factor of a
sentence about the first from the span of the second is exactly the composite this
project has ruled out four times, and the earlier report's "wrong by a factor of 60"
did it. **No error factor is computable. The sentence is void**, because the metric
it describes is no longer printed, and its replacement attributes the span to depth
against round length:

- amortisation's own contribution, `1/(1−f)`, is **1.000850 / 1.016905 / 1.047902**;
  carrying TOM's ratio by 2PC's factor gives 1.502277 against a measured top of
  5.671896, so amortisation can account for **0.067454 of a span of 4.237073**
- what does account for it: depth rising **21.25×** against CE round length. Slots
  per decision under CE run 4.68 → 24.34 while under CI they run 4.70 → 6.18

---

## Decision 52 — the saturation row

Addition 8's coefficients are computed from `runs.csv`, which is **N = 27 only**:
90 rows, one topology, one loss rate, the fifteen-seed reference point. The
N = 188 runs appear solely in `charge14_maxCt.csv`, which feeds the max `C_t` table
and the charge-17 bound and nothing else. **No coefficient in this document pools
N = 188.**

At the reference point the zero-commit question does not arise either: 2PC-CI has
**five incomplete seeds** — 3, 7, 23, 31, 37, committing 95 to 99 — and **no
zero-commit seed**. How an incomplete seed enters, stated explicitly: under the
ratio of sums its awake node-slots go into the numerator and its committed count
into the denominator, so it contributes to both; under the ratio of means it
contributes one finite per-seed ratio. A zero-commit seed would contribute energy
and zero decisions to the ratio of sums, and an undefined term to the ratio of
means — decision 10's rule applies, and no such seed exists here.

The required row, restricted to the **ten seeds that commit 100 of 100 in every
arm** — 2, 5, 11, 13, 17, 19, 29, 41, 43, 47, so `t(0.975,9) = 2.262157`:

| quantity | fifteen seeds | ten fully-committing seeds | change |
|---|---|---|---|
| TOM ratio | 1.434823 ± 0.018025 | 1.419209 ± 0.014339 | −1.09 % |
| Paxos ratio | 3.827738 ± 0.075337 | 3.879175 ± 0.023178 | +1.34 % |
| 2PC ratio | 5.671896 ± 0.298615 | 5.945115 ± 0.182164 | **+4.82 %** |
| TOM depth | 1.000000 ± 0.000000 | 1.000000 ± 0.000000 | 0 |
| Paxos depth | 11.661524 ± 0.015311 | 11.665773 ± 0.019986 | +0.04 % |
| 2PC depth | 21.254664 ± 0.218137 | 21.493550 ± 0.051648 | +1.12 % |
| endpoint slope | 0.209190 ± 0.013620 | 0.220845 ± 0.009180 | +5.57 % |
| Paxos residual | +0.162630 ± 0.156234 | +0.104479 ± 0.076813 | −35.8 % |

The printed digits survive: 1.4 / 3.8 / **5.9** — and that last one does **not**
survive. Dropping the five incomplete seeds moves 2PC from 5.671896 to 5.945115,
which prints 5.9 rather than 5.7. So the selection matters more than the
uncertainty does, and the fifteen-seed row is the one to print: dropping seeds
because their runs were harder is selection on the outcome. The row above is
recorded so the sensitivity is visible, not so it can be chosen.

The residual's separation is also selection-sensitive: on ten seeds it is
+0.104479 ± 0.076813, which separates from zero more comfortably than the
fifteen-seed +0.162630 ± 0.156234 does. Neither is printed as a linearity result.

---

## Decision 41 — the printed duty cycle

Ratio of sums, fifteen seeds: TOM **0.692900**, Paxos **0.693253**, 2PC
**0.694603**, all three arms pooled **0.693660**. The printed figure is **0.69**,
and it is an insertion: neither 0.70 nor 0.69 occurs anywhere in the manuscript
today.

---

## Charge 18 — why the seed-mean density column must not exist

Withdrawn on your side; the substance is recorded here because the two aggregations
**disagree in direction**, which is the strongest argument decision 42 has.

| arm | `f` slot share (RoS) | `f` energy share (RoS) | pooled density |
|---|---|---|---|
| TOM | 0.00085046 | 0.00084857 | **0.997775** |
| Paxos | 0.01668534 | 0.01662420 | **0.996336** |
| 2PC | 0.03298023 | 0.03299890 | **1.000566** |

Pooled, TOM's and Paxos's drain tails hold a larger share of the slots than of the
energy, so they are **sparser** than the run average. The seed-mean aggregation of
the same per-seed identity gives 1.036123 / 1.016194 / 1.007734 — **denser**. A
Simpson reversal in the exact quantity decision 47's sentence turns on.

Hence decision 47's negative form is the only printable one: **no arm's drain tail
is materially sparser than its own run average**, which holds under every
aggregation, and "amortise it, the radio is off anyway" has no physical basis under
any of them.

---

## Corrections to `addition7.md`, folded in here

1. **The Paxos `max C_t` bound, decision 45.** `addition7.md` said `ceil(N/2)`,
   citing `bitmap.len()/2 + 1` at `src/protocol/paxos.rs:102`. In integer
   arithmetic that expression is `floor(N/2)+1`, the majority size, and the two
   differ for even `N` — which is exactly where the prose failed:

   | N | 6 | 13 | 27 | 54 | 188 |
   |---|---|---|---|---|---|
   | observed max `C_t` | 3 | 7 | 14 | 28 | 95 |
   | `ceil(N/2)` | 3 ✓ | 7 ✓ | 14 ✓ | 27 ✗ | 94 ✗ |
   | majority `floor(N/2)+1` | 4 ✓ | 7 ✓ | 14 ✓ | 28 ✓ | 95 ✓ |

   The bound is the **majority size**, attained for N ≥ 13 and unattained at N = 6.
   Nothing published moves: the reference point N = 27 is odd. The table, the code
   citation and the data were all correct; only the sentence joining them was wrong.

2. **The gate's wording, charge 21.** Zero differing cells across 630 comparisons
   including `avg_latency` to two decimals is **deterministic re-execution of the
   same seeds and configuration**, not an independent set of runs — on a real-valued
   quantity independence would make exact agreement impossible. Decision 40 is a
   **determinism check** from here on. The only genuinely independent comparison in
   that table is the two published sweeps against each other.

3. **TOM's duty ratio.** `addition7.md` printed 1.0847 where the script emits
   **1.036123** — a wrong number in a committed file, and the one that made charge
   18's "only TOM matches" look like a coincidence when it is exact. Paxos's
   1.047834 and 2PC's 1.014265 in that file are right.

4. **The `1.036 / 1.016 / 1.008` identification.** The earlier claim that the ratio
   between the two `f` definitions "is the drain tail's duty ratio from item (b)"
   equated two aggregations of the same per-seed identity:
   `mean(f_e)/mean(f_s)` against `mean(f_e/f_s)`. Withdrawn.

---

## The standing note

Charges 24, 25 and 26 are the sixth, seventh and eighth instances of a concluding
sentence contradicting a table printed in the same message, and all three were
mine. The mechanical check now applied before anything is written: for every
sentence stating a formula, a bound, a share or an inequality, evaluate it against
the nearest table and confirm the direction and the aggregation. Charge 24 would
have been caught by multiplying the column; charge 25 by dividing 1.441953 into
1.434823; charge 26 by dividing the half-width by the point estimate.
