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

// ---------------------------------------------------------------------------
// Addition 14 — calibration lock, blind-prediction failure, and slot lengths
// ---------------------------------------------------------------------------

/// Helper: read a TOML file from disk and return its parsed Value.
fn read_toml(path: &str) -> toml::Value {
    let text = std::fs::read_to_string(path).unwrap_or_else(|e| panic!("cannot read {path}: {e}"));
    text.parse::<toml::Value>()
        .unwrap_or_else(|e| panic!("cannot parse {path} as TOML: {e}"))
}

/// Helper: assert two f64s are equal within a tolerance, with a descriptive message.
fn assert_f64_eq(actual: f64, expected: f64, tol: f64, file: &str, key: &str) {
    assert!(
        (actual - expected).abs() < tol,
        "{file}: {key} = {actual}, expected {expected} (tol {tol}). \
         The calibration is frozen; changing it requires re-running BOTH blind predictions.",
    );
}

/// Step 2.6, test 1 — the calibration lock file pins the single free parameter.
///
/// Nothing in `src/` reads `profiles/calibration.lock.toml`. That is precisely the
/// defect this test closes: the lock is enforced here, in the test suite, so that a
/// CI run fails loudly if it is altered without re-running both blind predictions.
#[test]
fn calibration_lock_pins_the_single_free_parameter() {
    let lock = read_toml("profiles/calibration.lock.toml");

    // [calibration] section
    let cal = &lock["calibration"];
    assert_f64_eq(
        cal["loss_rate"].as_float().unwrap(),
        0.05,
        1e-12,
        "profiles/calibration.lock.toml",
        "calibration.loss_rate",
    );
    assert_eq!(
        cal["free_parameters"].as_integer().unwrap(),
        1,
        "profiles/calibration.lock.toml: calibration.free_parameters must be 1. \
         The calibration is frozen; changing it requires re-running BOTH blind predictions.",
    );
    assert_eq!(
        cal["targets"].as_integer().unwrap(),
        1,
        "profiles/calibration.lock.toml: calibration.targets must be 1. \
         The calibration is frozen; changing it requires re-running BOTH blind predictions.",
    );
    assert_eq!(
        cal["interpretation"].as_str().unwrap(),
        "upper bound",
        "profiles/calibration.lock.toml: calibration.interpretation must be \"upper bound\". \
         The calibration is frozen; changing it requires re-running BOTH blind predictions.",
    );

    // [decision_rule] section
    let dr = &lock["decision_rule"];
    assert_f64_eq(
        dr["p_star"].as_float().unwrap(),
        0.05,
        1e-12,
        "profiles/calibration.lock.toml",
        "decision_rule.p_star",
    );
    assert_f64_eq(
        dr["margin_above_target"].as_float().unwrap(),
        0.000066,
        1e-12,
        "profiles/calibration.lock.toml",
        "decision_rule.margin_above_target",
    );

    // [step_2_5] section
    let s25 = &lock["step_2_5"];
    assert_f64_eq(
        s25["primary_loss_rate"].as_float().unwrap(),
        0.05,
        1e-12,
        "profiles/calibration.lock.toml",
        "step_2_5.primary_loss_rate",
    );
    assert_f64_eq(
        s25["sensitivity_loss_rate"].as_float().unwrap(),
        0.06,
        1e-12,
        "profiles/calibration.lock.toml",
        "step_2_5.sensitivity_loss_rate",
    );

    // The blueflood profile is also a template (contains __SEED__), so it
    // cannot be parsed as TOML either. Read it as text and check loss_rate.
    let bf_text = std::fs::read_to_string("profiles/blueflood_ewsn19.toml")
        .unwrap_or_else(|e| panic!("cannot read profiles/blueflood_ewsn19.toml: {e}"));
    // Extract the line "loss_rate = 0.05" (not under a section that might shadow it).
    let bf_loss: f64 = bf_text
        .lines()
        .find(|l| {
            let trimmed = l.trim();
            trimmed.starts_with("loss_rate") && !trimmed.starts_with('#')
        })
        .and_then(|l| l.split('=').nth(1))
        .map(|v| v.trim().parse::<f64>().expect("loss_rate is not a float"))
        .expect("profiles/blueflood_ewsn19.toml: no loss_rate line found");
    assert_f64_eq(
        bf_loss,
        0.05,
        1e-12,
        "profiles/blueflood_ewsn19.toml",
        "network.loss_rate",
    );

    // The two prediction profiles are templates with __LOSS__ placeholders.
    // They cannot be parsed as TOML, so we verify the placeholder is present
    // and that step_2_5.primary_loss_rate (already asserted == 0.05 above)
    // is the value the harness substitutes at runtime.
    for template in ["profiles/a2_sensys17.toml", "profiles/wpaxos_ewsn19.toml"] {
        let text = std::fs::read_to_string(template)
            .unwrap_or_else(|e| panic!("cannot read {template}: {e}"));
        assert!(
            text.contains("loss_rate = __LOSS__"),
            "{template}: expected 'loss_rate = __LOSS__' placeholder. \
             The calibration is frozen; changing it requires re-running BOTH blind predictions.",
        );
    }
}

