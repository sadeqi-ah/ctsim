#!/usr/bin/env python3
"""Independent recomputation of every number quoted in patch_spec.md.

Decision 88: a generator cannot be its own verifier. make_patch_spec.py slices
its "current text" blocks straight out of paper/paper.tex, so byte-exactness of
those blocks is an INVARIANT of that script and never a finding. This script is
the other half of the pair: it opens the DATA, recomputes every quantity the
spec's replacement blocks assert, and prints for each one the file, the filter
and the column it came from (decisions 83 and 90).

Decision 89: if any check fails, no report is written and the exit status is 1.

Two constants here are not measurements and are labelled as such:
  T975_14  Student t at 0.975 with 14 df -- distributional, not a datum
  CAP      ce.max_round_slots = 512, which lives in sweep_topology.toml and is
           not present in any CSV column

Run from anywhere inside the repository:
    python3 docs/validation/addition7/scripts/check_patch_spec.py

Overrides, all optional: CTSIM_ROOT, CTSIM_SPEC, CTSIM_SWEEP_SCAL,
CTSIM_A9DIR, CTSIM_SWEEP_TOPO, CTSIM_REPORT. Defaults are repository paths
(decision 124), so what is checked is what is published.
"""
import csv
import os
import re
import statistics as st
import subprocess
import sys

T975_14 = 2.1447866879169273   # not a datum: Student t, 0.975, 14 df
CAP = 512                      # not a datum: ce.max_round_slots from the TOML


def _root():
    if os.environ.get("CTSIM_ROOT"):
        return os.environ["CTSIM_ROOT"]
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()


ROOT = _root()
SPEC = os.environ.get(
    "CTSIM_SPEC", os.path.join(ROOT, "docs", "validation", "patch_spec.md"))
SWEEP_SCAL = os.environ.get(
    "CTSIM_SWEEP_SCAL", os.path.join(ROOT, "plots", "scalability", "results",
                                     "sweep_summary.csv"))
A9DIR = os.environ.get(
    "CTSIM_A9DIR", os.path.join(ROOT, "docs", "validation", "addition9",
                                "data"))
SWEEP_TOPO = os.environ.get(
    "CTSIM_SWEEP_TOPO", os.path.join(A9DIR, "sweep_summary_topology.csv"))
# Deliberately outside the repository (decisions 107 and 119): this report is a
# derived artefact and is not committed.
REPORT = os.environ.get("CTSIM_REPORT", "/tmp/spec_recompute_report.tsv")

fail = []
Q = []


def rec(name, value, prov):
    """Record one recomputed quantity together with its provenance."""
    Q.append((name, value, prov))
    return value


def need(path, what):
    if os.path.exists(path):
        return True
    fail.append("MISSING DATA FILE: %s  (needed for: %s)" % (path, what))
    return False


def rd(path):
    fh = open(path, newline="")
    rows = list(csv.DictReader(fh))
    fh.close()
    return rows


def halfwidth(xs):
    return T975_14 * st.stdev(xs) / (len(xs) ** 0.5)


def hdr(t):
    print("")
    print("=" * 72)
    print(t)
    print("=" * 72)


def energy_per_dec(r):
    """(listen+flood)/committed, or None when the arm committed nothing.

    The None case is real: line/2pc_pipeline commits zero on fourteen of
    fifteen seeds, which is what made an earlier scratch script divide by zero.
    """
    c = int(r["committed"])
    if c == 0:
        return None
    return (int(r["listen"]) + int(r["flood"])) / c


ARMS = [("TOM (CI)", "tom_pipeline"), ("Paxos (CI)", "paxos_pipeline"),
        ("2PC (CI)", "2pc_pipeline"), ("TOM (CE)", "tom_ce"),
        ("Paxos (CE)", "paxos_ce"), ("2PC (CE)", "2pc_ce")]
TWINS = [("TOM", "tom_pipeline", "tom_ce"),
         ("Paxos", "paxos_pipeline", "paxos_ce"),
         ("2PC", "2pc_pipeline", "2pc_ce")]

print("ROOT   = %s" % ROOT)
print("spec   = %s" % SPEC)
print("scal   = %s" % SWEEP_SCAL)
print("topo   = %s" % SWEEP_TOPO)
print("a9dir  = %s" % A9DIR)
print("report = %s" % REPORT)
print("")
print("constants that are NOT data:")
print("  t(0.975,14)     = %.16f  (Student t, distributional)" % T975_14)
print("  max_round_slots = %d  (sweep_topology.toml [ce]; in no CSV)" % CAP)

