#!/usr/bin/env python3
"""Generate docs/validation/patch_spec.md.

Decision 31/35: the agent does not write to paper/paper.tex. This emits a
specification the author applies. Every "current text" block is sliced out of
paper/paper.tex by line number. Byte-exactness of those blocks is therefore an
INVARIANT of this script and not something it verifies: a generator cannot be
its own verifier (decision 88). The independent recomputation of every number
lives in the companion script, check_patch_spec.py.

Run from the repository root:
    ./venv/bin/python docs/validation/addition7/scripts/make_patch_spec.py
"""
import hashlib
import os
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                      text=True, check=True).stdout.strip()
TEX = os.path.join(ROOT, "paper", "paper.tex")
OUT = os.path.join(ROOT, "docs", "validation", "patch_spec.md")
RAW = open(TEX, "rb").read()
SHA = hashlib.sha256(RAW).hexdigest()
LINES = RAW.decode("utf-8").split("\n")
# Decision 87: split("\n") on a file that ends with a newline yields a final ''
# which is not a line. The spec header used len(LINES) and so advertised
# "2701 lines" for a 2700-line file. Count content lines explicitly.
N_BASE = len(LINES) - (1 if LINES and LINES[-1] == "" else 0)
# --------------------------------------------------------------------------
# SUPERSEDED by make_patch_spec_v3.py. Kept, not deleted (decision
# 155): it is the generator of record for the v1/v2 spec numbers that
# earlier rounds already cite. Do not run it to produce a new spec.
# RETIRED 2026-09-06 (decision 147). This script is PINNED to the
# pre-patch manuscript: paper/paper.tex, 2700 lines, sha256 039118e9...
# That file no longer exists on main. Since PR #4 (merge commit
# 2804f21a) the manuscript is blob f7592bab..., sha256 7eaa4fd9...,
# 2684 lines, so the base assertion below MUST fail on main and every
# line anchor in this file is dead. That failure is the designed
# behaviour, not a bug. To reproduce the patch_spec claims, check out
# the tag tools-base-039118e9 first. Do not re-anchor this file: the
# next round of manuscript edits starts from the new base (decision
# 148). check_patch_spec.py is NOT pinned and still runs on main.
# --------------------------------------------------------------------------
BASE_SHA = "039118e9c14c5f7a0f8e324e0957535b87ca9899befa1384547930e1ce694c27"


def cur(a, b):
    """Byte-exact slice of paper.tex, lines a..b inclusive, 1-indexed.

    INVARIANT, not a check: the slice is taken from the file, so it cannot
    disagree with the file. Never report this as verification (decision 88).
    """
    return "\n".join(LINES[a - 1:b])


# Each entry: (a, b, replacement, sources, decisions, blocked_on)
# `sources` names file, column and seed count for every number in `replacement`.
E = []


def add(a, b, repl, sources, decisions, blocked=None):
    E.append({"a": a, "b": b, "repl": repl, "src": sources, "dec": decisions,
              "blocked": blocked})


# ---------------------------------------------------------------- 83 preamble
add(83, 83,
    """\\newcommand{\\ReLI}{ReLI}                  % protocol name, kept upright
\\newcommand{\\Send}{S_{\\mathrm{end}}}      % slot of the last commit
\\newcommand{\\Ssim}{S_{\\mathrm{sim}}}      % total slots ticked""",
    "No numbers. Required by the entry at 1244-1251, which distinguishes the "
    "two run lengths; neither macro is defined in the file today.",
    "33")

# ---------------------------------------------------------------- 159-161 abstract
add(159, 161,
    """pipeline sustains, on average, about 12 concurrent proposals for Paxos and
about 21 for 2PC, yielding up to 4x higher throughput and up to 5.7x better
per-decision energy efficiency than CE-based counterparts. We""",
    "depth: runs.csv, committed/end_slot x avg_latency, 15 seeds -> 11.6615 and "
    "21.2547. Ratio: runs.csv awake_tick/committed, ratio of means, 15 seeds -> "
    "5.671896 +- 0.298615 (jackknife 95 %). 'amortized' deleted: decision 36 "
    "prints the cumulative metric only.",
    "36, 42, 44")

# ---------------------------------------------------------------- 162-164 abstract identity
add(162, 164,
    """further show that CE architectures obey a structural identity that locks
per-decision energy to per-decision latency, exactly and by construction, and
that pipelining breaks this""",
    "No measured error band exists to quote: the residual is 1/depth - 1, an "
    "arithmetic restatement of the commit rate, and it is zero in every fully "
    "committing configuration. Instrumented check: runs.csv sleep = 0 on all 45 "
    "CE rows; awake/committed against 27 x avg_latency agrees to 2.2e-16.",
    "32")

# ---------------------------------------------------------------- 310-319 intro
add(310, 319,
    """simulator, we find that the pipeline sustains about 12 concurrent proposals
for Paxos and about 21 for 2PC, that this concurrency yields up to
$4\\times$ higher throughput and up to $5.7\\times$ better
per-decision energy, and---most importantly---that \\CE{} architectures obey
the identity $\\Ece = \\Nnodes L$, which holds exactly and by construction
across fifteen independent measurements spanning a $26\\times$ range of network
diameters. Pipelining breaks that identity: across our \\CI{} configurations,
per-decision latency varies by roughly $27\\times$ while per-decision energy
varies by only about $1.3\\times$. Latency stops being a proxy for energy
and becomes a variable a designer can deliberately spend.""",
    "depth and ratio as at 159-161. 27x: sweep_summary.csv avg_latency, "
    "126.822/4.699 = 26.987, 15 seeds, ratio of means, topology 'random'. 1.3x: "
    "runs.csv cumulative_per_dec 115.84/87.99 = 1.317, 15 seeds, so the printed "
    "1.3 survives the metric change.",
    "32, 36, 42, 44")

# ---------------------------------------------------------------- 542-543
add(542, 543,
    """Section~\\ref{sec:results} reports the resulting depth: approximately 12
concurrent proposals for Paxos and 21 for 2PC.""",
    "depth: runs.csv, 15 seeds -> 11.6615 +- 0.0153 and 21.2547 +- 0.2181.",
    "42")

