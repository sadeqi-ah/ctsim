# Issue 257 — Piggyback Free-Quorum Defect: Impact Analysis

## 1. Precise Mechanism of the Defect

### Defect site

`src/sim/paxos_pipeline.rs:240–249`:

```rust
if let Some(pt) = received_pkt.piggyback_term {
    if !state.log.iter().any(|(lt, _)| *lt == pt)
        && !state.pending.iter().any(|p| p.term == pt)
    {
        state.pending.push(PendingProposal {
            term: pt,
            data: received_pkt.piggyback_data.clone(),
            bitmap: vec![true; num_nodes],
        });
    }
}
```

### Runtime condition

A node enters this branch when all three conditions hold simultaneously:

1. The received packet carries `piggyback_term = Some(pt)` — a term being
   retransmitted in response to an earlier NACK.
2. The receiving node does **not** have term `pt` in its committed log
   (`!state.log.iter().any(|(lt, _)| *lt == pt)`).
3. The receiving node does **not** have term `pt` in its pending proposals
   (`!state.pending.iter().any(|p| p.term == pt)`).

That is: the node has **never seen** this term before — not in log, not in
pending. The code inserts a `PendingProposal` with `bitmap: vec![true; num_nodes]`,
an all-ones vote bitmap that was never collected from the network.

### Quorum fabrication

The all-ones bitmap causes the proposal to satisfy `check_quorum`
(`src/protocol/paxos.rs:98–107`) immediately on the next evaluation: it counts
`num_nodes` votes, which is ≥ `num_nodes / 2 + 1` for any `num_nodes ≥ 1`.

When the initiator's turn comes in the round-robin schedule, the commit path at
`src/sim/paxos_pipeline.rs:113–130` finds the highest term with quorum and calls
`commit_up_to(t)` (`src/protocol/paxos.rs:126–135`), which commits the piggybacked
term and all lower terms that are in `pending`. The term is then recorded via
`record_proposal` with `ProposalOutcome::Committed`
(`src/sim/paxos_pipeline.rs:125–130`).

A node that has never observed a single real vote for a term can therefore commit
it immediately through this path.

### What the correct bitmap should be

The normal proposal-insertion path at `src/sim/paxos_pipeline.rs:99–104` creates
`bitmap: vec![false; num_nodes]` and sets only the proposer's own bit
(`bitmap[initiator] = true`). The piggyback site should use a bitmap with only
the sender's bit set (available as `received_pkt.sender`), forcing the proposal
to collect votes through `merge_votes_up_to` like any normally received proposal.

### Impact on observable counters

**(a) Can the defect create commits that never had real quorum?**
Yes. The guard condition admits only terms the node has never seen; the all-ones
bitmap grants instant quorum without any real vote. (`src/protocol/paxos.rs:98–107`,
`src/sim/paxos_pipeline.rs:119–121`.)

**(b) Can it lower reported latency?**
Yes. A term that arrives via piggyback with instant quorum commits on the same
slot it enters `pending`, instead of waiting for votes to accumulate through
subsequent floods. The latency recorded via `record_proposal`
(`src/sim/paxos_pipeline.rs:125–130`) uses `core.current_slot - start`.

**(c) Can it change energy counters?**
Yes, indirectly. If the defect reduces `end_slot` by completing the workload
faster, the energy counters (listen, flood, sleep) for slots that would have
run without the bug are never accumulated. Energy per decision
`(listen + flood) / committed` changes through both numerator (fewer total
node-slots) and denominator (potentially fewer legitimate commits).

**(d) Can it change the `nacks` / `piggybacks` counters themselves?**
`piggybacks_sent` is incremented at `src/sim/paxos_pipeline.rs:230` in the
NACK-response path, which runs independently of the bitmap value used by the
receiver. So `piggybacks_sent` itself is unaffected by the bitmap bug; it counts
correctly how many piggyback responses were prepared. `nacks_sent` is incremented at
`src/sim/paxos_pipeline.rs:87` (inside `prepare_round`) and is similarly unaffected.


## 2. Blast Radius in the Committed Data

### Exposure scope

