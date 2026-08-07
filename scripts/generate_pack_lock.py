#!/usr/bin/env python3
"""Generate or verify packs.lock.json (repo-source integrity lock for packs/).

Usage:
  python3 scripts/generate_pack_lock.py          # write packs.lock.json
  python3 scripts/generate_pack_lock.py --check  # verify only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib.registry import pack_integrity  # noqa: E402
from packlib.manifest import load_pack  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS_ROOT = REPO_ROOT / "packs"
LOCK_PATH = REPO_ROOT / "packs.lock.json"


def build_lock():
    lock = {
        "schema": "https://opencraft.dev/schema/packs.lock/v1",
        "algorithm": "sha256",
        "collection": "opencraft-context-packs",
        "source": "https://github.com/Lelianto/opencraft-skills",
        "packs": {},
    }
    for pack_dir in sorted(PACKS_ROOT.iterdir()):
        if not (pack_dir / "pack.yaml").is_file():
            continue
        pack = load_pack(pack_dir)
        lock["packs"][pack["name"]] = {
            "version": pack["version"],
            "integrity": pack_integrity(pack_dir),
        }
    return lock


def main():
    check = "--check" in sys.argv[1:]
    lock = build_lock()
    if check:
        if not LOCK_PATH.is_file():
            print("FAIL packs.lock.json is missing")
            return 1
        current = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        mismatches = []
        for name, entry in lock["packs"].items():
            if name not in current.get("packs", {}):
                mismatches.append(f"{name}: missing from lock")
            elif current["packs"][name]["integrity"] != entry["integrity"]:
                mismatches.append(f"{name}: integrity mismatch")
        if mismatches:
            print("FAIL integrity lock is out of date:")
            for mismatch in mismatches:
                print(f"  - {mismatch}")
            print("Run python3 scripts/generate_pack_lock.py to regenerate.")
            return 1
        print(f"OK {len(lock['packs'])} packs verified against packs.lock.json")
        return 0
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"OK wrote packs.lock.json for {len(lock['packs'])} packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
