#!/usr/bin/env python3
"""Read-only, SHA-pinned scheduler record audit for A2WC012E v39/v45.

Records start at 0x469C (NOT 0x4700); each is 16 bytes.
No ROM edits, checksum changes or claims of a millisecond interval.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

HASHES = {
    "v39": "43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4",
    "v45": "92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329",
}
BASE, COUNT, STRIDE = 0x469C, 19, 16

def u32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]

def u16(data, offset):
    return struct.unpack_from(">H", data, offset)[0]

def require(value, message):
    if not value:
        raise ValueError(message)

def run(path_v39, path_v45):
    a, b = path_v39.read_bytes(), path_v45.read_bytes()
    for name, data in (("v39", a), ("v45", b)):
        require(len(data) == 524288, name + " is not 512 KiB")
        require(hashlib.sha256(data).hexdigest() == HASHES[name], name + " SHA-256 mismatch")

    unchanged = [
        (0x3410, 0x4100, "scheduler helpers"),
        (0x4644, 0x4828, "scheduler descriptors and metadata"),
        (0x62A0, 0x6620, "callback functions"),
        (0x110B8, 0x11150, "callback chain"),
        (0x15148, 0x151D0, "AF84/AF88 producer"),
    ]
    for begin, end, label in unchanged:
        require(a[begin:end] == b[begin:end], "v39/v45 differ in " + label)

    require(u32(a, 0x4644) == 0xFFFF719C, "table header RAM")
    require(u16(a, 0x4648) == COUNT, "task count")
    require(u16(a, 0x464A) == 0xFFFF, "task count trailer")
    for off in (0x3810, 0x3964, 0x3FD0):
        require(u32(a, off) == BASE, "task table reference at " + hex(off))
    require([u16(a, p) for p in (0x37C8, 0x37CA, 0x37CC, 0x37CE)]
            == [0x4D08, 0x4D08, 0x3D3C, 0x5ED1], "stride / state-pointer instructions")
    require(u32(a, 0x65F4) == 0x110B8, "callback second hop")
    require(u32(a, 0x112F0) == 0x15148, "producer pointer")
    require(u16(a, 0x64E8) == 0x430B, "callback JSR")
    rows = []
    for index in range(COUNT):
        addr = BASE + index * STRIDE
        head, state, callback, flags = struct.unpack_from(">4I", a, addr)
        require(state == 0xFFFF719C + index * 8, "task RAM state: " + str(index))
        require(callback < len(a) and callback % 2 == 0, "callback: " + str(index))
        require(a[addr:addr+16] == b[addr:addr+16], "different record: " + str(index))
        rows.append({
            "index": index,
            "start": f"0x{addr:05X}",
            "header_00": f"0x{head:08X}",
            "state_04": f"0x{state:08X}",
            "callback_08": f"0x{callback:05X}",
            "flags_0C": f"0x{flags:08X}",
        })
    record = rows[6]
    require(record == {
        "index": 6, "start": "0x046FC", "header_00": "0x04000200",
        "state_04": "0xFFFF71CC", "callback_08": "0x064D6",
        "flags_0C": "0x02000000",
    }, "incorrect AF84 record alignment")
    require(u32(a, 0x470C) == 0x04000300, "following descriptor header")
    require(u32(a, 0x47CC) == 0x04FFFFFF, "table terminator")
    return {
        "status": "STRUCTURE_VALIDATED; PERIOD_UNKNOWN",
        "rom_sha256": HASHES,
        "record_start": f"0x{BASE:05X}",
        "record_count": COUNT,
        "record_stride": STRIDE,
        "AF84_record": record,
        "following_record_header_0x470C": "0x04000300",
        "callback_chain": ["0x64D6", "0x110B8", "0x15148"],
        "identical_regions": [{
            "from": f"0x{begin:05X}", "to_exclusive": f"0x{end:05X}",
            "role": label
        } for begin, end, label in unchanged],
        "notes": [
            "0x470C is NOT an AF84 sample-period field",
            "0x04000200 and 0x02000000 do NOT yet have proven physical time units",
            "No timer IRQ/timebase has been verified",
        ],
        "records": rows,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("v39", type=Path)
    parser.add_argument("v45", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = run(args.v39, args.v45)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json:
        args.json.write_text(output, encoding="utf-8")
    print("PASS: exact BIN hashes; 19 x 16-byte records; corrected AF84 index 6.")
    print("AF84 callback: 0x46FC -> 0x64D6 -> 0x110B8 -> 0x15148")
    print("Sampling period: UNKNOWN. Not for flashing.")
