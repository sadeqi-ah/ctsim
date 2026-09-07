# Addition 12 — Graph/Channel Decoupling

## 1. Starting point

```
git fetch origin && git rev-parse origin/main
04ea58970606157e8faf672d36fad9a85be5068a

git checkout -b validation/graph-channel-decoupling origin/main
```

Binary built with `cargo build --release` from that commit.

## 2. Graph provenance (15 frozen topologies)

Each seed was run with `protocol = "pure_flood"`, `num_proposals = 1`,
`loss_rate = 0.0`, `topology = "random"`, `num_nodes = 27`. The DOT file
was captured immediately after each run and converted to a sorted adjacency
file under `profiles/graphs/`.

| seed | edges | diameter | mean\_degree |
|-----:|------:|---------:|-------------:|
|    2 |    62 |        4 |     4.592593 |
|    3 |    59 |        5 |     4.370370 |
|    5 |    65 |        4 |     4.814815 |
|    7 |    62 |        4 |     4.592593 |
|   11 |    61 |        4 |     4.518519 |
|   13 |    60 |        4 |     4.444444 |
|   17 |    54 |        4 |     4.000000 |
|   19 |    57 |        4 |     4.222222 |
|   23 |    60 |        5 |     4.444444 |
|   29 |    62 |        4 |     4.592593 |
|   31 |    57 |        4 |     4.222222 |
|   37 |    52 |        4 |     3.851852 |
|   41 |    58 |        5 |     4.296296 |
|   43 |    57 |        4 |     4.222222 |
|   47 |    64 |        4 |     4.740741 |

SHA-256 hashes of each graph file are recorded in
`data/graph_provenance.csv`.

## 3. Round-trip gate

All 15 frozen graph files were re-loaded via `graph_file` and the printed
`(n, edges, diameter)` triple was compared against the original run. All 15
match exactly.

## 4. Variance decomposition

Two-way decomposition (no interaction term) of flood coverage `y[g][c]` on
the 15 × 15 graph × channel grid, G = C = 15.

| loss | grand\_mean | SS\_graph | SS\_channel | SS\_resid | MS\_graph | MS\_channel | MS\_resid | MS\_g/MS\_c |
|-----:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|
| 0.05 | 0.999292 | 0.00003496 | 0.00003805 | 0.00035375 | 0.00000250 | 0.00000272 | 0.00000180 | 0.92 |
| 0.06 | 0.999000 | 0.00011579 | 0.00006444 | 0.00039841 | 0.00000827 | 0.00000460 | 0.00000203 | 1.80 |
| 0.07 | 0.998655 | 0.00013191 | 0.00007739 | 0.00069896 | 0.00000942 | 0.00000553 | 0.00000357 | 1.70 |
| 0.08 | 0.998252 | 0.00027549 | 0.00008565 | 0.00101951 | 0.00001968 | 0.00000612 | 0.00000520 | 3.22 |
| 0.09 | 0.997697 | 0.00037641 | 0.00010450 | 0.00093269 | 0.00002689 | 0.00000746 | 0.00000476 | 3.60 |
| 0.10 | 0.997353 | 0.00038390 | 0.00008306 | 0.00093678 | 0.00002742 | 0.00000593 | 0.00000478 | 4.62 |

## 5. p\* determination

Graph-level t-interval: collapse channel variance first (take per-graph
means `ybar_g`), then compute a t-interval across the 15 graph means with
`t(0.975, 14) = 2.1447866879169273`.

p\* = the largest `loss_rate` whose lower confidence bound is ≥ 0.999.

| loss | mean(ȳ\_g) | sd(ȳ\_g) | half\_width | ci\_lower | ≥ 0.999? |
|-----:|-----------:|---------:|----------:|----------:|:--------:|
| 0.05 |   0.999292 | 0.000408 |  0.000226 |  0.999066 |   YES    |
| 0.06 |   0.999000 | 0.000743 |  0.000411 |  0.998589 |    no    |
| 0.07 |   0.998655 | 0.000793 |  0.000439 |  0.998216 |    no    |
| 0.08 |   0.998252 | 0.001145 |  0.000634 |  0.997618 |    no    |
| 0.09 |   0.997697 | 0.001339 |  0.000741 |  0.996955 |    no    |
| 0.10 |   0.997353 | 0.001352 |  0.000749 |  0.996604 |    no    |

**p\* = 0.05.**

## 6. Fine loss sweep (old methodology)

60 runs at loss_rate ∈ {0.06, 0.07, 0.08, 0.09}, 15 seeds, old methodology
(seed = graph + channel, no `graph_file`). Directly comparable to the
merged `coverage_curve.csv`.

| loss | fine\_mean | fine\_sd | fine\_ci\_hw | grid\_mean | grid\_sd | grid\_ci\_hw |
|-----:|----------:|---------:|-----------:|-----------:|---------:|-----------:|
| 0.06 |  0.999551 | 0.000403 |   0.000223 |   0.999000 | 0.000743 |   0.000411 |
| 0.07 |  0.998462 | 0.002023 |   0.001121 |   0.998655 | 0.000793 |   0.000439 |
| 0.08 |  0.998423 | 0.002013 |   0.001115 |   0.998252 | 0.001145 |   0.000634 |
| 0.09 |  0.997359 | 0.002889 |   0.001600 |   0.997697 | 0.001339 |   0.000741 |

Row-by-row comparison between the fine sweep and the grid is NOT
meaningful: with `graph_file` set, no RNG is consumed by graph
construction, so the ChaCha8 stream starts from a different point and the
per-(seed, loss) numbers are not expected to match. This is by design, not
a bug.

## 7. What the grid shows

Graph variance exceeds channel variance at every loss level above 0.05.
The ratio MS\_graph / MS\_channel grows from 0.92 at loss = 0.05 to 4.62 at
loss = 0.10. The range of per-graph means (min to max ȳ\_g) is 0.001192 at
loss = 0.05 and widens to 0.004397 at loss = 0.10, while the range of
per-channel means stays between 0.001526 and 0.003115. At loss = 0.10, the
graph range is 2.07× the channel range. This confirms the defect identified
in section 2 of the prompt: the merged curve's ± half-widths pool graph
and channel variance, and the graph component dominates.

## 8. Judgement calls

1. **Template shape.** The prompt's temporary config for Task A omits
   `abort_probability`, which is present in the committed template
   (`profiles/pure_flood_n27_template.toml`) only as a default (`0.0` via
   `default_abort_prob()` in `config.rs`). Since `SimConfig` deserialization
   defaults it to 0.0 when absent, omitting it is valid TOML. No field was
   added or changed.

2. **Edge deduplication.** The DOT file lists each edge once (`u -- v`),
   so no duplicates arise. The conversion script collects edges as
   `(min(u,v), max(u,v))` and deduplicates via `set` as a safety measure,
   but no actual duplicates were removed.

3. **Grid script progress output.** The grid runs 1350 iterations; printing
   every iteration produces excessive terminal output. The script prints
   progress every 50 runs instead of every run.

4. **`graph_file` path format.** The adjacency files are committed at
   `profiles/graphs/random_n27_seed{S}.txt` and the grid script references
   them by relative path. This works because the script `cd`s to
   `$REPO_ROOT` before running, and `src/main.rs` resolves `graph_file`
   relative to the working directory.

5. **No `src/` changes.** The entire mechanism (graph_file short-circuit +
   seed-only channel variation) was already in the code. Zero lines of
   `src/` were modified.
