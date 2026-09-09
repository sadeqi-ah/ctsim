#!/usr/bin/env python3
# The mean-SD and CV definition is duplicated in tests/validation.rs; they must be changed together.
import sys, os, csv

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
csv_path = os.path.join(repo_root, "docs/validation/addition14/data/stratified_predictions.csv")

def label(system):
    if system == "a2_sensys17": return "A2/2PC"
    if system == "wpaxos_ewsn19": return "WPaxos"
    return ""

stats = {}

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sys_name = row['system']
        arm = row['arm']
        loss = row['loss_rate']
        if arm not in ("dense", "base"):
            continue
        sd_val = float(row['sd_round_slots_committed'])
        mean_val = float(row['mean_round_slots_committed'])
        
        k = (sys_name, arm, loss)
        stats.setdefault(k, {'count': 0, 'sd': 0.0, 'mean': 0.0})
        stats[k]['count'] += 1
        stats[k]['sd'] += sd_val
        stats[k]['mean'] += mean_val
        
        pk = (sys_name, arm, "pooled")
        stats.setdefault(pk, {'count': 0, 'sd': 0.0, 'mean': 0.0})
        stats[pk]['count'] += 1
        stats[pk]['sd'] += sd_val
        stats[pk]['mean'] += mean_val

print("| System | Arm | loss=0.05 Mean SD | loss=0.05 CV | loss=0.05 Runs | loss=0.06 Mean SD | loss=0.06 CV | loss=0.06 Runs | Pooled Mean SD | Pooled CV | Pooled Runs |")
print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

for (sys_name, arm) in [("a2_sensys17", "dense"), ("a2_sensys17", "base"), ("wpaxos_ewsn19", "dense"), ("wpaxos_ewsn19", "base")]:
    k05 = (sys_name, arm, "0.05")
    k06 = (sys_name, arm, "0.06")
    kp = (sys_name, arm, "pooled")
    
    if stats[k05]['count'] != 15 or stats[k06]['count'] != 15 or stats[kp]['count'] != 30:
        print(f"ERROR: {sys_name}/{arm}: count mismatch", file=sys.stderr)
        sys.exit(1)
        
    sd05 = stats[k05]['sd'] / stats[k05]['count']
    mean05 = stats[k05]['mean'] / stats[k05]['count']
    cv05 = sd05 / mean05
    
    sd06 = stats[k06]['sd'] / stats[k06]['count']
    mean06 = stats[k06]['mean'] / stats[k06]['count']
    cv06 = sd06 / mean06
    
    sdp = stats[kp]['sd'] / stats[kp]['count']
    meanp = stats[kp]['mean'] / stats[kp]['count']
    cvp = sdp / meanp
    
    print(f"| {label(sys_name)} | {arm} | {sd05:.5f} | {cv05:.5f} | {stats[k05]['count']} | {sd06:.5f} | {cv06:.5f} | {stats[k06]['count']} | {sdp:.5f} | {cvp:.5f} | {stats[kp]['count']} |")
