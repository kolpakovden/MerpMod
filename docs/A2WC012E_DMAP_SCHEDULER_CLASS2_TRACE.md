# A2WC012E — event-mask scheduler, task class 2, and Delta MAP producer

> **STATIC RESEARCH, NOT FOR FLASH.** No proof of a fixed task period yet.
> v39 SHA-256: `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`.
> Original v45 SHA-256: `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`.

## Correct task record

The ROM has 19 task descriptors at `0x469C` with 16-byte stride. Delta MAP producer's task #6 (7th entry) begins `0x46FC`:

| Offset | Address | Value | Role |
| --- | --- | --- | --- |
| +0 | `0x46FC` | `0x04000200` | task header; byte +2 is **2** |
| +4 | `0x4700` | `0xFFFF71CC` | state pointer |
| +8 | `0x4704` | `0x000064D6` | callback |
| +12 | `0x4708` | `0x02000000` | auxiliary field (unknown meaning) |
| next record | `0x470C` | `0x04000300` | **next** task header |

## What '2' actually means

Task-distribution helper `0x3F70`, called from init `0x3E70`, loads task header byte +2 (`0x3FB0 = 84D2`), moves it to R6 (`0x3FB2 = 6603`), then calls helper `0x3A1A` via JSR (`0x3FB4 = 4A0B`).

Helper `0x3A1A` uses R6 to set a **bit in a queue/event mask**:

- `0x3A2E = E207`: R2 = 7
- `0x3A32 = 2269`: R2 = R6 & 7
- `0x3A3A,0x3A3E,0x3A40 = 4021`: R0 = R6 >> 3 (three signed right shifts for nonnegative class)
- `0x3A3C = D134`: R1 = pointer `0xFFFF72E0` (literal at `0x3B10`)
- `0x3A42 = 310C`: R1 += R0
- `0x3A44 = D033`: lookup table `0x3DA8`
- `0x3A46 = 032C`: load bit from table
- `0x3A4A = 223B`, `0x3A4C = 2120`: OR into RAM and store

The table `0x3DA8..0x3DAF` contains eight byte masks `01 02 04 08 10 20 40 80`. Thus the task's `class=2` maps to `RAM[0xFFFF72E0] |= 0x04` **when this registration branch is taken**. The value is a queue class/bit index, **not** a validated 2 ms interval. Classes 0,1,2,3,4 appear with counts 1,9,4,2,3 among the 19 records.

## Execution mechanism (not timer evidence)

- During scheduler setup `0x3E70` calls `0x3F70` to register the tasks.
- `0x37F4 = 54D2` loads callback pointer from descriptor +8.
- `0x37FA = 422B` jumps to context startup `0x38A8` (literal `0x381C`).
- `0x38A8..0x38B2` loads the selected task's stack, writes the callback as exception-return PC, then executes `RTE` at `0x38B0`.
- Task `0x64D6` calls `0x110B8` (through literal `0x65F4`); in turn `0x110B8` calls the AF84/AF88 producer `0x15148` (literal `0x112F0`).
- After its work, `0x64D6` tail-jumps to scheduler handoff `0x3DB8` (literal `0x6580`).

The bitmask `0xFFFF72E0` is consumed by scheduler selection code beginning `0x3CE0`. This establishes scheduling and task switching; it does **not** show which peripheral timer/IRQ (or other event) makes task #6 ready on subsequent occasions.

**Do not equate the number 2 with 2 ms**, or infer its physical timing from the mere presence of a queue. The actual AF88 update interval may depend on scheduling and runtime conditions.

## Verification and next experiments

Local exact-hash static verifier `verify_event_dispatch.py` validated **32 opcode locations in each original ROM**, matching dispatch-code regions, task #6 record, callback chain, eight bitmasks, and the full 19-entry category distribution. Deliberately modified source images are rejected.

Next to establish actual cadence:
1. Follow the event/interrupt path that wakes or readies descriptor #6 / state `0xFFFF71CC`.
2. Identify the hardware timebase/clock divisor, and whether the producer executes once per event.
3. Validate against time-correlated **read-only** RAM logging on a bench or known-good running ROM. Ordinary slow OBD polling alone is not enough.
4. Only then evaluate the `Delta MAP X = [0,333,666,1000,1333,1666,2000]` calibration spacing.

Never flash either experimental LAB image on the basis of this static work.
