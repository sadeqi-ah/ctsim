# Topology Table Propagation and Gap Audit

## 1. Overview and Provenance
Commit `4895efeb` regenerated `plots/topology/table_topology_N27_loss05.csv`
and its LaTeX counterpart `.tex` from the committed raw sweep summary
`plots/topology/results/sweep_summary.csv`.

The table changes stem from two distinct simulator updates:
1. Issue 257 (quorum bitmap fix): affected Paxos (CI) on `line` and
   `scale_free`.
2. Decision-9 (`tx_starts` fix, commit `629a0cd`): affected 2PC (CI) latency
   across all five topologies.

This document audits the propagation status of the five decision-9 latency
rows across the repository, catalogues existing patch document prescriptions,
and records baseline preservation and patch prediction conflicts.

---

## 2. Decision-9 Family: Propagation Audit

### Row 1: `random` / 2PC (CI) Latency
- Old value: `357.7` (raw: `357.71`)
- Authoritative new value: `126.8` (table line 15: `lat=126.8, lat_std=6.4`)
- Status in manuscript (`paper/paper.tex`):
  Already patched at line 1538 (`Table I`, `tab:baseline`) to `126.8`.
- Remaining occurrences in repository:
  - `docs/validation/inventory.md:290` (notes published 357.7)
  - `docs/validation/phase0_report.md:404` (historical Phase 0 report)
  - `docs/validation/phase0_tables.json:638,4208,5235` (frozen baseline)
  - `docs/validation/addition6_energy_paths.md:236` (records old vs new)
  - `docs/validation/amortised_and_step1b.md:182,188` (records old vs new)
  - `docs/validation/addition10_withdrawn_energy_artefacts.md:23,67`
  - `docs/validation/paper-audit/NUMBER_AUDIT.md:163` (audits 126.8 vs 357.7)
  - `docs/validation/addition7/scripts/make_patch_spec.py:155`
  - `docs/validation/addition7/scripts/make_patch_spec_v3.py:153`
- Patch document prescriptions:
  - `docs/validation/patch_spec.md:233-242,257,287,689` prescribes `126.8`.
  - `docs/validation/addition1_addition3_patch_list.md:45,80-84,111`
    prescribes `357.7 -> 126.8`.

### Row 2: `scale_free` / 2PC (CI) Latency
- Old value: `350.0` (raw: `350.028`)
- Authoritative new value: `124.7` (table line 21: `lat=124.7, lat_std=4.7`)
- Status in manuscript (`paper/paper.tex`):
  Already patched at line 2522 (`Table IV`, `tab:degree`) to `124.7` and
  delta `-1.6%`.
- Remaining occurrences in repository:
  - `docs/validation/phase0_tables.json:653` (frozen baseline)
  - `docs/validation/addition7/scripts/make_patch_spec.py:519`
  - `docs/validation/addition7/scripts/make_patch_spec_v3.py:601`
- Patch document prescriptions:
  - `docs/validation/patch_spec.md:1018,1027` prescribes `350.0 -> 124.7`.
  - `docs/validation/addition1_addition3_patch_list.md:268,273` prescribes
    `350.0 -> 124.7`.

### Row 3: `line` / 2PC (CI) Latency
- Old value: `108.1`
- Authoritative new value: `23.1` (table line 3: `lat=23.1, lat_std=89.5`)
- Statistical meaninglessness:
  For 2PC (CI) on the line topology, the commit rate is `0.2%` (only 3
  committed proposals out of 1500 across 15 seeds). Fourteen seeds had zero
  commits; only seed 29 had 3 commits. As established in `paper/paper.tex:2598-
  2603` and `docs/validation/addition1_addition3_patch_list.md:318-330`,
  averaging latency over zero-commit runs produces division by near-zero.
  The latency mean (diluted to 23.1 by zero-padding across uncommitted seeds)
  is statistically meaningless and uninterpretable.
