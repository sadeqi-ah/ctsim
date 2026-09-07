#!/usr/bin/env bash
#
# Pure-flood coverage-vs-loss curve (step 2.3).
#
# For each (loss_rate, seed) pair it fills the template in profiles/, runs the
# release binary, and appends the single PURE_FLOOD stdout line as one CSV row.
# Writes only under docs/validation/addition11/data/ — never under plots/ or
# examples/ (a config in examples/ would be smoke-run by CI on every push).
#
# loss_rate = 0.0 is deliberately NOT on the grid. The loss draw in src/phy/ci.rs
# short-circuits on `loss_rate == 0.0` and consumes no RNG value, so that point
# does not sit on the same random footing as the rest of the curve: every later
# draw would come from a differently-advanced stream. The lossless case is
# covered separately by the deterministic test in tests/validation.rs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
TEMPLATE="profiles/pure_flood_n27_template.toml"
OUT_DIR="docs/validation/addition11/data"
OUT_CSV="$OUT_DIR/coverage_curve.csv"
# The filename must not contain the substring "sweep": src/main.rs routes any
# config path containing it to the sweep runner.
RUN_CFG="/tmp/pure_flood_run.toml"

if [[ ! -x "$BIN" ]]; then
    echo "error: $BIN not found. Build it first:" >&2
    echo "    cargo build --release" >&2
    exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
    echo "error: template $TEMPLATE not found" >&2
    exit 1
fi

LOSS_RATES=(0.02 0.05 0.10 0.15 0.20 0.25 0.30 0.35 0.40 0.45 0.50 0.60 0.70 0.80 0.90)
# The 15 seeds already used by the committed sweeps.
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

        # PURE_FLOOD n=.. loss=.. seed=.. floods=.. covered=.. opportunities=..
        # coverage=.. rx_attempts=.. rx_success=.. slots=..
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
