//! Freeze dense random topologies to deterministic adjacency files.
//!
//! For each (n, seed) triple this binary:
//! 1. Builds the graph in-memory with dense degree parameters (0.5 * n ± 5%).
//! 2. Writes it to `profiles/graphs/random_n{n}_dense_seed{seed}.txt`.
//! 3. Reads it back and asserts exact equality (round-trip gate).
//! 4. Checks connectivity via BFS.
//! 5. Asserts mean degree within 5% of 0.5*n and diameter == 2.
//! 6. Emits `docs/validation/addition14/data/graph_provenance_dense.csv`.

use ctsim::network::NetworkGraph;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use std::collections::VecDeque;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::Command;

const SEEDS: [u64; 15] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];
const NODE_COUNTS: [usize; 2] = [180, 188];
const MAX_GENERATION_ATTEMPTS: usize = 100;

fn calibrated_degree_window(n: usize) -> (usize, usize) {
    match n {
        180 => (74, 78),
        188 => (76, 80),
        _ => panic!("no calibrated dense window for n={n}"),
    }
}

fn generate_dense_graph(n: usize, seed: u64) -> NetworkGraph {
    let (min_deg, max_deg) = calibrated_degree_window(n);
    let expected_mean = 0.5 * n as f64;
    let tolerance = 0.05 * expected_mean;

    let mut rng = ChaCha8Rng::seed_from_u64(seed);
    for _attempt in 1..=MAX_GENERATION_ATTEMPTS {
        let graph = NetworkGraph::random_topology(n, min_deg, max_deg, &mut rng);
        let mean_degree = 2.0 * graph.edge_count() as f64 / n as f64;
        if (mean_degree - expected_mean).abs() <= tolerance && graph.diameter() == 2 {
            return graph;
        }
    }

    panic!(
        "dense graph generation failed after {MAX_GENERATION_ATTEMPTS} attempts for seed={seed}, n={n}: \
         could not satisfy mean degree within 5% of 0.5*n and diameter == 2"
    );
}

fn graph_file_name(n: usize, seed: u64) -> String {
    format!("profiles/graphs/random_n{n}_dense_seed{seed}.txt")
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
    // Try sha256sum (Linux) first, then shasum -a 256 (macOS).
    let output = Command::new("sha256sum")
        .arg(path)
        .output()
        .or_else(|_| Command::new("shasum").args(["-a", "256", path]).output())
        .expect("failed to run sha256sum or shasum -a 256");
    assert!(output.status.success(), "sha256 command failed for {path}");
    let stdout = String::from_utf8(output.stdout).unwrap();
    stdout.split_whitespace().next().unwrap().to_string()
}

fn main() {
    let csv_dir = "docs/validation/addition14/data";
    fs::create_dir_all(csv_dir).unwrap();

    let csv_path = format!("{csv_dir}/graph_provenance_dense.csv");
    let mut csv = fs::File::create(&csv_path).unwrap();
    writeln!(
        csv,
        "n,arm,seed,num_nodes,edges,diameter,mean_degree,min_degree,max_degree,degree1_count,degree2_count,degree_histogram,sha256_graph_file"
    )
    .unwrap();

    let mut total_graphs = 0u32;

    for &n in &NODE_COUNTS {
        // Dense arm: target output mean degree ~0.5*n.
        // random_topology's bidirectional edge insertion inflates actual degree
        // above the input parameters. Empirical calibration (averaged over 5
        // seeds) gives these input windows:
        //   n=180: center=76 (min=74, max=78) → output mean ≈ 91.0 ≈ 0.506*n ✓
        //   n=188: center=78 (min=76, max=80) → output mean ≈ 93.2 ≈ 0.496*n ✓
        // Both are within the 5% tolerance band around 0.5*n.
        // Intentional call acting purely as an early guard for uncalibrated n.
        calibrated_degree_window(n);

        for &seed in &SEEDS {
            let graph = generate_dense_graph(n, seed);

            let path = graph_file_name(n, seed);
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

            // B6: mean degree within 5% of 0.5*n
            let expected_mean = 0.5 * n as f64;
            let tolerance = 0.05 * expected_mean;
            assert!(
                (mean_degree - expected_mean).abs() <= tolerance,
                "{path}: mean degree {mean_degree:.4} is not within 5% of {expected_mean:.1} \
                 (tolerance ±{tolerance:.2})"
            );

            // B6: diameter must be exactly 2
            assert_eq!(
                diameter, 2,
                "{path}: diameter is {diameter}, expected exactly 2"
            );

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
                "{n},dense,{seed},{},{edges},{diameter},{mean_degree:.6},{min_d},{max_d},{deg1_count},{deg2_count},{hist_str},{sha}",
                graph.num_nodes(),
            )
            .unwrap();

            total_graphs += 1;
            println!(
                "OK  n={n:3} arm=dense        seed={seed:2}  edges={edges:5}  diameter={diameter}  mean_deg={mean_degree:.3}  min={min_d} max={max_d}  connected=true",
            );
        }
    }

    println!("\nAll {total_graphs} dense graphs written, round-tripped and connected.");
    println!("Provenance CSV: {csv_path}");
}
