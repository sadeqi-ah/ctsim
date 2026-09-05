//! CI Pipeline Non-blocking 2PC — implements [`CiProtocol`].

use crate::config::SimConfig;
use crate::metrics::MetricsCollector;
use crate::network::NetworkGraph;
use crate::protocol::two_pc_pipeline::{
    deserialize_packet, serialize_packet, NodeTwoPcState, PendingTx, TwoPcPacket, TwoPcState,
};
use crate::sim::pipeline::{run_ci_pipeline, CiPipelineCore, CiProtocol};
use rand::Rng;
use std::collections::{HashMap, HashSet};

pub struct TwoPcPipelineSim {
    pub metrics: MetricsCollector,
    core: Option<CiPipelineCore>,
    num_txs: usize,
    abort_probability: f64,
}

impl TwoPcPipelineSim {
    pub fn new(config: SimConfig, graph: NetworkGraph) -> Self {
        let num_txs = config.num_proposals;
        let abort_probability = config.abort_probability;
        Self {
            metrics: MetricsCollector::new(),
            core: Some(CiPipelineCore::new(config, graph)),
            num_txs,
            abort_probability,
        }
    }

    pub fn run(&mut self) -> (MetricsCollector, u64, u64, u64) {
        let core = self.core.take().expect("already run");
        let n = core.num_nodes();
        let proto = TwoPcCi {
            states: vec![NodeTwoPcState::new(n); n],
            tx_counter: 0,
            txs_generated: 0,
            num_txs: self.num_txs,
            abort_probability: self.abort_probability,
            tx_starts: HashMap::new(),
            piggyback_tx: None,
            piggyback_state: None,
            stop: false,
            recorded: std::collections::HashSet::new(),
        };
        let core = run_ci_pipeline(proto, core);
        self.metrics = core.metrics.clone();
        let l = core.nodes.iter().map(|nd| nd.slots_listen).sum();
        let f = core.nodes.iter().map(|nd| nd.slots_flood).sum();
        let s = core.nodes.iter().map(|nd| nd.slots_sleep).sum();
        (core.metrics, l, f, s)
    }
}

struct TwoPcCi {
    states: Vec<NodeTwoPcState>,
    tx_counter: u64,
    txs_generated: usize,
    num_txs: usize,
    abort_probability: f64,
    /// Slot at which each tx was first floated by its originating initiator.
    /// Same pattern as `paxos_pipeline::PaxosCi::proposal_starts` and
    /// `tom_pipeline::TomCi::msg_starts`: recorded directly, never derived from
    /// a round index times a round length.
    tx_starts: HashMap<u64, u64>,
    piggyback_tx: Option<u64>,
    piggyback_state: Option<TwoPcState>,
    stop: bool,
    recorded: HashSet<u64>,
}

impl CiProtocol for TwoPcCi {
    fn name(&self) -> &str {
        "Non-blocking 2PC Pipeline"
    }

    fn on_start(&mut self, core: &mut CiPipelineCore) {
        if !core.config.quiet {
            println!(
                "Starting Non-blocking 2PC Pipeline (CI mode): {} nodes, {} TXs, diameter={}",
                core.num_nodes(),
                self.num_txs,
                core.graph.diameter()
            );
        }
    }

    fn prepare_round(&mut self, core: &mut CiPipelineCore) {
        let initiator = core.initiator();
        let num_nodes = core.num_nodes();
        let round_num = core.round_num;
        let state = &mut self.states[initiator];

        let nack_tx_id = state.detect_gap(self.tx_counter).unwrap_or(0);
        if nack_tx_id > 0 {
            core.metrics.nacks_sent += 1;
        }

        let (current_tx, tx_data, tx_state) = if self.txs_generated < self.num_txs {
            let d = format!("tx{}", self.tx_counter).into_bytes();
            let t = self.tx_counter;
            let mut bitmap = vec![false; num_nodes];
            let mut abort_flag = false;
            if core.rng.gen::<f64>() < self.abort_probability {
                abort_flag = true;
            } else {
                bitmap[initiator] = true;
            }
            state.pending.push(PendingTx {
                tx_id: t,
                data: d.clone(),
                bitmap: bitmap.clone(),
                abort_flag,
                start_round: round_num,
            });
            self.tx_counter += 1;
            self.txs_generated += 1;
            self.tx_starts.insert(t, core.current_slot);
            (t, d, TwoPcState::Prepare)
        } else {
            (
                self.tx_counter.saturating_sub(1),
                Vec::new(),
                TwoPcState::Prepare,
            )
        };

        let mut newly_resolved = Vec::new();
        for p in &state.pending {
            if round_num >= p.start_round + (num_nodes as u64) {
                if state.check_unanimity(p.tx_id) {
                    newly_resolved.push((p.tx_id, TwoPcState::Committed));
                } else {
                    newly_resolved.push((p.tx_id, TwoPcState::Aborted));
                }
            }
        }
        for (t, s) in newly_resolved {
            state.finalize_tx(t, s);
            if self.recorded.insert(t) {
                let outcome = match s {
                    TwoPcState::Committed => crate::protocol::ProposalOutcome::Committed,
                    TwoPcState::Aborted => crate::protocol::ProposalOutcome::Aborted,
                    _ => unreachable!(),
                };
                let start_slot = self.tx_starts.get(&t).copied().unwrap_or(0);
                core.metrics
                    .record_proposal(t as usize, start_slot, core.current_slot, outcome);
            }
        }

        let mut flags_bitmap = vec![false; num_nodes];
        let mut abort_flag = false;
        if let Some(p) = state.pending.iter().find(|p| p.tx_id == current_tx) {
            flags_bitmap = p.bitmap.clone();
            abort_flag = p.abort_flag;
        }
        if !abort_flag {
            flags_bitmap[initiator] = true;
        }

        let pkt = TwoPcPacket {
            transaction_id: current_tx,
            state: tx_state,
            flags_bitmap,
            abort_flag,
            nack_tx_id,
            sender: initiator,
            transaction_data: tx_data,
            piggyback_tx: self.piggyback_tx,
            piggyback_state: self.piggyback_state,
        };
        core.nodes[initiator].payload = serialize_packet(&pkt);
    }

