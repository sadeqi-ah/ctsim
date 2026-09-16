# Evidence Freshness and Issue 257 Exposure Audit

## 1. Overview and Non-Regeneration Statement
This document provides a comprehensive freshness and exposure audit for all
derived evidence files under `docs/validation/paper-audit/sources/`.

Explicit statement: No evidence file was regenerated, rewritten, or re-derived
in this PR. This audit is diagnostic only, classifying existing artifacts and
determining their exposure to the issue 257 quorum defect fix (`cf05dd8`).

---

## 2. Freshness Classification of Evidence Files (Task 1)

Command executed across all files in `docs/validation/paper-audit/sources/`:
```bash
for f in docs/validation/paper-audit/sources/*; do
  last=$(git log -1 --format='%H %cI' -- "$f")
  sha=$(echo "$last" | cut -d' ' -f1)
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

| Audit line | paper.tex | Claimed value | File | Protocol/arm | Exposure |
|---|---|---|---|---|---|
| 166 | 1883-1891 | progress-curve shape | F1 | All protocols | AFFECTED |
| 173 | 2093-2096 | slots/dec 4.70-5.97 | F2 | Pooled CI/CE | AFFECTED |
| 174 | 2054 | quartiles/percentiles | F3 | Pooled CI/CE | AFFECTED |
| 175 | 2130 | TOM-CE median 135 (N*5) | F4 | TOM (CE) | LIKELY UNAFFECTED |
| 177 | 2140 | concurrency IQR 7.2/9.0 | F4 | Paxos/TOM CI | AFFECTED |
| 213 | 2421,2424 | radio 2250/4500 runs | F5 | CE | LIKELY UNAFFECTED |
| 359 | 1814,1818 | Progress curves Fig 13 | F1 | All protocols | AFFECTED |
| 360 | 2095-2096 | Slots per decision ranges | F2 | Pooled CI/CE | AFFECTED |
| 361 | 2054 | Energy distribution extrema | F3 | Pooled CI/CE | AFFECTED |
| 362 | 2424 | Integer multiple check | F5 | CE protocols | LIKELY UNAFFECTED |
| 364 | 2093 | Proposal sharing (1.6%) | F6 | 2PC (CI) | LIKELY UNAFFECTED |

---

## 4. Code-Path Evidence for LIKELY UNAFFECTED Verdicts

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
+                                },
```

### Code-Path Justification:
1. **TOM (CE) Median Cost (line 2130):**
   TOM over CE executes via `src/sim/ce.rs` using non-pipelined round loops and
   the CE physical abstraction. It shares zero code paths with
   `PaxosPipelineSim` in `src/sim/paxos_pipeline.rs`.
2. **Integer Multiple Check (lines 2421, 2424):**
   Validates E_i = N * L_i on all CE decisions across 2250 runs. Because
   the quorum defect was strictly in `paxos_pipeline` under CI, CE accounting
   and run lengths are entirely uncoupled from the defect.
3. **Proposal Sharing Candidates (line 2093):**
   Documents historical withdrawn numbers for 2PC over CI, unaffected by Paxos.

---

## 5. What a Regeneration Would Settle

In a future owner-approved round, running the single generator script
`python3 tools/audit_sources_210b.py` would regenerate all derived evidence
files from the post-fix simulator and sweeps:
- `progress_snapshots.csv` and `progress_README.md`
- `slots_per_decision.csv` and `slots_per_decision.md`
- `per_decision_energy.csv`
- `distribution_stats.csv` and `distribution_stats.md`
- `integer_multiple_check.md`

### Manuscript Lines Exposed to Potential Numerical Movement:
- `paper/paper.tex:1883-1891`: Paxos (CI) completion time (currently "about 525"
  slots) in the progress-curve description.
- `paper/paper.tex:2054`: Pooled CI distribution percentiles (currently Q3
  94.5, P99 269.9, extreme tail 369.3).
- `paper/paper.tex:2095-2096`: Pooled slots-per-decision range for CI
  (currently 4.70-5.97).
- `paper/paper.tex:2140`: Paxos (CI) per-decision energy interquartile range
  (currently 7.2).