ok_scal = need(SWEEP_SCAL, "baseline cell, escape triple")
ok_topo = need(SWEEP_TOPO, "topology sweep")

# ============================================================ A: baseline cell
CELL = []
if ok_scal:
    hdr("A. baseline cell: nodes == 27 and loss_rate == 0.05")
    allrows = rd(SWEEP_SCAL)
    CELL = [r for r in allrows
            if int(r["nodes"]) == 27
            and abs(float(r["loss_rate"]) - 0.05) < 1e-12]
    print("rows in file: %d    rows in cell: %d    topologies present: %s"
          % (len(allrows), len(CELL),
             sorted(set(r["topology"] for r in CELL))))
    if len(CELL) != 90:
        fail.append("BASELINE CELL IS %d ROWS, EXPECTED 90 (6 arms x 15 seeds)"
                    % len(CELL))
    print("")
    print("%-11s %3s %9s %8s %10s %10s %8s %9s %12s %12s"
          % ("arm", "n", "commit%", "thr", "latency", "E/dec", "eff", "end",
             "depth(mop)", "depth(pom)"))
    for label, proto in ARMS:
        rs = [r for r in CELL if r["protocol"] == proto]
        if len(rs) != 15:
            fail.append("ARM %s HAS %d SEEDS, EXPECTED 15" % (label, len(rs)))
            continue
        p = ("plots/scalability/results/sweep_summary.csv, "
             "nodes==27 & loss_rate==0.05, protocol==%s, 15 seeds" % proto)
        cr = rec("cell.%s.commit_rate_pct" % label,
                 st.mean([100.0 * int(r["committed"]) / int(r["proposals"])
                          for r in rs]),
                 p + "; 100*committed/proposals per row, then mean")
        thr_i = [int(r["committed"]) / int(r["end_slot"]) for r in rs]
        thr = rec("cell.%s.throughput" % label, st.mean(thr_i),
                  p + "; committed/end_slot per row, then mean")
        lat_i = [float(r["avg_latency"]) for r in rs]
        lat = rec("cell.%s.latency_slots" % label, st.mean(lat_i),
                  p + "; mean of the avg_latency column")
        ed_i = [energy_per_dec(r) for r in rs]
        mop = rec("cell.%s.depth_mean_of_products" % label,
                  st.mean([t * l for t, l in zip(thr_i, lat_i)]),
                  p + "; mean of per-seed throughput*latency "
                      "<-- this is the estimator the manuscript prints")
        pom = rec("cell.%s.depth_product_of_means" % label, thr * lat,
                  p + "; product of the two column means")
        if None in ed_i:
            fail.append("ARM %s HAS %d ZERO-COMMIT SEED(S): energy per "
                        "decision is undefined" % (label, ed_i.count(None)))
            continue
        ed = rec("cell.%s.energy_per_dec" % label, st.mean(ed_i),
                 p + "; (listen+flood)/committed per row, then mean")
        eff = rec("cell.%s.efficiency" % label,
                  st.mean([1000.0 * t / e for t, e in zip(thr_i, ed_i)]),
                  p + "; 1000*throughput/energy_per_dec per row, then mean")
        end = rec("cell.%s.end_slot" % label,
                  st.mean([int(r["end_slot"]) for r in rs]),
                  p + "; mean of the end_slot column")
        print("%-11s %3d %9.4f %8.4f %10.4f %10.4f %8.4f %9.2f %12.6f %12.6f"
              % (label, len(rs), cr, thr, lat, ed, eff, end, mop, pom))
    print("")
    print("depth(mop) = mean of per-seed products; depth(pom) = product of "
          "means.")
    print("They are different estimators. The manuscript prints mop and does "
          "not say so.")

