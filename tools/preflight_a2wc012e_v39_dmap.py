#!/usr/bin/env python3
"""Read-only preflight for the exact 512-KiB Forester SG9 clean v39 ROM.

No binary modification, checksum patching, or ECU flashing is performed.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

EXPECTED_SHA = "43a4751d68da4ddca9d483c1723a78f04c85ad982423f48177402f9962245ad4"
PATCH_SIGNATURE = b"A2WC012E.MeRpMoD.Gratis.Testing.v13.5.6.212"

def preflight(path):
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    def at(offset, size):
        return data[offset:offset + size]
    checks = {
        "exact_v39_sha256": len(data) == 524288 and sha == EXPECTED_SHA,
        "rom_size_512kib": len(data) == 524288,
        "rom_id_A2WC0MME": at(0x2000, 8) == b"A2WC0MME",
        "legacy_merpmod_signature": at(0x69C10, len(PATCH_SIGNATURE)) == PATCH_SIGNATURE,
        "original_maf_hook_pointer": at(0x77B4, 4) == bytes.fromhex("0006A558"),
        "original_dmap_intercept_bytes": at(0x6A612, 4) == bytes.fromhex("F13C711C"),
        "dmap_candidate_block_all_ff": at(0x6AC40, 0x104) == b"\xff" * 0x104,
        "speed_density_mode_2": at(0x69DD4, 1) == b"\x02",
        "two_stock_ol_maps_identical": at(0x59F4C, 288) == at(0x5A108, 288),
    }
    failures = [key for key, value in checks.items() if not value]
    valid_length = len(data) == 524288
    result = {
        "input": path.name,
        "size_bytes": len(data),
        "sha256": sha,
        "checks": checks,
        "failed_checks": failures,
        "addresses": {
            "maf_hook_pointer": "0x077B4",
            "maf_hook_target": hex(int.from_bytes(at(0x77B4,4), "big")) if valid_length else None,
            "candidate_dmap_block": ["0x6AC40", "0x6AD43"],
            "candidate_dmap_block_bytes": 260,
            "candidate_dmap_hook": "0x6A612",
            "hook_original_bytes": at(0x6A612,4).hex().upper() if valid_length else None,
            "v45_documented_hook_bytes": "A3850009",
            "mode": "0x69DD4",
            "primary_open_loop": "0x59F4C",
            "failsafe_open_loop": "0x5A108",
            "fuel_map_iam_threshold": "0x58CD0",
        },
        "mode": data[0x69DD4] if valid_length else None,
        "iam_threshold": struct.unpack(">f", at(0x58CD0, 4))[0] if valid_length else None,
        "status": "PREFLIGHT_INPUT_MATCHES" if not failures else "REJECT_INPUT",
        "patch_status": "NOT_BUILT",
        "must_verify_before_patch": [
            "pDeltaMap RAM 0xFFFFAF88 units, updates, lifetime",
            "SH7055 hook ABI and displaced instructions",
            "real compiled size/linker map and ROM overlap",
            "output calibration and tuning byte preservation",
            "EcuFlash definition address from actual output",
            "checksum, bench tests and LC/FFS regression"
        ]
    }
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = preflight(args.rom)
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    print(output)
    if args.report:
        args.report.write_text(output, encoding="utf-8")
    raise SystemExit(0 if not report["failed_checks"] else 2)
