# Addition 14 stratified-run provenance

- Git HEAD: `bb1bb2d9bb926e3d7581010e7f36f4ce72183f6c`
- `git status --porcelain` before commit:

```text
?? docs/validation/addition14/data/run_provenance.md
?? docs/validation/addition14/data/stratified_predictions.csv
?? docs/validation/addition14/scripts/stratified_predictions.sh
```

- Calibration lock blob: `fd88f784e18062c075f0b9c8a940918c87b2d0cf`
- Binary build command: `cargo build --release --bin ctsim`
- Sweep command: `/usr/bin/time -p docs/validation/addition14/scripts/stratified_predictions.sh`
- Dense block wall clock: `756.57 s`
- Sparse base block wall clock: `266.19 s`
- Dense channel-control block wall clock: `253.09 s`
- Whole round wall clock: `1276.05 s`

## Graph input blobs

- `profiles/graphs/random_n180_dense_seed2.txt`: `9dc0b5d27ad0f23a2aab669cc07f1c3914c86359`
- `profiles/graphs/random_n180_dense_seed3.txt`: `5b2b75b40eecbe8dfa6407a695bd791f708d38f6`
- `profiles/graphs/random_n180_dense_seed5.txt`: `6eff63e176396460c667a6acb382829812014dd4`
- `profiles/graphs/random_n180_dense_seed7.txt`: `7ecc07243aa2271e1b6ac0dc733c3022f62ab6c8`
- `profiles/graphs/random_n180_dense_seed11.txt`: `74d856c428ba04e12286a266f5206c6d2079b2a3`
- `profiles/graphs/random_n180_dense_seed13.txt`: `162cc288f489e5ecb8eecec9611741906b6d1031`
- `profiles/graphs/random_n180_dense_seed17.txt`: `1dcea612985d8fb44b814b21b79f8435c9824f2d`
- `profiles/graphs/random_n180_dense_seed19.txt`: `3d89fbb7f22dbaa288d37e724c06f020c49e2882`
- `profiles/graphs/random_n180_dense_seed23.txt`: `e0059ed8d86e7b53e258767cdad48128affeeb9b`
- `profiles/graphs/random_n180_dense_seed29.txt`: `b47f443f0fdeb4a5693cdfad7e9787a463a4fba5`
- `profiles/graphs/random_n180_dense_seed31.txt`: `d995670e87587e17105b182ee475567b4ce76771`
- `profiles/graphs/random_n180_dense_seed37.txt`: `2f49825d6c37601cd0684e178452c3779a942faf`
- `profiles/graphs/random_n180_dense_seed41.txt`: `26d3c8c51fc9e3ed336a08ab1e17432cd382cb9c`
- `profiles/graphs/random_n180_dense_seed43.txt`: `b34a257b4b3cc9307ec0ff89c19df143dc41e4a8`
- `profiles/graphs/random_n180_dense_seed47.txt`: `94eb3bec724657b7d855873957b35f76aa698a2e`
- `profiles/graphs/random_n188_dense_seed2.txt`: `b1887a675e4cb83a8075ab52ee583bf9b39ff2c4`
- `profiles/graphs/random_n188_dense_seed3.txt`: `12aa49088a5ef1d97eccf580c4aebc06bb932288`
- `profiles/graphs/random_n188_dense_seed5.txt`: `121ccf713a7c9b33860e54c947e03c798eb6d927`
- `profiles/graphs/random_n188_dense_seed7.txt`: `c308cb6758bd48df714f060155b23e06977c4fae`
- `profiles/graphs/random_n188_dense_seed11.txt`: `2b62ac7775d6b2a159066c3855f35796618512bd`
- `profiles/graphs/random_n188_dense_seed13.txt`: `14ef068c1d29c31f7a857ac1bb6d474d43c4252a`
- `profiles/graphs/random_n188_dense_seed17.txt`: `161c3522765fc32d09e94efb4c49b783f42d5627`
- `profiles/graphs/random_n188_dense_seed19.txt`: `7555ace5d15765625da2943cb264f2848c4288f0`
- `profiles/graphs/random_n188_dense_seed23.txt`: `e83b72d0e71be7065ca3fa17360ec18aab256894`
- `profiles/graphs/random_n188_dense_seed29.txt`: `c8d07ec58f62389d93a3b2d027424fb2178a1119`
- `profiles/graphs/random_n188_dense_seed31.txt`: `ccc548e095665d51fa1d9c299433846182b33c80`
- `profiles/graphs/random_n188_dense_seed37.txt`: `6fddbb3d4ac5ad70b9ca69c1c7c41e0e38c609ad`
- `profiles/graphs/random_n188_dense_seed41.txt`: `3743870e97f389ae2ac3b67f58f4eb7652e49bf8`
- `profiles/graphs/random_n188_dense_seed43.txt`: `9979603f2f6d8954a369a32f253acdc7027bde7a`
- `profiles/graphs/random_n188_dense_seed47.txt`: `fe94771868db508e2892cda735513c63a9975506`
- `profiles/graphs/random_n180_seed2.txt`: `504aea127b5406b450cd2a43e7d1b35cb3d6e154`
- `profiles/graphs/random_n180_seed3.txt`: `672ba0a5d885270e35cf43647fdfeaf18e9ec9de`
- `profiles/graphs/random_n180_seed5.txt`: `17f4e872470095fc367a476f0d9ff6f86da02641`
- `profiles/graphs/random_n180_seed7.txt`: `d52a6a0f5161d77e9f622978fe5011d0043ffdaf`
- `profiles/graphs/random_n180_seed11.txt`: `c58fab665777dc15faad04fe975febd8e534b189`
- `profiles/graphs/random_n180_seed13.txt`: `1d42d97e6de00524d1c035c492818decf1ccced8`
- `profiles/graphs/random_n180_seed17.txt`: `ad12a3f3a113e64239810a9aff3dc012181d36f9`
- `profiles/graphs/random_n180_seed19.txt`: `cab54c757e56ca6641f3a43652ef802f7f481904`
- `profiles/graphs/random_n180_seed23.txt`: `79eca53bdb27af733b4273ce7de9b25c952ab664`
- `profiles/graphs/random_n180_seed29.txt`: `fcad0bcebb6c2278e3e8928aa72de7abd6a3551b`
- `profiles/graphs/random_n180_seed31.txt`: `010c2358be38dfbd4a38483c7cba6b0717028e9e`
- `profiles/graphs/random_n180_seed37.txt`: `08b5ca77741ab3f5baf76f4be7a4dfd22caa07fb`
- `profiles/graphs/random_n180_seed41.txt`: `10808808cdb16f65beca0134562f838442f4d64c`
- `profiles/graphs/random_n180_seed43.txt`: `cf479b5b4aa3e0330902791aac3c562460bb4226`
- `profiles/graphs/random_n180_seed47.txt`: `0d1c7d0690566c89c9038f1eaa8f8653cac6285d`
- `profiles/graphs/random_n188_seed2.txt`: `c23d9fa3a270bacbadbcd9375f930d22587d0f31`
- `profiles/graphs/random_n188_seed3.txt`: `750e5bdc1b737d192c7968b3a00425c7d4788e7b`
- `profiles/graphs/random_n188_seed5.txt`: `806811c23752f57a51004f5106c06bee33b2bf2e`
- `profiles/graphs/random_n188_seed7.txt`: `0f65a8da61cf30dfc49ba1652349f96e3675cb2f`
- `profiles/graphs/random_n188_seed11.txt`: `076e7c0918829179fa9be8dfa135c7e9ab08f9d9`
- `profiles/graphs/random_n188_seed13.txt`: `edb525424492bc858163d1749d40e2ef1d5cf350`
- `profiles/graphs/random_n188_seed17.txt`: `7a9f127586bac9c69315d4c5277eb378cf3e9464`
- `profiles/graphs/random_n188_seed19.txt`: `d9d8ed61969b22d0e8754977d1638f2ae97d57b9`
- `profiles/graphs/random_n188_seed23.txt`: `62f6a99d22cc571bc7898ffb7b572b93ce69c366`
- `profiles/graphs/random_n188_seed29.txt`: `d2d003baa95ce8c928c7ca38e8edf121073303d1`
- `profiles/graphs/random_n188_seed31.txt`: `0ef3521861965067111f229a658057188c44a878`
- `profiles/graphs/random_n188_seed37.txt`: `f93f0cc089ab37ed867a1959dd79d78d5a010b6a`
- `profiles/graphs/random_n188_seed41.txt`: `4422e2157079cd890bbb86261ed90fe75d4c40ed`
- `profiles/graphs/random_n188_seed43.txt`: `8897a733974da7225b3d6c4830e5e35663315eef`
- `profiles/graphs/random_n188_seed47.txt`: `b6a9007be6f9c0454e71847ab201151bed21a66a`