# ==================================================== B: the escape triple
if ok_scal and len(CELL) == 90:
    hdr("B. escape triple: CE energy per decision / CI energy per decision")
    print("%-7s %12s %12s %14s %12s %4s"
          % ("twin", "RoM", "RoS", "mean-of-r", "halfwidth", "n"))
    for name, ci, ce in TWINS:
        a = sorted([r for r in CELL if r["protocol"] == ci],
                   key=lambda r: int(r["seed"]))
        b = sorted([r for r in CELL if r["protocol"] == ce],
                   key=lambda r: int(r["seed"]))
        if [r["seed"] for r in a] != [r["seed"] for r in b]:
            fail.append("SEED SETS DIFFER for twin %s: pairing impossible"
                        % name)
            continue
        eci = [energy_per_dec(r) for r in a]
        ece = [energy_per_dec(r) for r in b]
        if None in eci or None in ece:
            fail.append("TWIN %s HAS A ZERO-COMMIT SEED: ratio undefined"
                        % name)
            continue
        p = ("plots/scalability/results/sweep_summary.csv, "
             "nodes==27 & loss_rate==0.05, %s over %s, 15 paired seeds"
             % (ce, ci))
        rom = rec("escape.%s.ratio_of_means" % name,
                  st.mean(ece) / st.mean(eci),
                  p + "; mean(E_CE)/mean(E_CI)")
        sci = (sum(int(r["listen"]) + int(r["flood"]) for r in a)
               / sum(int(r["committed"]) for r in a))
        sce = (sum(int(r["listen"]) + int(r["flood"]) for r in b)
               / sum(int(r["committed"]) for r in b))
        ros = rec("escape.%s.ratio_of_sums" % name, sce / sci,
                  p + "; sum(listen+flood)/sum(committed) per arm, then ratio")
        rr = [y / x for x, y in zip(eci, ece)]
        mor = rec("escape.%s.mean_of_ratios" % name, st.mean(rr),
                  p + "; per-seed ratio, then mean")
        hw = rec("escape.%s.halfwidth95" % name, halfwidth(rr),
                 p + "; t(0.975,14)*stdev/sqrt(15) over the per-seed ratios")
        print("%-7s %12.6f %12.6f %14.6f %12.6f %4d"
              % (name, rom, ros, mor, hw, len(rr)))
    print("")
    print("The published half-widths 0.018025 / 0.075337 / 0.298615 are not "
          "reproduced by")
    print("any of these three estimators; the paired per-seed ratio gives the "
          "column above.")

