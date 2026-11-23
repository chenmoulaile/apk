#!/usr/bin/env python3
"""Find DEX const-string references and report owning class/method callsites."""
from __future__ import annotations

import argparse
import re
import struct
import zipfile
from collections import defaultdict
from pathlib import Path


def uleb(data: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, pos
        shift += 7
    raise ValueError("truncated ULEB128")


def instruction_width(op: int) -> int:
    if op in (0x03, 0x06, 0x09, 0x14, 0x17, 0x24, 0x25, 0x26,
              0x2A, 0x2B, 0x2C, 0x6E, 0x6F, 0x70, 0x71, 0x72,
              0x74, 0x75, 0x76, 0x77, 0x78, 0xFC, 0xFD):
        return 3
    if op == 0x18:  # const-wide (31i is five code units)
        return 5
    if op in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1A,
              0x1C, 0x1F, 0x20, 0x22, 0x23, 0x29, 0x2D, 0x2E,
              0x2F, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36,
              0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D,
              *range(0x44, 0x6E), *range(0x90, 0xB0),
              *range(0xD0, 0xE3), 0xFE, 0xFF):
        return 2
    if op in (0xFA, 0xFB):
        return 4
    return 1


def read_dex_strings(data: bytes) -> list[str]:
    count, table = struct.unpack_from("<II", data, 56)
    strings: list[str] = []
    for i in range(count):
        off = struct.unpack_from("<I", data, table + 4 * i)[0]
        _, pos = uleb(data, off)  # UTF-16 length; actual string is MUTF-8
        end = data.find(b"\0", pos)
        if end < 0:
            strings.append("")
        else:
            strings.append(data[pos:end].decode("utf-8", errors="replace"))
    return strings


def scan_dex(name: str, data: bytes, pattern: re.Pattern[str]) -> list[tuple[str, str, str]]:
    if len(data) < 112 or data[:4] != b"dex\n":
        return []
    strings = read_dex_strings(data)
    type_count, type_off = struct.unpack_from("<II", data, 64)
    types = [
        strings[struct.unpack_from("<I", data, type_off + 4 * i)[0]]
        for i in range(type_count)
    ]
    method_count, method_off = struct.unpack_from("<II", data, 88)
    methods: list[tuple[str, str]] = []
    for i in range(method_count):
        class_idx, _, name_idx = struct.unpack_from("<HHI", data, method_off + 8 * i)
        methods.append((types[class_idx], strings[name_idx]))

    class_count, class_off = struct.unpack_from("<II", data, 96)
    found: list[tuple[str, str, str]] = []
    for class_number in range(class_count):
        base = class_off + 32 * class_number
        class_idx = struct.unpack_from("<I", data, base)[0]
        class_data = struct.unpack_from("<I", data, base + 24)[0]
        if not class_data:
            continue

        pos = class_data
        static_fields, pos = uleb(data, pos)
        instance_fields, pos = uleb(data, pos)
        direct_methods, pos = uleb(data, pos)
        virtual_methods, pos = uleb(data, pos)
        for _ in range(static_fields + instance_fields):
            _, pos = uleb(data, pos)
            _, pos = uleb(data, pos)

        for method_group_count in (direct_methods, virtual_methods):
            method_idx = 0
            for _ in range(method_group_count):
                delta, pos = uleb(data, pos)
                method_idx += delta
                _, pos = uleb(data, pos)  # access flags
                code_off, pos = uleb(data, pos)
                if not code_off:
                    continue

                insn_count = struct.unpack_from("<I", data, code_off + 12)[0]
                insns = struct.unpack_from(
                    f"<{insn_count}H", data, code_off + 16
                )
                pc = 0
                while pc < insn_count:
                    word = insns[pc]
                    opcode = word & 0xFF

                    # DEX variable-length payload pseudo-instructions.
                    if opcode == 0 and word in (0x0100, 0x0200, 0x0300):
                        if word == 0x0100 and pc + 1 < insn_count:
                            pc += 4 + 2 * insns[pc + 1]
                        elif word == 0x0200 and pc + 1 < insn_count:
                            pc += 2 + 4 * insns[pc + 1]
                        elif word == 0x0300 and pc + 3 < insn_count:
                            element_width = insns[pc + 1]
                            element_count = insns[pc + 2] | (insns[pc + 3] << 16)
                            pc += 4 + (element_width * element_count + 1) // 2
                        else:
                            pc += 1
                        continue

                    string_idx = -1
                    if opcode == 0x1A and pc + 1 < insn_count:
                        string_idx = insns[pc + 1]
                    elif opcode == 0x1B and pc + 2 < insn_count:
                        string_idx = insns[pc + 1] | (insns[pc + 2] << 16)

                    if 0 <= string_idx < len(strings):
                        value = strings[string_idx]
                        if pattern.search(value):
                            owner, method_name = methods[method_idx]
                            found.append((value, owner, method_name))

                    pc += instruction_width(opcode)

    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument(
        "--contains",
        action="append",
        default=[],
        help="case-insensitive string or regex fragment; repeat to add alternatives",
    )
    args = parser.parse_args()
    fragments = args.contains or [
        r"ruiruiyouxi",
        r"/v1/user/",
        r"/v1/auth/",
        r"/leaderboard/",
        r"/simulator/mobile/login",
    ]
    pattern = re.compile("|".join(f"(?:{item})" for item in fragments), re.I)

    with zipfile.ZipFile(args.apk) as archive:
        dex_names = sorted(n for n in archive.namelist() if n.endswith(".dex"))
        if not dex_names:
            parser.error("APK contains no DEX files")
        results = []
        for dex_name in dex_names:
            results.extend(scan_dex(dex_name, archive.read(dex_name), pattern))

    grouped: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for value, owner, method in results:
        grouped[value].add((owner, method))

    for value in sorted(grouped):
        print(value)
        for owner, method in sorted(grouped[value]):
            print(f"  {owner}->{method}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
