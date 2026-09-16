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
| 173 | 2093-2096 | 4.70-5.97 slots | F2 | CI/CE | CONFIRMED AFFECTED (N=5) |
| 174 | 2054 | quartiles/percentiles | F3 | Pooled | UNKNOWN - REQUIRES A RUN |
| 175 | 2130 | median 135 (N*5) | F4 | TOM CE | UNAFFECTED (MEASURED) (N=0) |
| 177 | 2140 | concurrency IQR 7.2/9.0 | F4 | Paxos | UNKNOWN - REQUIRES A RUN |
| 213 | 2421,2424 | radio 2250/4500 | F5 | CE | UNAFFECTED (MEASURED) (N=0) |
| 359 | 1814,1818 | Progress curves | F1 | All | UNKNOWN - REQUIRES A RUN |
| 360 | 2095-2096 | Slots/dec ranges | F2 | CI/CE | CONFIRMED AFFECTED (N=5) |
| 361 | 2054 | Energy extrema | F3 | Pooled | UNKNOWN - REQUIRES A RUN |
| 362 | 2424 | Integer check | F5 | CE | UNAFFECTED (MEASURED) (N=0) |
| 364 | 2093 | 1.6% (withdrawn) | F6 | 2PC CI | UNAFFECTED (MEASURED) (N=0) |

Exposure verdict summary:
- `CONFIRMED AFFECTED`: 2 rows (audit lines 173 and 360).
  Input subset contains N=5 rows with piggybacks > 0.
- `UNAFFECTED (MEASURED)`: 4 rows (audit lines 175, 213, 362, 364).
  Input subset / protocol slice contains exactly zero Paxos CI rows (N=0).
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
+                                    let mut bitmap = vec![false; num_nodes];
+                                    bitmap[i] = true;
+                                    bitmap
                                 },
```

### Measured Justification for UNAFFECTED (MEASURED) Rows:
1. **TOM (CE) Median Cost (line 175):**
   Protocol slice `per_decision_energy.csv:2713-4212` contains 1500 TOM (CE)
   decisions and exactly 0 Paxos CI rows. TOM over CE executes via
   `src/sim/ce.rs`, completely uncoupled from `src/sim/paxos_pipeline.rs`.
2. **Integer Multiple Check (lines 213, 362):**
   `integer_multiple_check.md` checks all CE decisions across 2250 runs
   (`df_energy[df_energy[\"phy\"] == \"CE\"]`). Contains 0 Paxos CI rows. CE
   execution and accounting are unaffected by the CI quorum defect.
3. **Proposal Sharing Candidates (line 364):**
   `proposal_sharing_candidates.md` documents withdrawn claims for 2PC (CI),
   containing 0 Paxos CI rows.

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
   178-190). All quantities in it (94.5, 351, 3.7, 269.9, 324.0) support
   paper lines 2054 / 2120-2125, which are audited under
   `distribution_stats.csv` in `NUMBER_AUDIT.md:174`. No independent paper
   number rests on it.
2. `progress_README.md`:
   Human-readable companion of cited CSV `progress_snapshots.csv` (lines
   53-80). Discloses configuration parameters and the 99 vs 100 reporting
   mismatch. No manuscript number rests on it.
3. `slots_per_decision.csv`:
   Raw tabular companion to cited summary markdown `slots_per_decision.md`
   (lines 82-88). The manuscript numbers (4.70-5.97 CI, 4.68-24.34 CE at
   lines 2095-2096) are audited under `slots_per_decision.md` in
   `NUMBER_AUDIT.md:173,360`. No manuscript number rests on it independently.

Conclusion: None of the three files are orphaned. No audit row additions needed.

---

## 6. What a Regeneration Would Settle

In a future owner-approved round, running the single generator script
`python3 tools/audit_sources_210b.py` would regenerate all derived evidence
files from the post-fix simulator and sweeps:
- `progress_snapshots.csv` and `progress_README.md`
- `slots_per_decision.csv` and `slots_per_decision.md`
- `per_decision_energy.csv`
- `distribution_stats.csv` and `distribution_stats.md`
- `integer_multiple_check.md`

### Manuscript Lines Exposed to Potential Numerical Movement:
Only manuscript lines that are CONFIRMED AFFECTED or UNKNOWN - REQUIRES A RUN:
- `paper/paper.tex:1883-1891`: Paxos (CI) completion time (currently "about 525"
  slots) in the progress-curve description (UNKNOWN - REQUIRES A RUN).
- `paper/paper.tex:2054`: Pooled CI distribution percentiles (currently Q3
  94.5, P99 269.9, extreme tail 369.3) (UNKNOWN - REQUIRES A RUN).
- `paper/paper.tex:2093,2095,2096`: Pooled slots-per-decision range for CI
  (currently 4.70-5.97) (CONFIRMED AFFECTED, N=5 input rows with piggybacks).
- `paper/paper.tex:2140`: Paxos (CI) per-decision energy interquartile range
  (currently 7.2) (UNKNOWN - REQUIRES A RUN).
