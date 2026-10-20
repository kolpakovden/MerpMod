# v39 Delta MAP — post-hook liveness reassessment

> **RESEARCH ONLY. NOT FLASHABLE.** This note corrects premature claims in the first ABI review. The evidence is direct big-endian SH instruction decoding in the exact v39 image (SHA-256: `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`).

## Why the initial conclusion needed correction

At `0x6A61E` the opcode is **`621C` = `EXTU.B R1,R2`**, **not** `FMOV FR1,FR2`. This matters:

- After the hook, `R2` is overwritten at `0x6A61E` **before** the mode compare at `0x6A622`. Thus v45's temporary use of R2 as a jump register need not change the mode comparison.
- `3210` (`CMP/EQ R1,R2`) at `0x6A622` overwrites **SR.T** before `8F05` (`BF/S`) at `0x6A624`. Thus the selector's T-flag change is not necessarily a functional problem at that branch.
- All three mode branches **reload FR1 from memory** before `FR1` is copied to `FR0` at `0x6A6A0`. Therefore the fact that v45 does not set FR1 to the calculated result at the hook exit is a register snapshot difference, **not** a proven functional defect.

## Verified branch flow

| ROM address | Opcode | Meaning |
| --- | --- | --- |
| `0x6A612` | `F13C` | FMOV FR3,FR1 (original v39) |
| `0x6A614` | `711C` | ADD #28,R1 |
| `0x6A616` | `F11A` | FMOV.S FR1,@R1 |
| `0x6A61E` | `621C` | EXTU.B R1,R2 — overwrite R2 |
| `0x6A622` | `3210` | CMP/EQ R1,R2 — overwrite T |
| `0x6A624` | `8F05` | BF/S to `0x6A632` |
| `0x6A62C` | `F118` | SD branch: load RAM airflow into FR1 |
| `0x6A62E` | `A037` | BRA to `0x6A6A0` |
| `0x6A63E` | `8F2C` | BF/S to `0x6A69A` |
| `0x6A64E` | `F128` | Blending branch: reload FR1 |
| `0x6A696` | `A003` | BRA to `0x6A6A0` |
| `0x6A69E` | `F118` | MAF fallback branch: reload FR1 |
| `0x6A6A0` | `F01C` | FMOV FR1,FR0, final result |

All instructions and branch offsets were checked against the exact v39 bytes.

## Interpretation of LAB v1 and LAB v2

The initial opcode-level harness correctly observed **different immediate CPU snapshots** at `0x6A618`, but incorrectly promoted them to proof of a bug in the v45 algorithm. The later branch flow shows that `FR1`, `R2` and `T` differences **may be dead** before they affect the output.

LAB v2 independently demonstrates that restoring FR1/R2 is possible using 3 changed instructions, but **it is not established that this change is required or superior**. Both LAB v1 and v2 are experimental; **do not flash either**. The XML ON/OFF and 7x7 displaying correctly is only metadata/UI validation.

## Still unresolved

- Complete liveness across the wrapper for general-purpose and floating registers (especially **R0/R4 and FR0/FR4/FR5**), and branch/interrupt timing.
- Full ABI and side effects of **real** `Pull3DFloat@0x2110` (the Python test uses a stub returning a known 7x7 corner; it does not implement the OEM routine).
- Raw units, producer path, update cadence and RAM ownership of `pDeltaMap@0xFFFFAF88`.
- Flash checksum, ECU bench execution and LC/FFS regression.

Keep the project at **EXPERIMENTAL / NOT FOR FLASH** until these checks are closed. In particular, a mismatch in a temporary CPU register is not necessarily a defect; determining whether a value is live is the relevant test.