# ================================================ C: topology sweep, 450 rows
trows = []
if ok_topo:
    hdr("C. topology sweep: 5 topologies x 6 arms x 15 seeds")
    trows = rd(SWEEP_TOPO)
    print("rows: %d    topologies: %s"
          % (len(trows), sorted(set(r["topology"] for r in trows))))
    if len(trows) != 450:
        fail.append("TOPOLOGY SWEEP IS %d ROWS, EXPECTED 450" % len(trows))
    tovals = sorted(set(int(r["timed_out"]) for r in trows))
    print("distinct timed_out values over all rows: %s" % tovals)
    rec("topo.timed_out_max",
        max(int(r["timed_out"]) for r in trows),
        "addition9/data/sweep_summary_topology.csv; max of the timed_out "
        "column over all 450 rows")
    if tovals != [0]:
        fail.append("timed_out IS NOT IDENTICALLY ZERO: %s -- decision 112 "
                    "rests on it being zero" % tovals)
    else:
        print("timed_out is identically 0: decision 112 is now mechanical, "
              "not an assertion.")
    print("")
    print("%-13s %-11s %3s %9s %8s %10s %11s %8s %10s %12s %12s"
          % ("topology", "arm", "n", "commit%", "thr", "latency", "E/dec",
             "eff", "end", "depth(mop)", "depth(pom)"))
    for topo in sorted(set(r["topology"] for r in trows)):
        for label, proto in ARMS:
            rs = [r for r in trows
                  if r["topology"] == topo and r["protocol"] == proto]
            if len(rs) != 15:
                fail.append("TOPOLOGY %s ARM %s HAS %d SEEDS, EXPECTED 15"
                            % (topo, label, len(rs)))
                continue
            k = "topo.%s.%s" % (topo, proto)
            p = ("addition9/data/sweep_summary_topology.csv, topology==%s, "
                 "protocol==%s, 15 seeds" % (topo, proto))
            cr = rec(k + ".commit_rate_pct",
                     st.mean([100.0 * int(r["committed"])
                              / int(r["proposals"]) for r in rs]),
                     p + "; 100*committed/proposals per row, then mean")
            thr_i = [int(r["committed"]) / int(r["end_slot"]) for r in rs]
            thr = rec(k + ".throughput", st.mean(thr_i),
                      p + "; committed/end_slot per row, then mean")
            lat_i = [float(r["avg_latency"]) for r in rs]
            lat = rec(k + ".latency_slots", st.mean(lat_i),
                      p + "; mean of the avg_latency column")
            end = rec(k + ".end_slot",
                      st.mean([int(r["end_slot"]) for r in rs]),
                      p + "; mean of the end_slot column")
            mop = rec(k + ".depth_mean_of_products",
                      st.mean([t * l for t, l in zip(thr_i, lat_i)]),
                      p + "; mean of per-seed throughput*latency")
            pom = rec(k + ".depth_product_of_means", thr * lat,
                      p + "; product of the two column means")
            ed_i = [energy_per_dec(r) for r in rs]
            if None in ed_i:
                # Expected, and not a failure: line/2pc_pipeline commits zero
                # on fourteen of fifteen seeds. Decision 96: do not invent a
                # per-decision cost for an arm that made no decision.
                print("%-13s %-11s %3d %9.4f %8.4f %10.4f %11s %8s %10.2f "
                      "%12.6f %12.6f"
                      % (topo, label, len(rs), cr, thr, lat,
                         "undef(%d)" % ed_i.count(None), "undef", end,
                         mop, pom))
                continue
            ed = rec(k + ".energy_per_dec", st.mean(ed_i),
                     p + "; (listen+flood)/committed per row, then mean")
            eff = rec(k + ".efficiency",
                      st.mean([1000.0 * t / e
                               for t, e in zip(thr_i, ed_i)]),
                      p + "; 1000*throughput/energy_per_dec per row, "
                          "then mean")
            print("%-13s %-11s %3d %9.4f %8.4f %10.4f %11.4f %8.4f %10.2f "
                  "%12.6f %12.6f"
                  % (topo, label, len(rs), cr, thr, lat, ed, eff, end,
                     mop, pom))
    print("")
    print("%-13s %10s %10s %10s   (decision 115: a triple without its "
          "topology is meaningless)" % ("topology", "TOM", "Paxos", "2PC"))
    for topo in sorted(set(r["topology"] for r in trows)):
        cells = []
        for name, ci, ce in TWINS:
            a = [r for r in trows
                 if r["topology"] == topo and r["protocol"] == ci]
            b = [r for r in trows
                 if r["topology"] == topo and r["protocol"] == ce]
            eci = [energy_per_dec(r) for r in a]
            ece = [energy_per_dec(r) for r in b]
            if None in eci or None in ece:
                cells.append("undef")
                continue
            v = rec("topo.%s.%s.ce_over_ci" % (topo, name),
                    st.mean(ece) / st.mean(eci),
                    "addition9/data/sweep_summary_topology.csv, topology==%s, "
                    "%s over %s, 15 seeds; mean(E_CE)/mean(E_CI)"
                    % (topo, ce, ci))
            cells.append("%.4f" % v)
        print("%-13s %10s %10s %10s" % (topo, cells[0], cells[1], cells[2]))

# ======================================= D: addition9 per-run proposal ledgers
hdr("D. addition9 ledgers: the orphan span and the residual identity")
print("CAP = %d is config, not data. The law tested is "
      "orphan == aborted * CAP." % CAP)
print("")
print("%-6s %5s %6s %5s %5s %5s %8s %8s %7s %14s %10s %10s"
      % ("proto", "seed", "props", "comm", "abrt", "t/o", "sum_L", "end",
         "orphan", "d", "res %", "f %"))
