# A2WC012E v39/v45 — AF84 producer paths and raw Delta MAP units

**Status: STATIC OPCODE RESEARCH / NOT FOR FLASH**. No ROM modifications were made.

Original ROM evidence:
- v39 `Forester_SG9_MAP_clean_v39(1).bin` (524288 bytes), SHA-256 `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`
- v45 `forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin` (524288 bytes), SHA-256 `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`

The two ROMs contain byte-identical producer code in `0x15148..0x151C5`.

## Confirmed output

`0x15150` reads the pointer to `0xFFFFAF84`. `0x15154` saves the previous float in `FR14`. `0x151BC` reads the pointer to `0xFFFFAF88`. `0x151C0..0x151C4` subtracts prior AF84 from new AF84 and writes **`AF88 = new(AF84) - old(AF84)`**.

**Important correction**: AF84 is **not necessarily a single unfiltered MAP sensor value**; its producer has multiple branches.

## Three observed AF84 source paths

1. **Average of two RAM floats:** `0x1519C..0x151A4` loads `0xFFFFAF90` and `0xFFFFAF8C`, adds them and multiplies by a ROM literal `0.5` at `0x1527C` (in the BRA delay slot). Thus `AF84 = (AF90 + AF8C) / 2` on that path.
2. **Derived from Engine Load:** `0x151A6..0x151B8` reads `0xFFFFB0E0` (labeled `pEngineLoad` in MerpMod), adds float constant `0.083399996` at `0x575F8`, and divides by float constant `0.001650484977` at `0x575F4`: **`AF84 = (EngineLoad + 0.083399996) / 0.001650484977`**. Physical units of AF84 are not independently proven; the input name `pEngineLoad` comes from the target header.
3. **Caller-provided FPU value:** `0x15190` branches to `0x151BA` with a delay-slot `0x15192` that writes `FR15` into `AF84`. Origin and units of incoming `FR15` still require tracing.

The relevant conditional branches were checked at `0x15184, 0x1518C, 0x15198`, with `BRA` at `0x15190` and `0x151A2`. These paths are **observed in machine code**, but their conditions in real driving and the producer cadence are not yet validated.

## Static call chain (not a timing determination)

The literal at `0x112F0` points to `0x15148`. Code at `0x110C6..0x110C8` loads that function pointer and performs `JSR`. The dispatcher pointer at `0x65F4` refers to `0x110B8`. This identifies a call path; it **does not establish a 5/10/15 ms update rate**.

## Calibration implications

The experimental v45 Delta MAP X-axis is `[0,333,666,1000,1333,1666,2000]` (raw/unverified units). The SH axis lookup clamps values below zero to the first column, so negative transients have no dedicated X-axis region.

On the **load-derived** AF84 path alone, a change of `0.1` in the `pEngineLoad` float yields a change of about `60.6` internal AF84/AF88 units, assuming adjacent updates stay in the same branch. The axis may be coarse for small transients, but one cannot recalibrate it from this fact alone: other paths may use different raw ranges.

## Next evidence needed

- Trace provenance and physical scaling of incoming `FR15` and the two source floats `0xFFFFAF8C/AF90`.
- Resolve which flags select each producer path.
- Identify the scheduler/task period that calls `0x110B8`; verify against timestamped runtime readings.
- Compare AF84, AF88, AF8C, AF90, Engine Load, MAP, TPS, RPM in a safe **read-only RAM logging** setup, only after logger/addresses are verified.
- Then decide on the future Delta MAP axis and separate runtime tests of the LAB hooks/ABI/checksum. **No LAB BIN is currently approved for flashing.**

An independent 88-check, exact-hash Python static verification was run locally on both source images, including a deliberate mutated-opcode rejection test. The script and JSON audit were delivered as a separate reproducible research package.
