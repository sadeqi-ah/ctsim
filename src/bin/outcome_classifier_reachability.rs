use ctsim::config::{CeConfig, NetworkConfig, SimConfig};
use ctsim::run::run_experiment;

fn main() {
    println!("Configuration: a2_sensys17, 2pc_ce, n=180, arm dense, graph_seed=2, channel_seed=2, proposals=20, abort_probability=0.0");
    println!("\n=== Validation Configuration (max_round_slots=4000) ===");
    for loss_i in (5..=50).step_by(5) {
        let loss = loss_i as f64 / 100.0;
        let config = SimConfig {
            seed: 2,
            phy_mode: "ce".to_string(),
            protocol: "2pc_ce".to_string(),
            network: NetworkConfig {
                num_nodes: 180,
                topology: "random".to_string(),
                loss_rate: loss,
                graph_file: Some("profiles/graphs/random_n180_dense_seed2.txt".to_string()),
            },
            ci: None,
            ce: Some(CeConfig {
                listen_timeout: 5,
                max_round_slots: 4000,
            }),
            num_proposals: 20,
            snapshot_interval: 1_000_000,
            max_slots: 5_000_000,
            abort_probability: 0.0,
            quiet: true,
        };

        let report = run_experiment(config);
        let s = report.summary;
        let lats: Vec<u64> = report.metrics.proposals.iter().map(|p| p.latency).collect();
        let mean = if lats.is_empty() {
            0.0
        } else {
            lats.iter().sum::<u64>() as f64 / lats.len() as f64
        };
        let max = lats.iter().copied().max().unwrap_or(0);

        println!(
            "Loss = {:.2} | C/A/T: {}/{}/{} | Mean round: {:.2} slots | Max round: {} slots",
            loss, s.committed, s.aborted, s.timed_out, mean, max
        );
    }

    println!(
        "\n=== Diagnostic Arm (max_round_slots=200) - NOT part of validation configuration ==="
    );
    for loss_i in (5..=50).step_by(5) {
        let loss = loss_i as f64 / 100.0;
        let config = SimConfig {
            seed: 2,
            phy_mode: "ce".to_string(),
            protocol: "2pc_ce".to_string(),
            network: NetworkConfig {
                num_nodes: 180,
                topology: "random".to_string(),
                loss_rate: loss,
                graph_file: Some("profiles/graphs/random_n180_dense_seed2.txt".to_string()),
            },
            ci: None,
            ce: Some(CeConfig {
                listen_timeout: 5,
                max_round_slots: 200,
            }),
            num_proposals: 20,
            snapshot_interval: 1_000_000,
            max_slots: 5_000_000,
            abort_probability: 0.0,
            quiet: true,
        };

        let report = run_experiment(config);
        let s = report.summary;
        let lats: Vec<u64> = report.metrics.proposals.iter().map(|p| p.latency).collect();
        let mean = if lats.is_empty() {
            0.0
        } else {
            lats.iter().sum::<u64>() as f64 / lats.len() as f64
        };
        let max = lats.iter().copied().max().unwrap_or(0);

        println!(
            "Loss = {:.2} | C/A/T: {}/{}/{} | Mean round: {:.2} slots | Max round: {} slots",
            loss, s.committed, s.aborted, s.timed_out, mean, max
        );
    }
}