/// Step 2.6, test 2 — the blind prediction failure is a published result.
///
/// Both predictions undershoot the published testbed latencies by roughly 57 %.
/// This test makes that deficit permanent and machine-checked: if it fires,
/// either the recorded result has been altered or the model has changed, and in
/// both cases the manuscript must be revised before this test is relaxed.
#[test]
fn blind_prediction_failure_is_recorded_not_repaired() {
    let csv_path = "docs/validation/addition13/data/blind_predictions.csv";
    let text =
        std::fs::read_to_string(csv_path).unwrap_or_else(|e| panic!("cannot read {csv_path}: {e}"));
    let lines: Vec<&str> = text.lines().collect();
    assert!(lines.len() >= 2, "{csv_path}: expected header + data rows",);

    // Read the primary loss rate from the calibration lock — no hard-coded "0.05".
    let lock = read_toml("profiles/calibration.lock.toml");
    let primary_loss: f64 = lock["step_2_5"]["primary_loss_rate"].as_float().expect(
        "profiles/calibration.lock.toml: step_2_5.primary_loss_rate missing or not a float",
    );

    // Parse header for column indices.
    let header: Vec<&str> = lines[0].split(',').collect();
    let col = |name: &str| -> usize {
        header
            .iter()
            .position(|&h| h == name)
            .unwrap_or_else(|| panic!("{csv_path}: missing column '{name}'"))
    };
    let i_system = col("system");
    let i_arm = col("arm");
    let i_loss = col("loss_rate");
    let i_committed = col("committed");
    let i_total = col("total_recorded");
    let i_mean_lat = col("mean_latency_slots");
    let required_fields = [i_system, i_arm, i_loss, i_committed, i_total, i_mean_lat]
        .into_iter()
        .max()
        .unwrap()
        + 1;

    struct CellSpec {
        system: &'static str,
        expected_mean: f64,
        target_ms: f64,
        slot_ms: f64,
    }
    let cells = [
        CellSpec {
            system: "a2_sensys17",
            expected_mean: 42.4407,
            target_ms: 475.0,
            slot_ms: 4.75,
        },
        CellSpec {
            system: "wpaxos_ewsn19",
            expected_mean: 24.6140,
            target_ms: 289.0,
            slot_ms: 5.00,
        },
    ];

    for spec in &cells {
        // Collect primary cell: arm=base, loss_rate == primary_loss (numeric comparison)
        let mut latencies: Vec<f64> = Vec::new();
        for (data_row, line) in lines[1..].iter().enumerate() {
            let file_line = data_row + 2; // 1-indexed, skip header
            let fields: Vec<&str> = line.split(',').collect();
            assert!(
                fields.len() >= required_fields,
                "{csv_path} line {file_line}: expected at least {required_fields} fields, found {}",
                fields.len(),
            );
            if fields[i_system] != spec.system || fields[i_arm] != "base" {
                continue;
            }
            let row_loss: f64 = fields[i_loss].parse().unwrap_or_else(|_| {
                panic!(
                    "{csv_path} line {file_line}: loss_rate '{}' is not a valid float; \
                     a corrupted row must be investigated, not skipped",
                    fields[i_loss],
                )
            });
            if (row_loss - primary_loss).abs() < 1e-12 {
                let committed: u64 = fields[i_committed].parse().unwrap();
                let total: u64 = fields[i_total].parse().unwrap();
                assert_eq!(
                    committed, total,
                    "{csv_path}: {}: committed ({committed}) != total_recorded ({total}); \
                     100 % commit rate required so the latency mean is not contaminated by partial runs",
                    spec.system,
                );
                latencies.push(fields[i_mean_lat].parse::<f64>().unwrap());
            }
        }

        // (a) Distinguish zero-match (lock changed) from wrong-count (data changed).
        assert!(
            !latencies.is_empty(),
            "{csv_path}: {}: the loss rate in profiles/calibration.lock.toml \
             (step_2_5.primary_loss_rate = {primary_loss}) selects no rows in \
             blind_predictions.csv; the calibration has been changed without \
             re-running both blind predictions",
            spec.system,
        );
        assert_eq!(
            latencies.len(),
            15,
            "{csv_path}: {} base/loss={primary_loss} cell has {} rows, expected 15",
            spec.system,
            latencies.len(),
        );

        // (c) arithmetic mean matches the recorded value within 1e-3
        let mean: f64 = latencies.iter().sum::<f64>() / 15.0;
        assert!(
            (mean - spec.expected_mean).abs() < 1e-3,
            "{csv_path}: {} mean_latency_slots = {mean:.4}, expected {:.4} (tol 1e-3)",
            spec.system,
            spec.expected_mean,
        );

        // (d) convert published target to slots and check relative error
        let target_slots = spec.target_ms / spec.slot_ms;
        let rel_err = (mean - target_slots) / target_slots;
        assert!(
            (-0.60..=-0.55).contains(&rel_err),
            "{csv_path}: {} relative error = {rel_err:.4}, expected in [-0.60, -0.55]",
            spec.system,
        );

        // (e) the pre-registered acceptance test is recorded as FAILED
        assert!(
            rel_err.abs() > 0.20,
            "{csv_path}: {}: |relative error| = {:.4} is within 0.20 — \
             the pre-registered acceptance test is recorded as FAILED for this system; \
             if this assertion fires, either the recorded result has been altered or the \
             model has changed, and in both cases the manuscript must be revised before \
             this test is relaxed",
            spec.system,
            rel_err.abs(),
        );
    }
}

/// Step 2.6, test 3 — published slot lengths match their primary sources.
///
/// Every conversion from published milliseconds to simulator slots relies on a
/// slot length extracted from the released firmware. This test pins those values
/// and the arithmetic they feed.
#[test]
fn published_slot_lengths_match_their_primary_sources() {
    let csv_path = "docs/validation/addition14/data/published_slot_lengths.csv";
    let text =
        std::fs::read_to_string(csv_path).unwrap_or_else(|e| panic!("cannot read {csv_path}: {e}"));
    let lines: Vec<&str> = text.lines().collect();
    assert!(lines.len() >= 2, "{csv_path}: expected header + data rows",);

    let header: Vec<&str> = lines[0].split(',').collect();
    let col = |name: &str| -> usize {
        header
            .iter()
            .position(|&h| h == name)
            .unwrap_or_else(|| panic!("{csv_path}: missing column '{name}'"))
    };
    let i_constant = col("constant");
    let i_nominal = col("slot_ms_nominal");
    let i_ticks = col("ticks_at_32768");
    let i_realised = col("slot_ms_realised");
    let i_repo = col("repo");
    let i_ref = col("git_ref");
    let i_path = col("path");
    let i_blob = col("blob_sha");

    // Build a map keyed by constant name.
    let mut rows: std::collections::HashMap<String, Vec<&str>> = std::collections::HashMap::new();
    for line in &lines[1..] {
        let fields: Vec<&str> = line.split(',').collect();
        rows.insert(fields[i_constant].to_string(), fields.clone());
    }

    // (a) all six rows present
    let expected_constants = [
        "TWO_PC_SLOT_LEN",
        "THREE_PC_SLOT_LEN",
        "PAXOS_SLOT_LEN",
        "MAX_SLOT_LEN",
        "CHAOS_GLOSSY_SLOT_LEN",
        "ASSOCIATION_SLOT_LEN",
    ];
    for name in &expected_constants {
        assert!(
            rows.contains_key(*name),
            "{csv_path}: missing row for constant '{name}'",
        );
    }
    assert_eq!(
        rows.len(),
        6,
        "{csv_path}: expected 6 rows, got {}",
        rows.len(),
    );

    // (b) tick-grid consistency for every row
    for (name, fields) in &rows {
        let nominal: f64 = fields[i_nominal].parse().unwrap();
        let ticks: u64 = fields[i_ticks].parse().unwrap();
        let realised: f64 = fields[i_realised].parse().unwrap();

        // ticks_at_32768 == nominal_ms * (RTIMER_SECOND / 1000)
        // The firmware computes integer division RTIMER_SECOND/1000 = 32768/1000 = 32
        // first, then multiplies: ticks = nominal_ms * 32.
        let expected_ticks = (nominal * 32.0) as u64;
        assert_eq!(
            ticks, expected_ticks,
            "{csv_path}: {name}: ticks_at_32768 = {ticks}, expected {expected_ticks} \
             (nominal {nominal} * 32)",
        );

        // slot_ms_realised == ticks * (1000 / 32768) within 1e-3
        let expected_realised = ticks as f64 * 1000.0 / 32768.0;
        assert!(
            (realised - expected_realised).abs() < 1e-3,
            "{csv_path}: {name}: slot_ms_realised = {realised}, expected {expected_realised:.4} (tol 1e-3)",
        );
    }

    // (c) the four study conversions, each within 1e-6
    let conversions: [(f64, f64, f64); 4] = [
        (475.0, 4.75, 100.0),
        (289.0, 5.00, 57.8),
        (633.0, 5.00, 126.6),
        (959.0, 7.00, 137.0),
    ];
    for (target_ms, slot_ms, expected_slots) in &conversions {
        let computed = target_ms / slot_ms;
        assert!(
            (computed - expected_slots).abs() < 1e-6,
            "{target_ms} / {slot_ms} = {computed}, expected {expected_slots} (tol 1e-6)",
        );
    }

    // (d) firmware round caps — each published measurement is strictly below its cap,
    // so it is a measurement and not a timeout. The caps are read from the CSV's
    // round_max_slots column; rows with "NA" are skipped.
    let i_round_max = col("round_max_slots");
    let a2_slots = conversions[0].2; // 100.0
    let paxos_slots = conversions[2].2; // 126.6

    // TWO_PC cap
    let two_pc_cap_str = rows["TWO_PC_SLOT_LEN"][i_round_max];
    assert_ne!(
        two_pc_cap_str, "NA",
        "{csv_path}: TWO_PC_SLOT_LEN round_max_slots is NA — cannot check cap",
    );
    let two_pc_round_max: f64 = two_pc_cap_str.parse().unwrap();
    assert!(
        a2_slots < two_pc_round_max,
        "TWO_PC: {a2_slots} slots must be below TWO_PC_ROUND_MAX_SLOTS ({two_pc_round_max}); \
         the published figure is a measurement and not a timeout",
    );

    // PAXOS cap
    let paxos_cap_str = rows["PAXOS_SLOT_LEN"][i_round_max];
    assert_ne!(
        paxos_cap_str, "NA",
        "{csv_path}: PAXOS_SLOT_LEN round_max_slots is NA — cannot check cap",
    );
    let paxos_round_max: f64 = paxos_cap_str.parse().unwrap();
    assert!(
        paxos_slots < paxos_round_max,
        "PAXOS: {paxos_slots} slots must be below PAXOS_ROUND_MAX_SLOTS ({paxos_round_max}); \
         the published figure is a measurement and not a timeout",
    );

    // (e) every row has non-empty provenance and a valid 40-char hex blob_sha
    for (name, fields) in &rows {
        assert!(
            !fields[i_repo].is_empty(),
            "{csv_path}: {name}: repo is empty",
        );
        assert!(
            !fields[i_ref].is_empty(),
            "{csv_path}: {name}: git_ref is empty",
        );
        assert!(
            !fields[i_path].is_empty(),
            "{csv_path}: {name}: path is empty",
        );
        let sha = fields[i_blob];
        assert!(!sha.is_empty(), "{csv_path}: {name}: blob_sha is empty",);
        assert_eq!(
            sha.len(),
            40,
            "{csv_path}: {name}: blob_sha has {} chars, expected 40",
            sha.len(),
        );
        assert!(
            sha.chars().all(|c| c.is_ascii_hexdigit()),
            "{csv_path}: {name}: blob_sha '{sha}' is not valid hex",
        );
    }
}

