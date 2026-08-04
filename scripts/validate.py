#!/usr/bin/env python3
"""Validate the portable subset used by this Agent Skills collection."""

from __future__ import annotations

from pathlib import Path
import re
import sys


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\[[^]]+\]\((references/[^)]+)\)")


def frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return None
    values: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            return None
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values, parts[2]


def validate(skill: Path) -> list[str]:
    errors: list[str] = []
    source = skill / "SKILL.md"
    text = source.read_text(encoding="utf-8")
    parsed = frontmatter(text)
    if parsed is None:
        return ["invalid or missing YAML frontmatter"]
    metadata, body = parsed
    if set(metadata) != {"name", "description"}:
        errors.append("portable frontmatter must contain only name and description")
    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if name != skill.name:
        errors.append(f"name {name!r} does not match directory")
    if len(name) > 64 or not NAME_PATTERN.fullmatch(name):
        errors.append("name must be lowercase kebab-case and at most 64 characters")
    if not 1 <= len(description) <= 1024:
        errors.append("description must contain 1-1024 characters")
    if len(text.splitlines()) >= 500:
        errors.append("SKILL.md must stay below 500 lines")
    if "TODO" in text or "[TODO" in text:
        errors.append("unresolved TODO placeholder")
    if not body.strip():
        errors.append("instruction body is empty")
    for relative in LINK_PATTERN.findall(body):
        if not (skill / relative).is_file():
            errors.append(f"missing referenced file: {relative}")
    openai_yaml = skill / "agents/openai.yaml"
    if not openai_yaml.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        ui = openai_yaml.read_text(encoding="utf-8")
        if f"${name}" not in ui:
            errors.append("openai.yaml default_prompt must mention the skill")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "skills"
    skills = sorted(path for path in root.iterdir() if path.is_dir())
    failures = 0
    for skill in skills:
        errors = validate(skill)
        if errors:
            failures += 1
            print(f"FAIL {skill.name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {skill.name}")
    print(f"\n{len(skills) - failures}/{len(skills)} skills passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
