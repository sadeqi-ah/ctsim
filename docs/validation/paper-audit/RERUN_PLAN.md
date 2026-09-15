# Issue 257 — Post-Fix Rerun Plan

## What Changed

One line in `src/sim/paxos_pipeline.rs:247`:

```diff
-                        bitmap: vec![true; num_nodes],
+                        let mut bitmap = vec![false; num_nodes];
+                        bitmap[i] = true; // only the receiving node's own vote
```

The piggyback-recovery path now initialises a `PendingProposal` with only the
receiving node's own vote set, matching the normal proposal path at line 99.
Previously, the all-ones bitmap granted instant quorum for any term recovered
via piggyback, without any real vote ever being observed.

## Which Data Must Be Regenerated

The fix changes the behaviour of `paxos_pipeline` (CI) runs that exercise
piggyback recovery. Every committed CSV containing `paxos_pipeline,ci` rows
with `piggybacks > 0` is stale:

| File | Stale rows | Total rows | Evidence |
|------|-----------|------------|----------|
| `plots/scalability/results/sweep_summary.csv` | 158 | 300 paxos_pipeline,ci rows (of 1800 total) | `awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $19>0' | wc -l` → 158 |
| `plots/topology/results/sweep_summary.csv` | 31 | 75 paxos_pipeline,ci rows (of 450 total) | `awk -F, 'NR>1 && $6=="paxos_pipeline" && $7=="ci" && $19>0' | wc -l` → 31 |

All other rows (2pc_pipeline, 2pc_ce, paxos_ce, tom_pipeline, tom_ce) are
unaffected — the fix touches only `PaxosPipelineSim::process_round`.

## Rerun Procedure

### Step 1 — Build the fixed binary

```bash
cargo build --release
```

### Step 2 — Re-run the scalability sweep

```bash
./target/release/ctsim sweep_scalability.toml
```

This overwrites `plots/scalability/results/sweep_summary.csv` with all 1800
configurations (all protocols × all PHY modes × all seeds). Wall-clock cost:
UNKNOWN — REQUIRES A RUN.

### Step 3 — Re-run the topology sweep

```bash
./target/release/ctsim sweep_topology.toml
```

This overwrites `plots/topology/results/sweep_summary.csv` with all 450
configurations. Wall-clock cost: < 1 minute (CI runs this twice in ~2 min;
`.github/workflows/ci.yml:48–55`).

### Step 4 — Regenerate all figures and tables

```bash
python3 tools/regen_figures.py --force
```

This regenerates every plot PNG/PDF and the LaTeX table fragments from the
new CSVs. The `--force` flag is required because the CSV content has changed.

### Step 5 — Update validation hashes

The `assert_blob` SHA1 literals in `tests/validation.rs` that pin sweep CSV
content will need updating. At minimum:

- The blob hash for `per_decision_energy.csv` (currently
  `7386c9467760b7c4bacb50d30705dfc7f00b0e8f` at `tests/validation.rs:1852`
  and `:2283`) will change because it is derived from `sweep_summary.csv`.
- Both `sweep_summary.csv` blob hashes will change.

After regeneration:

```bash
# Get new blob hash for each changed file:
git hash-object plots/scalability/results/sweep_summary.csv
git hash-object plots/topology/results/sweep_summary.csv
git hash-object docs/validation/paper-audit/sources/per_decision_energy.csv

# Update the corresponding assert_blob calls in tests/validation.rs.
```

### Step 6 — Verify

```bash
cargo test --all
```

All tests must pass, including the reproducibility and validation suites.
Any test that pins a specific numeric value from `paxos_pipeline,ci` rows may
need its expected value updated.

### Step 7 — Update paper numbers if they moved

Compare the new Table I Paxos(CI) row values against the current paper text.
The quantities that may change (per `ISSUE_257_IMPACT.md` §3 and §4):

- Table I Paxos(CI): throughput, E/dec, commit rate, latency
- Pipeline depth "about 12" (= throughput × latency)
- Paxos on line topology: throughput "0.0625"
- Fig 3b, Fig 4, Fig 12b: plotted data points

The headline 2PC ratios (4.083× throughput, 5.672× energy) are structurally
unaffected — they compare `2pc_pipeline` vs `2pc_ce` with no `paxos_pipeline`
data involved.

## What NOT to Change

- `paxos_ce` rows: unaffected (different simulator, no piggyback bitmap).
- `2pc_pipeline`, `2pc_ce`, `tom_pipeline`, `tom_ce` rows: unaffected.
- `.github/workflows/ci.yml`: the `regeneration` job stays disabled (`if: false`)
  until the rerun is complete and committed.
- `profiles/calibration.lock.toml`: unaffected (pins PHY parameters, not protocol).