/// The blind-prediction harness injects loss rates into simulation runs at four
/// distinct call sites (two variable-fed from `for loss in …` loops, two with
/// numeric literals). This test quantifies over every injection site and asserts
/// that every reachable loss rate traces back to the calibration lock.
#[test]
fn harness_loss_rates_come_from_the_calibration_lock() {
    const TOLERANCE: f64 = 1e-12;
    type LossLoop = Option<(usize, Vec<String>)>;

    let lock = read_toml("profiles/calibration.lock.toml");
    let primary: f64 = lock["step_2_5"]["primary_loss_rate"]
        .as_float()
        .expect("profiles/calibration.lock.toml: step_2_5.primary_loss_rate missing");
    let sensitivity: f64 = lock["step_2_5"]["sensitivity_loss_rate"]
        .as_float()
        .expect("profiles/calibration.lock.toml: step_2_5.sensitivity_loss_rate missing");

    let mut lock_rates = vec![primary, sensitivity];
    lock_rates.sort_by(|a, b| a.partial_cmp(b).unwrap());
    lock_rates.dedup_by(|a, b| (*a - *b).abs() < TOLERANCE);

    let script_path = "docs/validation/addition13/scripts/blind_predictions.sh";
    let script = std::fs::read_to_string(script_path)
        .unwrap_or_else(|e| panic!("cannot read {script_path}: {e}"));

    let script_lines: Vec<&str> = script.lines().collect();

    // The loss rate is the 5th whitespace-delimited token after `run_one`
    // (positional arg $5 in the function signature).
    // run_one <system> <protocol> <nn> <arm> <loss> <gseed>
    //   0        1        2        3     4     5      6
    let mut block_stack: Vec<LossLoop> = Vec::new();
    let mut call_sites: Vec<(usize, String, LossLoop)> = Vec::new();
    let mut structural_complaints = Vec::new();
    let is_done = |command: &str| {
        command
            .trim_start()
            .strip_prefix("done")
            .is_some_and(|rest| {
                rest.is_empty()
                    || rest
                        .chars()
                        .next()
                        .is_some_and(|c| c.is_whitespace() || "|&<>".contains(c))
            })
    };

    for (line_idx, line) in script_lines.iter().enumerate() {
        let file_line = line_idx + 1;
        let trimmed = line.trim();
        let scan_line = trimmed.split('#').next().unwrap_or("").trim();

        if is_done(scan_line) {
            if block_stack.pop().is_none() {
                structural_complaints.push(format!(
                    "{script_path} line {file_line}: 'done' has no matching open block"
                ));
            }
            continue;
        }

        let opens_loop = scan_line.starts_with("while ")
            || scan_line.starts_with("until ")
            || (scan_line.starts_with("for ") && !scan_line.starts_with("for ("))
            || scan_line.starts_with("for ((");
        if opens_loop {
            let loss_loop = if scan_line.starts_with("for loss in ") {
                let after_in = scan_line.strip_prefix("for loss in ").unwrap();
                let tokens_part = after_in.split(';').next().unwrap_or(after_in);
                let loop_rates = tokens_part.split_whitespace().map(str::to_owned).collect();
                Some((file_line, loop_rates))
            } else {
                None
            };
            block_stack.push(loss_loop);
        }

        for command in scan_line.split(';').skip(1) {
            if is_done(command) && block_stack.pop().is_none() {
                structural_complaints.push(format!(
                    "{script_path} line {file_line}: 'done' has no matching open block"
                ));
            }
        }

        if !trimmed.starts_with("run_one ") {
            continue;
        }

        let tokens: Vec<&str> = line.split_whitespace().collect();
        assert!(
            tokens.len() >= 6,
            "{script_path} line {file_line}: run_one call has {} tokens, expected at least 6 \
             (run_one system protocol nn arm loss gseed)",
            tokens.len(),
        );
        let raw_loss_arg = tokens[5]; // 0-indexed: run_one=0, system=1, ..., loss=5
        let loss_arg = if raw_loss_arg.len() >= 2
            && ((raw_loss_arg.starts_with('"') && raw_loss_arg.ends_with('"'))
                || (raw_loss_arg.starts_with('\'') && raw_loss_arg.ends_with('\'')))
        {
            &raw_loss_arg[1..raw_loss_arg.len() - 1]
        } else {
            raw_loss_arg
        };

        let enclosing_loss_loop = if loss_arg.starts_with('$') {
            match block_stack.iter().rev().find_map(Option::as_ref) {
                Some(loss_loop) => Some(loss_loop.clone()),
                None => {
                    structural_complaints.push(format!(
                        "{script_path} line {file_line}: run_one uses variable {loss_arg} \
                         but is not enclosed by a 'for loss in' loop"
                    ));
                    None
                }
            }
        } else {
            None
        };
        call_sites.push((file_line, loss_arg.to_owned(), enclosing_loss_loop));
    }

    assert_eq!(
        call_sites.len(),
        4,
        "{script_path}: found {} run_one call sites, expected exactly 4; \
         if the harness gains or loses a run this count must be updated deliberately",
        call_sites.len(),
    );
    assert!(
        block_stack.is_empty(),
        "{script_path}: structural scan ended with {} unclosed loop blocks",
        block_stack.len(),
    );
    assert!(
        structural_complaints.is_empty(),
        "{}",
        structural_complaints.join("\n"),
    );

    let mut all_reachable: Vec<f64> = Vec::new();
    for (file_line, loss_arg, enclosing_loss_loop) in call_sites {
        if let Some((loop_file_line, loop_rate_tokens)) = enclosing_loss_loop {
            let loop_rates: Vec<f64> = loop_rate_tokens
                .iter()
                .map(|token| {
                    token.parse::<f64>().unwrap_or_else(|e| {
                        panic!(
                            "{script_path} line {loop_file_line}: cannot parse '{token}' as f64: {e}"
                        )
                    })
                })
                .collect();

            // The variable-fed rate set must equal the lock rate set.
            let mut sorted_loop = loop_rates.clone();
            sorted_loop.sort_by(|a, b| a.partial_cmp(b).unwrap());
            sorted_loop.dedup_by(|a, b| (*a - *b).abs() < TOLERANCE);

            assert_eq!(
                sorted_loop.len(),
                lock_rates.len(),
                "{script_path} line {file_line}: variable-fed call site resolves to \
                 {sorted_loop:?} (from loop at line {loop_file_line}) but the lock defines \
                 {lock_rates:?}; they must be the same set",
            );
            for (s, l) in sorted_loop.iter().zip(lock_rates.iter()) {
                assert!(
                    (s - l).abs() < TOLERANCE,
                    "{script_path} line {file_line}: loop rate {s} (from line {loop_file_line}) \
                     does not match lock rate {l} (tol {TOLERANCE})",
                );
            }

            for r in &loop_rates {
                if !all_reachable
                    .iter()
                    .any(|reachable| (reachable - r).abs() < TOLERANCE)
                {
                    all_reachable.push(*r);
                }
            }
        } else {
            // Numeric literal — must equal primary_loss_rate.
            let literal: f64 = loss_arg.parse().unwrap_or_else(|e| {
                panic!(
                    "{script_path} line {file_line}: loss argument '{loss_arg}' is neither \
                     a numeric literal nor a shell variable reference: {e}"
                )
            });

            assert!(
                (literal - primary).abs() < TOLERANCE,
                "{script_path} line {file_line}: numeric literal {literal} does not equal \
                 step_2_5.primary_loss_rate ({primary}) from the calibration lock (tol {TOLERANCE})",
            );

            if !all_reachable
                .iter()
                .any(|reachable| (reachable - literal).abs() < TOLERANCE)
            {
                all_reachable.push(literal);
            }
        }
    }

    all_reachable.sort_by(|a, b| a.partial_cmp(b).unwrap());
    assert_eq!(
        all_reachable.len(),
        lock_rates.len(),
        "{script_path}: found {} unique reachable rates {all_reachable:?}, but the lock defines {} {lock_rates:?}",
        all_reachable.len(),
        lock_rates.len(),
    );
    for lock_rate in &lock_rates {
        let matches = all_reachable
            .iter()
            .filter(|reachable| (*reachable - lock_rate).abs() < TOLERANCE)
            .count();
        assert_eq!(
            matches, 1,
            "{script_path}: lock rate {lock_rate} has {matches} reachable matches within tolerance {TOLERANCE}; reachable rates: {all_reachable:?}",
        );
    }
    for reachable in &all_reachable {
        let matches = lock_rates
            .iter()
            .filter(|lock_rate| (*lock_rate - reachable).abs() < TOLERANCE)
            .count();
        assert_eq!(
            matches, 1,
            "{script_path}: reachable rate {reachable} has {matches} lock matches within tolerance {TOLERANCE}; lock rates: {lock_rates:?}",
        );
    }
}