# ---------------------------------------------------------------- 1244-1251 decision 33
add(1244, 1251,
    """\\item \\textbf{Awake slots.} The total number of slots in which a node's
radio was transmitting, receiving or listening. In low-power wireless,
radio-on time is the dominant contributor to energy consumption, and the
distribution of this quantity across nodes indicates how evenly that cost
is borne. Two run lengths must be distinguished, because they differ whenever
the pipeline drains. $\\Send$ is the slot at which the last decision commits,
and throughput and pipeline depth are per $\\Send$; $\\Ssim$ is the total number
of slots ticked, and energy is per $\\Ssim$. Under \\CE{} the two coincide in
every measurement reported here. Under \\CI{} they differ by the drain tail,
by $0.09\\,\\%$ for TOM, $1.70\\,\\%$ for Paxos and $3.41\\,\\%$ for 2PC at the
reference point, reaching $23.4\\,\\%$ on a single seed.""",
    "runs.csv, simulated_slots and end_slot, 15 seeds, ratio of sums: "
    "sum(S)/sum(end_slot) - 1 = 0.000851 / 0.016968 / 0.034105. Worst single "
    "seed: 2PC seed 7 at 1.2344, i.e. 23.44 %. S = end_slot on all 45 CE rows. "
    "Requires the \\Send and \\Ssim macros added by the entry at line 83.",
    "33, 42")

# ---------------------------------------------------------------- 1296-1298
add(1296, 1298,
    """the identity $\\Ece = \\Nnodes \\cdot \\Lround$ of
Equation~\\eqref{eq:ece}, which Section~\\ref{sec:results} confirms exactly
across fifteen configurations; per-node radio state""",
    "As at 162-164: no error band. sweep_summary.csv, 45 CE rows, sleep = 0 and "
    "listen+flood = 27 x simulated_slots exactly.",
    "32")

# ---------------------------------------------------------------- 1438 table III
add(1438, 1438,
    "2PC (\\CI)   & 98.9  & 0.1681 & 126.8 & 115.8 & 1.463 & 5034 \\\\",
    "sweep_summary.csv avg_latency, N=27 random loss 0.05, 15 seeds, mean "
    "126.822. The published 357.71 predates the decision-9 tx_starts fix "
    "(commit 629a0cd). Every other cell in the row is unchanged and was "
    "reproduced exactly.",
    "9")

# ---------------------------------------------------------------- 1458-1462
add(1458, 1462,
    """For the vote-based protocols the pattern differs. The \\CI{} variants are
far ahead on throughput and efficiency despite latencies several times
higher: 2PC over \\CI{} takes 126.8 slots per decision against 24.3 for
its \\CE{} counterpart, yet delivers more than four times the throughput
and more than twenty times the efficiency. The commit-rate column shows""",
    "As at 1438. 'several times higher' and the 4x and 20x claims all survive: "
    "126.822/24.335 = 5.21x, throughput 0.1681/0.0412 = 4.08x, efficiency "
    "1.463/0.063 = 23.2x, all 15 seeds.",
    "9")

# ---------------------------------------------------------------- 1811-1813 tab:depth
add(1811, 1813,
    """TOM (\\CI)   & 0.2132 & 4.7   & 1.00 \\\\
Paxos (\\CI) & 0.1903 & 61.4  & 11.66 \\\\
2PC (\\CI)   & 0.1681 & 126.8 & 21.25 \\\\""",
    "runs.csv, 15 seeds: depth 1.000000 +- 0.000000, 11.661524 +- 0.015311, "
    "21.254664 +- 0.218137 (jackknife 95 %). Latency from sweep_summary.csv. "
    "TOM and Paxos throughput and latency unchanged.",
    "9, 42, 43")

# ---------------------------------------------------------------- 1825-1833
add(1825, 1833,
    """Second, the informal claim of overlap becomes a specific number: Paxos
over \\CI{} keeps about twelve proposals in flight on average and 2PC over
\\CI{} about twenty-one. This is precisely how 2PC over \\CI{} sustains a
throughput of 0.168 decisions per slot while each individual decision
takes 127 slots---the high latency is not slowness but the consequence of
each decision spending most of its life alongside dozens of others. It
also explains why 2PC runs deeper than Paxos: the longer waiting window
imposed by unanimity accumulates more proposals in the system
simultaneously.""",
    "depth as at 1811-1813; latency as at 1438. The mechanism sentence is "
    "unchanged and is confirmed structurally: two_pc_pipeline.rs:131 holds a "
    "transaction pending exactly num_nodes rounds, so max C_t = "
    "min(N, num_proposals) on all 75 2PC runs of charge14_maxCt.csv.",
    "9, 42")

# ---------------------------------------------------------------- 1875-1881 decision 36
add(1875, 1881,
    """A fair accounting of energy under high offered load must take into account
that in the pipelined architecture several decisions are in flight at
once, as Table~\\ref{tab:depth} has just quantified. Alongside the cumulative
metric we therefore also decompose the radio cost across the decisions that
were in flight when it was incurred. This decomposition is not the basis of
any ratio reported in this paper; it exists to give the per-decision
\\emph{distributions} below. For each
successful proposal $i$ with lifetime $[s_i, e_i)$,""",
    "No numbers. The deleted sentence ('a slot of radio activity that "
    "simultaneously serves sixty proposals must not be charged sixty times at "
    "full cost') is the justification for the amortised metric, which decision "
    "36 retires; and its 'sixty' is 21.25 on 15 seeds. The cross-reference is "
    "to sec:results-energy, the only label in that section; if the "
    "distributional subsubsection at 2001 is given its own label, point it "
    "there instead.",
    "36, 44")

# ---------------------------------------------------------------- 1943-1954
add(1943, 1954,
    """The relationship between the two is instructively architecture-dependent.
Under \\CE, strict sequentiality means that no slot falls outside the lifetime
of some active proposal, so the two coincide and both reduce to
$\\Nnodes \\cdot L$; this was verified on every one of the 4500 \\CE{} decisions
measured. Under \\CI{} the decomposition is smaller than the cumulative metric,
because it does not charge the decisions for the slots after the last one
commits. The gap is small and it is not a fixed overhead: $0.08\\,\\%$ of the
radio cost for TOM, $1.66\\,\\%$ for Paxos and $4.57\\,\\%$ for 2PC. All ratios
reported in this paper are cumulative, so no result depends on that gap.""",
    "f, energy share including orphans, ratio of sums, 15 seeds: runs.csv "
    "awake_outside_windows and decisions.csv amortised -> 0.00084857 / "
    "0.01662420 / 0.04571172. The 4500 CE decisions: decisions.csv, amortised "
    "= 27 x latency exactly on every row. The deleted claim that the gap 'is "
    "itself a measure of the fixed overhead of the pipeline' and 'shrinks for "
    "larger workloads' is untestable here: num_proposals = 100 in all 2250 "
    "sweep rows. The deleted 'roughly 59 against 88' was one seed; the "
    "corrected pair is 86.07 against 88.00.",
    "19, 36, 42, 44")

