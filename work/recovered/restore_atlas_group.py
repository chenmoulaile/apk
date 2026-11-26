#!/usr/bin/env python3
"""Restore a runtime-loaded Laya atlas group that the offline asset scan can miss."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import urllib.request
from pathlib import Path, PurePosixPath

DEFAULT_BASE_URL = "https://cjjlqres.ruiruiyouxi.com/taptapReleaseRes/"


def safe_relative(path: str) -> PurePosixPath:
    rel = PurePosixPath(path.lstrip("/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe resource path: {path}")
    return rel


def download(base_url: str, root: Path, relative: str) -> dict[str, object]:
    rel = safe_relative(relative)
    destination = root.joinpath(*rel.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        data = destination.read_bytes()
        source = "snapshot"
        content_type = mimetypes.guess_type(str(destination))[0] or "application/octet-stream"
    else:
        url = base_url.rstrip("/") + "/" + str(rel)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GamePreservationBot/1.0)"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "application/octet-stream")
        if not data:
            raise RuntimeError(f"empty resource: {url}")
        if "text/html" in content_type.lower():
            raise RuntimeError(f"unexpected HTML for resource: {url}")
        destination.write_bytes(data)
        source = url
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "content_type": content_type,
        "source": source,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="H5 client root")
    parser.add_argument("--group", default="LifeTree", help="Laya atlas group name")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    root = args.root
    group = args.group
    atlas_rel = f"atlas/{group}.atlas"
    atlas_path = root / atlas_rel
    manifest_path = root.parent / "snapshot-manifest.json"
    manifest = {"files": {}}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.setdefault("files", {})

    restored: dict[str, dict[str, object]] = {}
    restored[atlas_rel] = download(args.base_url, root, atlas_rel)
    try:
        atlas = json.loads(atlas_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid {atlas_rel}: {exc}") from exc

    meta = atlas.get("meta") or {}
    page_names = meta.get("image") or meta.get("images")
    if isinstance(page_names, list):
        page_values = page_names
    elif isinstance(page_names, str):
        page_values = [part.strip() for part in page_names.split(",") if part.strip()]
    else:
        raise SystemExit(f"{atlas_rel} has no meta.image page declaration")

    for page_name in page_values:
        if not isinstance(page_name, str) or not page_name.strip():
            continue
        if page_name.startswith(("atlas/", "res/")):
            page_rel = page_name
        else:
            page_rel = str(PurePosixPath(atlas_rel).parent / page_name)
        restored[page_rel] = download(args.base_url, root, page_rel)

    # The main Life Tree panel uses this separately declared background image.
    loose_bg = f"{group}/bg1.png"
    restored[loose_bg] = download(args.base_url, root, loose_bg)

    for path, record in restored.items():
        records[path] = record
    manifest["downloaded_file_count"] = len(records)
    manifest["downloaded_bytes"] = sum(int(item.get("bytes", 0)) for item in records.values())
    manifest["downloaded_mib"] = round(manifest["downloaded_bytes"] / (1024 * 1024), 2)
    if manifest_path.is_file():
        missing = manifest.get("missing", [])
        manifest["missing"] = [item for item in missing if item not in restored]
        errors = manifest.get("errors", [])
        manifest["errors"] = [item for item in errors if item.get("path") not in restored]
        manifest["derived_assets"] = sorted(set(manifest.get("derived_assets", [])))
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    page_list = ",".join(restored.keys())
    print(f"RESTORE_ATLAS_GROUP=PASS group={group} files={len(restored)} paths={page_list}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
