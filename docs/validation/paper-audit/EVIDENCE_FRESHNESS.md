# Evidence Freshness and Issue 257 Exposure Audit

## 1. Overview and Non-Regeneration Statement
This document provides a freshness, exposure, and generator audit for all
derived evidence files under `docs/validation/paper-audit/sources/`.

Explicit statement: No evidence file was regenerated, rewritten, or re-derived
in this PR. This audit is diagnostic only, classifying existing artifacts and
measuring their exposure to the issue 257 quorum defect fix (`cf05dd8`).

---

## 2. Freshness Classification of Evidence Files (Task 1)

Command executed across all files in `docs/validation/paper-audit/sources/`:
```bash
for f in docs/validation/paper-audit/sources/*; do
  last=$(git log -1 --format="%H %cI" -- "$f")
  sha=$(echo "$last" | cut -d" " -f1)
  if git merge-base --is-ancestor cf05dd8 "$sha"; then
    cls="POST-FIX"
  else
    cls="PRE-FIX"
  fi
  echo "$cls  $last"
  echo "  $f"
done
```

Raw command output:
```text
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/distribution_stats.csv
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/distribution_stats.md
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/integer_multiple_check.md
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/per_decision_energy.csv
PRE-FIX  47dea4aa5e45ca3626ca6e082f62f35a4e8d5fdd  2026-09-14T21:15:32+03:30
  docs/validation/paper-audit/sources/progress_README.md
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/progress_snapshots.csv
PRE-FIX  57c435023a1f8fefc28b2ce8d51d291581becfd2  2026-09-14T16:07:41+03:30
  docs/validation/paper-audit/sources/proposal_sharing_candidates.md
PRE-FIX  913ea3333124f4d65b05181cadd0b7271d4fc2a9  2026-09-12T07:24:37+03:30
  docs/validation/paper-audit/sources/slots_per_decision.csv
PRE-FIX  61f292d7f08eb48e0ddfdadef59950d22f80505f  2026-09-12T09:37:26+03:30
  docs/validation/paper-audit/sources/slots_per_decision.md
```

Summary counts:
- `POST-FIX`: 0 files
- `PRE-FIX`: 9 files (100% of evidence files under sources/)

---

## 3. Exposure of Audit Rows and Manuscript Numbers (Task 2)

Evidence file key:
- F1: `progress_snapshots.csv`
- F2: `slots_per_decision.md`
- F3: `distribution_stats.csv`
- F4: `per_decision_energy.csv`
- F5: `integer_multiple_check.md`
- F6: `proposal_sharing_candidates.md`

| Line | paper.tex | Claimed value | File | Arm | Exposure |
|---:|---|---|---|---|---|
| 166 | 1883-1891 | progress-curve shape | F1 | All | UNKNOWN - REQUIRES A RUN |
| 173 | 2093-2096 | 4.70-5.97 slots | F2 | CI/CE | UNAFFECTED (MEASURED) |
| 174 | 2054 | quartiles/percentiles | F3 | Pooled | UNKNOWN - REQUIRES A RUN |
| 175 | 2130 | median 135 (N*5) | F4 | TOM CE | UNAFFECTED (CODE PATH) |
| 177 | 2140 | concurrency IQR 7.2/9.0 | F4 | Paxos | UNKNOWN - REQUIRES A RUN |
| 213 | 2421,2424 | radio 2250/4500 | F5 | CE | UNAFFECTED (CODE PATH) |
| 359 | 1814,1818 | Progress curves | F1 | All | UNKNOWN - REQUIRES A RUN |
| 360 | 2095-2096 | Slots/dec ranges | F2 | CI/CE | UNAFFECTED (MEASURED) |
| 361 | 2054 | Energy extrema | F3 | Pooled | UNKNOWN - REQUIRES A RUN |
| 362 | 2424 | Integer check | F5 | CE | UNAFFECTED (CODE PATH) |
| 364 | 2093 | 1.6% (withdrawn) | F6 | 2PC CI | UNAFFECTED (CODE PATH) |

