# Addition 15 Verification

## L1

```text
$ gh run view 34499786222 --job 102957096129 --log
figures	Check Addition 15 generated report	﻿2026-09-10T16:32:34.8020224Z ##[group]Run python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8020891Z ^[[36;1mpython3 docs/validation/addition15/scripts/analyze_n_sweep.py --check^[[0m
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8060190Z shell: /usr/bin/bash -e {0}
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8060454Z env:
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8060735Z   pythonLocation: /opt/hostedtoolcache/Python/3.11.16/x64
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8061183Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.16/x64/lib/pkgconfig
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8061607Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8061987Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8062368Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8062776Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.16/x64/lib
figures	Check Addition 15 generated report	2026-09-10T16:32:34.8063100Z ##[endgroup]
figures	Check Addition 15 generated report	2026-09-10T16:32:39.0495117Z ERROR: README.md does not match generated content. Hand-edited numbers detected.
figures	Check Addition 15 generated report	2026-09-10T16:32:39.1276499Z ##[error]Process completed with exit code 1.
```

## X1

```text
$ git status --porcelain
$ git rev-parse HEAD
8b497991ee8efa58bfc69a24a17984f196505f43
```

## X2

```text
$ git diff --stat main...HEAD
 .github/workflows/ci.yml                           |  3 +
 docs/validation/addition15/README.md               |  7 +-
 .../addition15/scripts/analyze_n_sweep.py          | 98 +++++++++++++++++-----
 3 files changed, 84 insertions(+), 24 deletions(-)
```

## X3

```text
$ git hash-object docs/validation/addition15/README.md
ac323033040be4e58dcde554d142fe5f6bf26e28
```

## X4

```text
$ python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
README check passed.
```

## X5

```text
$ git diff --stat main...HEAD -- docs/validation/addition15/data/ profiles/
```

## X6

```text
$ git hash-object profiles/calibration.lock.toml
fd88f784e18062c075f0b9c8a940918c87b2d0cf
```

## X7

```text
$ shasum -a 256 docs/validation/addition9/data/sweep_summary_topology.csv plots/scalability/results/sweep_summary.csv
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  docs/validation/addition9/data/sweep_summary_topology.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
```

## X8