- Remaining occurrences in repository:
  - `docs/validation/addition1_addition3_patch_list.md:318,322,328,566,568`
- Patch document prescriptions:
  - `docs/validation/addition1_addition3_patch_list.md:318-330,566-568`
    critiques the published `108.1` and notes post-decision-9 value `23.11`.
  - Not asserted as an inline paper claim in `paper/paper.tex` (the paper
    explicitly excludes line 2PC metrics as statistically meaningless).

### Row 4: `partial_mesh` / 2PC (CI) Latency
- Old value: `260.9`
- Authoritative new value: `92.1` (table line 9: `lat=92.1, lat_std=3.0`)
- Status in manuscript (`paper/paper.tex`):
  Not quoted in paper text.
- Remaining occurrences in repository:
  None outside pre-PR #58 commit history.
- Patch document prescriptions:
  UNPATCHED. Neither `patch_spec.md` nor `addition1_addition3_patch_list.md`
  contains a patch rule for this cell, as it only appeared in the full
  topology table and was never cited in manuscript text.

### Row 5: `full_mesh` / 2PC (CI) Latency
- Old value: `208.9` (raw: `208.932`)
- Authoritative new value: `73.6` (table line 27: `lat=73.6, lat_std=1.0`)
- Status in manuscript (`paper/paper.tex`):
  Not quoted in paper text.
- Remaining occurrences in repository:
  - `docs/validation/phase0_tables.json:668` (`"mean": 208.932`)
- Patch document prescriptions:
  UNPATCHED. Neither `patch_spec.md` nor `addition1_addition3_patch_list.md`
  contains a patch rule for this cell.

---

## 3. Frozen Baseline Snapshot (Correction 1)
`docs/validation/phase0_tables.json` is a frozen Phase 0 baseline snapshot.
Its purpose is to record pre-fix baseline values (including `0.062468` and
`204.448` for line Paxos, and `357.71`, `350.028`, `208.932` for 2PC latencies).
It is intentionally NOT updated in this or subsequent rounds so that historical
reproducibility comparisons remain verifiable.

---

## 4. Conflict in Prior Patch Documents (Correction 2)
`docs/validation/addition1_addition3_patch_list.md:267` predicted that
`scale_free`/Paxos(CI) latency would remain at `59.6`:
- `addition1_addition3_patch_list.md:267`: predicted `59.6` (delta `-2.9%`).
- Authoritative regenerated table (`4895efeb`): actual latency is `59.8`
  (raw delta `-2.5%`; rounded basis gave `-2.6%`).
That prediction is now superseded by the regenerated table. Per instructions,
existing patch documents are left unmodified; this entry serves as the official
gap record.

---

## 5. Basis Convention for Table IV Change Percentages
Table IV (`tab:degree`) change percentages are ratios of raw per-seed means
(as defined in the table caption: "each change is the ratio of the means").
Recomputing these changes from the rounded (1-decimal or 4-decimal) values in
`table_topology_N27_loss05.csv` gives different results due to rounding
truncation; the printed table is therefore NOT a valid basis for calculating the
percentage change columns.

### Worked Example: Paxos (CI) Latency Change
Per `plots/topology/plot_topology.py:94,143-145`, the raw per-seed means over
the 15 seeds are:
- Scale-free: `mean_lat = 59.85000000` slots
- Random: `mean_lat = 61.39400000` slots

1. Raw basis (authoritative):
   `(59.85000000 / 61.39400000 - 1) * 100 = -2.5149% -> -2.5%`
2. Rounded table basis (deprecated):
   Using 1-decimal table values (`59.8` vs `61.4`):
   `(59.8 / 61.4 - 1) * 100 = -2.6058% -> -2.6%`

Commit `a22d5bc` briefly introduced the rounded basis value (`-2.6%`), making
the Paxos (CI) row inconsistent with the other five rows of Table IV.
Commit 5 in PR #59 corrected it to `-2.5%` to restore uniform raw-basis
convention across the entire table.
