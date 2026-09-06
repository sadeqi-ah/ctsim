# Manuscript patch specification

Author-applied, per decisions 31 and 35. **Nothing in this file has been
applied to `paper/paper.tex`.** No agent writes to the manuscript.

Base file: `paper/paper.tex`, 2701 lines, sha256
`039118e9c14c5f7a0f8e324e0957535b87ca9899befa1384547930e1ce694c27`.
This matches the agreed base, so every line number below is valid.

Every *current text* block is sliced out of the file by line number by
`docs/validation/addition7/scripts/make_patch_spec.py`, so it is a byte-exact
copy and not a reconstruction. Apply the entries **bottom-up** — from the
highest line number to the lowest — so that earlier edits do not shift the
line numbers of later ones.

Entries are in line order. 32 entries, all final. Blocked items carry no
numbers and are listed separately at the end.

---

## 1. `paper/paper.tex` line 83

Authorised by decision 33.

**Current text** (byte-exact, 1 line):

```latex
\newcommand{\ReLI}{ReLI}                  % protocol name, kept upright
```

**Replacement text:**

```latex
\newcommand{\ReLI}{ReLI}                  % protocol name, kept upright
\newcommand{\Send}{S_{\mathrm{end}}}      % slot of the last commit
\newcommand{\Ssim}{S_{\mathrm{sim}}}      % total slots ticked
```

**Sources.** No numbers. Required by the entry at 1244-1251, which distinguishes the two run lengths; neither macro is defined in the file today.

**Blocked:** no.

---

## 2. `paper/paper.tex` lines 159-161

Authorised by decisions 36, 42, 44.

**Current text** (byte-exact, 3 lines):

```latex
pipeline sustains, on average, about 12 concurrent proposals for Paxos and
about 60 for 2PC, yielding up to 4x higher throughput and up to 8.2x better
amortized per-decision energy efficiency than CE-based counterparts. We
```

**Replacement text:**

```latex
pipeline sustains, on average, about 12 concurrent proposals for Paxos and
about 21 for 2PC, yielding up to 4x higher throughput and up to 5.7x better
per-decision energy efficiency than CE-based counterparts. We
```

**Sources.** depth: runs.csv, committed/end_slot x avg_latency, 15 seeds -> 11.6615 and 21.2547. Ratio: runs.csv awake_tick/committed, ratio of means, 15 seeds -> 5.671896 +- 0.298615 (jackknife 95 %). 'amortized' deleted: decision 36 prints the cumulative metric only.

**Blocked:** no.

---

## 3. `paper/paper.tex` lines 162-164

Authorised by decision 32.

**Current text** (byte-exact, 3 lines):

```latex
further show that CE architectures obey a structural identity that locks
per-decision energy to per-decision latency, validated within 1.5 percent
across fifteen independent configurations, and that pipelining breaks this
```

**Replacement text:**

```latex
further show that CE architectures obey a structural identity that locks
per-decision energy to per-decision latency, exactly and by construction, and
that pipelining breaks this
```

**Sources.** No measured error band exists to quote: the residual is 1/depth - 1, an arithmetic restatement of the commit rate, and it is zero in every fully committing configuration. Instrumented check: runs.csv sleep = 0 on all 45 CE rows; awake/committed against 27 x avg_latency agrees to 2.2e-16.

**Blocked:** no.

---

## 4. `paper/paper.tex` lines 310-319

Authorised by decisions 32, 36, 42, 44.

**Current text** (byte-exact, 10 lines):

```latex
simulator, we find that the pipeline sustains about 12 concurrent proposals
for Paxos and about 60 for 2PC, that this concurrency yields up to
$4\times$ higher throughput and up to $8.2\times$ better amortized
per-decision energy, and---most importantly---that \CE{} architectures obey
the identity $\Ece = \Nnodes L$, which holds within 1.5\% across fifteen
independent measurements spanning a $26\times$ range of network diameters.
Pipelining breaks that identity: across our \CI{} configurations,
per-decision latency varies by roughly $76\times$ while amortized energy
varies by only about $1.3\times$. Latency stops being a proxy for energy
and becomes a variable a designer can deliberately spend.
```

**Replacement text:**

```latex
simulator, we find that the pipeline sustains about 12 concurrent proposals
for Paxos and about 21 for 2PC, that this concurrency yields up to
$4\times$ higher throughput and up to $5.7\times$ better
per-decision energy, and---most importantly---that \CE{} architectures obey
the identity $\Ece = \Nnodes L$, which holds exactly and by construction
across fifteen independent measurements spanning a $26\times$ range of network
diameters. Pipelining breaks that identity: across our \CI{} configurations,
per-decision latency varies by roughly $27\times$ while per-decision energy
varies by only about $1.3\times$. Latency stops being a proxy for energy
and becomes a variable a designer can deliberately spend.
```

**Sources.** depth and ratio as at 159-161. 27x: sweep_summary.csv avg_latency, 126.822/4.699 = 26.987, 15 seeds, ratio of means, topology 'random'. 1.3x: runs.csv cumulative_per_dec 115.84/87.99 = 1.317, 15 seeds, so the printed 1.3 survives the metric change.

**Blocked:** no.

---

## 5. `paper/paper.tex` lines 542-543

Authorised by decision 42.

**Current text** (byte-exact, 2 lines):

```latex
Section~\ref{sec:results} reports the resulting depth: approximately 12
concurrent proposals for Paxos and 60 for 2PC.
```

**Replacement text:**

```latex
Section~\ref{sec:results} reports the resulting depth: approximately 12
concurrent proposals for Paxos and 21 for 2PC.
```

**Sources.** depth: runs.csv, 15 seeds -> 11.6615 +- 0.0153 and 21.2547 +- 0.2181.

**Blocked:** no.

---

## 6. `paper/paper.tex` lines 1244-1251

Authorised by decisions 33, 42.

**Current text** (byte-exact, 8 lines):

```latex
\item \textbf{Awake slots.} The total number of slots in which a node's
radio was transmitting, receiving or listening. In low-power wireless,
radio-on time is the dominant contributor to energy consumption, and the
distribution of this quantity across nodes indicates how evenly that cost
is borne. Section~\ref{sec:results} additionally derives a per-decision
amortised form of this metric, which is the appropriate basis for
comparing architectures that complete different numbers of decisions in
the same interval.
```

