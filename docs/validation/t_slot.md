# `T_slot`: deriving a real-time unit, and why perturbing it cannot move the simulator

Step 2.1 of the validation plan. **Analysis only — this document changes no
code.** It adds no config field, no constant and no output column; `Slot`
remains `pub type Slot = u64` (`src/event.rs`).

Two questions are answered:

1. **What is one slot worth in milliseconds**, if the radio is the Bluetooth 5
   LE 2M uncoded PHY?
2. **What does step 6b's ±50 % perturbation of slot duration change?** Answer:
   provably nothing that the simulator reports in slots. The proof is below and
   it removes the need for that sweep axis.

Every number in the tables was produced by
[`scripts/t_slot.py`](scripts/t_slot.py); rerun it rather than trusting the
tables.

---

## 1. Starting point: there is no `T_slot` to calibrate

`docs/validation/inventory.md` already recorded this, and it still holds on
`main`:

- `SimConfig` (`src/config.rs`) has `snapshot_interval`, `max_slots`,
  `round_slots`, `listen_timeout`, `max_round_slots` — all counted in slots.
  There is no duration, bitrate, airtime, turnaround or guard parameter.
- Both engines advance time with `slot += 1` (`src/phy/ci.rs`,
  `src/phy/ce.rs`). Neither reads a clock.
- Every reported latency (`avg_latency`, `results_*.csv`, `end_slot`) is a slot
  count, and every energy figure is a node-slot count.

So `T_slot` cannot be *calibrated* against the simulator; it can only be
*derived externally* and applied afterwards as a unit conversion. That is what
this document does, and section 4 shows why that ordering costs nothing.

---

## 2. PHY quantities

Bluetooth 5, LE 2M uncoded PHY. These are spec-level constants, not
measurements of our system.

| Quantity | Value | Note |
|---|---|---|
| Symbol rate | 2 Msym/s | 1 bit/symbol, uncoded |
| `t_bit` | 0.5 µs | 1 / 2 Msym/s |
| Preamble | 16 bits | 2 octets on the 2M PHY (1 octet on 1M) |
| Access address | 32 bits | |
| PDU header | 16 bits | |
| CRC | 24 bits | |
| **Framing overhead** | **88 bits = 44.0 µs** | sum of the four above |
| `T_IFS` | 150 µs | inter-frame space |
| Max LL Data PDU payload | 251 octets | with LE Data Length Extension |

**Cited locations in the Core Specification, Vol 6, Part B (Link Layer).**
Every row above is fixed by the spec, not measured:

| Row | CS Vol 6, Part B reference |
|---|---|
| Preamble, 16 bits on the 2M PHY | 2.2.2 ("the 2M PHY's preamble is 2 octets") |
| Access address, 32 bits | 2.3.1 (advertising) / 3.2.1 (data) |
| PDU header, 16 bits | 2.3.2 / 3.3.1, PDU header is 16 bits |
| CRC, 24 bits | 2.3.3.1 and 3.3.2 (CRC, 3 octets) |
| `T_IFS` = 150 us | 4.1.1, inter-frame spacing |
| 251-octet payload | Vol 6, Part B, 4.4.2.5; Data Length Extension, 5.4 |

> **Citation status - normative inputs closed, arithmetic explicit, step 2.50.**
> The normative PHY inputs are CLOSED: symbol rate, preamble, access
> address, PDU header, CRC, `T_IFS`, and the payload limit are each
> identified by Core Specification section numbers in the table just above
> (Vol 6, Part B, following the 6.0 Core Specification Supplement). These
> are *book* citations (section numbers, not per-row page numbers): the
> specification is a continuously paginated volume and its section numbers
> are the stable identifiers used in the standard. What is deliberately
> NOT claimed as closed: the airtime row. `T_air(L) = (88 + 8L) x 0.5 us
> = 44.0 + 4.0 x L` is not a specification quotation and needs no separate
> external citation; it is this document's transparent arithmetic
> derivation over the cited field widths and symbol rate, and it must not
> be read as if the specification itself states `44 + 4L` -- the spec
> fixes the field widths, not the airtime formula. `T_guard` remains an
> implementation parameter, not a spec constant, and stays bracketed at
> 10 us and 100 us per side below; it is a model assumption, not a
> normative input. No specification PDF was added and no page-level
> verification was performed; what is closed is the identification of the
> normative inputs by section number, nothing more.

