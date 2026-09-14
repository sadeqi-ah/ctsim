# Archive Note: Withdrawn Claim (kept only for provenance)

Reference operating point: N=27, random topology, loss_rate=0.05, 15 seeds.
Source path: plots/scalability/results/sweep_summary.csv

Former paper text (removed in step 2.13):
> The rise from there to $5.67$ under 2PC is not proposal sharing, which
> accounts for $1.6\,\%$ of it; it is the number of slots a decision
> occupies, measured as total simulated slots per committed decision and
> summed over seeds, which runs from $4.70$ to $6.17$ under \CI{} against
> $4.68$ to $24.34$ under \CE.

Current accepted manuscript text:
The manuscript now says "is not driven by proposal sharing", and the pooled slots-per-decision range is 4.70-5.97 under CI against 4.68-24.34 under CE, per docs/validation/paper-audit/sources/slots_per_decision.md.

The available paper text plus the named CSV columns do not define two defensible arithmetic candidates for the antecedent of 'it'.
No preferred candidate is selected.
The claim 1.6% was withdrawn as UNSOURCED and no longer appears in the manuscript.
The withdrawn 4.57% calculation must not be used because it divided a fresh-run numerator by a frozen-sweep denominator.
