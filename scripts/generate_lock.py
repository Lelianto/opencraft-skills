#!/usr/bin/env python3
"""Generate or verify SHA-256 provenance for canonical skill files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(repository: Path) -> dict[str, object]:
    collection = json.loads((repository / "collection.json").read_text(encoding="utf-8"))
    files: dict[str, str] = {}
    for path in sorted((repository / "skills").rglob("*")):
        if path.is_file():
            files[path.relative_to(repository).as_posix()] = digest(path)
    return {
        "schema_version": "1.0",
        "collection": collection["name"],
        "version": collection["version"],
        "source": collection["source"],
        "algorithm": "sha256",
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if skills.lock.json is stale")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    lock_path = repository / "skills.lock.json"
    expected = build(repository)
    rendered = json.dumps(expected, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not lock_path.is_file() or lock_path.read_text(encoding="utf-8") != rendered:
            print("ERROR skills.lock.json is missing or stale", file=sys.stderr)
            return 1
        print(f"PASS skills.lock.json ({len(expected['files'])} files)")
        return 0
    lock_path.write_text(rendered, encoding="utf-8")
    print(f"WROTE {lock_path} ({len(expected['files'])} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
