# Numeric audit of `paper/paper.tex`

## Provenance
All numbers, line references, and evidence blocks in this file were measured against `main` at commit `98ac7318b409ba580f2e5d9257b5208117444ff8`.

**Summary: 79 distinct numeric claims examined — MATCH 57 / MISMATCH 9 / UNSOURCED 9 / SOURCED 3 / REMOVED 1.** Base: `main` at `98ac7318b409ba580f2e5d9257b5208117444ff8` (original audit base: `cdc2f818af6b7b48cf05abfab293cd470a046335`). Verdicts use only the source precedence requested for this audit. A paper range is one distinct claim when adjacent values form one comparison, table row, or interval.

**Counting rule:** A row carrying a compound verdict (e.g. "UNSOURCED (Paxos not reproduced)" or "MISMATCH (Revised to ...)") is counted under its leading verdict word.

## Addition 15 fits, anchors, predictions, calibration, tests

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| slope `0.137331411`, CI `[0.131013055, 0.143649766]`, AIC `4.793313`, $R^2=0.997801$; Paxos slope `0.124085227`, CI `[0.115956905, 0.132213550]`, AIC `20.403476`, $R^2=0.995552$ | 1640,1642 | 2PC `0.13733 [0.13101, 0.14365]`, AIC `4.8`, R² `0.998`; Paxos `0.12409 [0.11596, 0.13221]`, AIC `20.4`, R² `0.996` | `docs/validation/addition15/data/fits.csv:3,11`; `docs/validation/addition15/README.md:72,86` | MATCH |
| withdrawn `0.13797`, `0.12264`, AIC `8.9`, `26.0` absent | — | values withdrawn; no occurrence | `paper/paper.tex` grep below | MATCH |
| residual ratios `3.5234x` at $\Nnodes=180$ for 2PC and `3.7776x` at $\Nnodes=188$ for Paxos | 1648 | 2PC `3.5234x` at n=180; Paxos `3.7776x` at n=188 | `docs/validation/addition15/README.md:21-27` | MATCH |
| withdrawn reference slots `100.0`, `57.8` absent | — | values withdrawn; no occurrence | `paper/paper.tex` grep below | MATCH |
| A2 predicts `16.722\,ms [16.527, 16.917]` against `475\,ms` (relative error `$-0.9648$`) | 1423 | `42.441` slots against `100.0`; fails | `docs/validation/addition13/README.md:89-99,115-121` | MATCH |
| Wireless Paxos predicts `9.796\,ms [9.735, 9.858]` against `289\,ms` (relative error `$-0.9661$`) | 1424 | `24.614` slots against `57.8`; fails | `docs/validation/addition13/README.md:101-111,115-121` | MATCH |
| calibration has one free parameter and one target; `p^*=0.05`; duty target dropped; slot duration a unit conversion | — | one free parameter/target; `p*=0.05`; duty target dropped; slot duration not a simulator parameter | `profiles/calibration.lock.toml:13-24,62-68,107-113` | MATCH |
| `475 ms` as published A2 end-to-end target | 257,1201,1423 | A2 published target `475 ms` | `docs/validation/addition13/README.md:14-17` | MATCH |
| tests maintained; counts omitted | 1433 | `9 / 3 / 22`, all `0 failed` | `cargo test --all` output below | UNSOURCED |