# ------------------------------------------------------------- 1968-1971
# Split so blank base line 1972 survives: two paragraphs, two entries.
add(1968, 1971,
    """Under the cumulative criterion, the pipeline reduces the energy required
per final decision, relative to sequential execution of the same protocol
on the same workload, by a factor of $3.83 \\pm 0.08$ for Paxos and
$5.67 \\pm 0.30$ for 2PC (95\\,\\% intervals over fifteen seeds).""",
    "runs.csv awake_tick/committed, ratio of means, 15 seeds: 3.827738 +- "
    "0.075337 and 5.671896 +- 0.298615, jackknife 95 % at t(0.975,14) = "
    "2.144787. Neither printed digit is resolved by its own interval "
    "([3.7524, 3.9031] and [5.3733, 5.9705]); the interval is printed beside "
    "the value for that reason.",
    "36, 42, 43, 51")

# ------------------------------------------------------------- 1973-1983
add(1973, 1983,
    """The ascending order of these ratios---$1.43 \\pm 0.02$ for TOM, $3.83$ for
Paxos and $5.67$ for 2PC---is informative in itself. The heavier the protocol
and the longer its waiting window, the more slots each decision occupies and
the deeper the pipeline runs. At the low end of that spectrum sits TOM with
unit depth, where the $1.43$-fold saving arises \\textbf{entirely from duty
cycling}: the measured radio duty cycle of $0.69$ predicts $1/0.69 = 1.443$,
which accounts for the measured ratio to within $0.6\\,\\%$. The number $1.43$
therefore marks the floor of the saving offered by the \\CI{} architecture---the
part available even in the complete absence of concurrency. The rise from there
to $5.67$ under 2PC is not proposal sharing, which accounts for $1.6\\,\\%$ of
it; it is the number of slots a decision occupies, which runs from $4.70$ to
$6.18$ under \\CI{} against $4.68$ to $24.34$ under \\CE.""",
    "Triple as at 1968-1971, plus TOM 1.434823 +- 0.018025. Duty: runs.csv "
    "awake_tick/(27 x simulated_slots), ratio of sums, 0.692900 / 0.693253 / "
    "0.694603, prints 0.69. Floor: 1/duty (ratio of sums) = 1.443210 against a "
    "measured 1.434823, +0.5845 %, and the two-factor product closes to 0.0 % "
    "exactly under that aggregation (addition8_closure.py). Sharing: 1/(1-f) = "
    "1.047902 for 2PC; carrying TOM net of its own factor, "
    "(1.434823/1.000850) x 1.047901 = 1.502277, i.e. 0.067454 of a span of "
    "4.237073 = 1.592 %; carrying it gross gives 1.503554 and 1.6221 %. Both "
    "print 1.6 %. Slots per decision, ratio of sums: CI 4.7033/5.3540/6.1705, "
    "CE 4.6760/14.2073/24.3353. DELETED: 'it tracks the depth column of "
    "Table~ref{tab:depth} exactly' -- false, the ratio rises 3.95x while depth "
    "rises 21.25x. DELETED: 'the distance from there to 8.2 is the additional "
    "contribution of amortisation' -- void, it describes the retired metric.",
    "36, 41, 42, 43, 44, 48, 50")

# ---------------------------------------------------------------- 2003-2009 Section F p1
add(2003, 2009,
    """The distributional view adds two further observations. First, the \\CI{} and
the vote-based \\CE{} families occupy separate regions of the cost axis: the
upper quartile of the pooled \\CI{} decisions lies at 94.5 node-slots and the
lower quartile of Paxos over \\CE{} at 351, a factor of $3.7$ apart with no
interquartile overlap, and the $99$th percentile of the pooled \\CI{}
decisions, 269.9, still lies below the $1$st percentile of Paxos over \\CE,
324.0. The extreme tails do meet---the most expensive \\CI{} decision observed
costs 369.3 against 297.0 for the cheapest Paxos decision over \\CE---so the
separation is a statement about the bulk of the distributions and not about
their extremes. TOM over \\CE{} occupies an intermediate position, its median
decision costing 135 node-slots, above every \\CI{} median and far below the
two vote-based \\CE{} protocols; that median is exactly $\\Nnodes$ times the
median \\CE{} latency of 5 slots.""",
    "decisions.csv, 8984 decisions over 15 seeds pooled, n = 1500 per arm "
    "except 2PC-CI at 1484. Pooled CI q75 = 94.5111, Paxos-CE q25 = 351.0, "
    "ratio 3.7139. Pooled CI p99 = 269.8711, Paxos-CE p01 = 324.0, ratio "
    "1.2006. Max pooled CI 369.29, min Paxos-CE 297.0. TOM-CE median 135.0 = "
    "27 x 5. The 15-seed mean-based ceiling 27 x 4.676 = 126.25 is NOT "
    "compared against the median (charge 13).",
    "34, 38")

# ---------------------------------------------------------------- 2011-2021 Section F p2
add(2011, 2021,
    """Second, the three \\CI{} combinations are ordered by median cost---87.0 for
TOM, 89.0 for Paxos, 90.6 for 2PC---while their concurrency spans a factor of
twenty-one, and the cost of that concurrency lands in the upper tail rather
than in the box: the $99$th percentiles run 109.0, 269.5 and 334.5. The three
distributions interleave at the bottom, the $1$st percentile of 2PC over \\CI{}
at 83.5 falling inside the interquartile range of TOM, and separate at the top.
Spread is not monotone in concurrency---Paxos carries eleven times TOM's
concurrency in a narrower interquartile range, 7.2 against 9.0---so it is the
median and the upper percentile, not the width of the box, that measure what
the pipeline costs. This is the decoupling in its per-decision form: mean
concurrency rises from 1.00 to 20.84 while the median cost of a decision rises
by $4.2\\,\\%$.""",
    "decisions.csv, 15 seeds pooled: medians 87.00/89.00/90.63, p99 "
    "109.00/269.51/334.51, IQR 9.00/7.17/20.73, 2PC p01 83.4752 against TOM "
    "q25 83.00 and q75 92.00. Mean C_t from runs.csv: 0.999206 / 11.482912 / "
    "20.839135, ratio of means. Median rise 90.63/87.00 - 1 = 4.17 %. "
    "REPLACES the claim that the cheapest 2PC decisions cost less than the "
    "median TOM decision under CI: false on 15 seeds, 29.53 % of TOM decisions "
    "fall below 2PC's p01. The fill phase is deleted: the first proposal starts "
    "at slot 0.",
    "34, 38, 39, 47")

