# Addition 14 — Published Slot Lengths

## 1. Purpose

This directory records the slot lengths used to convert published
millisecond latencies into slot counts, together with the primary source
of each constant.

## 2. Why the code and not the papers

The A2 paper never prints the slot length used for its 2PC experiment,
and Table 3 of the Wireless Paxos paper prints 4 ms for 2PC/3PC while
the firmware released with that same paper defines 4.75 ms. Where a
paper and its own released code disagree, this study cites the code and
discloses the disagreement.

## 3. Nominal versus realised

The macros are written as N*(RTIMER_SECOND/1000). With
RTIMER_SECOND = 32768 the integer division truncates to 32 ticks, so
every realised slot is 2.34 % shorter than nominal. ALL CONVERSIONS IN
THIS STUDY USE NOMINAL VALUES, because the papers themselves multiply
nominal values: 137 Join slots × 7.00 ms = 959 ms is exactly the figure
printed in the A2 paper's Table 2. The realised column is recorded as a
caveat only.

## 4. Caveat

Repository HEAD is not a guaranteed record of every published run.
MAX_SLOT_LEN at HEAD is 4.00 ms, but the Max experiment in A2
section 6.5 was run at 3.75 ms.

## 5. Conversions relied on by this study

| Conversion | Result |
|---|---|
| 475 ms / 4.75 ms = 100.0 slots | A2 2PC, N=180, Rennes |
| 289 ms / 5.00 ms = 57.8 slots | Wireless Paxos majority, N=188 |
| 633 ms / 5.00 ms = 126.6 slots | Wireless Paxos full completion |
| 959 ms / 7.00 ms = 137.0 slots | A2 Join, Euratech |

The `round_max_slots` column records the firmware's per-round slot
ceiling for the same blob, so that "the published figure is below the
cap" is a claim with a source rather than a number typed into a test.