**Replacement text:**

```latex
\item \textbf{Awake slots.} The total number of slots in which a node's
radio was transmitting, receiving or listening. In low-power wireless,
radio-on time is the dominant contributor to energy consumption, and the
distribution of this quantity across nodes indicates how evenly that cost
is borne. Two run lengths must be distinguished, because they differ whenever
the pipeline drains. $\Send$ is the slot at which the last decision commits,
and throughput and pipeline depth are per $\Send$; $\Ssim$ is the total number
of slots ticked, and energy is per $\Ssim$. Under \CE{} the two coincide in
every measurement reported here. Under \CI{} they differ by the drain tail,
by $0.09\,\%$ for TOM, $1.70\,\%$ for Paxos and $3.41\,\%$ for 2PC at the
reference point, reaching $23.4\,\%$ on a single seed.
```

**Sources.** runs.csv, simulated_slots and end_slot, 15 seeds, ratio of sums: sum(S)/sum(end_slot) - 1 = 0.000851 / 0.016968 / 0.034105. Worst single seed: 2PC seed 7 at 1.2344, i.e. 23.44 %. S = end_slot on all 45 CE rows. Requires the \Send and \Ssim macros added by the entry at line 83.

**Blocked:** no.

---

## 7. `paper/paper.tex` lines 1296-1298

Authorised by decision 32.

**Current text** (byte-exact, 3 lines):

```latex
the identity $\Ece = \Nnodes \cdot \Lround$ of
Equation~\eqref{eq:ece}, which Section~\ref{sec:results} confirms to
within 1.5\,\% across fifteen configurations; per-node radio state
```

**Replacement text:**

```latex
the identity $\Ece = \Nnodes \cdot \Lround$ of
Equation~\eqref{eq:ece}, which Section~\ref{sec:results} confirms exactly
across fifteen configurations; per-node radio state
```

**Sources.** As at 162-164: no error band. sweep_summary.csv, 45 CE rows, sleep = 0 and listen+flood = 27 x simulated_slots exactly.

**Blocked:** no.

---

## 8. `paper/paper.tex` line 1438

Authorised by decision 9.

**Current text** (byte-exact, 1 line):

```latex
2PC (\CI)   & 98.9  & 0.1681 & 357.7 & 115.8 & 1.463 & 5034 \\
```

**Replacement text:**

```latex
2PC (\CI)   & 98.9  & 0.1681 & 126.8 & 115.8 & 1.463 & 5034 \\
```

**Sources.** sweep_summary.csv avg_latency, N=27 random loss 0.05, 15 seeds, mean 126.822. The published 357.71 predates the decision-9 tx_starts fix (commit 629a0cd). Every other cell in the row is unchanged and was reproduced exactly.

**Blocked:** no.

---

## 9. `paper/paper.tex` lines 1458-1462

Authorised by decision 9.

**Current text** (byte-exact, 5 lines):

```latex
For the vote-based protocols the pattern differs. The \CI{} variants are
far ahead on throughput and efficiency despite latencies several times
higher: 2PC over \CI{} takes 357.7 slots per decision against 24.3 for
its \CE{} counterpart, yet delivers more than four times the throughput
and more than twenty times the efficiency. The commit-rate column shows
```

**Replacement text:**

```latex
For the vote-based protocols the pattern differs. The \CI{} variants are
far ahead on throughput and efficiency despite latencies several times
higher: 2PC over \CI{} takes 126.8 slots per decision against 24.3 for
its \CE{} counterpart, yet delivers more than four times the throughput
and more than twenty times the efficiency. The commit-rate column shows
```

**Sources.** As at 1438. 'several times higher' and the 4x and 20x claims all survive: 126.822/24.335 = 5.21x, throughput 0.1681/0.0412 = 4.08x, efficiency 1.463/0.063 = 23.2x, all 15 seeds.

**Blocked:** no.

---

## 10. `paper/paper.tex` lines 1811-1813

Authorised by decisions 9, 42, 43.

**Current text** (byte-exact, 3 lines):

```latex
TOM (\CI)   & 0.2132 & 4.7   & 1.00 \\
Paxos (\CI) & 0.1903 & 61.4  & 11.7 \\
2PC (\CI)   & 0.1681 & 357.7 & 60.1 \\
```

**Replacement text:**

```latex
TOM (\CI)   & 0.2132 & 4.7   & 1.00 \\
Paxos (\CI) & 0.1903 & 61.4  & 11.66 \\
2PC (\CI)   & 0.1681 & 126.8 & 21.25 \\
```

**Sources.** runs.csv, 15 seeds: depth 1.000000 +- 0.000000, 11.661524 +- 0.015311, 21.254664 +- 0.218137 (jackknife 95 %). Latency from sweep_summary.csv. TOM and Paxos throughput and latency unchanged.

**Blocked:** no.

---

## 11. `paper/paper.tex` lines 1825-1833

Authorised by decisions 9, 42.

**Current text** (byte-exact, 9 lines):

```latex
Second, the informal claim of overlap becomes a specific number: Paxos
over \CI{} keeps about twelve proposals in flight on average and 2PC over
\CI{} about sixty. This is precisely how 2PC over \CI{} sustains a
throughput of 0.168 decisions per slot while each individual decision
takes 358 slots---the high latency is not slowness but the consequence of
each decision spending most of its life alongside dozens of others. It
also explains why 2PC runs deeper than Paxos: the longer waiting window
imposed by unanimity accumulates more proposals in the system
simultaneously.
```

**Replacement text:**

```latex
Second, the informal claim of overlap becomes a specific number: Paxos
over \CI{} keeps about twelve proposals in flight on average and 2PC over
\CI{} about twenty-one. This is precisely how 2PC over \CI{} sustains a
throughput of 0.168 decisions per slot while each individual decision
takes 127 slots---the high latency is not slowness but the consequence of
each decision spending most of its life alongside dozens of others. It
also explains why 2PC runs deeper than Paxos: the longer waiting window
imposed by unanimity accumulates more proposals in the system
simultaneously.
```

