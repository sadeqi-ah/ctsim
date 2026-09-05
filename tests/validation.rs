//! Validation-study checks (Layer 1 / Layer 3 support).
//!
//! These tests assert *structural* properties of the model that the
//! validation report relies on. They run no protocol logic and call no
//! existing simulation entry point beyond the public graph builders, so a
//! failure here means a graph builder changed, not that a protocol regressed.

use ctsim::config::NetworkConfig;
use ctsim::event::NodeId;
use ctsim::network::NetworkGraph;
use ctsim::run::build_graph;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

/// The seed set used by both published sweeps (`sweep_topology.toml`,
/// `sweep_scalability.toml`).
const SEEDS: [u64; 15] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];

/// Topology arms of the published topology sweep.
const TOPOLOGIES: [&str; 5] = ["line", "partial_mesh", "random", "scale_free", "full_mesh"];

/// Node counts of the published scalability sweep.
const NODE_COUNTS: [usize; 5] = [6, 13, 27, 54, 188];

/// Size of the largest connected component, found by BFS from node 0's component
/// and then from every unvisited node.
fn component_sizes(graph: &NetworkGraph) -> Vec<usize> {
    let n = graph.num_nodes();
    let mut seen = vec![false; n];
    let mut sizes = Vec::new();
    for start in 0..n {
        if seen[start] {
            continue;
        }
        let mut size = 0usize;
        let mut queue = std::collections::VecDeque::new();
        queue.push_back(start as NodeId);
        seen[start] = true;
        while let Some(u) = queue.pop_front() {
            size += 1;
            for v in graph.neighbors(u) {
                if !seen[v] {
                    seen[v] = true;
                    queue.push_back(v);
                }
            }
        }
        sizes.push(size);
    }
    sizes.sort_unstable_by(|a, b| b.cmp(a));
    sizes
}

fn graph_for(topology: &str, num_nodes: usize, seed: u64) -> NetworkGraph {
    let network = NetworkConfig {
        num_nodes,
        topology: topology.to_string(),
        loss_rate: 0.0,
        graph_file: None,
    };
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    build_graph(&network, &mut rng)
}

/// Risk (a): `diameter()` filters unreachable pairs, so a disconnected graph
/// reports a component diameter rather than infinity and no error is raised.
/// Every graph actually used by the published sweeps must therefore be checked
/// for connectivity explicitly.
#[test]
fn every_published_graph_is_connected() {
    let mut disconnected = Vec::new();

    for topology in TOPOLOGIES {
        for seed in SEEDS {
            let graph = graph_for(topology, 27, seed);
            let sizes = component_sizes(&graph);
            println!(
                "topology={topology:<13} n=27  seed={seed:<3} components={:<2} largest={:<3} diameter={} edges={}",
                sizes.len(),
                sizes[0],
                graph.diameter(),
                graph.edge_count()
            );
            if sizes.len() != 1 {
                disconnected.push(format!("{topology} n=27 seed={seed} components={sizes:?}"));
            }
        }
    }

    for num_nodes in NODE_COUNTS {
        for seed in SEEDS {
            let graph = graph_for("random", num_nodes, seed);
            let sizes = component_sizes(&graph);
            println!(
                "topology=random        n={num_nodes:<4} seed={seed:<3} components={:<2} largest={:<3} diameter={} edges={}",
                sizes.len(),
                sizes[0],
                graph.diameter(),
                graph.edge_count()
            );
            if sizes.len() != 1 {
                disconnected.push(format!(
                    "random n={num_nodes} seed={seed} components={sizes:?}"
                ));
            }
        }
    }

    assert!(
        disconnected.is_empty(),
        "disconnected graphs feed the published sweeps, so their reported diameter is a \
         component diameter and their commit rates are affected:\n{}",
        disconnected.join("\n")
    );
}

/// The connectivity above is not luck: `random_topology` and `partial_mesh` both
/// open by attaching every node `i >= 1` to a uniformly chosen node `< i`, which
/// is a spanning tree, and `scale_free` grows from a complete core by attaching
/// each new node to existing ones. This test pins that reasoning at the node
/// counts the study actually uses.
///
/// HAZARD, deliberately not exercised here: `random_topology`'s second loop is
/// `while adj[i].len() < num_neighbors`, with `num_neighbors` drawn from
/// `min_neighbors..=max_neighbors` (`src/network.rs:291-298`). When
/// `n - 1 < max_neighbors` the condition can never be satisfied and the builder
/// spins forever. With the published bounds (2, 5) that means any `n <= 5`
/// hangs. Every published configuration has `n >= 6`, so no published run is
/// affected, but a future sweep over small `n` would hang rather than fail.
#[test]
fn random_builders_are_connected_by_construction_not_by_degree() {
    for seed in SEEDS {
        for n in [6usize, 13, 27, 54, 180, 188] {
            let mut rng = ChaCha8Rng::seed_from_u64(seed);
            let graph = NetworkGraph::random_topology(n, 2, 5, &mut rng);
            assert_eq!(
                component_sizes(&graph).len(),
                1,
                "random_topology(n={n}, 2, 5) disconnected at seed {seed}"
            );
        }
    }
}