/// Compute the git blob object ID: SHA-1("blob <len>\0" + content).
fn git_blob_sha1(bytes: &[u8]) -> String {
    let mut hasher = sha1_smol::Sha1::new();
    hasher.update(format!("blob {}\0", bytes.len()).as_bytes());
    hasher.update(bytes);
    format!("{}", hasher.digest())
}

/// Verify that every `*_blob` evidence hash in the calibration lock matches
/// the current content of the file it describes. The hashes are git blob
/// object IDs, not plain file SHA-1s.
#[test]
fn calibration_lock_evidence_blobs_match_their_files() {
    // Sanity-check the helper: the git blob hash of the empty byte string is
    // a well-known constant.
    assert_eq!(
        git_blob_sha1(b""),
        "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        "git_blob_sha1 helper is broken: wrong hash for empty input",
    );

    let lock = read_toml("profiles/calibration.lock.toml");
    let evidence = lock["evidence"]
        .as_table()
        .expect("profiles/calibration.lock.toml: [evidence] section missing or not a table");

    // Collect all *_blob keys and their sibling path keys.
    let blob_keys: Vec<(&String, &toml::Value)> = evidence
        .iter()
        .filter(|(k, _)| k.ends_with("_blob"))
        .collect();

    assert_eq!(
        blob_keys.len(),
        4,
        "profiles/calibration.lock.toml [evidence]: expected exactly 4 *_blob keys, found {}; \
         if a fifth evidence blob is added, this count must be updated deliberately",
        blob_keys.len(),
    );

    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));

    for (blob_key, blob_val) in &blob_keys {
        let recorded_hash = blob_val.as_str().unwrap_or_else(|| {
            panic!("profiles/calibration.lock.toml: {blob_key} is not a string")
        });

        // Derive the sibling path key: "foo_blob" → "foo"
        let path_key = blob_key.strip_suffix("_blob").unwrap_or_else(|| {
            panic!(
                "profiles/calibration.lock.toml: key '{blob_key}' ends_with '_blob' \
                 but strip_suffix failed — this should be unreachable"
            )
        });
        let rel_path = evidence[path_key].as_str().unwrap_or_else(|| {
            panic!("profiles/calibration.lock.toml: sibling key '{path_key}' for '{blob_key}' missing or not a string")
        });

        let full_path = root.join(rel_path);
        assert!(
            full_path.exists(),
            "profiles/calibration.lock.toml: {blob_key} references '{rel_path}' \
             (via key '{path_key}') but that file does not exist",
        );

        let bytes = std::fs::read(&full_path)
            .unwrap_or_else(|e| panic!("cannot read '{}': {e}", full_path.display()));
        let computed = git_blob_sha1(&bytes);

        assert_eq!(
            computed, recorded_hash,
            "profiles/calibration.lock.toml: {blob_key} for '{rel_path}': \
             recorded {recorded_hash}, computed {computed}; \
             the evidence file has changed since the calibration was frozen; do \
             not update the lock - re-run the affected step or report the change",
        );
    }
}

