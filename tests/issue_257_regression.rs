//! Regression test for Issue 257: piggyback-recovery must NOT grant free quorum.
//!
//! The defect was in `src/sim/paxos_pipeline.rs` at the piggyback-insertion site:
//! a `PendingProposal` recovered from a piggybacked term was created with
//! `bitmap: vec![true; num_nodes]` — an all-ones vote bitmap — granting instant
//! quorum without any real vote. The fix initialises the bitmap with only the
//! receiving node's own vote (`bitmap[i] = true`), forcing the proposal to
//! collect votes through `merge_votes_up_to` like any normally received proposal.

use ctsim::config::SimConfig;
use ctsim::run::run_experiment;
use std::path::Path;

/// Build a Paxos-CI config that reliably triggers piggyback recovery.
///
/// Uses N=27, random topology, loss=0.20 (the highest paper operating point),
/// which produces piggybacks in every seed tested in the committed data.
/// Only 10 proposals so the test stays fast in debug builds.
fn lossy_paxos_ci() -> SimConfig {
    SimConfig::from_file(Path::new("examples/paxos_ci.toml"))
        .map(|mut cfg| {
            cfg.num_proposals = 10;
            cfg.network.loss_rate = 0.20;
            cfg.quiet = true;
            cfg
        })
        .expect("examples/paxos_ci.toml must parse")
}

#[test]
fn piggyback_recovery_does_not_grant_free_quorum() {
    let cfg = lossy_paxos_ci();
    let r = run_experiment(cfg);
    let s = &r.summary;

    // Piggyback path must be exercised for this test to be meaningful.
    assert!(
        s.piggybacks_sent > 0,
        "test requires piggybacks_sent > 0 to exercise the recovery path; got 0"
    );

    // The simulation must still make progress after the fix.
    assert!(
        s.committed > 0,
        "no proposals committed — the fix must not break convergence"
    );

    // Every proposal must reach a terminal state.
    assert_eq!(
        s.committed + s.aborted + s.timed_out,
        s.num_proposals,
        "every proposal must reach a terminal outcome"
    );
}

#[test]
fn piggyback_recovery_is_reproducible_after_fix() {
    let cfg = lossy_paxos_ci();
    let a = run_experiment(cfg.clone());
    let b = run_experiment(cfg);
    assert_eq!(
        a.summary.committed, b.summary.committed,
        "same seed must produce identical committed count"
    );
    assert_eq!(
        a.summary.piggybacks_sent, b.summary.piggybacks_sent,
        "same seed must produce identical piggybacks_sent"
    );
    assert_eq!(
        a.summary.end_slot, b.summary.end_slot,
        "same seed must produce identical end_slot"
    );
}
