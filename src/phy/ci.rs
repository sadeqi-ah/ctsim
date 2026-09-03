//! CI (Constructive Interference) engine.
//!
//! Rounds are time-bound up to `round_slots`, but **end early** once the flood
//! wave finishes (no node remains in Flood). That removes long all-Sleep padding
//! after the wave has already completed.
//!
//! Slot rule: state fixed at slot start → action from that state → transitions for next slot.
//!
//! Pipelines use [`flood_identical_round`]: one identical payload for the whole round
//! (no mid-round Protocol merge). Middleware runs only after the flood returns.

use crate::config::CiConfig;
use crate::event::{NodeId, Slot};
use crate::metrics::MetricsCollector;
use crate::network::NetworkGraph;
use crate::node::{Node, NodeState};
use rand::Rng;
use rand_chacha::ChaCha8Rng;

/// Run one CI identical-payload flood round.
///
/// - Reads flood bytes from `nodes[initiator].payload` at round start.
/// - Successful participants end in `Sleep` with **that same** payload copied in.
/// - Ends at `min(round_end, first slot where no node is Flooding)` after at least
///   one transition step (so initiator always floods `flood_repeats` times).
///
/// Returns the slot index after the round ends.
#[allow(clippy::too_many_arguments)]
pub fn flood_identical_round(
    round_start: Slot,
    initiator: NodeId,
    nodes: &mut [Node],
    graph: &NetworkGraph,
    ci_cfg: &CiConfig,
    rng: &mut ChaCha8Rng,
    loss_rate: f64,
    metrics: &mut MetricsCollector,
    next_snapshot: &mut u64,
    snapshot_interval: u64,
) -> Slot {
    let round_slots = ci_cfg.round_slots.unwrap_or_else(|| {
        std::cmp::max(
            3,
            ((graph.diameter() + 2) as u64) * (ci_cfg.flood_repeats as u64),
        )
    });

    let round_end = round_start + round_slots;

    for node in nodes.iter_mut() {
        node.reset_round();
    }

    let round_payload = nodes[initiator].payload.clone();

    nodes[initiator].state = NodeState::Flood;
    nodes[initiator].flood_remaining = ci_cfg.flood_repeats;

    let mut slot = round_start;
    while slot < round_end {
        // 1. Tick + snapshot from CURRENT state (start of slot).
        for node in nodes.iter_mut() {
            node.tick();
        }

        while *next_snapshot <= slot {
            metrics.take_snapshot(*next_snapshot, nodes);
            *next_snapshot += snapshot_interval;
        }

        // 2. Action: TX from Flood; RX marks for Listen neighbors.
        let mut received_this_slot = vec![false; nodes.len()];
        let mut any_flood = false;
        for i in 0..nodes.len() {
            if nodes[i].state == NodeState::Flood {
                any_flood = true;
                let src = nodes[i].id;
                for nbr in graph.neighbors(src) {
                    if nodes[nbr].state == NodeState::Listen
                        && (loss_rate == 0.0 || rng.gen::<f64>() >= loss_rate)
                    {
                        received_this_slot[nbr] = true;
                    }
                }
            }
        }

        // Early end: wave already finished before this slot's action (all Sleep/Listen,
        // nobody Flooding). Skip burning slots on all-Sleep padding.
        // Exception: slot == round_start always has initiator Flood after setup.
        if !any_flood && slot > round_start {
            break;
        }

        // 3. Transitions for NEXT slot only.
        for i in 0..nodes.len() {
            if nodes[i].state == NodeState::Flood {
                nodes[i].flood_remaining -= 1;
                if nodes[i].flood_remaining == 0 {
                    nodes[i].state = NodeState::Sleep;
                }
            } else if nodes[i].state == NodeState::Listen && received_this_slot[i] {
                nodes[i].state = NodeState::Flood;
                nodes[i].flood_remaining = ci_cfg.flood_repeats;
            }
        }

        // After transitions: if nobody will Flood next slot, end after this slot
        // (last flooders just went to Sleep; no padding).
        let next_any_flood = nodes.iter().any(|n| n.state == NodeState::Flood);
        slot += 1;
        if !next_any_flood {
            // Snapshot the all-Sleep (or Listen-stuck) state at `slot` once if due,
            // then stop — do not run empty padding slots until round_end.
            while *next_snapshot <= slot && slot < round_end {
                // tick already done for previous; for end-of-wave we don't invent extra ticks
                metrics.take_snapshot(*next_snapshot, nodes);
                *next_snapshot += snapshot_interval;
            }
            break;
        }
    }

    // Deliver identical flood bytes to participants that completed (Sleep).
    // Initiator already holds the source payload.
    for node in nodes.iter_mut() {
        if node.state == NodeState::Sleep && node.id != initiator {
            node.payload = round_payload.clone();
        }
    }

    // If we broke early, `slot` is the first free slot; if we ran to deadline, slot==round_end.
    slot.min(round_end)
}
