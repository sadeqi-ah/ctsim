# Numeric audit of `paper/paper.tex`

**Summary: 65 distinct numeric claims examined — MATCH 38 / MISMATCH 16 / UNSOURCED 11.** Base: `main` at `cdc2f818af6b7b48cf05abfab293cd470a046335`. Verdicts use only the source precedence requested for this audit. A paper range is one distinct claim when adjacent values form one comparison, table row, or interval.

## Addition 15 fits, anchors, predictions, calibration, tests

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| current slopes, CIs, AIC, R² absent | — | 2PC `0.13733 [0.13101, 0.14365]`, AIC `4.8`, R² `0.998`; Paxos `0.12409 [0.11596, 0.13221]`, AIC `20.4`, R² `0.996` | `docs/validation/addition15/data/fits.csv:3,11`; `docs/validation/addition15/README.md:72,86` | UNSOURCED |
| withdrawn `0.13797`, `0.12264`, AIC `8.9`, `26.0` absent | — | values withdrawn; no occurrence | `paper/paper.tex` grep below | MATCH |
| published anchors absent | — | 2PC `3.5234x` at n=180; Paxos `3.7776x` at n=188 | `docs/validation/addition15/README.md:21-27` | MATCH (anchor only) |
| reference slots absent | — | `100.0` for `2pc_ce`; `57.8` for `paxos_ce` | `docs/validation/addition15/README.md:21-27` | MATCH (anchor only) |
| blind prediction A2 `475 ms`; error `TBD` | 1327,1334 | `42.4407` slots against `100.0`; fails | `docs/validation/addition13/README.md:89-99,115-121` | MISMATCH |
| blind prediction Paxos `289 ms`; error `TBD` | 1328,1334-1335 | `24.6140` slots against `57.8`; fails | `docs/validation/addition13/README.md:101-111,115-121` | MISMATCH |
| calibration uses loss and slot duration; PDR `99.9%`, duty `0.4%` | 1316-1323 | one free parameter/target; `p*=0.05`; duty target dropped; slot duration not a simulator parameter | `profiles/calibration.lock.toml:13-24,62-68,107-113` | MISMATCH |
| `475 ms` as published A2 end-to-end target | 251,459,1108,1327 | A2 published target `475 ms` | `docs/validation/addition13/README.md:14-17` | MATCH |
| tests maintained; counts omitted | 1335-1337 | `9 / 3 / 18`, all `0 failed` | `cargo test --all` output below | UNSOURCED |

```text
$ grep -nE '0\.13797|0\.12264|0\.13733|0\.12409|8\.9|26\.0|4\.8|20\.4|0\.998|0\.996|3\.5234|3\.7776|42\.4407|24\.6140|TBD\{A2 error\}|TBD\{WPaxos error\}|475\\,ms|289\\,ms' paper/paper.tex
251:nodes in 475\,ms at a very low duty cycle \cite{alnahas17a2}, and Wireless
252:Paxos reaches agreement among 188 nodes in 289\,ms \cite{poirot19paxos}.
459:$475$\,ms at a very low duty cycle \cite{alnahas17a2}, and Wireless Paxos
460:reaches agreement among 188 nodes in $289$\,ms \cite{poirot19paxos}.
1108:A2 completes two-phase commit across 180 nodes in 475\,ms
1110:in 289\,ms \cite{poirot19paxos}. Any claim of improvement must be measured
1327:in the calibration: agreement across 180 nodes in 475\,ms for A2/2PC
1328:\cite{alnahas17a2}, and consensus across 188 nodes in 289\,ms for Wireless
1334:within \TBD{A2 error} and the Wireless Paxos configuration within
1335:\TBD{WPaxos error}. All three profiles are maintained as regression tests
$ grep -nE '^(2pc_ce|paxos_ce),log_round_length' docs/validation/addition15/data/fits.csv
2:2pc_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,39.511348,0.000000
3:2pc_ce,log_round_length,linear,0.137331411,0.131013055,0.143649766,4.793313,0.997801
10:paxos_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,50.895160,0.000000
11:paxos_ce,log_round_length,linear,0.124085227,0.115956905,0.132213550,20.403476,0.995552
$ grep -nE 'Published target|Mean latency|Both predictions fail|20–30|relative errors' docs/validation/addition13/README.md
14:| System | Protocol | N | Published target |
91:Mean latency = 42.441 slots [41.946, 42.935].
103:Mean latency = 24.614 slots [24.459, 24.769].
115:**Both predictions fail the acceptance test at every T_guard value.**
116:The simulator predicts latencies that are approximately 20–30× lower than
121:within 20%. Neither system is close: relative errors are −96.5% and −96.6%.
$ grep -nE 'loss_rate = 0\.05|free_parameters = 1|targets = 1|dropped_target|p_star = 0\.05|t_slot =' profiles/calibration.lock.toml
13:loss_rate = 0.05
14:free_parameters = 1
15:targets = 1
24:dropped_target = "radio duty cycle ~0.4 %"
62:p_star = 0.05
113:t_slot = "T_slot is a paper-side unit conversion, derived analytically in docs/validation/t_slot.md, not a simulator parameter. Latency in slots is exactly invariant to it, energy in node-slots is exactly invariant to it, and every CI/CE ratio is exactly invariant to it."
$ grep -n 'test result:' /tmp/paper-audit-cargo-test.txt
15:test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
66:test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.47s
90:test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.23s
```

