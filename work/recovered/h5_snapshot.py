#!/usr/bin/env python3
"""Download the reachable Laya H5 client, its referenced resources and atlas images."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path, PurePosixPath
from typing import Iterable

DEFAULT_BASE = "https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/"
CORE_FILES = [
    "index.html",
    "code.js",
    "code2.js",
    "libQuickSDKH5_To_Client.js",
    "libSDK.js",
    "libSDK_To_Client.js",
    "zip.txt",
    "atlas/loading.atlas",
    "atlas/loading/bg3.jpg",
    # Runtime fallback groups requested by loadCommonResAndConfigZip().
    "atlas/common.atlas",
    "atlas/common2.atlas",
    "atlas/commonAni.atlas",
]
EXT_RE = re.compile(
    r"(?<![A-Za-z0-9_])((?:atlas|res|json|font|sound|scene)/"
    r"[A-Za-z0-9_./-]+\.(?:atlas|json|png|jpg|jpeg|webp|mp3|wav|ttf|fnt|sk|zip))",
    re.IGNORECASE,
)


def path_candidates(text: str) -> set[str]:
    found: set[str] = set()
    for match in EXT_RE.findall(text):
        for item in match.split(","):
            item = item.strip().lstrip("/")
            if not item or ".." in PurePosixPath(item).parts:
                continue
            found.add(item)
    return found


def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GamePreservationBot/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
        headers = {k.lower(): v for k, v in response.headers.items()}
        return data, headers


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_dest(root: Path, relative: str) -> Path:
    relative_path = PurePosixPath(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"unsafe resource path: {relative}")
    destination = root.joinpath(*relative_path.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def decode_config(data: bytes) -> bytes | None:
    for window_bits in (zlib.MAX_WBITS, -zlib.MAX_WBITS, zlib.MAX_WBITS | 16):
        try:
            return zlib.decompress(data, window_bits)
        except zlib.error:
            pass
    return None


def atlas_images(path: Path, relative: str) -> set[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    meta = payload.get("meta") or {}
    images = meta.get("image")
    if not isinstance(images, str):
        return set()
    result: set[str] = set()
    parent = PurePosixPath(relative).parent
    for image in images.split(","):
        image = image.strip()
        if not image:
            continue
        if image.startswith(("atlas/", "res/", "scene/")):
            candidate = image
        else:
            candidate = str(parent / image)
        if ".." not in PurePosixPath(candidate).parts:
            result.add(candidate)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=Path("work/recovered/h5/client"))
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--max-total-mib", type=int, default=700)
    args = parser.parse_args()

    base = args.base_url.rstrip("/") + "/"
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "base_url": base,
        "downloaded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": {},
        "missing": [],
        "errors": [],
    }
    files: dict[str, dict[str, object]] = manifest["files"]  # type: ignore[assignment]
    total_bytes = 0
    total_limit = args.max_total_mib * 1024 * 1024

    def download_one(relative: str) -> tuple[str, bytes | None, dict[str, str], str | None]:
        url = base + relative
        try:
            data, headers = fetch_bytes(url)
            if len(data) > 100 * 1024 * 1024:
                return relative, None, headers, "single file exceeds 100 MiB safety cap"
            content_type = headers.get("content-type", "").lower()
            if "text/html" in content_type and PurePosixPath(relative).suffix.lower() not in {".html", ".htm"}:
                return relative, None, headers, "unexpected HTML response for asset"
            return relative, data, headers, None
        except urllib.error.HTTPError as exc:
            return relative, None, {}, f"HTTP {exc.code}"
        except Exception as exc:  # network errors are recorded and the rest continues
            return relative, None, {}, f"{type(exc).__name__}: {exc}"

    queue = set(CORE_FILES)

    def fetch_batch(items: Iterable[str]) -> list[str]:
        nonlocal total_bytes
        newly_downloaded: list[str] = []
        items = sorted(set(items))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {executor.submit(download_one, item): item for item in items}
            for future in concurrent.futures.as_completed(futures):
                relative, data, headers, error = future.result()
                if data is None:
                    if relative not in manifest["missing"]:  # type: ignore[operator]
                        manifest["missing"].append(relative)  # type: ignore[union-attr]
                    manifest["errors"].append({"path": relative, "error": error})  # type: ignore[union-attr]
                    continue
                if total_bytes + len(data) > total_limit:
                    manifest["errors"].append({
                        "path": relative,
                        "error": f"total resource limit {args.max_total_mib} MiB reached",
                    })  # type: ignore[union-attr]
                    continue
                dest = safe_dest(output, relative)
                dest.write_bytes(data)
                total_bytes += len(data)
                files[relative] = {
                    "bytes": len(data),
                    "sha256": sha256(data),
                    "content_type": headers.get("content-type", ""),
                    "last_modified": headers.get("last-modified", ""),
                    "url": base + relative,
                }
                newly_downloaded.append(relative)
        return newly_downloaded

    first = fetch_batch(queue)
    code_path = output / "code.js"
    if not code_path.is_file():
        (output.parent / "snapshot-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("ERROR: code.js could not be downloaded")
        return 2

    code = code_path.read_text(encoding="utf-8", errors="replace")
    queue = path_candidates(code)
    config_path = output / "zip.txt"
    if config_path.is_file():
        decoded = decode_config(config_path.read_bytes())
        if decoded is not None:
            config_output = output.parent / "zip.decompressed.json"
            config_output.write_bytes(decoded)
            text_config = decoded.decode("utf-8", errors="replace")
            queue.update(path_candidates(text_config))
            try:
                parsed = json.loads(text_config)
                def walk(value: object) -> None:
                    if isinstance(value, str):
                        queue.update(path_candidates(value))
                    elif isinstance(value, list):
                        for child in value:
                            walk(child)
                    elif isinstance(value, dict):
                        for key, child in value.items():
                            queue.update(path_candidates(key))
                            walk(child)
                walk(parsed)
            except json.JSONDecodeError as exc:
                manifest["errors"].append({"path": "zip.txt", "error": f"decompressed but JSON parse failed: {exc}"})  # type: ignore[union-attr]
            manifest["config_decompressed"] = {
                "path": str(config_output),
                "bytes": len(decoded),
                "sha256": sha256(decoded),
            }
        else:
            manifest["errors"].append({"path": "zip.txt", "error": "could not decompress with zlib variants"})  # type: ignore[union-attr]

    # Download all literal assets and any additional paths referenced by config.
    downloaded = fetch_batch(queue)
    atlas_candidates = sorted(
        item for item in downloaded if item.lower().endswith(".atlas")
    )
    atlas_refs: set[str] = set()
    for relative in atlas_candidates:
        atlas_refs.update(atlas_images(output / relative, relative))
    if atlas_refs:
        fetch_batch(atlas_refs)

    # Include selected additional runtime files if the minified code references them.
    text_refs = set()
    for match in re.findall(r'["\']([^"\']+\.(?:js|json|zip|txt))["\']', code, re.I):
        if (
            match.startswith(("atlas/", "res/", "json/", "font/", "sound/", "scene/"))
            and ".." not in PurePosixPath(match).parts
        ):
            text_refs.add(match)
    if text_refs:
        fetch_batch(text_refs)

    manifest["downloaded_file_count"] = len(files)
    manifest["downloaded_bytes"] = total_bytes
    manifest["downloaded_mib"] = round(total_bytes / (1024 * 1024), 2)
    manifest["static_asset_candidates"] = len(queue)
    manifest["atlas_referenced_images"] = len(atlas_refs)
    manifest_path = output.parent / "snapshot-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "downloaded_file_count": manifest["downloaded_file_count"],
        "downloaded_mib": manifest["downloaded_mib"],
        "static_asset_candidates": manifest["static_asset_candidates"],
        "atlas_referenced_images": manifest["atlas_referenced_images"],
        "missing_count": len(manifest["missing"]),  # type: ignore[arg-type]
        "manifest": str(manifest_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
