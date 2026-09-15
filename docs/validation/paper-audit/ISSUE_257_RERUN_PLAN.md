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
`paxos_pipeline,ci` rows with `piggybacks > 0` is stale:

| File | Stale rows | Total paxos_pipeline,ci rows |
|------|-----------|------------------------------|
| `plots/scalability/results/sweep_summary.csv` | 158 | 300 |
| `plots/topology/results/sweep_summary.csv` | 31 | 75 |

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

### Step 9 -- Regenerate derived audit sources

The file `docs/validation/paper-audit/sources/per_decision_energy.csv`
is generated from `plots/scalability/results/sweep_summary.csv` by
`tools/audit_sources_210b.py:72` (reads the sweep CSV) and `:112`
(writes the derived CSV).  After the sweep CSV changes:

```bash
python3 tools/audit_sources_210b.py
```

Then verify or update the assert_blob SHA in `tests/validation.rs`
(see section 5 below).

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

All tests must pass.  If any assert_blob or numeric assertion
fails, update the expected value and document the change.

## 4. Timing Constraint from CI Configuration

`.github/workflows/ci.yml:83` contains the comment:

> Permanently disabled: one run costs ~55 min of the free-tier
> allowance.

This refers to one execution of the disabled `regeneration` job
(`.github/workflows/ci.yml:85-86`, guarded by `if: false`), which
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

Every `assert_blob` call in `tests/validation.rs` and the file
it hashes, with rerun impact:

Lines 1850, 2281: `sources/per_decision_energy.csv`
  SHA1 `7386c946...` -- YES, changes (derived from sweep CSV)

Lines 1854, 2285: `sources/distribution_stats.csv`
  SHA1 `ace5a6b0...` -- UNKNOWN - REQUIRES A RUN

Lines 1858, 2289: `sources/distribution_stats.md`
  SHA1 `73a554b1...` -- UNKNOWN - REQUIRES A RUN

Lines 1862, 2293: `sources/integer_multiple_check.md`
  SHA1 `7c9cfbe5...` -- UNKNOWN - REQUIRES A RUN

Lines 1868, 2297: `profiles/calibration.lock.toml`
  SHA1 `fd88f784...` -- NO (pins PHY, not protocol)

Lines 1874, 2301: `.gitignore`
  SHA1 `420330ed...` -- NO

After regeneration, compute the new blob hashes:

```bash
git hash-object docs/validation/paper-audit/sources/per_decision_energy.csv
git hash-object docs/validation/paper-audit/sources/distribution_stats.csv
git hash-object docs/validation/paper-audit/sources/distribution_stats.md
git hash-object docs/validation/paper-audit/sources/integer_multiple_check.md
```

Update the corresponding `assert_blob` calls at lines 1852, 1856,
1860, 1864, 2283, 2287, 2291, 2295 in `tests/validation.rs`.

## 6. Paper Numbers to Check After the Rerun

Compare the new Table I Paxos(CI) row values against the current
paper text.  Quantities that may change (per `ISSUE_257_IMPACT.md`
sections 3 and 4):

- Table I Paxos(CI): throughput, E/dec, commit rate, latency
- Pipeline depth "about 12" (= throughput x latency)
- Paxos on line topology: throughput "0.0625"
- Fig 3b, Fig 4, Fig 12b: plotted data points

The headline 2PC ratios (4.083x throughput, 5.672x energy) are
structurally unaffected -- they compare `2pc_pipeline` vs `2pc_ce`
with no `paxos_pipeline` data involved.

## 7. What NOT to Change

- `paxos_ce` rows: unaffected (different simulator, no piggyback
  bitmap).
- `2pc_pipeline`, `2pc_ce`, `tom_pipeline`, `tom_ce` rows:
  unaffected.
- `.github/workflows/ci.yml`: the `regeneration` job stays disabled
  (`if: false`) until the rerun is complete and committed.
- `profiles/calibration.lock.toml`: unaffected (pins PHY
  parameters, not protocol).
