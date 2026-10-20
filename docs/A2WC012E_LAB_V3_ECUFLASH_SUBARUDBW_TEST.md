# A2WC0MME LAB v3 — cross-checking real EcuFlash subarudbw output (NO ECU FLASH)

> **Checker v4 PowerShell hotfix (2026-10-21):** The v3 script used signed hexadecimal integer literals `0x97A46BAF` / `0x98A46BAF` in a `[uint64]$expectedWord` assignment. Windows PowerShell treated `0x97A46BAF` as the negative `Int32` value `-1750832209` and raised a conversion error **after** successfully printing matching checksum values and exact five changed offsets. Fixed by explicit unsigned parsing: `[Convert]::ToUInt64('97A46BAF', 16)` and similarly for OFF. Reproducible Python checker passes both known OFF and ON expected complete-file hashes; native PowerShell v4 execution awaits user testing. **The earlier saved ON ROM SHA-256 already matched independently predicted output; no further EcuFlash save or ECU connection is required.**


> **STATUS:** The offline checksum scheme has been proven on user-supplied v39 and v45 and predicted for LAB v3. **The actual proprietary EcuFlash `subarudbw` module has NOT yet been run against LAB v3.** No LAB image has been approved for ECU flashing.

## Actual file-only EcuFlash test result — 2026-10-21

The user opened LAB v3 in EcuFlash 1.44.4347 with 245 A2WC0MME tables and saved a modified ROM. The external read-only checker reported:

```text
Source SHA256: def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f
Saved  SHA256: c885809462d19aae8c019c7338be512828fde8524b5ab07fab6933fa08a2e5cb
Changed bytes: 5
Changed offsets: 0x6AD48, 0x7FB88, 0x7FB89, 0x7FB8A, 0x7FB8B
Checksum stored:   0x97A46BAF
Checksum expected: 0x97A46BAF
```

The initial checker printed `MISMATCH` because it **incorrectly expected only a checksum correction**, assuming Delta MAP flag OFF. The original LAB flag at `0x6AD48` is 0; the saved image corresponds **exactly** to changing it to ON=1 and balancing the checksum. The byte at `0x6AD48` is the first byte of a big-endian 32-bit summand, so its +1 increases the sum by `0x01000000` and decreases the checksum from expected OFF `0x98A46BAF` to expected ON `0x97A46BAF`. The **complete saved SHA-256 matches the independently constructed ON image exactly**; no other ROM edits are present.

A **revised v3 validator** accepts the two strict expected complete-image hashes:
- OFF=0 → checksum `0x98A46BAF` → SHA-256 `fc4945f1566bfd863b42bb214e9fc1809c4416e7cece3b0d444a46bb1451d0b9`
- ON=1 → checksum `0x97A46BAF` → SHA-256 `c885809462d19aae8c019c7338be512828fde8524b5ab07fab6933fa08a2e5cb`

The revised *Python* checker was tested against six modeled cases, but the *PowerShell* script still requires a fresh Windows test. **Conclusion:** user EcuFlash saved output validates against the independently calculated checksum for **ON**. This does **not** demonstrate that the code can safely execute on the ECU, nor that a real SH7055 or engine has been tested. **Still NOT FOR FLASH.**

## Test data

- LAB v3 original SHA-256: `def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f` (524288 bytes)
- ROM ID `A2WC0MME`, checksum module `subarudbw` in EcuFlash 1.44 XML.
- Denso range: `[0x2000,0x7FAF7]`; checksum word at `0x7FB88`.
- LAB v3 stored word: `0x9B084277` (stale).
- Independently predicted corrected word: **`0x98A46BAF`**.
- If the EcuFlash switch is OFF, the expected SHA-256 is `fc4945f1566bfd863b42bb214e9fc1809c4416e7cece3b0d444a46bb1451d0b9`; if ON it is `c885809462d19aae8c019c7338be512828fde8524b5ab07fab6933fa08a2e5cb`.
- The predicted four changed byte offsets are `0x7FB88–0x7FB8B`; no patched-to-flash BIN has been distributed as part of this test.

## On the user's Windows PC — file-only validation, no cable

1. Disconnect **ECU / OpenPort**. Extract the checksum cross-check ZIP to a new folder.
2. Open `LAB_v3_CHECKSUM_TEST_DO_NOT_FLASH.bin` with EcuFlash 1.44.
3. Verify the correct `A2WC0MME` metadata and 245-table definition.
4. If EcuFlash offers to correct the *opened ROM's checksum*, accept; if there is no prompt, do not treat absence alone as proof of a fault.
5. Use **File → Save ROM As** and save to a distinct name `ECUFLASH_AFTER_SAVE.bin`, leaving the input untouched. **Never select Write ECU or Test Write ECU.**
6. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\check_ecuflash.ps1 -SavedRom .\ECUFLASH_AFTER_SAVE.bin` in the extracted folder, or run the bundled Python equivalent.
7. Return the checker output and EcuFlash log; ideally the saved ROM for independent byte-by-byte review.

The cross-check returns one of three outcomes:
- **PASS:** only four expected bytes changed, checksum and full SHA-256 agree with the independent model. This confirms module output behavior, **not ECU safety**.
- **INCONCLUSIVE:** no correction was observed in saved image.
- **MISMATCH:** EcuFlash saved unexpected changes. Stop and investigate; do not use this image.

The checker was locally tested with an in-memory-only predicted change (PASS), unchanged input (INCONCLUSIVE), and an extra mutated-code byte (MISMATCH). **No real EcuFlash run was claimed.**

## Hardware bench stage — NOT authorized by file checksum check

A separate, explicitly reviewed bench process must establish the ECU model and wiring, fused current-limited supply, known-good v39 and **demonstrated recovery procedure**. Hardware tests must cover boot/diagnostics, FPU/FPSCR, interrupts, SD/MAF/Blend, transient inputs, NaN/invalid sensor signals, startup/watchdog, LC/FFS and engine protections. Do not run LAB v3 on an engine or in the vehicle before passing those gates.

Related: [offline checksum findings](A2WC012E_DMAP_V3_CHECKSUM_AUDIT.md); [v3 ABI review](A2WC012E_DMAP_LAB_V3_REGRESSION_ABI.md).
