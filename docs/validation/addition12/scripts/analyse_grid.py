#!/usr/bin/env python3
"""
Two-way variance decomposition and p* analysis for the graph/channel
decoupling grid (addition 12, step 7).

Uses ONLY Python 3 standard library: csv, math, statistics.
"""

import csv
import math
import os
import statistics

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GRID_CSV = os.path.join(REPO_ROOT, "docs", "validation", "addition12", "data", "coverage_grid.csv")
FINE_CSV = os.path.join(REPO_ROOT, "docs", "validation", "addition12", "data", "coverage_curve_fine.csv")
OUT_CSV = os.path.join(REPO_ROOT, "docs", "validation", "addition12", "data", "variance_decomposition.csv")

T_975_14 = 2.1447866879169273  # t(0.975, df=14)

LOSS_LEVELS = ["0.05", "0.06", "0.07", "0.08", "0.09", "0.10"]
SEEDS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
G = C = 15


def load_grid():
    """Return {loss: {(graph_seed, channel_seed): coverage}}."""
    data = {}
    with open(GRID_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            loss = row["loss_rate"]
            gs = int(row["graph_seed"])
            cs = int(row["channel_seed"])
            cov = float(row["coverage"])
            data.setdefault(loss, {})[(gs, cs)] = cov
    return data


def load_fine():
    """Return {loss: {seed: coverage}}."""
    data = {}
    with open(FINE_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            loss = row["loss_rate"]
            seed = int(row["seed"])
            cov = float(row["coverage"])
            data.setdefault(loss, {})[seed] = cov
    return data


def analyse_loss_level(grid_loss):
    """Two-way ANOVA decomposition for one loss level."""
    # Build y[g][c]
    y = {}
    for (gs, cs), cov in grid_loss.items():
        y.setdefault(gs, {})[cs] = cov

    graphs = sorted(y.keys())
    channels = sorted(list(y[graphs[0]].keys()))
    assert len(graphs) == G
    assert len(channels) == C

    # Grand mean
    all_vals = [y[g][c] for g in graphs for c in channels]
    ybar = statistics.mean(all_vals)

    # Row means (per graph, averaged over channels)
    ybar_g = {g: statistics.mean([y[g][c] for c in channels]) for g in graphs}

    # Column means (per channel, averaged over graphs)
    ybar_c = {c: statistics.mean([y[g][c] for g in graphs]) for c in channels}

    # SS
    ss_graph = C * sum((ybar_g[g] - ybar) ** 2 for g in graphs)
    ss_channel = G * sum((ybar_c[c] - ybar) ** 2 for c in channels)
    ss_resid = sum(
        (y[g][c] - ybar_g[g] - ybar_c[c] + ybar) ** 2
        for g in graphs
        for c in channels
    )

    df_graph = G - 1  # 14
    df_channel = C - 1  # 14
    df_resid = df_graph * df_channel  # 196

    ms_graph = ss_graph / df_graph
    ms_channel = ss_channel / df_channel
    ms_resid = ss_resid / df_resid

    ms_ratio = ms_graph / ms_channel if ms_channel > 0 else float("inf")

    # p* rule: t-interval over graph means
    graph_means = [ybar_g[g] for g in graphs]
    sd_graph_means = statistics.stdev(graph_means)
    half_width = T_975_14 * sd_graph_means / math.sqrt(G)
    grand_mean_of_graph_means = statistics.mean(graph_means)
    ci_lower = grand_mean_of_graph_means - half_width

    # Spreads
    graph_range = max(graph_means) - min(graph_means)
    channel_means = [ybar_c[c] for c in channels]
    channel_range = max(channel_means) - min(channel_means)

    return {
        "grand_mean": ybar,
        "ss_graph": ss_graph,
        "ss_channel": ss_channel,
        "ss_resid": ss_resid,
        "ms_graph": ms_graph,
        "ms_channel": ms_channel,
        "ms_resid": ms_resid,
        "ms_ratio": ms_ratio,
        "graph_mean_sd": sd_graph_means,
        "half_width": half_width,
        "ci_lower": ci_lower,
        "graph_range": graph_range,
        "channel_range": channel_range,
        "graph_min": min(graph_means),
        "graph_max": max(graph_means),
        "channel_min": min(channel_means),
        "channel_max": max(channel_means),
    }


def main():
    grid = load_grid()
    fine = load_fine()

    results = {}
    for loss in LOSS_LEVELS:
        assert loss in grid, f"loss {loss} not in grid"
        assert len(grid[loss]) == G * C, f"loss {loss}: expected {G*C} rows, got {len(grid[loss])}"
        results[loss] = analyse_loss_level(grid[loss])

    # ── Print variance decomposition ──
    print("=" * 80)
    print("VARIANCE DECOMPOSITION (two-way, no interaction)")
    print("=" * 80)
    print()
    print(f"{'loss':>6}  {'grand_mean':>10}  {'SS_graph':>12}  {'SS_channel':>12}  "
          f"{'SS_resid':>12}  {'MS_graph':>12}  {'MS_channel':>12}  {'MS_resid':>12}  "
          f"{'MS_g/MS_c':>10}")
    for loss in LOSS_LEVELS:
        r = results[loss]
        print(f"{loss:>6}  {r['grand_mean']:>10.6f}  {r['ss_graph']:>12.8f}  "
              f"{r['ss_channel']:>12.8f}  {r['ss_resid']:>12.8f}  {r['ms_graph']:>12.8f}  "
              f"{r['ms_channel']:>12.8f}  {r['ms_resid']:>12.8f}  {r['ms_ratio']:>10.2f}")

    # ── Print p* table ──
    print()
    print("=" * 80)
    print("p* TABLE (graph-level t-interval, t(0.975,14) = 2.1447866879169273)")
    print("=" * 80)
    print()
    print(f"{'loss':>6}  {'mean(ybar_g)':>12}  {'sd(ybar_g)':>12}  {'half_width':>12}  "
          f"{'ci_lower':>12}  {'>=0.999?':>8}")
    p_star = None
    for loss in LOSS_LEVELS:
        r = results[loss]
        ok = r["ci_lower"] >= 0.999
        flag = "YES" if ok else "no"
        if ok:
            p_star = loss
        print(f"{loss:>6}  {r['grand_mean']:>12.6f}  {r['graph_mean_sd']:>12.6f}  "
              f"{r['half_width']:>12.6f}  {r['ci_lower']:>12.6f}  {flag:>8}")

    print()
    if p_star is not None:
        print(f"p* = {p_star}")
    else:
        print("p* = NONE (no loss level has ci_lower >= 0.999)")

    # ── Print spread table ──
    print()
    print("=" * 80)
    print("SPREAD OF GRAPH vs CHANNEL MEANS")
    print("=" * 80)
    print()
    print(f"{'loss':>6}  {'g_min':>10}  {'g_max':>10}  {'g_range':>10}  "
          f"{'c_min':>10}  {'c_max':>10}  {'c_range':>10}  {'g/c ratio':>10}")
    for loss in LOSS_LEVELS:
        r = results[loss]
        gc_ratio = r["graph_range"] / r["channel_range"] if r["channel_range"] > 0 else float("inf")
        print(f"{loss:>6}  {r['graph_min']:>10.6f}  {r['graph_max']:>10.6f}  "
              f"{r['graph_range']:>10.6f}  {r['channel_min']:>10.6f}  {r['channel_max']:>10.6f}  "
              f"{r['channel_range']:>10.6f}  {gc_ratio:>10.2f}")

    # ── Fine sweep comparison ──
    print()
    print("=" * 80)
    print("FINE SWEEP (old methodology) vs GRID at shared loss levels 0.06-0.09")
    print("=" * 80)
    print()
    print("NOTE: row-by-row comparison is NOT meaningful. With graph_file set,")
    print("no RNG is consumed by graph construction, so the ChaCha8 stream starts")
    print("from a different point and the per-(seed,loss) numbers are not expected")
    print("to match. This is by design, not a bug.")
    print()
    shared_losses = ["0.06", "0.07", "0.08", "0.09"]
    print(f"{'loss':>6}  {'fine_mean':>10}  {'fine_sd':>10}  {'fine_ci_hw':>10}  "
          f"{'grid_mean':>10}  {'grid_sd':>10}  {'grid_ci_hw':>10}")
    for loss in shared_losses:
        # Fine sweep: 15 values (one per seed)
        fine_vals = [fine[loss][s] for s in SEEDS]
        fine_mean = statistics.mean(fine_vals)
        fine_sd = statistics.stdev(fine_vals)
        fine_hw = T_975_14 * fine_sd / math.sqrt(15)

        # Grid: use graph means (15 values)
        r = results[loss]
        grid_mean = r["grand_mean"]
        grid_sd = r["graph_mean_sd"]
        grid_hw = r["half_width"]

        print(f"{loss:>6}  {fine_mean:>10.6f}  {fine_sd:>10.6f}  {fine_hw:>10.6f}  "
              f"{grid_mean:>10.6f}  {grid_sd:>10.6f}  {grid_hw:>10.6f}")

    # ── Write variance_decomposition.csv ──
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "loss_rate", "grand_mean", "ss_graph", "ss_channel", "ss_resid",
            "ms_graph", "ms_channel", "ms_resid", "ms_ratio",
            "graph_mean_sd", "half_width", "ci_lower", "graph_range", "channel_range",
        ])
        for loss in LOSS_LEVELS:
            r = results[loss]
            writer.writerow([
                loss,
                f"{r['grand_mean']:.6f}",
                f"{r['ss_graph']:.8f}",
                f"{r['ss_channel']:.8f}",
                f"{r['ss_resid']:.8f}",
                f"{r['ms_graph']:.8f}",
                f"{r['ms_channel']:.8f}",
                f"{r['ms_resid']:.8f}",
                f"{r['ms_ratio']:.2f}",
                f"{r['graph_mean_sd']:.6f}",
                f"{r['half_width']:.6f}",
                f"{r['ci_lower']:.6f}",
                f"{r['graph_range']:.6f}",
                f"{r['channel_range']:.6f}",
            ])
    print()
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
