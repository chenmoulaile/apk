#!/usr/bin/env python3
"""Restore loose offline UI images from frames already present in packed Laya atlases."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: derive_atlas_assets.py <game-client-root>")

    root = Path(sys.argv[1])
    target_rel = "atlas/receive/huode_shilianb.png"
    target = root / target_rel
    atlas_rel = "atlas/combat/result.atlas"
    atlas_path = root / atlas_rel
    if not atlas_path.is_file():
        raise SystemExit(f"cannot derive {target_rel}: missing {atlas_rel}")

    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    frame = atlas.get("frames", {}).get("huode_shilianb.png")
    meta = atlas.get("meta") or {}
    page_name = meta.get("image")
    if not isinstance(frame, dict) or not isinstance(page_name, str) or not page_name:
        raise SystemExit("combat/result.atlas has no huode_shilianb.png frame/page")

    rect = frame.get("frame") or {}
    try:
        x, y = int(rect["x"]), int(rect["y"])
        width, height = int(rect["w"]), int(rect["h"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"invalid huode_shilianb frame rectangle: {exc}") from exc
    if min(x, y) < 0 or min(width, height) <= 0:
        raise SystemExit("invalid huode_shilianb frame bounds")

    page_path = atlas_path.parent / page_name
    if not page_path.is_file():
        raise SystemExit(f"cannot derive {target_rel}: missing atlas page {page_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(page_path) as page:
        if x + width > page.width or y + height > page.height:
            raise SystemExit(
                f"frame exceeds atlas page: page={page.size}, frame={(x, y, width, height)}"
            )
        page.crop((x, y, x + width, y + height)).convert("RGBA").save(target, format="PNG")

    data = target.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    manifest_path = root.parent / "snapshot-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest.setdefault("files", {})
        files[target_rel] = {
            "bytes": len(data),
            "sha256": digest,
            "content_type": "image/png",
            "derived_from": atlas_rel,
            "atlas_page": str(page_path.relative_to(root)).replace("\\", "/"),
            "frame": {"x": x, "y": y, "width": width, "height": height},
        }
        manifest["derived_assets"] = sorted(
            set(manifest.get("derived_assets", [])) | {target_rel}
        )
        manifest["downloaded_file_count"] = len(files)
        total_bytes = sum(int(item.get("bytes", 0)) for item in files.values())
        manifest["downloaded_bytes"] = total_bytes
        manifest["downloaded_mib"] = round(total_bytes / (1024 * 1024), 2)
        manifest["missing"] = [
            path for path in manifest.get("missing", []) if path != target_rel
        ]
        manifest["errors"] = [
            item for item in manifest.get("errors", [])
            if item.get("path") != target_rel
        ]
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(
        f"DERIVED_ATLAS_ASSET=PASS path={target_rel} "
        f"size={width}x{height} bytes={len(data)} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
