use ctsim::config::{CeConfig, NetworkConfig, SimConfig};
use ctsim::network::NetworkGraph;
use ctsim::protocol::ProposalOutcome;
use ctsim::run::run_experiment;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use std::env;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

const NS: [usize; 8] = [60, 90, 120, 150, 180, 188, 240, 2];
const SWEEP_NS: [usize; 6] = [60, 90, 120, 150, 180, 240];
const SEEDS: [u64; 15] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];
const MAX_GENERATION_ATTEMPTS: usize = 100;

fn admissible(graph: &NetworkGraph, n: usize) -> bool {
    let mean = 2.0 * graph.edge_count() as f64 / n as f64;
    (mean - 0.5 * n as f64).abs() <= 0.05 * 0.5 * n as f64 && graph.diameter() == 2
}

fn generate(n: usize, min_deg: usize, max_deg: usize, seed: u64) -> Option<NetworkGraph> {
    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    (0..MAX_GENERATION_ATTEMPTS).find_map(|_| {
        let graph = NetworkGraph::random_topology(n, min_deg, max_deg, &mut rng);
        admissible(&graph, n).then_some(graph)
    })
}

fn selected_window(n: usize) -> Option<(usize, usize)> {
    match n {
        // Published anchors remain pinned because the search independently selects
        // (72,72)/(75,75), not their historical (74,78)/(76,80) arguments.
        180 => Some((74, 78)),
        188 => Some((76, 80)),
        _ => solve_window(n),
    }
}

fn candidate_windows(n: usize) -> impl Iterator<Item = (usize, usize)> {
    let centre = (0.4 * n as f64).round() as isize;
    (0..n).flat_map(move |distance| {
        let distance = distance as isize;
        [centre - distance, centre + distance]
            .into_iter()
            .filter(move |min| *min >= 1 && *min < n as isize)
            .flat_map(move |min| (0..=8).map(move |width| (min as usize, min as usize + width)))
            .filter(move |(_, max)| *max < n)
    })
}

fn solve_window(n: usize) -> Option<(usize, usize)> {
    candidate_windows(n).find(|&(min_deg, max_deg)| {
        SEEDS
            .iter()
            .all(|&seed| generate(n, min_deg, max_deg, seed).is_some())
    })
}

fn graph_stats(graph: &NetworkGraph) -> (usize, f64, f64, usize, usize, usize) {
    let degrees: Vec<usize> = (0..graph.num_nodes())
        .map(|node| graph.neighbors(node).len())
        .collect();
    let mean = degrees.iter().sum::<usize>() as f64 / degrees.len() as f64;
    let variance = degrees
        .iter()
        .map(|&degree| (degree as f64 - mean).powi(2))
        .sum::<f64>()
        / degrees.len() as f64;
    (
        graph.edge_count(),
        mean,
        variance,
        *degrees.iter().min().unwrap(),
        *degrees.iter().max().unwrap(),
        graph.diameter(),
    )
}

fn write_graph(path: &Path, graph: &NetworkGraph) {
    let mut out = BufWriter::new(File::create(path).unwrap());
    writeln!(out, "{}", graph.num_nodes()).unwrap();
    for node in 0..graph.num_nodes() {
        for neighbor in graph.neighbors(node) {
            if node < neighbor {
                writeln!(out, "{node} {neighbor}").unwrap();
            }
        }
    }
}