Airtime for a payload of `L` octets:

```
T_air(L) = (88 + 8L) x 0.5 us = 44.0 + 4.0 x L   [us]
```

One flooding slot must hold the transmission plus the receiver's turnaround and
a guard band on each side:

```
T_slot(L) = T_air(L) + T_IFS + 2 x T_guard
```

`T_guard` is an **implementation** parameter, not a spec constant. Rather than
invent one value, the tables below bracket it at 10 µs and 100 µs per side and
report both ends. Narrowing that bracket requires a citation to a concrete
constructive-interference stack (BlueFlood or A2), and is deliberately left
open here.

---

## 3. What is actually in the packet

### 3.1 The encoding CTSim floods today: `serde_json`

`src/protocol/two_pc_pipeline.rs`:

```rust
pub fn serialize_packet(pkt: &TwoPcPacket) -> Vec<u8> {
    serde_json::to_vec(pkt).unwrap_or_default()
}
```

`TwoPcPacket::flags_bitmap` is a `Vec<bool>` of length `N`, so the JSON text
carries the literal `true`/`false` for every node: **+6 bytes per node**,
measured by differencing consecutive `N` (the script does this rather than
assuming it).

| `N` | `L_json` (B) | Fits in 251 octets? |
|---:|---:|:---|
| 2 | 196 | yes |
| 9 | 238 | yes |
| 15 | 274 | **no** |
| 27 | 346 | **no** |
| 45 | 454 | **no** |
| 81 | 670 | **no** |
| 180 | 1264 | **no** |
| 188 | 1312 | **no** |
| 255 | 1714 | **no** |

**The crossing point is `N = 12` (`L_json` = 256 B).**

This is a finding, and it needs stating plainly rather than burying:

> Every configuration in the paper with `N ≥ 15` — including the `N = 27`
> topology study, the scalability sweep, and the `N = 180` / `N = 188`
> literature comparison points — floods a packet that, **as currently encoded**,
> does not fit in a single Bluetooth 5 2M packet.

What it does and does not invalidate:

- **It does not change any slot count.** The simulator never models packet
  length; `flood_identical_round` transmits `node.payload` in one slot whatever
  its size. So every published slot-valued and node-slot-valued result stands
  exactly as measured.
- **It does invalidate any naive millisecond claim** built by multiplying those
  slot counts by an airtime computed from `L_json`. A one-slot flood of a 1264-byte
  JSON blob is not a physically realisable BLE transmission.
- **It is an encoding artefact, not a protocol defect.** JSON is a debugging
  convenience; the protocol's semantic content is small. Section 3.2 quantifies that.

### 3.2 The wire model: what the same packet costs bit-packed

Same semantic content, encoded as a real radio protocol would:

| Field | Encoding | Octets |
|---|---|---:|
| `transaction_id` | u32 | 4 |
| `flags_bitmap` | `N` bits | `ceil(N/8)` |
| `nack_tx_id` | u32 | 4 |
| `sender` | u8 (`N ≤ 255` in every configuration we run) | 1 |
| `transaction_data` | `tx{term}` ASCII | 8 |
| `piggyback_tx` | u32 | 4 |
| `state`, `abort_flag`, `piggyback_state` | packed bit fields | 1 |
| **Total** | | **`ceil(N/8) + 22`** |

| `N` | `L_wire` (B) | `T_air` (µs) | `T_slot` @10 µs guard (µs) | `T_slot` @100 µs guard (µs) |
|---:|---:|---:|---:|---:|
| 2 | 23 | 136.0 | 306.0 | 486.0 |
| 9 | 24 | 140.0 | 310.0 | 490.0 |
| 27 | 26 | 148.0 | 318.0 | 498.0 |
| 45 | 28 | 156.0 | 326.0 | 506.0 |
| 81 | 33 | 176.0 | 346.0 | 526.0 |
| 180 | 45 | 224.0 | 394.0 | 574.0 |
| 188 | 46 | 228.0 | 398.0 | 578.0 |
| 255 | 54 | 260.0 | 430.0 | 610.0 |

