//! Totally Ordered Multicast (TOM) over CI Pipeline.
//!
//! - Round-robin = distributed sequencer (no central sequencer).
//! - Term/Sequence ID increases only when a node publishes.
//! - In-order delivery: deliver term only if == last_delivered+1; else buffer + NACK.
//! - Gap recovery: piggyback missing term data on later floods.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// CI flood packet for TOM.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TomPacket {
    /// Sequence ID of the primary payload this round (or last known if idle).
    pub current_term: u64,
    /// True if this round carries a new application message for current_term.
    pub has_message: bool,
    /// Application payload for current_term (empty if idle / no publish).
    pub message_data: Vec<u8>,
    /// Sender (round-robin initiator).
    pub sender: usize,
    /// First missing term at sender (0 = none).
    pub nack_term: u64,
    /// Piggybacked recovery of a missing term.
    pub piggyback_term: Option<u64>,
    pub piggyback_data: Vec<u8>,
}

/// Per-node TOM middleware state.
#[derive(Debug, Clone)]
pub struct NodeTomState {
    /// Last term delivered to the application layer.
    pub last_delivered: Option<u64>,
    /// Highest term observed on the wire (not necessarily delivered).
    pub highest_seen: Option<u64>,
    /// Store of all known messages (for delivery + piggyback help).
    pub store: BTreeMap<u64, Vec<u8>>,
    /// Delivered log: (term, data) in order.
    pub delivered: Vec<(u64, Vec<u8>)>,
}

impl Default for NodeTomState {
    fn default() -> Self {
        Self::new()
    }
}

impl NodeTomState {
    pub fn new() -> Self {
        Self {
            last_delivered: None,
            highest_seen: None,
            store: BTreeMap::new(),
            delivered: Vec::new(),
        }
    }

    pub fn next_expected(&self) -> u64 {
        self.last_delivered.map(|t| t + 1).unwrap_or(0)
    }

    /// Insert message into store. Returns true if new.
    pub fn insert_message(&mut self, term: u64, data: Vec<u8>) -> bool {
        if self.store.contains_key(&term) {
            return false;
        }
        self.store.insert(term, data);
        match self.highest_seen {
            Some(h) if h >= term => {}
            _ => self.highest_seen = Some(term),
        }
        true
    }

    /// Deliver all consecutive terms from next_expected. Returns count delivered.
    pub fn try_deliver_in_order(&mut self) -> usize {
        let mut count = 0;
        loop {
            let next = self.next_expected();
            if let Some(data) = self.store.get(&next).cloned() {
                self.delivered.push((next, data));
                self.last_delivered = Some(next);
                count += 1;
            } else {
                break;
            }
        }
        count
    }

    /// First gap relative to highest_seen (or next_expected).
    pub fn detect_gap(&self) -> Option<u64> {
        let up_to = self.highest_seen?;
        let start = self.next_expected();
        (start..=up_to).find(|t| !self.store.contains_key(t))
    }

    pub fn get_message(&self, term: u64) -> Option<&Vec<u8>> {
        self.store.get(&term)
    }
}

pub fn serialize_packet(pkt: &TomPacket) -> Vec<u8> {
    serde_json::to_vec(pkt).unwrap_or_default()
}

pub fn deserialize_packet(data: &[u8]) -> Option<TomPacket> {
    serde_json::from_slice(data).ok()
}
