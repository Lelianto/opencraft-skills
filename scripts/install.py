#!/usr/bin/env python3
"""Install canonical skills into project-level directories for supported agents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


TARGETS = {
    "agents": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "codex": Path(".codex/skills"),
    "cursor": Path(".cursor/skills"),
    "github": Path(".github/skills"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Target project root")
    parser.add_argument("--target", choices=[*TARGETS, "all"], default="agents")
    parser.add_argument("--mode", choices=["copy", "link"], default="copy")
    parser.add_argument("--force", action="store_true", help="Replace same-named installed skills")
    parser.add_argument("--with-project-files", action="store_true", help="Initialize AGENTS.md, PROJECT_CONTEXT.md, and .product templates")
    parser.add_argument("--human-loop", choices=["off", "autonomous", "guided", "approval-gated"], default="guided", help="Human decision mode for new project artifacts")
    return parser.parse_args()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_lock(repository: Path) -> dict[str, object]:
    lock = json.loads((repository / "skills.lock.json").read_text(encoding="utf-8"))
    for relative, expected in lock["files"].items():
        source = repository / relative
        if not source.is_file() or digest(source) != expected:
            raise ValueError(f"integrity check failed: {relative}")
    return lock


def initialize_project_files(repository: Path, project: Path, human_loop: str) -> list[str]:
    results: list[str] = []
    mappings = {
        repository / "templates/AGENTS.md": project / "AGENTS.md",
        repository / "templates/PROJECT_CONTEXT.md": project / "PROJECT_CONTEXT.md",
    }
    for source, target in mappings.items():
        if target.exists():
            results.append(f"SKIP {target} (exists)")
        else:
            shutil.copy2(source, target)
            results.append(f"OK   {target}")
    product_target = project / ".product"
    if product_target.exists():
        results.append(f"SKIP {product_target} (exists)")
    else:
        shutil.copytree(repository / "templates/product", product_target)
        config_path = product_target / "human-loop.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["enabled"] = human_loop != "off"
        config["mode"] = human_loop
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        results.append(f"OK   {product_target}")
    return results


def install_one(source: Path, destination: Path, mode: str, force: bool) -> str:
    target = destination / source.name
    if target.exists() or target.is_symlink():
        if not force:
            return f"SKIP {target} (exists; use --force to replace)"
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()

    destination.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copytree(source, target)
    else:
        relative_source = Path(os.path.relpath(source, destination))
        target.symlink_to(relative_source, target_is_directory=True)
    return f"OK   {target}"


def main() -> int:
    args = parse_args()
    repository = Path(__file__).resolve().parent.parent
    source_root = repository / "skills"
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        print(f"ERROR project does not exist: {project}", file=sys.stderr)
        return 2

    try:
        lock = verify_lock(repository)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR source integrity: {error}", file=sys.stderr)
        return 2

    skills = sorted(path for path in source_root.iterdir() if (path / "SKILL.md").is_file())
    if not skills:
        print(f"ERROR no skills found in {source_root}", file=sys.stderr)
        return 2

    selected = TARGETS if args.target == "all" else {args.target: TARGETS[args.target]}
    for client, relative_destination in selected.items():
        print(f"[{client}]")
        destination = project / relative_destination
        for source in skills:
            print(install_one(source, destination, args.mode, args.force))
    if args.with_project_files:
        print("[project]")
        for result in initialize_project_files(repository, project, args.human_loop):
            print(result)
    receipt = {
        "collection": lock["collection"],
        "version": lock["version"],
        "source": lock["source"],
        "targets": list(selected),
        "mode": args.mode,
        "skills": [source.name for source in skills],
        "human_loop": args.human_loop if args.with_project_files else None,
    }
    (project / ".ai-skills-install.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