fn run_one(n: usize, seed: u64, graph_path: &Path, protocol: &str) -> String {
    let config = SimConfig {
        seed,
        phy_mode: "ce".into(),
        protocol: protocol.into(),
        network: NetworkConfig {
            num_nodes: n,
            topology: "random".into(),
            loss_rate: 0.05,
            graph_file: Some(graph_path.display().to_string()),
        },
        ci: None,
        ce: Some(CeConfig {
            listen_timeout: 5,
            max_round_slots: 4000,
        }),
        num_proposals: 100,
        snapshot_interval: 1_000_000,
        max_slots: 5_000_000,
        abort_probability: 0.0,
        quiet: true,
    };
    let started = Instant::now();
    let result = run_experiment(config);
    let latencies: Vec<u64> = result.metrics.proposals.iter().map(|p| p.latency).collect();
    let mean_latency = latencies.iter().sum::<u64>() as f64 / latencies.len() as f64;
    let committed = result
        .metrics
        .proposals
        .iter()
        .filter(|p| p.outcome == ProposalOutcome::Committed)
        .count();
    format!(
        "{n},{protocol},{seed},{mean_latency:.6},{mean_latency:.6},{committed},{},{:.6}",
        latencies.len(),
        started.elapsed().as_secs_f64()
    )
}

fn main() {
    let mode = env::args().nth(1).unwrap_or_else(|| "search".into());
    let out = PathBuf::from("docs/validation/addition15/data");
    fs::create_dir_all(&out).unwrap();

    println!("acceptance: abs(mean_degree - 0.5*N) <= 0.05*(0.5*N), diameter == 2");
    println!("search: centre=round(0.4*N); min_deg by increasing distance, lower before upper; width 0..=8; max_deg<N; attempts=100; seeds={SEEDS:?}");

    if mode == "search" {
        for n in NS {
            println!(
                "N={n} searched={:?} selected={:?}",
                solve_window(n),
                selected_window(n)
            );
        }
        return;
    }

    let mut provenance =
        BufWriter::new(File::create(out.join("graph_provenance_dense.csv")).unwrap());
    writeln!(provenance, "n,seed,min_deg_arg,max_deg_arg,edges,mean_degree,degree_variance,min_degree,max_degree,diameter,graph_file").unwrap();
    let mut rows = BufWriter::new(File::create(out.join("n_sweep.csv")).unwrap());
    writeln!(rows, "n,arm,seed,mean_round_slots,mean_decision_latency_slots,committed,proposals,elapsed_seconds").unwrap();

    let ns: Vec<usize> = if mode == "cost" {
        vec![240]
    } else {
        SWEEP_NS.to_vec()
    };
    for n in ns {
        let (min_deg, max_deg) = selected_window(n).unwrap_or_else(|| {
            panic!("N={n}: no generator window satisfies the fixed acceptance criterion")
        });
        let seeds: &[u64] = if mode == "cost" { &SEEDS[..1] } else { &SEEDS };
        for &seed in seeds {
            let anchored_path =
                PathBuf::from(format!("profiles/graphs/random_n{n}_dense_seed{seed}.txt"));
            let graph = if n == 180 || n == 188 {
                NetworkGraph::from_file(&anchored_path).unwrap_or_else(|error| {
                    panic!(
                        "failed to load pinned graph {}: {error}",
                        anchored_path.display()
                    )
                })
            } else {
                generate(n, min_deg, max_deg, seed).unwrap()
            };
            let (edges, mean, variance, min_real, max_real, diameter) = graph_stats(&graph);
            assert!(
                admissible(&graph, n),
                "N={n} seed={seed}: graph is inadmissible"
            );
            let graph_path = if n == 180 || n == 188 {
                anchored_path
            } else {
                let path = PathBuf::from(format!("/tmp/addition15_graph_n{n}_seed{seed}.txt"));
                write_graph(&path, &graph);
                path
            };
            writeln!(provenance, "{n},{seed},{min_deg},{max_deg},{edges},{mean:.6},{variance:.6},{min_real},{max_real},{diameter},{}", graph_path.display()).unwrap();
            provenance.flush().unwrap();
            for protocol in ["2pc_ce", "paxos_ce"] {
                println!("run N={n} seed={seed} arm={protocol}");
                std::io::stdout().flush().unwrap();
                writeln!(rows, "{}", run_one(n, seed, &graph_path, protocol)).unwrap();
                rows.flush().unwrap();
            }
            if n != 180 && n != 188 {
                fs::remove_file(graph_path).unwrap();
            }
        }
    }
}