```text
$ git ls-tree -r HEAD -- profiles/graphs/ | awk '$4 ~ /random_n(180|188)_dense_seed[0-9]+\.txt$/ {print $3, $4}' | sort
121ccf713a7c9b33860e54c947e03c798eb6d927 profiles/graphs/random_n188_dense_seed5.txt
12aa49088a5ef1d97eccf580c4aebc06bb932288 profiles/graphs/random_n188_dense_seed3.txt
14ef068c1d29c31f7a857ac1bb6d474d43c4252a profiles/graphs/random_n188_dense_seed13.txt
161c3522765fc32d09e94efb4c49b783f42d5627 profiles/graphs/random_n188_dense_seed17.txt
162cc288f489e5ecb8eecec9611741906b6d1031 profiles/graphs/random_n180_dense_seed13.txt
1dcea612985d8fb44b814b21b79f8435c9824f2d profiles/graphs/random_n180_dense_seed17.txt
26d3c8c51fc9e3ed336a08ab1e17432cd382cb9c profiles/graphs/random_n180_dense_seed41.txt
2b62ac7775d6b2a159066c3855f35796618512bd profiles/graphs/random_n188_dense_seed11.txt
2f49825d6c37601cd0684e178452c3779a942faf profiles/graphs/random_n180_dense_seed37.txt
3743870e97f389ae2ac3b67f58f4eb7652e49bf8 profiles/graphs/random_n188_dense_seed41.txt
3d89fbb7f22dbaa288d37e724c06f020c49e2882 profiles/graphs/random_n180_dense_seed19.txt
5b2b75b40eecbe8dfa6407a695bd791f708d38f6 profiles/graphs/random_n180_dense_seed3.txt
6eff63e176396460c667a6acb382829812014dd4 profiles/graphs/random_n180_dense_seed5.txt
6fddbb3d4ac5ad70b9ca69c1c7c41e0e38c609ad profiles/graphs/random_n188_dense_seed37.txt
74d856c428ba04e12286a266f5206c6d2079b2a3 profiles/graphs/random_n180_dense_seed11.txt
7555ace5d15765625da2943cb264f2848c4288f0 profiles/graphs/random_n188_dense_seed19.txt
7ecc07243aa2271e1b6ac0dc733c3022f62ab6c8 profiles/graphs/random_n180_dense_seed7.txt
94eb3bec724657b7d855873957b35f76aa698a2e profiles/graphs/random_n180_dense_seed47.txt
9979603f2f6d8954a369a32f253acdc7027bde7a profiles/graphs/random_n188_dense_seed43.txt
9dc0b5d27ad0f23a2aab669cc07f1c3914c86359 profiles/graphs/random_n180_dense_seed2.txt
b1887a675e4cb83a8075ab52ee583bf9b39ff2c4 profiles/graphs/random_n188_dense_seed2.txt
b34a257b4b3cc9307ec0ff89c19df143dc41e4a8 profiles/graphs/random_n180_dense_seed43.txt
b47f443f0fdeb4a5693cdfad7e9787a463a4fba5 profiles/graphs/random_n180_dense_seed29.txt
c308cb6758bd48df714f060155b23e06977c4fae profiles/graphs/random_n188_dense_seed7.txt
c8d07ec58f62389d93a3b2d027424fb2178a1119 profiles/graphs/random_n188_dense_seed29.txt
ccc548e095665d51fa1d9c299433846182b33c80 profiles/graphs/random_n188_dense_seed31.txt
d995670e87587e17105b182ee475567b4ce76771 profiles/graphs/random_n180_dense_seed31.txt
e0059ed8d86e7b53e258767cdad48128affeeb9b profiles/graphs/random_n180_dense_seed23.txt
e83b72d0e71be7065ca3fa17360ec18aab256894 profiles/graphs/random_n188_dense_seed23.txt
fe94771868db508e2892cda735513c63a9975506 profiles/graphs/random_n188_dense_seed47.txt
$ git ls-tree -r main -- profiles/graphs/ | awk '$4 ~ /random_n(180|188)_dense_seed[0-9]+\.txt$/ {print $3, $4}' | sort
121ccf713a7c9b33860e54c947e03c798eb6d927 profiles/graphs/random_n188_dense_seed5.txt
12aa49088a5ef1d97eccf580c4aebc06bb932288 profiles/graphs/random_n188_dense_seed3.txt
14ef068c1d29c31f7a857ac1bb6d474d43c4252a profiles/graphs/random_n188_dense_seed13.txt
161c3522765fc32d09e94efb4c49b783f42d5627 profiles/graphs/random_n188_dense_seed17.txt
162cc288f489e5ecb8eecec9611741906b6d1031 profiles/graphs/random_n180_dense_seed13.txt
1dcea612985d8fb44b814b21b79f8435c9824f2d profiles/graphs/random_n180_dense_seed17.txt
26d3c8c51fc9e3ed336a08ab1e17432cd382cb9c profiles/graphs/random_n180_dense_seed41.txt
2b62ac7775d6b2a159066c3855f35796618512bd profiles/graphs/random_n188_dense_seed11.txt
2f49825d6c37601cd0684e178452c3779a942faf profiles/graphs/random_n180_dense_seed37.txt
3743870e97f389ae2ac3b67f58f4eb7652e49bf8 profiles/graphs/random_n188_dense_seed41.txt
3d89fbb7f22dbaa288d37e724c06f020c49e2882 profiles/graphs/random_n180_dense_seed19.txt
5b2b75b40eecbe8dfa6407a695bd791f708d38f6 profiles/graphs/random_n180_dense_seed3.txt
6eff63e176396460c667a6acb382829812014dd4 profiles/graphs/random_n180_dense_seed5.txt
6fddbb3d4ac5ad70b9ca69c1c7c41e0e38c609ad profiles/graphs/random_n188_dense_seed37.txt
74d856c428ba04e12286a266f5206c6d2079b2a3 profiles/graphs/random_n180_dense_seed11.txt
7555ace5d15765625da2943cb264f2848c4288f0 profiles/graphs/random_n188_dense_seed19.txt
7ecc07243aa2271e1b6ac0dc733c3022f62ab6c8 profiles/graphs/random_n180_dense_seed7.txt
94eb3bec724657b7d855873957b35f76aa698a2e profiles/graphs/random_n180_dense_seed47.txt
9979603f2f6d8954a369a32f253acdc7027bde7a profiles/graphs/random_n188_dense_seed43.txt
9dc0b5d27ad0f23a2aab669cc07f1c3914c86359 profiles/graphs/random_n180_dense_seed2.txt
b1887a675e4cb83a8075ab52ee583bf9b39ff2c4 profiles/graphs/random_n188_dense_seed2.txt
b34a257b4b3cc9307ec0ff89c19df143dc41e4a8 profiles/graphs/random_n180_dense_seed43.txt
b47f443f0fdeb4a5693cdfad7e9787a463a4fba5 profiles/graphs/random_n180_dense_seed29.txt
c308cb6758bd48df714f060155b23e06977c4fae profiles/graphs/random_n188_dense_seed7.txt
c8d07ec58f62389d93a3b2d027424fb2178a1119 profiles/graphs/random_n188_dense_seed29.txt
ccc548e095665d51fa1d9c299433846182b33c80 profiles/graphs/random_n188_dense_seed31.txt
d995670e87587e17105b182ee475567b4ce76771 profiles/graphs/random_n180_dense_seed31.txt
e0059ed8d86e7b53e258767cdad48128affeeb9b profiles/graphs/random_n180_dense_seed23.txt
e83b72d0e71be7065ca3fa17360ec18aab256894 profiles/graphs/random_n188_dense_seed23.txt
fe94771868db508e2892cda735513c63a9975506 profiles/graphs/random_n188_dense_seed47.txt
$ diff <(git ls-tree -r HEAD -- profiles/graphs/ | awk '$4 ~ /random_n(180|188)_dense_seed[0-9]+\.txt$/ {print $3, $4}' | sort) <(git ls-tree -r main -- profiles/graphs/ | awk '$4 ~ /random_n(180|188)_dense_seed[0-9]+\.txt$/ {print $3, $4}' | sort)
```

