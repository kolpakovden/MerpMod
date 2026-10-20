# v39 Delta MAP LAB v3 — extended functional & ABI review

> **EXPERIMENTAL / NOT FOR FLASH.** Static ROM audit and restricted SH-opcode execution, **not** a full SH7055 emulator, hardware test or checksum correction.

## Provenance

- Original v39 SHA-256 `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`
- Reference experimental v45 SHA-256 `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`
- LAB v3 SHA-256 `def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f`

Independent raw byte compare: v3 has **308 changed bytes** vs v39, confined to `[0x6A612,0x6A616)` and `[0x6AC40,0x6AD84)`. Everything else, including existing vehicle/LC/FFS/VE and both **stock OEM Primary and Failsafe OL fuel maps**, remains byte-identical.

## Correct memory context

A problem in early *test setup*, not proven a ROM defect, was fixed: after the hook, v39 accesses mode, SD, MAF and blend ratio from slots based at `0xFFFFCA00`:

| Slot | Meaning |
| --- | --- |
| `0xFFFFCA15` | MAF=1, SD=2, Blend=3 |
| `0xFFFFCA1C` | SD airflow |
| `0xFFFFCA20` | MAF airflow |
| `0xFFFFCA2C` | SD blend ratio |

Earlier isolated traces initialized R1 to `0xFFFFCA60`, which validated only the local hook and **not** the actual later SD read. The new test initializes R1 to `0xFFFFCA00` and runs the original post-hook instructions until after the final `FMOV FR1,FR0` at `0x6A6A0`.

## New tests: 1080 opcode traces

Using a **temporary in-memory** 7×7 test table with 49 distinct cells:

- Modes MAF, SD and Blend (1/2/3).
- MAP samples 585, 645, 705, 765 yielding blending ratios 0, ~0.196, ~0.588, ~0.980.
- Delta MAP samples -40, 250 and 1800, RPM 850, 2500 and 5900.
- Two initial T flag states.
- Five images/variants per combination: original v39, v3 switch 0, v3 switch 1, v3 switch 2, v3 switch 255.

This yields **216 combinations / 1080 real-opcode-model traces**.

| Check | Pass |
| --- | --- |
| OFF matches original v39 final airflow, saved SD, and **all modeled CPU registers/state** after mode selection | 216/216 |
| Invalid flags 2 and 255 behave just like v39, including all modeled CPU registers | 432/432 |
| ON matches a **separately implemented mathematical bilinear oracle** for the SD path and final MAF/SD/Blend result | 216/216 |

The Python opcode simulator is **the same narrow instruction interpreter** used in earlier tests; the new test harness, RAM setup and bilinear math are independently authored. **These are additional test cases, not execution by an independent CPU engine.**

In v3 ON, the calculated SD airflow follows `SD_base × K(DeltaMAP,RPM)`, and Blend follows `MAF × (1 - ratio) + (SD_base × K) × ratio`. In MAF mode the final returned airflow is unchanged in the tested conditions.

## Register and FPU ABI context

Official SuperH compiler notes by Renesas describe R8–R14 and FR12–FR15 as call-preserved, whereas R0–R7 and FR0–FR11 can be overwritten by a callee. Source references:

- https://www.renesas.com/en/document/apn/superh-cc-compiler-package-application-note
- https://www.renesas.com/en/document/apn/sh-compiler-application-note-2-compiler-use-guide-efficient-programming-techniques

The v3 wrapper's observed ON-path differences from v39 at the output include **R0, R3–R6 and FR2–FR4** (with final values varying by MAF/SD/Blend); these are scratch/argument registers in the documented interface. No differences in preserved R8–R14, FR12–FR15, SP or PR were observed in the modeled paths.

OFF and flags 2/255 match all modeled CPU registers and SR.T after the original mode branches, even though R2 and T differ *temporarily* immediately after the hook (they are overwritten before use by original code).

**Not yet verified**: hardware FPSCR operation mode, floating exception behavior, asynchronous interrupts, timing and full instruction-set emulation. The C-source branch is not the source of this manually assembled experimental LAB ROM.

## Remaining stop conditions

1. Full CPU/FPU/FPSCR/interrupt/ABI validation in an independent SH7055 emulator or controlled hardware bench.
2. Determine the Subaru ROM checksum region and algorithm and validate it separately, **without confusing a checksum fix with successful code execution**.
3. Validate target read-only Delta MAP signal range/units/update cadence; the supplied axis 0–2000 clamps all negative deltas into column 0.
4. Bench-test MAF/SD/Blend and LC/FFS regression, startup and fail-safe paths; have a recovery method and original image ready.

**The v3 binary is NOT approved for ECU flashing.**

The user was provided a separate `A2WC012E_DMAP_LAB_v3_INDEPENDENT_REVIEW_NOT_FOR_FLASH.zip` with the reproducible test runner, narrow interpreter, JSON regression report and detailed Russian README. Original ROMs and LAB BIN are not included in that report bundle.