Bit-packed, the packet fits comfortably at every `N` we simulate, and `T_slot`
is weakly dependent on `N`: it grows by 124 µs (10 µs guard) across the whole
range 2 → 255, because the bitmap contributes only one bit per node
(every `T_slot` here is a lower bound; see section 5.5).

**`T_slot` is a function of `N`, not a constant** (a lower bound; see section
5.5). Any millisecond figure quoted
for a given topology must name the `N` it used.

---

## 4. Step 6b: perturbing `T_slot` is provably a no-op

Step 6 asks for a ±50 % sensitivity sweep over slot duration. It does not need
to be run. The claim is structural.

**Lemma 1 (the engines are dimensionless).** The only time variable in either
engine is the integer `slot`, advanced by `slot += 1`. Every branch that reads
time compares slot integers:

- `src/phy/ci.rs`: `while slot < round_end`, with
  `round_end = round_start + round_slots` and `round_slots` an integer config
  value or `max(3, (diameter + 2) * flood_repeats)`.
- `src/phy/ce.rs`: `while slot < deadline`, with
  `deadline = round_start + ce_cfg.max_round_slots`, and the recovery predicate
  `(slot - nodes[i].last_progress_slot) >= ce_cfg.listen_timeout`.

No expression anywhere in `src/` multiplies, divides or compares a slot against
a duration, because no duration exists in the program. ∎

**Lemma 2 (the transition relation is `T_slot`-free).** State transitions depend
on `(state, adjacency, loss_rate, rng, payload)` only. `T_slot` appears in none
of them, so the entire trajectory of the simulation — hence every slot count,
every `start_slot`/`end_slot`, every `listen`/`flood`/`sleep` tick total — is
invariant under any change of `T_slot`. ∎

**Lemma 3 (`T_slot` acts as a scalar on the derived quantities).** Wall-clock
latency is `latency_ms = slots x T_slot`, and duty cycle is a ratio of node-slot
counts, so it is invariant outright. Therefore:

| Quantity | Under `T_slot -> c x T_slot` |
|---|---|
| Any slot count (`avg_latency`, `end_slot`, slots/decision) | **unchanged** |
| Any node-slot count (`listen`, `flood`, `sleep`) | **unchanged** |
| Duty cycle, `C_t`, pipeline depth, energy ratios | **unchanged** (ratios) |
| Latency in ms, throughput in tx/s | scales by `c`, exactly |

Numerically, on the `full_mesh` `N = 27` CI/Paxos figure of 4.7033
slots/decision, with `T_slot` = 318.0 µs (a lower bound; see section 5.5):

| Factor | `T_slot` (µs) | Latency (ms) | Slot count |
|---|---:|---:|---:|
| 0.5 | 159.00 | 0.7478 | 4.7033 |
| 1.0 | 318.00 | 1.4956 | 4.7033 |
| 1.5 | 477.00 | 2.2435 | 4.7033 |

**Consequence for the manuscript.** The step-6 sensitivity table has three axes.
`N_retx` (`flood_repeats`) is genuinely sweepable. The slot-duration axis is
not a sensitivity axis at all — it is a unit change, and reporting it as
sensitivity would overstate what was tested. The correlated-loss axis remains
genuinely missing (there is no such process in `src/`; `loss_rate` is i.i.d. per
link per slot). The honest statement is one sentence of algebra plus the table
above, not a sweep.

---

## 5. What this does **not** license

1. **No millisecond figure enters the paper yet.** `T_guard` is bracketed, not
   pinned, so `T_slot` is known to roughly ±30 % at every `N`. Publishing a
   point value would be false precision.
