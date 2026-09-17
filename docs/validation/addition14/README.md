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

## 6. Round-cap provenance notes

These notes qualify the `round_max_slots` values that have no home in
the CSV schema (there is no note column, and prose does not belong in
a numeric cell).

- `MAX_SLOT_LEN` (max): `MAX_ROUND_MAX_SLOTS` in
  `lib/max/max.h` (blob `515e83301bf32bca450b38c9f096da69570f169e`)
  is an overridable default, not a fixed constant: it is wrapped in
  `#ifndef MAX_ROUND_MAX_SLOTS` with a `#warning "define
  MAX_ROUND_MAX_SLOTS"`. The recorded value 255 is therefore the
  project default at that commit, and any build that defines the
  macro itself runs with a different cap.
- `ASSOCIATION_SLOT_LEN` (join): `chaos/chaos-config.h` (blob
  `0122c69fb6da7113c68271090b36f1fe58937776`) defines only
  `ASSOCIATION_SLOT_LEN`; it contains no round-slot-cap macro, so
  the upstream value is undefined and the cell retains the literal
  `NA` (the test suite skips `NA` rows when checking caps).
- `THREE_PC_SLOT_LEN` (3pc): `THREE_PC_ROUND_MAX_SLOTS` in
  `lib/3pc/3pc.h` (blob `7cdec10cd686c215a9e3a961967448b896840b68`)
  is a plain `#define THREE_PC_ROUND_MAX_SLOTS (350)`, with no
  `#ifndef` guard, so 350 is the fixed upstream value.
