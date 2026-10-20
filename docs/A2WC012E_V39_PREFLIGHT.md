# A2WC012E / clean v39 — binary preflight (no patch yet)

Status: **SOURCE/BIN AUDIT PASSED — PATCH NOT BUILT**.

## Exact input

- Filename: `Forester_SG9_MAP_clean_v39(1).bin`
- Size: `524288` bytes (`512 KiB`)
- SHA-256: `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`
- Patched internal ID at `0x2000`: `A2WC0MME`
- Existing MerpMod signature at `0x69C10`: `A2WC012E.MeRpMoD.Gratis.Testing.v13.5.6.212`
- Existing SD mode `0x69DD4`: `2` (Speed Density)

This is a **previously patched ECU**. Applying a full fresh MerpMod release patch over it, or re-generating the table block from default `SpeedDensityTables.c`, would risk overwriting calibration/tuning and existing LC/FFS code.

## Read-only findings

| Region/address | Actual v39 bytes / state | Interpretation |
| --- | --- | --- |
| `0x077B4` | `00 06 A5 58` | Existing MAF/SD hook pointer to `0x6A558`, not a free hook |
| `0x6A612` | `F1 3C 71 1C` | Instruction site used by old experimental v45 |
| `0x6AC40..0x6AD43` | `FF` for all 260 bytes | Candidate for extra code/data; no guarantee it fits |
| `0x69DD4` | `02` | Existing SD setting |
| `0x59F4C` | 288-byte table | Primary Open Loop Fueling 16×18 |
| `0x5A108` | 288-byte table, identical | OEM Failsafe Open Loop Fueling 16×18 |
| `0x58CD0` | BE float ~`0.35` | IAM threshold for OEM failsafe fuel-map selection |

The [experimental v45 document](https://github.com/kolpakovden/forester_A2WC012E/blob/main/roms/experimental/v45/README.md) states a hook `0x6A612 = A3 85 00 09`, with a Delta MAP block `0x6AC40..0x6AD43`. **Those are historical v45 observations, not a safe transferable patch to v39**.

The SH2-family branch opcode `A385` at `0x6A612` would target `0x6AD20` using the PC-relative BRA formula, but that is only an instruction-level arithmetic check; it does **not** establish proper register/FPU state, execution order, re-entrant safety or restoration of displaced instructions.

## Outstanding blockers for a *working* BIN

1. Obtain and verify the reference experimental v45 bytes; the repo currently has the compressed `.bin.xz` but the connected GitHub text-only file reader cannot decode the archive. **Reference download:** [v45 .xz](https://github.com/kolpakovden/forester_A2WC012E/raw/refs/heads/main/roms/experimental/v45/forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin.xz). SHA-256 of decompressed BIN expected `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`.
2. Verify `pDeltaMap = 0xFFFFAF88` read cadence, raw units, volatility and ownership from reverse-engineered code or runtime trace.
3. Confirm the new runtime flag `DefaultSDDeltaMapEnabled` is linked in *ROM*, lookup is gated, and the EcuFlash `1D` definition uses its **final build address**, not a guessed fixed location.
4. Design a non-destructive patch method (or build from a clean stock ROM and selectively carry over v39 calibrations). **Do not re-apply MerpMod wholesale over this patched v39.**
5. Confirm ROM size, patch boundaries, embedded tables, checksum, hook ABI and existing LC/FFS behavior. Build and bench-test before any flash.

## Exact baseline guard

Run the read-only tool:

```bash
python tools/preflight_a2wc012e_v39_dmap.py clean_v39.bin --report preflight.json
```

It rejects any ROM that fails the exact SHA/expected bytes checks. Passing is a **necessary input check**, not an endorsement of an output BIN.

## Configuration of the source fork

- `SD_DMAP = 1` in the target config only means **compile support** for the algorithm and 7×7 table.
- `DefaultSDDeltaMapEnabled = 0` means disabled by default, if linked.
- `Speed Density Mode = 1/2/3` remains separate and already exists in clean v39.
- Primary OL and Failsafe OL remain the two separate **OEM** IAM-selected maps. Do not repurpose failsafe as user bank 2.

**No new v39 firmware or flashable patch was produced by this preflight.**


## v45 reference archive validation (2026-10-20)

The user supplied the purported v45 reference `forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin.xz`, downloaded from the Forester repository.

**Result: INVALID XZ ARCHIVE. No machine-code comparison performed.**

- Filename size: `14,999` bytes.
- SHA-256 of uploaded archive: `aeec7da9598621616f7afe6c1d84534ed299b5df8119a70b8a3b1b80c0fc335a`.
- Git blob SHA-1 of uploaded archive: `f161ff2cbb4be5309321415eaeb7718e9def208e`.
- This SHA-1 **exactly matches the Git blob** for the corresponding `.bin.xz` at `roms/experimental/v45/` in `forester_A2WC012E`; the issue is present in the repository artifact, not caused by download.
- Header bytes: `2D 6F 69 C0 1E D4`, while a valid XZ file should begin `FD 37 7A 58 5A 00`.
- Standard XZ/LZMA, gzip, bzip2, zlib, deflate, Brotli, Zstandard and LZ4 frame checks did not recognize it.
- Expected SHA-256 of **decompressed** v45 BIN from [original v45 documentation](https://github.com/kolpakovden/forester_A2WC012E/blob/main/roms/experimental/v45/README.md): `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`. This cannot be verified without the actual ROM data.

**Next action:** obtain the original full 524,288-byte `forester_sg9_sti_MAP_v45_DMAP_TEST_CHECKSUM.bin` directly from the PC/older archive, or a *genuine* XZ archive containing exactly that file. Then check SHA-256 before disassembly or patch integration. Do not treat the invalid `.xz` as an executable reference and do not copy `v45` hook bytes based only on README.

The exact original `v39` remains confirmed by the nine independent checks and has not been modified.
