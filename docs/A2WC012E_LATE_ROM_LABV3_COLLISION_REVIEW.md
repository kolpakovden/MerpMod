# A2WC012E — hardware history review and LAB v3 integration blocker

> **STOP: NEVER FLASH v39 LAB v3 AS IF IT WERE AN UPDATE FOR A LATER v68/v84/v85 VEHICLE ROM.** It is a separate, v39-based offline artifact. Its checksum PASS applies only to its own image.

## Repository evidence reviewed (2026-10-21)

Source of truth: [forester_A2WC012E](https://github.com/kolpakovden/forester_A2WC012E) `main`.

The repo **does** document repeated on-vehicle experiments, including executable hooks:
- `roms/experimental/v68/README.md` and `docs/launch-control-spark-cut.md`: user-confirmed v68 SPARK_CUT_ENABLED on-car RomRaider log `romraiderlog_20260902_001107.csv`. Result: launch MAP ~1.93 bar abs but fuel cut remained (IPW periodically ~0.77 ms). So v68 is **vehicle-tested, not clean spark proven**.
- `docs/rejected-experiments.md`: a direct, insufficiently validated airflow-limit BIN edit led to misfire/abnormal throttle response; previous working ROM was flashed successfully afterward. This demonstrates successful *software rollback in one recoverable case*, not the ability to unbrick an ECU with failed boot/flash communication.
- `docs/v85-ffs-spark-cut.md`: reproducible v84->v85 FFS patch and checksum workflow exist, but v85 remains **EXPERIMENTAL / vehicle validation pending**, not demonstrated currently installed ROM.
- `roms/experimental/README.md`: v45 historically introduced Delta MAP, v68 preserved its code and table. These are not conclusive evidence of active non-neutral correction or current ECU ROM identity.
- `docs/workflow.md`, `roms/README.md`: must keep known-good original/rollback and version-linked logs.

## Critical address collision: v39 LAB v3 vs newer LC ROM families

LAB v3 (from **clean v39**) modifies `0x6A612..0x6A615` and `0x6AC40..0x6AD83`, with selector `0x6AD50..0x6AD83` and literals at:
- `0x6AD78` — OFF return pointer
- `0x6AD7C` — enable-byte pointer
- `0x6AD80` — ON wrapper pointer

By contrast in the later `v67→v68` series:
- `tools/build_v68_spark_cut.py` explicitly labels the existing **Advanced LC block `0x6AD50..0x6ADC3`** and asserts it must stay preserved apart from intentional timing edits.
- `docs/launch-control-spark-cut.md` assigns **LC Advanced Fuel Mode `0x6AD78`**, **LC Advanced Fuel Target `0x6AD7C`**, Advanced Timing Mode `0x6ADB8`, Base Timing Lock `0x6ADBC`, LC Cut Mode `0x6ADC4` etc.
- The earlier `Delta MAP` table/code at `0x6AC40..0x6AD43` are also already preserved unchanged in v68, per the builder's explicit byte-for-byte check.

**Therefore the LAB v3 selector's address range COLLIDES with existing Advanced LC data/code in late firmware.** Neither mere byte-swap nor the known checksum fix makes LAB v3 compatible with later/current tuning. Do not transplant the whole v3 code or flash v39-based v3 on this SG9 assuming v84/v85 compatibility.

## Correct next engineering sequence

1. **Identify and secure the *actual ECU-installed ROM* and last known-good rollback** (filenames alone and latest files in a repo do not prove what is currently installed). If the user has a verified current full BIN, compare its SHA-256; otherwise consider only safe read-only acquisition/diagnostics within equipment capabilities.
2. Analyze actual ROM region `0x6A612`/Delta MAP wrapper/Advanced LC/`0x6AD50..0x6ADC3`, all hook call targets, and map truly unused space **from actual BIN, not from the historic v39 FF gaps**.
3. Preserve actual working code/AVCS/FFS/LC/tuning unchanged except a narrowly designed Delta MAP ON/OFF selector. OFF branch must match **actual base ROM**, not historic v39. The v45 table may already exist and should be reused only after validating descriptors and call points in that base.
4. Run exact ROM preflight (diff, checksums, 245-table XML compatibility) plus test traces and independent ABI/FPSCR concerns, then evaluate a cautious, reversible bench/vehicle plan with recovery capability demonstrated for realistic boot failure cases. A known software rollback alone is not proof of bootloader recovery.

**Hardware:** user currently has only one ECU, installed in the Forester SG9. A spare isn't an absolute prerequisite for continuing research, but changes in executable boot/runtime code with no recovery-tested route carry a different risk from calibration-only changes. Never suggest a LAB binary is ready for on-road flashing solely because EcuFlash reports checksum PASS.

No ECU was accessed or flashed and no new firmware was produced as part of this history review.