**Sources.** depth as at 1811-1813; latency as at 1438. The mechanism sentence is unchanged and is confirmed structurally: two_pc_pipeline.rs:131 holds a transaction pending exactly num_nodes rounds, so max C_t = min(N, num_proposals) on all 75 2PC runs of charge14_maxCt.csv.

**Blocked:** no.

---

## 12. `paper/paper.tex` lines 1875-1881

Authorised by decisions 36, 44.

**Current text** (byte-exact, 7 lines):

```latex
A fair accounting of energy under high offered load must take into account
that in the pipelined architecture several decisions are in flight at
once, as Table~\ref{tab:depth} has just quantified. Conventional
radio-on accounting double-counts in this situation: a slot of radio
activity that simultaneously serves sixty proposals must not be charged
sixty times at full cost. We therefore define the amortised per-decision
energy. For each successful proposal $i$ with lifetime $[s_i, e_i)$,
```

**Replacement text:**

```latex
A fair accounting of energy under high offered load must take into account
that in the pipelined architecture several decisions are in flight at
once, as Table~\ref{tab:depth} has just quantified. Alongside the cumulative
metric we therefore also decompose the radio cost across the decisions that
were in flight when it was incurred. This decomposition is not the basis of
any ratio reported in this paper; it exists to give the per-decision
\emph{distributions} below. For each
successful proposal $i$ with lifetime $[s_i, e_i)$,
```

**Sources.** No numbers. The deleted sentence ('a slot of radio activity that simultaneously serves sixty proposals must not be charged sixty times at full cost') is the justification for the amortised metric, which decision 36 retires; and its 'sixty' is 21.25 on 15 seeds. The cross-reference is to sec:results-energy, the only label in that section; if the distributional subsubsection at 2001 is given its own label, point it there instead.

**Blocked:** no.

---

## 13. `paper/paper.tex` lines 1899-1900

Authorised by decision 18.

**Current text** (byte-exact, 2 lines):

```latex
and $C_t \equiv 1$---an assumption Table~\ref{tab:depth} has now confirmed
empirically to two decimal places. And the radio of every node stays on
```

**Replacement text:**

```latex
and $C_t \equiv 1$---which is structural under \CE{} rather than measured.
And the radio of every node stays on
```

**Sources.** No numbers. sim.rs:75, :89 and :111 admit one proposal at a time under CE, so unit depth is a property of the control flow; runs.csv reports mean_Ct = 1.000000 with zero variance across all 45 CE rows because it cannot report anything else. Table~ref{tab:depth} therefore cannot 'confirm empirically to two decimal places' what the simulator constructs. SMALLEST-SPAN NOTE, decision 55: the changed words end mid-line at base 1900, so the remainder of that line is RE-SUPPLIED VERBATIM and not changed -- 'And the radio of every node stays on', whose predicate is base 1901 ('for the whole round and never sleeps, so $A_t = \Nnodes$'), outside the span. The leading 'and ' of base 1899 is likewise re-supplied, so the conjunction with base 1898 ('at most one proposal is in flight') survives. Both conditions of the paragraph therefore still arrive intact.

**Blocked:** no.

---

## 14. `paper/paper.tex` lines 1943-1954

Authorised by decisions 19, 36, 42, 44.

**Current text** (byte-exact, 12 lines):

```latex
The relationship between the two is instructively architecture-dependent.
Under \CE, strict sequentiality means that in practice no slot falls
outside the lifetime of some active proposal, so the two metrics coincide
and both reduce to $\Nnodes \cdot L$. Under \CI, the amortised metric is
systematically smaller than the cumulative one---for TOM, roughly 59
against 88---because it does not charge the decisions for the slots spent
filling the pipeline at the start of the run and draining it at the end.
\textbf{The gap between the two metrics under \CI{} is itself a measure of
the fixed overhead of the pipeline}, and it shrinks for larger workloads,
over which that overhead is amortised across more decisions. Under either
definition the relative ordering of the combinations is the same and the
qualitative conclusions of this paper are unaffected.
```

**Replacement text:**

```latex
The relationship between the two is instructively architecture-dependent.
Under \CE, strict sequentiality means that no slot falls outside the lifetime
of some active proposal, so the two coincide and both reduce to
$\Nnodes \cdot L$; this was verified on every one of the 4500 \CE{} decisions
measured. Under \CI{} the decomposition is smaller than the cumulative metric,
because it does not charge the decisions for the slots after the last one
commits. The gap is small and it is not a fixed overhead: $0.08\,\%$ of the
radio cost for TOM, $1.66\,\%$ for Paxos and $4.57\,\%$ for 2PC. All ratios
reported in this paper are cumulative, so no result depends on that gap.
```

**Sources.** f, energy share including orphans, ratio of sums, 15 seeds: runs.csv awake_outside_windows and decisions.csv amortised -> 0.00084857 / 0.01662420 / 0.04571172. The 4500 CE decisions: decisions.csv, amortised = 27 x latency exactly on every row. The deleted claim that the gap 'is itself a measure of the fixed overhead of the pipeline' and 'shrinks for larger workloads' is untestable here: num_proposals = 100 in all 2250 sweep rows. The deleted 'roughly 59 against 88' was one seed; the corrected pair is 86.07 against 88.00.

**Blocked:** no.

---

## 15. `paper/paper.tex` lines 1968-1971

Authorised by decisions 36, 42, 43, 51.

**Current text** (byte-exact, 4 lines):

```latex
Under the amortised criterion, the pipeline reduces the energy required
per final decision, relative to sequential execution of the same protocol
on the same workload, by a factor of about 5.4 for Paxos and about 8.2 for
2PC.
```

**Replacement text:**

```latex
Under the cumulative criterion, the pipeline reduces the energy required
per final decision, relative to sequential execution of the same protocol
on the same workload, by a factor of $3.83 \pm 0.08$ for Paxos and
$5.67 \pm 0.30$ for 2PC (95\,\% intervals over fifteen seeds).
```

**Sources.** runs.csv awake_tick/committed, ratio of means, 15 seeds: 3.827738 +- 0.075337 and 5.671896 +- 0.298615, jackknife 95 % at t(0.975,14) = 2.144787. Neither printed digit is resolved by its own interval ([3.7524, 3.9031] and [5.3733, 5.9705]); the interval is printed beside the value for that reason.

