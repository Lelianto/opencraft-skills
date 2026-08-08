#!/usr/bin/env python3
"""Generate or verify packs/registry/index.json (the remote catalog).

The catalog maps every reference pack to its @opencraft/* npm package and pins
the sha256 integrity of the pack content. Keeping it in sync with packs/ is
required before any pack is published or fetched over the remote transport.

Usage:
  python3 scripts/generate_pack_catalog.py          # write index.json
  python3 scripts/generate_pack_catalog.py --check  # verify only
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
CATALOG_PATH = REPO_ROOT / "packs" / "registry" / "index.json"

FIELD_ORDER = [
    "name", "type", "description", "license", "author", "tags",
    "latest", "lifecycle", "versions",
]

PACK_TYPE_LABEL = {
    "baseline": "baseline",
    "technology": "technology",
    "framework": "framework",
    "baas": "baas",
    "cross-cutting": "cross-cutting",
    "domain": "domain",
}


def build_catalog():
    packs = []
    for pack_dir in sorted(PACKS_ROOT.iterdir()):
        manifest_path = pack_dir / "pack.yaml"
        if not manifest_path.is_file():
            continue
        pack = load_pack(pack_dir)
        manifest = pack["manifest"]
        name = manifest.get("name")
        version = manifest.get("version")
        if not name or not version:
            continue
        author = manifest.get("author") or {}
        owner = manifest.get("owner") or {}
        entry = {
            "name": name,
            "type": PACK_TYPE_LABEL.get(manifest.get("type"), manifest.get("type") or "technology"),
            "description": manifest.get("description") or "",
            "license": manifest.get("license") or "MIT",
            "author": author.get("name") or owner.get("name") or "OpenCraft",
            "tags": sorted(manifest.get("tags") or []),
            "latest": version,
            "lifecycle": manifest.get("lifecycle") or "active",
            "versions": {
                version: {
                    "npm": f"@opencraft/{name}",
                    "integrity": pack_integrity(pack_dir),
                    "extends": list(manifest.get("extends") or []),
                    "dependencies": list(manifest.get("dependencies") or []),
                }
            },
        }
        entry = {k: entry[k] for k in FIELD_ORDER}
        packs.append(entry)
    packs.sort(key=lambda e: e["name"])
    return {"schema": "https://opencraft.dev/schema/registry/v1", "packs": packs}


def main():
    check = "--check" in sys.argv[1:]
    catalog = build_catalog()
    if check:
        if not CATALOG_PATH.is_file():
            print("FAIL packs/registry/index.json is missing")
            return 1
        current = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        if current != catalog:
            print("FAIL packs/registry/index.json is out of date; run scripts/generate_pack_catalog.py")
            return 1
        print(f"OK catalog ({len(catalog['packs'])} packs) verified against packs tree")
        return 0
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"OK wrote packs/registry/index.json for {len(catalog['packs'])} packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
