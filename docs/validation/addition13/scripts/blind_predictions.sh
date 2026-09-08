#!/usr/bin/env bash
#
# Blind-prediction run matrix (addition 13, step 2.5).
#
# 120 runs total:
#   Primary: 2 systems x 15 graph seeds x {0.05, 0.06}          = 60
#   Robustness: 2 systems x 15 graph seeds x {deg_minus1, deg_plus1} at 0.05 = 60
#
# For every run: seed = graph_seed (one channel realisation per graph).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
OUT_DIR="docs/validation/addition13/data"
OUT_CSV="$OUT_DIR/blind_predictions.csv"
RUN_DIR="/tmp/blind_pred_runs"

if [[ ! -x "$BIN" ]]; then
    echo "error: $BIN not found. Build first: cargo build --release" >&2
    exit 1
fi

SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)

mkdir -p "$OUT_DIR" "$RUN_DIR"

echo "system,protocol,num_nodes,arm,loss_rate,graph_seed,channel_seed,total_recorded,committed,aborted,timed_out,mean_latency_slots,median_latency_slots,max_latency_slots,ce_timeouts,total_listen,total_flood,total_sleep,end_slot,edges,diameter,mean_degree,degree2_count,graph_sha256" > "$OUT_CSV"

run_one() {
    local system="$1" protocol="$2" nn="$3" arm="$4" loss="$5" gseed="$6"
    local template="profiles/${system}.toml"
    local cseed="$gseed"  # seed = graph_seed

    # Build graph file path
    local gf
    if [[ "$arm" == "base" ]]; then
        gf="profiles/graphs/random_n${nn}_seed${gseed}.txt"
    else
        gf="profiles/graphs/random_n${nn}_${arm}_seed${gseed}.txt"
    fi

    # Assert graph file first line = nn
    local first_line
    first_line=$(head -1 "$gf")
    if [[ "$first_line" != "$nn" ]]; then
        echo "ERROR: $gf first line is '$first_line', expected '$nn'" >&2
        exit 1
    fi

    local cfg="/tmp/blind_pred_cfg.toml"
    sed -e "s/__SEED__/$cseed/g" -e "s/__LOSS__/$loss/g" -e "s|__GRAPH__|$gf|g" "$template" > "$cfg"

    # Fail loudly if any placeholder survived substitution.
    if grep -qE '__SEED__|__LOSS__|__GRAPH__' "$cfg"; then
        echo "ERROR: $cfg still contains an unsubstituted placeholder after sed:" >&2
        grep -nE '__SEED__|__LOSS__|__GRAPH__' "$cfg" >&2
        exit 1
    fi

    local out
    out=$("$BIN" "$cfg" 2>&1)

    # Determine results CSV name
    local results_csv
    if [[ "$protocol" == "2pc_ce" ]]; then
        results_csv="results/results_2pc_ce.csv"
    else
        results_csv="results/results_paxos_ce.csv"
    fi

    # Copy immediately
    local saved_csv="$RUN_DIR/${system}_${arm}_loss${loss}_gs${gseed}.csv"
    cp "$results_csv" "$saved_csv"

    # Count rows (excluding header)
    local nrows
    nrows=$(tail -n +2 "$saved_csv" | wc -l | tr -d ' ')
    if [[ "$nrows" -ne 100 ]]; then
        echo "ERROR: $saved_csv has $nrows data rows, expected 100" >&2
        echo "STDOUT: $out" >&2
        exit 1
    fi

    # Compute from CSV
    local committed aborted timed_out total_recorded
    committed=$(awk -F, '$5=="committed"' "$saved_csv" | wc -l | tr -d ' ')
    aborted=$(awk -F, '$5=="aborted"' "$saved_csv" | wc -l | tr -d ' ')
    timed_out=$(awk -F, '$5=="timed_out"' "$saved_csv" | wc -l | tr -d ' ')
    total_recorded=$((committed + aborted + timed_out))

    # Mean/median/max latency of committed proposals, from the CSV at full precision
    local stats
    stats=$(awk -F, '
        $5=="committed" { lat[++n] = $4 }
        END {
            if (n == 0) { print "0,0,0"; exit }
            sum = 0; max_v = 0
            for (i = 1; i <= n; i++) { sum += lat[i]; if (lat[i] > max_v) max_v = lat[i] }
            mean = sum / n
            # sort for median
            for (i = 1; i <= n; i++) for (j = i+1; j <= n; j++) if (lat[i] > lat[j]) { t=lat[i]; lat[i]=lat[j]; lat[j]=t }
            if (n % 2 == 1) median = lat[(n+1)/2]
            else median = (lat[n/2] + lat[n/2+1]) / 2.0
            printf "%.6f,%.1f,%d\n", mean, median, max_v
        }
    ' "$saved_csv")

    local mean_lat median_lat max_lat
    mean_lat=$(echo "$stats" | cut -d, -f1)
    median_lat=$(echo "$stats" | cut -d, -f2)
    max_lat=$(echo "$stats" | cut -d, -f3)

    # Cross-check against stdout
    local stdout_lat
    stdout_lat=$(echo "$out" | grep 'Avg latency (committed):' | sed 's/.*: //; s/ slots//')
    if [[ -n "$stdout_lat" ]]; then
        local diff
        diff=$(awk -v a="$mean_lat" -v b="$stdout_lat" 'BEGIN { d = a - b; if (d < 0) d = -d; print d }')
        local bad
        bad=$(awk -v d="$diff" 'BEGIN { print (d > 0.05) ? "YES" : "NO" }')
        if [[ "$bad" == "YES" ]]; then
            echo "WARNING: latency cross-check failed for $system arm=$arm loss=$loss gs=$gseed: csv=$mean_lat stdout=$stdout_lat diff=$diff" >&2
        fi
    fi

    # Extract from stdout
    local ce_timeouts total_listen total_flood total_sleep
    ce_timeouts=$(echo "$out" | grep 'CE_Timeouts=' | sed 's/.*CE_Timeouts=//')
    total_listen=$(echo "$out" | grep 'Energy profile:' | sed 's/.*Listen=//; s/ .*//')
    total_flood=$(echo "$out" | grep 'Energy profile:' | sed 's/.*Flood=//; s/ .*//')
    total_sleep=$(echo "$out" | grep 'Energy profile:' | sed 's/.*Sleep=//; s/ .*//')

    # end_slot = max end_slot from csv
    local end_slot
    end_slot=$(awk -F, 'NR>1 { if ($3+0 > m) m=$3+0 } END { print m }' "$saved_csv")

    # Graph stats from the Topology line
    local topo_line edges diameter
    topo_line=$(echo "$out" | grep '^Topology:')
    edges=$(echo "$topo_line" | sed 's/.*edges=//; s/ .*//')
    diameter=$(echo "$topo_line" | sed 's/.*diameter=//; s/ .*//')
    local mean_degree
    mean_degree=$(awk -v e="$edges" -v n="$nn" 'BEGIN { printf "%.6f", 2*e/n }')

    # degree2_count from the provenance CSV
    local degree2_count
    degree2_count=$(awk -F, -v n="$nn" -v a="$arm" -v s="$gseed" '
        $1==n && $2==a && $3==s { print $11 }
    ' "$OUT_DIR/graph_provenance_large.csv")
    if [[ -z "$degree2_count" ]]; then
        # For n=27 base graphs, check the addition12 provenance (won't apply here)
        degree2_count="NA"
    fi

    # graph sha (portable: sha256sum on Linux, shasum -a 256 on macOS)
    local graph_sha
    if command -v sha256sum &>/dev/null; then
        graph_sha=$(sha256sum "$gf" | cut -d' ' -f1)
    else
        graph_sha=$(shasum -a 256 "$gf" | cut -d' ' -f1)
    fi

    # Report
    if [[ "$timed_out" -gt 0 ]]; then
        echo "TIMED_OUT: $system arm=$arm loss=$loss gs=$gseed timed_out=$timed_out" >&2
    fi

    echo "$system,$protocol,$nn,$arm,$loss,$gseed,$cseed,$total_recorded,$committed,$aborted,$timed_out,$mean_lat,$median_lat,$max_lat,$ce_timeouts,$total_listen,$total_flood,$total_sleep,$end_slot,$edges,$diameter,$mean_degree,$degree2_count,$graph_sha" >> "$OUT_CSV"

    printf '  %s arm=%-12s loss=%s gs=%2d  committed=%3d aborted=%d timed_out=%d  mean_lat=%.1f\n' \
        "$system" "$arm" "$loss" "$gseed" "$committed" "$aborted" "$timed_out" "$mean_lat"
}

total=0

echo "=== PRIMARY RUNS (base arm, loss 0.05 and 0.06) ==="
for loss in 0.05 0.06; do
    for gseed in "${SEEDS[@]}"; do
        run_one a2_sensys17 2pc_ce 180 base "$loss" "$gseed"
        total=$((total + 1))
    done
done
for loss in 0.05 0.06; do
    for gseed in "${SEEDS[@]}"; do
        run_one wpaxos_ewsn19 paxos_ce 188 base "$loss" "$gseed"
        total=$((total + 1))
    done
done

echo ""
echo "=== ROBUSTNESS RUNS (deg_minus1 and deg_plus1, loss 0.05) ==="
for arm in deg_minus1 deg_plus1; do
    for gseed in "${SEEDS[@]}"; do
        run_one a2_sensys17 2pc_ce 180 "$arm" 0.05 "$gseed"
        total=$((total + 1))
    done
done
for arm in deg_minus1 deg_plus1; do
    for gseed in "${SEEDS[@]}"; do
        run_one wpaxos_ewsn19 paxos_ce 188 "$arm" 0.05 "$gseed"
        total=$((total + 1))
    done
done

echo ""
echo "Done: $total runs."
echo "Output: $OUT_CSV"