    fn process_round(&mut self, core: &mut CiPipelineCore) {
        let num_nodes = core.num_nodes();
        let num_txs = self.num_txs;
        let round_num = core.round_num;
        self.piggyback_tx = None;
        self.piggyback_state = None;

        let mut all_resolved = true;

        for i in 0..num_nodes {
            if !core.participated(i) {
                if self.states[i].log.len() < num_txs {
                    all_resolved = false;
                }
                continue;
            }

            let state = &mut self.states[i];
            let Some(received_pkt) = deserialize_packet(&core.nodes[i].payload) else {
                all_resolved = false;
                continue;
            };

            if !received_pkt.transaction_data.is_empty() {
                let tx_id = received_pkt.transaction_id;
                if !state.pending.iter().any(|p| p.tx_id == tx_id)
                    && !state.log.iter().any(|(lt, _)| *lt == tx_id)
                {
                    let mut bitmap = received_pkt.flags_bitmap.clone();
                    let mut abort_flag = received_pkt.abort_flag;
                    if core.rng.gen::<f64>() < self.abort_probability {
                        abort_flag = true;
                    } else {
                        bitmap[i] = true;
                    }
                    state.pending.push(PendingTx {
                        tx_id,
                        data: received_pkt.transaction_data.clone(),
                        bitmap,
                        abort_flag,
                        start_round: round_num,
                    });
                }
            }

            state.merge_votes_up_to(
                received_pkt.transaction_id,
                &received_pkt.flags_bitmap,
                received_pkt.abort_flag,
            );
            if let Some(p) = state
                .pending
                .iter()
                .find(|p| p.tx_id == received_pkt.transaction_id)
            {
                if !p.abort_flag {
                    let mut our_vote = vec![false; num_nodes];
                    our_vote[i] = true;
                    state.merge_votes_up_to(received_pkt.transaction_id, &our_vote, false);
                }
            }

            let mut fast_aborts = Vec::new();
            for p in &state.pending {
                if p.abort_flag {
                    fast_aborts.push(p.tx_id);
                }
            }
            for t in fast_aborts {
                state.finalize_tx(t, TwoPcState::Aborted);
                if self.recorded.insert(t) {
                    // Same start-slot source as the commit path above: the slot the
                    // tx was floated, not a hand-written 0.
                    let start_slot = self.tx_starts.get(&t).copied().unwrap_or(0);
                    core.metrics.record_proposal(
                        t as usize,
                        start_slot,
                        core.current_slot,
                        crate::protocol::ProposalOutcome::Aborted,
                    );
                }
            }

            if let (Some(ptx), Some(pst)) =
                (received_pkt.piggyback_tx, received_pkt.piggyback_state)
            {
                if !state.log.iter().any(|(lt, _)| *lt == ptx) {
                    state.finalize_tx(ptx, pst);
                }
            }

            if received_pkt.nack_tx_id > 0 {
                if let Some((_, log_state)) = state
                    .log
                    .iter()
                    .find(|(t, _)| *t == received_pkt.nack_tx_id)
                {
                    self.piggyback_tx = Some(received_pkt.nack_tx_id);
                    self.piggyback_state = Some(*log_state);
                    core.metrics.piggybacks_sent += 1;
                }
            }

            let mut newly_resolved_rx = Vec::new();
            for p in &state.pending {
                if round_num >= p.start_round + (num_nodes as u64) {
                    if state.check_unanimity(p.tx_id) {
                        newly_resolved_rx.push((p.tx_id, TwoPcState::Committed));
                    } else {
                        newly_resolved_rx.push((p.tx_id, TwoPcState::Aborted));
                    }
                }
            }
            for (t, s) in newly_resolved_rx {
                state.finalize_tx(t, s);
            }

            if state.log.len() < num_txs {
                all_resolved = false;
            }
        }

        // Unified progress: how many txs EVERY node has finalized.
        let min_done = self.states.iter().map(|s| s.log.len()).min().unwrap_or(0);
        for i in 0..num_nodes {
            core.nodes[i].goal_reached = self.states[i].log.len() >= num_txs;
            core.nodes[i].progress_count = min_done;
        }

        if all_resolved && self.txs_generated >= num_txs {
            if !core.config.quiet {
                println!(
                    "All nodes successfully finalized {} transactions at round {}",
                    num_txs, core.round_num
                );
            }
            self.stop = true;
        } else if core.round_num as usize > num_txs + 1000 {
            if !core.config.quiet {
                println!("Timeout: infinite idle rounds.");
            }
            self.stop = true;
        }
    }

    fn should_stop(&self, _core: &CiPipelineCore) -> bool {
        self.stop
    }
}
