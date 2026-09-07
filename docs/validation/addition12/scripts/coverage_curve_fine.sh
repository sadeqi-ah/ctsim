#!/usr/bin/env bash
#
# Fine loss sweep at 0.06-0.09 (addition 12, step 5).
#
# Old methodology (seed = graph + channel), deliberately identical to the merged
# coverage_curve.sh so the two grids are directly comparable.
# Output: docs/validation/addition12/data/coverage_curve_fine.csv

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
TEMPLATE="profiles/pure_flood_n27_template.toml"
OUT_DIR="docs/validation/addition12/data"
OUT_CSV="$OUT_DIR/coverage_curve_fine.csv"
RUN_CFG="/tmp/pure_flood_fine_run.toml"

if [[ ! -x "$BIN" ]]; then
    echo "error: $BIN not found. Build it first:" >&2
    echo "    cargo build --release" >&2
    exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
    echo "error: template $TEMPLATE not found" >&2
    exit 1
fi

LOSS_RATES=(0.06 0.07 0.08 0.09)
SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)

mkdir -p "$OUT_DIR"
echo "loss_rate,seed,num_nodes,floods,receivers_covered,receiver_opportunities,coverage,rx_attempts,rx_success,slots" > "$OUT_CSV"

total=$(( ${#LOSS_RATES[@]} * ${#SEEDS[@]} ))
done_n=0

for loss in "${LOSS_RATES[@]}"; do
    for seed in "${SEEDS[@]}"; do
        sed -e "s/__SEED__/$seed/g" -e "s/__LOSS__/$loss/g" "$TEMPLATE" > "$RUN_CFG"

        out="$("$BIN" "$RUN_CFG")"
        line="$(printf '%s\n' "$out" | grep '^PURE_FLOOD ' || true)"
        if [[ -z "$line" ]]; then
            echo "error: no PURE_FLOOD line for loss=$loss seed=$seed" >&2
            printf '%s\n' "$out" >&2
            exit 1
        fi

        printf '%s\n' "$line" | awk -v loss="$loss" -v seed="$seed" '
        {
            for (i = 2; i <= NF; i++) {
                split($i, kv, "=")
                v[kv[1]] = kv[2]
            }
            printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
                loss, seed, v["n"], v["floods"], v["covered"], v["opportunities"],
                v["coverage"], v["rx_attempts"], v["rx_success"], v["slots"]
        }' >> "$OUT_CSV"

        done_n=$(( done_n + 1 ))
        printf '\r  %3d/%3d  loss=%s seed=%s ' "$done_n" "$total" "$loss" "$seed"
    done
done

printf '\n'
rm -f "$RUN_CFG"
echo "wrote $OUT_CSV ($done_n runs)"
