# Step 1 — Inventory of the simulator

Read-only survey of `ctsim` at `HEAD = 6d2be8cecfe27ae1f10e3952a3c74b2ee2b68b4c`.
No simulator code was modified and no simulation was run. Every claim below cites
`file:line`. Where a quantity the validation plan asks for does not exist in the
code, it is marked **absent** rather than approximated.

---

## a. Configuration parsing, parameters, units

Parsing: `SimConfig::from_file` (`src/config.rs:82`) reads the file, `toml::from_str`
deserialises it into `SimConfig`, then `validate()` (`src/config.rs:89`) runs. There is
no layering, no env override, no defaults file — one TOML, one run.

Validation rules (`src/config.rs:89-109`): `network.num_nodes >= 2`;
`network.loss_rate ∈ [0.0, 1.0)` (1.0 rejected); `phy_mode` must be `"ci"` or `"ce"`,
and the matching `[ci]` / `[ce]` section must be present.

| Parameter | Type / default | Unit | Effect |
|---|---|---|---|
| `seed` | u64, required | — | Seeds `ChaCha8Rng` for graph, PHY and protocol randomness |
| `phy_mode` | `"ci"` \| `"ce"` | — | Selects the PHY engine and the orchestrator |
| `protocol` | string, required | — | One of `paxos_pipeline`, `2pc_pipeline`, `tom_pipeline`, `paxos_ce`, `2pc_ce`, `tom_ce` (`src/run.rs:160-208`) |
| `num_proposals` | usize, 100 (`config.rs:70`) | count | Decisions attempted per run |
| `snapshot_interval` | u64, 50 (`config.rs:73`) | **slots** | Sampling period of `snapshots_*.csv` |
| `max_slots` | u64, 100 000 (`config.rs:76`) | **slots** | Global cutoff; remaining proposals recorded `TimedOut` (`src/sim.rs:76-86`) |
| `abort_probability` | f64, 0.0 (`config.rs:66`) | probability | Application-level NO vote in 2PC (`src/sim/two_pc_pipeline.rs:99`, `:206`) |
| `quiet` | bool, false | — | Silences stdout; used by the sweep |
| `network.num_nodes` | usize | count | N |
| `network.topology` | string | — | Dispatched in `src/run.rs:55-69` |
| `network.loss_rate` | f64, 0.0 | probability **per reception attempt** | See §c |
| `network.graph_file` | optional path | — | Overrides `topology` (`src/run.rs:51`) |
| `ci.flood_repeats` | u32 | **slots of TX per flood participation** | This is the paper's `N_retx`; also scales the auto round length |
| `ci.round_slots` | Option\<u64\> | **slots** | Round length. `None` ⇒ `max(3, (diameter + 2) · flood_repeats)` (`src/phy/ci.rs:41-46`) |
| `ce.listen_timeout` | u64 | **slots** | No-progress slots before a random re-flood (`src/phy/ce.rs:83`) |
| `ce.max_round_slots` | u64 | **slots** | Per-round deadline (`src/phy/ce.rs:34`) |

Sweep configs are a separate, flatter schema (`src/sweep_config.rs`) expanded into the
cartesian product of its list fields (`src/sweep_runner.rs:29-70`). Note that the sweep
path always sets `round_slots: None` (`src/run.rs:249`), so every sweep row uses the
auto round length.

**Unit finding, material to Steps 2–3 and 6b.** Every timing quantity in the
simulator is an abstract integer slot (`pub type Slot = u64`, `src/event.rs`). A grep
over `src/`, `tests/`, `examples/`, `docs/` and the root TOMLs for
`t_slot|slot_us|slot_ms|microsecond|millisecond|airtime|turnaround|guard|drift|bluetooth|2M PHY`
returns no configuration parameter, no constant and no output field. There is no
slot→seconds conversion anywhere in the repository. Slots are not calibrated to
physical time, and no metric is expressed in seconds.

## b. Topology generation, diameter, average degree

