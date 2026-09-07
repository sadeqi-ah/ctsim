//! Paxos over CI Pipeline — pipelined consensus with round-robin flooding.
//!
//! Packet structure (unified flood payload):
//!
//! ```text
//! ┌─────────── Header ───────────┐  ┌───── Payload ──────────────┐
//! │ current_term: u64            │  │ proposal_data: Vec<u8>     │
//! │ last_accepted_term: Option   │  │ piggyback_term: Option<u64>│
//! │ flags_bitmap: Vec<bool>      │  │ piggyback_data: Vec<u8>    │
//! │ nack_term: u64 (0=none)      │  └────────────────────────────┘
//! └──────────────────────────────┘
//! ```
//!
//! No explicit Phase field. Commit is implicit via last_accepted_term:
//!   - Initiator sets current_term=T, broadcasts proposal_data
//!   - Other nodes set their bit in flags_bitmap (vote)
//!   - When initiator's turn comes back, it checks bitmap for quorum
//!   - If majority reached: last_accepted_term = T in next packet
//!   - All nodes seeing last_accepted_term=T know T and everything before is committed

use serde::{Deserialize, Serialize};

/// The unified CI packet: header + payload. No phase field.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaxosPacket {
    // ── Header ─────────────────────────────────────────
    /// Term of the NEW proposal being broadcast this round.
    pub current_term: u64,
    /// Highest term known to be globally accepted (quorum reached).
    /// Implicitly commits this and all prior terms.
    pub last_accepted_term: Option<u64>,
    /// Bitmap: bit i = 1 means node i has seen & voted for current_term.
    pub flags_bitmap: Vec<bool>,
    /// NACK: if > 0, sender is missing data for this term.
    pub nack_term: u64,
    /// The sender's node ID.
    pub sender: usize,

    // ── Payload ────────────────────────────────────────
    /// Proposal data for current_term.
    pub proposal_data: Vec<u8>,
    /// Piggybacked recovery: term of NACK'd proposal being retransmitted.
    pub piggyback_term: Option<u64>,
    /// Piggybacked recovery data.
    pub piggyback_data: Vec<u8>,
}

/// Per-node local state for the Paxos pipeline.
#[derive(Debug, Clone)]
pub struct NodePaxosState {
    /// Highest term this node has seen.
    pub highest_seen_term: Option<u64>,
    /// Highest term this node knows is globally accepted.
    pub last_accepted: Option<u64>,
    /// Log of committed proposals: term → data.
    pub log: Vec<(u64, Vec<u8>)>,
    /// Pending proposals awaiting quorum: term → (data, bitmap).
    pub pending: Vec<PendingProposal>,
}

#[derive(Debug, Clone)]
pub struct PendingProposal {
    pub term: u64,
    pub data: Vec<u8>,
    pub bitmap: Vec<bool>,
}

impl Default for NodePaxosState {
    fn default() -> Self {
        Self::new()
    }
}

impl NodePaxosState {
    pub fn new() -> Self {
        Self {
            highest_seen_term: None,
            last_accepted: None,
            log: Vec::new(),
            pending: Vec::new(),
        }
    }

    /// Merge a received bitmap into all pending proposals <= the given term.
    pub fn merge_votes_up_to(&mut self, up_to_term: u64, bitmap: &[bool]) {
        for p in &mut self.pending {
            if p.term <= up_to_term {
                for (j, &v) in bitmap.iter().enumerate() {
                    if v {
                        p.bitmap[j] = true;
                    }
                }
            }
        }
    }

    /// Check if a pending proposal has reached majority quorum.
    pub fn check_quorum(&self, term: u64) -> bool {
        for p in &self.pending {
            if p.term == term {
                let votes: usize = p.bitmap.iter().filter(|&&b| b).count();
                let majority = p.bitmap.len() / 2 + 1;
                return votes >= majority;
            }
        }
        false
    }

    /// Move a term from pending to committed log.
    pub fn commit_term(&mut self, term: u64) {
        if self.log.iter().any(|(t, _)| *t == term) {
            return; // already committed
        }
        if let Some(pos) = self.pending.iter().position(|p| p.term == term) {
            let p = self.pending.remove(pos);
            self.log.push((term, p.data));
        }
        // Update last_accepted
        match self.last_accepted {
            Some(la) if la >= term => {}
            _ => self.last_accepted = Some(term),
        }
    }

    /// Commit all terms up to and including `up_to`. Returns a list of newly committed terms.
    pub fn commit_up_to(&mut self, up_to: u64) -> Vec<u64> {
        let mut newly_committed = Vec::new();
        for t in 0..=up_to {
            if !self.log.iter().any(|(lt, _)| *lt == t) {
                self.commit_term(t);
                newly_committed.push(t);
            }
        }
        newly_committed
    }

    /// Detect gap: first term missing from both log and pending.
    pub fn detect_gap(&self, up_to_term: u64) -> Option<u64> {
        let start = self.last_accepted.map(|t| t + 1).unwrap_or(0);
        for t in start..up_to_term {
            let in_log = self.log.iter().any(|(lt, _)| *lt == t);
            let in_pending = self.pending.iter().any(|p| p.term == t);
            if !in_log && !in_pending {
                return Some(t);
            }
        }
        None
    }
}

/// Serialize a PaxosPacket to bytes.
///
/// NOT a wire format — identical caveat to the 2PC and TOM serialisers. This JSON
/// encoding is an internal carrier for protocol state; its byte length feeds no
/// metric, no energy term and no timing term in this slot-level model. Millisecond
/// conversions use the specified bit-packed encoding of `docs/validation/t_slot.md`
/// §5 (`L_wire(N) = ceil(N/8) + 22` octets for the 2PC packet; the Paxos header
/// differs in fields but is bounded by the same 251-octet LE Data PDU budget), and
/// the guard test is
/// `tests/validation.rs::specified_wire_packet_fits_in_one_ll_data_pdu`.
pub fn serialize_packet(pkt: &PaxosPacket) -> Vec<u8> {
    serde_json::to_vec(pkt).unwrap_or_default()
}

/// Deserialize a PaxosPacket from bytes.
pub fn deserialize_packet(data: &[u8]) -> Option<PaxosPacket> {
    serde_json::from_slice(data).ok()
}