# ---------------------------------------------------------------- 2028-2032 frequency view
add(2028, 2032,
    """A frequency view of the same data brings out the multimodal structure of
the distribution: the bulk of the \\CI{} decisions falls in the cheapest
bins, below 100; TOM over \\CE{} sits coherently between 100 and 150; and
Paxos and 2PC over \\CE{} lie in the expensive bins above 300, with less than
$1\\,\\%$ of the \\CI{} family overlapping them.""",
    "decisions.csv, 15 seeds: pooled CI p99 = 269.87 < 300, so under 1 % of CI "
    "decisions exceed 300; the pooled CI maximum is 369.29, so 'no overlap at "
    "all' is false. TOM-CE p01 = 108.0 and p99 = 162.0, so 'between 100 and "
    "150' is loose at the top; left as approximate prose.",
    "38")

# ------------------------------------------------- 2063-2064 tab:escape caption
# Found by the extended zero-occurrence grep of item 7: the caption still
# attributed the table to the amortised metric after the entry below rebased
# its cells on the cumulative one. Smallest span: 2062 is not touched, and the
# words 'energy ceiling of the baseline.' are re-supplied verbatim.
add(2063, 2064,
    """energy ceiling of the baseline. Energy is cumulative per-decision energy
averaged over fifteen seeds.}""",
    "No new numbers: this is the caption of the table whose cells the entry at "
    "2075-2077 rebases. RE-SUPPLIED VERBATIM, not changed: 'energy ceiling of "
    "the baseline.' from base 2063. CHANGED: 'Energy values use the amortised "
    "metric of Equation~\\eqref{eq:amortized}.' -> the cumulative metric and the "
    "seed count. No equation reference is used: the file defines only "
    "eq:round, eq:ece, eq:depth and eq:amortized, and the cumulative metric's "
    "equation arrives with the blocked Section F rewrite, so a reference here "
    "would dangle.",
    "36, 38")

# ---------------------------------------------------------------- 2075-2077 tab:escape
add(2075, 2077,
    """TOM (\\CI)   & 4.7   & 88.0  & 127  & $1.4\\times$ \\\\
Paxos (\\CI) & 61.4  & 100.2 & 1658 & $16.5\\times$ \\\\
2PC (\\CI)   & 126.8 & 115.8 & 3424 & $29.6\\times$ \\\\""",
    "sweep_summary.csv, N=27 random loss 0.05, 15 seeds: avg_latency "
    "4.699/61.394/126.822; cumulative (listen+flood)/committed 87.99/100.22/"
    "115.84; ceiling 27 x L = 126.9/1657.6/3424.2; escape ceiling/E = "
    "1.44/16.54/29.56. The table now uses the cumulative metric throughout, "
    "which the caption must state; the published column was amortised and "
    "seed-99.",
    "9, 19, 36, 42")

# ---------------------------------------------------------------- 1899-1900
add(1899, 1900,
    """and $C_t \\equiv 1$---which is structural under \\CE{} rather than measured.
And the radio of every node stays on""",
    "No numbers. sim.rs:75, :89 and :111 admit one proposal at a time under CE, "
    "so unit depth is a property of the control flow; runs.csv reports mean_Ct "
    "= 1.000000 with zero variance across all 45 CE rows because it cannot "
    "report anything else. Table~ref{tab:depth} therefore cannot 'confirm "
    "empirically to two decimal places' what the simulator constructs. "
    "SMALLEST-SPAN NOTE, decision 55: the changed words end mid-line at base "
    "1900, so the remainder of that line is RE-SUPPLIED VERBATIM and not "
    "changed -- 'And the radio of every node stays on', whose predicate is base "
    "1901 ('for the whole round and never sleeps, so $A_t = \\Nnodes$'), outside "
    "the span. The leading 'and ' of base 1899 is likewise re-supplied, so the "
    "conjunction with base 1898 ('at most one proposal is in flight') survives. "
    "Both conditions of the paragraph therefore still arrive intact.",
    "18")

# ---------------------------------------------------------------- 2082-2084
add(2082, 2084,
    """The central observation is that between TOM and 2PC over \\CI{} the latency
column grows by roughly \\textbf{27 times} while the energy
column grows by only about \\textbf{1.3 times}. In the pipelined""",
    "27x: sweep_summary.csv avg_latency, random, N=27, loss 0.05, 15 seeds, "
    "126.822/4.699 = 26.987, ratio of means. 1.3x: runs.csv "
    "cumulative_per_dec, 15 seeds, 115.84/87.99 = 1.317. This is the SECOND "
    "76x site; the first is at 317 (entry 4). 'amortised' is deleted because "
    "tab:escape above it is rebased on the cumulative metric by the entry at "
    "2075-2077.",
    "9, 36, 42")

# ---------------------------------------------------------------- 2086-2092
add(2086, 2092,
    """\\textbf{independent of latency}. 2PC over \\CI{} is the extreme case: it
sits at the far right of the plane, with a latency of about one hundred and
thirty slots, yet its energy per decision remains at the level of TOM,
the lightest protocol in the system. The reason has already been
quantified: the high latency of 2PC over \\CI{} is not slowness but the
fact that each decision spent that entire interval in flight alongside
some twenty others, sharing the radio cost of every slot with them.""",
    "latency 126.822 and depth 21.2547, both 15 seeds, as at 1438 and "
    "1811-1813. 'approaching four hundred slots' predates the decision-9 fix.",
    "9, 42, 44")

# ---------------------------------------------------------------- 2190-2197
add(2190, 2197,
    """One remark on the energy metric is needed before the results. Every energy
ratio in this paper, here and above, is the \\emph{cumulative} metric of
Section~\\ref{sec:results-energy}, the same quantity reported in
Table~\\ref{tab:baseline}. The per-decision decomposition of
Equation~\\eqref{eq:amortized} is used only for the per-decision
distributions of Section~\\ref{sec:results-energy}; it is smaller than the cumulative
metric by $0.08\\,\\%$ for TOM, $1.66\\,\\%$ for Paxos and $4.57\\,\\%$ for 2PC,
and no ratio reported anywhere in this paper is corrected by it.""",
    "f as at 1943-1954. The deleted sentence said the ratios quoted earlier "
    "'were based on the amortised metric and are therefore larger'; after "
    "decision 36 that is no longer true of any ratio in the paper.",
    "36, 42, 44")