The defect exists only in `src/sim/paxos_pipeline.rs:247`. It does not affect
2PC (`src/sim/two_pc_pipeline.rs` uses `finalize_tx` at line 264) or TOM
(`src/sim/tom_pipeline.rs` uses `insert_message` at line 195). The exposed
protocol–PHY arm is `paxos_pipeline, ci` only.

### Exposed row counts

**Scalability sweep** (`plots/scalability/results/sweep_summary.csv`):

```
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" {total++; if($19>0) exposed++} END {print "total:", total, "exposed:", exposed}' plots/scalability/results/sweep_summary.csv
total: 300 exposed: 158
```

**Topology sweep** (`plots/topology/results/sweep_summary.csv`):

```
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" {total++; if($19>0) exposed++} END {print "total:", total, "exposed:", exposed}' plots/topology/results/sweep_summary.csv
total: 75 exposed: 31
```

**Total: 158 + 31 = 189 exposed rows.**

### Piggyback statistics (all 189 exposed rows)

| Statistic | piggybacks | piggybacks / committed |
|-----------|-----------|----------------------|
| min | 2 | 0.020 |
| median | 128 | 1.280 |
| max | 5341 | 53.410 |

Zero-committed rows: none (all 189 rows have committed > 0).

### Exposure by network size (scalability sweep, paxos_pipeline,ci)

| nodes | total rows | exposed | share | sum(piggybacks) |
|------:|-----------:|--------:|------:|----------------:|
| 6 | 60 | 18 | 30.0% | 141 |
| 13 | 60 | 30 | 50.0% | 1494 |
| 27 | 60 | 30 | 50.0% | 4371 |
| 54 | 60 | 38 | 63.3% | 12303 |
| 188 | 60 | 42 | 70.0% | 84276 |

Exposure is concentrated at larger networks and higher loss rates. At N=188
with loss ≥ 0.05, 42 of 45 rows are exposed.

### Exposure by topology (topology sweep, paxos_pipeline,ci)

| topology | total rows | exposed | share | sum(piggybacks) |
|----------|----------:|--------:|------:|----------------:|
| full_mesh | 15 | 0 | 0.0% | 0 |
| line | 15 | 15 | 100.0% | 9010 |
| partial_mesh | 15 | 0 | 0.0% | 0 |
| random | 15 | 5 | 33.3% | 180 |
| scale_free | 15 | 11 | 73.3% | 574 |

The line topology has 100% exposure; all 15 seeds have piggybacks ranging
from 474 to 763 against committed = 100.

### Critical observation: committed = proposals in every exposed row

```
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $11 < $10 {count++} END {print count+0}' plots/scalability/results/sweep_summary.csv
0
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $11 < $10 {count++} END {print count+0}' plots/topology/results/sweep_summary.csv
0
```

Every paxos_pipeline,ci row has `committed = proposals = 100`. The defect has
not inflated the committed count beyond the workload ceiling. However, this does
not prove the count would remain 100 without the bug — it may have caused
proposals to commit that would otherwise have timed out.


## 3. Which Published Numbers Consume the Exposed Rows

All scripts read `plots/scalability/results/sweep_summary.csv` (scalability) or
`plots/topology/results/sweep_summary.csv` (topology) and include all six
protocol–PHY arms without filtering out paxos_pipeline,ci.

The energy and progress figures (`plots/energy/plot_paper_energy.py`,
`plots/progress/plot_progress.py`) use single-run results from `results/`
(gitignored, seed=99, N=27, loss=0.05) rather than the sweep CSVs. These runs
also use the paxos_pipeline protocol and are affected by the defect, but their
output is not committed in the repository.