Exposure verdict summary:
- `CONFIRMED AFFECTED`: 0 rows.
- `UNAFFECTED (MEASURED)`: 2 rows (audit lines 173, 360).
  Rows 173 and 360 recomputed from post-fix sweep data; deltas are 0.000.
  (Extended in step 2.34: the remaining 8 slots_per_decision numbers also
  recompute IDENTICAL from post-fix data; none is supplied by paxos_pipeline.)
- `UNAFFECTED (CODE PATH)`: 4 rows (audit lines 175, 213, 362, 364; relabelled
  from `UNAFFECTED (MEASURED) (N=0)` in step 2.34: no recomputation was run,
  only the code path was inspected):
  - 175: checked that TOM (CE) executes via `src/sim/ce.rs`, uncoupled from
    `src/sim/paxos_pipeline.rs` (relabelled; no simulation was run).
  - 213: checked that `integer_multiple_check.md` covers CE decisions only
    (relabelled; no simulation was run).
  - 362: same file as 213, paper line 2424 (relabelled; no simulation was run).
  - 364: `proposal_sharing_candidates.md` is static reference text for 2PC (CI),
    no simulator rows at all (relabelled; no simulation was run).
- `UNKNOWN - REQUIRES A RUN`: 5 rows (audit lines 166, 174, 177, 359, 361).
  Evidence files have no committed input in repo; derived from runtime runs.

---

## 4. Code-Path and Counting Evidence for Measured Verdicts

Commit `d6937dc8` isolated the issue 257 quorum defect fix exclusively to:
`src/sim/paxos_pipeline.rs:247`

```text
commit d6937dc8d3241f685525842e77fd0d1af6331472
Author: AmirHossein Sadeghi <sadeghi.ah79@gmail.com>
Date:   Tue Sep 15 16:11:29 2026 +0330

    fix(paxos): replace fabricated all-ones quorum bitmap with single vote
    (issue 257)

 docs/validation/paper-audit/RERUN_PLAN.md | 120 ++++++++++++++++++++++++++++++
 src/sim/paxos_pipeline.rs                 |   4 +-
 tests/issue_257_regression.rs             |  73 ++++++++++++++++++
 3 files changed, 196 insertions(+), 1 deletion(-)

diff --git a/src/sim/paxos_pipeline.rs b/src/sim/paxos_pipeline.rs
index e46b146..ba2fa28 100644
--- a/src/sim/paxos_pipeline.rs
+++ b/src/sim/paxos_pipeline.rs
@@ -244,7 +244,9 @@ impl Sim for PaxosPipelineSim {
                     if !self.pending.contains_key(&term) {
                         self.pending.insert(
                             term,
-                            PendingProposal {
-                                bitmap: vec![true; num_nodes],
+                            PendingProposal {
+                                bitmap: {
                                     let mut bitmap = vec![false; num_nodes];
                                     bitmap[i] = true;
                                     bitmap
                                 },
```

### Measured Justification for UNAFFECTED (MEASURED) Rows:
1. **TOM (CE) Median Cost (line 175):**
   Protocol slice `per_decision_energy.csv:7486-8985` contains 1500 TOM (CE)
   decisions and exactly 0 Paxos CI rows. TOM over CE executes via
   `src/sim/ce.rs`, completely uncoupled from `src/sim/paxos_pipeline.rs`.
   (Correction: the previously cited slice `2713-4212` is the 2PC (CI) and
   TOM (CI) block; the TOM (CE) block actually spans lines 7486-8985.
   Separately, the file as a whole contains 1500 Paxos (CI) rows (lines
   2-1501) and the file-level claim of "0 Paxos CI rows" was never true.)
2. **Integer Multiple Check (lines 213, 362):**
   `integer_multiple_check.md` checks all CE decisions across 2250 runs
   (`df_energy[df_energy["phy"] == "CE"]`). Contains 0 Paxos CI rows. CE
   execution and accounting are unaffected by the CI quorum defect.
3. **Proposal Sharing Candidates (line 364):**
   `proposal_sharing_candidates.md` documents withdrawn claims for 2PC (CI),
   containing 0 Paxos CI rows.