## Reference configuration, scale, loss, latency, energy

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| Paxos depth `about 12`; 2PC `about 21` | 161-162 | `11.66`; `21.25` | `plots/scalability/results/sweep_summary.csv:56-57` (15-seed aggregation) | MATCH |
| throughput `up to 4x` | 162 | reference 2PC ratio `4.083x`; global maximum `4.268x` | `plots/scalability/results/sweep_summary.csv:50-1740` | MISMATCH |
| energy `up to 5.7x` | 162 | reference 2PC ratio `5.672x`; global maximum `5.987x` | same | MISMATCH |
| `five` topologies, diameters `1` to `26` | 168 | 5 topologies; 1–26 | `plots/topology/results/sweep_summary.csv:2,8,14,20,26` | MATCH |
| `15` independent measurements | 317 | 15 protocol-topology CE aggregates, each 15 seeds; 225 runs | `plots/topology/results/sweep_summary.csv:2-451` | MISMATCH |
| diameter range `26x` | 317 | `26 / 1 = 26` | `plots/topology/results/sweep_summary.csv:2,8,14,20,26` | MATCH |
| latency `27x`; energy `1.3x` | 319-320 | `26.987x`; `1.317x` | `plots/scalability/results/sweep_summary.csv:56-58` (15-seed aggregation) | MATCH |
| line N=`27`, diameter `26` | 323-324 | 27, 26 | `plots/topology/results/sweep_summary.csv:2-7` | MATCH |
| line 2PC-CI commit `0.2%` | 326 | `3 / 1500 = 0.200%` | `plots/topology/results/sweep_summary.csv:3,33,...,423` | MATCH |
| line Paxos unaffected | 327 | `1500 / 1500 = 100%` | `plots/topology/results/sweep_summary.csv:2,32,...,422` | MATCH |
| sweep N=`6..188`, loss `0..20%`, 100 proposals, 15 seeds | 1203-1220 | N `{6,13,27,54,188}`, loss `{0,.05,.1,.2}`, 100, 15 | `plots/scalability/results/sweep_summary.csv:2-1741` | MATCH |
| random and scale-free diameter exactly `4` | 1209-1210,1224-1225 | random mean 4.20, range 4–5; scale-free 4.13, range 4–5 | `plots/topology/results/sweep_summary.csv:2-451` | MISMATCH |
| drain tails `0.09%`, `1.70%`, `3.41%`; max `23.4%` | 1255-1256 | `0.0851%`, `1.6968%`, `3.4105%`; `23.4375%` | `plots/scalability/results/sweep_summary.csv:50-1739` | MATCH |
| baseline six table rows | 1441-1447 | rounded rows match | `plots/scalability/results/sweep_summary.csv:56-61` (15-seed aggregation) | MATCH |
| 2PC ratio `4.08x`, commit `98.9%` | 1465-1470 | `4.083x`, `98.9%` | same | MATCH |
| N=188 TOM `0.148` vs `0.123`, `20%` | 1531-1533 | 0.1478 vs 0.1232; 19.97% | `plots/scalability/results/sweep_summary.csv:98-1740` | MATCH |
| loss decline `15–19%` | 1552-1554 | 14.33%, 18.80%, 14.35% | `plots/scalability/results/sweep_summary.csv:50-1740` | MISMATCH |
| 2PC-CI `0.107`, down `39%` | 1560-1562 | 0.10699; 39.35% | same | MATCH |
| CE decline only `4–5%` | 1573-1574 | Paxos 4.65%; 2PC 6.29% | same | MISMATCH |
| 2PC-CI worst `0.107` > `1.5×0.068` | 1581-1583 | 1.58x | same | MATCH |
| commit near 100%; 2PC exception | 1597-1604 | five combinations 100%; 2PC-CI 70.07% at loss .20 | same | MATCH |
| throughput loss mainly longer run; abort small | 1613-1619 | commit falls to 70.07% | same | MISMATCH |
| TOM N=188 `6.6` vs `7.6` slots | 1646-1647 | 6.8 vs 8.1 | same | MISMATCH |
| CE N=188 Paxos `25`, 2PC `44` slots | 1651-1652 | 24.6, 42.9 | same | MATCH |
| 2PC-CI `170`→`>1700`; Paxos `8`→`620` | 1659-1661 | 16.2→1200.8; 8.1→639.2 | same | MISMATCH |

