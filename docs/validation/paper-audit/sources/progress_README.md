Reference operating point: N=27, topology=random, loss_rate=0.05, num_proposals=100
Config files used:
- plots/progress/sim_paxos_pipeline_progress.toml
- plots/progress/sim_2pc_pipeline_progress.toml
- plots/progress/sim_tom_pipeline_progress.toml
- plots/progress/sim_paxos_ce_progress.toml
- plots/progress/sim_2pc_ce_progress.toml
- plots/progress/sim_tom_ce_progress.toml
Commit SHA: 3383773f2f72ffcf46414acd6c08891282a61ef9
- Paxos (CI): final decisions=99, max slot=515
- 2PC (CI): final decisions=99, max slot=587
- TOM (CI): final decisions=99, max slot=454
- Paxos (CE): final decisions=99, max slot=1383
- 2PC (CE): final decisions=99, max slot=2371
- TOM (CE): final decisions=99, max slot=466

## Snapshot vs run totals
- Paxos (CI): snapshot at slot 490 has progress_count=99. results_paxos.csv has 100 committed proposals. Agree: False
- 2PC (CI): snapshot at slot 547 has progress_count=99. results_2pc.csv has 100 committed proposals. Agree: False
- TOM (CI): snapshot at slot 434 has progress_count=99. results_tom.csv has 100 committed proposals. Agree: False
- Paxos (CE): snapshot at slot 1363 has progress_count=99. results_paxos_ce.csv has 100 committed proposals. Agree: False
- 2PC (CE): snapshot at slot 2302 has progress_count=99. results_2pc_ce.csv has 100 committed proposals. Agree: False
- TOM (CE): snapshot at slot 435 has progress_count=99. results_tom_ce.csv has 100 committed proposals. Agree: False

The evidence supports explanation (ii): the snapshot series is truncated before the final decision is recorded. The final decision commits at the end_slot of the run, but the snapshot series does not contain a snapshot *after* that slot is completed, so the 100th decision is missing from the snapshots.
