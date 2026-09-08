#!/usr/bin/env bash
# Dense-topology latency-structure matrix (addition 14, step 2.7).
# Exactly 60 sequential runs: 2 systems x 15 graph seeds x 2 lock-file loss rates.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
LOCK="profiles/calibration.lock.toml"
OUT_DIR="docs/validation/addition14/data"
OUT_CSV="$OUT_DIR/dense_predictions.csv"
RUN_DIR="/tmp/dense_pred_runs"
SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)
EXPECTED_RUNS=60
EXPECTED_ROWS=100

if [[ ! -x "$BIN" ]]; then
    echo "ERROR: $BIN not found; build with: cargo build --release --bin ctsim" >&2
    exit 1
fi

read_lock_rate() {
    local key="$1"
    local value
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

PRIMARY_LOSS=$(read_lock_rate primary_loss_rate)
SENSITIVITY_LOSS=$(read_lock_rate sensitivity_loss_rate)
printf 'Parsed loss rates from %s: primary=%s sensitivity=%s\n' \
    "$LOCK" "$PRIMARY_LOSS" "$SENSITIVITY_LOSS"

mkdir -p "$OUT_DIR" "$RUN_DIR"
printf '%s\n' 'system,protocol,n,arm,graph_seed,loss_rate,channel_seed,rounds,total_slots,mean_round_slots,max_round_slots_observed,slot_len_ms,total_ms,completed,cap_hit' > "$OUT_CSV"

run_one() {
    local system="$1" protocol="$2" nn="$3" arm="$4" loss="$5" gseed="$6"
    local template="profiles/${system}.toml"
    local cseed="$gseed"
    local gf="profiles/graphs/random_n${nn}_${arm}_seed${gseed}.txt"
    local cfg="$RUN_DIR/${system}_${arm}_loss${loss}_gs${gseed}.toml"

    if [[ ! -f "$gf" ]]; then
        echo "ERROR: graph file not found: $gf" >&2
        exit 1
    fi
    local first_line
    first_line=$(head -n 1 "$gf")
    if [[ "$first_line" != "$nn" ]]; then
        echo "ERROR: $gf: first line '$first_line' does not equal n=$nn" >&2
        exit 1
    fi

    sed -e "s/__SEED__/$cseed/g" \
        -e "s/__LOSS__/$loss/g" \
        -e "s|__GRAPH__|$gf|g" \
        "$template" > "$cfg"

    if grep -qE '__SEED__|__LOSS__|__GRAPH__' "$cfg"; then
        echo "ERROR: $cfg: generated config contains an unsubstituted placeholder" >&2
        exit 1
    fi

    local actual_loss actual_graph
    actual_loss=$(awk -F= '/^[[:space:]]*loss_rate[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    actual_graph=$(awk -F= '/^[[:space:]]*graph_file[[:space:]]*=/ { v=$2; sub(/^[[:space:]]*/, "", v); sub(/[[:space:]]*$/, "", v); gsub(/^"|"$/, "", v); print v; exit }' "$cfg")

    if [[ "$actual_loss" != "$loss" ]]; then
        echo "ERROR: $cfg: loss_rate mismatch: intended '$loss', read back '$actual_loss'" >&2
        exit 1
    fi
    if [[ "$actual_graph" != "$gf" ]]; then
        echo "ERROR: $cfg: graph_file mismatch: intended '$gf', read back '$actual_graph'" >&2
        exit 1
    fi

    local out results_csv saved_csv
    out=$("$BIN" "$cfg" 2>&1)
    case "$protocol" in
        2pc_ce) results_csv="results/results_2pc_ce.csv" ;;
        paxos_ce) results_csv="results/results_paxos_ce.csv" ;;
        *) echo "ERROR: unsupported protocol '$protocol'" >&2; exit 1 ;;
    esac
    saved_csv="$RUN_DIR/${system}_${arm}_loss${loss}_gs${gseed}.csv"
    cp "$results_csv" "$saved_csv"

    local nrows
    nrows=$(awk 'END { print NR - 1 }' "$saved_csv")
    if [[ "$nrows" -ne "$EXPECTED_ROWS" ]]; then
        echo "ERROR: $saved_csv: expected $EXPECTED_ROWS data rows, found $nrows" >&2
        echo "$out" >&2
        exit 1
    fi

    # Validate every row before field access. The simulator proposal CSV is:
    # proposal_id,start_slot,end_slot,latency,outcome
    awk -F, -v file="$saved_csv" '
        NR == 1 {
            if ($0 != "proposal_id,start_slot,end_slot,latency,outcome") {
                printf "ERROR: %s line 1: unexpected header: %s\n", file, $0 > "/dev/stderr"
                exit 1
            }
            next
        }
        NF != 5 {
            printf "ERROR: %s line %d: expected 5 fields, found %d: %s\n", file, NR, NF, $0 > "/dev/stderr"
            exit 1
        }
        $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" {
            printf "ERROR: %s line %d: blank field in row: %s\n", file, NR, $0 > "/dev/stderr"
            exit 1
        }
        $1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ || $4 !~ /^[0-9]+$/ {
            printf "ERROR: %s line %d: non-integer numeric field: %s\n", file, NR, $0 > "/dev/stderr"
            exit 1
        }
        $5 != "committed" && $5 != "aborted" && $5 != "timed_out" {
            printf "ERROR: %s line %d: invalid outcome %s\n", file, NR, $5 > "/dev/stderr"
            exit 1
        }
    ' "$saved_csv"

    local stats
    stats=$(awk -F, '
        NR > 1 {
            rounds++
            total += $4
            if ($4 > max_round) max_round = $4
            if ($5 == "timed_out") timed_out++
            if ($5 == "aborted") aborted++
        }
        END {
            printf "%d,%d,%.6f,%d,%d,%d\n", rounds, total, total / rounds, max_round, timed_out, aborted
        }
    ' "$saved_csv")

    local rounds total_slots mean_round_slots max_round observed_timed_out observed_aborted
    IFS=, read -r rounds total_slots mean_round_slots max_round observed_timed_out observed_aborted <<< "$stats"

    local max_slots max_round_cap
    max_slots=$(awk -F= '/^[[:space:]]*max_slots[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")
    max_round_cap=$(awk -F= '/^[[:space:]]*max_round_slots[[:space:]]*=/ { gsub(/[[:space:]]/, "", $2); print $2; exit }' "$cfg")

    local completed=true cap_hit=false
    if [[ "$observed_timed_out" -gt 0 || "$rounds" -ne "$EXPECTED_ROWS" ]]; then
        completed=false
    fi
    if [[ "$observed_timed_out" -gt 0 || "$max_round" -ge "$max_round_cap" || "$total_slots" -ge "$max_slots" ]]; then
        cap_hit=true
    fi

    local slot_len_ms
    case "$protocol" in
        2pc_ce) slot_len_ms="4.75" ;;
        paxos_ce) slot_len_ms="5.00" ;;
    esac
    local total_ms
    total_ms=$(awk -v slots="$total_slots" -v ms="$slot_len_ms" 'BEGIN { printf "%.6f", slots * ms }')

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$system" "$protocol" "$nn" "$arm" "$gseed" "$loss" "$cseed" \
        "$rounds" "$total_slots" "$mean_round_slots" "$max_round" "$slot_len_ms" \
        "$total_ms" "$completed" "$cap_hit" >> "$OUT_CSV"

    printf '  %-16s arm=%-5s loss=%s gs=%2d rounds=%3d total_slots=%5d mean_round=%7.3f completed=%s cap_hit=%s\n' \
        "$system" "$arm" "$loss" "$gseed" "$rounds" "$total_slots" "$mean_round_slots" "$completed" "$cap_hit"
}

total=0
for system_spec in "a2_sensys17 2pc_ce 180" "wpaxos_ewsn19 paxos_ce 188"; do
    read -r system protocol nn <<< "$system_spec"
    for loss in "$PRIMARY_LOSS" "$SENSITIVITY_LOSS"; do
        for gseed in "${SEEDS[@]}"; do
            run_one "$system" "$protocol" "$nn" dense "$loss" "$gseed"
            total=$((total + 1))
        done
    done
done

if [[ "$total" -ne "$EXPECTED_RUNS" ]]; then
    echo "ERROR: executed $total runs, expected exactly $EXPECTED_RUNS" >&2
    exit 1
fi

actual_rows=$(awk 'END { print NR - 1 }' "$OUT_CSV")
if [[ "$actual_rows" -ne "$EXPECTED_RUNS" ]]; then
    echo "ERROR: $OUT_CSV contains $actual_rows data rows, expected $EXPECTED_RUNS" >&2
    exit 1
fi

printf 'Done: %d sequential runs. Output: %s\n' "$total" "$OUT_CSV"