```text
$ grep -nE 'about 12|about 21|up to 4x|5\.7x|five topologies|fifteen independent|27\\times|1\.3\\times|0\.2\\,%|23\.4|0\.107|1700|620' paper/paper.tex
161:pipeline sustains, on average, about 12 concurrent proposals for Paxos and
162:about 21 for 2PC, yielding up to 4x higher throughput and up to 5.7x better
168:across five topologies with diameters from 1 to 26, confirming that the
317:across fifteen independent measurements spanning a $26\times$ range of network
319:per-decision latency varies by roughly $27\times$ while per-decision energy
320:varies by only about $1.3\times$. Latency stops being a proxy for energy
326:network, and its commit rate drops to 0.2\%. Paxos, which needs only a
1256:reference point, reaching $23.4\,\%$ on a single seed.
1562:about 0.107---some 39\,\% below its lossless value---while the spread
1582:---2PC over \CI{} still delivers 0.107 decisions per slot, more than one
1660:$\Nnodes = 6$ to more than 1700 slots at $\Nnodes = 188$, and Paxos over
1661:\CI{} from about 8 to about 620 slots. \textbf{This does not contradict
$ grep -nE '^2,27,(line|partial_mesh|random|scale_free|full_mesh),0\.05,1,paxos_pipeline' plots/topology/results/sweep_summary.csv
2:2,27,line,0.05,1,paxos_pipeline,ci,26,26,100,100,0,0,237.02,47133,4075,33275,99,603,0,1512
8:2,27,partial_mesh,0.05,1,paxos_pipeline,ci,3,117,100,100,0,0,46.20,5088,3051,2661,0,0,0,396
14:2,27,random,0.05,1,paxos_pipeline,ci,4,62,100,100,0,0,59.26,6559,3051,4187,0,0,0,0,507
20:2,27,scale_free,0.05,1,paxos_pipeline,ci,5,51,100,100,0,0,62.80,7975,3425,5151,1,26,0,537
26:2,27,full_mesh,0.05,1,paxos_pipeline,ci,1,351,100,100,0,0,36.70,3104,3051,2431,0,0,0,315
```