/// Every profile template consumed by the blind-prediction harness must contain
/// all three placeholders (__SEED__, __LOSS__, __GRAPH__). If a template ever
/// loses a placeholder, `sed` silently leaves whatever value is baked into the
/// template, causing the output CSV to report a loss rate that was never executed.
/// The list of templates is derived from the harness itself, not hard-coded.
#[test]
fn harness_templates_contain_all_placeholders() {
    let script_path = "docs/validation/addition13/scripts/blind_predictions.sh";
    let script = std::fs::read_to_string(script_path)
        .unwrap_or_else(|e| panic!("cannot read {script_path}: {e}"));

    // Discover systems from run_one call sites (first arg after `run_one`).
    let mut systems: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    for line in script.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("run_one ") {
            let tokens: Vec<&str> = trimmed.split_whitespace().collect();
            if tokens.len() >= 2 {
                systems.insert(tokens[1].to_string());
            }
        }
    }

    assert!(
        !systems.is_empty(),
        "{script_path}: no run_one call sites found; cannot discover templates",
    );

    // The harness constructs templates as profiles/${system}.toml (line 34).
    let placeholders = ["__SEED__", "__LOSS__", "__GRAPH__"];
    for system in &systems {
        let template_path = format!("profiles/{system}.toml");
        let text = std::fs::read_to_string(&template_path)
            .unwrap_or_else(|e| panic!("cannot read template '{template_path}': {e}"));

        for ph in &placeholders {
            assert!(
                text.contains(ph),
                "{template_path}: missing placeholder {ph}; if the template loses this \
                 placeholder, sed substitution is silently skipped and the run executes \
                 with whatever value is baked into the template",
            );
        }
    }
}

#[test]
fn high_loss_2pc_exercises_non_committed_outcomes() {
    let config = make_sim_config(
        2,
        "ce",
        "2pc_ce",
        6,
        "line",
        0.20,
        1,
        &CeConfig {
            listen_timeout: 5,
            max_round_slots: 100,
        },
        10,
        1_000_000,
        100_000,
        0.0,
    );
    let result = run_experiment(config);
    assert!(
        result.summary.aborted + result.summary.timed_out > 0,
        "high-loss outcome classifier stayed all-committed: committed={} aborted={} timed_out={}",
        result.summary.committed,
        result.summary.aborted,
        result.summary.timed_out,
    );
}

#[test]
fn committed_per_proposal_evidence_reproduces_stratified_aggregate() {
    let dir_path = "docs/validation/addition14/data/per_proposal";
    let aggregate_path = "docs/validation/addition14/data/stratified_predictions.csv";
    let aggregate = std::fs::read_to_string(aggregate_path)
        .unwrap_or_else(|e| panic!("cannot read {aggregate_path}: {e}"));

    let entries: Vec<_> = std::fs::read_dir(dir_path)
        .unwrap_or_else(|e| panic!("cannot read {dir_path}: {e}"))
        .filter_map(Result::ok)
        .collect();

    assert_eq!(
        entries.len(),
        23,
        "expected exactly 23 files in per_proposal directory"
    );

    for entry in entries {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let file_name = path.file_name().unwrap().to_str().unwrap();
        if !file_name.ends_with(".csv") {
            continue;
        }

        let stem = file_name.strip_suffix(".csv").unwrap();
        let parts: Vec<&str> = stem.split('_').collect();
        let cs_str = parts.last().unwrap().strip_prefix("cs").unwrap();
        let gs_str = parts[parts.len() - 2].strip_prefix("gs").unwrap();
        let loss_str = parts[parts.len() - 3].strip_prefix("loss").unwrap();
        let system = format!("{}_{}", parts[0], parts[1]);
        let arm = parts[2..parts.len() - 3].join("_");

        let proposals = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", path.display()));
        let mut latencies = Vec::new();
        for (index, line) in proposals.lines().enumerate().skip(1) {
            let fields: Vec<&str> = line.split(',').collect();
            assert_eq!(
                fields.len(),
                5,
                "{} line {}: expected 5 fields",
                path.display(),
                index + 1
            );
            if fields[4] == "committed" {
                latencies.push(fields[3].parse::<f64>().unwrap_or_else(|e| {
                    panic!(
                        "{} line {}: invalid latency '{}': {e}",
                        path.display(),
                        index + 1,
                        fields[3]
                    )
                }));
            }
        }
        assert!(
            !latencies.is_empty(),
            "{}: no committed rows",
            path.display()
        );
        let mean = latencies.iter().sum::<f64>() / latencies.len() as f64;
        let sd = (latencies.iter().map(|x| (x - mean).powi(2)).sum::<f64>()
            / (latencies.len() - 1) as f64)
            .sqrt();

        let row = aggregate
            .lines()
            .skip(1)
            .find(|line| {
                let f: Vec<&str> = line.split(',').collect();
                f.len() == 20
                    && f[0] == system
                    && f[3] == arm
                    && f[4] == gs_str
                    && f[5] == loss_str
                    && f[6] == cs_str
            })
            .unwrap_or_else(|| panic!("{}: matching aggregate row not found", file_name));

        let fields: Vec<&str> = row.split(',').collect();
        let recorded_mean: f64 = fields[13].parse().unwrap();
        let recorded_sd: f64 = fields[14].parse().unwrap();
        assert_eq!(
            format!("{mean:.6}"),
            format!("{recorded_mean:.6}"),
            "{}: committed mean {mean:.6} != {aggregate_path} mean {recorded_mean:.6}",
            file_name
        );
        assert_eq!(
            format!("{sd:.6}"),
            format!("{recorded_sd:.6}"),
            "{}: committed sample SD {sd:.6} != {aggregate_path} SD {recorded_sd:.6}",
            file_name
        );
    }
}