| Published quantity | paper.tex line | Figure/Table | Script:line that computes it | Consumes exposed rows? | Exposed rows in input |
|---|---|---|---|---|---|
| Table I Paxos(CI) row: thr 0.1903 | 1537 | Table I | `plots/scalability/plot_summary_commit.py:63` | YES | 5 of 15 at baseline (N=27, loss=0.05) |
| Table I Paxos(CI) row: E/dec 100.2 | 1537 | Table I | `plots/scalability/plot_summary_commit.py:64,80` | YES | 5 of 15 at baseline |
| Table I Paxos(CI) row: Eff 1.906 | 1537 | Table I | `plots/scalability/plot_summary_commit.py:65` | YES | 5 of 15 at baseline |
| Table II Paxos(CI) depth 11.66 | 1923 | Table II | Derived: thr × lat (Little's law) | YES | 5 of 15 at baseline |
| "roughly 2.7 times" Paxos thr ratio | 1611 | — | Paxos(CI)/Paxos(CE) from same CSV | YES | 5 of 15 at baseline |
| "about 12 concurrent proposals" | 166, 318, 1937, 2662 | — | Derived: thr × lat (Little's law) | YES | 5 of 15 at baseline |
| Paxos on line: "thr 0.0625" | 2594 | — | `plots/topology/plot_topology.py:94` | YES | 15 of 15 on line |
| Paxos on line: "highest among all" | 2594 | — | — | YES | 15 of 15 on line |
| Fig 3a throughput_vs_nodes Paxos(CI) | 1585 | Fig. 3a | `plots/scalability/plot_scalability.py:65` | YES | 158 total across all (N, loss) |
| Fig 3b throughput_vs_loss Paxos(CI) | 1658 | Fig. 3b | `plots/scalability/plot_scalability.py:65` | YES | 30 exposed rows (N=27, loss > 0) |
| Fig 4 latency_vs_nodes Paxos(CI) | 1740 | Fig. 4 | `plots/scalability/plot_scalability.py:117` | YES* | 158 total across all (N, loss) |
| Fig 10 efficiency_vs_nodes Paxos(CI) | 2229 | Fig. 10 | `plots/scalability/plot_efficiency.py:60,66` | YES | 158 total |
| Fig 12a thr_vs_topology Paxos(CI) | 2325 | Fig. 12a | `plots/topology/plot_topology.py:94` | YES | 31 total |
| Fig 12b lat_vs_topology Paxos(CI) | 2329 | Fig. 12b | `plots/topology/plot_topology.py:95` | YES* | 31 total |
| Table I 2PC(CI) row (all columns) | 1538 | Table I | same script | NO | 0 |
| "4.083× throughput" 2PC ratio | 167, 319 | — | 2PC(CI)/2PC(CE) | NO | 0 |
| "5.672× energy" 2PC ratio | 167, 320 | — | 2PC(CE)/2PC(CI) E/dec | NO | 0 |
| "4.268× global max thr" | 167, 320 | — | max over all (N, loss) | NO | 0 |
| "5.987× global max energy" | 168, 321 | — | max over all (N, loss) | NO | 0 |
| "70.07% commit rate" (2PC at 20% loss) | 1728, 2653 | — | 2PC(CI) commit rate | NO | 0 |
| "0.2% commit rate" (2PC on line) | 2578, 2726 | — | 2PC(CI) on line | NO | 0 |
| Energy identity E = N×L | 2024–2026 | — | CE protocols only | NO | 0 |
| "616 slots" TOM latency on line | 175, 329, 2616 | — | TOM(CI) on line | NO | 0 |

\* Note on latency figures: Latency is read directly from `avg_latency` (not arithmetically derived from `committed`), but it is measured inside simulation runs where the defect fabricated quorums; thus the plotted Paxos(CI) data points consume exposed runs.


## 4. Worst-Case Analytical Bounds

### Loose bound (prescribed, dimensionally mismatched)

> **LOOSE BOUND — DIMENSIONALLY MISMATCHED, VACUOUS WHERE piggybacks ≥ committed.**
>
> Worst-case assumption: every proposal admitted through the piggyback-recovery
> path is treated as a spurious commit, i.e.
> `committed_adjusted = committed - piggybacks` (floored at zero) for exposed
> rows only, all other columns unchanged.

This bound subtracts a packet-event counter (`piggybacks_sent`, which counts the
number of times any node prepared a piggyback response) from a decision counter
(`committed`). Since the median ratio piggybacks/committed is 1.28, this bound
drives most exposed rows to zero commits and yields vacuous results (e.g. −100%
throughput on the line topology).

#### Loose-bound results (Table I Paxos(CI) baseline: N=27, loss=0.05)

**Throughput arithmetic** (5 of 15 seeds exposed):

The script `plots/scalability/plot_summary_commit.py:63` computes
`throughput = committed / end_slot` per row, then averages over the 15 seeds.

- 10 unexposed seeds: committed=100, throughput unchanged.
- seed 5: committed=100, piggybacks=26, adj=74 → thr_adj=74/end_slot.
- seed 19: committed=100, piggybacks=52, adj=48.
- seed 23: committed=100, piggybacks=26, adj=74.
- seed 31: committed=100, piggybacks=50, adj=50.
- seed 41: committed=100, piggybacks=26, adj=74.

```
Original mean throughput: 0.1903
Adjusted mean throughput: 0.1680
```

**Energy/dec arithmetic** (`plots/scalability/plot_summary_commit.py:64` per-row definition, line 80 mean aggregation):

`energy_per_dec = (listen + flood) / committed` per row, then averaged.

For the 5 exposed seeds the denominator shrinks while the numerator (listen+flood)
stays the same, inflating the per-row ratio nonlinearly. The mean of per-row
ratios (121.5) differs from the ratio of sums (113.9) because Jensen's inequality
applies to the convex function 1/x:

| Seed | listen+flood | committed | adj | E/dec orig | E/dec adj |
|------|-------------|-----------|-----|-----------|-----------|
| 5 | 9583 | 100 | 74 | 95.83 | 129.50 |
| 19 | 10044 | 100 | 48 | 100.44 | 209.25 |
| 23 | 11501 | 100 | 74 | 115.01 | 155.42 |
| 31 | 10142 | 100 | 50 | 101.42 | 202.84 |
| 41 | 10129 | 100 | 74 | 101.29 | 136.88 |

```
Mean E/dec original: 100.2
Mean E/dec adjusted (mean of per-row ratios): 121.5
```

**Commit rate**: 10 seeds at 100.0%, seeds 5/23/41 at 74.0%, seed 19 at 48.0%,
seed 31 at 50.0%. Mean: 88.0%.

#### Loose-bound summary table

| Published quantity | Published value | Loose-bound value | Δ absolute | Δ relative |
|---|---|---|---|---|
| 2PC throughput ratio 4.083× | 4.083× | 4.083× | 0 | 0% |
| 2PC energy ratio 5.672× | 5.672× | 5.672× | 0 | 0% |
| Global max thr ratio 4.268× | 4.268× | 4.268× | 0 | 0% |
| Global max energy ratio 5.987× | 5.987× | 5.987× | 0 | 0% |
| Table I Paxos(CI) thr | 0.1903 | 0.1680 | −0.0223 | −11.7% |
| Table I Paxos(CI) E/dec | 100.2 | 121.5 | +21.3 | +21.3% |
| Table I Paxos(CI) commit% | 100.0% | 88.0% | −12.0 pp | −12.0% |
| Paxos CI/CE thr ratio "~2.7×" | 2.703× | 2.386× | −0.317 | −11.7% |
| Table I Paxos(CI) Eff | 1.906 | UNKNOWN — REQUIRES A RUN | — | — |
| Pipeline depth "about 12" (11.66) | 11.66 | UNKNOWN — REQUIRES A RUN | — | — |
| Paxos on line thr "0.0625" | 0.0625 | 0.0000 | −0.0625 | −100% |
| Energy identity E=N×L | exact | exact (CE only) | 0 | 0% |
| 70.07% 2PC commit rate | 70.07% | 70.07% | 0 | 0% |
| Latency-dependent quantities | various | UNKNOWN — REQUIRES A RUN | — | — |

### Tight bound (structural, from code and data)

The number of **distinct terms** that can enter `pending` through the piggyback
path is bounded by the number of proposals in the workload. The guard at
`src/sim/paxos_pipeline.rs:241–242` ensures each term enters `pending` at most
once per node (it is skipped if the term is already in `log` or `pending`).
Terms are integers in `0..num_proposals`, so at most `proposals` (= 100 in all
committed configurations) distinct terms can be inserted.

Crucially, every paxos_pipeline,ci row in both sweep CSVs has
`committed = proposals = 100`:

```
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $11 < $10 {c++} END {print c+0}' plots/scalability/results/sweep_summary.csv
0
$ awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $11 < $10 {c++} END {print c+0}' plots/topology/results/sweep_summary.csv
0
```

The defect has not inflated the committed count beyond the workload ceiling.
The committed count **cannot** exceed `proposals` because `commit_up_to`
(`src/protocol/paxos.rs:126–135`) only commits terms that exist in `pending`,
and each term can appear in `pending` at most once.

Therefore the **tight bound establishes that upward inflation beyond 100 is
impossible, but downward movement is UNKNOWN — REQUIRES A RUN**. The
distortion in committed counts is bounded from above by the ceiling, but the
true bug-free commit count could be lower if certain proposals only succeeded
due to fabricated quorums. Distortion is also present in **latency** (the defect
causes earlier commits, reducing `avg_latency` and `end_slot`), which in turn
affects **throughput** (`committed / end_slot`) and **energy per decision**
(`(listen + flood) / committed` through the numerator, since fewer slots means
less total listen+flood time).

This specific cell matters because Paxos(CI) reports 100.0% commit at loss=0.20
(`plots/scalability/results/sweep_summary.csv` rows 68, 188, 308, 428, 548, 668,
788, 908, 1028, 1148, 1268, 1388, 1508, 1628, 1748) where 2PC(CI) reports
70.07% (`paper/paper.tex:1728, 2653`), and 100% on the `line` topology
(`plots/topology/results/sweep_summary.csv` rows 2, 32, 62, 92, 122, 152, 182,
212, 242, 272, 302, 332, 362, 392, 422; `paper/paper.tex:2594`) where 2PC(CI)
reports 0.2% (`paper/paper.tex:174, 328, 335, 2578, 2726`). These are exactly the
values most plausibly propped up by free quorum. We do not claim the 100% figure
is wrong (since majority consensus is structurally more resilient than unanimity),
only that it is unverified and that its verification requires a simulation run.

#### Tight-bound summary table

| Published quantity | Published value | Tight-bound value | Reasoning |
|---|---|---|---|
| Table I Paxos(CI) committed/commit% | 100 / 100.0% | <= 100 (inflation impossible); downward movement UNKNOWN — REQUIRES A RUN | Ceiling prevents inflation above 100; downward sensitivity unverified |
| Table I Paxos(CI) throughput | 0.1903 | UNKNOWN — REQUIRES A RUN | Depends on end_slot, which may decrease with bug |
| Table I Paxos(CI) E/dec | 100.2 | UNKNOWN — REQUIRES A RUN | Depends on total listen+flood, which changes with end_slot |
| Table I Paxos(CI) latency | 61.4 | UNKNOWN — REQUIRES A RUN | Directly affected by instant-quorum commits |
| Pipeline depth "about 12" | 11.66 | UNKNOWN — REQUIRES A RUN | Product of throughput and latency |
| Paxos on line thr "0.0625" | 0.0625 | UNKNOWN — REQUIRES A RUN | committed=100 stays, but end_slot may change |
| All 2PC and TOM quantities | various | No change | Different protocol, not affected by defect |
| All CE quantities | various | No change | Different PHY, not affected by defect |
| 4.083×, 4.268×, 5.672×, 5.987× | various | No change | 2PC ratios, not affected |


## 5. Decision Options

### Option A: Fix the code and re-run only the exposed configurations

**Code change:** `src/sim/paxos_pipeline.rs:247` — replace `vec![true; num_nodes]`
with a single-bit bitmap for the sender (analogous to `src/sim/paxos_pipeline.rs:99–100`).

**Re-run:** 158 scalability + 31 topology = 189 configurations. Only seeds with
`piggybacks > 0` would produce different output, but all 300 + 75 paxos_pipeline,ci
rows should be re-run for consistency (same binary).

**Files changed:**
- `src/sim/paxos_pipeline.rs` (1-line fix)
- `plots/scalability/results/sweep_summary.csv` (300 paxos_pipeline,ci rows re-run)
- `plots/topology/results/sweep_summary.csv` (75 paxos_pipeline,ci rows re-run)
- `paper/paper.tex` — Table I Paxos(CI) row, Table II Paxos(CI) row, inline
  claims "about 12", "roughly 2.7 times", and Paxos-on-line throughput "0.0625"
  would need verification and possible update.

**`assert_blob` SHA1 locks that would need updating:**
- `tests/validation.rs:1852` and `tests/validation.rs:2283`:
  `7386c9467760b7c4bacb50d30705dfc7f00b0e8f` for
  `docs/validation/paper-audit/sources/per_decision_energy.csv` — only if the
  energy figures are re-generated from the corrected single-run data.

**Wall-clock cost:** Split estimate based on committed repository and CI evidence:
- *Topology sweep (75 paxos-ci configs):* Cheap (< 1 minute). In CI (`.github/workflows/ci.yml:48–55`), the entire 450-configuration topology sweep is executed twice consecutively for byte-identity checks, and the entire `rust` CI job (including compilation, all 34 tests, smoke runs, and both sweeps) completed in ~2 minutes in PR #53, which provides an upper bound for a single run.
- *Scalability sweep (300 paxos-ci configs):* The expensive portion. CI notes at `.github/workflows/ci.yml:69` that "The scalability sweep includes N=188 and takes minutes", and `docs/validation/addition14/data/run_provenance.md:15` records a dense-block wall clock of 756.57 s (~12.6 minutes) for a sweep (`docs/validation/addition14/data/run_provenance.md:14`), but that figure comes from a different harness (running the `a2_sensys17` calibration profile for 2pc_ce and Wireless Paxos arms over `random_n180_*` / `random_n188_*` graphs at loss 0.05 and 0.06, rather than the ctsim scalability grid of $N \in \{6, 13, 27, 54, 188\}$, loss $\in \{0, 0.05, 0.1, 0.2\}$, 100 proposals, 15 seeds) and is therefore not directly comparable to the ctsim scalability sweep. However, because the 300 paxos-ci configurations span 5 network sizes ($N \in \{6, 13, 27, 54, 188\}$) and $N=188$ dominates execution time with no documented per-configuration breakdown in the repository, any wall-clock estimate for this sweep is UNKNOWN — REQUIRES A RUN.

### Option B: Fix the code and re-run the full sweeps

**Code change:** Same as Option A.

**Re-run:** All 1800 scalability + 450 topology = 2250 configurations.

**Files changed:** Same as Option A, plus all generated figures, tables, and
the full `NUMBER_AUDIT.md` tally would need re-verification.

**`assert_blob` SHA1 locks:** Same as Option A, potentially more if figures change.

**Wall-clock cost:** COST UNKNOWN.

### Option C: Document the defect as a stated limitation

**Code change:** None.

**Re-run:** None.

**Files changed:**
- `paper/paper.tex` — add one sentence to Section 7.6 "Limitations and Scope of
  Validity" (`\label{sec:results-limitations}`, lines 2568–2638):

  > The piggyback recovery path for Paxos over \CI{} inserts recovered proposals
  > with a pre-filled vote bitmap (`src/sim/paxos\_pipeline.rs:247`), granting
  > instant quorum to terms the receiving node has never collected votes for.
  > The 2PC and TOM headline ratios ($4.083\times$ throughput, $5.672\times$
  > energy) are structurally unaffected because the defect exists only in the
  > Paxos pipeline; the Paxos-specific numbers in Table~\ref{tab:baseline}
  > are exposed but cannot be bounded without re-running the affected
  > configurations.

**`assert_blob` SHA1 locks:** None.

**Wall-clock cost:** Zero computation; editorial only.

### Recommendation

Option A is the correct choice. Option C alone is no longer defensible now that the guard condition is settled: because `vec![true; num_nodes]` is admitted precisely when the node has never seen the proposal in `log` or `pending` (`src/sim/paxos_pipeline.rs:241–242`), the simulator fabricates unanimous consent for entirely unobserved proposals, converting an unverified consensus protocol into an unsound artifact that cannot be defended as a mere modeling approximation. A reviewer would reasonably reject Option C because the paper claims Paxos results are valid while the simulator grants free quorum without observed votes. The code fix is a single line, and the headline 2PC claims (4.083×, 5.672×) are structurally unaffected.
