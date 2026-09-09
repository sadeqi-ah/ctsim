use ctsim::config::{CeConfig, NetworkConfig, SimConfig};
use ctsim::run::run_experiment;

fn main() {
    let mut first_non_committed = None;
    for loss_i in (5..=50).step_by(5) {
        let loss = loss_i as f64 / 100.0;
        let config = SimConfig {
            seed: 2, // channel_seed = 2
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

        println!("Running at loss = {}", loss);
        let report = run_experiment(config);

        if report.summary.aborted > 0 || report.summary.timed_out > 0 {
            first_non_committed = Some(loss);
            break;
        }
    }

    if let Some(l) = first_non_committed {
        println!("RESULT: first non-committed outcome at loss = {:.2}", l);
    } else {
        println!("RESULT: no non-committed outcome up to loss = 0.50");
    }
}
