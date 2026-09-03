//! Single-experiment runner shared by CLI and sweep.

use crate::config::{CeConfig, CiConfig, NetworkConfig, SimConfig};
use crate::metrics::MetricsCollector;
use crate::network::NetworkGraph;
use crate::protocol::ProposalOutcome;
use crate::sim::paxos_pipeline::PaxosPipelineSim;
use crate::sim::tom_pipeline::TomPipelineSim;
use crate::sim::two_pc_pipeline::TwoPcPipelineSim;
use crate::sim::Simulator;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use std::path::Path;

/// Aggregate numbers useful for analysis / sweep summary.
#[derive(Debug, Clone)]
pub struct RunSummary {
    pub protocol: String,
    pub phy_mode: String,
    pub seed: u64,
    pub num_nodes: usize,
    pub topology: String,
    pub loss_rate: f64,
    pub flood_repeats: u32,
    pub listen_timeout: u64,
    pub max_round_slots: u64,
    pub diameter: usize,
    pub edge_count: usize,
    pub num_proposals: usize,
    pub committed: usize,
    pub aborted: usize,
    pub timed_out: usize,
    pub avg_latency_committed: f64,
    pub total_listen: u64,
    pub total_flood: u64,
    pub total_sleep: u64,
    pub nacks_sent: u64,
    pub piggybacks_sent: u64,
    pub ce_timeouts: u64,
    pub end_slot: u64,
}

/// Full result of one simulation.
pub struct RunResult {
    pub summary: RunSummary,
    pub metrics: MetricsCollector,
}