Construction: `build_graph` (`src/run.rs:50-70`) — `graph_file` if present, else a
builder chosen by name. Builders in `src/network.rs`: `full_mesh` (`:148`), `line`,
`star`, `grid` (side = ⌈√N⌉, `src/run.rs:60`), `ring`, `tree` (branching factor 3),
`scale_free` (Barabási–Albert, m = 2), `random_topology(n, 2, 5)` (degree bounds 2–5),
`partial_mesh(n, 0.3)` (spanning tree plus edge probability 0.3). Randomised builders
draw from an RNG seeded with `config.seed` (`src/run.rs:154`); the graph is rebuilt from
a fresh RNG on the same seed to fill the summary (`src/run.rs:212-214`), so reported
diameter/edges describe the graph actually simulated.

The graph is an undirected adjacency list of `HashSet`s. `neighbors()`
(`src/network.rs:20-24`) returns a **sorted** `Vec`, which is what keeps loss draws
reproducible across processes.

`diameter()` (`src/network.rs:27-52`): BFS from every node, maximum finite
eccentricity. Unreachable pairs are filtered out (`x != usize::MAX`), so a
disconnected graph reports the largest *component* diameter rather than infinity — no
connectivity check is performed.

`edge_count()` (`src/network.rs:55-57`): `Σ|adj[i]| / 2`.

**Average degree is absent.** Neither the simulator nor any plot script computes it;
`sweep_summary.csv` carries `diameter` and `edges` only. Any average-degree figure is
a derived quantity, `2·edges/N`, computed outside the simulator.

## c. Loss model

Loss is applied **per reception attempt**: one Bernoulli draw per
(transmitter, listening receiver) ordered pair, per slot. It is not per link (no
per-link state is stored), not per frame, and not cached across slots.

CI (`src/phy/ci.rs:74-86`): for each node in `Flood`, for each neighbour in `Listen`,
reception succeeds iff `loss_rate == 0.0 || rng.gen::<f64>() >= loss_rate`. Several
concurrent flooders each get their own draw at the same receiver.

CE (`src/phy/ce.rs:104-141`): the flooding neighbours of a `Listen` target are
collected, sorted, then Fisher–Yates shuffled (`:115-118`) to model random capture. The
list is walked in that order; each candidate is dropped with probability `loss_rate`
(`:121`), and the first surviving candidate is merged and ends the target's slot
(`break`, `:140`). So at most one successful reception per receiver per slot.

Independence: draws are memoryless and redrawn every slot. **No bursty or correlated
loss model exists** — a grep for `gilbert|burst|markov|correlat` over `src/` returns
nothing.

Symmetry: the graph is undirected and one scalar `loss_rate` governs both directions,
so loss is symmetric *in distribution*; per realisation each direction draws
independently, and there is no parameter for per-link or asymmetric loss.

One RNG detail worth recording: both engines short-circuit at exactly zero loss
(`loss_rate == 0.0 ||` in CI, `loss_rate > 0.0 &&` in CE), so a `loss_rate = 0` run
consumes no loss draws and its RNG stream is structurally different from any
`loss_rate > 0` run.

## d. The slot loop

A slot is one indivisible transmit opportunity for every radio in the network. It has
no physical duration (§a). Both engines obey the same three-phase rule
(`src/phy/ci.rs:60-122`, `src/phy/ce.rs:44-162`): (1) `tick()` every node and take any
due snapshot **from the state held at slot start**; (2) act — transmit from `Flood`,
receive into `Listen`; (3) compute next-slot states and apply them at slot end. A
node's radio state never changes mid-slot.

Energy cost of a slot: `Node::tick()` (`src/node.rs:68-74`) increments exactly one of
`slots_listen`, `slots_flood`, `slots_sleep` for each node. So one node-slot is charged
to exactly one bucket, and radio-on time is `listen + flood`.

Radios on during a slot:

- **CI.** The initiator starts in `Flood` with `flood_remaining = flood_repeats`;
  all others start in `Listen` (`src/phy/ci.rs:50-57`). A receiver flips to `Flood` for
  `flood_repeats` slots (`:102-105`), then to `Sleep` for the rest of the round
  (`:97-101`). CI nodes therefore genuinely sleep. The round also ends as soon as no
  node will flood next slot (`:91`, `:108-121`), so there is no all-`Sleep` padding to
  the nominal round length.