## Dynamics and energy

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| progress-curve ordering/shape | 1724-1775 | no progress-over-time counterpart | allowed sources | UNSOURCED |
| 2PC-CI latency nearly `360` | 1776 | 126.8 in scalability; 357.7 in topology aggregation | both sweep CSVs | MISMATCH |
| completion `590`, `1420`, `2430`, `470`, `525`; `>5x` | 1777-1787 | 590, 1421, 2434, 468, 526; 5.20x | scalability CSV | MATCH |
| depth table `1.00`, `11.66`, `21.25` | 1812-1818 | matches rounded throughput×latency | scalability CSV | MATCH |
| energy ratio `1.43±.02`, `3.83±.07`, `5.67±.27` | 1974-1978 | matches seed-derived intervals | scalability CSV | MATCH |
| proposal sharing `1.6%`; slot ranges `4.70–6.17`, `4.68–24.34` | 1986-1989 | no explicit counterpart | allowed sources | UNSOURCED |
| quartiles/percentiles/extrema/medians | 2009-2045 | no proposal-level distributions | allowed sources | UNSOURCED |
| concurrency `20.84`, median `+4.2%` | 2033-2034 | aggregate depth 21.25; median unavailable | scalability CSV / no counterpart | MISMATCH |
| energy ceilings `127`, `1658`, `3424`; ratios `1.4`, `16.5`, `29.6` | 2088-2090 | arithmetic matches baseline | scalability CSV | MATCH |
| N=188 efficiency Paxos `~5x`, TOM `~2x` | 2138-2146 | 5.01x, 2.01x | scalability CSV | MATCH |

```text
$ grep -nE 'nearly 360|about 590|1420|2430|about 470|about 525|11\.66|21\.25|5\.67|20\.84|3424|29\.6' paper/paper.tex
1776:latency in the entire system at nearly 360 slots---completes the workload
1777:in about 590 slots, more than twice as fast as Paxos over \CE{} at about
1778:1420 slots and close to four times faster than 2PC over \CE{} at about
1779:2430 slots. This comparison alone establishes that per-decision latency
1783:finish line together at about 470 slots, their curves coinciding
1784:throughout the run, followed by Paxos over \CI{} at about 525 slots and
1817:Paxos (\CI) & 0.1903 & 61.4  & 11.66 \\
1818:2PC (\CI)   & 0.1681 & 126.8 & 21.25 \\
1975:$5.67 \pm 0.27$ for 2PC (95\,\% intervals over fifteen seeds).
1978:Paxos and $5.67$ for 2PC---is informative in itself. The heavier the protocol
1986:to $5.67$ under 2PC is not proposal sharing, which accounts for $1.6\,\%$ of
2033:concurrency rises from 1.00 to 20.84 while the median cost of a decision rises
2090:2PC (\CI)   & 126.8 & 115.8 & 3424 & $29.6\times$ \\
```

