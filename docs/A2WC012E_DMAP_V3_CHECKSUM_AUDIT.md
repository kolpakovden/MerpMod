# A2WC0MME v39/v45/LAB v3 — Subaru/Denso checksum audit (read-only)

> **LAB v3 HAS A STALE CHECKSUM. DO NOT FLASH.** This investigation inspected the three exact original images locally, without modifying or creating a corrected BIN. Proprietary EcuFlash `subarudbw` was **not run**.

## Input identities and target metadata

| Image | Size | SHA-256 |
| --- | ---: | --- |
| user clean v39 | 524288 | `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4` |
| user reference v45 | 524288 | `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329` |
| previously created LAB v3 | 524288 | `def65da29d7a6c6387c186d7d8aeaf3cd36baa4a34d289807778cd9da47d538f` |

ROM ID `A2WC0MME`, SH7055, EcuFlash `sti04` and `subarudbw` come from the actual user-supplied ROM metadata. The original MerpMod target map labels `Checksum_Fix` at `0x7FB80`, matching the bytes found.

## Exact descriptor structure

- Descriptor table begins at **`0x7FB80`**, 17 records × 12 bytes through `0x7FC4B`.
- The **single active** descriptor at `0x7FB80` contains start `0x00002000`, **inclusive end** `0x0007FAF7`, and a 32-bit balancing checksum stored at **`0x7FB88`**.
- Remaining **16 neutral** descriptors contain `[0,0,0x5AA5A55A]`. Bytes from `0x7FC4C` belong to the subsequent ROM structure, not another checksum record.
- Coverage: **514808 bytes** (= 128702 big-endian 32-bit words) from `0x2000` to `0x7FAF7` inclusive.

The calculation that independently passes both existing v39 and v45 is:

```python
sum32 = sum(BE32_words(rom[0x2000:0x7FAF8])) & 0xffffffff
expected = (0x5AA5A55A - sum32) & 0xffffffff
valid = int.from_bytes(rom[0x7FB88:0x7FB8C], 'big') == expected
```

The 12-byte descriptor and `0x5AA5A55A` sum agree with the documented Subaru/Denso checksum family: https://docs.openremap.com/checksum/cli . This validates the **identified scheme on these specific images**, not the entire behavior of proprietary EcuFlash plugin or ECU ROM verification.

## Read-only results

| ROM | Sum over coverage | Stored checksum @0x7FB88 | Expected checksum | Result |
| --- | --- | --- | --- | --- |
| v39 | `BF9D62E3` | `9B084277` | `9B084277` | **OK** |
| v45 | `23253EC4` | `37806696` | `37806696` | **OK** |
| LAB v3 | `C20139AB` | `9B084277` | `98A46BAF` | **STALE** |

`SUM(v3) + STORED(v39) = 0x5D097C22`, which is not `0x5AA5A55A`. Hypothetically replacing bytes at `0x7FB88..0x7FB8B` from `9B 08 42 77` to `98 A4 6B AF` yields the expected balance **in an in-memory Python test only**; no corrected BIN was saved. Four of the original bytes would change. This is **not** evidence of safe executable code.

The unchanged LAB v3 differs from v39 at exactly **308 bytes**, contained strictly inside `[0x6A612,0x6A616)` and `[0x6AC40,0x6AD84)`. All other original data, including LC/FFS and both OEM IAM-selected OL fuel tables, remains byte-identical.

## Reproducible verifier

`tools/verify_a2wc012e_v3_checksum.py` accepts original v39, original v45 and the exact v3 LAB image; it requires exact SHA-256, checks the complete descriptor table and code diff, reports expected/stored words, and does **not** write ROM files. It performs a checksum correction **only in temporary Python RAM** as a unit test.

Negative tests: mutated code byte `0x6A612` and mutated stored word `0x7FB88` are detected as STALE; damaged checksum-range descriptor rejected. An independent user-visible ZIP with a Python script, Russian README and full JSON audit has been prepared.

## Remaining work

- Have EcuFlash validate/checksum **a disposable copy**, without opening any flashing operation, and compare with this result.
- Full independent CPU/FPU/FPSCR and timer/interrupt validation; controlled ECU bench, LC/FFS and engine-protection regressions.
- Back-up original known-good v39 and **verify actual recovery capability** before any ECU writing.
- Keep LAB v1/v2/v3 marked **NOT FOR FLASH**, even if a checksum word becomes correct.