// The mean-SD and CV definition is duplicated in docs/validation/addition14/scripts/cv_table.py; they must be changed together.
#[test]
fn cv_table_values_in_provenance_match_data() {
    let md_path = "docs/validation/addition14/data/run_provenance.md";
    let md_text =
        std::fs::read_to_string(md_path).unwrap_or_else(|e| panic!("cannot read {md_path}: {e}"));

    // Parse the Markdown table. We look for the table after "## Within-run committed-latency dispersion"
    let table_start = md_text
        .find("## Within-run committed-latency dispersion")
        .expect("table heading not found");
    let md_text_after = &md_text[table_start..];

    struct MdRow {
        sd05: f64,
        cv05: f64,
        runs05: usize,
        sd06: f64,
        cv06: f64,
        runs06: usize,
        sd_pooled: f64,
        cv_pooled: f64,
        runs_pooled: usize,
    }

    let mut table_parsed = std::collections::HashMap::new();
    for line in md_text_after.lines() {
        if line.starts_with("| A2") || line.starts_with("| WP") {
            let cols: Vec<&str> = line.split('|').map(|s| s.trim()).collect();
            let system = if cols[1] == "A2/2PC" {
                "a2_sensys17"
            } else {
                "wpaxos_ewsn19"
            };
            let arm = cols[2];
            table_parsed.insert(
                (system.to_string(), arm.to_string()),
                MdRow {
                    sd05: cols[3].parse().unwrap(),
                    cv05: cols[4].parse().unwrap(),
                    runs05: cols[5].parse().unwrap(),
                    sd06: cols[6].parse().unwrap(),
                    cv06: cols[7].parse().unwrap(),
                    runs06: cols[8].parse().unwrap(),
                    sd_pooled: cols[9].parse().unwrap(),
                    cv_pooled: cols[10].parse().unwrap(),
                    runs_pooled: cols[11].parse().unwrap(),
                },
            );
        }
    }
    assert_eq!(
        table_parsed.len(),
        4,
        "expected to parse 4 rows from the Markdown table"
    );

    let csv_path = "docs/validation/addition14/data/stratified_predictions.csv";
    let csv =
        std::fs::read_to_string(csv_path).unwrap_or_else(|e| panic!("cannot read {csv_path}: {e}"));

    // Key: (system, arm, loss), Value: (sum_mean, sum_sd, count)
    let mut stats = std::collections::HashMap::new();

    for line in csv.lines().skip(1) {
        let f: Vec<&str> = line.split(',').collect();
        if f.len() < 20 {
            continue;
        }
        let sys = f[0].to_string();
        let arm = f[3].to_string();
        let loss = f[5].to_string();
        if arm != "dense" && arm != "base" {
            continue;
        }

        let mean: f64 = f[13].parse().unwrap();
        let sd: f64 = f[14].parse().unwrap();

        let entry = stats
            .entry((sys.clone(), arm.clone(), loss))
            .or_insert((0.0, 0.0, 0usize));
        entry.0 += mean;
        entry.1 += sd;
        entry.2 += 1;

        let entry_pooled = stats
            .entry((sys, arm, "pooled".to_string()))
            .or_insert((0.0, 0.0, 0usize));
        entry_pooled.0 += mean;
        entry_pooled.1 += sd;
        entry_pooled.2 += 1;
    }

    for (sys, arm) in [
        ("a2_sensys17", "dense"),
        ("a2_sensys17", "base"),
        ("wpaxos_ewsn19", "dense"),
        ("wpaxos_ewsn19", "base"),
    ] {
        let k_05 = (sys.to_string(), arm.to_string(), "0.05".to_string());
        let k_06 = (sys.to_string(), arm.to_string(), "0.06".to_string());
        let k_pooled = (sys.to_string(), arm.to_string(), "pooled".to_string());

        let stat_05 = stats.get(&k_05).unwrap();
        let stat_06 = stats.get(&k_06).unwrap();
        let stat_pooled = stats.get(&k_pooled).unwrap();

        let sd05 = stat_05.1 / stat_05.2 as f64;
        let cv05 = (stat_05.1 / stat_05.2 as f64) / (stat_05.0 / stat_05.2 as f64);
        let runs05 = stat_05.2;

        let sd06 = stat_06.1 / stat_06.2 as f64;
        let cv06 = (stat_06.1 / stat_06.2 as f64) / (stat_06.0 / stat_06.2 as f64);
        let runs06 = stat_06.2;

        let sd_pooled = stat_pooled.1 / stat_pooled.2 as f64;
        let cv_pooled =
            (stat_pooled.1 / stat_pooled.2 as f64) / (stat_pooled.0 / stat_pooled.2 as f64);
        let runs_pooled = stat_pooled.2;

        let row = table_parsed
            .get(&(sys.to_string(), arm.to_string()))
            .unwrap();

        assert_eq!(
            format!("{sd05:.5}"),
            format!("{:.5}", row.sd05),
            "{} {} column loss=0.05 Mean SD mismatch",
            sys,
            arm
        );
        assert_eq!(
            format!("{cv05:.5}"),
            format!("{:.5}", row.cv05),
            "{} {} column loss=0.05 CV mismatch",
            sys,
            arm
        );
        assert_eq!(
            runs05, row.runs05,
            "{} {} column loss=0.05 Runs mismatch",
            sys, arm
        );

        assert_eq!(
            format!("{sd06:.5}"),
            format!("{:.5}", row.sd06),
            "{} {} column loss=0.06 Mean SD mismatch",
            sys,
            arm
        );
        assert_eq!(
            format!("{cv06:.5}"),
            format!("{:.5}", row.cv06),
            "{} {} column loss=0.06 CV mismatch",
            sys,
            arm
        );
        assert_eq!(
            runs06, row.runs06,
            "{} {} column loss=0.06 Runs mismatch",
            sys, arm
        );

        assert_eq!(
            format!("{sd_pooled:.5}"),
            format!("{:.5}", row.sd_pooled),
            "{} {} column Pooled Mean SD mismatch",
            sys,
            arm
        );
        assert_eq!(
            format!("{cv_pooled:.5}"),
            format!("{:.5}", row.cv_pooled),
            "{} {} column Pooled CV mismatch",
            sys,
            arm
        );
        assert_eq!(
            runs_pooled, row.runs_pooled,
            "{} {} column Pooled Runs mismatch",
            sys, arm
        );
    }
}

#[test]
fn round_boundaries_tile_timeline_and_latency_equals_round_length() {
    let dir_path = "docs/validation/addition14/data/per_proposal";
    let entries: Vec<_> = std::fs::read_dir(dir_path)
        .unwrap_or_else(|e| panic!("cannot read {dir_path}: {e}"))
        .filter_map(Result::ok)
        .collect();

    let mut file_count = 0;

    for entry in entries {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let file_name = path.file_name().unwrap().to_str().unwrap();
        if !file_name.ends_with(".csv") {
            continue;
        }

        file_count += 1;

        let content = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", path.display()));

        let lines: Vec<&str> = content.lines().collect();
        if lines.len() <= 1 {
            panic!("{file_name}: file has only a header or is empty");
        }

        let mut sum_latency = 0;
        let mut prev_end_slot: Option<u64> = None;
        let mut last_end_slot = 0;
        let mut data_row_count = 0;

        for (i, line) in lines.iter().enumerate().skip(1) {
            let fields: Vec<&str> = line.split(',').collect();
            let file_row = i + 1;
            assert_eq!(
                fields.len(),
                5,
                "{file_name}: row {file_row} has invalid fields"
            );

            let id: usize = fields[0].parse().unwrap();
            let start_slot: u64 = fields[1].parse().unwrap();
            let end_slot: u64 = fields[2].parse().unwrap();
            let latency: u64 = fields[3].parse().unwrap();

            data_row_count += 1;

            let expected_proposal_id = i - 1;

            // This is what makes checking (b) in file order equivalent to checking it in proposal_id order.
            assert_eq!(
                id, expected_proposal_id,
                "{file_name}: row {file_row} failed: proposal_id {} != expected {}",
                id, expected_proposal_id
            );

            // (a) latency == end_slot - start_slot
            assert_eq!(
                latency,
                end_slot - start_slot,
                "{file_name}: row {file_row} failed property (a): latency {latency} != end_slot {end_slot} - start_slot {start_slot}"
            );

            // (c) first row start_slot == 0
            if i == 1 {
                assert_eq!(
                    start_slot, 0,
                    "{file_name}: row {file_row} failed property (c): start_slot {start_slot} != 0"
                );
            }

            // (b) start_slot[i+1] == end_slot[i]
            if let Some(prev) = prev_end_slot {
                assert_eq!(
                    start_slot, prev,
                    "{file_name}: row {file_row} failed property (b): start_slot {start_slot} != previous end_slot {prev}"
                );
            }

            prev_end_slot = Some(end_slot);
            sum_latency += latency;
            last_end_slot = end_slot;
        }

        assert!(data_row_count > 0, "{file_name}: examined 0 data rows");

        // Property (d) is implied by (a), (b) and (c) via the telescoping sum and is therefore a consistency guard, not an independent property.
        assert_eq!(
            last_end_slot, sum_latency,
            "{file_name}: last row failed property (d): last end_slot {last_end_slot} != sum of latency {sum_latency}"
        );
    }

    assert!(file_count > 0, "examined 0 .csv files in per_proposal/");
}

