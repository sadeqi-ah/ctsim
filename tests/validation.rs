//! Validation-study checks (Layer 1 / Layer 3 support).
//!
//! These tests assert *structural* properties of the model that the
//! validation report relies on. They run no protocol logic and call no
//! existing simulation entry point beyond the public graph builders, so a
//! failure here means a graph builder changed, not that a protocol regressed.

use ctsim::config::{CeConfig, CiConfig, NetworkConfig, SimConfig};
use ctsim::event::NodeId;
use ctsim::network::NetworkGraph;
use ctsim::protocol::two_pc_pipeline::{serialize_packet, TwoPcPacket, TwoPcState};
use ctsim::run::{build_graph, make_sim_config, run_experiment};
use ctsim::sim::pure_flood::PureFloodSim;
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
        "disconnected graphs feed the published sweeps, so their reported diameter is a \\
         component diameter and their commit rates are affected:\n{}",
        disconnected.join("\n")
    );
}

/// Decision 19: the snapshot series and the energy counters must agree exactly.
///
/// `node.tick()` charges every node-slot to exactly one of Listen/Flood/Sleep, so
/// `listen + flood + sleep == N * (slots simulated)` identically. The snapshot
/// series is a second accounting of the same slots, and the amortised-energy
/// metric integrates over it (`plots/energy/plot_paper_energy.py:101-125`). If a
/// slot is emitted that was never ticked, or a ticked slot is not emitted, the two
/// disagree and the amortised figures are wrong by that amount.
///
/// Two defects made them disagree before this test existed: `phy/ci.rs` emitted the
/// round-boundary slot with the pre-`reset_round()` all-Sleep state (one row per
/// round, `N` node-slots each, ~1.41x under-count on CI), and both orchestrators
/// emitted a trailing snapshot for the first *free* slot, duplicating one row.
///
/// SCOPE: this invariant is defined at `snapshot_interval = 1` ONLY, which is what
/// these six runs use. At any larger interval the series is a deliberate *sample*
/// and `rows * N == L+F+S` fails by construction — a 455-slot run emits 23 rows at
/// interval 20 (594 node-slots against 12285 charged). The published sweeps use 20
/// and `config.rs:73` defaults to 50, so this test does NOT cover them; the
/// amortised-energy path refuses a sampled series instead
/// (`plots/_common.py::require_per_slot_series`). What this test does not check:
/// any interval but 1, any topology but `random`, any N but 27, and whether the
/// *values* in each row are right — only that every ticked slot is represented
/// exactly once and that the two accountings of it agree.
#[test]
fn snapshot_series_accounts_for_every_ticked_slot() {
    let ce = CeConfig {
        listen_timeout: 5,
        max_round_slots: 300,
    };
    let arms = [
        ("ci", "tom_pipeline"),
        ("ci", "paxos_pipeline"),
        ("ci", "2pc_pipeline"),
        ("ce", "tom_ce"),
        ("ce", "paxos_ce"),
        ("ce", "2pc_ce"),
    ];

    for (phy, protocol) in arms {
        let config = make_sim_config(
            99, phy, protocol, 27, "random", 0.05, 1, &ce, 100, 1, 50_000, 0.0,
        );
        let result = run_experiment(config);
        let s = &result.summary;
        let snaps = &result.metrics.snapshots;

        let awake_ticks = s.total_listen + s.total_flood;
        let awake_snaps: u64 = snaps
            .iter()
            .map(|x| (x.nodes_listening + x.nodes_flooding) as u64)
            .sum();
        assert_eq!(
            awake_ticks, awake_snaps,
            "{protocol}: energy counters charged {awake_ticks} awake node-slots but the \\
             snapshot series accounts for {awake_snaps}"
        );

        let sleep_snaps: u64 = snaps.iter().map(|x| x.nodes_sleeping as u64).sum();
        assert_eq!(sleep_snaps, s.total_sleep, "{protocol}: sleep disagrees");

        // Every ticked slot emitted exactly once: no duplicate rows, contiguous from 0.
        let mut slots: Vec<u64> = snaps.iter().map(|x| x.slot).collect();
        let rows = slots.len();
        slots.sort_unstable();
        slots.dedup();
        assert_eq!(rows, slots.len(), "{protocol}: duplicate snapshot rows");
        assert_eq!(slots[0], 0, "{protocol}: snapshots do not start at slot 0");
        assert_eq!(
            *slots.last().unwrap(),
            rows as u64 - 1,
            "{protocol}: snapshot slots are not contiguous"
        );
        assert_eq!(
            rows as u64 * 27,
            s.total_listen + s.total_flood + s.total_sleep,
            "{protocol}: rows * N != total node-slots charged"
        );
    }
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

/// Maximum payload of one BLE LE Data PDU (Core Spec, LL Data PDU payload field).
const LL_DATA_PDU_MAX_OCTETS: usize = 251;

/// The wire encoding *specified* in `docs/validation/t_slot.md` §5, in octets.
///
/// The 22 fixed octets are transaction_id u32 (4), nack_tx_id u32 (4),
/// piggyback_tx u32 (4), transaction_data `tx{term}` ASCII (8), sender u8 (1),
/// and one octet holding state, abort_flag and piggyback_state packed together
/// (1). The vote bitmap adds `ceil(N/8)` octets on top of those 22.
#[allow(clippy::manual_div_ceil)]
fn wire_payload_len(num_nodes: usize) -> usize {
    (num_nodes + 7) / 8 + 22
}

/// Length of the *internal* JSON carrier for a 2PC packet at N nodes, measured
/// through the real serialiser rather than modelled.
fn json_packet_len(num_nodes: usize) -> usize {
    let pkt = TwoPcPacket {
        transaction_id: 0,
        state: TwoPcState::Prepare,
        flags_bitmap: vec![false; num_nodes],
        abort_flag: false,
        nack_tx_id: 0,
        transaction_data: b"tx0".to_vec(),
        sender: 0,
        piggyback_tx: None,
        piggyback_state: None,
    };
    serialize_packet(&pkt).len()
}

/// Decision 158, part 2 — the packet-length guard.
///
/// `docs/validation/t_slot.md` §5 maps slot counts to wall-clock time through an
/// air-time term `T_air(L) = 44.0 + 4.0 * L` microseconds, which presupposes that
/// one flood packet fits in one LE Data PDU: otherwise the link layer fragments and
/// "one flood occupies one slot" is false. This test pins exactly that
/// presupposition over the whole simulated range, together with the anchor values
/// quoted in the document.
///
/// What it does NOT do: it does not check that the simulator emits this encoding.
/// It cannot, because the simulator emits JSON and consumes no packet length at all
/// (there is no `payload.len()` in the crate). `L_wire` is a specification attached
/// to the time mapping, and this test is a consistency check on that specification.
#[test]
fn specified_wire_packet_fits_in_one_ll_data_pdu() {
    for n in 1..=255usize {
        let len = wire_payload_len(n);
        assert!(
            len <= LL_DATA_PDU_MAX_OCTETS,
            "L_wire({n}) = {len} octets exceeds the {LL_DATA_PDU_MAX_OCTETS}-octet \\
             LE Data PDU payload budget, so a flood would need link-layer fragmentation"
        );
    }

    // Anchors quoted in docs/validation/t_slot.md §5.
    assert_eq!(wire_payload_len(2), 23);
    assert_eq!(wire_payload_len(27), 26);
    assert_eq!(wire_payload_len(180), 45);
    assert_eq!(wire_payload_len(188), 46);
    assert_eq!(wire_payload_len(255), 54);
}

/// The companion half of decision 158: the JSON encoding is an artefact, and it is
/// an artefact that would *not* fit the budget above. That is precisely why the
/// manuscript states the wire encoding as a specification instead of reporting
/// `serialize_packet(..).len()` as a packet size.
///
/// Deliberately asserted as inequalities and orderings, never as exact byte counts:
/// this test must fail if the encoding stops being an over-budget artefact, not
/// merely because a serde version renders a field differently.
#[test]
fn json_carrier_is_an_artefact_not_a_wire_format() {
    let probes = [2usize, 16, 27, 188];
    let lens: Vec<usize> = probes.iter().map(|&n| json_packet_len(n)).collect();
    for (n, len) in probes.iter().zip(&lens) {
        println!("N={n:<4} L_json={len:<6} L_wire={}", wire_payload_len(*n));
    }

    // Grows with N, because the bitmap is rendered as one JSON literal per node.
    for w in lens.windows(2) {
        assert!(
            w[1] > w[0],
            "JSON length is expected to grow with the node count: {lens:?}"
        );
    }

    // Already over the one-PDU budget well inside the simulated range.
    assert!(
        lens[1] > LL_DATA_PDU_MAX_OCTETS,
        "expected the JSON carrier to exceed {LL_DATA_PDU_MAX_OCTETS} octets by N=16, got {}",
        lens[1]
    );

    // And the specified encoding is smaller by an order of magnitude at the sizes
    // the study publishes, which is the whole content of the artefact claim.
    assert!(
        wire_payload_len(188) * 4 < lens[3],
        "expected L_wire(188) = {} to be far below L_json(188) = {}",
        wire_payload_len(188),
        lens[3]
    );
}

/// Step 2.3 — the pure-flood harness must be sound before its curve is read.
///
/// A lossless connected graph has to give total coverage: every non-initiator
/// node is reachable, no transmission is dropped, and the round bound is derived
/// from the diameter, so the flood wave cannot be cut short. A failure here is
/// therefore a bug in the harness (payload provenance, initiator exclusion, round
/// bookkeeping) and not a property of the loss model. No reading of the
/// coverage-vs-loss curve is meaningful until this test is green.
///
/// A `line` graph is used because it is the deterministic worst case for the
/// round bound (diameter `n - 1`) and needs no RNG to construct, so the assertion
/// is exact rather than seed-dependent.
#[test]
fn pure_flood_reaches_every_receiver_on_a_lossless_line() {
    let num_nodes = 27;
    let floods = 5;
    let config = SimConfig {
        seed: 1,
        phy_mode: "ci".to_string(),
        network: NetworkConfig {
            num_nodes,
            topology: "line".to_string(),
            loss_rate: 0.0,
            graph_file: None,
        },
        ci: Some(CiConfig {
            flood_repeats: 1,
            round_slots: None,
        }),
        ce: None,
        protocol: "pure_flood".to_string(),
        num_proposals: floods,
        snapshot_interval: 1_000_000,
        max_slots: 100_000,
        abort_probability: 0.0,
        quiet: true,
    };

    let graph = NetworkGraph::line(num_nodes);
    let mut sim = PureFloodSim::new(config, graph);
    let report = sim.run();

    assert_eq!(
        report.receiver_opportunities,
        floods * (num_nodes - 1),
        "expected {floods} floods x {} receivers",
        num_nodes - 1
    );
    assert_eq!(
        report.coverage,
        1.0,
        "lossless line left {} of {} receivers uncovered",
        report.receiver_opportunities - report.receivers_covered,
        report.receiver_opportunities
    );
}

/// Addition 12: the frozen adjacency files under `profiles/graphs/` must
/// reproduce the random topologies that `build_graph` generates from each seed.
///
/// This guards against DOT-to-adjacency conversion errors (section 4.3 of the
/// addition-12 prompt). The test is fast: it builds 15 in-memory graphs and
/// loads 15 small text files, with no simulation runs.
#[test]
fn frozen_graph_files_reproduce_the_published_random_topologies() {
    use std::path::Path;

    for &seed in &SEEDS {
        let mut rng = ChaCha8Rng::seed_from_u64(seed);
        let expected = NetworkGraph::random_topology(27, 2, 5, &mut rng);

        let graph_path = format!("profiles/graphs/random_n27_seed{seed}.txt");
        let loaded = NetworkGraph::from_file(Path::new(&graph_path))
            .unwrap_or_else(|e| panic!("failed to load {graph_path}: {e}"));

        assert_eq!(
            expected.num_nodes(),
            loaded.num_nodes(),
            "seed {seed}: num_nodes mismatch"
        );
        assert_eq!(
            expected.edge_count(),
            loaded.edge_count(),
            "seed {seed}: edge_count mismatch ({} vs {})",
            expected.edge_count(),
            loaded.edge_count()
        );
        assert_eq!(
            expected.diameter(),
            loaded.diameter(),
            "seed {seed}: diameter mismatch"
        );

        for i in 0..expected.num_nodes() {
            assert_eq!(
                expected.neighbors(i),
                loaded.neighbors(i),
                "seed {seed}: neighbors({i}) differ"
            );
        }
    }
}
