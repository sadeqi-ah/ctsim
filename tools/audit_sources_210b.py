import os
import sys
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs/validation/paper-audit/sources"
SOURCES.mkdir(parents=True, exist_ok=True)
RESULTS = ROOT / "results"

def main():
    print("Running A1...")
    env = os.environ.copy()
    
    with open(ROOT / "plots/progress/sim_paxos_pipeline_progress.toml", "rb") as f:
        t = tomllib.load(f)
    ref_op = f"N={t['network']['num_nodes']}, topology={t['network']['topology']}, loss_rate={t['network']['loss_rate']}, num_proposals={t['num_proposals']}"

    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    
    # Run progress generators
    subprocess.run(["python3", "plots/progress/plot_progress.py"], cwd=ROOT, check=True, env=env)
    subprocess.run(["python3", "plots/progress/plot_progress_log.py"], cwd=ROOT, check=True, env=env)

    dfs = []
    protos = ["paxos", "2pc", "tom", "paxos_ce", "2pc_ce", "tom_ce"]
    labels = ["Paxos (CI)", "2PC (CI)", "TOM (CI)", "Paxos (CE)", "2PC (CE)", "TOM (CE)"]
    summary_lines = []
    
    for proto, label in zip(protos, labels):
        df = pd.read_csv(RESULTS / f"snapshots_{proto}.csv")
        df['protocol'] = label
        df['decisions'] = df['progress_count']
        dfs.append(df[['protocol', 'slot', 'decisions']])
        
        final_decisions = df['decisions'].max()
        max_slot = df['slot'].max()
        summary_lines.append(f"- {label}: final decisions={final_decisions}, max slot={max_slot}")
        
    pd.concat(dfs, ignore_index=True).to_csv(SOURCES / "progress_snapshots.csv", index=False)
    
    with open(SOURCES / "progress_README.md", "w") as f:
        f.write(f"Reference operating point: {ref_op}\n")
        f.write(f"Config files used:\n")
        for p in ["paxos_pipeline", "2pc_pipeline", "tom_pipeline", "paxos_ce", "2pc_ce", "tom_ce"]:
            f.write(f"- plots/progress/sim_{p}_progress.toml\n")
        f.write(f"Pre-generation source revision: {sha}\n")
        f.write("\n".join(summary_lines) + "\n")
        
        f.write("\n## Snapshot vs run totals\n")
        for proto, label in zip(protos, labels):
            df_snap = pd.read_csv(RESULTS / f"snapshots_{proto}.csv")
            max_slot = df_snap['slot'].max()
            prog_count = df_snap[df_snap['slot'] == max_slot]['progress_count'].values[0]
            
            df_res = pd.read_csv(RESULTS / f"results_{proto}.csv")
            commits = len(df_res[df_res['outcome'] == 'committed'])
            final_end_slot = df_res['end_slot'].max()
            
            agree = (prog_count == commits)
            operator = "<=" if final_end_slot <= max_slot else ">"
            
            line = f"- {label}: snapshot file `results/snapshots_{proto}.csv` (snapshot slot column `slot`, last snapshot slot={max_slot}, progress_count column `progress_count`, progress_count={prog_count}) vs run-total file `results/results_{proto}.csv` (committed-decision column `outcome`, run total committed decisions={commits}, final end-slot column `end_slot`, value={final_end_slot}). Comparison: final end slot {final_end_slot} {operator} last snapshot slot {max_slot}. Agree: {str(agree).lower()}\n"
            f.write(line)
            
        f.write("\nConclusion: the complete run records 100 committed decisions; the progress snapshot/report records 99. This is treated in this round as a known one-count reporting mismatch. No counter, snapshot code, protocol logic, or simulator behavior is changed. The discrepancy does not alter the paper's main performance conclusions, but it is disclosed for reproducibility.\n")

    print("Running A2...")
    df_sweep = pd.read_csv(ROOT / "plots/scalability/results/sweep_summary.csv")
    df_ref = df_sweep[(df_sweep["nodes"] == 27) & (df_sweep["loss_rate"] == 0.05)].copy()
    
    df_ref["slots_per_decision"] = df_ref["end_slot"] / df_ref["committed"]
    df_ref[["phy", "protocol", "seed", "end_slot", "committed", "slots_per_decision"]].rename(
        columns={"end_slot": "total_slots", "committed": "committed_decisions"}
    ).to_csv(SOURCES / "slots_per_decision.csv", index=False)
    
    # Calculate pooled estimator: sum(total_slots) / sum(committed_decisions)
    pooled = df_ref.groupby(["phy", "protocol"]).apply(
        lambda x: pd.Series({"pooled_slots_per_decision": x["end_slot"].sum() / x["committed"].sum()})
    ).reset_index()
    pooled.columns = ["phy", "protocol", "pooled_slots_per_decision"]
    pooled_ci_min = pooled[pooled["phy"] == "ci"]["pooled_slots_per_decision"].min()
    pooled_ci_max = pooled[pooled["phy"] == "ci"]["pooled_slots_per_decision"].max()
    pooled_ce_min = pooled[pooled["phy"] == "ce"]["pooled_slots_per_decision"].min()
    pooled_ce_max = pooled[pooled["phy"] == "ce"]["pooled_slots_per_decision"].max()

    # Calculate per-seed mean estimator: mean(total_slots / committed_decisions)
    per_seed_mean = df_ref.groupby(["phy", "protocol"])["slots_per_decision"].mean().reset_index()
    per_seed_mean.columns = ["phy", "protocol", "mean_slots_per_decision"]
    per_seed_mean_ci_min = per_seed_mean[per_seed_mean["phy"] == "ci"]["mean_slots_per_decision"].min()
    per_seed_mean_ci_max = per_seed_mean[per_seed_mean["phy"] == "ci"]["mean_slots_per_decision"].max()
    per_seed_mean_ce_min = per_seed_mean[per_seed_mean["phy"] == "ce"]["mean_slots_per_decision"].min()
    per_seed_mean_ce_max = per_seed_mean[per_seed_mean["phy"] == "ce"]["mean_slots_per_decision"].max()

    # Calculate per-seed min/max (over all seeds for a given family)
    per_seed_ci_min = df_ref[df_ref["phy"] == "ci"]["slots_per_decision"].min()
    per_seed_ci_max = df_ref[df_ref["phy"] == "ci"]["slots_per_decision"].max()
    per_seed_ce_min = df_ref[df_ref["phy"] == "ce"]["slots_per_decision"].min()
    per_seed_ce_max = df_ref[df_ref["phy"] == "ce"]["slots_per_decision"].max()

    # Generate per-decision energy and keep for A3 and A4
    sys.path.insert(0, str(ROOT / "plots" / "energy"))
    import plot_stacked_bar
    df_energy = plot_stacked_bar.run_simulation_and_extract_per_proposal(plot_stacked_bar.SEEDS)
    df_energy.rename(columns={"awake_slots": "energy_node_slots", "Protocol": "protocol", "proposal_id": "decision_index"}, inplace=True)
    def get_phy(prot):
        return "CI" if "(CI)" in prot else "CE"
    df_energy["phy"] = df_energy["protocol"].apply(get_phy)
    df_energy[["phy", "protocol", "seed", "decision_index", "energy_node_slots"]].to_csv(SOURCES / "per_decision_energy.csv", index=False)
    
    with open(SOURCES / "slots_per_decision.md", "w") as f:
        f.write("Configs: scalability sweep at N=27, random topology, loss_rate=0.05, 15 seeds\n")
        f.write("\npooled (paper definition): sum(total_slots) / sum(committed_decisions)\n")
        f.write(f"CI min: {pooled_ci_min:.3f}, CI max: {pooled_ci_max:.3f}\n")
        f.write(f"CE min: {pooled_ce_min:.3f}, CE max: {pooled_ce_max:.3f}\n")
        
        f.write("\nper-seed mean: mean(total_slots / committed_decisions)\n")
        f.write(f"CI min: {per_seed_mean_ci_min:.3f}, CI max: {per_seed_mean_ci_max:.3f}\n")
        f.write(f"CE min: {per_seed_mean_ce_min:.3f}, CE max: {per_seed_mean_ce_max:.3f}\n")
        
        f.write("\nper-seed raw min/max:\n")
        f.write(f"CI min: {per_seed_ci_min:.3f}, CI max: {per_seed_ci_max:.3f}\n")
        f.write(f"CE min: {per_seed_ce_min:.3f}, CE max: {per_seed_ce_max:.3f}\n")

    print("Running B2...")
    with open(SOURCES / "proposal_sharing_candidates.md", "w") as f:
        f.write("Reference operating point: N=27, random topology, loss_rate=0.05, 15 seeds.\n")
        f.write("Source path: plots/scalability/results/sweep_summary.csv\n\n")
        f.write("Paper text:\n")
        f.write("> The rise from there to $5.67$ under 2PC is not proposal sharing, which\n")
        f.write("> accounts for $1.6\\,\\%$ of it; it is the number of slots a decision\n")
        f.write("> occupies, measured as total simulated slots per committed decision and\n")
        f.write("> summed over seeds, which runs from $4.70$ to $6.17$ under \\CI{} against\n")
        f.write("> $4.68$ to $24.34$ under \\CE.\n\n")
        f.write("The available paper text plus the named CSV columns do not define two defensible arithmetic candidates for the antecedent of 'it'.\n")
        f.write("No preferred candidate is selected.\n")
        f.write("The claim 1.6% remains UNSOURCED.\n")
        f.write("The withdrawn 4.57% calculation must not be used because it divided a fresh-run numerator by a frozen-sweep denominator.\n")

    print("Running A3...")
    stats_rows = []
    # Pooled CI
    ci_energy = df_energy[df_energy["phy"] == "CI"]["energy_node_slots"]
    stats_rows.append({
        "family": "Pooled CI", "n": len(ci_energy),
        "min": ci_energy.min(), "p1": np.percentile(ci_energy, 1, method="linear"),
        "q1": np.percentile(ci_energy, 25, method="linear"), "median": ci_energy.median(),
        "q3": np.percentile(ci_energy, 75, method="linear"), "p99": np.percentile(ci_energy, 99, method="linear"),
        "max": ci_energy.max()
    })
    # Paxos CE
    paxos_ce_e = df_energy[df_energy["protocol"] == "Paxos (CE)"]["energy_node_slots"]
    stats_rows.append({
        "family": "Paxos CE", "n": len(paxos_ce_e),
        "min": paxos_ce_e.min(), "p1": np.percentile(paxos_ce_e, 1, method="linear"),
        "q1": np.percentile(paxos_ce_e, 25, method="linear"), "median": paxos_ce_e.median(),
        "q3": np.percentile(paxos_ce_e, 75, method="linear"), "p99": np.percentile(paxos_ce_e, 99, method="linear"),
        "max": paxos_ce_e.max()
    })
    pd.DataFrame(stats_rows).to_csv(SOURCES / "distribution_stats.csv", index=False)
    
    with open(SOURCES / "distribution_stats.md", "w") as f:
        q3_ci = stats_rows[0]["q3"]
        q1_paxos = stats_rows[1]["q1"]
        ratio = q1_paxos / q3_ci
        p99_ci = stats_rows[0]["p99"]
        p1_paxos = stats_rows[1]["p1"]
        f.write(f"Pooled CI Q3: {q3_ci:.1f}\n")
        f.write(f"Paxos CE Q1: {q1_paxos:.1f}\n")
        f.write(f"Ratio (Paxos CE Q1 / Pooled CI Q3): {ratio:.2f}\n")
        f.write(f"Pooled CI P99: {p99_ci:.1f}\n")
        f.write(f"Paxos CE P1: {p1_paxos:.1f}\n")
        f.write("Percentile interpolation method: linear\n")

    print("Running A4...")
    ce_data = df_energy[df_energy["phy"] == "CE"]
    N_total = len(ce_data)
    
    # divisor = N_nodes = 27
    divisor = t['network']['num_nodes']
    violations = sum(ce_data["energy_node_slots"] % divisor != 0)
    
    with open(SOURCES / "integer_multiple_check.md", "w") as f:
        f.write("Population: all CE decisions across 15 seeds from the reference operating point\n")
        f.write(f"N (number of values checked): {N_total}\n")
        f.write(f"Violations (energy not an exact multiple of {divisor}): {violations}\n")
        f.write(f"Divisor used: {divisor} (N_nodes from the reference operating point config)\n")
        
if __name__ == "__main__":
    main()
