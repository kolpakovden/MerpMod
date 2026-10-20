# v39 A2WC0MME — Delta MAP experimental lab artifact

**WARNING: OFFLINE RESEARCH ONLY. DO NOT FLASH. NOT ENGINE/ECU VALIDATED.**

On 2026-10-20 the original 524,288-byte `forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin` was supplied and its SHA-256 matched the v45 project reference.

- v39 original SHA-256: `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`
- v45 original SHA-256: `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`
- v39/v45 differences: **2,938 bytes** across both ROM code and calibration tables. A full v45 replacement would overwrite v39 tuning.
- Local proof-of-concept ROM SHA-256: `af8930ee6945cf170d5c82efa7fad89d459b408e38bc65496e5c0865852503f3`.
- Changed from original v39: **300 bytes**; all other 524,288-byte positions are preserved.

The local experimental proof of concept copies v45's Delta MAP table, descriptor and tiny calculation routine, retains the original MerpMod hooks and calibrations of v39, and adds a new **proposed** SH7055 byte-selector. Its files, full audit and reproducible builder were provided to the user as a separate **LAB / NOT FOR FLASH** archive; the unvalidated full binary is deliberately **not committed** to the firmware source repository.

## Candidate layout

| ROM | Meaning |
| --- | --- |
| `0x6A612..0x6A615` | v45's experimental branch to wrapper, `A3 85 00 09` |
| `0x6AC40` | 7 Delta MAP axis floats |
| `0x6AC5C` | 7 RPM axis floats |
| `0x6AC78` | 49 UInt16 neutral cells (`0x4000`) |
| `0x6ACDC` | v45 7x7 `ThreeDTable` descriptor |
| `0x6ACF8` | v45 Delta MAP multiply subroutine |
| `0x6AD20` | v45 wrapper returns to MerpMod `0x6A618` |
| `0x6AD3C` | wrapper function pointer redirected to `0x6AD50` selector |
| `0x6AD48` | **NEW** byte switch, `0=off` by default, `1=on`, all others off |
| `0x6AD50..0x6AD73` | **NEW** standalone selector + literals, SH-2/SH7055 instruction stream |

For `0` the proposed selector sends the input SD airflow to the caller without reading `pDeltaMap`; for `1`, tail-jumps to the original v45 subroutine `0x6ACF8`. **Static instruction-level path checks** passed for values `0`, `1`, `2`, `255`. This is **not** evidence of runtime ABI compatibility or safe operation.

## Proposed EcuFlash metadata

The lab XML uses the verified EcuFlash `A2WC0MME.xml` with **245 tables** (the previously working 243 + these two):

- `Delta MAP Compensation Enable` → byte `0x6AD48`, OFF / ON list.
- `Delta MAP Compensation` → 7x7 data `0x6AC78`, axes `0x6AC40` and `0x6AC5C`.

`Speed Density Mode = 1 MAF, 2 SD, 3 Blend` is **unchanged** at `0x69DD4`. Both standard `Primary Open Loop Fueling` and `Failsafe` remain exactly the original v39 tables selected by stock IAM logic, **not** user map banks.

## Limits before any flashing

- This laboratory binary is **not the result of compiling the current C branch**. It combines documented v45 machine code and a newly reasoned SH selector; the code in `SpeedDensity.c` is a **separate future build path**.
- The original v45 code was itself EXPERIMENTAL. Validate the patched SH wrapper's preservation of PR, R1 and floating registers in actual context; a static selector test does **not** prove this.
- The source and units/freshness of RAM `pDeltaMap` at `0xFFFFAF88` are not independently verified.
- The new ROM was **not checksummed**, dynamically emulated, bench-tested or vehicle-tested.
- EcuFlash must not be used to flash this lab ROM. Saving through EcuFlash may update checksum but does not validate machine code.
- A real usable build requires full disassembly/ABI review, runtime and fault-case tests, engine protection/LC/FFS regression, checksum, known rollback and bench verification.

Reference: [historical v45 research](https://github.com/kolpakovden/forester_A2WC012E/blob/main/roms/experimental/v45/README.md).
