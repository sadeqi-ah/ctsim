# Issue 257 -- Post-Fix Rerun Plan

## 1. What Changed

One site in `src/sim/paxos_pipeline.rs`, inside `process_round`:

```diff
--- a/src/sim/paxos_pipeline.rs
+++ b/src/sim/paxos_pipeline.rs
@@ -241,10 +241,12 @@ impl CiProtocol for PaxosCi {
                 if !state.log.iter().any(|(lt, _)| *lt == pt)
                     && !state.pending.iter().any(|p| p.term == pt)
                 {
+                    let mut bitmap = vec![false; num_nodes];
+                    bitmap[i] = true; // only the receiving node's own vote
                     state.pending.push(PendingProposal {
                         term: pt,
                         data: received_pkt.piggyback_data.clone(),
-                        bitmap: vec![true; num_nodes],
+                        bitmap,
                     });
                 }
             }
```

The piggyback-recovery path now initialises a `PendingProposal`
with only the receiving node's own vote set, matching the normal
proposal path at `src/sim/paxos_pipeline.rs:99-100`.  Previously,
the all-ones bitmap granted instant quorum for any term recovered
via piggyback, without any real vote ever being observed.

## 2. Which Data Must Be Regenerated

The fix changes the behaviour of `paxos_pipeline` (CI) runs that
exercise piggyback recovery.  Every committed CSV containing
`paxos_pipeline,ci` rows with `piggybacks > 0` was AT RISK:

| File | Rows at risk (`piggybacks > 0`) | Total paxos_pipeline,ci rows |
|------|---------------------------------|------------------------------|
| `plots/scalability/results/sweep_summary.csv` | 158 | 300 |
| `plots/topology/results/sweep_summary.csv` | 31 | 75 |

At risk is not the same as changed.  After the post-fix rerun
(data commit `cf05dd8`, landed on main through PR #56, merge
commit `589252a`), the number of `paxos_pipeline,ci`
rows whose values actually changed is:

| File | Rows actually changed |
|------|-----------------------|
| `plots/scalability/results/sweep_summary.csv` | 79 |
| `plots/topology/results/sweep_summary.csv` | 16 |

Counts recorded in PR #56.  Commit `cf05dd8` is not a merge commit
(single parent `d1273fb8275bb4089c64bbf32e131843a75666de`); it is
the data commit "data(sweeps): regenerate sweep_summary.csv after
issue 257 quorum fix" that landed on main through PR #56, whose
merge commit is `589252a`.  The establishing command over that
commit's diff, `git show cf05dd8 -- <file> | grep '^-' |
grep -v '^---' | grep -c paxos_pipeline`, yields 79 (scalability)
and 16 (topology), and the `+` side matches, so these are
replaced-row counts, not insertion counts.  Every changed row has
`piggybacks > 0` (awk `$19>0` over the minus side: 79 of 79
scalability and 16 of 16 topology; command:
`git show cf05dd8 -- <file> | grep '^-' | grep -v '^---' |
grep paxos_pipeline | sed 's/^-//' | awk -F, '$19>0' | wc -l`),
so the change set is a strict subset of the at-risk set, as
expected.

All other protocol/PHY combinations (2pc_pipeline, 2pc_ce,
paxos_ce, tom_pipeline, tom_ce) are unaffected -- the fix touches
only `PaxosPipelineSim::process_round`.

## 3. Rerun Procedure

### Step 1 -- Build the fixed binary

```bash
cargo build --release
```

### Step 2 -- Baseline the current results

Copy the tracked CSVs before anything is deleted, so a diff is
possible after regeneration:

```bash
cp plots/scalability/results/sweep_summary.csv /tmp/scalability_baseline.csv
cp plots/topology/results/sweep_summary.csv /tmp/topology_baseline.csv
```

### Step 3 -- Delete the stale results directories

```bash
rm -rf plots/scalability/results
rm -rf plots/topology/results
```

### Step 4 -- Re-run the scalability sweep

```bash
./target/release/ctsim sweep_scalability.toml
```

This regenerates `plots/scalability/results/sweep_summary.csv`
with all 1800 configurations (6 protocols x 5 network sizes x 4
loss rates x 15 seeds).  Wall-clock cost:
UNKNOWN - REQUIRES A RUN

### Step 5 -- Re-run the topology sweep

```bash
./target/release/ctsim sweep_topology.toml
```

This regenerates `plots/topology/results/sweep_summary.csv` with
all 450 configurations (6 protocols x 5 topologies x 15 seeds).
Wall-clock cost: UNKNOWN - REQUIRES A RUN

### Step 6 -- Diff each regenerated CSV against its baseline

```bash
diff /tmp/scalability_baseline.csv \
     plots/scalability/results/sweep_summary.csv
