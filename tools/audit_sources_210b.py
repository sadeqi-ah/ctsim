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
        f.write(f"Commit SHA: {sha}\n")
        f.write("\n".join(summary_lines) + "\n")

    print("Running A2...")
    df_sweep = pd.read_csv(ROOT / "plots/scalability/results/sweep_summary.csv")
    df_ref = df_sweep[(df_sweep["nodes"] == 27) & (df_sweep["loss_rate"] == 0.05)].copy()
    
    df_ref["slots_per_decision"] = df_ref["end_slot"] / df_ref["committed"]
    df_ref[["phy", "protocol", "seed", "end_slot", "committed", "slots_per_decision"]].rename(
        columns={"end_slot": "total_slots", "committed": "committed_decisions"}
    ).to_csv(SOURCES / "slots_per_decision.csv", index=False)
    
    means = df_ref.groupby(["phy", "protocol"])["slots_per_decision"].mean().reset_index()
    ci_min = means[means["phy"] == "ci"]["slots_per_decision"].min()
    ci_max = means[means["phy"] == "ci"]["slots_per_decision"].max()
    ce_min = means[means["phy"] == "ce"]["slots_per_decision"].min()
    ce_max = means[means["phy"] == "ce"]["slots_per_decision"].max()
    
    # To get proposal sharing share properly, let's compute it like this:
    # Use the 15-seed amortized energy
    sys.path.insert(0, str(ROOT / "plots" / "energy"))
    import plot_stacked_bar
    # This will run the 15 seeds and return per-proposal energy: Protocol, seed, proposal_id, awake_slots
    df_energy = plot_stacked_bar.run_simulation_and_extract_per_proposal(plot_stacked_bar.SEEDS)
    df_energy.rename(columns={"awake_slots": "energy_node_slots", "Protocol": "protocol", "proposal_id": "decision_index"}, inplace=True)
    
    # map PHY
    def get_phy(prot):
        return "CI" if "(CI)" in prot else "CE"
    df_energy["phy"] = df_energy["protocol"].apply(get_phy)
    
    df_energy[["phy", "protocol", "seed", "decision_index", "energy_node_slots"]].to_csv(SOURCES / "per_decision_energy.csv", index=False)
    
    # A2 proposal sharing for 2PC CI
    amortized_2pc = df_energy[df_energy["protocol"] == "2PC (CI)"]["energy_node_slots"].mean()
    d_2pc_ci = df_ref[df_ref["protocol"] == "2pc_pipeline"]
    cum_2pc = (d_2pc_ci["listen"] + d_2pc_ci["flood"]).sum() / d_2pc_ci["committed"].sum()
    prop_sharing_share = 1 - (amortized_2pc / cum_2pc)
    
    with open(SOURCES / "slots_per_decision.md", "w") as f:
        f.write("Formula: slots_per_decision = total_slots / committed_decisions (computed per seed, then mean taken)\n")
        f.write("Configs: scalability sweep at N=27, random topology, loss_rate=0.05, 15 seeds\n")
        f.write(f"CI min: {ci_min:.3f}, CI max: {ci_max:.3f}\n")
        f.write(f"CE min: {ce_min:.3f}, CE max: {ce_max:.3f}\n")
        f.write(f"Proposal sharing share for 2PC: {prop_sharing_share*100:.2f}%\n")
        f.write(f"  Numerator: Amortized energy per decision across 15 seeds ({amortized_2pc})\n")
        f.write(f"  Denominator: Cumulative energy per decision from sweep_summary.csv ({cum_2pc})\n")
        f.write(f"  Share = 1 - (Numerator / Denominator)\n")

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