### Sourcing Note: NUMBER_AUDIT Row Backed by `distribution_stats.md`
The bulk-separation audit row (`paper.tex:2121-2125`) is backed by
`sources/distribution_stats.md`. Its last writer is PRE-FIX:
```bash
git log -1 --format="%H %cI %s" -- \
  docs/validation/paper-audit/sources/distribution_stats.md
# Output: 913ea3333124f4d65b05181cadd0b7271d4fc2a9 2026-09-12T07:24:37+03:30
# docs(validation): source claims and rewrap
git merge-base --is-ancestor cf05dd8 \
  913ea3333124f4d65b05181cadd0b7271d4fc2a9 && echo "POST-FIX" || echo "PRE-FIX"
# Output: PRE-FIX
```
The audit row's claim status is therefore SOURCED, but its source predates the
issue 257 fix; it is not UNAFFECTED (MEASURED).

---

## 5. Generator Mapping, Counting Outputs, and Dispositions (Tasks 1-3)

### Generator Mapping (Task 1)
Path-handling lines printed from `tools/audit_sources_210b.py`:
- Line 18: `open(ROOT / \"plots/progress/sim_paxos_pipeline_progress.toml\")`
- Line 42: `pd.read_csv(RESULTS / f\"snapshots_{proto}.csv\")`
- Line 51: `to_csv(SOURCES / \"progress_snapshots.csv\")`
- Line 53: `open(SOURCES / \"progress_README.md\")`
- Line 63: `pd.read_csv(RESULTS / f\"snapshots_{proto}.csv\")`
- Line 67: `pd.read_csv(RESULTS / f\"results_{proto}.csv\")`
- Line 82: `pd.read_csv(ROOT / \"plots/scalability/results/sweep_summary.csv\")`
- Line 88: `to_csv(SOURCES / \"slots_per_decision.csv\")`
- Line 122: `to_csv(SOURCES / \"per_decision_energy.csv\")`
- Line 124: `open(SOURCES / \"slots_per_decision.md\")`
- Line 139: `open(SOURCES / \"proposal_sharing_candidates.md\")`
- Line 176: `to_csv(SOURCES / \"distribution_stats.csv\")`
- Line 178: `open(SOURCES / \"distribution_stats.md\")`
- Line 199: `open(SOURCES / \"integer_multiple_check.md\")`

Mapping table:
| Evidence file | In script? | Inputs read | Lines |
|---|:---:|---|---|
| distrib_stats.csv | YES | sim (plot_stacked_bar) | 115-117, 176 |
| distrib_stats.md | YES | sim (plot_stacked_bar) | 115-117, 178 |
| integer_multiple_check.md | YES | sim_paxos_*.toml; sim | 18, 117, 199 |
| per_decision_energy.csv | YES | sim (plot_stacked_bar) | 115-117, 122 |
| progress_README.md | YES | sim_paxos_*.toml; res | 18, 53, 63, 67 |
| progress_snapshots.csv | YES | results/snapshots_*.csv | 33-34, 42, 51 |
| proposal_sharing_cand.md | YES | none (static ref text) | 139-154 |
| slots_per_decision.csv | YES | sweep_summary.csv | 82-88 |
| slots_per_decision.md | YES | sweep_summary.csv | 82-83, 124 |

All 9 files are produced by `tools/audit_sources_210b.py`.
The script accepts no CLI arguments (no argparse or sys.argv); all parameters
(N=27, loss=0.05, 15 seeds, protocol list) are hardcoded.

### Piggyback Exposure Counting Commands and Raw Outputs (Task 2)
Commands executed on committed sweep data:
```bash
# Full sweep totals
awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci"' \
  plots/scalability/results/sweep_summary.csv | wc -l
# Output: 300
awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $19>0' \
  plots/scalability/results/sweep_summary.csv | wc -l
# Output: 158

# Filtered generator subset (nodes=27, loss_rate=0.05)
awk -F, 'NR>1 && $2==27 && $4==0.05 && \
  $6=="paxos_pipeline" && $7=="ci"' \
  plots/scalability/results/sweep_summary.csv | wc -l
# Output: 15
awk -F, 'NR>1 && $2==27 && $4==0.05 && \
  $6=="paxos_pipeline" && $7=="ci" && $19>0' \
  plots/scalability/results/sweep_summary.csv | wc -l
# Output: 5
```