**Blocked:** no.

---

## 16. `paper/paper.tex` lines 1973-1983

Authorised by decisions 36, 41, 42, 43, 44, 48, 50.

**Current text** (byte-exact, 11 lines):

```latex
The ascending order of these ratios---about 2.1 for TOM, 5.4 for Paxos and
8.2 for 2PC---is informative in itself, and it tracks the depth column of
Table~\ref{tab:depth} exactly. The heavier the protocol and the longer its
waiting window, the more proposals accumulate in the pipeline
simultaneously and the larger the contribution of amortisation to the
saving. At the low end of that spectrum sits TOM with unit depth, where
amortisation contributes nothing at all and the 2.1-fold saving arises
\textbf{entirely from duty cycling}. The number 2.1 therefore marks the
floor of the saving offered by the \CI{} architecture---the part available
even in the complete absence of concurrency---and the distance from there
to 8.2 under 2PC is the additional contribution of amortisation.
```

**Replacement text:**

```latex
The ascending order of these ratios---$1.43 \pm 0.02$ for TOM, $3.83$ for
Paxos and $5.67$ for 2PC---is informative in itself. The heavier the protocol
and the longer its waiting window, the more slots each decision occupies and
the deeper the pipeline runs. At the low end of that spectrum sits TOM with
unit depth, where the $1.43$-fold saving arises \textbf{entirely from duty
cycling}: the measured radio duty cycle of $0.69$ predicts $1/0.69 = 1.443$,
which accounts for the measured ratio to within $0.6\,\%$. The number $1.43$
therefore marks the floor of the saving offered by the \CI{} architecture---the
part available even in the complete absence of concurrency. The rise from there
to $5.67$ under 2PC is not proposal sharing, which accounts for $1.6\,\%$ of
it; it is the number of slots a decision occupies, which runs from $4.70$ to
$6.18$ under \CI{} against $4.68$ to $24.34$ under \CE.
```

**Sources.** Triple as at 1968-1971, plus TOM 1.434823 +- 0.018025. Duty: runs.csv awake_tick/(27 x simulated_slots), ratio of sums, 0.692900 / 0.693253 / 0.694603, prints 0.69. Floor: 1/duty (ratio of sums) = 1.443210 against a measured 1.434823, +0.5845 %, and the two-factor product closes to 0.0 % exactly under that aggregation (addition8_closure.py). Sharing: 1/(1-f) = 1.047902 for 2PC; carrying TOM net of its own factor, (1.434823/1.000850) x 1.047901 = 1.502277, i.e. 0.067454 of a span of 4.237073 = 1.592 %; carrying it gross gives 1.503554 and 1.6221 %. Both print 1.6 %. Slots per decision, ratio of sums: CI 4.7033/5.3540/6.1705, CE 4.6760/14.2073/24.3353. DELETED: 'it tracks the depth column of Table~ref{tab:depth} exactly' -- false, the ratio rises 3.95x while depth rises 21.25x. DELETED: 'the distance from there to 8.2 is the additional contribution of amortisation' -- void, it describes the retired metric.

**Blocked:** no.

---

## 17. `paper/paper.tex` lines 2003-2009

Authorised by decisions 34, 38.

**Current text** (byte-exact, 7 lines):

```latex
The distributional view adds two further observations. First, Paxos and
2PC over \CE{} not only have higher means, their boxes sit at a height
entirely disjoint from the \CI{} family: the \emph{most} expensive
decision under \CI---including its outliers---is still cheaper than the
\emph{least} expensive decision under Paxos over \CE. TOM over \CE{}
occupies an intermediate position, its median near 127, above all three
\CI{} combinations but far below the two vote-based \CE{} protocols.
```

**Replacement text:**

```latex
The distributional view adds two further observations. First, the \CI{} and
the vote-based \CE{} families occupy separate regions of the cost axis: the
upper quartile of the pooled \CI{} decisions lies at 94.5 node-slots and the
lower quartile of Paxos over \CE{} at 351, a factor of $3.7$ apart with no
interquartile overlap, and the $99$th percentile of the pooled \CI{}
decisions, 269.9, still lies below the $1$st percentile of Paxos over \CE,
324.0. The extreme tails do meet---the most expensive \CI{} decision observed
costs 369.3 against 297.0 for the cheapest Paxos decision over \CE---so the
separation is a statement about the bulk of the distributions and not about
their extremes. TOM over \CE{} occupies an intermediate position, its median
decision costing 135 node-slots, above every \CI{} median and far below the
two vote-based \CE{} protocols; that median is exactly $\Nnodes$ times the
median \CE{} latency of 5 slots.
```

**Sources.** decisions.csv, 8984 decisions over 15 seeds pooled, n = 1500 per arm except 2PC-CI at 1484. Pooled CI q75 = 94.5111, Paxos-CE q25 = 351.0, ratio 3.7139. Pooled CI p99 = 269.8711, Paxos-CE p01 = 324.0, ratio 1.2006. Max pooled CI 369.29, min Paxos-CE 297.0. TOM-CE median 135.0 = 27 x 5. The 15-seed mean-based ceiling 27 x 4.676 = 126.25 is NOT compared against the median (charge 13).

**Blocked:** no.

---

## 18. `paper/paper.tex` lines 2011-2021

Authorised by decisions 34, 38, 39, 47.

**Current text** (byte-exact, 11 lines):

```latex
Second, the spread of 2PC over \CI{} is noticeably larger than that of the
other \CI{} combinations, with a wide interquartile range. This is not a
defect but a direct reflection of the amortisation mechanism. Proposals in
flight in the middle of the run, at peak pipeline saturation, divide their
cost among dozens of parallel transactions and end up very cheap---so much
so that the cheapest 2PC decisions under \CI{} cost less than the median
TOM decision under \CI---whereas proposals at the beginning and end of the
run, during fill and drain, find less concurrency to share with and end up
more expensive. The width of that box therefore traces the operating range
over which the pipeline is effective, and its upper outliers are the cost
of the transient phases.
```

**Replacement text:**