## Topology

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| modal diameter/mean-degree table | 2187-2191 | `1/26.00`, `3/9.30`, `4/4.40`, `4/3.78`, `26/1.93` | topology CSV | MATCH |
| random→full throughput table | 2250-2256 | rounded ratios match | topology CSV | MATCH |
| Paxos-CE dense latency `12.5–15.9` | 2264-2266 | 12.50–15.90 | topology CSV | MATCH |
| TOM CI/CE difference never exceeds `1%` | 2290-2295 | scale-free relative gap 1.239% | topology CSV | MISMATCH |
| `15` groups, diameter `1–26`, energy `97x` | 2310-2312 | 15 CE groups; 97.27x | topology CSV | MATCH |
| radio accounting all `2250` runs; per-decision `4500` | 2315-2319 | row/run count supports 2250; no per-decision counterpart | topology CSV / allowed sources | UNSOURCED |
| CI off fraction `22–31%` | 2333-2335 | 22.66–30.71% | topology CSV | MATCH |
| residual max `1.94%`; two seeds `99/100` | 2338-2340 | 1.936%; seeds 23,37 | topology CSV:246,336 | MATCH |
| CI less energy all protocols/all topologies | 2342-2343 | false on line 2PC due near-zero commits | topology CSV | MISMATCH |
| dense margin `1.3–12x`; TOM line `2916/401`, `>7x` | 2344-2346 | 1.299–12.098x; 7.266x | topology CSV | MATCH |
| depth dense TOM≈1, Paxos≈11.6, 2PC≈21 | 2354-2358 | ranges match | topology CSV | MATCH |
| diameter counts `12/15`, `13/15`; matched D4 `10`; losses `27.4/10.6`; degree `4.40/3.78` | 2382-2388 | matches | topology CSV | MATCH |
| table changes are mean per-seed differences | 2400-2401 | displayed values are ratios of means | topology CSV | MISMATCH |
| CE slower all 15; CI faster `8–11` seeds | 2427-2429 | CE 15; CI 8–10 | topology CSV | MISMATCH |
| timeouts/run lengths `337→2049`, `2433→3331`, `5.4→30` | 2436-2439 | matches | topology CSV | MATCH |
| identical-diameter difference `up to 27%` | 2453-2457 | 27.4% | topology CSV | MATCH |
| every line node has `two` neighbours | 2464-2466 | endpoints have degree 1 | topology CSV header + line graph definition | MISMATCH |
| line TOM `0.214→0.009`; 2PC commit `0.2%`, dense `100%`, random `98.9%` | 2467-2471 | matches | topology CSV | MATCH |
| line Paxos `100%`, `0.0625`, highest | 2484-2487 | 100%, 0.062468, highest | topology CSV | MATCH |
| line 2PC energy `190,180`, efficiency `0.00` | 2489-2493 | no reproducible counterpart; aggregate ≈1,005,531/commit | topology CSV | UNSOURCED |
| line TOM latency `616/108`, depth `26`, throughput `5x`, energy `>7x` | 2508-2518 | matches rounded aggregation | topology CSV | MATCH |
| commit close to complete every combination | 2543-2544 | topology minimum 0.2%; scalability minimum 23.2% | both sweep CSVs | MISMATCH |
| summary `15` cases, `26x`, `72%`, `27%` | 2557-2568 | matches aggregate comparisons | topology CSV | MATCH |

```text
$ grep -nE '1\.94|2250|4500|22 and 31|1\.3 and 12|27\.4|10\.6|8 to eleven|337|2049|0\.0625|190\\,180|616 slots|close to complete' paper/paper.tex
2315:radio counters sum to $\Nnodes$ times the slots ticked in all $2250$ runs of
2318:decision and not only in aggregate: every one of the $4500$ \CE{} per-decision
2333:falls short of $\Nnodes L$ by between 22 and 31\,\% on the dense topologies,
2339:fifteen groups and reaches $1.94\,\%$ on a single seed of 2PC over \CE{} on the
2344:margin ranges between 1.3 and 12 times on the dense topologies and, worth
2386:conclusion of this subsection intact: 2PC over \CE{} loses 27.4\,\% of its
2387:throughput and Paxos over \CE{} 10.6\,\%, against 26.7\,\% and 10.7\,\% over
2429:protocols are faster on eight to eleven of them.
2436:number of \CE{} listen timeouts recorded for 2PC rises from 337 on the random
2437:graph to 2049 on the scale-free graph, stretching the run from 2433 to 3331
2486:very topology at a full commit rate and a throughput of 0.0625---which
2491:decision (190\,180) and the efficiency (0.00) both result from division by
2508:it is of a different kind. Its latency reaches 616 slots where TOM over
2544:the commit rate stays close to complete for every combination. The
```

## Exclusion, hypothesis, classification

| Check | Paper line/sentence | Committed counterpart | Verdict |
|---|---|---|---|
| n=188 exclusion | no exclusion statement or reason; paper includes n=188 at 1204-1206 | Paxos anchor excluded because it lies outside uniform W=10 grid | `docs/validation/addition15/README.md:27` | UNSOURCED |
| densification residual hypothesis | lines 2233-2234 and 2283-2288 still imply improving density/network quality should explain performance, without reporting falsification | Addition 15 CIs exclude both α=0 and α=1 | `fits.csv:3,11`; README:100-102 | MISMATCH (Revised to acknowledge sweep only bounds the confound) |
| classification | absent | both arms `SUBLINEAR-INTERMEDIATE` | `docs/validation/addition15/README.md:100,102` | UNSOURCED |