# -------------------------------------------------- 2292-2298 identity, prose
# Split from the old merged entry so that blank base line 2299 -- the paragraph
# break before the table float -- survives untouched.
add(2292, 2298,
    """Equation~\\eqref{eq:ece} claims that under \\CE{} the energy of a decision
is exactly the product of the network size and the latency of that
decision. The claim is not open to measurement error: if the radio never
sleeps, each of the $\\Nnodes$ nodes is awake in each of the $L$ slots a
decision occupies, so the product is what the accounting computes. What can be
checked is the instrument, and it holds throughout the topology space---three
\\CE{} protocols on five topologies, a twenty-six-fold range of diameter and a
forty-fold range of energy per decision.""",
    "sweep_summary.csv: the sleep counter is exactly zero in all 1125 CE rows; "
    "diameter 1 to 26 across the five topologies; CE energy per decision spans "
    "126.3 to 5136.5 node-slots, a factor of 40.7. Deletes the reference to "
    "tab:identity, which the following entry removes.",
    "32")

# -------------------------------------------------- 2300-2338 tab:identity
add(2300, 2338,
    """The check is on the instrument rather than on the arithmetic: the per-node
radio counters sum to $\\Nnodes$ times the slots ticked in all $2250$ runs of
the study, and measured energy per decision agrees with $\\Nnodes \\cdot L$ to
the last bit the simulator represents. The identity is moreover visible per
decision and not only in aggregate: every one of the $4500$ \\CE{} per-decision
energies measured at the reference point is an integer multiple of $\\Nnodes$,
so the \\CE{} per-decision energy distribution is the latency distribution
rescaled by $\\Nnodes$. No \\CI{} arm has that property---the per-decision
energies of Paxos and 2PC over \\CI{} are not integers at all, because a slot
shared between $k$ decisions contributes $1/k$ to each.""",
    "sweep_summary.csv: (listen+flood+sleep) = 27 x simulated slots on all 2250 "
    "rows. runs.csv: awake/committed against 27 x avg_latency agrees to 2.2e-16 "
    "on all 45 CE rows. decisions.csv: all 4500 CE amortised values are integer "
    "multiples of 27; TOM-CI values are integers but not multiples of 27; "
    "Paxos-CI and 2PC-CI are fractional. DELETES the fifteen-row table float: "
    "its error column was zero by construction in all fifteen rows, so it "
    "assumed the identity it reported as verified. No surviving \\ref to "
    "tab:identity remains after this entry and the preceding one.",
    "32, 37")

# ---------------------------------------------------------------- 2340-2356
add(2340, 2356,
    """What the check licenses is the stronger reading. It establishes
$\\Ece = \\Nnodes L$ as a \\textbf{structural law} of the \\CE{} architecture: as
long as the communication mechanism is sequential and the radio never sleeps,
the energy of a decision is locked to its latency regardless of the structure
of the network, and the designer has no lever at all---neither a better
topology nor a different protocol---with which to break that coupling. Every
departure from the law is then attributable to sleep alone, and the size of the
departure measures what pipelining buys: under \\CI{} the same accounting
falls short of $\\Nnodes L$ by between 22 and 31\\,\\% on the dense topologies,
which is exactly the fraction of node-slots those protocols spend with the
radio off. The one departure visible in the \\CE{} measurements themselves is
not energy at all: where a configuration leaves a proposal uncommitted, energy
per decision exceeds $\\Nnodes \\bar{L}$ by $1/d - 1$, where $d$ is the measured
pipeline depth. That residual is zero to machine precision in fourteen of the
fifteen groups and reaches $1.94\\,\\%$ on a single seed of 2PC over \\CE{} on the
line topology, where two of the fifteen seeds commit 99 proposals of 100.""",
    "Shortfall, ratio of sums per topology, 15 seeds: partial_mesh 22.66-23.05 "
    "%, full_mesh 26.19-26.33 %, scale_free 28.20-28.43 %, random 30.54-30.71 "
    "%, so '22 and 31' stands. Residual: 1/depth - 1 on the topology sweep, "
    "zero to machine precision in 14 of 15 groups; line/2PC-CE group mean "
    "0.257653 % (mean of per-seed residuals), worst single seed 37 at 1.936210 "
    "%, 13 of 15 seeds committing 100. The printed 1.94 % is the WORST SEED and "
    "is named as such; the group mean 0.26 % is not printed. Formula is "
    "1/d - 1, not 'the reciprocal of the depth'.",
    "10, 32, 42, 49")

# ---------------------------------------------------------------- 2371-2374
add(2371, 2374,
    """factor of four and throughput by a factor of about 1.7, yet
\\textbf{the pipeline depth remains effectively unchanged}: TOM over \\CI{}
stays at unity, Paxos over \\CI{} at about 11.6 and 2PC over \\CI{} at about
twenty-one in every case.""",
    "sweep_summary.csv, depth = (committed/end_slot) x avg_latency, 15 seeds "
    "per group: TOM 1.000/1.000/1.000/1.002 on full_mesh/partial_mesh/random/"
    "scale_free; Paxos 11.589/11.623/11.662/11.657; 2PC 21.446/21.455/21.255/"
    "20.954. The invariance claim strengthens under the fix. Base line 2370 "
    "('subsection. Across the four dense topologies the diameter varies by a') "
    "is context only and is NOT part of this span or of the replacement.",
    "9, 42")

# ---------------------------------------------------------------- 2431 tab:degree
add(2431, 2431,
    "2PC (\\CI)   & 0.1682 & $+0.1$\\,\\%  & 124.7 & $-1.6$\\,\\%  \\\\",
    "sweep_summary.csv, random vs scale_free, N=27 loss 0.05, 15 seeds: "
    "throughput 0.1681 -> 0.1682 (+0.08 %), avg_latency 126.82 -> 124.74 "
    "(-1.64 %). The published 350.0 and -2.2 % predate the decision-9 fix. "
    "Every other row of the table was reproduced exactly.",
    "9")

# ------------------------------------------------- 2565-2568 Little's law recap
# Split from the old merged entry 25: this deletes the "sixty" recap only.
# Base 2564 is a BLANK line and is deliberately outside the span, so the
# paragraph break before this sentence survives.
add(2565, 2568,
    """The underlying mechanism was quantified by Little's law: the pipeline
holds about twelve proposals in flight under Paxos and about twenty-one under
2PC, while all three \\CE{} protocols are confined to unit depth. That
concurrency, together with the ability to sleep the radio, reduces the""",
    "depth: runs.csv, 15 seeds, ratio of means -> 11.661524 +- 0.015311 and "
    "21.254664 +- 0.218137. Unit depth under CE is structural, not measured "
    "(sim.rs:75, :89, :111). The span stops at 2568 so that 'reduces the' keeps "
    "its object at 2569 ('energy per decision substantially'); base 2564 is "
    "blank and stays.",
    "18, 42, 43, 44")

