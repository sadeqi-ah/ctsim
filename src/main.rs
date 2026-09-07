//! CTSim CLI entry point.

use ctsim::config::SimConfig;
use ctsim::network::NetworkGraph;
use ctsim::sim::paxos_pipeline::PaxosPipelineSim;
use ctsim::sim::tom_pipeline::TomPipelineSim;
use ctsim::sim::two_pc_pipeline::TwoPcPipelineSim;
use rand::SeedableRng;
use std::path::Path;

fn build_graph(config: &SimConfig, rng: &mut rand_chacha::ChaCha8Rng) -> NetworkGraph {
    if let Some(ref path) = config.network.graph_file {
        return NetworkGraph::from_file(Path::new(path)).expect("Failed to load graph file");
    }
    let n = config.network.num_nodes;
    match config.network.topology.as_str() {
        "full_mesh" => NetworkGraph::full_mesh(n),
        "line" => NetworkGraph::line(n),
        "star" => NetworkGraph::star(n),
        "grid" => {
            let side = (n as f64).sqrt().ceil() as usize;
            NetworkGraph::grid(side, side)
        }
        "ring" => NetworkGraph::ring(n),
        "tree" => NetworkGraph::tree(n, 3),
        "scale_free" => NetworkGraph::scale_free(n, 2, rng),
        "random" => NetworkGraph::random_topology(n, 2, 5, rng),
        "partial_mesh" => NetworkGraph::partial_mesh(n, 0.3, rng),
        other => panic!("Unknown topology: {other}"),
    }
}

fn export_pair(metrics: &ctsim::metrics::MetricsCollector, results: &str, snapshots: &str) {
    std::fs::create_dir_all("results").unwrap_or_default();
    if let Err(e) = metrics.export_csv(Path::new(results)) {
        eprintln!("Failed to export {results}: {e}");
    }
    if let Err(e) = metrics.export_snapshots_csv(Path::new(snapshots)) {
        eprintln!("Failed to export {snapshots}: {e}");
    }
    println!("Exported: {results}, {snapshots}");
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let config_path = args
        .get(1)
        .map(|s| s.as_str())
        .unwrap_or("examples/paxos_ci.toml");

    if config_path.contains("sweep") {
        let sweep_cfg = ctsim::sweep_config::SweepConfig::from_file(Path::new(config_path))
            .unwrap_or_else(|e| panic!("Sweep config error: {e}"));
        ctsim::sweep_runner::run_sweep(sweep_cfg);
        return;
    }

    let config = SimConfig::from_file(Path::new(config_path))
        .unwrap_or_else(|e| panic!("Config error: {e}"));

    let mut rng = rand_chacha::ChaCha8Rng::seed_from_u64(config.seed);
    let graph = build_graph(&config, &mut rng);

    // Topology visuals (always; deterministic for fixed seed on random topologies).
    std::fs::create_dir_all("results").unwrap_or_default();
    match graph.export_visuals(Path::new("results"), "topology") {
        Ok((dot, svg)) => {
            println!(
                "Topology: n={} edges={} diameter={} → {}, {}",
                graph.num_nodes(),
                graph.edge_count(),
                graph.diameter(),
                dot.display(),
                svg.display()
            );
        }
        Err(e) => eprintln!("Failed to export topology visuals: {e}"),
    }

    let protocol = config.protocol.as_str();

    match protocol {
        "paxos_pipeline" => {
            let mut sim = PaxosPipelineSim::new(config, graph);
            let (m, _, _, _) = sim.run();
            export_pair(
                &m,
                "results/results_paxos.csv",
                "results/snapshots_paxos.csv",
            );
        }
        "2pc_pipeline" => {
            let mut sim = TwoPcPipelineSim::new(config, graph);
            let (m, _, _, _) = sim.run();
            export_pair(
                &m,
                "results/results_2pc.csv",
                "results/snapshots_2pc.csv",
            );
        }
        "tom_pipeline" => {
            let mut sim = TomPipelineSim::new(config, graph);
            let (m, _, _, _) = sim.run();
            export_pair(
                &m,
                "results/results_tom.csv",
                "results/snapshots_tom.csv",
            );
        }
        "pure_flood" => {
            let mut sim = ctsim::sim::pure_flood::PureFloodSim::new(config, graph);
            sim.run();
        }
        "paxos_ce" => {
            let mut protocol = Box::new(ctsim::protocol::paxos_ce::PaxosCE::new());
            let mut sim = ctsim::sim::Simulator::new(config, graph);
            sim.run(protocol.as_mut());
            export_pair(
                &sim.metrics,
                "results/results_paxos_ce.csv",
                "results/snapshots_paxos_ce.csv",
            );
        }
        "2pc_ce" => {
            let mut protocol = Box::new(ctsim::protocol::two_pc_ce::TwoPcCE::new(
                config.abort_probability,
                config.seed,
            ));
            let mut sim = ctsim::sim::Simulator::new(config, graph);
            sim.run(protocol.as_mut());
            export_pair(
                &sim.metrics,
                "results/results_2pc_ce.csv",
                "results/snapshots_2pc_ce.csv",
            );
        }
        "tom_ce" => {
            let mut protocol = Box::new(ctsim::protocol::tom_ce::TomCE::new());
            let mut sim = ctsim::sim::Simulator::new(config, graph);
            sim.run(protocol.as_mut());
            export_pair(
                &sim.metrics,
                "results/results_tom_ce.csv",
                "results/snapshots_tom_ce.csv",
            );
        }
        other => panic!(
            "Unknown protocol: {other}. Available: paxos_pipeline, 2pc_pipeline, tom_pipeline, paxos_ce, 2pc_ce, tom_ce, pure_flood"
        ),
    }
}