## X9

```text
$ cargo test --all
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.49s
test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.29s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

## NC-A

```text
$ python3 -c 'from pathlib import Path; p=Path("docs/validation/addition15/README.md"); p.write_text(p.read_text().replace("0.13733", "0.13734", 1))'
$ python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
ERROR: README.md does not match generated content. Hand-edited numbers detected.
--- committed README.md
+++ generated README.md
@@ -69,7 +69,7 @@

 ### 2PC over CE
 *   **log(round_length) vs log(N) (Primary):**
-    *   Linear model: Slope = `0.13734` (95% CI: `[0.13101, 0.14365]`), AIC = 4.8, R² = 0.998
+    *   Linear model: Slope = `0.13733` (95% CI: `[0.13101, 0.14365]`), AIC = 4.8, R² = 0.998
     *   Constant model: AIC = 39.5, R² = 0.000
 *   **round_length vs N:**
     *   Linear model: Slope = `0.02649` (95% CI: `[0.02103, 0.03195]`), AIC = 22.9, R² = 0.958
exit code: 1
$ git checkout -- docs/validation/addition15/README.md
$ git status --porcelain
```

## NC-B

```text
$ python3 -c 'from pathlib import Path; p=Path("docs/validation/addition15/README.md"); p.write_text(p.read_text() + "\nraw { placeholder\n")'
$ python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
ERROR: Unrendered placeholder { or } found outside code blocks.
exit code: 1
$ git checkout -- docs/validation/addition15/README.md
$ git status --porcelain
```

## NC-C

```text
$ python3 -c 'from pathlib import Path; p=Path("docs/validation/addition15/README.md"); s=p.read_text(); p.write_text(s.replace("| 180 | 2PC | 3.523 | 3.508 | -0.015 |", "| 180 | 2PC | 3.523 | 3.508 | -0.015 |\n| 189 | 2PC | 3.523 | 3.508 | -0.015 |", 1))'
$ python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
Row provenance assertion failed: Anchor N=189 found in README but not in n_sweep_summary.csv!
exit code: 1
$ git checkout -- docs/validation/addition15/README.md
$ git status --porcelain
```

## NC-D

BLOCK NC-D UNAVAILABLE: the X7 topology digest hashes `docs/validation/addition9/data/sweep_summary_topology.csv`, so perturbing an anchor graph does not change that digest.

## NC-E

```text
$ git clone --branch task/addition15-n-sweep-fix --single-branch https://github.com/sadeqi-ah/ctsim.git /var/folders/lq/7p6d7nnx5_s_37rghmgnv3zr0000gn/T/tmp.Lv3mLVneQ9
Cloning into '/var/folders/lq/7p6d7nnx5_s_37rghmgnv3zr0000gn/T/tmp.Lv3mLVneQ9'...
$ cd /var/folders/lq/7p6d7nnx5_s_37rghmgnv3zr0000gn/T/tmp.Lv3mLVneQ9
$ python3 docs/validation/addition15/scripts/analyze_n_sweep.py --check
README check passed.
$ git status --porcelain
```

## X10

````text
$ nl -ba README.md | sed -n '104,113p'
   104	## Parameter sweeps
   105
   106	The same binary runs a Cartesian-product sweep when given a sweep config
   107	(any file whose name contains `sweep`). Results are collected into a single
   108	summary CSV:
   109
   110	```bash
   111	cargo run --release -- sweep_scalability.toml   # N × loss, 15 seeds
   112	cargo run --release -- sweep_topology.toml      # 5 topologies, 15 seeds
   113	```
$ cargo run --release --bin ctsim -- sweep_topology.toml && cargo run --release --bin ctsim -- sweep_scalability.toml
    Finished `release` profile [optimized] target(s) in 0.20s
     Running `target/release/ctsim sweep_topology.toml`
Starting sweep of 450 experiments...
Sweep complete. Ran 450 experiments.
Summary written to: plots/topology/results/sweep_summary.csv
    Finished `release` profile [optimized] target(s) in 0.13s
     Running `target/release/ctsim sweep_scalability.toml`
Starting sweep of 1800 experiments...
Sweep complete. Ran 1800 experiments.
Summary written to: plots/scalability/results/sweep_summary.csv
$ shasum -a 256 plots/topology/results/sweep_summary.csv plots/scalability/results/sweep_summary.csv
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  plots/topology/results/sweep_summary.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
$ python3 -c 'from pathlib import Path; import re; text=Path("docs/validation/addition13/README.md").read_text(); print("\n".join(line for line in text.splitlines() if re.match(r"^(topology|scalability) ", line.strip())))'
topology     1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329
scalability  b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7
$ git status --porcelain
````

## NC-D re-execution

NC-D FAILED: the canonical regressions do not consume `profiles/graphs/random_n180_dense_seed2.txt`; perturbing that anchor graph left both regenerated digests unchanged.

```text
$ printf 'X' >> profiles/graphs/random_n180_dense_seed2.txt
$ cargo run --release --bin ctsim -- sweep_topology.toml && cargo run --release --bin ctsim -- sweep_scalability.toml
    Finished `release` profile [optimized] target(s) in 0.13s
     Running `target/release/ctsim sweep_topology.toml`
