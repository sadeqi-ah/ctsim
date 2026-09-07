#!/usr/bin/env python3
"""Derive T_slot for CTSim from the Bluetooth 5 LE 2M (uncoded) PHY.

Produces every number in docs/validation/t_slot.md. Standard library only.

Every number printed here is computed, not recalled. Two payload models:

  L_json(N): the bytes CTSim actually puts in `node.payload` today
             (serde_json::to_vec of TwoPcPacket, src/protocol/two_pc_pipeline.rs).
  L_wire(N): the bit-packed encoding the same packet would need on a real radio.

serde_json emits struct fields in declaration order, no spaces, bools as
true/false, unit enum variants as quoted names, Option::None as null,
Vec<u8> as a JSON array of decimal integers.
"""

import json


def json_payload_len(n_nodes: int, tx_id: int, data: bytes, *, piggyback: bool) -> int:
    """Exact byte length of serde_json::to_vec(&TwoPcPacket).

    Field order copied from the struct declaration:
    transaction_id, state, flags_bitmap, abort_flag, nack_tx_id,
    transaction_data, sender, piggyback_tx, piggyback_state.
    """
    pkt = {
        "transaction_id": tx_id,
        "state": "Prepare",
        "flags_bitmap": [False] * n_nodes,
        "abort_flag": False,
        "nack_tx_id": 0,
        "transaction_data": list(data),
        "sender": 0,
        "piggyback_tx": tx_id if piggyback else None,
        "piggyback_state": "Committed" if piggyback else None,
    }
    # separators=(',', ':') reproduces serde_json's compact output.
    return len(json.dumps(pkt, separators=(",", ":")).encode())


def wire_payload_len(n_nodes: int) -> int:
    """Bit-packed encoding of the same semantic content, in octets.

    transaction_id  u32  -> 4   (100 proposals per run; u64 is not needed on air)
    flags_bitmap    N bits -> ceil(N/8)
    nack_tx_id      u32  -> 4
    sender          u8   -> 1   (N <= 255 in every configuration we run)
    transaction_data     -> 8   ('tx{term}' is <= 8 ASCII bytes for term < 100000)
    piggyback_tx    u32  -> 4
    state + abort_flag + piggyback_state -> 1 packed octet
    """
    return 4 + (n_nodes + 7) // 8 + 4 + 1 + 8 + 4 + 1


# ---- Bluetooth 5, LE 2M uncoded PHY: fixed, spec-level quantities ----
SYMBOL_RATE_MSPS = 2.0                 # 2 Msym/s, 1 bit/symbol uncoded
T_BIT_US = 1.0 / SYMBOL_RATE_MSPS      # 0.5 us per bit
PREAMBLE_BITS = 16                     # 2 octets on the 2M PHY (1 octet on 1M)
ACCESS_ADDR_BITS = 32
PDU_HEADER_BITS = 16
CRC_BITS = 24
OVERHEAD_BITS = PREAMBLE_BITS + ACCESS_ADDR_BITS + PDU_HEADER_BITS + CRC_BITS
MAX_PDU_PAYLOAD_OCTETS = 251           # LL Data PDU payload ceiling (LE Data Length Extension)

# Per-slot additions. T_IFS is the spec value; the guard band is an
# implementation parameter and is reported as a range, never as one
# invented number.
T_IFS_US = 150.0
GUARD_US_RANGE = (10.0, 100.0)


def airtime_us(payload_octets: int) -> float:
    return (OVERHEAD_BITS + 8 * payload_octets) * T_BIT_US


def t_slot_us(payload_octets: int, guard_us: float) -> float:
    return airtime_us(payload_octets) + T_IFS_US + 2.0 * guard_us


print(f"t_bit                 = {T_BIT_US} us")
print(f"framing overhead      = {OVERHEAD_BITS} bits = {OVERHEAD_BITS * T_BIT_US} us")
print(f"airtime(L)            = {OVERHEAD_BITS * T_BIT_US} + {8 * T_BIT_US}*L us")
print(f"T_IFS                 = {T_IFS_US} us")
print(f"guard band            = {GUARD_US_RANGE[0]}..{GUARD_US_RANGE[1]} us (per side, implementation)")
print(f"max PDU payload       = {MAX_PDU_PAYLOAD_OCTETS} octets")
print()

header = (
    f"{'N':>5} {'L_json':>7} {'fits?':>6} {'L_wire':>7} "
    f"{'air_us':>8} {'T_slot_lo':>10} {'T_slot_hi':>10}"
)
print(header)
print("-" * len(header))

for n in (2, 9, 15, 27, 45, 81, 180, 188, 255):
    lj = json_payload_len(n, tx_id=99, data=b"tx99", piggyback=True)
    lw = wire_payload_len(n)
    fits = "yes" if lj <= MAX_PDU_PAYLOAD_OCTETS else "NO"
    air = airtime_us(lw)
    lo = t_slot_us(lw, GUARD_US_RANGE[0])
    hi = t_slot_us(lw, GUARD_US_RANGE[1])
    print(f"{n:>5} {lj:>7} {fits:>6} {lw:>7} {air:>8.1f} {lo:>10.1f} {hi:>10.1f}")

print()
print("JSON growth per node (bytes), measured by differencing:")
for a, b in ((27, 28), (180, 181), (188, 189)):
    d = json_payload_len(b, 99, b"tx99", piggyback=True) - json_payload_len(
        a, 99, b"tx99", piggyback=True
    )
    print(f"  N={a} -> {b}: +{d} B/node")

print()
print("Smallest N whose JSON payload exceeds the 251-octet PDU ceiling:")
n = 2
while json_payload_len(n, 99, b"tx99", piggyback=True) <= MAX_PDU_PAYLOAD_OCTETS:
    n += 1
print(f"  N = {n} (L_json = {json_payload_len(n, 99, b'tx99', piggyback=True)} B)")

print()
print("Wire-model T_slot at the two literature comparison points:")
for n, ref_ms, ref in ((180, 475.0, "A2 2PC, SenSys'17"), (188, 289.0, "Wireless Paxos, EWSN'19")):
    lw = wire_payload_len(n)
    for g in GUARD_US_RANGE:
        ts = t_slot_us(lw, g) / 1000.0  # ms
        print(
            f"  N={n:<4} guard={g:>5.0f}us  T_slot={ts:.4f} ms  "
            f"-> {ref_ms} ms budget = {ref_ms / ts:.1f} slots  [{ref}]"
        )

print()
print("Invariance check (step 6b), done numerically as well as analytically:")
base = t_slot_us(wire_payload_len(27), 10.0)
for factor in (0.5, 1.0, 1.5):
    scaled = base * factor
    slots = 4.7033  # CI/Paxos slots-per-decision, full_mesh N=27, from the frozen table
    print(
        f"  T_slot x {factor:<4} = {scaled:>8.2f} us -> {slots} slots = "
        f"{slots * scaled / 1000.0:.4f} ms   (slot count unchanged: {slots})"
    )