```latex
Second, the three \CI{} combinations are ordered by median cost---87.0 for
TOM, 89.0 for Paxos, 90.6 for 2PC---while their concurrency spans a factor of
twenty-one, and the cost of that concurrency lands in the upper tail rather
than in the box: the $99$th percentiles run 109.0, 269.5 and 334.5. The three
distributions interleave at the bottom, the $1$st percentile of 2PC over \CI{}
at 83.5 falling inside the interquartile range of TOM, and separate at the top.
Spread is not monotone in concurrency---Paxos carries eleven times TOM's
concurrency in a narrower interquartile range, 7.2 against 9.0---so it is the
median and the upper percentile, not the width of the box, that measure what
the pipeline costs. This is the decoupling in its per-decision form: mean
concurrency rises from 1.00 to 20.84 while the median cost of a decision rises
by $4.2\,\%$.
```

**Sources.** decisions.csv, 15 seeds pooled: medians 87.00/89.00/90.63, p99 109.00/269.51/334.51, IQR 9.00/7.17/20.73, 2PC p01 83.4752 against TOM q25 83.00 and q75 92.00. Mean C_t from runs.csv: 0.999206 / 11.482912 / 20.839135, ratio of means. Median rise 90.63/87.00 - 1 = 4.17 %. REPLACES the claim that the cheapest 2PC decisions cost less than the median TOM decision under CI: false on 15 seeds, 29.53 % of TOM decisions fall below 2PC's p01. The fill phase is deleted: the first proposal starts at slot 0.

**Blocked:** no.

---

## 19. `paper/paper.tex` lines 2028-2032

Authorised by decision 38.

**Current text** (byte-exact, 5 lines):

```latex
A frequency view of the same data brings out the multimodal structure of
the distribution: the bulk of the \CI{} decisions falls in the cheapest
bins, below 100; TOM over \CE{} sits coherently between 100 and 150; and
Paxos and 2PC over \CE{} lie entirely in the expensive bins above 300,
with no overlap at all with the \CI{} family.
```

**Replacement text:**

```latex
A frequency view of the same data brings out the multimodal structure of
the distribution: the bulk of the \CI{} decisions falls in the cheapest
bins, below 100; TOM over \CE{} sits coherently between 100 and 150; and
Paxos and 2PC over \CE{} lie in the expensive bins above 300, with less than
$1\,\%$ of the \CI{} family overlapping them.
```

**Sources.** decisions.csv, 15 seeds: pooled CI p99 = 269.87 < 300, so under 1 % of CI decisions exceed 300; the pooled CI maximum is 369.29, so 'no overlap at all' is false. TOM-CE p01 = 108.0 and p99 = 162.0, so 'between 100 and 150' is loose at the top; left as approximate prose.

**Blocked:** no.

---

## 20. `paper/paper.tex` lines 2063-2064

Authorised by decisions 36, 38.

**Current text** (byte-exact, 2 lines):

```latex
energy ceiling of the baseline. Energy values use the amortised metric of
Equation~\eqref{eq:amortized}.}
```

**Replacement text:**

```latex
energy ceiling of the baseline. Energy is cumulative per-decision energy
averaged over fifteen seeds.}
```

**Sources.** No new numbers: this is the caption of the table whose cells the entry at 2075-2077 rebases. RE-SUPPLIED VERBATIM, not changed: 'energy ceiling of the baseline.' from base 2063. CHANGED: 'Energy values use the amortised metric of Equation~\eqref{eq:amortized}.' -> the cumulative metric and the seed count. No equation reference is used: the file defines only eq:round, eq:ece, eq:depth and eq:amortized, and the cumulative metric's equation arrives with the blocked Section F rewrite, so a reference here would dangle.

**Blocked:** no.

---

## 21. `paper/paper.tex` lines 2075-2077

Authorised by decisions 9, 19, 36, 42.

**Current text** (byte-exact, 3 lines):

```latex
TOM (\CI)   & 4.7   & $\approx 59$ & 127  & $\approx 2\times$ \\
Paxos (\CI) & 61.4  & $\approx 69$ & 1658 & $\approx 24\times$ \\
2PC (\CI)   & 357.7 & $\approx 78$ & 9658 & $\approx 124\times$ \\
```

**Replacement text:**

```latex
TOM (\CI)   & 4.7   & 88.0  & 127  & $1.4\times$ \\
Paxos (\CI) & 61.4  & 100.2 & 1658 & $16.5\times$ \\
2PC (\CI)   & 126.8 & 115.8 & 3424 & $29.6\times$ \\
```

**Sources.** sweep_summary.csv, N=27 random loss 0.05, 15 seeds: avg_latency 4.699/61.394/126.822; cumulative (listen+flood)/committed 87.99/100.22/115.84; ceiling 27 x L = 126.9/1657.6/3424.2; escape ceiling/E = 1.44/16.54/29.56. The table now uses the cumulative metric throughout, which the caption must state; the published column was amortised and seed-99.

**Blocked:** no.

---

## 22. `paper/paper.tex` lines 2082-2084

Authorised by decisions 9, 36, 42.

**Current text** (byte-exact, 3 lines):

```latex
The central observation is that between TOM and 2PC over \CI{} the latency
column grows by roughly \textbf{76 times} while the amortised energy
column grows by only about \textbf{1.3 times}. In the pipelined
```

**Replacement text:**

```latex
The central observation is that between TOM and 2PC over \CI{} the latency
column grows by roughly \textbf{27 times} while the energy
column grows by only about \textbf{1.3 times}. In the pipelined
```

**Sources.** 27x: sweep_summary.csv avg_latency, random, N=27, loss 0.05, 15 seeds, 126.822/4.699 = 26.987, ratio of means. 1.3x: runs.csv cumulative_per_dec, 15 seeds, 115.84/87.99 = 1.317. This is the SECOND 76x site; the first is at 317 (entry 4). 'amortised' is deleted because tab:escape above it is rebased on the cumulative metric by the entry at 2075-2077.

**Blocked:** no.

---

## 23. `paper/paper.tex` lines 2086-2092

Authorised by decisions 9, 42, 44.

**Current text** (byte-exact, 7 lines):

