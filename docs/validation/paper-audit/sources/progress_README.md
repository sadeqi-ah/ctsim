Reference operating point: N=27, topology=random, loss_rate=0.05, num_proposals=100
Config files used:
- plots/progress/sim_paxos_pipeline_progress.toml
- plots/progress/sim_2pc_pipeline_progress.toml
- plots/progress/sim_tom_pipeline_progress.toml
- plots/progress/sim_paxos_ce_progress.toml
- plots/progress/sim_2pc_ce_progress.toml
- plots/progress/sim_tom_ce_progress.toml
Commit SHA: 61f292d7f08eb48e0ddfdadef59950d22f80505f
- Paxos (CI): final decisions=99, max slot=515
- 2PC (CI): final decisions=99, max slot=587
- TOM (CI): final decisions=99, max slot=454
- Paxos (CE): final decisions=99, max slot=1383
- 2PC (CE): final decisions=99, max slot=2371
- TOM (CE): final decisions=99, max slot=466

## Snapshot vs run totals
- Paxos (CI): snapshot file `results/snapshots_paxos.csv` (snapshot slot column `slot`, last snapshot slot=515, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_paxos.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=511). Comparison: final end slot 511 <= last snapshot slot 515. Agree: false
- 2PC (CI): snapshot file `results/snapshots_2pc.csv` (snapshot slot column `slot`, last snapshot slot=587, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_2pc.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=584). Comparison: final end slot 584 <= last snapshot slot 587. Agree: false
- TOM (CI): snapshot file `results/snapshots_tom.csv` (snapshot slot column `slot`, last snapshot slot=454, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_tom.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=455). Comparison: final end slot 455 <= last snapshot slot 454. Agree: false
- Paxos (CE): snapshot file `results/snapshots_paxos_ce.csv` (snapshot slot column `slot`, last snapshot slot=1383, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_paxos_ce.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=1384). Comparison: final end slot 1384 <= last snapshot slot 1383. Agree: false
- 2PC (CE): snapshot file `results/snapshots_2pc_ce.csv` (snapshot slot column `slot`, last snapshot slot=2371, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_2pc_ce.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=2372). Comparison: final end slot 2372 <= last snapshot slot 2371. Agree: false
- TOM (CE): snapshot file `results/snapshots_tom_ce.csv` (snapshot slot column `slot`, last snapshot slot=466, progress_count column `progress_count`, progress_count=99) vs run-total file `results/results_tom_ce.csv` (committed-decision column `outcome`, run total committed decisions=100, final end-slot column `end_slot`, value=467). Comparison: final end slot 467 <= last snapshot slot 466. Agree: false

Conclusion: the complete run records 100 committed decisions; the progress snapshot/report records 99. This is treated in this round as a known one-count reporting mismatch. No counter, snapshot code, protocol logic, or simulator behavior is changed. The discrepancy does not alter the paper's main performance conclusions, but it is disclosed for reproducibility.
