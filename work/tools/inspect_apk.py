#!/usr/bin/env python3
"""Inspect an APK's ZIP structure, manifest metadata and likely game payloads.

This script uses only Python's standard library. It deliberately does not
pretend to decode Android's binary XML manifest or disassemble DEX bytecode.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import PurePosixPath


def read_uleb128(data: bytes, offset: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
        if shift > 35:
            raise ValueError("invalid ULEB128")


def dex_strings(data: bytes) -> list[str]:
    if len(data) < 112 or data[:4] != b"dex\n":
        return []
    count, table = struct.unpack_from("<II", data, 56)
    result: list[str] = []
    for i in range(count):
        string_offset = struct.unpack_from("<I", data, table + i * 4)[0]
        _, pos = read_uleb128(data, string_offset)
        end = data.find(b"\0", pos)
        if end < 0:
            continue
        result.append(data[pos:end].decode("utf-8", errors="replace"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", help="path to the input APK")
    args = parser.parse_args()

    digest = hashlib.sha256()
    with open(args.apk, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    print(f"APK: {args.apk}")
    print(f"SHA-256: {digest.hexdigest()}")

    try:
        archive = zipfile.ZipFile(args.apk)
    except (OSError, zipfile.BadZipFile) as exc:
        parser.error(f"not a readable APK/ZIP: {exc}")

    with archive:
        names = archive.namelist()
        print(f"ZIP entries: {len(names)}")
        for name in names:
            if name.endswith(".dex"):
                print(f"DEX: {name} ({archive.getinfo(name).file_size:,} bytes)")

        html = [n for n in names if PurePosixPath(n).suffix.lower() in {".html", ".htm"}]
        js = [n for n in names if PurePosixPath(n).suffix.lower() == ".js"]
        assets = [n for n in names if n.startswith("assets/")]
        print(f"HTML files: {len(html)}")
        for name in html[:30]:
            print(f"  {name}")
        print(f"JS files: {len(js)}")
        for name in js[:40]:
            print(f"  {name}")
        print(f"Assets: {len(assets)}")

        candidates = (
            "AndroidManifest.xml",
            "assets/quickgame_sdk/qg_ipconfig.txt",
            "assets/libQuickSDKH5_To_Client.js",
        )
        for name in candidates:
            if name in names:
                raw = archive.read(name)
                print(f"\n--- {name} ({len(raw)} bytes) ---")
                if name.endswith(".txt"):
                    print(raw.decode("utf-8", errors="replace").strip())

        terms = re.compile(
            r"ruiruiyouxi|cjjlq|loginNotify|uploadGameRoleInfo|leaderboard|"
            r"taptapReleaseRes|gateway",
            re.IGNORECASE,
        )
        for dex_name in (n for n in names if n.endswith(".dex")):
            strings = dex_strings(archive.read(dex_name))
            hits = sorted({s for s in strings if terms.search(s) and len(s) < 300})
            if hits:
                print(f"\n--- matching strings in {dex_name} ---")
                for value in hits[:100]:
                    print(value)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