```latex
\textbf{independent of latency}. 2PC over \CI{} is the extreme case: it
sits at the far right of the plane, with a latency approaching four
hundred slots, yet its energy per decision remains at the level of TOM,
the lightest protocol in the system. The reason has already been
quantified: the high latency of 2PC over \CI{} is not slowness but the
fact that each decision spent that entire interval in flight alongside
some sixty others, sharing the radio cost of every slot with them.
```

**Replacement text:**

```latex
\textbf{independent of latency}. 2PC over \CI{} is the extreme case: it
sits at the far right of the plane, with a latency of about one hundred and
thirty slots, yet its energy per decision remains at the level of TOM,
the lightest protocol in the system. The reason has already been
quantified: the high latency of 2PC over \CI{} is not slowness but the
fact that each decision spent that entire interval in flight alongside
some twenty others, sharing the radio cost of every slot with them.
```

**Sources.** latency 126.822 and depth 21.2547, both 15 seeds, as at 1438 and 1811-1813. 'approaching four hundred slots' predates the decision-9 fix.

**Blocked:** no.

---

## 24. `paper/paper.tex` lines 2190-2197

Authorised by decisions 36, 42, 44.

**Current text** (byte-exact, 8 lines):

```latex
One remark on the energy metric is needed before the results. This
subsection uses the \emph{cumulative} metric of
Section~\ref{sec:results-energy}, the same quantity reported in
Table~\ref{tab:baseline}. The ratios quoted earlier were based on the
\emph{amortised} metric of Equation~\eqref{eq:amortized} and are therefore
larger. As established there, the two metrics coincide under \CE{} and
differ under \CI{} by the fixed overhead of the pipeline; the relative
ordering of the combinations is the same under either.
```

**Replacement text:**

```latex
One remark on the energy metric is needed before the results. Every energy
ratio in this paper, here and above, is the \emph{cumulative} metric of
Section~\ref{sec:results-energy}, the same quantity reported in
Table~\ref{tab:baseline}. The per-decision decomposition of
Equation~\eqref{eq:amortized} is used only for the per-decision
distributions of Section~\ref{sec:results-energy}; it is smaller than the cumulative
metric by $0.08\,\%$ for TOM, $1.66\,\%$ for Paxos and $4.57\,\%$ for 2PC,
and no ratio reported anywhere in this paper is corrected by it.
```

**Sources.** f as at 1943-1954. The deleted sentence said the ratios quoted earlier 'were based on the amortised metric and are therefore larger'; after decision 36 that is no longer true of any ratio in the paper.

**Blocked:** no.

---

## 25. `paper/paper.tex` lines 2292-2298

Authorised by decision 32.

**Current text** (byte-exact, 7 lines):

```latex
Equation~\eqref{eq:ece} claims that under \CE{} the energy of a decision
is exactly the product of the network size and the latency of that
decision. So far that claim has been tested on one topology.
Table~\ref{tab:identity} now confronts it with fifteen independent
cases---three \CE{} protocols on five topologies---across which the
diameter varies by a factor of twenty-six and the energy per decision by
more than a factor of forty.
```

**Replacement text:**

```latex
Equation~\eqref{eq:ece} claims that under \CE{} the energy of a decision
is exactly the product of the network size and the latency of that
decision. The claim is not open to measurement error: if the radio never
sleeps, each of the $\Nnodes$ nodes is awake in each of the $L$ slots a
decision occupies, so the product is what the accounting computes. What can be
checked is the instrument, and it holds throughout the topology space---three
\CE{} protocols on five topologies, a twenty-six-fold range of diameter and a
forty-fold range of energy per decision.
```

**Sources.** sweep_summary.csv: the sleep counter is exactly zero in all 1125 CE rows; diameter 1 to 26 across the five topologies; CE energy per decision spans 126.3 to 5136.5 node-slots, a factor of 40.7. Deletes the reference to tab:identity, which the following entry removes.

**Blocked:** no.

---

## 26. `paper/paper.tex` lines 2300-2338

Authorised by decisions 32, 37.

**Current text** (byte-exact, 39 lines):

```latex
\begin{table*}[!t]
\caption{Validation of the identity $\Ece = \Nnodes L$ across the topology
space ($\Nnodes = 27$ throughout, 5\,\% loss, 100 proposals, fifteen
seeds). Latency and energy are per decision and are reported in slots and
in node-slots of radio-on time respectively; the two are measured
independently, $L$ from the slot counter and $\Ece$ from the per-node radio
state log. Diameters are the modal values of the generated instances
(Table~\ref{tab:topologies}).}
\label{tab:identity}
\centering
\small
\begin{tabular}{@{}lclrrrr@{}}
\toprule
\textbf{Topology} & \textbf{Diameter} & \textbf{Protocol} &
\textbf{Latency $L$} & \textbf{Predicted $\Nnodes L$} &
\textbf{Measured $\Ece$} & \textbf{Error} \\
\midrule
Full mesh    & 1  & TOM   & 2.738   & 73.926   & 73.926   & $<10^{-12}$ \\
             &    & Paxos & 15.277  & 412.470  & 412.470  & $<10^{-12}$ \\
             &    & 2PC   & 30.899  & 834.264  & 834.264  & $<10^{-12}$ \\
\addlinespace
Partial mesh & 3  & TOM   & 3.406   & 91.962   & 91.962   & $<10^{-12}$ \\
             &    & Paxos & 12.499  & 337.482  & 337.482  & $<10^{-12}$ \\
             &    & 2PC   & 23.225  & 627.066  & 627.066  & $<10^{-12}$ \\
\addlinespace
Random       & 4  & TOM   & 4.676   & 126.252  & 126.252  & $<10^{-12}$ \\
             &    & Paxos & 14.207  & 383.598  & 383.598  & $<10^{-12}$ \\
             &    & 2PC   & 24.335  & 657.054  & 657.054  & $<10^{-12}$ \\
\addlinespace
Scale-free   & 4  & TOM   & 4.614   & 124.578  & 124.578  & $<10^{-12}$ \\
             &    & Paxos & 15.899  & 429.282  & 429.282  & $<10^{-12}$ \\
             &    & 2PC   & 33.315  & 899.496  & 899.496  & $<10^{-12}$ \\
\addlinespace
Line         & 26 & TOM   & 108.001 & 2916.018 & 2916.018 & $<10^{-12}$ \\
             &    & Paxos & 114.409 & 3089.034 & 3089.034 & $<10^{-12}$ \\
             &    & 2PC   & 266.331 & 7190.926 & 7190.926 & $<10^{-12}$ \\
\bottomrule
\end{tabular}
\end{table*}
```

