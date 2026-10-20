# A2WC012E: where Delta MAP comes from, and how Pull3D reads it

**Status: byte-exact static analysis of supplied v39 and original experimental v45, not an ECU/bench validation. No firmware or flashing changes.**

## Sources and exact ROMs

| Source | SHA-256 |
| --- | --- |
| `Forester_SG9_MAP_clean_v39(1).bin` | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |
| `forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin` | `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329` |

The OEM code segments `0x150F0..0x1527F`, `0x2100..0x2153`, and `0x2580..0x26DF` are **byte-identical** in the two binaries.

## 1. Delta MAP producer — confirmed in the stock code

The RAM address `0xFFFFAF88` is not merely an alias from MerpMod's target header; it has a real producer in stock v39:

| PC | Opcode | Semantics |
| --- | --- | --- |
| `0x15150` | `9E81` | `MOV.W @(0x81,PC),R14`; literal at `0x15256` = `AF84` → sign-extended `0xFFFFAF84` |
| `0x15154` | `FEE8` | `FMOV.S @R14,FR14` — save earlier value from `0xFFFFAF84` |
| `0x151B8` | `FE2A` | `FMOV.S FR2,@R14` — update the same RAM slot on the observed path |
| `0x151BC` | `954F` | `MOV.W @(0x4F,PC),R5`; literal at `0x1525E` = `AF88` → `0xFFFFAF88` |
| `0x151C0` | `F3E8` | `FMOV.S @R14,FR3` — read updated `0xFFFFAF84` |
| `0x151C2` | `F3E1` | `FSUB FR14,FR3` — new value minus old value |
| `0x151C4` | `F53A` | `FMOV.S FR3,@R5` — store difference to `0xFFFFAF88` |

Therefore, on this code path, `pDeltaMap = current_AF84 - previous_AF84`. This proves the source and sign of the **arithmetic difference**, but **not** what physical units AF84 represents or how frequently the producer runs. A negative value is possible.

## 2. Consumer — reference v45 SH machine code

The actual reference code in the original v45 has the following inputs and call:

| PC | Opcode | Semantics |
| --- | --- | --- |
| `0x6ACFC` | `910B` | Load signed 16-bit `B218` at `0x6AD16` → `R1 = 0xFFFFB218` (RPM) |
| `0x6AD00` | `F518` | `FR5 = float[@R1]` |
| `0x6AD02` | `9109` | Load signed `AF88` at `0x6AD18` → `R1 = 0xFFFFAF88` |
| `0x6AD04` | `D405` | Load table descriptor pointer `0x0006ACDC` into `R4` |
| `0x6AD06` | `F418` | `FR4 = float[@R1]` |
| `0x6AD08` | `9107` | Load subroutine address `0x2110` |
| `0x6AD0A` | `410B` | `JSR @R1` — call `Pull3D` |
| `0x6AD0E` | `F0C2` | `FMUL FR12,FR0` — multiply returned coefficient into airflow |

The source points to independent `Delta MAP` and `RPM` inputs. It does **not** show an independent primary/failsafe AFR map switch.

## 3. What happens inside generic Pull3D

In the byte-identical original `Pull3D@0x2110`:

- `BSR` at `0x2114` calls the axis preparation helper at `0x26B8`.
- `MOV #16,R0; ADD R4,R0; MOV.B @R0,R6` at `0x2118..0x211C` reads the descriptor's table-type byte at offset `+16`.
- `MOVA` at `0x211E` locates a dispatch table at `0x2140`.
- `MOV.L @(R0,R6),R5` at `0x2120` selects a routine from that table.
- The Delta MAP descriptor has `type = 0x08000000`: type byte `0x08` selects entry `0x2148`, which points to `0x2654`.
- `MOV.L @(12,R4),R1` at `0x2122` reads the cell-data pointer. `JSR @R5` at `0x2124` invokes the selected reader.

This verifies table structure, inputs, dispatch and selected cell handler at the instruction level. **It does not fully validate the interpolation routine's FPU/calling conventions under real ECU execution.**

## 4. Axis handling from `0x2684..0x26B6`

The 26 actual SH opcodes in this helper are unchanged between v39 and v45. A narrow opcode-to-pseudocode translation was checked using the real Delta MAP and RPM axes:

- Below first axis value: select the first index with fraction zero.
- Within axis range: search backward for the lower interval and compute `(query - lower) / (upper - lower)`.
- At/above the maximum: select the last index with fraction zero.

**Practical implication:** the Delta MAP X-axis is `0,333,666,1000,1333,1666,2000`. An input `pDeltaMap < 0` clamps to **column 0**, not to a distinct negative-pressure compensation region. Inputs above 2000 clamp to the last column. This has been checked with a *model of the verified axis-helper opcodes*, not a complete MCU emulator.

## 5. Neutral-table precision

The genuine v45 descriptor at `0x6ACDC` contains:
- dimensions `7 x 7`;
- X header `0x6AC40`, Y header `0x6AC5C`, 16-bit cell data `0x6AC78`;
- all 49 cell words `16384 (0x4000)`;
- `multiplier = 6.103699706727639e-05` as an IEEE-754 float, zero offset.

The effective uniform multiplier is **`1.0000301599502563`**, which EcuFlash rounds to `1.000` (about **+0.003016%**, *not* exact unity).

The initial LAB table displayed in EcuFlash is correctly neutral to the displayed precision. The switch and table metadata being visible still do not establish execution correctness.

## Open questions before a flashable build

1. What physical units/scale does `0xFFFFAF84` use? This cannot be inferred safely from the producer alone.
2. How often is AF84 updated in actual conditions, and does the result at AF88 reflect a meaningful ΔMAP magnitude for an X-axis extending to 2000?
3. Are negative ΔMAP events intentionally intended to clamp at zero? Should a later table design support signed changes?
4. Full Pull3D interpolation, register/FPU ABI, failure paths and liveness through the SD wrapper remain to be verified.
5. Lab ROM checksum, bench testing, LC/FFS regressions and safe rollback still outstanding.

**No new BIN was written and neither LAB v1 nor LAB v2 is approved for flashing.**