Protocol row counts from direct inspection of evidence files:
- `per_decision_energy.csv`: 1500 2PC (CE), 1484 2PC (CI), 1500 Paxos (CE),
  1500 Paxos (CI), 1500 TOM (CE), 1500 TOM (CI).
- `progress_snapshots.csv`: 2372 2PC (CE), 588 2PC (CI), 1384 Paxos (CE),
  516 Paxos (CI), 467 TOM (CE), 455 TOM (CI).
- `slots_per_decision.csv`: 15 rows each for 2pc_ce, 2pc_pipeline, paxos_ce,
  paxos_pipeline, tom_ce, tom_pipeline.
- `distribution_stats.csv`: 1 row Paxos CE, 1 row Pooled CI.

### Disposition of Unreferenced Evidence Files (Task 3)
1. `distribution_stats.md`:
   Human-readable companion of cited CSV `distribution_stats.csv` (lines
   178-190). Quantities in it (94.5, 351, 3.7, 269.9, 324.0) support paper
   lines 2121-2125, audited under row 174 and newly added row in
   `NUMBER_AUDIT.md` (PR #65).
2. `progress_README.md`:
   Human-readable companion of cited CSV `progress_snapshots.csv` (lines
   53-80). Discloses configuration parameters and the 99 vs 100 reporting
   mismatch. No manuscript number rests on it.
3. `slots_per_decision.csv`:
   Raw tabular companion to cited summary markdown `slots_per_decision.md`
   (lines 82-88). Backs manuscript lines 2095-2096 audited under rows 173
   and 360. No manuscript number rests on it independently.

Conclusion: None of the three files are orphaned.

---

## 6. Recomputed Pooled Slots-Per-Decision and Provenance Traps

### Recomputation from Post-Fix Committed Sweep Data (Task 1)
Generator definition in `tools/audit_sources_210b.py:82-96`:
```python
    df_sweep = pd.read_csv(
        ROOT / "plots/scalability/results/sweep_summary.csv"
    )
    df_ref = df_sweep[
        (df_sweep["nodes"] == 27) & (df_sweep["loss_rate"] == 0.05)
    ].copy()

    df_ref["slots_per_decision"] = (
        df_ref["end_slot"] / df_ref["committed"]
    )
    cols = ["phy", "protocol", "seed", "end_slot",
            "committed", "slots_per_decision"]
    ren = {"end_slot": "total_slots", "committed": "committed_decisions"}
    df_ref[cols].rename(columns=ren).to_csv(
        SOURCES / "slots_per_decision.csv", index=False
    )

    # Calculate pooled estimator: sum(total_slots) / sum(committed_decisions)
    pooled = df_ref.groupby(["phy", "protocol"]).apply(
        lambda x: pd.Series({
            "pooled_slots_per_decision": (
                x["end_slot"].sum() / x["committed"].sum()
            )
        })
    ).reset_index()
    pooled.columns = ["phy", "protocol", "pooled_slots_per_decision"]
    ci_pooled = pooled[pooled["phy"] == "ci"]["pooled_slots_per_decision"]
    pooled_ci_min = ci_pooled.min()
    pooled_ci_max = ci_pooled.max()
    ce_pooled = pooled[pooled["phy"] == "ce"]["pooled_slots_per_decision"]
    pooled_ce_min = ce_pooled.min()
    pooled_ce_max = ce_pooled.max()
```

Input file commit provenance (Task 2):
```bash
git log -1 --format="%H %cI %s" -- \
  plots/scalability/results/sweep_summary.csv
# Output: cf05dd851855aa2358a4f1a52b4bd8bdf690cee2 2026-09-15T19:57:37+03:30
# data(sweeps): regenerate sweep_summary.csv after issue 257 quorum fix
git merge-base --is-ancestor cf05dd8 \
  "$(git log -1 --format=%H -- plots/scalability/results/sweep_summary.csv)" \
  && echo "POST-FIX"
# Output: POST-FIX
```
(The earlier one-argument form `git merge-base --is-ancestor cf05dd8 cf05dd8`
compared the fix commit with itself and proved nothing; the two-argument form
above compares the fix commit against the last writer of the file.)

Throwaway script arithmetic execution:
| phy | protocol | pooled_slots_per_decision |
|---|---|---:|
| ce | 2pc_ce | 24.335 |
| ce | paxos_ce | 14.207 |
| ce | tom_ce | 4.676 |
| ci | 2pc_pipeline | 5.967 |
| ci | paxos_pipeline | 5.265 |
| ci | tom_pipeline | 4.699 |

Recomputed ranges:
- CI min/max: `4.699` to `5.967` (min: TOM CI, max: 2PC CI)
- CE min/max: `4.676` to `24.335` (min: TOM CE, max: 2PC CE)

Committed values in `docs/validation/paper-audit/sources/slots_per_decision.md`:
```text
Configs: scalability sweep at N=27, random topology, loss_rate=0.05, 15 seeds

pooled (paper definition): sum(total_slots) / sum(committed_decisions)
CI min: 4.699, CI max: 5.967
CE min: 4.676, CE max: 24.335
```

Manuscript values at `paper/paper.tex:2098-2099` (lines 2093-2096):
```latex
and summed over seeds, which runs from $4.70$ to $5.97$ under \CI{} against
$4.68$ to $24.34$ under \CE.
```

Verdict: **`IDENTICAL`**
Recomputed values match committed evidence and manuscript at 3 decimals.
Neither family min nor max is supplied by Paxos. Audit rows 173 and 360 are
not stale after all.

### Provenance Limitations in Generator Script (Task 3)
Two provenance traps exist in `tools/audit_sources_210b.py`:
1. **Sticky revision line (`tools/audit_sources_210b.py:22-29`):**
   The generator explicitly reads the existing `Pre-generation source
   revision:` line out of `sources/progress_README.md` and preserves it across
   runs to avoid diffs on git commit hashes. Consequence: neither file content
   nor that line can be used to date evidence freshness.
2. **Hardcoded text in companion document (`tools/audit_sources_210b.py:150`):**
   The writer for `sources/proposal_sharing_candidates.md` hardcodes the
   literal string `4.70-5.97 under CI against 4.68-24.34 under CE`. If the
   range had moved, this companion file would have become stale independently
   of its own claim. Because TASK 1 confirmed `IDENTICAL`, the text remains
   accurate.

---

## 7. What a Regeneration Would Settle

In a future owner-approved round, running the single generator script
`python3 tools/audit_sources_210b.py` would regenerate all derived evidence
files from the post-fix simulator and sweeps:
- `progress_snapshots.csv` and `progress_README.md`
- `slots_per_decision.csv` and `slots_per_decision.md`
- `per_decision_energy.csv`
- `distribution_stats.csv` and `distribution_stats.md`
- `integer_multiple_check.md`

Note: Rows 173 and 360 (`paper.tex:2093,2095,2096`) were proven `IDENTICAL`
from post-fix sweep data in TASK 1 and are settled.

### Manuscript Lines Exposed to Potential Numerical Movement:
Only manuscript lines that remain UNKNOWN - REQUIRES A RUN:
- `paper/paper.tex:1883-1891`: Paxos (CI) completion time (currently "about 525"
  slots) in the progress-curve description (UNKNOWN - REQUIRES A RUN).
- `paper/paper.tex:2054` / `2121-2125`: Pooled CI distribution percentiles
  (currently Q3 94.5, P99 269.9, extreme tail 369.3) (UNKNOWN - REQUIRES A RUN).
- `paper/paper.tex:2140`: Paxos (CI) per-decision energy interquartile range
  (currently 7.2) (UNKNOWN - REQUIRES A RUN).

---

## 8. File Freshness vs Claim Freshness (step 2.34)

These two judgements are independent and must not be conflated:

- A **manuscript number** is `UNAFFECTED (MEASURED)` only when the
  recomputation supporting it ran on post-fix committed data.
- An **evidence file** is `FRESH` only when every number it publishes
  reproduces from post-fix committed data.

A manuscript number can be proven UNAFFECTED while its backing file stays
stale or PRE-FIX (e.g. the bulk-separation row is SOURCED from a PRE-FIX
`distribution_stats.md`), and an evidence file can be fully reproducible
(`slots_per_decision.csv` = FRESH) while the manuscript numbers it backs were
never the ones at risk. State each separately, with its own evidence.