**Replacement text:**

```latex
The check is on the instrument rather than on the arithmetic: the per-node
radio counters sum to $\Nnodes$ times the slots ticked in all $2250$ runs of
the study, and measured energy per decision agrees with $\Nnodes \cdot L$ to
the last bit the simulator represents. The identity is moreover visible per
decision and not only in aggregate: every one of the $4500$ \CE{} per-decision
energies measured at the reference point is an integer multiple of $\Nnodes$,
so the \CE{} per-decision energy distribution is the latency distribution
rescaled by $\Nnodes$. No \CI{} arm has that property---the per-decision
energies of Paxos and 2PC over \CI{} are not integers at all, because a slot
shared between $k$ decisions contributes $1/k$ to each.
```

**Sources.** sweep_summary.csv: (listen+flood+sleep) = 27 x simulated slots on all 2250 rows. runs.csv: awake/committed against 27 x avg_latency agrees to 2.2e-16 on all 45 CE rows. decisions.csv: all 4500 CE amortised values are integer multiples of 27; TOM-CI values are integers but not multiples of 27; Paxos-CI and 2PC-CI are fractional. DELETES the fifteen-row table float: its error column was zero by construction in all fifteen rows, so it assumed the identity it reported as verified. No surviving \ref to tab:identity remains after this entry and the preceding one.

**Blocked:** no.

---

## 27. `paper/paper.tex` lines 2340-2356

Authorised by decisions 10, 32, 42, 49.

**Current text** (byte-exact, 17 lines):

```latex
The two independently measured quantities agree in all fifteen cases to the
full precision the simulator records. Exactness here is expected rather than
surprising, and that is the point: if the radio never sleeps, each of the
$\Nnodes$ nodes is awake in each of the $L$ slots that a decision occupies, so
the identity is a property of the architecture and the table is a check that
the energy accounting contains no leak anywhere in the space. What the check
licenses is the stronger reading. It establishes $\Ece = \Nnodes L$ as a
\textbf{structural law} of the \CE{} architecture: as long as the
communication mechanism is sequential and the radio never sleeps, the energy
of a decision is locked to its latency regardless of the structure of the
network, and the designer has no lever at all---neither a better topology nor
a different protocol---with which to break that coupling. Every departure
from the law is then attributable to sleep alone, and the size of the
departure measures what pipelining buys: under \CI{} the same accounting
falls short of $\Nnodes L$ by between 22 and 31\,\% on the dense topologies,
which is exactly the fraction of node-slots those protocols spend with the
radio off.
```

**Replacement text:**

```latex
What the check licenses is the stronger reading. It establishes
$\Ece = \Nnodes L$ as a \textbf{structural law} of the \CE{} architecture: as
long as the communication mechanism is sequential and the radio never sleeps,
the energy of a decision is locked to its latency regardless of the structure
of the network, and the designer has no lever at all---neither a better
topology nor a different protocol---with which to break that coupling. Every
departure from the law is then attributable to sleep alone, and the size of the
departure measures what pipelining buys: under \CI{} the same accounting
falls short of $\Nnodes L$ by between 22 and 31\,\% on the dense topologies,
which is exactly the fraction of node-slots those protocols spend with the
radio off. The one departure visible in the \CE{} measurements themselves is
not energy at all: where a configuration leaves a proposal uncommitted, energy
per decision exceeds $\Nnodes \bar{L}$ by $1/d - 1$, where $d$ is the measured
pipeline depth. That residual is zero to machine precision in fourteen of the
fifteen groups and reaches $1.94\,\%$ on a single seed of 2PC over \CE{} on the
line topology, where two of the fifteen seeds commit 99 proposals of 100.
```

**Sources.** Shortfall, ratio of sums per topology, 15 seeds: partial_mesh 22.66-23.05 %, full_mesh 26.19-26.33 %, scale_free 28.20-28.43 %, random 30.54-30.71 %, so '22 and 31' stands. Residual: 1/depth - 1 on the topology sweep, zero to machine precision in 14 of 15 groups; line/2PC-CE group mean 0.257653 % (mean of per-seed residuals), worst single seed 37 at 1.936210 %, 13 of 15 seeds committing 100. The printed 1.94 % is the WORST SEED and is named as such; the group mean 0.26 % is not printed. Formula is 1/d - 1, not 'the reciprocal of the depth'.

**Blocked:** no.

---

## 28. `paper/paper.tex` lines 2371-2374

Authorised by decisions 9, 42.

**Current text** (byte-exact, 4 lines):

```latex
factor of four and throughput by a factor of about 1.7, yet
\textbf{the pipeline depth remains effectively unchanged}: TOM over \CI{}
stays at unity, Paxos over \CI{} at about 11.7 and 2PC over \CI{} at about
sixty in every case.
```

**Replacement text:**

```latex
factor of four and throughput by a factor of about 1.7, yet
\textbf{the pipeline depth remains effectively unchanged}: TOM over \CI{}
stays at unity, Paxos over \CI{} at about 11.6 and 2PC over \CI{} at about
twenty-one in every case.
```

**Sources.** sweep_summary.csv, depth = (committed/end_slot) x avg_latency, 15 seeds per group: TOM 1.000/1.000/1.000/1.002 on full_mesh/partial_mesh/random/scale_free; Paxos 11.589/11.623/11.662/11.657; 2PC 21.446/21.455/21.255/20.954. The invariance claim strengthens under the fix. Base line 2370 ('subsection. Across the four dense topologies the diameter varies by a') is context only and is NOT part of this span or of the replacement.

**Blocked:** no.

---

## 29. `paper/paper.tex` line 2431

Authorised by decision 9.

**Current text** (byte-exact, 1 line):

```latex
2PC (\CI)   & 0.1682 & $+0.1$\,\%  & 350.0 & $-2.2$\,\%  \\
```

**Replacement text:**