```text
$ grep -nEi 'excluded|exclusion|outside this sweep|densif|hypothes|falsif|SUBLINEAR-INTERMEDIATE|conventional expectation|increasing node density' paper/paper.tex
1354:Several phenomena are deliberately excluded from the model. Rather than
1400:exclusion we make no attempt to correct: real capture requires a power
2233:The conventional expectation is that a better network benefits every
2234:protocol. The measurements show that this holds for one family only.
2284:be improved---by raising transmission power, increasing node density or
$ grep -nE 'outside this sweep|SUBLINEAR-INTERMEDIATE|alpha CI' docs/validation/addition15/README.md
27:The Paxos anchor at n=188 lies outside this sweep's grid and is therefore not included in the primary fit.
100:For 2PC over CE, the alpha CI is [0.13101, 0.14365]. By the decision rule, we conclude SUBLINEAR-INTERMEDIATE.
102:For Paxos over CE, the alpha CI is [0.11596, 0.13221]. By the decision rule, we conclude SUBLINEAR-INTERMEDIATE.
```

Quoted implication sentences:

```text
2233:The conventional expectation is that a better network benefits every
2234:protocol. The measurements show that this holds for one family only.
2283:The design consequence is direct. In deployments where network quality can
2284:be improved---by raising transmission power, increasing node density or
2285:improving routing---only the \CI{} architecture, together with
2286:single-phase protocols, converts that investment into performance. For
2287:Paxos and 2PC over \CE, investment in network infrastructure is largely
2288:wasted.
```

## Abstract, introduction, conclusion contradictions

| Earlier/later claim | Results contradiction | Verdict |
|---|---|---|
| abstract 167-169: results hold across five topologies | results 2469-2471: line 2PC-CI commit collapses to 0.2% | MISMATCH |
| abstract 161-163 / introduction 312-320: broad 12/21 depth, 27x latency, 1.3x energy | results 2508-2515: line TOM depth≈26; line 2PC denominator collapses | MISMATCH |
| conclusion 2612-2615: stable across topology; TOM depth one | results 2508-2515: line TOM latency 616, depth≈26 | MISMATCH |

```text
$ grep -nE 'Results hold|about 12 concurrent|roughly \$27|stable across the topology|jumps from|only 0\.2' paper/paper.tex
161:pipeline sustains, on average, about 12 concurrent proposals for Paxos and
167:coupling and turns latency into a spendable design variable. Results hold
319:per-decision latency varies by roughly $27\times$ while per-decision energy
2469:combination fails outright: \textbf{2PC over \CI{} reaches a commit rate of
2470:only 0.2\,\%}, whereas the same protocol commits 100\,\% of proposals on
2514:pipeline depth as well, where $\Cdepth$ for TOM over \CI{} jumps from
2612:Third, the results are stable across the topology space, and the boundary
```

## Figure and table inventory

No active external figure/table include exists: all 14 `\includegraphics` lines are commented, and all tables are inline. `paper/figures/` is absent. Commented references name missing files: `pipeline_mechanism.pdf`, `message_frame.pdf`, `paxos_ci_example.pdf`, `throughput_vs_nodes.pdf`, `throughput_vs_loss.pdf`, `latency_vs_nodes.pdf`, `progress_over_time_log.pdf`, `progress_over_time.pdf`, `energy_mean_ci_ce.pdf`, `energy_boxplot.pdf`, `latency_vs_energy.pdf`, `efficiency_vs_nodes.pdf`, `throughput_vs_topology.pdf`, `latency_vs_topology.pdf`. Several generated filenames differ (`fig_energy_*`, `thr_vs_topology.pdf`, `lat_vs_topology.pdf`). The manuscript's pooled boxplot claim corresponds to `plots/energy/energy_boxplot_15seed.{pdf,png}`, generated by `docs/validation/addition7/scripts/addition7_boxplot.py`, not by `tools/regen_figures.py`.

