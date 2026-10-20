# A2WC012E — scheduler record boundaries and AF84 callback (v39/v45)

**Status: BYTE-VERIFIED STRUCTURE; ABSOLUTE UPDATE PERIOD STILL UNKNOWN.**

Validated against the exact 524,288-byte images:

- Forester v39 SHA-256: `43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4`
- Experimental v45 SHA-256: `92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329`

No BIN modification or ECU execution testing was performed.

## Critical correction to the previous study

The earlier analysis described `0x4700..0x470F` as a single descriptor, assigning `0x04000300` to its final field. **This was incorrect.** The actual descriptor array starts at **`0x469C`** and has a stride of **16 bytes**. The correct record for callback `0x64D6` starts at **`0x46FC`**.

| Record-relative | Exact address | Value | Grounded meaning |
| --- | --- | --- | --- |
| `+0x00` | `0x46FC` | `0x04000200` | Descriptor header; detailed flags/period unknown |
| `+0x04` | `0x4700` | `0xFFFF71CC` | Per-task RAM state pointer |
| `+0x08` | `0x4704` | `0x000064D6` | Task callback address |
| `+0x0C` | `0x4708` | `0x02000000` | Additional descriptor data; meaning unresolved |
| next `+0x00` | `0x470C` | `0x04000300` | **Header of the following task**, not this one's interval |

At `0x4648`, a `0x0013` count gives **19 records**; callback `0x64D6` is index 6 (7th record). The next marker at `0x47CC` is `0x04FFFFFF`.

## Corroboration from dispatch code

- `0x37C0` loads a literal at `0x3810 = 0x469C`.
- `0x37C8` and `0x37CA` are two `SHLL2 R13` instructions, multiplying record index by **16**.
- `0x37CC` adds descriptor base `0x469C`.
- `0x37CE` uses `MOV.L @(4,R13),R14`, retrieving the **RAM state pointer** from `+0x04`. This matches the corrected record alignment.
- `0x3F20` also walks the table using the count from `0x4648`; other literal references to the same table base exist at `0x3964` and `0x3FD0`.

The callback chain remains:

```text
task record @0x46FC (index 6)
    +0x08 = 0x64D6
    0x64D6 -> 0x110B8 (literal @0x65F4)
    0x110B8 -> 0x15148 (literal @0x112F0)
    0x15148 -> AF84/AF88 producer (Delta MAP)
```

## All records at a glance

`0x04000100` occurs in **9** headers; `0x04000200` in **4**; `0x04000300` in **2**; `0x04000400` in **3**; `0x04000000` in **1**. The last field is `0x02000000` for **17** records and `0x01000000` for **2** records.

This variation suggests that the header includes a category/dispatch selector, **but its numerical values cannot yet be translated into ms**. Treat these labels as values, not measured timing.

### How the third header byte is used

In dispatcher helper `0x3F70`, code `0x3FA2`/`0x3FA4` shifts a task index to a 16-byte offset and `0x3FA6` adds base `0x469C`. It then reads the descriptor header's **byte at offset +2** using `84D2` at `0x3FB0` (`MOV.B @(2,R13),R0`), copies it to `R6` at `0x3FB2`, and calls the helper at `0x3A1A` through `JSR @R10` at `0x3FB4`. For our task, this byte equals `2`.

This is **actual evidence that the byte is consumed as an input to dispatch logic**. It is **not evidence that its value 2 means 2 ms**, 2 ticks or a particular priority. The helper and its timer origin must still be fully resolved.

## Shared sections between v39 and v45

The following ranges are byte-identical:

- `0x3410–0x40FF`: dispatcher/helper section
- `0x4644–0x4827`: descriptor table and adjacent records
- `0x62A0–0x661F`: callbacks and pointers
- `0x110B8–0x1114F`: callback chain
- `0x15148–0x151CF`: AF84/AF88 producer

Thus the v45 Delta MAP experiment did not change these scheduler bytes relative to v39.

## Remaining proof to determine the *actual* sample period

1. Trace the code that sets task-ready flags and invokes the descriptor walker. This may lead to interrupts and hardware timer registers, but no timer source or clock divisor is established yet.
2. Decode the meaning of the record's first and last fields by their **actual offsets** (`+0` and `+12`).
3. Obtain time-correlated **read-only** logs or a bench trace of AF84/AF88 production; note that sparse OBD polling is not proof of the update period.
4. Only after determining the input delta time should we reassess whether the Delta MAP axis `0..2000` has adequate resolution.

**Do not claim 10, 15, 20 ms, or any other update period from `0x04000200` alone.** Do not flash LAB v1/v2.

The standalone, exact-SHA Python validator `tools/verify_a2wc012e_scheduler.py` lists all 19 records and enforces corrected field boundaries.
