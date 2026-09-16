# Audit of Abstract and Key Manuscript Claims

## 1. Overview
This document audits six specific numeric claims from `paper/paper.tex` that
characterize the performance envelope and distributional properties of the
CTSim protocol evaluation:
1. Global maximum 2PC throughput ratio (`4.268x`, lines 167, 320)
2. Global maximum 2PC energy efficiency ratio (`5.987x`, lines 168, 321)
3. Historical residual ratios (`3.5234x` and `3.7776x`, line 1648)
4. TOM (CE) median cost as exact integer multiple of latency (line 2130)
5. Concurrency cost interquartile ranges (`7.2` against `9.0`, line 2140)
6. Latency-energy decoupling ratio ("about 1.3 times", line 2206)

---

## 2. Claim 1: Global Maximum Throughput Ratio (4.268x)

### Manuscript Sentence (lines 165-168 and 319-322)
```latex
preserving total order. Extensive slot-level simulation shows that the
pipeline sustains, on average, about 12 concurrent proposals for Paxos and
about 21 for 2PC, yielding 4.083x higher baseline throughput (global maximum
4.268x) and 5.672x better baseline per-decision energy efficiency (global
maximum 5.987x) than CE-based counterparts.
```

### Claim Interpretation and Search Set
- Metric: 2PC throughput ratio CI / CE.
- Protocols: `2pc_pipeline` (CI) vs `2pc_ce` (CE).
- Topology: `random`.
- Baseline reference point: N = 27, loss = 0.05 (ratio = 4.083x).
- Search set: all 20 configurations in the scalability sweep grid in
  `plots/scalability/results/sweep_summary.csv` across N in {6, 13, 27, 54, 188}
  and loss in {0.00, 0.05, 0.10, 0.20} (1800 rows total, 90 rows per cell).

### Aggregation Basis Comparison
At the maximising configuration (N = 27, loss = 0.00, random):
- **Basis A (ratio of 15-seed means):**
  `mean(thr_ci) / mean(thr_ce) = 0.176423 / 0.041335 = 4.268160` -> `4.268x`
  (MATCHES published figure).
- **Basis B (mean of 15 per-seed ratios):**
  `mean(thr_ci_i / thr_ce_i) = 4.270708` -> `4.271x` (DIFFERS).

Basis A is the authoritative aggregation basis used in the manuscript.

### Reproduction Script and Output
Source file: `plots/scalability/results/sweep_summary.csv`
```python
import pandas as pd
df = pd.read_csv("plots/scalability/results/sweep_summary.csv")
df["thr"] = df["committed"] / df["end_slot"].replace(0, 1)

rows = []
for (n, loss), g in df.groupby(["nodes", "loss_rate"]):
    ci = g[(g["protocol"] == "2pc_pipeline") & (g["phy"] == "ci")]
    ce = g[(g["protocol"] == "2pc_ce") & (g["phy"] == "ce")]
    if len(ci) > 0 and len(ce) > 0:
        ratio_a = ci["thr"].mean() / ce["thr"].mean()
        rows.append({"n": n, "loss": loss, "ratio_a": ratio_a})
res = pd.DataFrame(rows).sort_values("ratio_a", ascending=False)
```
Top 3 candidates across the scalability sweep grid (Basis A):
1. N = 27, loss = 0.00: ratio = 4.268160 (rounds to 4.268x)
2. N = 13, loss = 0.00: ratio = 4.250182 (rounds to 4.250x)
3. N =  6, loss = 0.00: ratio = 4.236629 (rounds to 4.237x)

The unique global maximum across the scalability grid is at N = 27, loss = 0.00.

### Verdict
**MATCH** (full precision: `4.268160`, Basis A).

---

## 3. Claim 2: Global Maximum Energy Efficiency Ratio (5.987x)

### Manuscript Sentence (lines 167-168 and 320-322)
```latex
and 5.672x better baseline per-decision energy efficiency (global maximum
5.987x) than CE-based counterparts.
```

### Claim Interpretation and Search Set
- Metric: 2PC per-decision energy ratio CE / CI, where per-decision energy is
  `(listen + flood) / committed`.
- Protocols: `2pc_ce` (CE) vs `2pc_pipeline` (CI).
- Topology: `random`.
- Baseline reference point: N = 27, loss = 0.05 (ratio = 5.672x).
- Search set: all 20 configurations in the scalability sweep grid in
  `plots/scalability/results/sweep_summary.csv` across N in {6, 13, 27, 54, 188}
  and loss in {0.00, 0.05, 0.10, 0.20} (1800 rows total, 90 rows per cell).

### Aggregation Basis Comparison
At the maximising configuration (N = 27, loss = 0.00, random):
- **Basis A (ratio of 15-seed means):**
  `mean(energy_ce) / mean(energy_ci) = 653.886000 / 109.208667 = 5.987492`
  -> `5.987x` (MATCHES published figure).
- **Basis B (mean of 15 per-seed ratios):**
  `mean(energy_ce_i / energy_ci_i) = 5.989324` -> `5.989x` (DIFFERS).