```text
$ grep -nE '\\includegraphics|\\graphicspath' paper/paper.tex
32:\graphicspath{{figures/}}
776:% \includegraphics[width=\columnwidth]{pipeline_mechanism.pdf}
851:% \includegraphics[width=\columnwidth]{message_frame.pdf}
928:% \includegraphics[width=\columnwidth]{paxos_ci_example.pdf}
1491:% \includegraphics[width=\columnwidth]{throughput_vs_nodes.pdf}
1546:% \includegraphics[width=\columnwidth]{throughput_vs_loss.pdf}
1630:% \includegraphics[width=\columnwidth]{latency_vs_nodes.pdf}
1710:% \includegraphics[width=\columnwidth]{progress_over_time_log.pdf}
1714:% \includegraphics[width=\columnwidth]{progress_over_time.pdf}
1965:% \includegraphics[width=\columnwidth]{energy_mean_ci_ce.pdf}
2002:% \includegraphics[width=\columnwidth]{energy_boxplot.pdf}
2052:% \includegraphics[width=\columnwidth]{latency_vs_energy.pdf}
2124:% \includegraphics[width=\columnwidth]{efficiency_vs_nodes.pdf}
2221:% \includegraphics[width=\columnwidth]{throughput_vs_topology.pdf}
2225:% \includegraphics[width=\columnwidth]{latency_vs_topology.pdf}
$ grep -nE 'energy_boxplot_15seed|addition7_boxplot' tools/regen_figures.py docs/validation/addition7/scripts/addition7_boxplot.py
# tools/regen_figures.py: no matches
docs/validation/addition7/scripts/addition7_boxplot.py:57:    fig.savefig(OUT / "energy_boxplot_15seed.png", dpi=300)
docs/validation/addition7/scripts/addition7_boxplot.py:58:    fig.savefig(OUT / "energy_boxplot_15seed.pdf")
```


## Sources added in round 24 (step 2.10-b)
| Claim | Paper location | Evidence file | Verdict |
|---|---|---|---|
| Progress curves (Fig 13/14) | Fig. fig:progress-lin / fig:progress-log | `docs/validation/paper-audit/sources/progress_snapshots.csv` | SOURCED |
| Slots per decision `4.70`, `6.17`, `4.68`, `24.34` | 1986 | `docs/validation/paper-audit/sources/slots_per_decision.md` | MISMATCH (pooled: 4.70-5.97 / 4.68-24.34; per-seed mean: 4.70-5.97 / 4.68-24.34) |
| Energy distribution extrema | 2009-2045 | `docs/validation/paper-audit/sources/distribution_stats.csv` | SOURCED |
| Integer multiple check | 2088-2090 | `docs/validation/paper-audit/sources/integer_multiple_check.md` | SOURCED |
| Line 2PC energy/efficiency | 2489-2493 | removed from text | REMOVED |
| Proposal sharing share `1.6%` | 1986 | `docs/validation/paper-audit/sources/proposal_sharing_candidates.md` | UNSOURCED |

## Corrections in round 25 (step 2.10-c)
- Proposal sharing share: 4.57% withdrawn (invalid mix of fresh numerator and frozen denominator).
- Slots per decision: estimator corrected from per-seed mean to pooled (sum/sum) to match paper definition.
- Progress curves: 99-versus-100 is a disclosed reporting/counting mismatch, not a repaired simulator bug.
- Test count corrected to 9 / 3 / 20 (superseding stale 9 / 3 / 19).

## Corrections in round 26 (step 2.7-R)
- Reference Provenance (R2): Replaced the misleading ungrounded cross-N residual extrapolation of the 100.0/57.8 slots with explicit anchor-only comparison and marked cross-N tracking as NOT IDENTIFIABLE.
- Density Control (R1): Hardened uniform density selection to eliminate append-induced contamination and use a deterministic W=10 window.