```text
$ grep -nE '0\.13797|0\.12264|0\.13733|0\.12409|8\.9|26\.0|4\.8|20\.4|0\.998|0\.996|3\.5234|3\.7776|16\.722|9\.796|475\\,ms|289\\,ms|100\.0|57\.8' paper/paper.tex
1423:16.722\,ms [16.527, 16.917] against 475\,ms (relative error $-0.9648$), while
1424:Wireless Paxos predicts 9.796\,ms [9.735, 9.858] against 289\,ms (relative
1536:TOM (\CI)   & 100.0 & 0.2132 & 4.7   & 88.0  & 2.429 & 3900 \\
1537:Paxos (\CI) & 100.0 & 0.1903 & 61.4  & 100.2 & 1.906 & 4434 \\
1538:2PC (\CI)   & 98.9  & 0.1681 & 126.8 & 115.8 & 1.463 & 5034 \\
1540:TOM (\CE)   & 100.0 & 0.2143 & 4.7   & 126.3 & 1.705 & 0 \\
1541:Paxos (\CE) & 100.0 & 0.0704 & 14.2  & 383.6 & 0.184 & 0 \\
1542:2PC (\CE)   & 100.0 & 0.0412 & 24.3  & 657.1 & 0.063 & 0 \\
1565:slightly short of complete commitment, at 98.9\,\%, which is a
1640:$\log(\text{round length})$--$\log(\Nnodes)$ fit has slope 0.137331411 with
1643:[0.115956905, 0.132213550], AIC 20.403476 and $R^2=0.995552$. The
1648:residual ratios 3.5234x at $\Nnodes=180$ for 2PC and 3.7776x at
1716:(98.9\,\% at 5\,\% loss, per Table~\ref{tab:baseline}, and further
2293:Full mesh    & 1  & 26.00 \\
2577:the full and partial meshes and 98.9\,\% on the random topology.
$ grep -nE '^(2pc_ce|paxos_ce),log_round_length' docs/validation/addition15/data/fits.csv
2:2pc_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,39.511348,0.000000
3:2pc_ce,log_round_length,linear,0.137331411,0.131013055,0.143649766,4.793313,0.997801
6:paxos_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,50.895160,0.000000
7:paxos_ce,log_round_length,linear,0.124085227,0.115956905,0.132213550,20.403476,0.995552
$ grep -nE '16\.722|9\.796' docs/validation/addition13/README.md
96:| 10 | 394.0 | 16.722 | 16.527 | 16.917 | 475.0 | −0.9648 | NO |
108:| 10 | 398.0 | 9.796 | 9.735 | 9.858 | 289.0 | −0.9661 | NO |
$ grep -nE 'loss_rate = 0\.05|free_parameters = 1|targets = 1|dropped_target|p_star = 0\.05|t_slot =' profiles/calibration.lock.toml
13:loss_rate = 0.05
14:free_parameters = 1
15:targets = 1
24:dropped_target = "radio duty cycle ~0.4 %"
62:p_star = 0.05
113:t_slot = "T_slot is a paper-side unit conversion, derived analytically in docs/validation/t_slot.md, not a simulator parameter. Latency in slots is exactly invariant to it, energy in node-slots is exactly invariant to it, and every CI/CE ratio is exactly invariant to it."
122:primary_loss_rate = 0.05
$ cargo test --all 2>&1 | grep -E '^test result:'
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.44s
test result: ok. 22 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 50.48s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

## Reference configuration, scale, loss, latency, energy

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| Paxos depth `about 12`; 2PC `about 21` | 166,167,318,319 | `11.69`; `21.31` | `plots/scalability/results/sweep_summary.csv:56-57` (15-seed aggregation) | MATCH |
| throughput `4.083x` (global max `4.268x`) | 167 | reference 2PC ratio `4.083x`; global maximum `4.268x` | `plots/scalability/results/sweep_summary.csv:50-1740` | MATCH |
| energy `5.672x` (global max `5.987x`) | 167 | reference 2PC ratio `5.672x`; global maximum `5.987x` | same | MATCH |
| `five` topologies, diameters `1` to `26` | — | 5 topologies; 1–26 | `plots/topology/results/sweep_summary.csv:2,8,14,20,26` | MATCH |
| `15` protocol-topology CE aggregates (225 runs) | 323 | 15 protocol-topology CE aggregates, each 15 seeds; 225 runs | `plots/topology/results/sweep_summary.csv:2-451` | MATCH |
| diameter range `26x` | 323 | `26 / 1 = 26` | `plots/topology/results/sweep_summary.csv:2,8,14,20,26` | MATCH |
| latency `27x`; energy `1.3x` | — | `26.987x`; `1.317x` | `plots/scalability/results/sweep_summary.csv:56-58` (15-seed aggregation) | MATCH |
| line N=`27`, diameter `26` | — | 27, 26 | `plots/topology/results/sweep_summary.csv:2-7` | MATCH |
| line 2PC-CI commit `0.2%` | — | `3 / 1500 = 0.200%` | `plots/topology/results/sweep_summary.csv:3,33,...,423` | MATCH |
| line Paxos unaffected | — | `1500 / 1500 = 100%` | `plots/topology/results/sweep_summary.csv:2,32,...,422` | MATCH |
| sweep N=`6..188`, loss `0..20%`, 100 proposals, 15 seeds | — | N `{6,13,27,54,188}`, loss `{0,.05,.1,.2}`, 100, 15 | `plots/scalability/results/sweep_summary.csv:2-1741` | MATCH |
| random mean `4.20` (range 4–5); scale-free mean `4.13` (range 4–5) | 1303,2285 | random mean 4.20, range 4–5; scale-free 4.13, range 4–5 | `plots/topology/results/sweep_summary.csv:2-451` | MATCH |
| drain tails `0.09%`, `1.70%`, `3.41%`; max `23.4%` | — | `0.0851%`, `1.6968%`, `3.4105%`; `23.4375%` | `plots/scalability/results/sweep_summary.csv:50-1739` | MATCH |
| baseline six table rows | 1516,1716,1903,1909,1964,2014,2047,2312,2504 | rounded rows match | `plots/scalability/results/sweep_summary.csv:56-61` (15-seed aggregation) | MATCH |
| 2PC ratio `4.08x`, commit `98.9%` | — | `4.083x`, `98.9%` | same | MATCH |
| N=188 TOM `0.148` vs `0.123`, `20%` | 1628 | 0.1478 vs 0.1232; 19.97% | `plots/scalability/results/sweep_summary.csv:98-1740` | MATCH |
| loss decline `14.33%, 18.80%, 14.35%` | — | 14.33%, 18.80%, 14.35% | `plots/scalability/results/sweep_summary.csv:50-1740` | MATCH |
| 2PC-CI `0.107`, down `39%` | — | 0.10699; 39.35% | same | MATCH |
| CE decline `4.65%` (Paxos), `6.29%` (2PC) | — | Paxos 4.65%; 2PC 6.29% | same | MATCH |
| 2PC-CI worst `0.107` > `1.5×0.068` | — | 1.58x | same | MATCH |
| commit near 100%; 2PC exception | 1710 | five combinations 100%; 2PC-CI 70.07% at loss .20 | same | MATCH |
| throughput loss mainly longer run; abort small | 2650 | commit falls to 70.07% | same | MISMATCH |
| TOM N=188 `6.8` vs `8.1` slots | — | 6.8 vs 8.1 | same | MATCH |
| CE N=188 Paxos `25`, 2PC `44` slots | — | 24.6, 42.9 | same | MATCH |
| 2PC-CI `16.2`→`1200.8`; Paxos `8.1`→`639.2` | 1771 | 16.2→1200.8; 8.1→639.2 | same | MATCH |
# Numeric audit of `paper/paper.tex`

## Provenance
All numbers, line references, and evidence blocks in this file were measured against `main` at commit `98ac7318b409ba580f2e5d9257b5208117444ff8`.

## Addition 15 fits, anchors, predictions, calibration, tests

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| slope `0.137331411`, CI `[0.131013055, 0.143649766]`, AIC `4.793313`, $R^2=0.997801$; Paxos slope `0.124085227`, CI `[0.115956905, 0.132213550]`, AIC `20.403476`, $R^2=0.995552$ | — | 2PC `0.13733 [0.13101, 0.14365]`, AIC `4.8`, R² `0.998`; Paxos `0.12409 [0.11596, 0.13221]`, AIC `20.4`, R² `0.996` | `docs/validation/addition15/data/fits.csv:3,11`; `docs/validation/addition15/README.md:72,86` | MATCH |
| withdrawn `0.13797`, `0.12264`, AIC `8.9`, `26.0` absent | — | values withdrawn; no occurrence | `paper/paper.tex` grep below | MATCH |
| residual ratios `3.5234x` at $\Nnodes=180$ for 2PC and `3.7776x` at $\Nnodes=188$ for Paxos | — | 2PC `3.5234x` at n=180; Paxos `3.7776x` at n=188 | `docs/validation/addition15/README.md:21-27` | MATCH |
| withdrawn reference slots `100.0`, `57.8` absent | — | values withdrawn; no occurrence | `paper/paper.tex` grep below | MATCH |
| A2 predicts `16.722\,ms [16.527, 16.917]` against `475\,ms` (relative error `$-0.9648$`) | 1423 | `42.441` slots against `100.0`; fails | `docs/validation/addition13/README.md:89-99,115-121` | MATCH |
| Wireless Paxos predicts `9.796\,ms [9.735, 9.858]` against `289\,ms` (relative error `$-0.9661$`) | — | `24.614` slots against `57.8`; fails | `docs/validation/addition13/README.md:101-111,115-121` | MATCH |
| calibration has one free parameter and one target; `p^*=0.05`; duty target dropped; slot duration a unit conversion | — | one free parameter/target; `p*=0.05`; duty target dropped; slot duration not a simulator parameter | `profiles/calibration.lock.toml:13-24,62-68,107-113` | MATCH |
| `475 ms` as published A2 end-to-end target | 257,1201,1423 | A2 published target `475 ms` | `docs/validation/addition13/README.md:14-17` | MATCH |
| tests maintained; counts omitted | 1433 | `9 / 3 / 22`, all `0 failed` | `cargo test --all` output below | UNSOURCED |

```text
$ grep -nE '0\.13797|0\.12264|0\.13733|0\.12409|8\.9|26\.0|4\.8|20\.4|0\.998|0\.996|3\.5234|3\.7776|16\.722|9\.796|475\\,ms|289\\,ms|100\.0|57\.8' paper/paper.tex
1423:16.722\,ms [16.527, 16.917] against 475\,ms (relative error $-0.9648$), while
1424:Wireless Paxos predicts 9.796\,ms [9.735, 9.858] against 289\,ms (relative
1536:TOM (\CI)   & 100.0 & 0.2132 & 4.7   & 88.0  & 2.429 & 3900 \\
1537:Paxos (\CI) & 100.0 & 0.1903 & 61.4  & 100.2 & 1.906 & 4434 \\
1538:2PC (\CI)   & 98.9  & 0.1681 & 126.8 & 115.8 & 1.463 & 5034 \\
1540:TOM (\CE)   & 100.0 & 0.2143 & 4.7   & 126.3 & 1.705 & 0 \\
1541:Paxos (\CE) & 100.0 & 0.0704 & 14.2  & 383.6 & 0.184 & 0 \\
1542:2PC (\CE)   & 100.0 & 0.0412 & 24.3  & 657.1 & 0.063 & 0 \\
1565:slightly short of complete commitment, at 98.9\,\%, which is a
1640:$\log(\text{round length})$--$\log(\Nnodes)$ fit has slope 0.137331411 with
1643:[0.115956905, 0.132213550], AIC 20.403476 and $R^2=0.995552$. The
1648:residual ratios 3.5234x at $\Nnodes=180$ for 2PC and 3.7776x at
1716:(98.9\,\% at 5\,\% loss, per Table~\ref{tab:baseline}, and further
2293:Full mesh    & 1  & 26.00 \\
2577:the full and partial meshes and 98.9\,\% on the random topology.
$ grep -nE '^(2pc_ce|paxos_ce),log_round_length' docs/validation/addition15/data/fits.csv
2:2pc_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,39.511348,0.000000
3:2pc_ce,log_round_length,linear,0.137331411,0.131013055,0.143649766,4.793313,0.997801
6:paxos_ce,log_round_length,constant,0.000000000,0.000000000,0.000000000,50.895160,0.000000
7:paxos_ce,log_round_length,linear,0.124085227,0.115956905,0.132213550,20.403476,0.995552
$ grep -nE '16\.722|9\.796' docs/validation/addition13/README.md
96:| 10 | 394.0 | 16.722 | 16.527 | 16.917 | 475.0 | −0.9648 | NO |
108:| 10 | 398.0 | 9.796 | 9.735 | 9.858 | 289.0 | −0.9661 | NO |
$ grep -nE 'loss_rate = 0\.05|free_parameters = 1|targets = 1|dropped_target|p_star = 0\.05|t_slot =' profiles/calibration.lock.toml
13:loss_rate = 0.05
14:free_parameters = 1
15:targets = 1
24:dropped_target = "radio duty cycle ~0.4 %"
62:p_star = 0.05
113:t_slot = "T_slot is a paper-side unit conversion, derived analytically in docs/validation/t_slot.md, not a simulator parameter. Latency in slots is exactly invariant to it, energy in node-slots is exactly invariant to it, and every CI/CE ratio is exactly invariant to it."
122:primary_loss_rate = 0.05
$ cargo test --all 2>&1 | grep -E '^test result:'
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.45s
test result: ok. 22 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 49.99s
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```


## Dynamics and energy

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| progress-curve ordering/shape | — | no progress-over-time counterpart | allowed sources | UNSOURCED |
| 2PC-CI latency `126.8` (scalability baseline) | — | 126.8 in scalability; 357.7 only in topology aggregation | both sweep CSVs | MATCH |
| completion `590`, `1420`, `2430`, `470`, `525`; `>5x` | — | 590, 1421, 2434, 468, 526; 5.20x | scalability CSV | MATCH |
| depth table `1.00`, `11.66`, `21.25` | — | matches rounded throughput×latency | scalability CSV | MATCH |
| energy ratio `1.43±.02`, `3.83±.07`, `5.67±.27` | — | matches seed-derived intervals | scalability CSV | MATCH |
| proposal sharing `1.6%`; slot ranges `4.70–6.17`, `4.68–24.34` | — | no explicit counterpart | allowed sources | UNSOURCED |
| quartiles/percentiles/extrema/medians | 2133 | no proposal-level distributions | allowed sources | UNSOURCED |
| concurrency `21.25` (median clause withdrawn) | — | aggregate depth 21.25; median unavailable | scalability CSV / no counterpart | MATCH |
| energy ceilings `127`, `1658`, `3424`; ratios `1.4`, `16.5`, `29.6` | — | arithmetic matches baseline | scalability CSV | MATCH |
| N=188 efficiency Paxos `~5x`, TOM `~2x` | — | 5.01x, 2.01x | scalability CSV | MATCH |

```text
$ grep -nE '126\.8 in the scalability baseline|about 590|1420|2430|about 470|about 525|11\.66|21\.25|5\.67|3424|29\.6' paper/paper.tex
167:about 21 for 2PC, yielding 4.083x higher baseline throughput (global maximum 4.268x) and 5.672x better
320:higher baseline throughput (global maximum $4.268\times$) and $5.672\times$ better baseline
1883:in about 590 slots, more than twice as fast as Paxos over \CE{} at about
1884:1420 slots and close to four times faster than 2PC over \CE{} at about
1885:2430 slots. This comparison alone establishes that per-decision latency
1889:finish line together at about 470 slots, their curves coinciding
1890:throughout the run, followed by Paxos over \CI{} at about 525 slots and
1891:2PC over \CI{} at about 590. The slowest combination to reach the finish
1923:Paxos (\CI) & 0.1903 & 61.4  & 11.66 \\
1924:2PC (\CI)   & 0.1681 & 126.8 & 21.25 \\
2080:$5.67 \pm 0.27$ for 2PC (95\,\% intervals over fifteen seeds);
2085:Paxos and $5.67$ for 2PC---is informative in itself. The heavier the protocol
2093:to $5.67$ under 2PC is not proposal sharing, which accounts for $1.6\,\%$ of
2140:concurrency rises from 1.00 to 21.25.
2196:2PC (\CI)   & 126.8 & 115.8 & 3424 & $29.6\times$ \\
```

## Topology

| Paper value | `paper.tex` line | Committed value | Exact source | Verdict |
|---|---:|---|---|---|
| modal diameter/mean-degree table | — | `1/26.00`, `3/9.30`, `4/4.40`, `4/3.78`, `26/1.93` | topology CSV | MATCH |
| random→full throughput table | 2343 | rounded ratios match | topology CSV | MATCH |
| Paxos-CE dense latency `12.5–15.9` | — | 12.50–15.90 | topology CSV | MATCH |
| TOM CI/CE gap stays within about `1.3%` | — | scale-free relative gap 1.239% | topology CSV | MATCH |
| `15` groups, diameter `1–26`, energy `97x` | — | 15 CE groups; 97.27x | topology CSV | MATCH |
| radio accounting all `2250` runs; per-decision `4500` | — | row/run count supports 2250; no per-decision counterpart | topology CSV / allowed sources | UNSOURCED |
| CI off fraction `22–31%` | 2439 | 22.66–30.71% | topology CSV | MATCH |
| residual max `1.94%`; two seeds `99/100` | — | 1.936%; seeds 23,37 | topology CSV:246,336 | MATCH |
| CI less energy all protocols/all topologies | — | false on line 2PC due near-zero commits | topology CSV | MISMATCH |
| dense margin `1.3–12x`; TOM line `2916/401`, `>7x` | — | 1.299–12.098x; 7.266x | topology CSV | MATCH |
| depth dense TOM≈1, Paxos≈11.6, 2PC≈21 | — | ranges match | topology CSV | MATCH |
| diameter counts `12/15`, `13/15`; matched D4 `10`; losses `27.4/10.6`; degree `4.40/3.78` | — | matches | topology CSV | MATCH |
| table changes are mean per-seed differences | — | displayed values are ratios of means | topology CSV | MISMATCH |
| CE slower all 15; CI faster `8–11` seeds | — | CE 15; CI 8–10 | topology CSV | MISMATCH |
| timeouts/run lengths `337→2049`, `2433→3331`, `5.4→30` | 2542 | matches | topology CSV | MATCH |
| identical-diameter difference `up to 27%` | — | 27.4% | topology CSV | MATCH |
| line node: endpoints have one neighbour, interior two | — | endpoints have degree 1 | topology CSV header + line graph definition | MATCH |
| line TOM `0.214→0.009`; 2PC commit `0.2%`, dense `100%`, random `98.9%` | — | matches | topology CSV | MATCH |
| line Paxos `100%`, `0.0625`, highest | — | 100%, 0.062468, highest | topology CSV | MATCH |
| line 2PC energy `190,180`, efficiency `0.00` | — | no reproducible counterpart; aggregate ≈1,005,531/commit | topology CSV | UNSOURCED |
| line TOM latency `616/108`, depth `26`, throughput `5x`, energy `>7x` | — | matches rounded aggregation | topology CSV | MATCH |
| commit close to complete except 2PC-CI line (0.2%) and scalability min (23.2%) | — | topology minimum 0.2%; scalability minimum 23.2% | both sweep CSVs | MATCH |
| summary `15` cases, `26x`, `72%`, `27%` | — | matches aggregate comparisons | topology CSV | MATCH |

```text
$ grep -nE '1\.94|2250|4500|22 and 31|1\.3 and 12|27\.4|10\.6|8 to eleven|337|2049|0\.0625|190\\,180|616 slots|0\.2\\,%.*23\.2\\,%' paper/paper.tex
175:pipeline depth reaches about 26 and latency reaches 616 slots.
329:and its latency reaches 616 slots. Latency stops being a proxy for energy
1428:The distinct raw-slot comparison gives 42.441 slots [41.946, 42.935] for A2,
2059:$\Nnodes \cdot L$; this was verified on every one of the 4500 \CE{} decisions
2421:radio counters sum to $\Nnodes$ times the slots ticked in all $2250$ runs of
2424:decision and not only in aggregate: every one of the $4500$ \CE{} per-decision
2439:falls short of $\Nnodes L$ by between 22 and 31\,\% on the dense topologies,
2445:fifteen groups and reaches $1.94\,\%$ on a single seed of 2PC over \CE{} on the
2450:margin ranges between 1.3 and 12 times on the dense topologies and, worth
2492:conclusion of this subsection intact: 2PC over \CE{} loses 27.4\,\% of its
2493:throughput and Paxos over \CE{} 10.6\,\%, against 26.7\,\% and 10.7\,\% over
2541:number of \CE{} listen timeouts recorded for 2PC rises from 337 on the random
2542:graph to 2049 on the scale-free graph, stretching the run from 2433 to 3331
2592:very topology at a full commit rate and a throughput of 0.0625---which
2614:it is of a different kind. Its latency reaches 616 slots where TOM over
2724:latency reaches 616 slots. The boundary case of TOM nevertheless shows that
```

## Exclusion, hypothesis, classification

| Check | Paper line/sentence | Committed counterpart | Exact source | Verdict |
|---|---|---|---|---|
| n=188 exclusion | no exclusion statement or reason; paper includes n=188 at 1449,1495 | Paxos anchor at n=188 is not reproduced in this round | `docs/validation/addition15/README.md:27` | UNSOURCED |
| densification residual hypothesis | lines — still imply improving density/network quality should explain performance, without reporting falsification | Addition 15 CIs exclude both α=0 and α=1 | `fits.csv:3,11`; README:100-102 | MISMATCH (Revised to acknowledge sweep only bounds the confound) |
| classification | absent | both arms `SUBLINEAR-INTERMEDIATE` | `docs/validation/addition15/README.md:100,102` | UNSOURCED |

```text
$ grep -nEi 'excluded|exclusion|outside this sweep|densif|hypothes|falsif|SUBLINEAR-INTERMEDIATE|conventional expectation|increasing node density' paper/paper.tex
1449:Several phenomena are deliberately excluded from the model. Rather than
1456:\caption{Excluded phenomena and the direction in which each biases the
1462:\textbf{Excluded phenomenon} & \textbf{Favours} & \textbf{Treatment} \\
1495:exclusion we make no attempt to correct: real capture requires a power
1644:pre-registered rule identifies $\alpha \sim 0$ with Hypothesis A and
1645:$\alpha \sim 1$ with Hypothesis B; a CI excluding both yields
1646:\texttt{SUBLINEAR-INTERMEDIATE}. Both reported CIs exclude 0 and 1, so both
1651:-0.015. The Paxos anchor at $\Nnodes=188$ lies outside this sweep's grid and
2339:remain \texttt{SUBLINEAR-INTERMEDIATE}. The measurements bound the effect of
2392:committed cases, not the cause of the residual. Because the densification
2393:hypothesis is falsified, they do not justify the broader claim that
$ grep -nE 'not reproduced|SUBLINEAR-INTERMEDIATE|alpha CI' docs/validation/addition15/README.md
8:Decision rule: If the CI for alpha contains 0 and excludes 1, conclude A. If it contains 1 and excludes 0, conclude B. If it excludes both, conclude SUBLINEAR-INTERMEDIATE. If it contains both, conclude indeterminate.
27:The Paxos anchor at n=188 is not reproduced in this round. The cross-N residual across the whole domain is NOT IDENTIFIABLE (there is no external reference that scales with N to compare against). The previous analysis that scaled a constant 100.0/57.8 by N/180 or N/188 was an ungrounded model, not a measurement.
88:For 2PC over CE, the alpha CI is [0.13101, 0.14365]. By the decision rule, we conclude SUBLINEAR-INTERMEDIATE.
90:For Paxos over CE, the alpha CI is [0.11596, 0.13221]. By the decision rule, we conclude SUBLINEAR-INTERMEDIATE.
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
166:pipeline sustains, on average, about 12 concurrent proposals for Paxos and
174:boundary: 2PC over \CI{} reaches a commit rate of only 0.2\,\%, while TOM
318:simulator, we find that the pipeline sustains about 12 concurrent proposals
325:per-decision latency varies by roughly $27\times$ while per-decision energy
328:commits only 0.2\,\% of proposals, while TOM pipeline depth reaches about 26
2576:only 0.2\,\%}, whereas the same protocol commits 100\,\% of proposals on
2620:pipeline depth as well, where $\Cdepth$ for TOM over \CI{} jumps from
2723:commit rate of only 0.2\,\%, while TOM pipeline depth reaches about 26 and
```

## Figure and table inventory

No active external figure/table include exists: all 14 `\includegraphics` lines are commented, and all tables are inline. `paper/figures/` is absent. Commented references name missing files: `pipeline_mechanism.pdf`, `message_frame.pdf`, `paxos_ci_example.pdf`, `throughput_vs_nodes.pdf`, `throughput_vs_loss.pdf`, `latency_vs_nodes.pdf`, `progress_over_time_log.pdf`, `progress_over_time.pdf`, `energy_mean_ci_ce.pdf`, `energy_boxplot.pdf`, `latency_vs_energy.pdf`, `efficiency_vs_nodes.pdf`, `throughput_vs_topology.pdf`, `latency_vs_topology.pdf`. Several generated filenames differ (`fig_energy_*`, `thr_vs_topology.pdf`, `lat_vs_topology.pdf`). The manuscript's pooled boxplot claim corresponds to `plots/energy/energy_boxplot_15seed.{pdf,png}`, generated by `docs/validation/addition7/scripts/addition7_boxplot.py`, not by `tools/regen_figures.py`.

```text
$ grep -nE '\\includegraphics|\\graphicspath' paper/paper.tex
28:  \graphicspath{{figures/}}
32:  \graphicspath{{figures/}}
1585:\includegraphics[width=3.4in]{throughput_vs_nodes.pdf}
1658:\includegraphics[width=3.4in]{throughput_vs_loss.pdf}
1740:\includegraphics[width=3.4in]{latency_vs_nodes.pdf}
1814:  \includegraphics[width=1.65in]{progress_over_time_log.pdf}%
1818:  \includegraphics[width=1.65in]{progress_over_time.pdf}%
2070:\includegraphics[width=3.4in]{energy_mean_ci_ce.pdf}
2108:\includegraphics[width=3.4in]{energy_boxplot.pdf}
2157:\includegraphics[width=3.4in]{latency_vs_energy.pdf}
2229:\includegraphics[width=3.4in]{efficiency_vs_nodes.pdf}
2325:  \includegraphics[width=1.65in]{throughput_vs_topology.pdf}%
2329:  \includegraphics[width=1.65in]{latency_vs_topology.pdf}%
$ grep -nE 'energy_boxplot_15seed|addition7_boxplot' tools/regen_figures.py docs/validation/addition7/scripts/addition7_boxplot.py
docs/validation/addition7/scripts/addition7_boxplot.py:58:    plt.savefig(f"{OUT}/energy_boxplot_15seed.{ext}")
docs/validation/addition7/scripts/addition7_boxplot.py:61:print(f"wrote {OUT}/energy_boxplot_15seed.pdf / .png")
```

## Sources added in round 24 (step 2.10-b)
| Claim | Paper location | Evidence file | Verdict |
|---|---|---|---|
| Progress curves (Fig 13/14) | Fig. fig:progress-lin / fig:progress-log | `docs/validation/paper-audit/sources/progress_snapshots.csv` | SOURCED |
| Slots per decision `4.70`, `6.17`, `4.68`, `24.34` | — | `docs/validation/paper-audit/sources/slots_per_decision.md` | MISMATCH (pooled: 4.70-5.97 / 4.68-24.34; per-seed mean: 4.70-5.97 / 4.68-24.34) |
| Energy distribution extrema | — | `docs/validation/paper-audit/sources/distribution_stats.csv` | SOURCED |
| Integer multiple check | 612,2425 | `docs/validation/paper-audit/sources/integer_multiple_check.md` | SOURCED |
| Line 2PC energy/efficiency | — | removed from text | REMOVED |
| Proposal sharing share `1.6%` | — | `docs/validation/paper-audit/sources/proposal_sharing_candidates.md` | UNSOURCED |

## Corrections in round 25 (step 2.10-c)
- Proposal sharing share: 4.57% withdrawn (invalid mix of fresh numerator and frozen denominator).
- Slots per decision: estimator corrected from per-seed mean to pooled (sum/sum) to match paper definition.
- Progress curves: 99-versus-100 is a disclosed reporting/counting mismatch, not a repaired simulator bug.
- Test count corrected to 9 / 3 / 22 (superseding stale 9 / 3 / 20).

## Corrections in round 26 (step 2.7-R)
- Reference Provenance (R2): Replaced the misleading ungrounded cross-N residual extrapolation of the 100.0/57.8 slots with explicit anchor-only comparison and marked cross-N tracking as NOT IDENTIFIABLE.
- Density Control (R1): Hardened uniform density selection to eliminate append-induced contamination and use a deterministic W=10 window.

## Known internal staleness

This file is now completely rebuilt and synchronized against `main` at the current commit.
