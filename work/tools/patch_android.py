#!/usr/bin/env python3
"""Patch the native JS-shell startup so offline mode does not show a fatal network dialog."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

def patch(root: Path) -> None:
    candidates = [p for p in root.rglob("MainActivity.smali")
                  if "com/qk/plugin/js/shell/MainActivity" in str(p).replace("\\", "/")]
    if not candidates:
        raise SystemExit("MainActivity.smali not found after apktool decode")
    path = candidates[0]
    source = path.read_text(encoding="utf-8", errors="replace")
    method = re.search(
        r"(?ms)^\.method[^\n]*\bonCreate\(Landroid/os/Bundle;\)V[^\n]*\n.*?^\.end method",
        source,
    )
    if not method:
        raise SystemExit("MainActivity.onCreate(Bundle) method not found")
    block = method.group(0)
    lines = block.splitlines()
    call_index = next((i for i, line in enumerate(lines)
                       if "->checkNetOk()Z" in line), None)
    if call_index is None:
        raise SystemExit("checkNetOk() call not found in onCreate")
    branch_index = None
    for i in range(call_index + 1, min(call_index + 5, len(lines))):
        if re.search(r"\bif-(?:eqz|nez)\s+\w+,\s*:cond_\d+", lines[i]):
            branch_index = i
            break
    if branch_index is None:
        if any(re.search(r"\bgoto(?:/16|/32)?\s+:cond_\d+", line) for line in lines[call_index+1:call_index+5]):
            print("Native offline network dialog is already bypassed")
            return
        raise SystemExit("conditional branch after checkNetOk() not found")
    target = re.search(r"(:cond_\d+)", lines[branch_index]).group(1)
    if not any(line.strip() == target for line in lines[branch_index+1:]):
        raise SystemExit(f"network dialog skip label {target} is missing")
    lines[branch_index] = re.sub(r"if-(?:eqz|nez)\s+\w+,\s*:cond_\d+", "goto " + target, lines[branch_index])
    patched = "\n".join(lines)
    source = source[:method.start()] + patched + source[method.end():]
    path.write_text(source, encoding="utf-8")
    # QuickSDK may push a login callback before the H5 document has parsed its bridge stub.
    # Guard the native javascript: URL so an early callback cannot raise a page-level ReferenceError.
    callback_marker = "CallbackFromAndroid"
    guarded_marker = "if(window.CallbackFromAndroid)CallbackFromAndroid"
    callback_matches = []
    for smali in root.rglob("*.smali"):
        content = smali.read_text(encoding="utf-8", errors="replace")
        count = content.count(callback_marker)
        if count:
            callback_matches.append((smali, content, count))
    total_callbacks = sum(count for _, _, count in callback_matches)
    if total_callbacks != 1:
        raise SystemExit(f"expected one native CallbackFromAndroid javascript URL, found {total_callbacks}")
    smali, content, count = callback_matches[0]
    smali.write_text(content.replace(callback_marker, guarded_marker), encoding="utf-8")
    print(f"Guarded early QuickSDK callback in {smali}")
    summary = root.parent / "native-network-dialog-patch.txt"
    summary.write_text(
        "Patched com.qk.plugin.js.shell.MainActivity.onCreate: "
        f"checkNetOk() result now unconditionally skips network AlertDialog via {target}\n"
        f"Guarded {total_callbacks} early CallbackFromAndroid javascript call(s) in {smali.name}\n",
        encoding="utf-8",
    )
    print(summary.read_text(encoding="utf-8").strip())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    args = parser.parse_args()
    patch(args.decoded_apk)