## Within-run committed-latency dispersion

These values summarize three aggregation levels per system and arm (loss=0.05 only, loss=0.06 only, and pooled 30 runs). `mean SD` is the arithmetic mean of `sd_round_slots_committed`; CV is that mean SD divided by the arithmetic mean of `mean_round_slots_committed`.

| System | Arm | loss=0.05 Mean SD | loss=0.05 CV | loss=0.05 Runs | loss=0.06 Mean SD | loss=0.06 CV | loss=0.06 Runs | Pooled Mean SD | Pooled CV | Pooled Runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A2/2PC | dense | 2.12894 | 0.07501 | 15 | 2.11347 | 0.07447 | 15 | 2.12120 | 0.07474 | 30 |
| A2/2PC | base | 3.19254 | 0.07522 | 15 | 3.03784 | 0.07163 | 15 | 3.11519 | 0.07343 | 30 |
| WPaxos | dense | 0.46155 | 0.03017 | 15 | 0.45610 | 0.02983 | 15 | 0.45883 | 0.03000 | 30 |
| WPaxos | base | 1.03461 | 0.04203 | 15 | 1.00121 | 0.04057 | 15 | 1.01791 | 0.04130 | 30 |

The reference figure is the loss=0.05 row.

No causal conclusion is drawn.