diff /tmp/topology_baseline.csv \
     plots/topology/results/sweep_summary.csv
```

Only `paxos_pipeline,ci` rows with `piggybacks > 0` should differ.
If any other protocol/PHY row differs, the rerun is suspect.

### Step 7 -- Inspect working tree state

```bash
git status --porcelain
git diff --stat
```

The only modified tracked files should be the two
`sweep_summary.csv` files.

### Step 8 -- What to commit

The `.gitignore` rules relevant to the results directories are
(from `.gitignore:5-6`):

```
/results
/sweep_results
```

These ignore only `<repo-root>/results` and
`<repo-root>/sweep_results`.  The two tracked sweep CSVs live
under `plots/*/results/` and are NOT covered by those rules -- they
were explicitly `git add`-ed when the repository was set up:

```
plots/scalability/results/sweep_summary.csv
plots/topology/results/sweep_summary.csv
```

Commit exactly those two files:

```bash
git add plots/scalability/results/sweep_summary.csv
git add plots/topology/results/sweep_summary.csv
```

Do NOT use `git add -f`.  If `git add` refuses, the file is
gitignored and must not be committed -- investigate first.

### Step 9 -- Regenerate derived audit sources (CAUTION)

The file `docs/validation/paper-audit/sources/per_decision_energy.csv`
is NOT derived from the committed sweep CSV.  Its provenance
(`tools/audit_sources_210b.py`):

  Line 72: `df_sweep = pd.read_csv(... sweep_summary.csv)`
    -> feeds ONLY `slots_per_decision.csv` (line 78) and
       `slots_per_decision.md`.
  Line 107: `df_energy = plot_stacked_bar
       .run_simulation_and_extract_per_proposal(...)`
    -> a FRESH SIMULATOR RUN via the `plots/energy` path,
       not a read of the committed sweep CSV.
  Line 112: `df_energy -> per_decision_energy.csv`

Therefore re-running the two sweeps (Steps 4-5) is NOT sufficient
to refresh `per_decision_energy.csv`, `distribution_stats.*`, or
`integer_multiple_check.md`.  Those require running the
energy/progress path via `tools/audit_sources_210b.py`, which
executes the simulator internally.

WARNING: mixing a fresh-run numerator with a frozen-sweep
denominator is the exact error this repository already rejected.
`docs/validation/paper-audit/sources/proposal_sharing_candidates.md:19`
states: "The withdrawn 4.57% calculation must not be used because
it divided a fresh-run numerator by a frozen-sweep denominator."
The same principle applies here: Step 9 must run AFTER Steps 4-5
have regenerated the sweep CSVs, never against stale sweep data.

Running this step:

```bash
python3 tools/audit_sources_210b.py
```

This step RUNS THE SIMULATOR (plots/progress and plots/energy
paths).  It writes into `docs/validation/paper-audit/sources/`,
whose git blob hashes are pinned in `tests/validation.rs`.

All `tests/validation.rs` line numbers in this document were read at
commit `44588b212574da71cd985842860048d61b29aaf4`; they drift with any
edit to that file, so a bare number is never authoritative.

Complete inventory of pinned blob hashes (all under
`docs/validation/paper-audit/sources/` except the last two; line
numbers from the greps of `sha1_smol`, `assert_blob`, and 40-hex
literals in `tests/validation.rs` at the base of this section; the
Assertion column mixes `assert_blob` call-site lines with inline
`sha1_smol` literal lines, marked "inl" = inline sha1_smol):

| File pinned | Test function | Assertion line(s) | Step 9? |
|-------------|---------------|-------------------|---------|
| per_decision_energy.csv | 210c/27r | 1850, 2281 | YES, changes |
| distribution_stats.csv | 210c/27r | 1854, 2285 | UNKNOWN - REQUIRES A RUN |
| distribution_stats.md | 210c/27r | 1858, 2289 | UNKNOWN - REQUIRES A RUN |
| integer_multiple_check.md | 210c/27r | 1862, 2293 | UNKNOWN - REQUIRES A RUN |
| profiles/calibration.lock.toml | 210c/27r/210b | 1868, 2297, 2032 inl | NO |
| .gitignore | 210c/27r/210b | 1874, 2301, 2021 inl | NO |

Two families of numbers appear here and in Section 5, named by what
they point at: the `assert_blob(` call-site lines (1850, 1854, ...,
2301; also quoted in Section 5's per-file headings), and the
expected-hash literal lines (1852, 1856, ..., 2295; quoted in the
final paragraph of Section 5), which sit two lines below their
matching call site.  Lines 2021 and 2032 belong to neither family:
they are the inline `sha1_smol` literals in `step_210b_assertions`,
which is why they carry the "inl" marker above.  All verified at
the commit named above.  Re-derive each family with:

    grep -n 'assert_blob' tests/validation.rs
    grep -nE '"[0-9a-f]{40}"' tests/validation.rs

Function-to-line assignment (derived from the fn grep; each
assert_blob call site belongs to the enclosing test fn):
1850, 1854, 1858, 1862, 1868, 1874 -> fn at 1774
  (`step_210c_assertions`); 2281, 2285, 2289, 2293, 2297, 2301 ->
  fn at 2039 (`step_27r_assertions`); 2021, 2032 -> fn at 1881
  (`step_210b_assertions`, inline sha1_smol, no assert_blob).

Total: 6 files pinned at 14 pin sites (12 `assert_blob` calls plus
2 inline `sha1_smol` literals at 2021, 2032).  A 15th 40-hex
literal at line 1120 (`e69de29...`) is the empty-blob sanity
constant inside `calibration_lock_evidence_blobs_match_their_files`,
not a file pin.  `step_210b_assertions` owns only the two inline
pins and contains no `assert_blob` call.  The four `sources/`
files are the only pinned files Step 9 can change; `.gitignore`
and `profiles/calibration.lock.toml` cannot be affected by it.

Updating any of these expected hashes is a SEPARATE, OWNER-APPROVED
round (see Step 11 and Section 5).  Do not modify
`tests/validation.rs` in this PR.

Wall-clock cost: UNKNOWN - REQUIRES A RUN

### Step 10 -- Regenerate figures

```bash
python3 tools/regen_figures.py --force
```

This regenerates every plot PNG/PDF and the LaTeX table fragments
from the new CSVs.  The `--force` flag is required because the CSV
content has changed.

### Step 11 -- Verify

```bash
cargo test --all
```

Unit, reproducibility, and regression tests must pass.  However, an
`assert_blob` failure after regenerating the sources directory
(Step 9) is EXPECTED, not a defect, because the derived audit
sources in `docs/validation/paper-audit/sources/` were recomputed.

STEP 2.40 ANNOTATION (added in step 2.39, relabelled in step 2.40;
this paragraph is not part of the original text). The original
prediction is the preceding paragraph beginning "Unit,
reproducibility, and regression tests must pass."  Its status:

- The Step 9 prediction is UNTESTED, not superseded.  Step 9
  (regenerating `docs/validation/paper-audit/sources/` via
  `tools/audit_sources_210b.py`) has never been executed in this
  repository: `git log --oneline --all --grep='regenerate' --
  docs/validation/paper-audit/sources/` returns no commits.  A
  prediction about Step 9 cannot be refuted by an event outside
  Step 9.
- Separately, an unpredicted `assert_blob` failure mode was
  observed outside Step 9.  The tooling commit `5a29d3a`
  ("fix(tooling): track textual evidence (.tex tables) and update
  .gitignore (issue 348)") changed `.gitignore`, and the
  validation suite failed with:

  Blob SHA mismatch for .gitignore
   left: 24022f39d03af223750fd1dc4c25644f60eec61a
   right: 420330edbd2721dd41114c1a8c7653c395a4c7af

  This was repaired by commit `297e9bc` ("test(validation): update
  .gitignore blob hash after issue 348").
- Lesson recorded: `assert_blob` can break from commits unrelated
  to regeneration, so the failure taxonomy in this section is
  incomplete, not wrong.  Moreover, hash pins exist outside
  `assert_blob` (inline `sha1_smol` literals), so a taxonomy
  keyed on `assert_blob` is structurally incomplete.

When an `assert_blob` failure occurs:
- Record the verbatim failure output (test name, expected hash,
  actual hash) into the round report.
- Defer every hash update to a separate, owner-approved round,
  as required by Step 9.
- `tests/validation.rs` MUST NOT be edited in the rerun described
  by this document.

## 4. Timing Constraint from CI Configuration

`.github/workflows/ci.yml:83` contains the comment:

> Permanently disabled: one run costs ~55 min of the free-tier
> allowance.

This refers to one execution of the disabled `regeneration` job
(`.github/workflows/ci.yml:86`, guarded by `if: false`), which
runs on a GitHub-hosted runner.  This is NOT an estimate for a
local machine and NOT an estimate for the individual scalability or
topology sweeps.

`.github/workflows/ci.yml:69` contains:

> The scalability sweep includes N=188 and takes minutes

This is a CI comment, not a measured value.

No committed artifact provides a wall-clock timing for either the
scalability sweep or the topology sweep executed in isolation.
Both are: UNKNOWN - REQUIRES A RUN

## 5. Validation Hashes That Must Be Updated After the Rerun

Every pinned blob hash in `tests/validation.rs`, with rerun
impact (mechanism is `assert_blob` unless marked inline
`sha1_smol`; see the pin inventory in Step 9):

Lines 1850, 2281: `sources/per_decision_energy.csv`
  SHA1 `7386c946...` -- YES, changes (fresh simulator run
  via `tools/audit_sources_210b.py:107,112`; see Step 9)

Lines 1854, 2285: `sources/distribution_stats.csv`
  SHA1 `ace5a6b0...` -- UNKNOWN - REQUIRES A RUN

Lines 1858, 2289: `sources/distribution_stats.md`
  SHA1 `73a554b1...` -- UNKNOWN - REQUIRES A RUN

Lines 1862, 2293: `sources/integer_multiple_check.md`
  SHA1 `7c9cfbe5...` -- UNKNOWN - REQUIRES A RUN

Lines 1868, 2297: `profiles/calibration.lock.toml`
  SHA1 `fd88f784...` -- NO (pins PHY, not protocol)

Lines 1874, 2301: `.gitignore`
  SHA1 `24022f39...` -- NO
  (step 2.40: was `420330ed...`; commit `297e9bc` repinned the
  expected hash to `24022f39...` after the issue-348 tooling
  commit changed `.gitignore`.)

The two inline `sha1_smol` pins for `.gitignore` (line 2021) and
`profiles/calibration.lock.toml` (line 2032) assert the same
hashes as the matching `assert_blob` rows above; update them in
the same owner-approved round if those files ever change.

After regeneration, compute the new blob hashes:

```bash
git hash-object docs/validation/paper-audit/sources/per_decision_energy.csv
git hash-object docs/validation/paper-audit/sources/distribution_stats.csv
git hash-object docs/validation/paper-audit/sources/distribution_stats.md
git hash-object docs/validation/paper-audit/sources/integer_multiple_check.md
```

In the separate, owner-approved round (see Step 9 and Step 11),
update the corresponding expected-hash literals at lines 1852, 1856,
1860, 1864, 2283, 2287, 2291, 2295 in `tests/validation.rs`, and
the inline `sha1_smol` literals at lines 2021 and 2032 should the
`.gitignore` or `profiles/calibration.lock.toml` hashes ever
change.  `tests/validation.rs` must NOT be edited during this
rerun.

## 6. Paper Numbers to Check After the Rerun

Compare the new Table I Paxos(CI) row values against the current
paper text.  Quantities that may change (per `ISSUE_257_IMPACT.md`
sections 3 and 4):

- Table I Paxos(CI): throughput, E/dec, commit rate, latency
- Pipeline depth "about 12" (= throughput x latency)
- Paxos on line topology: throughput "0.0625" -- RESOLVED: measured at
  0.0611 (-2.24% rounded table basis; -2.27% full precision) in 4895efeb
  (paper text updated to 0.0611)
- Fig 3b, Fig 4, Fig 12b: plotted data points

The headline 2PC ratios (throughput and energy) are structurally
unaffected -- they compare `2pc_pipeline` vs `2pc_ce` with no
`paxos_pipeline` data involved.

## 7. What NOT to Change

- `paxos_ce` rows: unaffected (different simulator, no piggyback
  bitmap).
- `2pc_pipeline`, `2pc_ce`, `tom_pipeline`, `tom_ce` rows:
  unaffected.
- `.github/workflows/ci.yml`: the `regeneration` job stays disabled
  (`if: false`) until the rerun is complete and committed.
- `profiles/calibration.lock.toml`: unaffected (pins PHY
  parameters, not protocol).
