//! Freeze large random topologies to deterministic adjacency files.
//!
//! For each (n, arm, seed) triple this binary:
//! 1. Builds the graph in-memory with the documented RNG parameters.
//! 2. Writes it to `profiles/graphs/random_n{n}[_{arm}]_seed{seed}.txt`.
//! 3. Reads it back and asserts exact equality (round-trip gate).
//! 4. Checks connectivity via BFS.
//! 5. Emits `docs/validation/addition13/data/graph_provenance_large.csv`.

use ctsim::network::NetworkGraph;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use std::collections::VecDeque;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::Command;

const SEEDS: [u64; 15] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];

struct ArmSpec {
    label: &'static str,
    min_deg: usize,
    max_deg: usize,
}

const ARMS: [ArmSpec; 3] = [
    ArmSpec {
        label: "base",
        min_deg: 2,
        max_deg: 5,
    },
    ArmSpec {
        label: "deg_minus1",
        min_deg: 1,
        max_deg: 4,
    },
    ArmSpec {
        label: "deg_plus1",
        min_deg: 3,
        max_deg: 6,
    },
];

const NODE_COUNTS: [usize; 2] = [180, 188];

fn graph_file_name(n: usize, arm: &str, seed: u64) -> String {
    if arm == "base" {
        format!("profiles/graphs/random_n{n}_seed{seed}.txt")
    } else {
        format!("profiles/graphs/random_n{n}_{arm}_seed{seed}.txt")
    }
}

fn write_graph(graph: &NetworkGraph, path: &str) {
    let n = graph.num_nodes();
    let mut edges: Vec<(usize, usize)> = Vec::new();
    for u in 0..n {
        for v in graph.neighbors(u) {
            if u < v {
                edges.push((u, v));
            }
        }
    }
    edges.sort();

    let dir = Path::new(path).parent().unwrap();
    fs::create_dir_all(dir).unwrap();

    let mut f = fs::File::create(path).unwrap();
    writeln!(f, "{n}").unwrap();
    for (u, v) in &edges {
        writeln!(f, "{u} {v}").unwrap();
    }
}

fn roundtrip_gate(expected: &NetworkGraph, path: &str) {
    let loaded = NetworkGraph::from_file(Path::new(path))
        .unwrap_or_else(|e| panic!("failed to load {path}: {e}"));

    assert_eq!(
        expected.num_nodes(),
        loaded.num_nodes(),
        "{path}: num_nodes mismatch"
    );
    assert_eq!(
        expected.edge_count(),
        loaded.edge_count(),
        "{path}: edge_count mismatch ({} vs {})",
        expected.edge_count(),
        loaded.edge_count()
    );
    for i in 0..expected.num_nodes() {
        assert_eq!(
            expected.neighbors(i),
            loaded.neighbors(i),
            "{path}: neighbors({i}) differ"
        );
    }
}

fn bfs_reachable(graph: &NetworkGraph) -> usize {
    let n = graph.num_nodes();
    let mut visited = vec![false; n];
    let mut queue = VecDeque::new();
    visited[0] = true;
    queue.push_back(0);
    let mut count = 0;
    while let Some(u) = queue.pop_front() {
        count += 1;
        for v in graph.neighbors(u) {
            if !visited[v] {
                visited[v] = true;
                queue.push_back(v);
            }
        }
    }
    count
}

fn degree_stats(graph: &NetworkGraph) -> (usize, usize, Vec<(usize, usize)>) {
    let n = graph.num_nodes();
    let mut min_d = usize::MAX;
    let mut max_d = 0;
    let mut deg_counts = std::collections::BTreeMap::new();
    for i in 0..n {
        let d = graph.neighbors(i).len();
        min_d = min_d.min(d);
        max_d = max_d.max(d);
        *deg_counts.entry(d).or_insert(0usize) += 1;
    }
    let histogram: Vec<(usize, usize)> = deg_counts.into_iter().collect();
    (min_d, max_d, histogram)
}

fn sha256_file(path: &str) -> String {
    // Cargo.lock has no SHA-256 crate; prefer Linux sha256sum, then macOS shasum.
    let output = match Command::new("sha256sum").arg(path).output() {
        Ok(output) => output,
        Err(sha256sum_error) if sha256sum_error.kind() == std::io::ErrorKind::NotFound => {
            Command::new("shasum")
                .args(["-a", "256", path])
                .output()
                .unwrap_or_else(|shasum_error| {
                    panic!(
                        "neither sha256sum nor shasum -a 256 is available: \
                         sha256sum: {sha256sum_error}; shasum: {shasum_error}"
                    )
                })
        }
        Err(error) => panic!("failed to run sha256sum for {path}: {error}"),
    };
    assert!(output.status.success(), "sha256 command failed for {path}");
    let stdout = String::from_utf8(output.stdout).unwrap();
    stdout.split_whitespace().next().unwrap().to_string()
}

fn main() {
    let csv_dir = "docs/validation/addition13/data";
    fs::create_dir_all(csv_dir).unwrap();

    let csv_path = format!("{csv_dir}/graph_provenance_large.csv");
    let mut csv = fs::File::create(&csv_path).unwrap();
    writeln!(
        csv,
        "n,arm,seed,num_nodes,edges,diameter,mean_degree,min_degree,max_degree,degree1_count,degree2_count,degree_histogram,sha256_graph_file"
    )
    .unwrap();

    let mut total_graphs = 0u32;

    for &n in &NODE_COUNTS {
        for arm in &ARMS {
            for &seed in &SEEDS {
                let mut rng = ChaCha8Rng::seed_from_u64(seed);
                let graph = NetworkGraph::random_topology(n, arm.min_deg, arm.max_deg, &mut rng);

                let path = graph_file_name(n, arm.label, seed);
                write_graph(&graph, &path);
                roundtrip_gate(&graph, &path);

                let reachable = bfs_reachable(&graph);
                if reachable != n {
                    eprintln!("DISCONNECTED: {path} — BFS from 0 reached {reachable}/{n}");
                    std::process::exit(1);
                }

                let edges = graph.edge_count();
                let diameter = graph.diameter();
                let mean_degree = 2.0 * edges as f64 / n as f64;
                let (min_d, max_d, histogram) = degree_stats(&graph);

                let deg1_count = histogram
                    .iter()
                    .find(|&&(d, _)| d == 1)
                    .map(|&(_, c)| c)
                    .unwrap_or(0);
                let deg2_count = histogram
                    .iter()
                    .find(|&&(d, _)| d == 2)
                    .map(|&(_, c)| c)
                    .unwrap_or(0);

                let hist_str: String = histogram
                    .iter()
                    .map(|(d, c)| format!("{d}:{c}"))
                    .collect::<Vec<_>>()
                    .join("|");

                let sha = sha256_file(&path);

                writeln!(
                    csv,
                    "{n},{},{seed},{},{edges},{diameter},{mean_degree:.6},{min_d},{max_d},{deg1_count},{deg2_count},{hist_str},{sha}",
                    arm.label,
                    graph.num_nodes(),
                )
                .unwrap();

                total_graphs += 1;
                println!(
                    "OK  n={n:3} arm={:12} seed={seed:2}  edges={edges:4}  diameter={diameter:2}  mean_deg={mean_degree:.3}  min={min_d} max={max_d}  connected=true",
                    arm.label,
                );
            }
        }
    }

    println!("\nAll {total_graphs} graphs written, round-tripped and connected.");
    println!("Provenance CSV: {csv_path}");
}