for proto in ["tom", "paxos", "2pc"]:
    for seed in [23, 37]:
        fn = "results_%s_ce_line_n27_loss05_seed%d.csv" % (proto, seed)
        path = os.path.join(A9DIR, fn)
        if not need(path, "orphan law for %s seed %d" % (proto, seed)):
            continue
        rows = rd(path)
        oc = [r["outcome"] for r in rows]
        comm, abrt, tout = (oc.count("committed"), oc.count("aborted"),
                            oc.count("timed_out"))
        sumL = sum(int(r["latency"]) for r in rows
                   if r["outcome"] == "committed")
        end = max(int(r["end_slot"]) for r in rows)
        orphan = end - sumL
        p = ("addition9/data/%s; outcome and latency columns over %d "
             "proposals" % (fn, len(rows)))
        k = "a9.%s.%d" % (proto, seed)
        rec(k + ".committed", comm, p + "; count of outcome==committed")
        rec(k + ".aborted", abrt, p + "; count of outcome==aborted")
        rec(k + ".sum_latency", sumL,
            p + "; sum of latency over committed proposals")
        rec(k + ".end_slot", end, p + "; max of the end_slot column")
        rec(k + ".orphan_span", orphan, p + "; end_slot - sum_latency")
        if tout:
            fail.append("%s HAS %d timed_out PROPOSALS: decision 112 says the "
                        "CE shortfall is an ABORT at the round cap"
                        % (fn, tout))
        if orphan != abrt * CAP:
            fail.append("ORPHAN LAW BROKEN in %s: orphan %d != aborted %d * "
                        "CAP %d" % (fn, orphan, abrt, CAP))
        d = sumL / end
        res = 1.0 / d - 1.0
        leak = orphan / end
        rec(k + ".depth", d, p + "; sum_latency/end_slot (Little's law)")
        rec(k + ".res_pct", 100.0 * res, p + "; 100*(1/d - 1)")
        rec(k + ".f_pct", 100.0 * leak, p + "; 100*orphan_span/end_slot")
        if abs(res - leak / (1.0 - leak)) > 1e-12:
            fail.append("IDENTITY res == f/(1-f) BROKEN in %s" % fn)
        print("%-6s %5d %6d %5d %5d %5d %8d %8d %7d %14.10f %10.6f %10.6f"
              % (proto, seed, len(rows), comm, abrt, tout, sumL, end, orphan,
                 d, 100.0 * res, 100.0 * leak))
print("")
print("res == f/(1-f) == 1/d - 1 holds to 1e-12 on every run above.")
print("Decision 92: the denominator is Little's-law depth, never the commit "
      "rate --")
print("both departing seeds commit exactly 99, so a commit-rate denominator "
      "is void.")

# ============================== E: the 15-seed group mean the manuscript needs
if ok_topo and trows:
    hdr("E. line / 2pc_ce over all 15 seeds: the group residual")
    rs = sorted([r for r in trows if r["topology"] == "line"
                 and r["protocol"] == "2pc_ce"], key=lambda r: int(r["seed"]))
    print("seeds: %d" % len(rs))
    print("")
    print("%6s %6s %6s %8s %8s %14s %10s"
          % ("seed", "comm", "abrt", "end", "orphan", "d", "res %"))
    rr = []
    for r in rs:
        seed, abrt = int(r["seed"]), int(r["aborted"])
        end = int(r["end_slot"])
        # The sweep CSV stores no sum_latency, so reconstruct it from the law
        # proved run-by-run in section D: every aborted proposal contributes
        # exactly CAP slots of orphan span.
        orphan = abrt * CAP
        sumL = end - orphan
        d = sumL / end
        res = 1.0 / d - 1.0
        rr.append(res)
        rec("topo.line.2pc_ce.seed%d.res_pct" % seed, 100.0 * res,
            "addition9/data/sweep_summary_topology.csv, topology==line, "
            "protocol==2pc_ce, seed==%d; orphan = aborted*CAP, "
            "d = (end_slot-orphan)/end_slot, res = 1/d - 1" % seed)
        print("%6d %6d %6d %8d %8d %14.10f %10.6f"
              % (seed, int(r["committed"]), abrt, end, orphan, d,
                 100.0 * res))
    gm = rec("topo.line.2pc_ce.group_res_pct", 100.0 * st.mean(rr),
             "addition9/data/sweep_summary_topology.csv, topology==line, "
             "protocol==2pc_ce, 15 seeds; mean of the per-seed residuals")
    print("")
    print("group mean over %d seeds: %.8f %%" % (len(rr), gm))
    both = [q for q in Q if q[0] in ("a9.2pc.23.res_pct", "a9.2pc.37.res_pct")]
    for name, v, _ in both:
        seedk = "topo.line.2pc_ce.seed%s.res_pct" % name.split(".")[2]
        other = [q[1] for q in Q if q[0] == seedk]
        if other and abs(other[0] - v) > 1e-6:
            fail.append("SWEEP AND LEDGER DISAGREE for %s: %.8f vs %.8f"
                        % (name, other[0], v))
    print("The two seeds that also have per-run ledgers agree with section D "
          "to 1e-6.")

