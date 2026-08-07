#!/usr/bin/env python3
"""Performance benchmark for the Context Packs engine.

Measures validate --all, an end-to-end install (Python and Node), and resolver
scaling on a synthetic 100-pack diamond. Fails (exit 1) if any step exceeds a
loose upper bound, so a regression trips CI.

Usage:
  python3 scripts/pack-bench.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib import manifest, merger, resolver  # noqa: E402
from packlib.registry import Registry  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

BOUNDS = {
    "validate_all": 15.0,
    "install_python": 10.0,
    "install_node": 10.0,
    "resolve_100_pack_diamond": 5.0,
}


def timed(label, fn, bound):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    status = "OK " if elapsed <= bound else "SLOW"
    print(f"{status} {label:28s} {elapsed:7.3f}s (limit {bound:5.1f}s)")
    return result, elapsed <= bound


def make_synthetic(root: Path, count: int):
    """Build `count` packs in a diamond: each extends two lower-index parents."""
    packs_root = root / "packs"
    for i in range(count):
        parents = []
        if i >= 1:
            parents.append(f"base-{i - 1}-pack@^1")
        if i >= 2:
            parents.append(f"base-{i - 2}-pack@^1")
        extends = "extends:\n" + "".join(f"  - {p}\n" for p in parents) if parents else ""
        write(
            packs_root / f"base-{i}-pack" / "pack.yaml",
            "schema: https://opencraft.dev/schema/context-pack/v1\n"
            f"name: base-{i}-pack\nversion: 1.0.0\ntype: technology\ndescription: t\n"
            "license: MIT\nauthor:\n  type: organization\n  id: o\n  name: O\n"
            f"{extends}"
            "lifecycle: active\ngovernance:\n  classification: local-standard\n  approval_required: false\n"
            "owner:\n  type: organization\n  id: o\n  name: O\n",
        )
    proj = root / "proj"
    write(
        proj / "packs.yaml",
        "schema: https://opencraft.dev/schema/project-packs/v1\nextends:\n"
        + "".join(f"  - base-{i}-pack@^1\n" for i in range(count - 1, count - 11, -1)),
    )
    return packs_root, proj


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    results = []

    def validate_all():
        return subprocess.run(
            [sys.executable, "scripts/packtool.py", "packs", "validate", "--all"],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )

    results.append(timed("validate --all (13 packs)", validate_all, BOUNDS["validate_all"]))

    demo = Path(tempfile.mkdtemp())
    write(
        demo / "packs.yaml",
        "schema: https://opencraft.dev/schema/project-packs/v1\nextends:\n"
        "  - nextjs-pack@^1\n  - security-pack@^1\n  - fintech-pack@^1\nconflict_policy: fail\n",
    )
    results.append(
        timed(
            "install --project (python)",
            lambda: subprocess.run(
                [sys.executable, "scripts/packtool.py", "packs", "install", "--project", str(demo)],
                cwd=REPO_ROOT, capture_output=True, check=True,
            ),
            BOUNDS["install_python"],
        )
    )
    results.append(
        timed(
            "install --project (node)",
            lambda: subprocess.run(
                ["node", "scripts/packtool.mjs", "packs", "install", "--project", str(demo)],
                cwd=REPO_ROOT, capture_output=True, check=True,
            ),
            BOUNDS["install_node"],
        )
    )

    root = Path(tempfile.mkdtemp())
    packs_root, proj = make_synthetic(root, 100)
    reg = Registry(packs_root)
    project = manifest.load_project_declaration(proj)

    def resolve100():
        ordered = resolver.resolve(project, reg)
        merger.merge(ordered, project)
        return ordered

    results.append(timed("resolve 100-pack diamond", resolve100, BOUNDS["resolve_100_pack_diamond"]))

    ok = all(status for _, status in results)
    print(f"\n{'ALL BENCHMARKS WITHIN BOUNDS' if ok else 'BENCHMARK REGRESSION'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