## Slot-length convention

`published_slot_lengths.csv` records both `slot_ms_nominal` and `slot_ms_realised`. The harness uses nominal values. The published targets were themselves derived from nominal values (`100 × 4.75 = 475 ms`; `57.8 × 5.00 = 289 ms`), so this convention leaves the residual unchanged. The realised values are 2.34% below nominal for both protocols because of 32768 Hz timer quantisation. Any comparison against a hardware-measured millisecond figure therefore carries that systematic bias.

## Previously reused addition13 aggregate

- File: `docs/validation/addition13/data/blind_predictions.csv`
- Current blob: `d0707627a6ecdc3ed2c686dd19305aecd46d4474`
- Commit that last touched it: `c16bf856d0b3473c4b756244efec708fcbd5fcda`

## Outcome-classifier reachability

Configuration: `a2_sensys17`, `2pc_ce`, n=180, arm dense (graph `random_n180_dense_seed2.txt`), proposals=20, channel_seed=2.

In this architecture, `ProposalRecord::latency` is the per-round slot count: `src/metrics.rs` defines it as `end - start`, the simulation deadline in `src/phy/ce.rs` is `round_start + max_round_slots`, and one proposal corresponds to one round. The test `round_boundaries_tile_timeline_and_latency_equals_round_length` enforces that rounds tile the timeline with no gaps, ensuring this equivalence. The CSV columns named `*_round_slots_*` and the Rust field named `latency` are therefore the same quantity under two names, and no published number changes as a result of this clarification.

For 2PC over CE, a round exceeding the cap is classified as an ABORT (see `proposal_outcome` in `src/protocol/two_pc_ce.rs`); `timed_out` is produced only by the global `max_slots` guard in `src/sim.rs` (unlike Paxos and TOM, which classify incompleteness as `TimedOut`).

The setting `abort_probability = 0.0` makes deadline-incompleteness the only possible source of an abort. The timeout limit `max_round_slots = 4000` is about 140x the mean round length. The three diagnostic arms below map the boundary: cap 40 yields aborts only at the highest loss values, while cap 30 and cap 20 abort every proposal. The published configuration's maximum round length is 46 slots at loss 0.50, representing 1.15% of the 4000-slot cap. The final arm demonstrates that the `timed_out` column is reachable in principle, through global budget exhaustion only.

