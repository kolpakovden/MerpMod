# Current Forester clean v39 → Delta MAP LAB v3: checksum-valid preflight artifacts

> **PRECHECK ONLY — NOT HARDWARE-VALIDATED / NOT APPROVED FOR FLASHING.**
> The user has a single SH7055 ECU installed in their SG9. This is a status and reproducibility report, not an authorization to write to the car.

## Baseline

On 2026-10-21 user clarified that historic v86 was an abandoned overcomplicated branch; the car returned to clean v0→v25→v39. They uploaded `Forester_SG9_MAP_clean_v39(3).bin`. Full 524288-byte SHA-256 **`43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`**, identical to the v39 input used to construct LAB v3. **No direct readback of actual ECU flash has yet been supplied**; file identity alone does not independently prove current installed bytes.

LAB v3 uncorrected SHA-256 `def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f`. It was rebuilt byte-for-byte from this precise v39 and original v45. The verified ROM hole in clean v39 avoids the address conflict with Advanced LC present in older historical late-series v68+, which are **not currently installed per user**.

## Checksummed output images

| State | Filename | Header flag @ 0x6AD48 | Checksum @ 0x7FB88 | SHA-256 |
| --- | --- | --- | --- | --- |
| OFF default | `Forester_SG9_v39_DMAP_v3_OFF_CHECKSUM_PRECHECK.bin` | 0 | `0x98A46BAF` | `fc4945f1566bfd863b42bb214e9fc1809c4416e7cece3b0d444a46bb1451d0b9` |
| ON optional | `Forester_SG9_v39_DMAP_v3_ON_CHECKSUM_PRECHECK.bin` | 1 | `0x97A46BAF` | `c885809462d19aae8c019c7338be512828fde8524b5ab07fab6933fa08a2e5cb` |
| untouched rollback | `Forester_SG9_v39_VERIFIED_ORIGINAL_ROLLBACK.bin` | no Delta MAP selector | `0x9B084277` | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |

Both candidates are 524288 bytes. Both differ from v39 at **312** byte positions (308 code/table/flag byte changes + 4 checksum). They change nothing outside `0x6A612..0x6A615`, `0x6AC40..0x6AD83`, `0x7FB88..0x7FB8B`. Existing LC/FFS, fueling, VE, SD mode, calibration values and original ROM ID are byte-identical. Correct checksum balance: `BE32_SUM(0x2000..0x7FAF7) + BE32[0x7FB88] == 0x5AA5A55A (mod 2^32)`.

The ON SHA-256 **exactly matches** the actual earlier saved-by-EcuFlash ON file reported with a Windows `PASS`. OFF is verified independently against the same checksum formula; there is no new OFF hardware/plugin flash operation.

## Actual executed offline verification

- exact v39/experimental v45 hash pin and byte-for-byte LAB v3 rebuild;
- ROM code cave, branch targets, literals, metadata and 245 EcuFlash entries;
- OEM `Pull3D` 10-case interpolation, 64 hook traces, additional 1080 MAF/SD/Blend traces rerun: **PASS under a narrow, non-independent opcode simulator**;
- strict checksum and diff verifier tested with deliberately damaged enable-byte, checksum word and unrelated ECU code region; all three were rejected;
- complete output SHA-256 for OFF and ON and file contents verified; ZIP file integrity check passed.

## Remaining genuine NO-GO conditions

1. No independently verified **readback** from the ECU, just a user-reported installed BIN identical to supplied v39.
2. No independent actual SH7055/FPU/FPSCR execution and real-time interrupt/timing safety tests of the patched code.
3. No **demonstrated recovery route** for a no-boot/no-communications outcome on the only ECU. An earlier successful recovery from a misbehaving calibration is not such proof.
4. No engine/bench data validating Delta MAP X-axis `0–2000`, negative transients, LC/FFS and fail-safe behavior.

**Therefore this is a checksum-valid, file-level preflight artifact and not yet a safe-to-flash release.** In EcuFlash, ON/OFF is a ROM file calibration flag; it is not a live in-car switch and takes a flash write to change.

The complete offline ZIP (two BINs, rollback, XML, hashes, Python verifier and Russian README) was delivered through the conversation, **not committed to GitHub**.

For specialist recovery context, Tactrix documents SH705x-family Subaru boot-mode repair involving disassembly/special FTDI/watchdog hardware, not a guaranteed one-click recovery for any specific car: https://www.tactrix.com/index.php?Itemid=41&catid=42%3Aecu-repair&id=66%3Areflashing-subaru-sh705x-ecus-using-the-renesas-boot-mode&option=com_content&view=article .
