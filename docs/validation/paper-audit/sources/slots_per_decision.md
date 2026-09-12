Formula: slots_per_decision = total_slots / committed_decisions (computed per seed, then mean taken)
Configs: scalability sweep at N=27, random topology, loss_rate=0.05, 15 seeds
CI min: 4.699, CI max: 5.971
CE min: 4.676, CE max: 24.335
Proposal sharing share for 2PC: 4.57%
  Numerator: Amortized energy per decision across 15 seeds (110.43314687145975)
  Denominator: Cumulative energy per decision from sweep_summary.csv (115.72304582210242)
  Share = 1 - (Numerator / Denominator)