```text
Configuration: a2_sensys17, 2pc_ce, n=180, arm dense, graph_seed=2, channel_seed=2, proposals=20, abort_probability=0.0

=== Validation Configuration (max_round_slots=4000) ===
Loss = 0.05 | C/A/T: 20/0/0 | Mean round: 28.75 slots | Max round: 34 slots
Loss = 0.10 | C/A/T: 20/0/0 | Mean round: 28.45 slots | Max round: 31 slots
Loss = 0.15 | C/A/T: 20/0/0 | Mean round: 28.15 slots | Max round: 31 slots
Loss = 0.20 | C/A/T: 20/0/0 | Mean round: 29.65 slots | Max round: 36 slots
Loss = 0.25 | C/A/T: 20/0/0 | Mean round: 29.50 slots | Max round: 34 slots
Loss = 0.30 | C/A/T: 20/0/0 | Mean round: 31.30 slots | Max round: 38 slots
Loss = 0.35 | C/A/T: 20/0/0 | Mean round: 32.35 slots | Max round: 39 slots
Loss = 0.40 | C/A/T: 20/0/0 | Mean round: 35.80 slots | Max round: 43 slots
Loss = 0.45 | C/A/T: 20/0/0 | Mean round: 37.35 slots | Max round: 43 slots
Loss = 0.50 | C/A/T: 20/0/0 | Mean round: 38.20 slots | Max round: 46 slots

=== Diagnostic Arm: third outcome class reachability (max_round_slots=40) - NOT part of validation configuration ===
Loss = 0.05 | C/A/T: 20/0/0 | Mean round: 28.75 slots | Max round: 34 slots
Loss = 0.10 | C/A/T: 20/0/0 | Mean round: 28.45 slots | Max round: 31 slots
Loss = 0.15 | C/A/T: 20/0/0 | Mean round: 28.15 slots | Max round: 31 slots
Loss = 0.20 | C/A/T: 20/0/0 | Mean round: 29.65 slots | Max round: 36 slots
Loss = 0.25 | C/A/T: 20/0/0 | Mean round: 29.50 slots | Max round: 34 slots
Loss = 0.30 | C/A/T: 20/0/0 | Mean round: 31.30 slots | Max round: 38 slots
Loss = 0.35 | C/A/T: 20/0/0 | Mean round: 32.35 slots | Max round: 39 slots
Loss = 0.40 | C/A/T: 19/1/0 | Mean round: 33.80 slots | Max round: 40 slots
Loss = 0.45 | C/A/T: 18/2/0 | Mean round: 35.40 slots | Max round: 40 slots
Loss = 0.50 | C/A/T: 15/5/0 | Mean round: 37.90 slots | Max round: 40 slots
Summary: The 'aborted' outcome class was reached at loss values: 0.40, 0.45, 0.50

=== Diagnostic Arm: third outcome class reachability (max_round_slots=30) - NOT part of validation configuration ===
Loss = 0.05 | C/A/T: 17/3/0 | Mean round: 28.05 slots | Max round: 30 slots
Loss = 0.10 | C/A/T: 20/0/0 | Mean round: 28.25 slots | Max round: 30 slots
Loss = 0.15 | C/A/T: 20/0/0 | Mean round: 28.00 slots | Max round: 30 slots
Loss = 0.20 | C/A/T: 18/2/0 | Mean round: 28.35 slots | Max round: 30 slots
Loss = 0.25 | C/A/T: 15/5/0 | Mean round: 28.40 slots | Max round: 30 slots
Loss = 0.30 | C/A/T: 12/8/0 | Mean round: 29.40 slots | Max round: 30 slots
Loss = 0.35 | C/A/T: 6/14/0 | Mean round: 29.80 slots | Max round: 30 slots
Loss = 0.40 | C/A/T: 8/12/0 | Mean round: 29.95 slots | Max round: 30 slots
Loss = 0.45 | C/A/T: 3/17/0 | Mean round: 30.00 slots | Max round: 30 slots
Loss = 0.50 | C/A/T: 0/20/0 | Mean round: 30.00 slots | Max round: 30 slots
Summary: The 'aborted' outcome class was reached at loss values: 0.05, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50

=== Diagnostic Arm: third outcome class reachability (max_round_slots=20) - NOT part of validation configuration ===
Loss = 0.05 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.10 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.15 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.20 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.25 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.30 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.35 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.40 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.45 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Loss = 0.50 | C/A/T: 0/20/0 | Mean round: 20.00 slots | Max round: 20 slots
Summary: The 'aborted' outcome class was reached at loss values: 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50

=== Diagnostic Arm: timed_out is reachable only through global budget exhaustion and not through round length (max_slots=500) - NOT part of validation configuration ===
Loss = 0.05 | C/A/T: 18/0/2 | Mean round: 25.85 slots | Max round: 34 slots
Loss = 0.10 | C/A/T: 18/0/2 | Mean round: 25.80 slots | Max round: 31 slots
Loss = 0.15 | C/A/T: 18/0/2 | Mean round: 25.50 slots | Max round: 31 slots
Loss = 0.20 | C/A/T: 18/0/2 | Mean round: 26.40 slots | Max round: 36 slots
Loss = 0.25 | C/A/T: 17/0/3 | Mean round: 25.05 slots | Max round: 34 slots
Loss = 0.30 | C/A/T: 17/0/3 | Mean round: 26.40 slots | Max round: 38 slots
Loss = 0.35 | C/A/T: 16/0/4 | Mean round: 25.75 slots | Max round: 37 slots
Loss = 0.40 | C/A/T: 14/0/6 | Mean round: 25.85 slots | Max round: 43 slots
Loss = 0.45 | C/A/T: 14/0/6 | Mean round: 26.30 slots | Max round: 43 slots
Loss = 0.50 | C/A/T: 14/0/6 | Mean round: 26.00 slots | Max round: 43 slots
```

The `n_timed_out = 0` column is a structural guarantee for this protocol and configuration and carries no information, whereas `n_aborted = 0` is informative because `abort_probability = 0.0` makes deadline-incompleteness the only possible source of an abort, and the diagnostic arms prove that column is reachable in this same code. Note that the mean produced by the 20-proposal single-channel-seed reachability run is not the same quantity as the 15-run aggregate mean of 28.45 slots and must not be quoted in its place.

Within the tested parameter range no run reached abort or timeout; these zero columns are a property of the chosen configuration, not evidence of robustness.