#[test]
fn per_proposal_latencies_match_aggregate_round_columns() {
    let dir_path = "docs/validation/addition14/data/per_proposal";
    let agg_path = "docs/validation/addition14/data/stratified_predictions.csv";

    let agg_content = std::fs::read_to_string(agg_path)
        .unwrap_or_else(|e| panic!("cannot read {}: {}", agg_path, e));
    let agg_lines: Vec<&str> = agg_content.lines().collect();

    let entries: Vec<_> = std::fs::read_dir(dir_path)
        .unwrap_or_else(|e| panic!("cannot read {dir_path}: {e}"))
        .filter_map(Result::ok)
        .collect();

    let mut file_count = 0;

    for entry in entries {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let file_name = path.file_name().unwrap().to_str().unwrap();
        if !file_name.ends_with(".csv") {
            continue;
        }

        file_count += 1;

        let stem = file_name.strip_suffix(".csv").unwrap();
        let parts: Vec<&str> = stem.split('_').collect();
        if parts.len() < 4 {
            panic!("{file_name}: file stem must have at least 4 tokens separated by '_'");
        }

        let cs_str = parts.last().unwrap();
        if !cs_str.starts_with("cs") {
            panic!("{file_name}: token {cs_str} does not start with 'cs'");
        }
        let cs_val = cs_str.strip_prefix("cs").unwrap();

        let gs_str = parts[parts.len() - 2];
        if !gs_str.starts_with("gs") {
            panic!("{file_name}: token {gs_str} does not start with 'gs'");
        }
        let gs_val = gs_str.strip_prefix("gs").unwrap();

        let loss_str = parts[parts.len() - 3];
        if !loss_str.starts_with("loss") {
            panic!("{file_name}: token {loss_str} does not start with 'loss'");
        }
        let loss_val = loss_str.strip_prefix("loss").unwrap();

        let prefix = parts[..parts.len() - 3].join("_");

        let content = std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("cannot read {}: {}", path.display(), e));

        let mut max_latency = 0;
        let mut sum_committed_latency = 0;
        let mut committed_count = 0;

        for (i, line) in content.lines().enumerate().skip(1) {
            let fields: Vec<&str> = line.split(',').collect();
            if fields.len() < 5 {
                panic!(
                    "{file_name}: line {}: expected at least 5 fields, found {}",
                    i + 1,
                    fields.len()
                );
            }
            let latency: u64 = fields[3].parse().unwrap();
            let outcome = fields[4];

            if latency > max_latency {
                max_latency = latency;
            }
            if outcome == "committed" {
                sum_committed_latency += latency;
                committed_count += 1;
            }
        }

        let mean_committed_latency = if committed_count > 0 {
            sum_committed_latency as f64 / committed_count as f64
        } else {
            0.0
        };

        // Find matching aggregate row
        let mut match_count = 0;
        for (i, agg_line) in agg_lines.iter().enumerate().skip(1) {
            let f: Vec<&str> = agg_line.split(',').collect();
            if f.len() < 20 {
                panic!(
                    "stratified_predictions.csv: line {}: expected at least 20 fields, found {}",
                    i + 1,
                    f.len()
                );
            }

            let agg_prefix = format!("{}_{}", f[0], f[3]);
            if agg_prefix == prefix && f[4] == gs_val && f[5] == loss_val && f[6] == cs_val {
                match_count += 1;
                let row_mean: f64 = f[13].parse().unwrap();
                let row_max: u64 = f[15].parse().unwrap();

                assert_eq!(
                    max_latency, row_max,
                    "{file_name} (key sys_arm={prefix} loss={loss_val} gs={gs_val} cs={cs_val}): max latency {max_latency} != max_round_slots_observed {row_max}"
                );

                assert_eq!(
                    format!("{mean_committed_latency:.6}"), format!("{row_mean:.6}"),
                    "{file_name} (key sys_arm={prefix} loss={loss_val} gs={gs_val} cs={cs_val}): mean latency {:.6} != mean_round_slots_committed {:.6}", mean_committed_latency, row_mean
                );
            }
        }

        assert_eq!(
            match_count, 1,
            "{file_name}: found {} matching rows in aggregate CSV, expected exactly 1",
            match_count
        );
    }

    assert!(file_count > 0, "examined 0 .csv files in per_proposal/");
}

#[test]
fn step_210c_assertions() {
    use std::fs;
    use std::path::Path;
    let sources_dir = Path::new("docs/validation/paper-audit/sources");

    // T1: slots_per_decision.md contains required lines
    let slots_md = fs::read_to_string(sources_dir.join("slots_per_decision.md")).unwrap();
    assert!(slots_md.contains("pooled (paper definition): sum(total_slots) / sum(committed_decisions)"));
    assert!(slots_md.contains("per-seed mean: mean(total_slots / committed_decisions)"));

    // T2: slots_per_decision.md does NOT contain old proposal sharing text
    assert!(!slots_md.contains("Proposal sharing share"));
    assert!(!slots_md.contains("Share = 1 -"));

    // T3: proposal_sharing_candidates.md contains the exact claims, UNSOURCED, and no fake formulas
    let sharing_md = fs::read_to_string(sources_dir.join("proposal_sharing_candidates.md")).unwrap();
    assert!(!sharing_md.is_empty());
    assert!(sharing_md.contains("accounts for $1.6\\,\\%$ of it"));
    assert!(sharing_md.contains("sweep_summary.csv"));
    assert!(sharing_md.contains("UNSOURCED"));
    assert!(sharing_md.contains("4.57% calculation must not be used"));
    assert!(!sharing_md.contains("depth"));
    assert!(!sharing_md.contains("1.43 / 5.67"));

    // T4: progress_README.md has the exact heading and six arm lines, plus conclusion words
    let prog_md = fs::read_to_string(sources_dir.join("progress_README.md")).unwrap();
    assert!(prog_md.contains("## Snapshot vs run totals"));
    let mut arm_count = 0;
    let mut in_section = false;
    for line in prog_md.lines() {
        if line == "## Snapshot vs run totals" {
            in_section = true;
            continue;
        }
        if in_section {
            if line.starts_with("- Paxos") || line.starts_with("- 2PC") || line.starts_with("- TOM") {
                arm_count += 1;
            } else if line.is_empty() {
                in_section = false;
            }
        }
    }
    assert_eq!(arm_count, 6, "Expected 6 arm lines under Snapshot vs run totals, found {}", arm_count);
    assert!(prog_md.contains("100"), "missing 100 in progress_README.md");
    assert!(prog_md.contains("99"), "missing 99 in progress_README.md");
    assert!(prog_md.contains("reporting") || prog_md.contains("mismatch"), "missing reporting mismatch words");

    // T5: NUMBER_AUDIT.md contains the exact test count
    let audit_md = fs::read_to_string("docs/validation/paper-audit/NUMBER_AUDIT.md").unwrap();
    assert!(audit_md.contains("9 / 3 / 20"));

    // T6: Evidence blobs are byte-identical
    fn assert_blob(path: &Path, expected_sha: &str) {
        let content = fs::read(path).unwrap_or_else(|e| panic!("Failed to read {}: {}", path.display(), e));
        let mut hasher = sha1_smol::Sha1::new();
        hasher.update(format!("blob {}\0", content.len()).as_bytes());
        hasher.update(&content);
        assert_eq!(hasher.digest().to_string(), expected_sha, "Blob SHA mismatch for {}", path.display());
    }
    assert_blob(&sources_dir.join("per_decision_energy.csv"), "7386c9467760b7c4bacb50d30705dfc7f00b0e8f");
    assert_blob(&sources_dir.join("distribution_stats.csv"), "ace5a6b0e265259991efde61df3f8c65805543a0");
    assert_blob(&sources_dir.join("distribution_stats.md"), "73a554b1daf40c8206de2fd85256b9592ffba345");
    assert_blob(&sources_dir.join("integer_multiple_check.md"), "7c9cfbe521a3d082fbfa3ae254d7110164032def");

    // T7: calibration.lock.toml blob is fd88f784e18062c075f0b9c8a940918c87b2d0cf
    assert_blob(Path::new("profiles/calibration.lock.toml"), "fd88f784e18062c075f0b9c8a940918c87b2d0cf");

    // T8: .gitignore blob is 420330edbd2721dd41114c1a8c7653c395a4c7af
    assert_blob(Path::new(".gitignore"), "420330edbd2721dd41114c1a8c7653c395a4c7af");

    // T9: paper.tex blob is 55bbd7b12b3bb0631f5ccccb3b5455ac0ba49ede
    assert_blob(Path::new("paper/paper.tex"), "55bbd7b12b3bb0631f5ccccb3b5455ac0ba49ede");
}

