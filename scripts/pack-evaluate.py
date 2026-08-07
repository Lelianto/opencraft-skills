#!/usr/bin/env python3
"""Validate pack eval fixtures (evals/cases.yaml) for completeness.

Every pack that ships evals/cases.yaml must provide positive, negative,
ambiguous, and assertion fixtures, mirroring the skills collection standard.

Usage:
  python3 scripts/pack-evaluate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib.yamlmini import load_file  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS_ROOT = REPO_ROOT / "packs"


def check_cases(path: Path, name: str):
    errors = []
    data = load_file(path)
    if not isinstance(data, dict):
        return [f"{name}: evals/cases.yaml is not a mapping"]
    positive = data.get("positive") or []
    negative = data.get("negative") or []
    ambiguous = data.get("ambiguous") or []
    assertions = data.get("assertions") or []
    if len(positive) < 3:
        errors.append(f"{name}: need at least 3 positive prompts (got {len(positive)})")
    if len(negative) < 2:
        errors.append(f"{name}: need at least 2 negative prompts (got {len(negative)})")
    if not ambiguous:
        errors.append(f"{name}: need at least 1 ambiguous prompt")
    if not assertions:
        errors.append(f"{name}: need at least 1 assertion")
    return errors


def main():
    failures = 0
    for pack_dir in sorted(PACKS_ROOT.iterdir()):
        cases = pack_dir / "evals" / "cases.yaml"
        if not cases.is_file():
            continue
        errors = check_cases(cases, pack_dir.name)
        if errors:
            failures += 1
            print(f"FAIL {pack_dir.name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {pack_dir.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
