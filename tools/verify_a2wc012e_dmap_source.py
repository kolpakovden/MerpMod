#!/usr/bin/env python3
"""Read-only A2WC012E v39/v45 Delta MAP reference validator.

Checks exact 512KiB input SHA-256 and known opcode/PC-relative address
references. It does not emulate ECU, edit BIN or validate a flash image.
"""
import argparse
import hashlib
import struct
from pathlib import Path

HASHES = (
    "43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4",
    "92e0ff671bda35fe7951d68513c2ed188035b950556ffbe3e1e7cb603f241329",
)
PRODUCER = {
    0x15150: 0x9E81, 0x15154: 0xFEE8, 0x151B8: 0xFE2A,
    0x151BC: 0x954F, 0x151C0: 0xF3E8, 0x151C2: 0xF3E1,
    0x151C4: 0xF53A,
}
CONSUMER = {
    0x6ACFC: 0x910B, 0x6AD00: 0xF518, 0x6AD02: 0x9109,
    0x6AD04: 0xD405, 0x6AD06: 0xF418, 0x6AD08: 0x9107,
    0x6AD0A: 0x410B, 0x6AD0E: 0xF0C2,
}
AXIS_HELPER = (
    "70FF 4008 F116 F105 8F0E 2008 8D0F 70FC "
    "F116 F105 8DFA 2008 F011 7004 F216 70FC "
    "F211 F023 000B 4009 4009 000B F08D E000 000B F08D"
)

def u16(data, addr):
    return int.from_bytes(data[addr:addr + 2], "big")

def u32(data, addr):
    return int.from_bytes(data[addr:addr + 4], "big")

def literal16(data, pc):
    op = u16(data, pc)
    assert (op & 0xF000) == 0x9000
    val = u16(data, pc + 4 + (op & 255) * 2)
    return val | 0xFFFF0000 if val & 0x8000 else val

def literal32(data, pc):
    op = u16(data, pc)
    assert (op & 0xF000) == 0xD000
    return u32(data, ((pc + 4) & ~3) + (op & 255) * 4)

def main(v39_path, v45_path):
    base = v39_path.read_bytes()
    ref = v45_path.read_bytes()
    for tag, image, digest in zip(("v39", "v45"), (base, ref), HASHES):
        assert len(image) == 524288, f"{tag}: wrong ROM size"
        assert hashlib.sha256(image).hexdigest() == digest, f"{tag}: SHA-256 mismatch"

    assert all(u16(base, pc) == u16(ref, pc) == op for pc, op in PRODUCER.items())
    assert all(u16(ref, pc) == op for pc, op in CONSUMER.items())
    assert base[0x150F0:0x15280] == ref[0x150F0:0x15280]
    assert base[0x2100:0x2154] == ref[0x2100:0x2154]
    assert base[0x2684:0x26B8] == bytes.fromhex(AXIS_HELPER)
    assert literal16(base, 0x15150) == 0xFFFFAF84
    assert literal16(base, 0x151BC) == 0xFFFFAF88
    assert literal16(ref, 0x6ACFC) == 0xFFFFB218
    assert literal16(ref, 0x6AD02) == 0xFFFFAF88
    assert literal16(ref, 0x6AD08) == 0x2110
    assert literal32(ref, 0x6AD04) == 0x6ACDC
    assert struct.unpack_from(">HH", ref, 0x6ACDC) == (7, 7)
    assert struct.unpack_from(">III", ref, 0x6ACE0) == (0x6AC40, 0x6AC5C, 0x6AC78)
    assert u32(ref, 0x6ACEC) == 0x08000000
    assert u32(base, 0x2148) == 0x2654

    axes_x = struct.unpack_from(">7f", ref, 0x6AC40)
    axes_rpm = struct.unpack_from(">7f", ref, 0x6AC5C)
    assert axes_x == (0., 333., 666., 1000., 1333., 1666., 2000.)
    assert axes_rpm == (500., 800., 1000., 1200., 2000., 3000., 6000.)
    assert set(struct.unpack_from(">49H", ref, 0x6AC78)) == {16384}
    mult = struct.unpack_from(">f", ref, 0x6ACF0)[0]
    print("PASS: v39/v45 exact hashes, producer, consumer, Pull3D dispatch and axes")
    print("pDeltaMap@0xFFFFAF88 = updated AF84 - prior AF84 (physical units unverified)")
    print(f"Delta MAP neutral effective multiplier = {16384 * mult:.12f}")
    print("UNVERIFIED: raw units, update cadence, complete ABI, ECU execution, checksum")
    print("NOT FOR FLASH")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("v39", type=Path)
    p.add_argument("v45", type=Path)
    args = p.parse_args()
    main(args.v39, args.v45)
