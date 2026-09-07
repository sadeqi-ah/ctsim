//! Non-blocking Two-Phase Commit (2PC) over CI Pipeline.
//!
//! Features implemented:
//! 1. Bounded Voting: A proposal has exactly one full pipeline cycle (N slots) to gather votes.
//! 2. Unanimous Commit / Fast Abort: Requires All-1s in the bitmap to commit. Any 0 after N rounds = Abort.
//! 3. Non-blocking Execution: Due to overhearing, if the coordinator fails, any node that sees the
//!    All-1s bitmap can implicitly take over and declare the transaction Committed.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TwoPcState {
    Prepare,
    Committed,
    Aborted,
}

/// The unified CI packet for Pipeline 2PC
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TwoPcPacket {
    pub transaction_id: u64,
    pub state: TwoPcState,
    pub flags_bitmap: Vec<bool>,
    /// Optional abort flag. If any node sets this to true, the transaction is fast-aborted.
    pub abort_flag: bool,
    /// NACK field: used if a node misses the final commit/abort decision for an older transaction.
    pub nack_tx_id: u64,

    // Payload
    pub transaction_data: Vec<u8>,
    pub sender: usize,

    // Piggybacked recovery data for NACKs
    pub piggyback_tx: Option<u64>,
    pub piggyback_state: Option<TwoPcState>,
}

#[derive(Debug, Clone)]
pub struct NodeTwoPcState {
    pub num_nodes: usize,
    /// Highest transaction ID seen.
    pub highest_seen_tx: Option<u64>,
    /// Log of finalized transactions: tx_id -> State (Committed/Aborted)
    pub log: Vec<(u64, TwoPcState)>,
    /// Currently active/pending transactions.
    pub pending: Vec<PendingTx>,
}

#[derive(Debug, Clone)]
pub struct PendingTx {
    pub tx_id: u64,
    pub data: Vec<u8>,
    pub bitmap: Vec<bool>,
    pub abort_flag: bool,
    /// Slot (or round index) when this TX was first proposed.
    /// Used for bounded voting (max lifespan = num_nodes rounds).
    pub start_round: u64,
}

impl NodeTwoPcState {
    pub fn new(num_nodes: usize) -> Self {
        Self {
            num_nodes,
            highest_seen_tx: None,
            log: Vec::new(),
            pending: Vec::new(),
        }
    }

    /// Check if a transaction has reached Unanimity (All 1s).
    pub fn check_unanimity(&self, tx_id: u64) -> bool {
        if let Some(p) = self.pending.iter().find(|p| p.tx_id == tx_id) {
            // Unanimity fails if anyone explicitly aborted OR if any bit is 0
            if p.abort_flag {
                return false;
            }
            return p.bitmap.iter().all(|&v| v);
        }
        false
    }

    /// Check if explicitly aborted (so we can fast-abort before bounded time ends)
    pub fn check_explicit_abort(&self, tx_id: u64) -> bool {
        if let Some(p) = self.pending.iter().find(|p| p.tx_id == tx_id) {
            return p.abort_flag;
        }
        false
    }

    /// Merge incoming votes cumulatively for all pending TXs <= the given tx_id.
    pub fn merge_votes_up_to(&mut self, tx_id: u64, incoming_bitmap: &[bool], abort_flag: bool) {
        for p in &mut self.pending {
            if p.tx_id <= tx_id {
                for (j, &v) in incoming_bitmap.iter().enumerate() {
                    if v {
                        p.bitmap[j] = true;
                    }
                }
                if abort_flag && p.tx_id == tx_id {
                    p.abort_flag = true;
                }
            }
        }
    }

    /// Finalize a transaction to the log.
    pub fn finalize_tx(&mut self, tx_id: u64, state: TwoPcState) {
        if self.log.iter().any(|(t, _)| *t == tx_id) {
            return;
        }
        if let Some(pos) = self.pending.iter().position(|p| p.tx_id == tx_id) {
            self.pending.remove(pos);
        }
        self.log.push((tx_id, state));
    }

    pub fn detect_gap(&self, current_tx: u64) -> Option<u64> {
        // Find the lowest missing TX from 0 to current_tx
        for t in 0..current_tx {
            let in_log = self.log.iter().any(|(lt, _)| *lt == t);
            let in_pending = self.pending.iter().any(|p| p.tx_id == t);
            if !in_log && !in_pending {
                return Some(t);
            }
        }
        None
    }
}

/// Serialize a TwoPcPacket to bytes.
///
/// NOT a wire format. This JSON encoding is an internal carrier for protocol
/// state: the simulator is a slot-level model, and the byte length produced here
/// is consumed by no metric, no energy term and no timing term (there is no
/// `payload.len()` anywhere in the crate). The packet length behind every
/// millisecond conversion is instead a *specified* bit-packed encoding,
/// `L_wire(N) = ceil(N/8) + 22` octets — see `docs/validation/t_slot.md` §5 and
/// the guard `tests/validation.rs::specified_wire_packet_fits_in_one_ll_data_pdu`.
/// Do not quote `serialize_packet(..).len()` as a packet size in the manuscript.
pub fn serialize_packet(pkt: &TwoPcPacket) -> Vec<u8> {
    serde_json::to_vec(pkt).unwrap_or_default()
}

/// Deserialize a TwoPcPacket from bytes.
pub fn deserialize_packet(data: &[u8]) -> Option<TwoPcPacket> {
    serde_json::from_slice(data).ok()
}