# ==================================== F: literal audit of the rendered spec
def sig(s):
    t = s.lstrip("-").replace(".", "").lstrip("0")
    return len(t)


if need(SPEC, "literal audit of the replacement blocks"):
    hdr("F. literal audit: every decimal in the spec's replacement blocks")
    text = open(SPEC).read()
    blocks = re.findall(
        r"\*\*Replacement text:\*\*\n\n```latex\n(.*?)\n```", text, re.S)
    body = "\n".join(blocks)
    print("replacement blocks found: %d    characters: %d"
          % (len(blocks), len(body)))
    if not blocks:
        fail.append("NO REPLACEMENT BLOCKS FOUND IN %s: the audit would "
                    "vacuously pass" % SPEC)

    def occurs(s):
        return re.search(r"(?<![0-9.])" + re.escape(s) + r"(?![0-9])", body)

    matched, absent = [], []
    for name, val, prov in Q:
        if val is None:
            continue
        hit = None
        for dp in range(6, 0, -1):
            s = "%.*f" % (dp, val)
            # Decision 121: a one- or two-digit rendering matches almost any
            # LaTeX table by accident. Only three significant digits or more
            # count as agreement.
            if sig(s) >= 3 and occurs(s):
                hit = s
                break
        if hit:
            matched.append((name, val, hit))
        else:
            absent.append((name, val))
    # Charge 101, second incarnation, caught in the rebuild: sig() counts a
    # zero-padded "1.00" as three significant digits, so two DIFFERENT
    # quantities -- a depth of exactly 1.000000 and one of 1.002085 -- both
    # claim the same printed literal. A literal claimed by more than one
    # distinct value confirms neither of them, so it is not a source and goes
    # back into the residue.
    claim = {}
    for name, val, hit in matched:
        claim.setdefault(hit, {})[round(val, 9)] = name
    ambiguous = sorted(h for h, v in claim.items() if len(v) > 1)
    sourced = set(h for h, v in claim.items() if len(v) == 1)
    unambiguous = [m for m in matched if m[2] in sourced]
    lits = set(re.findall(r"(?<![0-9.])\d+\.\d+(?![0-9])", body))
    residue = sorted(l for l in lits if l not in sourced)
    print("")
    print("recomputed quantities:                           %d" % len(Q))
    print("  claiming a literal at >=3 significant digits:  %d" % len(matched))
    print("  of those, claims that are UNAMBIGUOUS:         %d"
          % len(unambiguous))
    print("  recomputed but absent from the spec:           %d" % len(absent))
    print("distinct decimal literals in the blocks:         %d" % len(lits))
    print("  claimed by two or more distinct values:        %d" % len(ambiguous))
    print("  with no unambiguous recomputed source:         %d" % len(residue))
    if ambiguous:
        print("")
        print("AMBIGUOUS literals -- each claimed by more than one distinct")
        print("recomputed value, so it confirms none of them:")
        for h in ambiguous:
            print("  %-10s claimed by %s" % (h, sorted(claim[h].values())))
    print("")
    print("first 24 unambiguous matches:")
    for name, val, hit in unambiguous[:24]:
        print("  %-46s %14.6f  printed as %s" % (name, val, hit))
    print("")
    print("RESIDUE -- decision 126: spec v3 may not ship while this list is "
          "non-empty:")
    print("  %s" % ", ".join(residue))
    rec("audit.residue_count", len(residue),
        "%s; decimal literals in replacement blocks with no recomputed "
        "source at >=3 significant digits" % SPEC)

# ===================================================================== SUMMARY
hdr("SUMMARY")
print("quantities recomputed from data: %d" % len(Q))
print("checks failed: %d" % len(fail))
for f in fail:
    print("  !! %s" % f)
if fail:
    print("")
    print("NOTHING WRITTEN: %d check(s) failed (decision 89)." % len(fail))
    print("No report was created or updated at %s." % REPORT)
    sys.exit(1)
print("  all clean")
fh = open(REPORT, "w")
fh.write("quantity\tvalue\tprovenance\n")
for name, val, prov in Q:
    fh.write("%s\t%s\t%s\n" % (name, "" if val is None else repr(val), prov))
fh.close()
print("")
print("wrote %s" % REPORT)
print("%d quantities, each with the file, the filter and the column it came "
      "from." % len(Q))