Basis A is the authoritative aggregation basis used in the manuscript.

### Reproduction Script and Output
Source file: `plots/scalability/results/sweep_summary.csv`
```python
import pandas as pd
df = pd.read_csv("plots/scalability/results/sweep_summary.csv")
df["energy"] = (df["listen"] + df["flood"]) / df["committed"].replace(0, 1)

rows = []
for (n, loss), g in df.groupby(["nodes", "loss_rate"]):
    ci = g[(g["protocol"] == "2pc_pipeline") & (g["phy"] == "ci")]
    ce = g[(g["protocol"] == "2pc_ce") & (g["phy"] == "ce")]
    if len(ci) > 0 and len(ce) > 0:
        ratio_a = ce["energy"].mean() / ci["energy"].mean()
        rows.append({"n": n, "loss": loss, "ratio_a": ratio_a})
res = pd.DataFrame(rows).sort_values("ratio_a", ascending=False)
```
Top 3 candidates across the scalability sweep grid (Basis A):
1. N = 27, loss = 0.00: ratio = 5.987492 (rounds to 5.987x)
2. N = 13, loss = 0.00: ratio = 5.984109 (rounds to 5.984x)
3. N = 13, loss = 0.05: ratio = 5.863042 (rounds to 5.863x)

The unique global maximum across the scalability grid is at N = 27, loss = 0.00.

### Verdict
**MATCH** (full precision: `5.987492`, Basis A).

---

## 4. Claim 3: Historical Residual Ratios (3.5234x and 3.7776x)

### Manuscript Sentence (lines 1647-1653)
```latex
Historical width-4 windows produced residual ratios 3.5234x at $\Nnodes=180$
for 2PC and 3.7776x at $\Nnodes=188$ for Paxos. At $\Nnodes=180$, the historical
2PC residual 3.523 agrees closely with the new sweep constant gap 3.508, a
difference of -0.015. The Paxos anchor at $\Nnodes=188$ lies outside this
sweep's grid and is therefore not compared under the uniform $W=10$ procedure.
```

### Claim Interpretation and N-Grid Disambiguation
- Metric: constant-gap residual ratios of the density-scaling power law.
- Protocols: 2PC at N = 180 and Paxos at N = 188.
- Topology: dense graphs with diameter 2.
- Data origin: historical width-4 search window residuals ($W=4$).
- N-grid resolution:
  - The scalability sweep (`plots/scalability/results/sweep_summary.csv`) is on
    `random` topology across N in {6, 13, 27, 54, 188}.
  - The dense-graph power-law sweep (`docs/validation/addition15/`) was run
    on `dense` graphs across N in {60, 90, 120, 150, 180, 240} with W=10.
  - The manuscript sentence explicitly contrasts the historical W=4 anchors
    (3.5234x at N=180; 3.7776x at N=188) against the uniform W=10 procedure
    (where 2PC at N=180 yields 3.508, difference -0.015).
  - The figures 3.5234x and 3.7776x are historical width-4 anchor artifacts
    supported by `docs/validation/addition15/README.md:21-27` and
    `docs/validation/addition15/scripts/analyze_n_sweep.py:164`.

### Verdict
**SOURCED** (supported by `docs/validation/addition15/README.md:21-27`).

---

## 5. Claim 4: TOM (CE) Median Cost Integer Multiple of Latency

### Manuscript Sentence (lines 2128-2131)
```latex
TOM over \CE{} occupies an intermediate position, its median decision costing
135 node-slots, above every \CI{} median and far below the two vote-based \CE{}
protocols; that median is exactly $\Nnodes$ times the median \CE{} latency
of 5 slots.
```

### Claim Interpretation
- Metric: median per-decision radio energy (node-slots) and median latency
  (slots).
- Protocol: `TOM (CE)`.
- Topology: `random`, N = 27, loss = 0.05, 15 seeds (1500 decisions).
- Aggregation: median over 1500 individual decisions.

### Reproduction Script and Output
Source file: `docs/validation/paper-audit/sources/per_decision_energy.csv`
```python
import pandas as pd
df = pd.read_csv("docs/validation/paper-audit/sources/per_decision_energy.csv")
tom_ce = df[df["protocol"] == "TOM (CE)"]
median_energy = tom_ce["energy_node_slots"].median()
median_latency = median_energy / 27
```
Output:
- Total decisions: 1500
- Median per-decision energy: 135.0 node-slots
- Divided by N = 27: exactly 5.0 slots
- Energy distribution across decisions:
  - 81 node-slots (3 slots): 2 decisions
  - 108 node-slots (4 slots): 573 decisions
  - 135 node-slots (5 slots): 838 decisions
  - 162 node-slots (6 slots): 85 decisions
  - 189 node-slots (7 slots): 1 decision
  - 243 node-slots (9 slots): 1 decision
Under CE, the radio is on across all N nodes every slot ($E_i = N \times L_i$).
The median is exactly $27 \times 5 = 135$ node-slots.

