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
# The first offline playability pass deliberately includes the asset groups used
# by the boot flow, main city, main PvE challenge, battle, and result/reward UI.
# The full zip.txt maps over 7k optional event/ranking skins; fetching all of them
# during the first APK build adds minutes without improving the core offline loop.
OFFLINE_UI_SKIN_PREFIXES = (
    "mainui/",
    "checkpoint/mainchallenge/",
    "checkpoint/result/",
    "checkpoint/quickcombat/",
    "checkpoint/quickchallenge/",
    "checkpoint/quickchallengeend/",
    "checkpoint/offlinegiftpanel/",
    "combatformation/",
    "combat/",
    "newbag/",
    # Dynamic pet strengthening panels reference these loose images via zip.txt.
    "pokemon/",
    "zpower/",
    "upgradelight/",
)

def is_offline_ui_skin(path: str) -> bool:
    return path.lower().startswith(OFFLINE_UI_SKIN_PREFIXES)


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
    "atlas/guide1.atlas",
    # Runtime fallback groups requested by loadCommonResAndConfigZip().
    "atlas/common.atlas",
    "atlas/common2.atlas",
    "atlas/commonAni.atlas",
    # Runtime-loaded resources can be absent from literal JS path scans.
    "atlas/combat/animation0.atlas",
    "atlas/combat/frmBattle.atlas",
    "atlas/combat/ani1.atlas",
    "atlas/mainUI/laba02_bg.png",
    # Dynamic UI groups normally fall back to these atlas bundles at runtime.
    "atlas/Checkpoint/MainChallenge.atlas",
    "atlas/Checkpoint/offLineGiftPanel.atlas",
    "atlas/Checkpoint/QuickCombat.atlas",
    "atlas/Checkpoint/Result.atlas",
    "atlas/CombatFormation.atlas",
    "atlas/combat/result.atlas",
    "atlas/combat/communicator.atlas",
    "atlas/NewBag.atlas",
]
EXT_RE = re.compile(
    r"(?<![A-Za-z0-9_])((?:atlas|res|json|font|sound|scene|role|music)/"
    r"[A-Za-z0-9_./-]+\.(?:atlas|json|png|jpg|jpeg|webp|ani|mp3|wav|ttf|fnt|sk|zip))",
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
        pending = sorted(set(items))
        max_attempts = 3

        def is_transient(error: str | None) -> bool:
            if not error:
                return False
            return error.startswith((
                "URLError:",
                "RemoteDisconnected:",
                "TimeoutError:",
                "ConnectionResetError:",
                "ConnectionAbortedError:",
                "IncompleteRead:",
                "HTTP 5",
            ))

        for attempt in range(max_attempts):
            if not pending:
                break
            retry: list[str] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
                futures = {executor.submit(download_one, item): item for item in pending}
                for future in concurrent.futures.as_completed(futures):
                    relative, data, headers, error = future.result()
                    if data is None:
                        if attempt + 1 < max_attempts and is_transient(error):
                            retry.append(relative)
                            manifest["download_retry_count"] = int(manifest.get("download_retry_count", 0)) + 1
                            continue
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
            pending = retry
            if pending and attempt + 1 < max_attempts:
                time.sleep(attempt + 1)
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
    # AudioManager calls use bare filenames, while the runtime resolves them under res/music/.
    audio_refs = {
        f"res/music/{name}"
        for name in re.findall(r"""["']([A-Za-z0-9_-]+\.(?:wav|mp3))["']""", code, re.IGNORECASE)
    }
    queue.update(audio_refs)
    # Some UI assets are referenced relative to the atlas directory (mainUI/)
    # rather than with an explicit atlas/ prefix in the minified bundle.
    queue.update(
        "atlas/" + item
        for item in re.findall(
            r"[\"\'](mainUI/[A-Za-z0-9_./-]+\.(?:png|jpg|jpeg|webp))[\"\']",
            code,
            re.IGNORECASE,
        )
    )
    # The scene player avatar is loaded dynamically by RoleAtlasAnimation.
    # A fresh offline profile uses avatarId=1 and these directional frame names.
    queue.update({
        "atlas/role/1.atlas",
        "atlas/trainerInfo.atlas",
        "res/music/10004.mp3",
        *[
            f"role/1/{direction}{frame}.png"
            for direction, count in (
                ("back", 4), ("front", 4), ("left", 6),
                ("rideback", 1), ("ridefront", 1), ("rideleft", 1),
                ("standback", 1), ("standfront", 1), ("standleft", 1),
            )
            for frame in range(1, count + 1)
        ],
    })
    config_path = output / "zip.txt"
    if config_path.is_file():
        decoded = decode_config(config_path.read_bytes())
        if decoded is not None:
            config_output = output.parent / "zip.decompressed.json"
            config_output.write_bytes(decoded)
            text_config = decoded.decode("utf-8", errors="replace")
            queue.update(path_candidates(text_config))
            # UI textures in the packed config commonly omit their atlas/ prefix.
            queue.update(
                "atlas/" + item
                for item in re.findall(
                    r"""["'](mainUI/[A-Za-z0-9_./-]+\.(?:png|jpg|jpeg|webp))["']""",
                    text_config,
                    re.IGNORECASE,
                )
            )
            try:
                parsed = json.loads(text_config)
                image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
                ui_skin_refs: set[str] = set()
                combat_animation_refs: set[str] = set()

                def walk(value: object) -> None:
                    if isinstance(value, str):
                        queue.update(path_candidates(value))
                        normalized = value.strip().lstrip("/")
                        candidate = PurePosixPath(normalized)
                        # These clips are relative to atlas/, not res/.
                        if (
                            candidate.suffix.lower() == ".ani"
                            and normalized.lower().startswith("combat/animation/")
                            and ".." not in candidate.parts
                        ):
                            combat_animation_refs.add("atlas/" + normalized)
                        elif (
                            "/" in normalized
                            and candidate.suffix.lower() in image_suffixes
                            and not normalized.startswith(("atlas/", "res/", "scene/", "http://", "https://"))
                            and ".." not in candidate.parts
                            and is_offline_ui_skin(normalized)
                        ):
                            ui_skin_refs.add("atlas/" + normalized)
                    elif isinstance(value, list):
                        for child in value:
                            walk(child)
                    elif isinstance(value, dict):
                        for key, child in value.items():
                            walk(key)
                            walk(child)

                walk(parsed)
                queue.update(ui_skin_refs)
                queue.update(combat_animation_refs)
                manifest["ui_skin_asset_candidates"] = len(ui_skin_refs)
                manifest["combat_animation_asset_candidates"] = len(combat_animation_refs)

                # Sound files are keyed by IDs in cdc_sound_conf, not always
                # referenced literally in code.js (e.g. 20019.wav).
                music_refs: set[str] = set()
                for sound in parsed.get("cdc_sound_conf", []):
                    if not isinstance(sound, dict):
                        continue
                    filename = sound.get("file")
                    if (
                        isinstance(filename, str)
                        and filename
                        and PurePosixPath(filename).name == filename
                        and PurePosixPath(filename).suffix.lower() in {".wav", ".mp3"}
                    ):
                        music_refs.add("res/music/" + filename)
                queue.update(music_refs)
                manifest["music_asset_candidates"] = len(music_refs)

                # Main PvE panels build item and point-icon URLs from ids.
                pet_by_id_for_items = {
                    int(row.get("id", 0)): row
                    for row in parsed.get("cdc_pet_conf", [])
                    if isinstance(row, dict) and str(row.get("id", "")).isdigit()
                }
                point_item_ids = {3, 4, 56, 59}
                main_scene_item_refs: set[str] = set()
                for stage in parsed.get("cdc_new_scene_grade_conf", []):
                    if not isinstance(stage, dict) or int(stage.get("id", 0) or 0) > 10:
                        continue
                    for action in stage.get("actionArr", []):
                        if not isinstance(action, dict):
                            continue
                        params = action.get("params", [])
                        if not isinstance(params, list) or not params:
                            continue
                        action_type = int(action.get("type", 0) or 0)
                        item_id = int(params[0] or 0)
                        if action_type == 100:
                            point_item_ids.add(4)
                        elif action_type == 101:
                            point_item_ids.add(3)
                        elif action_type == 102:
                            point_item_ids.add(2)
                        elif action_type == 109:
                            point_item_ids.add(item_id)
                        elif action_type == 103 and item_id > 0:
                            if 1000350 <= item_id <= 1000385:
                                main_scene_item_refs.add("res/items/1/1000350.png")
                            elif item_id // 1000000 == 5:
                                pet = pet_by_id_for_items.get(item_id % 100000)
                                if pet and pet.get("spiritIcon"):
                                    queue.add("res/icons/" + str(pet["spiritIcon"]))
                            else:
                                main_scene_item_refs.add(f"res/items/{item_id // 1000000}/{item_id}.png")
                for point_item in parsed.get("cdc_point_item_conf", []):
                    if not isinstance(point_item, dict) or int(point_item.get("id", 0) or 0) not in point_item_ids:
                        continue
                    for field in ("smallIcon", "bigIcon"):
                        icon = point_item.get(field)
                        if isinstance(icon, str) and icon and "/" not in icon and ".." not in icon:
                            queue.add(f"res/icons/{icon}.png")
                queue.update(main_scene_item_refs)
                manifest["main_scene_item_asset_candidates"] = len(main_scene_item_refs)
                manifest["main_scene_point_icon_ids"] = sorted(point_item_ids)

                # Battle sprites and skill effects are looked up dynamically from
                # the config tables and cannot be discovered by scanning code.js.
                pet_rows = parsed.get("cdc_pet_conf", [])
                pet_by_id = {
                    int(row.get("id", 0)): row
                    for row in pet_rows
                    if isinstance(row, dict) and str(row.get("id", "")).isdigit()
                }
                pve_pet_by_id = {
                    int(row.get("id", 0)): row
                    for row in parsed.get("cdc_pve_pet_conf", [])
                    if isinstance(row, dict) and str(row.get("id", "")).isdigit()
                }
                combat_pet_ids = {3101, 3108}
                for team in parsed.get("cdc_pve_team_conf", []):
                    if not isinstance(team, dict):
                        continue
                    pet_ids = team.get("petId", [])
                    if isinstance(pet_ids, list):
                        for pve_pet_id in pet_ids:
                            try:
                                pve_pet = pve_pet_by_id.get(int(pve_pet_id))
                                if pve_pet and pve_pet.get("petId"):
                                    combat_pet_ids.add(int(pve_pet["petId"]))
                            except (TypeError, ValueError):
                                pass
                combat_sprite_refs = set()
                for pet_id in combat_pet_ids:
                    pet = pet_by_id.get(pet_id)
                    if not pet:
                        continue
                    image = pet.get("spiritImage")
                    if not isinstance(image, str) or not image:
                        continue
                    image_path = PurePosixPath(image)
                    if not image_path.is_absolute() and ".." not in image_path.parts:
                        combat_sprite_refs.add(str(PurePosixPath("res/combat/spirits") / image_path))
                    icon = pet.get("spiritIcon")
                    if isinstance(icon, str) and icon and "/" not in icon and ".." not in icon:
                        queue.add(f"res/icons/{icon}")
                combat_effect_refs = set()
                for effect in parsed.get("cdc_effect_conf", []):
                    if not isinstance(effect, dict):
                        continue
                    image = effect.get("imgFile")
                    if isinstance(image, str) and image and "/" not in image and ".." not in image:
                        combat_effect_refs.add(f"res/combat/skills/{image}.atlas")
                for buff in parsed.get("cdc_buff_conf", []):
                    if not isinstance(buff, dict):
                        continue
                    animation = buff.get("animation")
                    if isinstance(animation, str) and animation and "/" not in animation and ".." not in animation:
                        combat_effect_refs.add(f"res/combat/skills/{animation}.atlas")
                queue.update(combat_sprite_refs)
                queue.update(combat_effect_refs)
                manifest["combat_pet_sprite_candidates"] = len(combat_sprite_refs)
                manifest["combat_effect_atlas_candidates"] = len(combat_effect_refs)
            except json.JSONDecodeError as exc:
                manifest["errors"].append({"path": "zip.txt", "error": f"decompressed but JSON parse failed: {exc}"})  # type: ignore[union-attr]
            manifest["config_decompressed"] = {
                "path": str(config_output),
                "bytes": len(decoded),
                "sha256": sha256(decoded),
            }
        else:
            manifest["errors"].append({"path": "zip.txt", "error": "could not decompress with zlib variants"})  # type: ignore[union-attr]

    # Scene tile images are requested dynamically by PicObject as
    # res/scene/<id>/<tile>.jpg, so ordinary string scanning cannot discover them.
    scene_refs: set[str] = set()
    for scene_id, width, height in re.findall(
        r"new e\.SceneDes\(\[(\d+),(\d+),(\d+),", code
    ):
        sid, columns, rows = int(scene_id), int(width), int(height)
        scene_refs.update({
            f"res/scene/{sid}/icon.png",
            f"res/scene/{sid}/area.png",
            f"res/scene/{sid}/temp.jpg",
        })
        scene_refs.update(
            f"res/scene/{sid}/{tile}.jpg"
            for tile in range(1, columns * rows + 1)
        )
    queue.update(scene_refs)

    # res/ui.json stores a second class of texture references relative to atlas/.
    # Those paths are not necessarily present in code.js or .atlas metadata.
    ui_config = output / "res/ui.json"
    if ui_config.is_file():
        try:
            ui_data = json.loads(ui_config.read_text(encoding="utf-8"))
            ui_refs: set[str] = set()
            image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
            def collect_ui_images(value: object) -> None:
                if isinstance(value, str):
                    normalized = value.lstrip("/")
                    candidate = PurePosixPath(normalized)
                    if (
                        "/" in normalized
                        and candidate.suffix.lower() in image_suffixes
                        and not normalized.startswith(("atlas/", "res/", "scene/"))
                        and ".." not in candidate.parts
                        and is_offline_ui_skin(normalized)
                    ):
                        ui_refs.add("atlas/" + normalized)
                elif isinstance(value, list):
                    for child in value:
                        collect_ui_images(child)
                elif isinstance(value, dict):
                    for child in value.values():
                        collect_ui_images(child)
            collect_ui_images(ui_data)
            queue.update(ui_refs)
            manifest["ui_config_asset_candidates"] = len(ui_refs)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            manifest["errors"].append({"path": "res/ui.json", "error": f"UI asset scan failed: {exc}"})

    # Download all literal assets and any additional paths referenced by config.
    downloaded = fetch_batch(queue)
    # CORE_FILES are fetched in the first batch, before code/config discovery.
    # Include them too: their atlas JSON files contain the image dependencies
    # (for example atlas/common.png) required during the first game boot.
    all_downloaded = sorted(set(first) | set(downloaded))
    atlas_candidates = sorted(
        item for item in all_downloaded if item.lower().endswith(".atlas")
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