#[test]
fn step_210b_assertions() {
    use std::fs;
    use std::path::Path;

    let paper = fs::read_to_string("paper/paper.tex").unwrap();

    // T1: paper/paper.tex contains exactly zero occurrences of the string "190\,180".
    assert!(
        !paper.contains("190\\,180"),
        "paper still contains 190\\,180"
    );

    // T2: paper/paper.tex contains no line consisting solely of the word "is".
    for (i, line) in paper.lines().enumerate() {
        assert_ne!(
            line.trim(),
            "is",
            "line {} consists solely of the word 'is'",
            i + 1
        );
    }

    // T3: paper/paper.tex contains no line shorter than 36 characters inside the
    // "Distributed decision" paragraph other than the paragraph command itself.
    let start_idx = paper.find("\\paragraph{Distributed decision}").unwrap();
    let end_idx = paper[start_idx..].find("\n\n").unwrap() + start_idx;
    let para = &paper[start_idx..end_idx];
    for line in para.lines() {
        let trimmed = line.trim();
        if !trimmed.is_empty() && !trimmed.starts_with("\\paragraph") {
            assert!(
                trimmed.len() >= 36,
                "line too short ({} chars): {}",
                trimmed.len(),
                trimmed
            );
        }
    }

    // T4: Every file listed in section 2 exists under docs/validation/paper-audit/sources/ and is non-empty.
    let sources_dir = Path::new("docs/validation/paper-audit/sources");
    let files = [
        "progress_snapshots.csv",
        "progress_README.md",
        "slots_per_decision.csv",
        "slots_per_decision.md",
        "per_decision_energy.csv",
        "distribution_stats.csv",
        "distribution_stats.md",
        "integer_multiple_check.md",
    ];
    for f in &files {
        let p = sources_dir.join(f);
        assert!(p.exists(), "file {} does not exist", p.display());
        let metadata = fs::metadata(&p).unwrap();
        assert!(metadata.len() > 0, "file {} is empty", p.display());
    }

    // T5: progress_snapshots.csv contains all six protocol labels used by
    // plots/progress/plot_progress.py, and at least two distinct slot values per protocol.
    let progress_csv = fs::read_to_string(sources_dir.join("progress_snapshots.csv")).unwrap();
    let mut labels = std::collections::HashSet::new();
    let mut slot_counts = std::collections::HashMap::new();
    for line in progress_csv.lines().skip(1) {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() >= 2 {
            labels.insert(parts[0].to_string());
            slot_counts
                .entry(parts[0].to_string())
                .or_insert_with(std::collections::HashSet::new)
                .insert(parts[1].to_string());
        }
    }
    let expected_labels = [
        "Paxos (CI)",
        "2PC (CI)",
        "TOM (CI)",
        "Paxos (CE)",
        "2PC (CE)",
        "TOM (CE)",
    ];
    for label in &expected_labels {
        assert!(labels.contains(*label), "missing protocol label {}", label);
        assert!(
            slot_counts.get(*label).unwrap().len() >= 2,
            "less than two distinct slots for {}",
            label
        );
    }

    // T6: per_decision_energy.csv row count equals the N reported in
    // integer_multiple_check.md for the CE reference population.
    let energy_csv = fs::read_to_string(sources_dir.join("per_decision_energy.csv")).unwrap();
    let ce_rows = energy_csv
        .lines()
        .skip(1)
        .filter(|l| l.starts_with("CE,"))
        .count();
    let check_md = fs::read_to_string(sources_dir.join("integer_multiple_check.md")).unwrap();
    let n_line = check_md
        .lines()
        .find(|l| l.starts_with("N (number of"))
        .unwrap();
    let reported_n: usize = n_line.split(':').nth(1).unwrap().trim().parse().unwrap();
    assert_eq!(
        ce_rows, reported_n,
        "row count {} does not match reported N {}",
        ce_rows, reported_n
    );

    // T7: distribution_stats.csv contains one row per family with all eight summary
    // columns populated and q1 <= median <= q3 for every row.
    let stats_csv = fs::read_to_string(sources_dir.join("distribution_stats.csv")).unwrap();
    for line in stats_csv.lines().skip(1) {
        let parts: Vec<&str> = line.split(',').collect();
        assert_eq!(
            parts.len(),
            9,
            "stats row has {} columns instead of 9",
            parts.len()
        );
        let q1: f64 = parts[4].parse().unwrap();
        let median: f64 = parts[5].parse().unwrap();
        let q3: f64 = parts[6].parse().unwrap();
        assert!(
            q1 <= median && median <= q3,
            "quartiles out of order: q1={}, median={}, q3={}",
            q1,
            median,
            q3
        );
    }

    // T8: .gitignore is byte-identical to blob 420330edbd2721dd41114c1a8c7653c395a4c7af.
    let gitignore = fs::read_to_string(".gitignore").unwrap();
    let mut sha1 = sha1_smol::Sha1::new();
    sha1.update(format!("blob {}\0", gitignore.len()).as_bytes());
    sha1.update(gitignore.as_bytes());
    assert_eq!(
        sha1.digest().to_string(),
        "420330edbd2721dd41114c1a8c7653c395a4c7af",
        ".gitignore was modified"
    );

    // T9: profiles/calibration.lock.toml is unchanged and still declares p* = 0.05.
    let calibration = fs::read_to_string("profiles/calibration.lock.toml").unwrap();
    let mut sha1_cal = sha1_smol::Sha1::new();
    sha1_cal.update(format!("blob {}\0", calibration.len()).as_bytes());
    sha1_cal.update(calibration.as_bytes());
    assert_eq!(
        sha1_cal.digest().to_string(),
        "fd88f784e18062c075f0b9c8a940918c87b2d0cf",
        "calibration.lock.toml was modified"
    );
    assert!(calibration.contains("0.05"), "p* != 0.05");
}