### Evidence Freshness Risk (Task 4)
- `docs/validation/paper-audit/sources/per_decision_energy.csv` was last
  committed in `913ea33`.
- `git merge-base --is-ancestor cf05dd8 913ea33` returns non-zero
  (`PREDATES-FIX`).
- The evidence file predates the post-issue-257 sweep regeneration (`cf05dd8`).
- For TOM (CE), protocol logic and CE phy are unaffected by issue 257 (which was
  confined to `paxos_pipeline`), but the artifact itself remains an
  unregenerated pre-fix file. Recorded as an open risk.

### Verdict
**SOURCED** (supported by
`docs/validation/paper-audit/sources/per_decision_energy.csv:7486-8985`;
slice corrected in step 2.35: the TOM (CE) block spans 7486-8985, while
2713-4212 is the 2PC (CI) and TOM (CI) block).

---

## 6. Claim 5: Concurrency Interquartile Ranges (7.2 against 9.0)

### Manuscript Sentence (lines 2139-2142)
```latex
Spread is not monotone in concurrency---Paxos carries eleven times TOM's
concurrency in a narrower interquartile range, 7.2 against 9.0---so it is the
median and the upper percentile, not the width of the box, that measure what
the pipeline costs.
```

### Claim Interpretation
- Metric: Interquartile range ($Q3 - Q1$) of per-decision radio energy
  (node-slots).
- Protocols: `Paxos (CI)` vs `TOM (CI)`.
- Topology: `random`, N = 27, loss = 0.05, 15 seeds (1500 decisions each).
- Aggregation: 75th percentile minus 25th percentile across 1500 decisions.

### Reproduction Script and Output
Source file: `docs/validation/paper-audit/sources/per_decision_energy.csv`
```python
import pandas as pd
import numpy as np
df = pd.read_csv("docs/validation/paper-audit/sources/per_decision_energy.csv")
for p in ["TOM (CI)", "Paxos (CI)"]:
    sub = df[df["protocol"] == p]["energy_node_slots"]
    q1 = np.percentile(sub, 25)
    q3 = np.percentile(sub, 75)
    print(p, "Q1:", q1, "Q3:", q3, "IQR:", q3 - q1)
```
Output:
- TOM (CI): Q1 = 83.0000, Q3 = 92.0000, IQR = 9.0000 (rounds to 9.0)
- Paxos (CI): Q1 = 86.3077, Q3 = 93.4808, IQR = 7.1731 (rounds to 7.2)

### Evidence Freshness Risk (Task 4)
- Source file `per_decision_energy.csv` has status `PREDATES-FIX`
  (commit `913ea33`, ancestor of `cf05dd8`).
- Paxos (CI) was directly affected by the issue 257 quorum defect. While the
  interquartile range reproduces exactly from the committed file, this file
  predates the issue 257 fix and has not been regenerated. Recorded as an
  open risk.

### Verdict
**SOURCED** (supported by
`docs/validation/paper-audit/sources/per_decision_energy.csv:2-1501,2986-4485`;
slice corrected in step 2.35: 2-1501 is the Paxos (CI) block and 2986-4485
the TOM (CI) block; the previously cited 2713-4212 mixes 2PC (CI) and TOM (CI)
rows).

---

## 7. Claim 6: Latency-Energy Decoupling Ratio ("about 1.3 times")

### Manuscript Sentence (lines 2204-2206)
```latex
The central observation is that between TOM and 2PC over \CI{} the latency
column grows by roughly \textbf{27 times} while the energy
column grows by only about \textbf{1.3 times}.
```

### Claim Interpretation
- Metric: ratio of per-decision energy between 2PC (CI) and TOM (CI).
- Protocols: `2pc_pipeline` (CI) vs `tom_pipeline` (CI).
- Topology: `random`, N = 27, loss = 0.05, 15 seeds.
- Aggregation: ratio of 15-seed arithmetic mean per-decision energy.

### Reproduction Script and Output
Source file: `plots/scalability/results/sweep_summary.csv:56-58`
```python
import pandas as pd
df = pd.read_csv("plots/scalability/results/sweep_summary.csv")
sub = df[(df["nodes"] == 27) & (df["loss_rate"] == 0.05)]
tom = sub[(sub["protocol"] == "tom_pipeline") & (sub["phy"] == "ci")]
twopc = sub[(sub["protocol"] == "2pc_pipeline") & (sub["phy"] == "ci")]

tom_e = ((tom["listen"] + tom["flood"]) / tom["committed"]).mean()
twopc_e = ((twopc["listen"] + twopc["flood"]) / twopc["committed"]).mean()
ratio = twopc_e / tom_e
```
Output:
- TOM (CI) mean energy: 87.991333 node-slots
- 2PC (CI) mean energy: 115.843797 node-slots
- Ratio: 1.316536 (rounds to 1.3 times)
Also in Table VI (`tab:escape`, line 2196):
$115.8 / 88.0 = 1.3159 \approx 1.3x$.

### Verdict
**MATCH** (full precision: `1.316536`).
