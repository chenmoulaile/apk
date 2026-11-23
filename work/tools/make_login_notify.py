#!/usr/bin/env python3
"""Generate the verified QuickSDK loginNotify bridge envelope for local tests.

This is not the game's HTTP login response and does not patch or run the APK.
"""
from __future__ import annotations

import argparse
import base64
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uid", default="offline-local-001")
    parser.add_argument("--username", default="离线玩家")
    parser.add_argument("--token", default="offline-local-session")
    parser.add_argument("--oaid", default="")
    parser.add_argument("--status-key", default="LOCAL_OFFLINE")
    parser.add_argument(
        "--failed",
        action="store_true",
        help="generate a failure callback instead of a success callback",
    )
    args = parser.parse_args()

    payload = {
        "action": "loginNotify",
        "data": {
            "status": not args.failed,
            "uid": args.uid,
            "username": args.username,
            "token": args.token,
            "oaid": args.oaid,
            "status_key": args.status_key if args.failed else "",
        },
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")

    print("Decoded bridge payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\nBase64 argument for CallbackFromAndroid(string):")
    print(encoded)
    print(
        "\nNOTE: The app-side QuickSDK.quickData.channel_type is read separately "
        "by the bridge. This generator does not set it."
    )
    print(
        "NOTE: This only tests the QuickSDK H5/native callback shape; it does not "
        "satisfy the remote game's own login API."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