- **CE.** `next_states` is re-initialised to `Listen` for every node every slot
  (`src/phy/ce.rs:65-70`); the only escape is `protocol.node_can_sleep`, whose base
  implementation returns `false` (`src/protocol/mod.rs:56`) and which only `2pc_ce`
  overrides (`src/protocol/two_pc_ce.rs:239-244`). Empirically the `sleep` column is
  **0 in all 1 125 CE rows** of the two on-disk sweeps, i.e. all N radios are on in
  every CE slot. That is the structural origin of `E = N · L`: over the same rows,
  `max |listen + flood + sleep − N · end_slot| = 0` exactly.

The CE round returns `slot + 1` on goal (`src/phy/ce.rs:56-62`); the comment records
that returning `slot` would re-tick one absolute slot per proposal and inflate energy
by `N · num_proposals`.

## e. How each reported metric is computed

**Decision latency** — `MetricsCollector::record_proposal` (`src/metrics.rs:73-81`)
stores `latency = end.saturating_sub(start)`, in slots, per proposal. Run-level
`avg_latency_committed` averages committed proposals only (`src/run.rs:95-105`). The
*start* slot is protocol-specific: CE uses the proposal's round start
(`src/sim.rs:89`, `:116`); Paxos CI records the slot the proposal was first floated
(`src/sim/paxos_pipeline.rs:108`); TOM CI likewise (`src/sim/tom_pipeline.rs:204`);
2PC CI computes `start_round · round_len` where
`round_len = config.ci.round_slots.unwrap_or(0)` (`src/sim/two_pc_pipeline.rs:140-146`).
Because the sweep path sets `round_slots = None` (`src/run.rs:249`), `round_len = 0` and
**every 2PC-CI start slot is 0** — confirmed in `results/results_2pc.csv`, where all 100
rows carry `start_slot = 0`, against `0, 4, 8, 12, …` for Paxos and TOM. 2PC-CI latency
is therefore measured from time zero, not from proposal creation. See conflict 9.

**Throughput** — not a simulator output. Defined identically in two plot scripts as
`committed / end_slot` (`plots/topology/plot_topology.py:94`,
`plots/scalability/plot_summary_commit.py:63`), unit decisions per slot, where
`end_slot` is the maximum proposal end slot of the run (`src/run.rs:117-122`).

**Commit rate** — `committed / proposals · 100` in the plot scripts
(`plot_topology.py:97`); the underlying counts come from
`ProposalOutcome` tallies (`src/run.rs:80-94`).

**Radio-on energy per decision** — cumulative variant: `listen + flood`, in node-slots,
exported per run. Per-decision variant: `(listen + flood) / committed`
(`plot_topology.py:95`, `plot_summary_commit.py:64`). Both plot scripts guard the
division with `.replace(0, 1)`, which silently substitutes a denominator of 1 when
nothing committed.

**Amortised energy per decision** — only in `plots/energy/plot_paper_energy.py:100-130`:
for each committed proposal, `E_i = Σ_{t ∈ [start, end)} A_t / C_t`, where
`A_t = nodes_listening + nodes_flooding` at snapshot slot `t` and `C_t` is the number of
live proposals covering `t`. It requires `snapshot_interval = 1` to be exact.

**Pipeline depth** — **absent.** A grep for `depth` and for Little's law over `src/`,
`plots/`, `tools/` and `docs/` finds no implementation. It exists only as a paper-side
derived quantity, throughput × latency.

**Duty cycle** — **absent as a scalar.** `plots/duty_cycle/plot_kde_awake.py:90` builds
the discrete PMF of `nodes_listening + nodes_flooding` per snapshot slot and never
divides by N. From the existing columns, `(listen + flood) / (listen + flood + sleep)`
gives 0.58–0.92 for CI rows and exactly 1.00 for CE rows.

**Packet delivery ratio** — **absent.** No packet is ever counted as sent versus
delivered anywhere in `src/`; the only delivery-like observable is the protocol-level
outcome per proposal (`Committed` / `Aborted` / `TimedOut`).

## f. Seeds and independent runs

