# Non-blocking 2PC on CI (`2pc_pipeline`)

**Code:** `src/protocol/two_pc_pipeline.rs`, `src/sim/two_pc_pipeline.rs`  
**PHY:** `flood_identical_round`  
**Config:** `protocol = "2pc_pipeline"`, `phy_mode = "ci"`  
**Related config:** top-level `abort_probability` (app-level NO)

---

## 1. Goal

**Unanimous** commit (all N YES) for each transaction, with:

- **Bounded voting:** decision after one full RR cycle (`num_nodes` rounds of life).
- **Non-blocking:** any node that sees All-1s (or explicit abort) can finalize without waiting for a single coordinator.
- **Fast abort:** missing YES after bound → Abort; or `abort_flag` → Abort.

---

## 2. Packet (`TwoPcPacket`)

```text
transaction_id: u64
state: Prepare | Committed | Aborted   # wire state for current flood focus
flags_bitmap: Vec<bool>                # YES votes (cumulative for pipeline)
abort_flag: bool                       # explicit NO / app failure
nack_tx_id: u64                        # gap recovery for finalized log
sender: usize
transaction_data: Vec<u8>
piggyback_tx / piggyback_state         # recovery of final decision
```

---

## 3. Local state

`PendingTx`: `tx_id`, `data`, `bitmap`, `abort_flag`, `start_round`  
`log`: finalized `(tx_id, Committed|Aborted)`

- `check_unanimity(tx)`: all bits true **and** not `abort_flag`.
- `check_explicit_abort(tx)`: `abort_flag`.
- `merge_votes_up_to(tx_id, bitmap, abort_flag)`: OR YES bits for all pending `≤ tx_id`; set abort if flag for that id.
- `detect_gap` / finalize helpers for log holes + piggyback.

---

## 4. Round loop

```
initiator = round_num % N
Phase 1: build TwoPcPacket
Phase 2: CI flood (identical)
Phase 3: Sleep participants update pending / finalize
```

### Phase 1 — initiator

1. NACK missing finalized TX if any.
2. If still generating TXs:
   - With probability `abort_probability`: start TX with `abort_flag=true` (no self YES).
   - Else: self YES in bitmap.
   - `start_round = round_num`.
3. **Bounded decision** for each pending with `round_num >= start_round + N`:
   - Unanimity → **Committed**
   - Else → **Aborted**
   - Record metrics (start_slot ≈ `start_round * round_len` when `round_slots` known).
4. Flood packet for `current_tx` with cumulative flags + abort_flag + piggyback.

### Phase 3 — receivers

1. First sight of TX: decide **once** YES or app-NO (`abort_probability`); store pending.
2. Merge overheard votes/abort for pipeline TXs.
3. Sticky self YES if not aborted.
4. **Fast abort** if `abort_flag` on any pending → finalize Aborted immediately.
5. Bounded finalize same as initiator (overhearing-based non-blocking).
6. Piggyback final decisions for NACK’d TX ids.

---

## 5. Why “non-blocking”

Classic 2PC blocks if coordinator dies after collecting votes. Here:

- Bitmap is flooded network-wide (CI overhearing).
- After **exactly N RR rounds** of lifetime, **every** node independently evaluates All-1s vs not.
- No extra PreCommit phase (3PC); determinism of RR replaces dynamic timeouts for the voting window.

---

## 6. Abort conditions

| Case | Outcome |
|------|---------|
| Explicit `abort_flag` (app NO) | **Aborted** (fast) |
| Bound elapsed, bitmap not All-1s (loss / offline) | **Aborted** |
| Bound elapsed, All-1s, no abort | **Committed** |

---

## 7. Recovery

- **NACK** on missing **finalized** log entry.
- **Piggyback** of `(tx_id, Committed|Aborted)`.
- CI identical-flood + RR continues regardless of coordinator failure (next initiator continues pipeline).

---

## 8. CI PHY coupling

Same as other pipelines: one identical JSON blob per flood; middleware only between rounds; Sleep ⇒ participated successfully.