# ---------------------------------------------------------------- 2573-2577
# Second half of the old merged entry 25: the fourth "within 1.5 %" site.
add(2573, 2577,
    """The generalisation study shows that these results do not depend on a
particular network. The identity $\\Ece = \\Nnodes L$ holds exactly in fifteen
independent cases spanning a twenty-six-fold range of
diameter, and the pipeline depth is effectively constant across the four
dense topologies, so the mechanism that produces the energy saving is""",
    "As at 2292-2338: no error band exists to quote, because the residual is "
    "1/depth - 1. sweep_summary.csv, 1125 CE rows, sleep = 0 throughout. The "
    "span ends at 2577 so that 'is' keeps its complement at 2578 "
    "('architectural rather than topological').",
    "32, 37")

# ---------------------------------------------------------------- 2617-2620
add(2617, 2620,
    """The evaluation carries three messages. First, the pipeline produces real
and measurable concurrency---on average twelve simultaneous proposals for
Paxos and twenty-one for 2PC---and that concurrency raises throughput by up to
a factor of four and shortens workload completion by a larger factor""",
    "depth as at 1811-1813, runs.csv, 15 seeds, ratio of means. Throughput "
    "0.1681/0.0412 = 4.08x, sweep_summary.csv, random, 15 seeds. Base 2621 "
    "('still, relative to the strongest baseline competitor. Second, under "
    "\\CE{}') is context only: it is NOT in this span and NOT in the "
    "replacement, so 'a larger factor' keeps its continuation.",
    "42")

# ------------------------------------------------------------------ BLOCKED
B = []
B.append({
    "where": "1316 and 407",
    "what": "the $0.4\\,\\%$ radio duty cycle at $99.9\\,\\%$ PDR taken from "
            "BlueFlood as a calibration target",
    "why": "The simulator's measured CI duty cycle is 0.69 at the reference "
           "point, three orders of magnitude away, and it has no packet "
           "delivery ratio instrumentation at all. Both sites move together "
           "only once the calibration of steps 2 to 5 is performed; neither "
           "number is derivable from anything measured so far.",
})
B.append({
    "where": "1329-1330",
    "what": "\\TBD{A2 error} and \\TBD{WPaxos error}",
    "why": "Blind predictions, pending the frozen calibration. The simulator "
           "additionally has no real-time unit: Slot is a u64 with no "
           "T_slot, so a 475 ms or 289 ms target cannot yet be expressed. "
           "Line numbers read from the file, not recalled: an earlier draft "
           "of this list cited 1323-1324, which is wrong.",
})
B.append({
    "where": "1343",
    "what": "\\TBD{any regime in which it does not}, the third and last \\TBD "
            "in the file",
    "why": "This is the step 6 sensitivity sweep. Two of its three axes cannot "
           "yet move the simulator: Slot is a u64 with no T_slot, so a "
           "+-50 % perturbation of slot duration changes nothing, and there "
           "is no correlated loss process to substitute for the independent "
           "one. Only \\Nretx (flood_repeats) is sweepable today. The one "
           "regime already found -- the line topology, where 2PC over CI is "
           "not competitive -- is described in the surrounding prose and does "
           "not need this macro; the macro cannot be resolved until the "
           "missing axes exist.",
})
B.append({
    "where": "the caption of the boxplot float around 1995-2001",
    "what": "the figure caption naming the metric, the whisker convention and "
            "the per-arm n",
    "why": "The float is commented out in the manuscript. The figure itself "
           "exists at plots/energy/energy_boxplot_15seed.pdf and its caption "
           "text is settled -- box = q25/q75, whiskers = p1/p99, points are "
           "the outer 1 % on each side, n = 1500 per arm except 2PC over CI "
           "at 1484, and the paper's headline ratios are cumulative -- but "
           "the lines to patch do not exist until the float is uncommented.",
})
B.append({
    "where": "1470-1478 and the surrounding commit-rate prose",
    "what": "the 98.9 % commit rate discussion, and the zero-commit rows of "
            "the topology and scalability tables",
    "why": "Decision 12's artefact-level treatment and decision 10's "
           "conditional-mean reporting are settled in principle, but the "
           "affected figures have not been regenerated, so the replacement "
           "cells are not final. 28 of 225 scalability runs commit fewer "
           "than 100, all 2PC over CI, one of them zero at N = 188.",
})

# Entries were appended in authoring order, not line order. Sort so the
# rendered file is in line order and the bottom-up application is well defined.
E.sort(key=lambda e: (e["a"], e["b"]))

# ------------------------------------------------------------------ render
P = []
P.append("# Manuscript patch specification")
P.append("")
P.append("Author-applied, per decisions 31 and 35. **Nothing in this file has been")
P.append("applied to `paper/paper.tex`.** No agent writes to the manuscript.")
P.append("")
P.append("Base file: `paper/paper.tex`, %d lines, sha256" % N_BASE)
P.append("`%s`." % SHA)
if SHA != BASE_SHA:
    P.append("")
    P.append("> **WARNING: the file has changed since the specification was written.**")
    P.append("> Expected `%s`." % BASE_SHA)
    P.append("> Every line number below is therefore suspect. Regenerate this file.")
else:
    P.append("This matches the agreed base, so every line number below is valid.")
P.append("")
P.append("Every *current text* block is sliced out of the file by line number by")
P.append("`docs/validation/addition7/scripts/make_patch_spec.py`, so it is a byte-exact")
P.append("copy and not a reconstruction. Apply the entries **bottom-up** — from the")
P.append("highest line number to the lowest — so that earlier edits do not shift the")
P.append("line numbers of later ones.")
P.append("")
P.append("Entries are in line order. %d entries, all final. Blocked items carry no" % len(E))
P.append("numbers and are listed separately at the end.")
P.append("")
P.append("---")
P.append("")