Starting sweep of 450 experiments...
Sweep complete. Ran 450 experiments.
Summary written to: plots/topology/results/sweep_summary.csv
    Finished `release` profile [optimized] target(s) in 0.02s
     Running `target/release/ctsim sweep_scalability.toml`
Starting sweep of 1800 experiments...
Sweep complete. Ran 1800 experiments.
Summary written to: plots/scalability/results/sweep_summary.csv
$ shasum -a 256 plots/topology/results/sweep_summary.csv plots/scalability/results/sweep_summary.csv
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  plots/topology/results/sweep_summary.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
$ git checkout -- profiles/graphs/random_n180_dense_seed2.txt
$ git status --porcelain
$ cargo run --release --bin ctsim -- sweep_topology.toml && cargo run --release --bin ctsim -- sweep_scalability.toml
    Finished `release` profile [optimized] target(s) in 0.13s
     Running `target/release/ctsim sweep_topology.toml`
Starting sweep of 450 experiments...
Sweep complete. Ran 450 experiments.
Summary written to: plots/topology/results/sweep_summary.csv
    Finished `release` profile [optimized] target(s) in 0.02s
     Running `target/release/ctsim sweep_scalability.toml`
Starting sweep of 1800 experiments...
Sweep complete. Ran 1800 experiments.
Summary written to: plots/scalability/results/sweep_summary.csv
$ shasum -a 256 plots/topology/results/sweep_summary.csv plots/scalability/results/sweep_summary.csv
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  plots/topology/results/sweep_summary.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
$ git status --porcelain
```


## NC-D2

Perturbed declared topology-sweep input: removed seed `2` from `sweep_topology.toml`.

````text
$ git diff -- sweep_topology.toml
diff --git a/sweep_topology.toml b/sweep_topology.toml
index d5a6a4d..916dd2d 100644
--- a/sweep_topology.toml
+++ b/sweep_topology.toml
@@ -2,7 +2,7 @@
 # Fixed N and loss; vary graph structure.
 output_dir = "plots/topology/results"

-seeds = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]  # Multiple seeds for error bands
+seeds = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]  # Multiple seeds for error bands
 num_nodes = [27]
 topologies = ["line", "partial_mesh", "random", "scale_free", "full_mesh"]
 loss_rates = [0.05]
$ cargo run --release --bin ctsim -- sweep_topology.toml && cargo run --release --bin ctsim -- sweep_scalability.toml
    Finished `release` profile [optimized] target(s) in 0.24s
     Running `target/release/ctsim sweep_topology.toml`
Starting sweep of 420 experiments...
Sweep complete. Ran 420 experiments.
Summary written to: plots/topology/results/sweep_summary.csv
    Finished `release` profile [optimized] target(s) in 0.06s
     Running `target/release/ctsim sweep_scalability.toml`
Starting sweep of 1800 experiments...
Sweep complete. Ran 1800 experiments.
Summary written to: plots/scalability/results/sweep_summary.csv
$ shasum -a 256 plots/topology/results/sweep_summary.csv plots/scalability/results/sweep_summary.csv
fea33f5db3356e4a71381a9a0265434959bfeb682d6947300786c34a8b9960e7  plots/topology/results/sweep_summary.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
$ grep -E '^(topology|scalability)[[:space:]]' docs/validation/addition13/README.md
topology     1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329
scalability  b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7
$ git checkout -- sweep_topology.toml
$ cargo run --release --bin ctsim -- sweep_topology.toml && cargo run --release --bin ctsim -- sweep_scalability.toml
    Finished `release` profile [optimized] target(s) in 0.14s
     Running `target/release/ctsim sweep_topology.toml`
Starting sweep of 450 experiments...
Sweep complete. Ran 450 experiments.
Summary written to: plots/topology/results/sweep_summary.csv
    Finished `release` profile [optimized] target(s) in 0.06s
     Running `target/release/ctsim sweep_scalability.toml`
Starting sweep of 1800 experiments...
Sweep complete. Ran 1800 experiments.
Summary written to: plots/scalability/results/sweep_summary.csv
$ shasum -a 256 plots/topology/results/sweep_summary.csv plots/scalability/results/sweep_summary.csv
1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329  plots/topology/results/sweep_summary.csv
b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7  plots/scalability/results/sweep_summary.csv
$ grep -E '^(topology|scalability)[[:space:]]' docs/validation/addition13/README.md
topology     1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329
scalability  b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7
$ git status --porcelain
````

## NC-F

Perturbed one byte in `profiles/graphs/random_n27_seed2.txt`: changed the edge line `0 1` to `0 2`.

````text
$ nl -ba tests/validation.rs | sed -n '389,431p'
   389	/// Addition 12: the frozen adjacency files under `profiles/graphs/` must
   390	/// reproduce the random topologies that `build_graph` generates from each seed.
   391	///
   392	/// This guards against DOT-to-adjacency conversion errors (section 4.3 of the
   393	/// addition-12 prompt). The test is fast: it builds 15 in-memory graphs and
   394	/// loads 15 small text files, with no simulation runs.
   395	#[test]
   396	fn frozen_graph_files_reproduce_the_published_random_topologies() {
   397	    use std::path::Path;
   398
   399	    for &seed in &SEEDS {
   400	        let mut rng = ChaCha8Rng::seed_from_u64(seed);
   401	        let expected = NetworkGraph::random_topology(27, 2, 5, &mut rng);
   402
   403	        let graph_path = format!("profiles/graphs/random_n27_seed{seed}.txt");
   404	        let loaded = NetworkGraph::from_file(Path::new(&graph_path))
   405	            .unwrap_or_else(|e| panic!("failed to load {graph_path}: {e}"));
   406
   407	        assert_eq!(
   408	            expected.num_nodes(),
   409	            loaded.num_nodes(),
   410	            "seed {seed}: num_nodes mismatch"
   411	        );
   412	        assert_eq!(
   413	            expected.edge_count(),
   414	            loaded.edge_count(),
   415	            "seed {seed}: edge_count mismatch ({} vs {})",
   416	            expected.edge_count(),
   417	            loaded.edge_count()
   418	        );
   419	        assert_eq!(
   420	            expected.diameter(),
   421	            loaded.diameter(),
   422	            "seed {seed}: diameter mismatch"
   423	        );
   424
   425	        for i in 0..expected.num_nodes() {
   426	            assert_eq!(
   427	                expected.neighbors(i),
   428	                loaded.neighbors(i),
   429	                "seed {seed}: neighbors({i}) differ"
   430	            );
   431	        }
$ git diff -- profiles/graphs/random_n27_seed2.txt
diff --git a/profiles/graphs/random_n27_seed2.txt b/profiles/graphs/random_n27_seed2.txt
index af672f5..8ae8602 100644
--- a/profiles/graphs/random_n27_seed2.txt
+++ b/profiles/graphs/random_n27_seed2.txt
@@ -1,5 +1,5 @@
 27
-0 1
+0 2
 0 3
 0 4
 0 6
$ cargo test --all
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.16s
     Running unittests src/lib.rs (target/debug/deps/ctsim-104f91eef602156c)

running 9 tests
test network::tests::line_diameter_is_n_minus_one ... ok
test node::tests::new_node_starts_listening ... ok
test network::tests::star_diameter_is_two ... ok
test network::tests::grid_3x3_diameter_is_four ... ok
test network::tests::to_dot_contains_edges ... ok
test network::tests::full_mesh_diameter_is_one ... ok
test node::tests::tick_increments_correct_counter ... ok
test network::tests::seeded_partial_mesh_is_deterministic ... ok
test network::tests::scale_free_is_deterministic_for_a_fixed_seed ... ok

test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs (target/debug/deps/ctsim-55866f5fe6d40ec9)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/freeze_dense_graphs.rs (target/debug/deps/freeze_dense_graphs-77b119eb7c8d7e55)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/freeze_graphs.rs (target/debug/deps/freeze_graphs-a18fc06e541dbfbf)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/n_sweep.rs (target/debug/deps/n_sweep-e94f94cc6e2daf6d)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/outcome_classifier_reachability.rs (target/debug/deps/outcome_classifier_reachability-938211f9e42c3238)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/search_density.rs (target/debug/deps/search_density-31e5082369b712a5)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/search_w.rs (target/debug/deps/search_w-cdb2c9a2fbe24f30)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/reproducibility.rs (target/debug/deps/reproducibility-8712ee831ad5cf0d)

running 3 tests
test a_different_seed_changes_the_run_under_loss ... ok
test every_example_makes_progress ... ok
test same_seed_reproduces_every_example_exactly ... ok

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.46s

     Running tests/validation.rs (target/debug/deps/validation-7e50d66c20114816)

running 18 tests
test cv_table_values_in_provenance_match_data ... ok
test harness_templates_contain_all_placeholders ... ok
test frozen_graph_files_reproduce_the_published_random_topologies ... FAILED
test json_carrier_is_an_artefact_not_a_wire_format ... ok
test harness_loss_rates_come_from_the_calibration_lock ... ok
test calibration_lock_pins_the_single_free_parameter ... ok
test blind_prediction_failure_is_recorded_not_repaired ... ok
test published_slot_lengths_match_their_primary_sources ... ok
test pure_flood_reaches_every_receiver_on_a_lossless_line ... ok
test calibration_lock_evidence_blobs_match_their_files ... ok
test specified_wire_packet_fits_in_one_ll_data_pdu ... ok
test round_boundaries_tile_timeline_and_latency_equals_round_length ... ok
test committed_per_proposal_evidence_reproduces_stratified_aggregate ... ok
test per_proposal_latencies_match_aggregate_round_columns ... ok
test high_loss_2pc_exercises_non_committed_outcomes ... ok
test random_builders_are_connected_by_construction_not_by_degree ... ok
test every_published_graph_is_connected ... ok
test snapshot_series_accounts_for_every_ticked_slot ... ok

failures:

---- frozen_graph_files_reproduce_the_published_random_topologies stdout ----

thread 'frozen_graph_files_reproduce_the_published_random_topologies' (7624049) panicked at tests/validation.rs:426:13:
assertion `left == right` failed: seed 2: neighbors(0) differ
  left: [1, 3, 4, 6, 7, 9, 12, 19]
 right: [2, 3, 4, 6, 7, 9, 12, 19]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    frozen_graph_files_reproduce_the_published_random_topologies

test result: FAILED. 17 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.08s

error: test failed, to rerun pass `--test validation`
exit code: 101
$ git checkout -- profiles/graphs/random_n27_seed2.txt
$ cargo test --all
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.12s
     Running unittests src/lib.rs (target/debug/deps/ctsim-104f91eef602156c)

running 9 tests
test node::tests::new_node_starts_listening ... ok
test network::tests::to_dot_contains_edges ... ok
test network::tests::line_diameter_is_n_minus_one ... ok
test network::tests::grid_3x3_diameter_is_four ... ok
test node::tests::tick_increments_correct_counter ... ok
test network::tests::star_diameter_is_two ... ok
test network::tests::full_mesh_diameter_is_one ... ok
test network::tests::seeded_partial_mesh_is_deterministic ... ok
test network::tests::scale_free_is_deterministic_for_a_fixed_seed ... ok

test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs (target/debug/deps/ctsim-55866f5fe6d40ec9)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/freeze_dense_graphs.rs (target/debug/deps/freeze_dense_graphs-77b119eb7c8d7e55)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/freeze_graphs.rs (target/debug/deps/freeze_graphs-a18fc06e541dbfbf)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/n_sweep.rs (target/debug/deps/n_sweep-e94f94cc6e2daf6d)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/outcome_classifier_reachability.rs (target/debug/deps/outcome_classifier_reachability-938211f9e42c3238)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/search_density.rs (target/debug/deps/search_density-31e5082369b712a5)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/bin/search_w.rs (target/debug/deps/search_w-cdb2c9a2fbe24f30)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/reproducibility.rs (target/debug/deps/reproducibility-8712ee831ad5cf0d)

running 3 tests
test a_different_seed_changes_the_run_under_loss ... ok
test every_example_makes_progress ... ok
test same_seed_reproduces_every_example_exactly ... ok

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.46s

     Running tests/validation.rs (target/debug/deps/validation-7e50d66c20114816)

running 18 tests
test cv_table_values_in_provenance_match_data ... ok
test harness_templates_contain_all_placeholders ... ok
test blind_prediction_failure_is_recorded_not_repaired ... ok
test calibration_lock_pins_the_single_free_parameter ... ok
test json_carrier_is_an_artefact_not_a_wire_format ... ok
test harness_loss_rates_come_from_the_calibration_lock ... ok
test published_slot_lengths_match_their_primary_sources ... ok
test calibration_lock_evidence_blobs_match_their_files ... ok
test pure_flood_reaches_every_receiver_on_a_lossless_line ... ok
test round_boundaries_tile_timeline_and_latency_equals_round_length ... ok
test specified_wire_packet_fits_in_one_ll_data_pdu ... ok
test committed_per_proposal_evidence_reproduces_stratified_aggregate ... ok
test frozen_graph_files_reproduce_the_published_random_topologies ... ok
test per_proposal_latencies_match_aggregate_round_columns ... ok
test high_loss_2pc_exercises_non_committed_outcomes ... ok
test random_builders_are_connected_by_construction_not_by_degree ... ok
test every_published_graph_is_connected ... ok
test snapshot_series_accounts_for_every_ticked_slot ... ok

test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.07s

   Doc-tests ctsim

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

$ git status --porcelain
````