/// Build undirected graph from network config + seeded RNG (for random topologies).
pub fn build_graph(network: &NetworkConfig, rng: &mut ChaCha8Rng) -> NetworkGraph {
    if let Some(ref path) = network.graph_file {
        return NetworkGraph::from_file(Path::new(path)).expect("Failed to load graph file");
    }
    let n = network.num_nodes;
    match network.topology.as_str() {
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

fn summarize(
    config: &SimConfig,
    graph: &NetworkGraph,
    metrics: &MetricsCollector,
    total_listen: u64,
    total_flood: u64,
    total_sleep: u64,
) -> RunSummary {
    let committed = metrics
        .proposals
        .iter()
        .filter(|p| p.outcome == ProposalOutcome::Committed)
        .count();
    let aborted = metrics
        .proposals
        .iter()
        .filter(|p| p.outcome == ProposalOutcome::Aborted)
        .count();
    let timed_out = metrics
        .proposals
        .iter()
        .filter(|p| p.outcome == ProposalOutcome::TimedOut)
        .count();
    let avg_latency_committed = if committed > 0 {
        metrics
            .proposals
            .iter()
            .filter(|p| p.outcome == ProposalOutcome::Committed)
            .map(|p| p.latency)
            .sum::<u64>() as f64
            / committed as f64
    } else {
        0.0
    };
    let mut_metrics = metrics.clone(); // Clone is cheap here, but we could pass it by value
                                       // If mut_metrics has total_listen set, use it; otherwise use the arguments (for CE paths)
    let (l, f, s) = if mut_metrics.total_listen > 0 || mut_metrics.total_flood > 0 {
        (
            mut_metrics.total_listen,
            mut_metrics.total_flood,
            mut_metrics.total_sleep,
        )
    } else {
        (total_listen, total_flood, total_sleep)
    };
    let end_slot = metrics
        .proposals
        .iter()
        .map(|p| p.end_slot)
        .max()
        .unwrap_or(0);

    RunSummary {
        protocol: config.protocol.clone(),
        phy_mode: config.phy_mode.clone(),
        seed: config.seed,
        num_nodes: config.network.num_nodes,
        topology: config.network.topology.clone(),
        loss_rate: config.network.loss_rate,
        flood_repeats: config.ci.as_ref().map(|c| c.flood_repeats).unwrap_or(0),
        listen_timeout: config.ce.as_ref().map(|c| c.listen_timeout).unwrap_or(0),
        max_round_slots: config.ce.as_ref().map(|c| c.max_round_slots).unwrap_or(0),
        diameter: graph.diameter(),
        edge_count: graph.edge_count(),
        num_proposals: config.num_proposals,
        committed,
        aborted,
        timed_out,
        avg_latency_committed,
        total_listen: l,
        total_flood: f,
        total_sleep: s,
        nacks_sent: metrics.nacks_sent,
        piggybacks_sent: metrics.piggybacks_sent,
        ce_timeouts: metrics.ce_timeouts,
        end_slot,
    }
}

/// Run one experiment. Graph is built with `config.seed` for random topologies;
/// simulators re-seed from the same value for protocol/PHY randomness.
pub fn run_experiment(config: SimConfig) -> RunResult {
    let mut graph_rng = ChaCha8Rng::seed_from_u64(config.seed);
    let graph = build_graph(&config.network, &mut graph_rng);
    let diameter = graph.diameter();
    let edge_count = graph.edge_count();

    let protocol = config.protocol.as_str();
    let (metrics, listen, flood, sleep) = match protocol {
        "paxos_pipeline" => {
            let mut sim = PaxosPipelineSim::new(config.clone(), graph);
            let (m, l, f, s) = sim.run();
            (m, l, f, s)
        }
        "2pc_pipeline" => {
            let mut sim = TwoPcPipelineSim::new(config.clone(), graph);
            let (m, l, f, s) = sim.run();
            (m, l, f, s)
        }
        "tom_pipeline" => {
            let mut sim = TomPipelineSim::new(config.clone(), graph);
            let (m, l, f, s) = sim.run();
            (m, l, f, s)
        }
        "paxos_ce" => {
            let mut protocol = Box::new(crate::protocol::paxos_ce::PaxosCE::new());
            let mut sim = Simulator::new(config.clone(), graph);
            sim.run(protocol.as_mut());
            let l: u64 = sim.nodes.iter().map(|n| n.slots_listen).sum();
            let f: u64 = sim.nodes.iter().map(|n| n.slots_flood).sum();
            let s: u64 = sim.nodes.iter().map(|n| n.slots_sleep).sum();
            (sim.metrics, l, f, s)
        }
        "2pc_ce" => {
            let mut protocol = Box::new(crate::protocol::two_pc_ce::TwoPcCE::new(
                config.abort_probability,
                config.seed,
            ));
            let mut sim = Simulator::new(config.clone(), graph);
            sim.run(protocol.as_mut());
            let l: u64 = sim.nodes.iter().map(|n| n.slots_listen).sum();
            let f: u64 = sim.nodes.iter().map(|n| n.slots_flood).sum();
            let s: u64 = sim.nodes.iter().map(|n| n.slots_sleep).sum();
            (sim.metrics, l, f, s)
        }
        "tom_ce" => {
            let mut protocol = Box::new(crate::protocol::tom_ce::TomCE::new());
            let mut sim = Simulator::new(config.clone(), graph);
            sim.run(protocol.as_mut());
            let l: u64 = sim.nodes.iter().map(|n| n.slots_listen).sum();
            let f: u64 = sim.nodes.iter().map(|n| n.slots_flood).sum();
            let s: u64 = sim.nodes.iter().map(|n| n.slots_sleep).sum();
            (sim.metrics, l, f, s)
        }
        other => panic!(
            "Unknown protocol: {other}. Available: paxos_pipeline, 2pc_pipeline, tom_pipeline, paxos_ce, 2pc_ce, tom_ce"
        ),
    };

    // Rebuild diameter/edge for summary (graph moved). Recompute from config.
    let mut graph_rng2 = ChaCha8Rng::seed_from_u64(config.seed);
    let graph2 = build_graph(&config.network, &mut graph_rng2);
    let _ = (diameter, edge_count); // same as graph2
    let summary = summarize(&config, &graph2, &metrics, listen, flood, sleep);
    RunResult { summary, metrics }
}

/// Helper to construct a SimConfig for one sweep cell.
// ponytail: flat parameters mirror the sweep grid axes; only the sweep runner
// calls this, so a builder struct would add indirection without a second user.
#[allow(clippy::too_many_arguments)]
pub fn make_sim_config(
    seed: u64,
    phy_mode: &str,
    protocol: &str,
    num_nodes: usize,
    topology: &str,
    loss_rate: f64,
    flood_repeats: u32,
    ce: &CeConfig,
    num_proposals: usize,
    snapshot_interval: u64,
    max_slots: u64,
    abort_probability: f64,
) -> SimConfig {
    SimConfig {
        seed,
        phy_mode: phy_mode.to_string(),
        network: NetworkConfig {
            num_nodes,
            topology: topology.to_string(),
            loss_rate,
            graph_file: None,
        },
        ci: if phy_mode == "ci" {
            Some(CiConfig {
                flood_repeats,
                round_slots: None,
            })
        } else {
            None
        },
        ce: if phy_mode == "ce" {
            Some(ce.clone())
        } else {
            None
        },
        protocol: protocol.to_string(),
        num_proposals,
        snapshot_interval,
        max_slots,
        abort_probability,
        quiet: true,
    }
}