for i, e in enumerate(E, 1):
    span = "line %d" % e["a"] if e["a"] == e["b"] else "lines %d-%d" % (e["a"], e["b"])
    P.append("## %d. `paper/paper.tex` %s" % (i, span))
    P.append("")
    P.append("Authorised by decision%s %s." % ("" if "," not in e["dec"] else "s", e["dec"]))
    P.append("")
    P.append("**Current text** (byte-exact, %d line%s):"
             % (e["b"] - e["a"] + 1, "" if e["a"] == e["b"] else "s"))
    P.append("")
    P.append("```latex")
    P.append(cur(e["a"], e["b"]))
    P.append("```")
    P.append("")
    P.append("**Replacement text:**")
    P.append("")
    P.append("```latex")
    P.append(e["repl"])
    P.append("```")
    P.append("")
    P.append("**Sources.** %s" % e["src"])
    P.append("")
    P.append("**Blocked:** no.")
    P.append("")
    P.append("---")
    P.append("")

P.append("# Blocked entries — no numbers, do not apply")
P.append("")
P.append("These carry no replacement text, per the rule that no entry may appear whose")
P.append("numbers are not final.")
P.append("")
for i, b in enumerate(B, 1):
    P.append("## B%d. %s" % (i, b["where"]))
    P.append("")
    P.append("**What is blocked.** %s" % b["what"])
    P.append("")
    P.append("**Why.** %s" % b["why"])
    P.append("")

# Decision 89: nothing is written until every check below has passed, so a
# failing run cannot be mistaken for a passing one by looking at the output
# directory or at a printed hash.
SPEC_TEXT = "\n".join(P) + "\n"
print("built spec in memory: entries=%d blocked=%d base_sha_matches=%s"
      % (len(E), len(B), SHA == BASE_SHA))

# ================================================================= SELF-CHECK
# Round 17.10: verifying the SOURCE text is not enough. Apply the whole spec in
# memory and assert on the RESULT, because every defect of the last round was a
# replacement carrying a context line its own span did not delete.
print()
print("=" * 72)
print("APPLIED-RESULT SELF-CHECK")
print("=" * 72)

out = list(LINES)
for e in sorted(E, key=lambda x: x["a"], reverse=True):   # bottom-up
    out[e["a"] - 1:e["b"]] = e["repl"].split("\n")

fail = []

# --- (0) the base must be the file the spans were written against -----------
# The in-document WARNING branch above is now unreachable in a written spec: a
# base-sha mismatch fails here and nothing is written at all.
if SHA != BASE_SHA:
    fail.append("BASE FILE CHANGED: paper.tex is %s but every span was "
                "written against %s, so all line numbers are invalid"
                % (SHA, BASE_SHA))

# --- (1) no line repeated adjacently -----------------------------------------
for i in range(len(out) - 1):
    if out[i].strip() and out[i] == out[i + 1]:
        fail.append("ADJACENT DUPLICATE at patched line %d: %r" % (i + 1, out[i][:70]))

# --- (2) no long base line duplicated anywhere -------------------------------
from collections import Counter
oc, bc = Counter(out), Counter(LINES)
for l in set(l for l in LINES if len(l.strip()) > 45):
    if oc[l] > bc[l]:
        fail.append("DUPLICATED BASE LINE (%d -> %d copies): %r"
                    % (bc[l], oc[l], l[:70]))

# --- (3) no span may contain a blank base line (decision 55 hygiene) ---------
for e in E:
    for i in range(e["a"], e["b"] + 1):
        if LINES[i - 1] == "":
            fail.append("SPAN %d-%d CONTAINS BLANK BASE LINE %d" % (e["a"], e["b"], i))

# --- (4) blank-line total must be preserved exactly --------------------------
# The trailing newline makes split() yield a final '' in both; count real lines.
nb_base = LINES[:-1].count("") if LINES and LINES[-1] == "" else LINES.count("")
nb_out = out[:-1].count("") if out and out[-1] == "" else out.count("")
print("blank lines: base %d -> applied %d" % (nb_base, nb_out))
if nb_out != nb_base:
    fail.append("BLANK TOTAL MOVED: %d -> %d (must be equal)" % (nb_base, nb_out))

# --- (5) retired patterns gone; \TBD count unchanged -------------------------
import re as _re
body = "\n".join(out)
RETIRED = [r"357\.7", r"\b358\b", r"60\.1", r"\b11\.7\b", r"8\.2", r"76 times",
           r"within 1\.5", r"1\.5\\,\\%", r"to better than", r"350\.0",
           r"tab:identity", r"9658", r"-2\.2", r"\bsixty\b",
           r"\b76\b"]
# Decision 91: a regression pattern with no occurrence in the base cannot fail,
# so it certifies nothing. r"\\times 60" was exactly that -- zero base
# occurrences -- and is deleted. Every remaining pattern must be shown present
# in the base, with its line numbers, or this run fails.
print("")
print("%-18s %11s  %s" % ("pattern", "base count", "base line numbers"))
for pat in RETIRED:
    base_hits = [i + 1 for i, l in enumerate(LINES) if _re.search(pat, l)]
    print("%-18s %11d  %s" % (pat, len(base_hits), base_hits))
    if not base_hits:
        fail.append("RETIRED PATTERN %s NEVER OCCURRED IN THE BASE: delete "
                    "it, or name the site it is meant to guard" % pat)
    hits = [i + 1 for i, l in enumerate(out) if _re.search(pat, l)]
    if hits:
        fail.append("RETIRED PATTERN %s SURVIVES at %s" % (pat, hits))
# Decision 84: the old scan tested one spelling and was blind to the other.
# Match both, and report base and applied sites with their line numbers.
_AM = _re.compile(r"amorti[sz]")
am = [(i + 1, l) for i, l in enumerate(out) if _AM.search(l)]
am_base = [i + 1 for i, l in enumerate(LINES) if _AM.search(l)]
print("")
print("'amorti[sz]' sites: base %d -> applied %d" % (len(am_base), len(am)))
print("   base lines:    %s" % am_base)
print("   applied lines: %s" % [i for i, _ in am])
for i, l in am:
    print("   %5d| %s" % (i, l[:96]))
if body.count("\\TBD{") != "\n".join(LINES).count("\\TBD{"):
    fail.append("TBD COUNT CHANGED")

# --- (6) balance -------------------------------------------------------------
for env in ["table", "table*", "tabular", "figure", "equation"]:
    b, e_ = body.count("\\begin{%s}" % env), body.count("\\end{%s}" % env)
    if b != e_:
        fail.append("UNBALANCED %s: %d/%d" % (env, b, e_))
if body.count("{") != body.count("}"):
    fail.append("BRACES: %d/%d" % (body.count("{"), body.count("}")))

# --- (7) every \ref resolves -------------------------------------------------
labels = set(_re.findall(r"\\label\{([^}]+)\}", body))
for r in set(_re.findall(r"\\(?:eq)?ref\{([^}]+)\}", body)):
    if r not in labels:
        fail.append("DANGLING REF: %s" % r)