One configuration plus one seed is one run. Two independent streams are derived from
the same `config.seed` value: the graph RNG (`src/run.rs:154`, rebuilt at `:212`) and
the simulator's own `ChaCha8Rng` (`src/sim.rs:35` for CE, `src/sim/pipeline.rs:37` for
CI). `2pc_ce` seeds a third stream for its abort draws (`src/run.rs:186-189`).

A sweep emits one run per cell of
`seeds × num_nodes × topologies × loss_rates × flood_repeats × (ci_protocols ∪ ce_protocols)`
(`src/sweep_runner.rs:29-70`), executed in parallel with rayon
(`src/sweep_runner.rs:85-98`); cells are self-contained, so the parallel order does not
affect results. Both baseline sweeps declare the same 15 seeds —
`[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]`
(`sweep_topology.toml:5`, `sweep_scalability.toml:4`) — so a configuration yields **15
independent runs** of 100 proposals each.

Initiator rotation is round-robin and deterministic: `round_num % N` for CI
(`src/sim/pipeline.rs:62`), `proposal_id % N` for CE (`src/sim.rs:88`).

`tests/reproducibility.rs` asserts that a fixed seed reproduces each of the six
examples exactly, and that a different seed changes the run under loss.

## g. Result files and formats

| Path | Writer | Format |
|---|---|---|
| `<output_dir>/sweep_summary.csv` | `src/sweep_runner.rs:14-19`, `:111-139` | one row per run; 21 columns: `seed,nodes,topology,loss_rate,flood_repeats,protocol,phy,diameter,edges,proposals,committed,aborted,timed_out,avg_latency,listen,flood,sleep,nacks,piggybacks,ce_timeouts,end_slot` (`avg_latency` formatted to 2 dp) |
| `results/results_<run>.csv` | `src/metrics.rs:127-145` | `proposal_id,start_slot,end_slot,latency,outcome` |
| `results/snapshots_<run>.csv` | `src/metrics.rs:146-160` | `slot,progress_count,nodes_listening,nodes_flooding,nodes_sleeping` |
| `results/topology.dot`, `.svg` | `src/network.rs:132-143` | graph rendering, one pair per run |

`output_dir` comes from the sweep TOML: `plots/scalability/results` and
`plots/topology/results`. The plot scripts additionally derive
`plots/scalability/table_summary_N27_loss05.{csv,tex}`,
`plots/topology/table_topology_N27_loss05.{csv,tex}` and
`plots/energy/{energy_per_proposal.csv,energy_summary.csv}`. All result directories are
gitignored, so the CSVs are the single source of truth and cannot be recovered from
git.

`progress_count` in the snapshots is the network-unified decision count — minimum local
log length across nodes on CI, post-outcome count on CE — collapsed with `max` over
nodes at snapshot time (`src/metrics.rs:49-70`). It is not a sum over nodes.

## Conflicts with the validation plan (Rule 7 — awaiting your decision)

Rule 7 says to stop and ask rather than resolve a conflict between the instructions
and the code. Nine conflicts. The first three block Steps 2–3 outright; the rest change
what later steps can honestly measure.

1. **No `T_slot` exists to calibrate.** Step 2 asks for `T_slot` derived from the
   Bluetooth 5 2M PHY. The simulator has no time unit beyond the abstract integer slot
   and no code path that consumes a duration (§a). Calibrating `T_slot` requires adding
   a parameter, and Step 6b (`T_slot` at ±50 %) requires that parameter to change a
   measured output — but no output depends on it, so ±50 % moves nothing. As the code
   stands, `T_slot` is a paper-side unit conversion applied to slot counts, not a
   simulator input.

2. **Neither BlueFlood target is a simulator output.** PDR is never computed — nothing
   counts packets sent against packets delivered (§e). Duty cycle exists only as a
   per-slot awake-node distribution; the scalar form must be derived as
   `(listen + flood) / (listen + flood + sleep)`. Also relevant to the ~0.4 % target:
   CE keeps every radio on in every slot, so CE duty cycle is exactly 100 %, and the
   CI rows on disk sit at 58–92 %. Neither PHY can express a sub-1 % duty cycle,
   because the model has no notion of idle time between rounds.

