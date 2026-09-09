#!/usr/bin/env bash
# Addition 14 outcome-stratified re-analysis and channel-control matrix.
#
# `rounds` equals the number of proposals by construction and is therefore
# constant at 100. `total_slots_all` and `total_ms_all` are algebraically
# determined by `mean_round_slots_all` and carry no independent information.
# The columns remain for explicit provenance and review.
#
# Exactly 135 sequential runs:
#   60 dense + 60 sparse base + 15 dense channel-control.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
LOCK="profiles/calibration.lock.toml"
SLOT_SOURCE="docs/validation/addition14/data/published_slot_lengths.csv"
OUT_CSV="docs/validation/addition14/data/stratified_predictions.csv"
RUN_DIR="/tmp/stratified_pred_runs"
TIMING_FILE="/tmp/stratified_prediction_timings.txt"
SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)
EXPECTED_ROWS=100

if [[ ! -x "$BIN" ]]; then
    echo "ERROR: $BIN not found; build with: cargo build --release --bin ctsim" >&2
    exit 1
fi

read_lock_rate() {
    local key="$1" value
    value=$(awk -v wanted="$key" '
        /^\[step_2_5\][[:space:]]*$/ { in_section=1; next }
        /^\[/ { in_section=0 }
        in_section && $1 == wanted && $2 == "=" { print $3; found=1; exit }
        END { if (!found) exit 1 }
    ' "$LOCK") || {
        echo "ERROR: $LOCK: missing or unparseable step_2_5.$key" >&2
        exit 1
    }
    if ! awk -v v="$value" 'BEGIN { exit !((v + 0) == v && v != "") }'; then
        echo "ERROR: $LOCK: missing or unparseable step_2_5.$key" >&2
        exit 1
    fi
    printf '%s\n' "$value"
}

read_slot_length() {
    local key="$1" value
    value=$(awk -F, -v wanted="$key" '
        NR == 1 {
            for (i=1; i<=NF; i++) if ($i == "constant") key_col=i
            for (i=1; i<=NF; i++) if ($i == "slot_ms_nominal") value_col=i
            next
        }
        key_col && value_col && $key_col == wanted { print $value_col; found=1; exit }
        END { if (!found) exit 1 }
    ' "$SLOT_SOURCE") || {
        echo "ERROR: $SLOT_SOURCE: missing or unparseable key '$key'.slot_ms_nominal" >&2
        exit 1
    }
    if ! awk -v v="$value" 'BEGIN { exit !((v + 0) == v && v > 0) }'; then
        echo "ERROR: $SLOT_SOURCE: missing or unparseable key '$key'.slot_ms_nominal" >&2
        exit 1
    fi
    printf '%s\n' "$value"
}

PRIMARY_LOSS=$(read_lock_rate primary_loss_rate)
SENSITIVITY_LOSS=$(read_lock_rate sensitivity_loss_rate)
TWO_PC_SLOT_MS=$(read_slot_length TWO_PC_SLOT_LEN)
PAXOS_SLOT_MS=$(read_slot_length PAXOS_SLOT_LEN)
printf 'Parsed loss rates: primary=%s sensitivity=%s\n' "$PRIMARY_LOSS" "$SENSITIVITY_LOSS"
printf 'Parsed slot lengths from %s: TWO_PC_SLOT_LEN.slot_ms_nominal=%s PAXOS_SLOT_LEN.slot_ms_nominal=%s\n' \
    "$SLOT_SOURCE" "$TWO_PC_SLOT_MS" "$PAXOS_SLOT_MS"

mkdir -p "$(dirname "$OUT_CSV")" "$RUN_DIR"
printf '%s\n' 'system,protocol,n,arm,graph_seed,loss_rate,channel_seed,rounds,n_committed,n_aborted,n_timed_out,total_slots_all,mean_round_slots_all,mean_round_slots_committed,sd_round_slots_committed,max_round_slots_observed,slot_len_ms,total_ms_all,completed,cap_hit' > "$OUT_CSV"
: > "$TIMING_FILE"

now_ns() {
    python3 -c 'import time; print(time.monotonic_ns())'
}

record_elapsed() {
    local block="$1" start_ns="$2" end_ns seconds
    end_ns=$(now_ns)
    seconds=$(awk -v a="$start_ns" -v b="$end_ns" 'BEGIN { printf "%.2f", (b-a)/1000000000 }')
    printf '%s_seconds=%s\n' "$block" "$seconds" | tee -a "$TIMING_FILE"
}

run_one() {
    local system="$1" protocol="$2" nn="$3" arm="$4" loss="$5" gseed="$6" cseed="$7"
    local template="profiles/${system}.toml" graph_arm="$arm"
    [[ "$arm" == "dense_chanctl" ]] && graph_arm="dense"
    local gf
    if [[ "$graph_arm" == "base" ]]; then
        gf="profiles/graphs/random_n${nn}_seed${gseed}.txt"
    else
        gf="profiles/graphs/random_n${nn}_${graph_arm}_seed${gseed}.txt"
    fi
    local cfg="$RUN_DIR/${system}_${arm}_loss${loss}_gs${gseed}_cs${cseed}.toml"

    [[ -f "$gf" ]] || { echo "ERROR: graph file not found: $gf" >&2; exit 1; }
    local first_line
    first_line=$(head -n 1 "$gf")
    [[ "$first_line" == "$nn" ]] || {
        echo "ERROR: $gf: first line '$first_line' does not equal n=$nn" >&2
        exit 1
    }

    sed -e "s/__SEED__/$cseed/g" -e "s/__LOSS__/$loss/g" -e "s|__GRAPH__|$gf|g" \
        "$template" > "$cfg"
    if grep -qE '__SEED__|__LOSS__|__GRAPH__' "$cfg"; then
        echo "ERROR: $cfg: generated config contains an unsubstituted placeholder" >&2
        exit 1
    fi

    local actual_loss actual_graph actual_seed
    actual_loss=$(awk -F= '/^[[:space:]]*loss_rate[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    actual_graph=$(awk -F= '/^[[:space:]]*graph_file[[:space:]]*=/ { v=$2; sub(/^[[:space:]]*/, "", v); sub(/[[:space:]]*$/, "", v); gsub(/^"|"$/, "", v); print v; exit }' "$cfg")
    actual_seed=$(awk -F= '/^[[:space:]]*seed[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    [[ "$actual_loss" == "$loss" ]] || { echo "ERROR: $cfg: loss_rate mismatch: intended '$loss', read back '$actual_loss'" >&2; exit 1; }
    [[ "$actual_graph" == "$gf" ]] || { echo "ERROR: $cfg: graph_file mismatch: intended '$gf', read back '$actual_graph'" >&2; exit 1; }
    [[ "$actual_seed" == "$cseed" ]] || { echo "ERROR: $cfg: seed mismatch: intended '$cseed', read back '$actual_seed'" >&2; exit 1; }

    local out results_csv saved_csv
    out=$("$BIN" "$cfg" 2>&1)
    case "$protocol" in
        2pc_ce) results_csv="results/results_2pc_ce.csv"; slot_len_ms="$TWO_PC_SLOT_MS" ;;
        paxos_ce) results_csv="results/results_paxos_ce.csv"; slot_len_ms="$PAXOS_SLOT_MS" ;;
        *) echo "ERROR: unsupported protocol '$protocol'" >&2; exit 1 ;;
    esac
    saved_csv="$RUN_DIR/${system}_${arm}_loss${loss}_gs${gseed}_cs${cseed}.csv"
    cp "$results_csv" "$saved_csv"

    local nrows
    nrows=$(awk 'END { print NR - 1 }' "$saved_csv")
    [[ "$nrows" -eq "$EXPECTED_ROWS" ]] || {
        echo "ERROR: $saved_csv: expected $EXPECTED_ROWS data rows, found $nrows" >&2
        echo "$out" >&2
        exit 1
    }

    awk -F, -v file="$saved_csv" '
        NR == 1 {
            if ($0 != "proposal_id,start_slot,end_slot,latency,outcome") {
                printf "ERROR: %s line 1: unexpected header: %s\n", file, $0 > "/dev/stderr"; exit 1
            }
            next
        }
        NF != 5 { printf "ERROR: %s line %d: expected 5 fields, found %d: %s\n", file, NR, NF, $0 > "/dev/stderr"; exit 1 }
        $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" {
            printf "ERROR: %s line %d: blank field in row: %s\n", file, NR, $0 > "/dev/stderr"; exit 1
        }
        $1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ || $4 !~ /^[0-9]+$/ {
            printf "ERROR: %s line %d: non-integer numeric field: %s\n", file, NR, $0 > "/dev/stderr"; exit 1
        }
        $5 != "committed" && $5 != "aborted" && $5 != "timed_out" {
            printf "ERROR: %s line %d: invalid outcome %s\n", file, NR, $5 > "/dev/stderr"; exit 1
        }
    ' "$saved_csv"

    local stats
    stats=$(awk -F, -v file="$saved_csv" '
        NR > 1 {
            rounds++; total += $4; if ($4 > max_round) max_round=$4
            if ($5 == "committed") { committed++; csum += $4; csumsq += $4*$4 }
            else if ($5 == "aborted") aborted++
            else if ($5 == "timed_out") timed_out++
        }
        END {
            outcomes=committed+aborted+timed_out
            if (outcomes != 100) {
                printf "ERROR: %s line %d: outcome count %d != 100 (committed=%d aborted=%d timed_out=%d)\n", file, NR, outcomes, committed, aborted, timed_out > "/dev/stderr"; exit 1
            }
            cmean=(committed ? csum/committed : 0)
            csd=(committed > 1 ? sqrt((csumsq-csum*csum/committed)/(committed-1)) : 0)
            printf "%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%d\n", rounds, committed, aborted, timed_out, total, total/rounds, cmean, csd, max_round
        }
    ' "$saved_csv")

    local rounds n_committed n_aborted n_timed_out total_slots mean_all mean_committed sd_committed max_round
    IFS=, read -r rounds n_committed n_aborted n_timed_out total_slots mean_all mean_committed sd_committed max_round <<< "$stats"
    local max_slots max_round_cap completed=true cap_hit=false total_ms
    max_slots=$(awk -F= '/^[[:space:]]*max_slots[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    max_round_cap=$(awk -F= '/^[[:space:]]*max_round_slots[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    [[ "$n_timed_out" -gt 0 || "$rounds" -ne 100 ]] && completed=false
    [[ "$n_timed_out" -gt 0 || "$max_round" -ge "$max_round_cap" || "$total_slots" -ge "$max_slots" ]] && cap_hit=true
    total_ms=$(awk -v s="$total_slots" -v ms="$slot_len_ms" 'BEGIN { printf "%.6f", s*ms }')

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$system" "$protocol" "$nn" "$arm" "$gseed" "$loss" "$cseed" "$rounds" \
        "$n_committed" "$n_aborted" "$n_timed_out" "$total_slots" "$mean_all" \
        "$mean_committed" "$sd_committed" "$max_round" "$slot_len_ms" "$total_ms" \
        "$completed" "$cap_hit" >> "$OUT_CSV"
    printf '  %-16s arm=%-13s loss=%s gs=%2d cs=%2d C/A/T=%d/%d/%d mean_all=%7.3f mean_C=%7.3f\n' \
        "$system" "$arm" "$loss" "$gseed" "$cseed" "$n_committed" "$n_aborted" "$n_timed_out" "$mean_all" "$mean_committed"
}

total=0
dense_start=$(now_ns)
for system_spec in "a2_sensys17 2pc_ce 180" "wpaxos_ewsn19 paxos_ce 188"; do
    read -r system protocol nn <<< "$system_spec"
    for loss in "$PRIMARY_LOSS" "$SENSITIVITY_LOSS"; do
        for seed in "${SEEDS[@]}"; do
            run_one "$system" "$protocol" "$nn" dense "$loss" "$seed" "$seed"
            total=$((total+1))
        done
    done
done
record_elapsed dense "$dense_start"

base_start=$(now_ns)
for system_spec in "a2_sensys17 2pc_ce 180" "wpaxos_ewsn19 paxos_ce 188"; do
    read -r system protocol nn <<< "$system_spec"
    for loss in "$PRIMARY_LOSS" "$SENSITIVITY_LOSS"; do
        for seed in "${SEEDS[@]}"; do
            run_one "$system" "$protocol" "$nn" base "$loss" "$seed" "$seed"
            total=$((total+1))
        done
    done
done
record_elapsed base "$base_start"

chanctl_start=$(now_ns)
for cseed in "${SEEDS[@]}"; do
    run_one a2_sensys17 2pc_ce 180 dense_chanctl "$PRIMARY_LOSS" 2 "$cseed"
    total=$((total+1))
done
record_elapsed dense_chanctl "$chanctl_start"

[[ "$total" -eq 135 ]] || { echo "ERROR: executed $total runs, expected exactly 135" >&2; exit 1; }
read -r rows dense_count base_count chanctl_count <<< "$(awk -F, 'NR>1 { rows++; count[$4]++ } END { print rows, count["dense"]+0, count["base"]+0, count["dense_chanctl"]+0 }' "$OUT_CSV")"
[[ "$rows" -eq 135 ]] || { echo "ERROR: $OUT_CSV has $rows data rows, expected 135" >&2; exit 1; }
[[ "$dense_count" -eq 60 ]] || { echo "ERROR: $OUT_CSV has $dense_count arm=dense rows, expected 60" >&2; exit 1; }
[[ "$base_count" -eq 60 ]] || { echo "ERROR: $OUT_CSV has $base_count arm=base rows, expected 60" >&2; exit 1; }
[[ "$chanctl_count" -eq 15 ]] || { echo "ERROR: $OUT_CSV has $chanctl_count arm=dense_chanctl rows, expected 15" >&2; exit 1; }
printf 'ASSERTIONS PASSED: runs=%d csv_rows=%d dense=%d base=%d dense_chanctl=%d\n' \
    "$total" "$rows" "$dense_count" "$base_count" "$chanctl_count"