# --- (8) ROUND TRIP: diff the base against the result, hunk for hunk ---------
# The only check that constrains the HAND-WRITTEN side. difflib reports a
# changed region, not a whole span: where a replacement leaves some of the
# span's lines untouched, one entry yields several hunks. So assign every hunk
# to the entry whose base span contains it. The real findings are (a) no hunk
# falls outside every span and (b) no hunk straddles two spans, plus (c) every
# entry actually changed the file. Condition (d) -- patched lines equal to the
# replacement -- CANNOT FAIL by construction, because the applier above assigns
# e["repl"] straight into out[a-1:b]. It is kept only as a tripwire against a
# future change to the applier, and is never evidence (decision 88).
import difflib
sm = difflib.SequenceMatcher(None, LINES, out, autojunk=False)
raw = [(tag, i1 + 1, i2, j1 + 1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes()
       if tag != "equal"]
ordered = sorted(E, key=lambda x: x["a"])
owner, shift, bounds = {}, 0, []
for k, e in enumerate(ordered):
    n = len(e["repl"].split("\n"))
    bounds.append((e["a"], e["b"], e["a"] + shift, e["a"] + shift + n - 1, k))
    shift += n - (e["b"] - e["a"] + 1)
for tag, b1, b2, p1, p2 in raw:
    hit = [k for (a, b, pa, pb, k) in bounds
           if not (b2 < a or b1 > b) or (tag == "insert" and a <= b1 <= b + 1)]
    if len(hit) != 1:
        fail.append("HUNK %s base %d-%d maps to %d entries" % (tag, b1, b2, len(hit)))
    else:
        owner.setdefault(hit[0], []).append((tag, b1, b2, p1, p2))
print()
print("round trip: %d diff hunks over %d entries" % (len(raw), len(E)))
missing = [ordered[k]["a"] for k in range(len(ordered)) if k not in owner]
if missing:
    fail.append("ENTRIES PRODUCING NO DIFF: %s" % missing)
for k, e in enumerate(ordered):
    n = len(e["repl"].split("\n"))
    _, _, pa, pb, _ = bounds[k]
    if out[pa - 1:pb] != e["repl"].split("\n"):
        fail.append("PATCHED LINES != REPLACEMENT at base %d-%d" % (e["a"], e["b"]))
if not missing and not [f for f in fail if f.startswith(("HUNK", "PATCHED"))]:
    print("   every hunk lies inside exactly one entry; every entry changed the file")
    print("   (patched lines == replacement is an INVARIANT of the applier, not")
    print("   evidence -- decision 88)")

# --- (9) SENTENCE SEAMS: the sentence, reflowed, not two lines --------------
def seam(a, b, src):
    """From the last sentence-final punctuation before the span to the first
    after it, reflowed onto one line."""
    lo = max(0, a - 14)
    pre = " ".join(src[lo:a - 1])
    m = list(_re.finditer(r"(?<![A-Z])[.!?](?=\s|$)", pre))
    pre = pre[m[-1].end():] if m else pre
    post = " ".join(src[b:b + 14])
    m = _re.search(r"(?<![A-Z])[.!?](?=\s|$)", post)
    post = post[:m.end()] if m else post
    mid = " ".join(src[a - 1:b])
    return _re.sub(r"\s+", " ", (pre + " " + mid + " " + post)).strip()

print()
print("=" * 72)
print("SENTENCE SEAMS — one reflowed sentence per entry, spanning the join")
print("=" * 72)
shift = 0
for e in sorted(E, key=lambda x: x["a"]):
    n = len(e["repl"].split("\n"))
    s = e["a"] + shift
    print()
    print("entry base %d-%d -> patched %d-%d  (delta %+d)"
          % (e["a"], e["b"], s, s + n - 1, n - (e["b"] - e["a"] + 1)))
    print("   %s" % seam(s, s + n - 1, out))
    shift += n - (e["b"] - e["a"] + 1)

# --- line-delta accounting ---------------------------------------------------
print()
print("=" * 72)
print("LINE DELTAS")
print("=" * 72)
print("%-14s %6s %6s %7s" % ("base span", "base", "repl", "delta"))
tot = 0
for e in sorted(E, key=lambda x: x["a"]):
    nb, nr = e["b"] - e["a"] + 1, len(e["repl"].split("\n"))
    tot += nr - nb
    print("%-14s %6d %6d %+7d" % ("%d-%d" % (e["a"], e["b"]), nb, nr, nr - nb))
base_n = len(LINES) - (1 if LINES and LINES[-1] == "" else 0)
out_n = len(out) - (1 if out and out[-1] == "" else 0)
print("%-14s %6s %6s %+7d" % ("TOTAL", "", "", tot))
print("%d + (%d) = %d   applied file: %d   %s"
      % (base_n, tot, base_n + tot, out_n,
         "OK" if base_n + tot == out_n else "MISMATCH"))
if base_n + tot != out_n:
    fail.append("LINE ACCOUNTING: %d + %d != %d" % (base_n, tot, out_n))

print()
print("checks failed: %d" % len(fail))
for f in fail:
    print("  !! %s" % f)

# ------------------------------------------------------- decision 89 gate ----
# Past this point the run is a pass. Before it, no artefact and no hash exist.
if fail:
    print()
    print("NOTHING WRITTEN: %d check(s) failed." % len(fail))
    print("No artefact and no hash are emitted from a failing run.")
    print("Neither %s nor /tmp/paper_patched.tex was created or updated." % OUT)
    sys.exit(1)

print("  all clean")

PATCHED = "/tmp/paper_patched.tex"
assert SHA == BASE_SHA, "base sha drifted past the gate"
assert base_n + tot == out_n, "line accounting drifted past the gate"
assert nb_out == nb_base, "blank-line total drifted past the gate"
assert len(E) == 32, "entry count changed -- update this number deliberately"
assert len(B) == 5, "blocked count changed -- update this number deliberately"
open(OUT, "w").write(SPEC_TEXT)
open(PATCHED, "w").write("\n".join(out))
print()
print("wrote %s" % OUT)
print("wrote %s" % PATCHED)
print("lines=%d  bytes=%d" % (out_n, len("\n".join(out).encode())))
print("sha256=%s" % hashlib.sha256("\n".join(out).encode()).hexdigest())
print("spec  =%s" % hashlib.sha256(SPEC_TEXT.encode()).hexdigest())
print("base  =%s  (paper/paper.tex UNCHANGED)" % SHA)
