"""Materialize the merged effective context into .lcdd/."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .yamlmini import dump

__all__ = ["materialize", "render_agents_md", "render_context_md", "safe_context_filename"]

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def safe_context_filename(cid: str) -> str:
    """Reject context ids that could escape or shadow the contexts/ directory."""
    if not isinstance(cid, str) or not cid:
        raise ValueError(f"unsafe context id for materialization: {cid!r}")
    if cid in (".", "..") or cid.startswith(".") or ".." in cid or not _SAFE_ID_RE.fullmatch(cid):
        raise ValueError(f"unsafe context id for materialization: {cid!r}")
    return f"{cid}.yaml"


def _render_rule(rule):
    level = rule.get("level", "must")
    label = {"must": "MUST", "must-not": "MUST NOT", "should": "SHOULD"}.get(level, level.upper())
    line = f"- **{label}** `{rule.get('id', '')}` — {rule.get('instruction', '')}"
    rationale = rule.get("rationale")
    if rationale:
        line += f" ({rationale})"
    return line


def render_agents_md(merged, prose_sources=None):
    lines = [
        "# AI coding rules (from OpenCraft Context Packs)",
        "",
        "Rules below are structured, merged, and versioned via `.lcdd/contexts/` and `.lcdd/project/ai-rules.yaml`.",
        "",
    ]
    if merged["ai_rules"]:
        lines.append("## Rules")
        lines.append("")
        for rule in merged["ai_rules"]:
            lines.append(_render_rule(rule))
        lines.append("")
    if prose_sources:
        lines.append("## Pack prose")
        lines.append("")
        for source in prose_sources:
            lines.append(f"### {source['pack']} v{source['version']}")
            lines.append("")
            lines.append(source["text"].strip())
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_context_md(merged):
    knowledge = merged["knowledge"]
    out = ["# Living Context", ""]
    out.append(
        "This file is generated from resolved OpenCraft Context Packs. "
        "Machine-readable sources live in `contexts/` and `project/`."
    )
    out.append("")

    vision = knowledge.get("vision")
    if vision:
        out.append("## Vision")
        out.append("")
        out.append(f"- **Purpose:** {vision.get('purpose', '—')}")
        users = vision.get("target_users") or []
        if users:
            out.append(f"- **Target users:** {', '.join(users)}")
        if vision.get("primary_journey"):
            out.append(f"- **Primary journey:** {vision['primary_journey']}")
        out.append("")

    stack = knowledge.get("tech-stack")
    if stack:
        out.append("## Technology stack")
        out.append("")
        if stack.get("language"):
            out.append(f"- Language: {stack['language']}")
        if stack.get("runtime"):
            out.append(f"- Runtime: {stack['runtime']}")
        if stack.get("framework"):
            out.append(f"- Framework: {stack['framework']}")
        for entry in stack.get("entries", []):
            version = f" {entry.get('version', '')}".rstrip()
            out.append(f"- {entry.get('name')}{version} — {entry.get('role')}")
        out.append("")

    conventions = knowledge.get("conventions")
    if conventions:
        out.append("## Conventions")
        out.append("")
        for section in ("naming", "formatting", "imports", "state", "structure"):
            rules = conventions.get(section) or []
            if rules:
                out.append(f"### {section}")
                for rule in rules:
                    out.append(f"- `{rule.get('id')}` — {rule.get('rule')}")
                out.append("")

    security = knowledge.get("security")
    if security:
        out.append("## Security")
        out.append("")
        for rule in security.get("rules", []):
            out.append(f"- **{rule.get('severity', 'info').upper()}** `{rule.get('id')}` — {rule.get('description')}")
        out.append("")

    out.append("## Active contexts")
    out.append("")
    if merged["contexts"]:
        out.append("| ID | Title | Level | Enforcement |")
        out.append("|---|---|---|---|")
        for cid in sorted(merged["contexts"]):
            ctx = merged["contexts"][cid]
            level = ctx.get("authority", {}).get("level", "?")
            mode = ctx.get("enforcement", {}).get("mode", "—")
            out.append(f"| `{cid}` | {ctx.get('title', '')} | {level} | {mode} |")
    else:
        out.append("_No active contexts._")
    out.append("")

    if merged["knowledge"].get("ai-rules"):
        out.append("## AI coding rules")
        out.append("")
        out.append("See `ai/AGENTS.md` (rendered) and `project/ai-rules.yaml` (structured).")
        out.append("")
    out.append("## Sources")
    out.append("")
    out.append("This living context is resolved from the packs declared in `packs.yaml`; versions are pinned in `packs.lock.json`.")
    out.append("")
    return "\n".join(out)


def materialize(project_dir, merged, ordered, project, lock_integrity=None):
    """Write the effective context into <project_dir>/.lcdd/."""
    lcdd = Path(project_dir) / ".lcdd"
    contexts_dir = lcdd / "contexts"
    project_out = lcdd / "project"
    ai_dir = lcdd / "ai"
    for directory in (contexts_dir, project_out, ai_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # Regenerate generated output; preserve user-local files (e.g. .lcdd/local/).
    for directory in (contexts_dir, project_out):
        for path in directory.glob("*.yaml"):
            path.unlink()
    for path in (ai_dir / "AGENTS.md", lcdd / "CONTEXT.md", lcdd / "report.json"):
        if path.is_file():
            path.unlink()

    for cid, ctx in merged["contexts"].items():
        (contexts_dir / safe_context_filename(cid)).write_text(dump(ctx), encoding="utf-8")

    for kind, doc in merged["knowledge"].items():
        (project_out / f"{kind}.yaml").write_text(dump(doc), encoding="utf-8")

    prose_sources = [
        {"pack": item["name"], "version": item["version"], "text": item["pack"]["ai_prose"]}
        for item in ordered
        if item["pack"]["ai_prose"]
    ]
    (ai_dir / "AGENTS.md").write_text(render_agents_md(merged, prose_sources), encoding="utf-8")
    (lcdd / "CONTEXT.md").write_text(render_context_md(merged), encoding="utf-8")

    lockfile = {
        "schema": "https://opencraft.dev/schema/packs.lock/v1",
        "algorithm": "sha256",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved": [],
    }
    for item in ordered:
        manifest = item["pack"]["manifest"]
        lockfile["resolved"].append(
            {
                "name": item["name"],
                "version": item["version"],
                "integrity": lock_integrity.get(item["name"]) if lock_integrity else "",
                "precedence": item["precedence"],
                "extends": list(manifest.get("extends", [])),
                "dependencies": list(manifest.get("dependencies", [])),
                "deprecated": manifest.get("lifecycle") == "deprecated",
            }
        )
    (lcdd / "packs.lock.json").write_text(
        json.dumps(lockfile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (lcdd / "report.json").write_text(
        json.dumps(merged["report"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return lcdd
