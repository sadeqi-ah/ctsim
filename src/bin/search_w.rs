use ctsim::network::NetworkGraph;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

const SEEDS: [u64; 15] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47];
const NS: [usize; 7] = [60, 90, 120, 150, 180, 188, 240];

fn main() {
    let mut best_w = 0;
    let mut best_max_err = f64::MAX;
    for w in 0..=20 {
        let mut max_err = 0.0;
        for &n in &NS {
            let target = 0.5 * n as f64;
            let mut best_error = f64::MAX;
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
                    for _ in 0..100 {
                        let graph = NetworkGraph::random_topology(n, min_deg, max_deg, &mut rng);
                        let mean_degree = 2.0 * graph.edge_count() as f64 / n as f64;
                        if (mean_degree - target).abs() <= 0.05 * target && graph.diameter() == 2 {
                            sum_mean += mean_degree;
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
                    let seed_mean = sum_mean / 15.0;
                    let error = (seed_mean - target).abs() / target;
                    if error < best_error {
                        best_error = error;
                    }
                }
            }
            if best_error > max_err {
                max_err = best_error;
            }
        }
        println!("W={} max_error={:.4}%", w, max_err * 100.0);
        if max_err < best_max_err {
            best_max_err = max_err;
            best_w = w;
        }
    }
    println!(
        "Best W={} with max error {:.4}%",
        best_w,
        best_max_err * 100.0
    );
}
