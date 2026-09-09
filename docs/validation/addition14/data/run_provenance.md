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

These values summarize the 30 runs per system and arm (15 graph seeds at each of two loss rates). `mean SD` is the arithmetic mean of `sd_round_slots_committed`; CV is that mean SD divided by the arithmetic mean of `mean_round_slots_committed`.

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
Result: Swept loss rate from 0.05 to 0.50 in steps of 0.05. No non-committed outcome appeared up to 0.50.
