# Pipeline Paxos on CI (`paxos_pipeline`)

**Code:** `src/protocol/paxos.rs`, `src/sim/paxos_pipeline.rs`  
**PHY:** `flood_identical_round` (identical flood)  
**Config:** `protocol = "paxos_pipeline"`, `phy_mode = "ci"`

---

## 1. Goal

Agree on a sequence of proposals (terms `0..num_proposals-1`) under **majority quorum**, with **pipelined** floods (one RR initiator per flood round), without classical Prepare/Accept **phases** in the packet.

Commit is **implicit** via `last_accepted_term`.

---

## 2. Packet (`PaxosPacket`)

```text
Header:
  current_term: u64              # term of primary data this flood (or drain term)
  last_accepted_term: Option     # highest term known committed (quorum)
  flags_bitmap: Vec<bool>        # votes for current_term (and merged into pending)
  nack_term: u64                 # 0 = none; else missing term request
  sender: usize

Payload:
  proposal_data: Vec<u8>         # empty when draining
  piggyback_term: Option<u64>
  piggyback_data: Vec<u8>
```

No `Phase` field.

---

## 3. Local state (`NodePaxosState`)

| Field | Meaning |
|-------|---------|
| `highest_seen_term` | Max term observed on wire |
| `last_accepted` | Max term known committed |
| `log` | Committed `(term, data)` |
| `pending` | Awaiting quorum: term, data, bitmap |

Helpers:

- `merge_votes_up_to(T, bitmap)` — OR bits into **all** pending with `term ≤ T` (**cumulative voting**).
- `check_quorum(term)` — votes ≥ `N/2 + 1`.
- `commit_up_to(T)` — move all terms `0..=T` into log.
- `detect_gap(up_to)` — first missing term in `[last_accepted+1, up_to)`.

---

## 4. Round loop (orchestrator)

```
round_num = 0
term_counter = 0
loop:
  initiator = round_num % N
  Phase 1: initiator builds PaxosPacket
  Phase 2: flood_identical_round(initiator)  # identical bytes
  Phase 3: every node that ended Sleep processes packet
  terminate / drain checks
  round_num += 1
```

### Phase 1 — initiator build

1. **NACK:** `nack_term = detect_gap(term_counter)`.
2. **New proposal** if still generating:
   - term = `term_counter`, data = `b"tx{term}"`
   - pending push with self-bit = 1
   - record `proposal_starts[term] = current_slot`
   - `term_counter++`
3. Else **drain:** `current_term = term_counter-1`, empty `proposal_data`.
4. **Local quorum check** on initiator’s pending → `commit_up_to` highest quorum term; first global commit → metrics.
5. Packet: `flags_bitmap` from pending for `current_term` (self-bit forced 1), `last_accepted_term = state.last_accepted`, attach piggyback from previous round if any.

### Phase 2 — CI flood

- `RawMergeProtocol`: end-of-round copy of initiator bytes into participants’ `payload`.
- PHY: fixed slots, Flood/Listen/Sleep as in [simulator.md](../simulator.md).

### Phase 3 — middleware (participants in Sleep)

For each node that participated (`state == Sleep` after round):

1. If `last_accepted_term = Some(L)` → `commit_up_to(L)`; metrics on first global commit.
2. Update `highest_seen_term`.
3. If non-empty `proposal_data` and term not known → push pending with received bitmap.
4. `merge_votes_up_to(current_term, flags_bitmap)` then OR **self vote** into all pending ≤ current_term.
5. If `piggyback_term/data` present → insert as pending with full-true bitmap (helps recovery).
6. If packet `nack_term > 0` and we have that term in log/pending → schedule **piggyback** for next initiator build.

---

## 5. Commit semantics

```
Majority votes on term T (in some node's view)
  → that node may set last_accepted = T when it initiates
  → flood carries last_accepted_term
  → all receivers commit_up_to(T)  # T and all prior
```

Pipeline: proposal T and votes for older terms travel in later RR floods (piggybacked in cumulative bitmaps / later packets).

---

## 6. Recovery

| Mechanism | When |
|-----------|------|
| **Gap NACK** | Initiator missing term in sequence |
| **Piggyback** | Peer holds NACK’d term data → attach on next flood |
| **Drain rounds** | After all proposals generated, empty-data floods continue so votes/commits/NACKs finish |

**Graceful stop:** when all terms are in `globally_committed`, allow ~`5 * diameter` extra rounds for stragglers, then exit (avoids infinite hang under loss).

---

## 7. Metrics meaning

- **Committed** = first time term enters global metrics (quorum path).
- Latency = commit slot − `proposal_starts[term]`.
- Recovery counters: `nacks_sent`, `piggybacks_sent`.

---

## 8. Example timeline (N=5, RR)

| Round | Initiator | Typical content |
|-------|-----------|-----------------|
| 0 | 0 | Propose term 0, bitmap [1,0,0,0,0] |
| 1 | 1 | Propose term 1; votes may cover term 0 |
| … | … | Pipeline overlap |
| k | * | `last_accepted_term` advances as quorums form |

Under loss: NACK + piggyback fill holes without restarting the whole log.
