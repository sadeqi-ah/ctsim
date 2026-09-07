# Addition 13 — Blind Predictions against Published Testbed Latencies

## 1. Starting point

```
git fetch origin && git rev-parse origin/main
06fac5bf7cc2f66a635e675e651402905fdb1ab5
```

## 2. Design declarations (fixed before any run)

### Systems

| System | Protocol | N | Published target |
|--------|----------|--:|----------------:|
| A2 (SenSys'17) | 2pc\_ce | 180 | 475 ms |
| Wireless Paxos (EWSN'19) | paxos\_ce | 188 | 289 ms |

### Profile parameters (declared in advance)

- `listen_timeout = 5`: the published value, deliberately NOT scaled with
  diameter. Scaling it after seeing a bad latency would be fitting.
- `max_round_slots = 4000`: replaces the n=27 value of 300, scaled by node
  count with headroom (180/27 ≈ 6.7). Hard cap before a CE round is
  declared failed.
- `abort_probability = 0.0` (A2 only): the published figure is a commit
  latency.
- `snapshot_interval = 1000000`: unused, avoids enormous CSVs.
- `max_slots = 5000000`: generous ceiling.

### Estimator

Per cell: point estimate = mean of 15 per-graph mean latencies.
95% CI = mean ± t(0.975,14) × sd/√15, where t(0.975,14) = 2.1447866879169273.

### Acceptance test (pre-registered)

Primary comparison at T\_guard = 10 µs: relative error within 20%.
Slot-equivalent intervals: [828, 1205] for 475 ms at N=180, [500, 726] for 289 ms at N=188.

### T\_slot conversion

```
T_slot = T_air + T_IFS + 2*T_guard
T_air  = 44.0 + 4.0 * L  (microseconds)
L      = ceil(N/8) + 22   (octets)
T_IFS  = 150 us

N=180: L=45, T_air=224 us, T_slot in [394, 574] us (T_guard 10..100)
N=188: L=46, T_air=228 us, T_slot in [398, 578] us (T_guard 10..100)
```

## 3. Graph provenance (90 frozen topologies)

Six (n, arm) groups with 15 seeds each.

| n | arm | mean(mean\_degree) | mean(diameter) |
|--:|:----|-------------------:|---------------:|
| 180 | base | 4.568889 | 6.60 |
| 180 | deg\_minus1 | 3.547407 | 8.87 |
| 180 | deg\_plus1 | 5.688148 | 5.27 |
| 188 | base | 4.552482 | 6.53 |
| 188 | deg\_minus1 | 3.570213 | 8.67 |
| 188 | deg\_plus1 | 5.714184 | 5.33 |

All 90 graphs: round-trip gate passed, BFS connectivity verified.
Full data in `data/graph_provenance_large.csv`.

## 4. Run matrix (120 runs)

All 120 runs completed with 100 recorded proposals each.
Zero timed\_out events. Zero latency cross-check warnings.

## 5. Estimator results (slots)

| system | arm | loss | mean | sd | SE | CI\_lo | CI\_hi |
|-------:|----:|-----:|-----:|---:|---:|------:|------:|
| a2\_sensys17 | base | 0.05 | 42.441 | 0.893 | 0.231 | 41.946 | 42.935 |
| a2\_sensys17 | base | 0.06 | 42.411 | 0.851 | 0.220 | 41.940 | 42.883 |
| a2\_sensys17 | deg\_minus1 | 0.05 | 55.003 | 3.851 | 0.994 | 52.871 | 57.136 |
| a2\_sensys17 | deg\_plus1 | 0.05 | 39.157 | 0.436 | 0.113 | 38.915 | 39.398 |
| wpaxos\_ewsn19 | base | 0.05 | 24.614 | 0.280 | 0.072 | 24.459 | 24.769 |
| wpaxos\_ewsn19 | base | 0.06 | 24.677 | 0.250 | 0.065 | 24.538 | 24.815 |
| wpaxos\_ewsn19 | deg\_minus1 | 0.05 | 29.601 | 1.325 | 0.342 | 28.867 | 30.334 |
| wpaxos\_ewsn19 | deg\_plus1 | 0.05 | 22.650 | 0.134 | 0.034 | 22.576 | 22.724 |

## 6. Millisecond conversion and acceptance test

### A2 (SenSys'17), N=180, target=475 ms

Mean latency = 42.441 slots [41.946, 42.935].
Slot-equivalent interval [828, 1205]: mean (42.4) is **outside** — far below.

| T\_guard (µs) | T\_slot (µs) | pred (ms) | CI\_lo (ms) | CI\_hi (ms) | target (ms) | rel err | \|err\|<20% |
|-:|--:|--:|--:|--:|--:|--:|:-:|
| 10 | 394.0 | 16.722 | 16.527 | 16.917 | 475.0 | −0.9648 | NO |
| 20 | 414.0 | 17.570 | 17.366 | 17.775 | 475.0 | −0.9630 | NO |
| 50 | 474.0 | 20.117 | 19.882 | 20.351 | 475.0 | −0.9576 | NO |
| 100 | 574.0 | 24.361 | 24.077 | 24.645 | 475.0 | −0.9487 | NO |

### Wireless Paxos (EWSN'19), N=188, target=289 ms

Mean latency = 24.614 slots [24.459, 24.769].
Slot-equivalent interval [500, 726]: mean (24.6) is **outside** — far below.

| T\_guard (µs) | T\_slot (µs) | pred (ms) | CI\_lo (ms) | CI\_hi (ms) | target (ms) | rel err | \|err\|<20% |
|-:|--:|--:|--:|--:|--:|--:|:-:|
| 10 | 398.0 | 9.796 | 9.735 | 9.858 | 289.0 | −0.9661 | NO |
| 20 | 418.0 | 10.289 | 10.224 | 10.354 | 289.0 | −0.9644 | NO |
| 50 | 478.0 | 11.765 | 11.691 | 11.840 | 289.0 | −0.9593 | NO |
| 100 | 578.0 | 14.227 | 14.137 | 14.317 | 289.0 | −0.9508 | NO |

### Verdict

**Both predictions fail the acceptance test at every T\_guard value.**
The simulator predicts latencies that are approximately 20–30× lower than
the published testbed measurements. The deficit is so large that no
admissible T\_guard value can close the gap.

The acceptance test was pre-registered as T\_guard=10 µs, relative error
within 20%. Neither system is close: relative errors are −96.5% and −96.6%.

## 7. Robustness to degree

The deg\_minus1 arm (sparser, larger diameter) increases A2 latency to 55.0
slots (+30%) and WPaxos to 29.6 slots (+20%). The deg\_plus1 arm (denser,
smaller diameter) decreases them to 39.2 and 22.7 slots. The direction is
correct — sparser graphs have longer latencies — but the magnitude is small
compared to the 20× gap with the published targets.

## 8. Regression gate

```
topology     1e596a3f480539972e21aa6a8f1186fc9f60f4bca6d08e125108c51a1dea0329
scalability  b982afa37606312737811bd985fcabf7d841d5bd3f6f782f5a424d8e8c3758e7
```

Both byte-identical. `.gitignore` covers `/results`.

## 9. Judgement calls

1. **`cargo run` with multiple binaries.** Adding `src/bin/freeze_graphs.rs`
   creates a second binary. `cargo run --release -- sweep_topology.toml` now
   requires `--bin ctsim`. The CLI binary `target/release/ctsim` is
   unambiguous and the harness script uses it directly.

2. **seed = graph_seed for channel.** As directed: one channel realisation
   per graph. The step-2.4 variance decomposition showed channel variance
   not significant.

3. **No parameters changed after seeing results.** listen\_timeout,
   max\_round\_slots, abort\_probability and the acceptance band are all
   exactly as declared before any run.
