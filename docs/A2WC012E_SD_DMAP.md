# A2WC012E — Delta MAP support in MerpMod (source-only change)

Status: **SOURCE PATCHED / NOT BUILT / NOT VEHICLE-VALIDATED**.

The changes in this fork make the existing optional MerpMod `SD_DMAP` code path available for the **A2WC012E 512-KiB SH7055 target**. No BIN, S-record, release patch or ECU flash has been produced.

## Controls: two different switches

| Setting | Value | Meaning |
| --- | --- | --- |
| `DefaultMafMode` / "Speed Density Mode" | `1` | Use MAF sensor for final airflow |
| `DefaultMafMode` / "Speed Density Mode" | `2` | Use calculated Speed Density airflow |
| `DefaultMafMode` / "Speed Density Mode" | `3` | Blend SD and MAF using the SD Blending Table |
| `SD_DMAP` (compile-time) | `0` | Do not compile Delta MAP correction |
| `SD_DMAP` (compile-time) | `1` | Compile Delta MAP correction and its definition |

**Do not use `SD_DMAP = 2` as an SD mode.** It is not a separate engine operating mode. The compiler code treats any nonzero `SD_DMAP` as enabled, but the documented option is 0/1.

The fork now configures `SD_DMAP = 1` only in `MerpMod/Targets/A2WC012EConfig.h`. Other targets remain unchanged.

## Two separate 7×7 compensation tables

The source already contains:
1. `AtmosphericCompensationTable` — atmospheric-pressure compensation (MAP × atmospheric-pressure axis).
2. `SDDeltaMapTable` — Delta MAP compensation (Delta MAP × engine-speed axis).

Both act as independent multipliers in the same SD airflow calculation:

```text
VE(MAP,RPM) × MAP × RPM × Displacement × SDConstant / IAT_kelvin
     × AtmosphericCompensation(MAP,AtmosphericPressure)
     × DeltaMapCompensation(DeltaMAP,RPM)    [when SD_DMAP=1]
     = SD airflow
```

`SDDeltaMapTable` in `SpeedDensityTables.c` has a neutral 7×7 matrix:

```text
Delta MAP columns: 0, 333, 666, 1000, 1333, 1666, 2000
RPM rows:          500, 800, 1000, 1200, 2000, 3000, 6000
Cells:             16384 (neutral)
Multiplier:        0.000061037
```

Raw values and axes are the *historical source defaults*, **not validated physical units for the A2WC012E Delta MAP signal**. With all cells neutral, the expected multiplier is approximately 1.0.

## Implementation changes

- Enabled the existing `#if SD_DMAP` sections for A2WC012E only.
- Added target-specific candidate `pDeltaMap = (float*)0xFFFFAF88`, from prior research.
- Fixed a typo in `Definition.c`: `DEFINE3D` → `DEFNEW3D`, so the exported metadata will include the Delta MAP 3D table when compiled.
- Kept `DefaultMafMode` as sensor mode `1` by default.
- Added a compile-time error if another target enables `SD_DMAP` without providing `pDeltaMap`.
- Added a source-level unit test assertion that the neutral Delta MAP compensation remains approximately 1.0.

## Sources and qualifications

Prior A2WC012E research:
- [MerpMod target address map](https://github.com/kolpakovden/forester_A2WC012E/blob/main/docs/merpmod-a2wc012e-address-map.md)
- [Historical v45 experimental Delta MAP build](https://github.com/kolpakovden/forester_A2WC012E/blob/main/roms/experimental/v45/README.md)
- [SD/transient analysis, including distinction between atmospheric and Delta MAP tables](https://github.com/kolpakovden/forester_A2WC012E/blob/main/docs/sd-transient-fueling.md)

The original `0x6A378` in the clean v25 is **Atmospheric Pressure Compensation**, not Delta MAP. The historic experimental Delta MAP block around `0x6AC40–0x6AD43` is **not** assumed to be the future MerpMod build address.

`pDeltaMap @ 0xFFFFAF88` remains a **candidate** until its units, freshness of the signal, memory lifetime and code references are validated against the exact target BIN. Source inclusion is not proof of safe real-engine behavior.

## Checks before any real-world patch

1. Identify exact input ROM (size, calibration ID, SHA-256).
2. Verify `pDeltaMap` representation, scale, producer/update cadence and RAM ownership.
3. Compile the relevant HEW/GNUSH target; check generated symbols and definition metadata (the source was not built for this change).
4. Confirm ROM/RAM allocations, patch section boundaries and required checksum.
5. Confirm neutral table causes no difference under representative input, including blending.
6. Validate experimentally with suitable sensors/logging and a known-good rollback.

The existing file names and the old Forester builds must not be mistaken for a generated, validated patch of this fork.

## License

MerpMod remains licensed under GNU GPL v3-or-later. This extension retains upstream attribution and license requirements.
