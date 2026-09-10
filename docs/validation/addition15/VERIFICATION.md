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
