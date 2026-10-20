# A2WC012E — Delta MAP raw source, flags and scheduler chain

**Status: STATIC RESEARCH — not an ECU execution test. No new BIN; LAB v1/v2 are NOT FOR FLASH.**

Validated from the user-provided 512-KiB ROM images:

| Version | SHA-256 |
| --- | --- |
| clean v39 | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |
| experimental v45 | `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329` |

213 exact-hash, source-reference, opcode, calibration and descriptor checks passed in the separately delivered reproducible Python research package. Deliberately corrupted ROM was rejected.

## 1. Raw sensor → calibrated float at `0xFFFF90D8`

The original v39 function at `0x7544–0x7584` reads an input from `0xFFFF9020`, processes its 16-bit value (including `0x5616C` calibration), then uses helper `0x2520` to convert it with factor `5/65536` (ROM float literal `0x75CC`). This produces a voltage-like value.

At `0x7578` and `0x757C` it loads floats from `0x56164` and `0x56168` and uses `FMAC` at `0x7582`:

```text
float[0xFFFF90D8] = -414.0 + 514.199951171875 * convertedSensorVoltage
```

`0x56164` is explicitly called **Manifold Pressure Sensor Scaling** in the supplied OEM EcuFlash `A2WC012E.xml`, corroborating the source's role. The output is plausibly absolute pressure in mmHg from its conversion range; that **physical unit remains an inference**, not independent sensor validation.

## 2. FR15 and history buffer are no longer unknown

- `0x15156–0x1515C` loads **FR15 from `float[0xFFFF90D8]`** in a JSR delay slot. The checked helpers `0x1D0F8` / `0x1E6B0` do not write FR15.
- `0x15170..0x15172`: old `float[0xFFFFAFA0]` → `float[0xFFFFAF8C]`.
- `0x15176..0x15178`: old `float[0xFFFFAFA4]` → `float[0xFFFFAF90]`.
- `0x1517E..0x15180`: FR15 → `float[0xFFFFAFA4]` and `float[0xFFFFAFA0]`.
- Downstream code generates `AF88 = new(AF84) - previous(AF84)`.

Thus the `FR15` path uses an internally calibrated pressure, not an unidentified FPU input from outside this function.

## 3. Exact selector conditions

`0x1D0F8`: test `(RAM[0xFFFFC4CC] & 0x10) != 0`; output R0=2 when true, 0 otherwise.

`0x1E6B0`: test `(RAM[0xFFFFB469] & 0x80) != 0`; output R0=1 when true, 0 otherwise.

The mode branches at `0x15184–0x151A6` give:

| C4CC bit 0x10 | B469 bit 0x80 | AF84 source |
| --- | --- | --- |
| 0 | 0 | `(float[AF8C] + float[AF90])/2` |
| 0 | 1 | `FR15` = calibrated pressure at `FFFF90D8` |
| 1 | 0 | `(float[B0E0] + 0.083399996)/0.001650484977` |
| 1 | 1 | Same load-derived formula; first flag takes precedence |

**Do not infer driver mode, throttle action or update period from a flag bit alone.** RAM flag producers and timing are still to be traced.

## 4. Scheduling chain — corrected record boundaries; no defensible millisecond number yet

```text
CORRECTED descriptor at 0x46FC (index 6 of 19, stride 16):
  0x46FC : 04000200  task header; exact meaning unknown
  0x4700 : FFFF71CC  RAM state pointer
  0x4704 : 000064D6  callback
  0x4708 : 02000000  additional metadata
  0x470C : 04000300  NEXT task's header (NOT current task timing)

0x64D6 -> ROM pointer at 0x65F4 -> 0x110B8
0x110B8 -> ROM pointer at 0x112F0 -> 0x15148
0x15148 -> AF84 / AF88 producer
```

The descriptor's fields **have not been decoded**; the earlier 0x4700-based record alignment was wrong.
**Alignment correction:** this exact record layout is corroborated by the two SHLL2 instructions and the +4 field load in dispatch code. See [19-record audit](A2WC012E_SCHEDULER_DESCRIPTOR_AUDIT.md).
 This confirms an integration path but not `10 ms`, `15 ms` or another fixed sampling period.

## Next proof steps

1. Trace code that consumes task descriptors around `0x4700`, determine field meanings and scheduler period.
2. Find who sets/clears `0xFFFFC4CC.bit4` and `0xFFFFB469.bit7`.
3. Verify sensor scale, raw AF88 distribution and sample interval with safe read-only RAM logging.
4. Only then revisit the experimental unsigned `0..2000` Delta MAP axis. Do not flash lab ROMs before ABI/real `Pull3D`/checksum/bench validations.

See also [earlier AF84 analysis](A2WC012E_AF84_PRODUCER_PATHS.md) and [Pull3D study](A2WC012E_DMAP_SOURCE_PULL3D.md).
