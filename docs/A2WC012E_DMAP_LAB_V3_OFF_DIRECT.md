# A2WC012E v39 Delta MAP — guarded LAB v3, OFF executes original SD instructions

> **EXPERIMENTAL OFFLINE RESEARCH. DO NOT FLASH ECU.** No checksum update, no full SH7055 emulator or bench validation. The binary described here is NOT produced by compiling the C sources in this branch.

## Motivation

Earlier LAB v1/v2 used the original experimental v45 wrapper even when the ROM switch was OFF. In v3 the disabled path executes the **original v39 instructions directly** instead of calling the v45 wrapper:

```asm
FMOV FR3,FR1
ADD #28,R1
FMOV.S FR1,@R1
```

The new switch remains at `0x6AD48` (`0` OFF, `1` ON, all other values OFF). EcuFlash's previously user-tested `A2WC0MME.xml` still contains 245 top-level tables. `ON` uses the genuine v45 Delta MAP wrapper and the original ROM `Pull3D@0x2110`.

## Reproducible input/output identities

| ROM | SHA-256 |
| --- | --- |
| Clean v39 524288-byte image | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |
| User-provided original v45 524288-byte image | `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329` |
| New LAB v3 `FORESTER_v39_DMAP_v3_LAB_DO_NOT_FLASH.bin` | `def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f` |

v3 differs from original v39 at exactly **308 byte positions**, exclusively in `0x6A612..0x6A615` and `0x6AC40..0x6AD83`. Thus all existing stock/vehicle calibration and LC/FFS code outside those regions remains byte-identical, including **both** OEM Primary and Failsafe Open Loop fuel tables (these are IAM-dependent, not manually switchable fuel banks).

## Hook/selector instructions

```asm
6A612 A39D    BRA 6AD50
6A614 0009    NOP             ; original overwritten hook
...
6AD50 2F06    MOV.L R0,@-R15
6AD52 D00A    MOV.L @(10,PC),R0  ; pointer to enable-byte address
6AD54 6000    MOV.B @R0,R0
6AD56 8801    CMP/EQ #1,R0
6AD58 60F6    MOV.L @R15+,R0
6AD5A 8905    BT 6AD68          ; ON when exactly 1
; OFF path:
6AD5C F13C    FMOV FR3,FR1
6AD5E 711C    ADD #28,R1
6AD60 F11A    FMOV.S FR1,@R1
6AD62 D205    MOV.L @(5,PC),R2  ; pointer 6A618
6AD64 422B    JMP @R2
6AD66 0009    NOP
; ON path:
6AD68 D205    MOV.L @(5,PC),R2  ; pointer 6AD20
6AD6A 422B    JMP @R2
6AD6C 0009    NOP
...
6AD78 0006A618  ; OFF return pointer
6AD7C 0006AD48  ; enable byte address
6AD80 0006AD20  ; ON wrapper pointer
```

The pre-existing v45 code copied at `0x6AC40..0x6AD43` has not been modified in LAB v3 (in particular the wrapper's function pointer still targets `0x6ACF8`). The flag byte at `0x6AD48` is 0.

**Register liveness:** OFF restores R0 and preserves FR0/FR4, and executes the actual original FR1 store. R2 and SR.T differ immediately after the hook, but original code overwrites R2 at `0x6A61E` and T at `0x6A622` before consuming them. This is *not* a claim of all-register CPU equivalence under all circumstances, interrupts or alternate FPSCR settings.

## New evidence: real Pull3D opcode-level evaluation

Earlier LAB tests substituted the table lookup with a stub. v3 research includes a narrower SH/FPU opcode interpreter **running the actual OEM `Pull3D@0x2110` plus axis helpers and 16-bit cell lookup**, with no 3D-function stub.

- **10 interpolation/boundary cases** on a temporary, distinct-cell 7x7 table verified OEM SH instruction output against an independent bilinear reference; maximum absolute discrepancy was below `6e-8`. Tests included negative Delta MAP, interior interpolation, limits and out-of-range values.
- **64 complete hook/selector/wrapper/real-Pull3D traces**: 4 choices (v39 / LAB v3 OFF / LAB v3 ON / LAB v3 invalid=255) × 8 Delta MAP/RPM points × 2 starting SR.T states.
- In these tests OFF (and invalid) matched original v39 airflow *exactly*; ON produced the table-derived result. PR, stack and FR12 returned to the modeled original values.
- Rebuild from the two source ROMs reproduced v3 SHA-256 byte-for-byte; the supplied EcuFlash metadata has 245 top-level tables and the previous OFF/ON selection.

Test-only, nonneutral cell values were applied **only in memory**; the distributed v3 LAB ROM keeps v45's neutral table (`16384 × float32(0.000061036997..) ≈ 1.00003016`).

## Outstanding blockers before any real ECU

1. Independent full SH7055/FPSCR/interrupts/ABI verification and bench execution.
2. Establish Delta MAP update distribution and proper axis units/spacing from trustworthy *read-only* runtime observations. The original v45 `0..2000` axis clamps negative readings to the first column.
3. Correctly validate Subaru checksum and recovery strategy **after** proof of code behavior; auto-fixing checksum is not code validation.
4. Verify engine safeguards, LC/FFS, MAF/SD/Blend and fueling transitions on a bench under controlled conditions.
5. Decide how/if the separate MerpMod C-source branch will be compiled and integrated; **LAB v3 is still a manually reasoned ROM prototype**.

The ZIP with ROM, EcuFlash XML, portable rebuild/test scripts and machine-readable reports was delivered within the user conversation (not committed to GitHub).

**DO NOT FLASH LAB v1, v2 OR v3.**