3. **"Pure flooding workload" has no entry point.** Every runnable protocol is one of
   the six consensus/multicast combinations (`src/run.rs:160-208`). Flooding is a PHY
   primitive (`flood_identical_round`) reachable only through a `CiProtocol`
   implementation. Measuring flooding alone needs either new code or a decision to use
   one existing protocol as a proxy.

4. **The Gilbert–Elliott arm of Step 6c does not exist.** Loss is i.i.d. per reception
   attempt with no per-link or Markov state (§c). A bursty arm is new simulation logic.

5. **Pipeline depth is not implemented.** Step 6's conclusion 1 and the Layer 1 claim
   ("CE pipeline depth exactly 1.00") rest on a quantity present nowhere in the code
   (§e). I can compute throughput × latency from the CSVs, which is the definition
   Step 6 gives, but note it is derived post hoc and not what the simulator measured.

6. **Steps 3 and 5 require running simulations.** The role statement says the task is a
   validation study and not a feature change, and asks me not to modify simulation
   logic unless a step authorises it. Steps 2, 3 and 5 need new profiles, new runs and
   a new `tests/validation.rs`. Steps 2–5 as written cannot be satisfied without
   writing code and executing runs — please confirm that is intended, since it is the
   opposite of the read-only framing.

7. **`N_retx` is named `flood_repeats`** (`src/config.rs:53`), and it is not purely a
   repetition count: with `round_slots = None` it also scales round length,
   `max(3, (diameter + 2) · flood_repeats)` (`src/phy/ci.rs:41-46`). Sweeping it varies
   two things at once. Say whether Step 6a should hold round length fixed by pinning
   `round_slots`, or accept the coupled sweep.

8. **A2 (N = 180) and Wireless Paxos (N = 188) topologies are not in the repo.** The
   existing sweeps use `random` with degree bounds 2–5. Their testbed graphs would have
   to come from the source papers, and Step 3 explicitly forbids inventing values
   silently.

9. **2PC-CI latency is measured from slot 0 in every sweep row.** `round_len` resolves
   to 0 on the sweep path, so `start_slot = 0` for all 100 proposals
   (`src/sim/two_pc_pipeline.rs:140-146`, `src/run.rs:249`; verified in
   `results/results_2pc.csv`). This is a code-level bug, not a reporting choice: it
   inflates 2PC-CI latency and therefore also any pipeline depth derived from it. The
   published 357.7-slot 2PC-CI latency is affected. I have changed nothing. Fixing it
   is a simulation-logic change and needs your authorisation; leaving it means Step 1b
   will reproduce a number that is internally consistent but measured from the wrong
   origin.

One further note, not a conflict but material to Step 1b: `src/run.rs:108` branches on
`metrics.total_listen > 0`, and those fields are never assigned anywhere in the
codebase. The branch is dead; the node-counter sums are always used. Harmless today,
but it is a trap for anyone who later populates those fields.

## Commands run for this step

Read-only. `git rev-parse HEAD` → `6d2be8cecfe27ae1f10e3952a3c74b2ee2b68b4c`;
`git status --porcelain` → `?? docs/validation/`, `?? report.md` (both untracked
outputs; no tracked file modified). Source files read: `src/{config,event,node,network,metrics,run,sim,sweep_config,sweep_runner,main}.rs`,
`src/phy/{ci,ce}.rs`, `src/sim/{pipeline,paxos_pipeline,two_pc_pipeline,tom_pipeline}.rs`,
`src/protocol/{mod,paxos,two_pc_ce}.rs`, `tests/reproducibility.rs`,
`sweep_{topology,scalability}.toml`, `examples/paxos_{ci,ce}.toml`, `docs/simulator.md`,
and the plot scripts named above. Aggregate checks over
`plots/{topology,scalability}/results/sweep_summary.csv` used the project venv
(`./venv/bin/python`, pandas): the CE `sleep`-column and `E = N·L` checks in §d, the
duty-cycle ranges in §e and conflict 2, and the `start_slot` check in §e and conflict 9
(`results/results_{2pc,paxos,tom}.csv`). No simulation was run and no simulator source
was modified.

