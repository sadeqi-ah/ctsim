use ctsim::config::{CeConfig, NetworkConfig, SimConfig};
use ctsim::network::NetworkGraph;
use ctsim::protocol::ProposalOutcome;
use ctsim::run::run_experiment;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use std::env;
use std::fs::OpenOptions;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

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

fn solve_window(n: usize) -> Option<(usize, usize)> {
    let w = 10;
    let target = 0.5 * n as f64;
    let mut best_error = f64::MAX;
    let mut best_window = None;

    let start = (0.3 * n as f64) as usize;
    let end = (0.5 * n as f64) as usize;

    for center in start..=end {
        let min_deg = center;
        let max_deg = center + w;
        if max_deg >= n {
            continue;
        }

        let mut valid = true;
        let mut sum_mean = 0.0;

        for &seed in &SEEDS {
            let mut rng = ChaCha8Rng::seed_from_u64(seed);
            let mut found = false;
            for _ in 0..MAX_GENERATION_ATTEMPTS {
                let graph = NetworkGraph::random_topology(n, min_deg, max_deg, &mut rng);
                if admissible(&graph, n) {
                    sum_mean += 2.0 * graph.edge_count() as f64 / n as f64;
                    found = true;
                    break;
                }
            }
            if !found {
                valid = false;
                break;
            }
        }

        if valid {
            let seed_mean = sum_mean / SEEDS.len() as f64;
            let error = (seed_mean - target).abs() / target;
            if error < best_error {
                best_error = error;
                best_window = Some((min_deg, max_deg));
            }
        }
    }

    if best_error <= 0.01 {
        best_window
    } else {
        None
    }
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
    println!("search: sweep min_deg to minimize density error across seeds, width W=10. Requires density error <= 1%.");

    if mode == "search" {
        for n in SWEEP_NS {
            println!("N={n} selected={:?}", solve_window(n));
        }
        return;
    }

    let prov_tmp = out.join("graph_provenance_dense_tmp.csv");
    let mut provenance = BufWriter::new(
        OpenOptions::new()
            .create(true)
            .truncate(true)
            .write(true)
            .open(&prov_tmp)
            .unwrap(),
    );
    writeln!(provenance, "n,seed,min_deg_arg,max_deg_arg,edges,mean_degree,degree_variance,min_degree,max_degree,diameter,graph_file").unwrap();

    let rows_tmp = out.join("n_sweep_tmp.csv");
    let mut rows = BufWriter::new(
        OpenOptions::new()
            .create(true)
            .truncate(true)
            .write(true)
            .open(&rows_tmp)
            .unwrap(),
    );
    writeln!(rows, "n,arm,seed,mean_round_slots,mean_decision_latency_slots,committed,proposals,elapsed_seconds").unwrap();

    let ns: Vec<usize> = if mode == "cost" {
        vec![240]
    } else if let Ok(n_val) = mode.parse::<usize>() {
        vec![n_val]
    } else {
        SWEEP_NS.to_vec()
    };
    for &n in &ns {
        let (min_deg, max_deg) = solve_window(n).unwrap_or_else(|| {
            panic!("N={n}: no generator window satisfies the fixed acceptance criterion")
        });
        let seeds: &[u64] = if mode == "cost" { &SEEDS[..1] } else { &SEEDS };
        for &seed in seeds {
            let graph = generate(n, min_deg, max_deg, seed).unwrap();
            let (edges, mean, variance, min_real, max_real, diameter) = graph_stats(&graph);
            assert!(
                admissible(&graph, n),
                "N={n} seed={seed}: graph is inadmissible"
            );
            let path = PathBuf::from(format!(
                "docs/validation/addition15/data/graph_n{n}_seed{seed}.txt"
            ));
            write_graph(&path, &graph);
            let graph_path = path;
            writeln!(provenance, "{n},{seed},{min_deg},{max_deg},{edges},{mean:.6},{variance:.6},{min_real},{max_real},{diameter},{}", graph_path.display()).unwrap();
            provenance.flush().unwrap();
            for protocol in ["2pc_ce", "paxos_ce"] {
                println!("run N={n} seed={seed} arm={protocol}");
                std::io::stdout().flush().unwrap();
                writeln!(rows, "{}", run_one(n, seed, &graph_path, protocol)).unwrap();
                rows.flush().unwrap();
            }
        }
    }

    provenance.flush().unwrap();
    rows.flush().unwrap();
    drop(provenance);
    drop(rows);

    if ns == SWEEP_NS {
        fs::rename(&prov_tmp, out.join("graph_provenance_dense.csv")).unwrap();
        fs::rename(&rows_tmp, out.join("n_sweep.csv")).unwrap();
    }
}