2. **The `N = 180` / `N = 188` comparisons stay blind.** For reference, the
   published budgets divided by the wire-model `T_slot` give the slot budgets we
   would have to meet:

   | Reference | `N` | Budget | Guard 10 µs | Guard 100 µs |
   |---|---:|---:|---:|---:|
   | A2 (2PC, SenSys'17) | 180 | 475 ms | 1205.6 slots | 827.5 slots |
   | Wireless Paxos (EWSN'19) | 188 | 289 ms | 726.1 slots | 500.0 slots |

   These are *targets*, computed here so the prediction can be stated in slots
   before any run. They are not results, and the citation debt on both budgets
   is still open.
3. **The framing table's normative inputs are now section-cited** (section 2),
   and the airtime formula is explicitly this document's own derivation
   over those cited inputs, not a specification statement.
4. **The `L_json` finding needs a decision**, recorded but not taken here:
   either the manuscript states that packet length is not modelled and quotes the
   bit-packed wire model when converting to milliseconds, or the simulator gains
   a real serialiser. The second is a code change and is out of scope for step 2.1.

---

## 5.5 Frozen scope of the timing model

By owner decision (option B), the timing model in this document is
frozen as it stands: it is neither rewritten nor recalibrated here.
This section records its limits explicitly.

1. **Lower bound, not an estimate.** `T_slot(L) = T_air(L) + T_IFS +
   2 x T_guard` accounts only for airtime, one inter-frame space, and
   a guard band on each side.  It excludes MCU wake-up, radio ramp-up
   and turnaround beyond `T_IFS`, per-packet processing, and any flood
   repetition.  Every value in the section 3.2 table - the 306 to 610
   microsecond range - is therefore a lower bound on a physically
   realisable slot, not an estimate of one.  This reminder applies
   wherever a `T_slot` value above is stated as if it were the slot
   duration.
2. **Conflict with published firmware slot lengths, recorded, not
   resolved.** `docs/validation/addition14/data/published_slot_lengths.csv`
   records nominal firmware slot lengths of 4.75 ms for the 2PC and 3PC
   profiles and 5.00 ms for `wireless_paxos`, roughly an order of
   magnitude above the 306 to 610 microsecond range derived here.  The
   gap is unexplained and is precisely the part of the model being
   frozen.  Neither figure may be used to calibrate the other; closing
   the gap requires a dedicated, owner-approved round with a
   measurement, not a documentation edit.
3. **Nominal versus realised.** Realised slot lengths run about 2.34
   percent below nominal because of 32.768 kHz timer quantisation, so
   any comparison against a published hardware figure carries that
   systematic bias.  This caveat is quoted, not recomputed, from
   `docs/validation/addition14/data/run_provenance.md`;
   `docs/validation/addition14/data/published_slot_lengths.csv` carries
   both the `slot_ms_nominal` and `slot_ms_realised` columns.
4. **No wall-clock claim is licensed.** Simulator round timing is
   uncalibrated: the engines advance an integer slot counter and no
   duration exists in the program (proved in section 4).  Every
   millisecond figure in this document is a unit conversion applied to
   a slot count, computed with a bracketed and not pinned `T_guard`.
   This document licenses no wall-clock latency claim for any
   protocol.  The A2 475 ms and Wireless Paxos 289 ms entries in
   section 5, item 2, remain targets stated in slots, with their citation
   debt still open, and the blind predictions already recorded
   against them are failures, not validations.

   STEP 2.50 PROVENANCE for the two budgets (issue 374), stated as
   precisely as the sources allow:
   - **A2, 475 ms, 180 nodes** comes from `alnahas17a2` (SenSys 2017,
     doi:10.1145/3131672.3131685). The paper reports the completion time
     of a single two-phase-commit decision across its 180-node testbed.
     The figure is a measured single-decision latency, read from the
     paper's evaluation; it is not a latency bound, not a throughput
     number, and not a figure this document derives. What is measured:
     one 2PC decision, end to end, on that testbed.
   - **Wireless Paxos, 289 ms, 188 nodes** comes from `poirot19paxos`
     (EWSN 2019) and is corroborated by `poirot20thesis`. Same status:
     a measured single-decision Paxos latency on a 188-node testbed, not
     a bound and not a derivation.
   - Neither source states a slot length, a guard time, or a
     packet-length model, so the slot budgets in the table above
     (1205.6 / 827.5 and 726.1 / 500.0) are this document's own
     conversion, not a claim from either paper. The conversion is
     one-way only (published ms to simulator slots); the reverse
     direction is not licensed, as section 5.5 already records.

---

## 6. Reproducing the tables

```
python3 docs/validation/scripts/t_slot.py
```

No dependencies beyond the standard library. The script recomputes the JSON
lengths by actually serialising the packet layout (field order copied from the
struct declaration), differences consecutive `N` to measure the per-node cost
rather than assuming 6 bytes, and searches for the 251-octet crossing point
rather than stating it.