```latex
2PC (\CI)   & 0.1682 & $+0.1$\,\%  & 124.7 & $-1.6$\,\%  \\
```

**Sources.** sweep_summary.csv, random vs scale_free, N=27 loss 0.05, 15 seeds: throughput 0.1681 -> 0.1682 (+0.08 %), avg_latency 126.82 -> 124.74 (-1.64 %). The published 350.0 and -2.2 % predate the decision-9 fix. Every other row of the table was reproduced exactly.

**Blocked:** no.

---

## 30. `paper/paper.tex` lines 2565-2568

Authorised by decisions 18, 42, 43, 44.

**Current text** (byte-exact, 4 lines):

```latex
The underlying mechanism was quantified by Little's law: the pipeline
holds about twelve proposals in flight under Paxos and about sixty under
2PC, while all three \CE{} protocols are confined to unit depth. That
concurrency, together with the ability to sleep the radio, reduces the
```

**Replacement text:**

```latex
The underlying mechanism was quantified by Little's law: the pipeline
holds about twelve proposals in flight under Paxos and about twenty-one under
2PC, while all three \CE{} protocols are confined to unit depth. That
concurrency, together with the ability to sleep the radio, reduces the
```

**Sources.** depth: runs.csv, 15 seeds, ratio of means -> 11.661524 +- 0.015311 and 21.254664 +- 0.218137. Unit depth under CE is structural, not measured (sim.rs:75, :89, :111). The span stops at 2568 so that 'reduces the' keeps its object at 2569 ('energy per decision substantially'); base 2564 is blank and stays.

**Blocked:** no.

---

## 31. `paper/paper.tex` lines 2573-2577

Authorised by decisions 32, 37.

**Current text** (byte-exact, 5 lines):

```latex
The generalisation study shows that these results do not depend on a
particular network. The identity $\Ece = \Nnodes L$ holds to better than
1.5\,\% in fifteen independent cases spanning a twenty-six-fold range of
diameter, and the pipeline depth is effectively constant across the four
dense topologies, so the mechanism that produces the energy saving is
```

**Replacement text:**

```latex
The generalisation study shows that these results do not depend on a
particular network. The identity $\Ece = \Nnodes L$ holds exactly in fifteen
independent cases spanning a twenty-six-fold range of
diameter, and the pipeline depth is effectively constant across the four
dense topologies, so the mechanism that produces the energy saving is
```

**Sources.** As at 2292-2338: no error band exists to quote, because the residual is 1/depth - 1. sweep_summary.csv, 1125 CE rows, sleep = 0 throughout. The span ends at 2577 so that 'is' keeps its complement at 2578 ('architectural rather than topological').

**Blocked:** no.

---

## 32. `paper/paper.tex` lines 2617-2620

Authorised by decision 42.

**Current text** (byte-exact, 4 lines):

```latex
The evaluation carries three messages. First, the pipeline produces real
and measurable concurrency---on average twelve simultaneous proposals for
Paxos and sixty for 2PC---and that concurrency raises throughput by up to
a factor of four and shortens workload completion by a larger factor
```

**Replacement text:**

```latex
The evaluation carries three messages. First, the pipeline produces real
and measurable concurrency---on average twelve simultaneous proposals for
Paxos and twenty-one for 2PC---and that concurrency raises throughput by up to
a factor of four and shortens workload completion by a larger factor
```

**Sources.** depth as at 1811-1813, runs.csv, 15 seeds, ratio of means. Throughput 0.1681/0.0412 = 4.08x, sweep_summary.csv, random, 15 seeds. Base 2621 ('still, relative to the strongest baseline competitor. Second, under \CE{}') is context only: it is NOT in this span and NOT in the replacement, so 'a larger factor' keeps its continuation.

**Blocked:** no.

---

# Blocked entries — no numbers, do not apply

These carry no replacement text, per the rule that no entry may appear whose
numbers are not final.

## B1. 1316 and 407

**What is blocked.** the $0.4\,\%$ radio duty cycle at $99.9\,\%$ PDR taken from BlueFlood as a calibration target

**Why.** The simulator's measured CI duty cycle is 0.69 at the reference point, three orders of magnitude away, and it has no packet delivery ratio instrumentation at all. Both sites move together only once the calibration of steps 2 to 5 is performed; neither number is derivable from anything measured so far.

## B2. 1329-1330

**What is blocked.** \TBD{A2 error} and \TBD{WPaxos error}

**Why.** Blind predictions, pending the frozen calibration. The simulator additionally has no real-time unit: Slot is a u64 with no T_slot, so a 475 ms or 289 ms target cannot yet be expressed. Line numbers read from the file, not recalled: an earlier draft of this list cited 1323-1324, which is wrong.

## B3. 1343

**What is blocked.** \TBD{any regime in which it does not}, the third and last \TBD in the file

**Why.** This is the step 6 sensitivity sweep. Two of its three axes cannot yet move the simulator: Slot is a u64 with no T_slot, so a +-50 % perturbation of slot duration changes nothing, and there is no correlated loss process to substitute for the independent one. Only \Nretx (flood_repeats) is sweepable today. The one regime already found -- the line topology, where 2PC over CI is not competitive -- is described in the surrounding prose and does not need this macro; the macro cannot be resolved until the missing axes exist.

## B4. the caption of the boxplot float around 1995-2001

**What is blocked.** the figure caption naming the metric, the whisker convention and the per-arm n

**Why.** The float is commented out in the manuscript. The figure itself exists at plots/energy/energy_boxplot_15seed.pdf and its caption text is settled -- box = q25/q75, whiskers = p1/p99, points are the outer 1 % on each side, n = 1500 per arm except 2PC over CI at 1484, and the paper's headline ratios are cumulative -- but the lines to patch do not exist until the float is uncommented.

## B5. 1470-1478 and the surrounding commit-rate prose

**What is blocked.** the 98.9 % commit rate discussion, and the zero-commit rows of the topology and scalability tables

**Why.** Decision 12's artefact-level treatment and decision 10's conditional-mean reporting are settled in principle, but the affected figures have not been regenerated, so the replacement cells are not final. 28 of 225 scalability runs commit fewer than 100, all 2PC over CI, one of them zero at N = 188.

