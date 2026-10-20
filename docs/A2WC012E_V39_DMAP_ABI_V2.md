# A2WC012E — v39 Delta MAP ABI analysis (LAB v1 → LAB v2)

> **2026-10-20 REASSESSMENT:** Earlier claims of a proven v45 FR1/R2 functional bug were **premature**. The correct opcode at `0x6A61E` is `621C = EXTU.B R1,R2`; R2 and T are overwritten before their immediate use, and FR1 is reloaded from RAM in MAF/SD/Blend branches. See [post-hook liveness](A2WC012E_V39_POSTHOOK_LIVENESS.md). Both LAB images remain **NOT FOR FLASH**.

> **OFFLINE RESEARCH ONLY. DO NOT FLASH EITHER LAB ROM TO ECU.**
> The checks below used a narrow Python interpreter for selected SH opcodes, with a **test stub** for the ROM's Pull3D routine at `0x2110`. This is **not** an MCU emulator, bench test, or confirmation of ABI safety.

## Confirmed input binaries

| Image | SHA-256 |
| --- | --- |
| Forester clean v39 | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |
| Experimental v45 reference | `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329` |
| First LAB v1 | `af8930ee6945cf170d5c82efa7fad89d459b408e38bc65496e5c0865852503f3` |
| Experimental LAB v2 | `969a6f0b6af50309a9cc3d2f9368badebaa9f0036e4c8fca081cb925209982ac` |

All are 524288-byte images. v2 differs from v1 in **four byte positions** within the three instructions at `0x6AD34..0x6AD39`; it differs from untouched v39 in **300 bytes** total.

## Register snapshot differences (NOT a confirmed defect)

Original v39 at `0x6A612`:

```asm
6A612  F13C  FMOV    FR3,FR1
6A614  711C  ADD     #28,R1
6A616  F11A  FMOV.S  FR1,@R1
6A618  9148  MOV.W   ...
...
6A61E  F21C  FMOV    FR1,FR2
```

The v45 reference replaces `0x6A612` with a jump to `0x6AD20`. Its wrapper moves `FR3` into `FR4`, calls the Delta MAP multiplication routine `0x6ACF8`, and writes `FR0` into `@R1`. **It does not update `FR1` before returning to `0x6A618`**, but `FR1` is later reloaded from memory on each MAF/SD/Blend path. Therefore the reference implementation and LAB v1 are **not immediately state-equivalent** at the hook exit; this does **not** establish a functional defect.

Additionally v45 uses `R2` as a jump register on returning to the original MerpMod code, overwriting the prior value of `R2` temporarily; the original code overwrites R2 again at `0x6A61E` before the compare.

## LAB v2 experimental snapshot-restoration changes (not established as necessary)

| Offset | LAB v1 | LAB v2 | Intended change |
| --- | --- | --- | --- |
| `0x6AD34` | `D202` — PC-relative pointer into R2 | `D002` — pointer into R0 | Avoid clobbering R2 |
| `0x6AD36` | `422B` — JMP @R2 | `402B` — JMP @R0 | Keep return semantics |
| `0x6AD38` | `0009` — NOP | `F10C` — FMOV FR0,FR1 | Restore FR1 during the JMP delay slot |

This **does not** establish ABI correctness or functional equivalence. `R0` was already changed by the on/off selector; using it as a return pointer reduces new clobbers but does not preserve original `R0`.

## Narrow SH instruction-level trace

The trace starts at the actual byte sequence `0x6A612`. Initial SD input `FR3=37.125`, distinct `FR1=12.125`, with a saved PR and stack pointer. For `ON` the 7×7 lookup routine `0x2110` is replaced by a test-only stub returning the **known first cell**; no interpolation algorithm is claimed.

| Input branch | RAM airflow at output | Final FR1 | R2 restored | PR/SP restored | T flag maintained when initially 1 |
| --- | ---: | ---: | --- | --- | --- |
| Original v39 | 37.125 | 37.125 | Yes | Yes | Yes |
| LAB v1 OFF | 37.125 | 12.125 | No | Yes | **No** |
| LAB v2 OFF | 37.125 | 37.125 | Yes | Yes | **No** |
| LAB v2 ON (all-neutral map) | ~37.12612 | ~37.12612 | Yes | Yes | Yes (for the tested initial T=1) |

A **test-memory-only**, non-neutral first cell set to about 1.10 gave ~40.84 with `ON` and 37.125 with `OFF`. This demonstrates branch selection under the deliberately limited model; it does **not** validate the real OEM 3D algorithm.

## Remaining questions and blockers

**Important: LAB v2 OFF is still NOT transparent to original v39.**

- The new conditional selector `CMP/EQ` changes **SR.T** at hook exit. The original code executes another `CMP/EQ` at `0x6A622` before the subsequent conditional branch, so this difference may be dead in the observed path. Wider liveness/interrupt-context review is still required.
- The wrapper changes **R0**, **FR0** and **FR4** even when OFF; ON can additionally change **R4**. Liveness and subsequent use have not been proven.
- Reference v45 itself is EXPERIMENTAL; inheriting its multiply logic gives no guarantee of safety.
- The model stubs `Pull3DFloat@0x2110`, knows nothing about other registers altered by the actual ROM function, FPU/FPSCR modes, interrupts, timing or RAM lifetime.
- Signal `pDeltaMap@0xFFFFAF88` physical units and producer/update cadence are not independently validated.
- Checksum was not corrected or verified; no bench/ECU/road validation.

**Required next implementation:** design a wrapper preserving the full state that is live across the hook, including SR.T, and verify it with real disassembly/SH7055 execution before attempting a checksum/bench test. A truly disabled mode must behave identically to v39, not merely produce the same one output variable under a test.

### Source and artifacts

User-provided original v39/v45 and LAB ZIP were examined locally. The binary LAB v2 was intentionally **not committed** to GitHub. The ZIP contains the full read-only audit and a limited opcode trace harness. The EcuFlash definition remains unchanged (245 tables; ON/OFF) from the previously visually checked version.
