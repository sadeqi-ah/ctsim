#!/usr/bin/env bash
#
# Graph/channel decoupling grid (addition 12, step 6).
#
# 15 frozen graphs x 15 channel seeds x 6 loss levels = 1350 runs.
# With graph_file set, build_graph returns early and rng is untouched, so
# config.seed controls ONLY the channel loss draws.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT"

BIN="target/release/ctsim"
OUT_DIR="docs/validation/addition12/data"
OUT_CSV="$OUT_DIR/coverage_grid.csv"
RUN_CFG="/tmp/pure_flood_grid_run.toml"

if [[ ! -x "$BIN" ]]; then
    echo "error: $BIN not found. Build it first:" >&2
    echo "    cargo build --release" >&2
    exit 1
fi

GRAPH_SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)
CHANNEL_SEEDS=(2 3 5 7 11 13 17 19 23 29 31 37 41 43 47)
LOSS_RATES=(0.05 0.06 0.07 0.08 0.09 0.10)

# Assert each graph file starts with 27
for gs in "${GRAPH_SEEDS[@]}"; do
    gf="profiles/graphs/random_n27_seed${gs}.txt"
    first=$(head -1 "$gf")
    if [[ "$first" != "27" ]]; then
        echo "error: $gf first line is '$first', expected '27'" >&2
        exit 1
    fi
done

mkdir -p "$OUT_DIR"
echo "loss_rate,graph_seed,channel_seed,num_nodes,floods,receivers_covered,receiver_opportunities,coverage,rx_attempts,rx_success,slots" > "$OUT_CSV"

total=$(( ${#LOSS_RATES[@]} * ${#GRAPH_SEEDS[@]} * ${#CHANNEL_SEEDS[@]} ))
done_n=0

for loss in "${LOSS_RATES[@]}"; do
    for gs in "${GRAPH_SEEDS[@]}"; do
        gf="profiles/graphs/random_n27_seed${gs}.txt"
        for cs in "${CHANNEL_SEEDS[@]}"; do
            cat > "$RUN_CFG" <<TOML
seed = ${cs}
phy_mode = "ci"
protocol = "pure_flood"
num_proposals = 200
snapshot_interval = 1000000
max_slots = 100000
quiet = false

[network]
num_nodes = 27
# IGNORED when graph_file is set: build_graph returns early (src/main.rs)
topology = "random"
loss_rate = ${loss}
graph_file = "${gf}"

[ci]
flood_repeats = 1
TOML

            out="$("$BIN" "$RUN_CFG")"
            line="$(printf '%s\n' "$out" | grep '^PURE_FLOOD ' || true)"
            if [[ -z "$line" ]]; then
                echo "error: no PURE_FLOOD line for loss=$loss gs=$gs cs=$cs" >&2
                printf '%s\n' "$out" >&2
                exit 1
            fi

            printf '%s\n' "$line" | awk -v loss="$loss" -v gs="$gs" -v cs="$cs" '
            {
                for (i = 2; i <= NF; i++) {
                    split($i, kv, "=")
                    v[kv[1]] = kv[2]
                }
                printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
                    loss, gs, cs, v["n"], v["floods"], v["covered"], v["opportunities"],
                    v["coverage"], v["rx_attempts"], v["rx_success"], v["slots"]
            }' >> "$OUT_CSV"

            done_n=$(( done_n + 1 ))
            if (( done_n % 50 == 0 )); then
                printf '\r  %4d/%4d  loss=%s gs=%s cs=%s ' "$done_n" "$total" "$loss" "$gs" "$cs"
            fi
        done
    done
done

printf '\r  %4d/%4d done\n' "$done_n" "$total"
rm -f "$RUN_CFG"
echo "wrote $OUT_CSV ($done_n runs)"
