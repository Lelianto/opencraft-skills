"""Validation: pack structure, LCDD context semantics, PKD schemas, and the
effective merged set."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from . import jsonschema_mini
from .knowledge import KNOWLEDGE_KINDS, kind_exists
from .manifest import PACK_NAME_RE, SEMVER_RE, PackError, parse_ref
from .yamlmini import load_file

__all__ = [
    "load_schema_store",
    "validate_pack",
    "validate_project",
    "validate_effective",
    "context_errors",
]

CONTEXT_LIFECYCLES = ["draft", "candidate", "approved", "active", "deprecated", "archived"]
SOURCE_TYPES = [
    "individual", "organization", "standard-body", "ai-system", "community",
    "automated", "regulatory", "documentation", "meeting", "incident", "unknown",
]
GOVERNANCE_CLASSES = [
    "hardened-mandate", "hardened-standard", "hardened-local",
    "local-standard", "local-guideline", "local-experimental",
]
ENFORCEMENT_MODES = ["block", "warn", "comment", "silent"]
CTX_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_SECRET_RE = re.compile(
    r"(?i)(?:api[_-]?key|secret|password|passwd|private[_-]?key|access[_-]?token"
    r"|authorization|bearer|connection[_-]?string)\s*[:=]\s*(?:Bearer\s+)?[A-Za-z0-9_\-/.+]{10,}"
)
_SKIP_SECRET_WORDS = {"secret-manager", "secret manager", "secrets must", "no secrets", "secret scanning", "secret-scanner"}


def secret_warnings(text: str) -> list:
    """Heuristic scan for likely secrets in pack content. Returns warnings."""
    if not text:
        return []
    warnings = []
    for line in text.splitlines():
        lower = line.lower()
        if any(skip in lower for skip in _SKIP_SECRET_WORDS):
            continue
        if _SECRET_RE.search(line):
            snippet = line.strip()[:80]
            warnings.append(f"possible secret in content: {snippet!r}")
    return warnings


def _as_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_schema_store(repo_root: Path):
    import json

    schemas = []
    for path in (Path(repo_root) / "packs" / "schemas").rglob("*.json"):
        with open(path, "r", encoding="utf-8") as handle:
            schemas.append(json.load(handle))
    return jsonschema_mini.build_store(schemas)


def _ctx_field_errors(ctx):
    errors = []
    for field in ("id", "version", "title", "description", "source", "authority", "lifecycle", "governance"):
        if field not in ctx:
            errors.append(f"missing required field '{field}'")
    if "id" in ctx and not (isinstance(ctx["id"], str) and CTX_ID_RE.fullmatch(ctx["id"])):
        errors.append("id must be ^[a-zA-Z0-9_-]+$")
    if "version" in ctx and not isinstance(ctx["version"], int):
        errors.append("version must be an integer")
    if "title" in ctx and not (isinstance(ctx["title"], str) and 1 <= len(ctx["title"]) <= 256):
        errors.append("title must be a string of 1-256 chars")
    if "description" in ctx and not (isinstance(ctx["description"], str) and 1 <= len(ctx["description"]) <= 16384):
        errors.append("description must be a string of 1-16384 chars")
    if "source" in ctx:
        st = ctx["source"]
        if not isinstance(st, dict) or "type" not in st or st["type"] not in SOURCE_TYPES:
            errors.append("source.type is missing or invalid")
    if "authority" in ctx:
        auth = ctx["authority"]
        if not isinstance(auth, dict) or "level" not in auth or not isinstance(auth.get("level"), int):
            errors.append("authority.level must be an integer")
        elif auth["level"] < 0 or auth["level"] > 4:
            errors.append("authority.level must be 0-4")
        if not isinstance(auth.get("source"), dict) or not auth["source"].get("id"):
            errors.append("authority.source.id is required")
    if "lifecycle" in ctx and ctx["lifecycle"] not in CONTEXT_LIFECYCLES:
        errors.append(f"lifecycle must be one of {CONTEXT_LIFECYCLES}")
    gov = ctx.get("governance", {})
    if not isinstance(gov, dict) or gov.get("classification") not in GOVERNANCE_CLASSES:
        errors.append(f"governance.classification must be one of {GOVERNANCE_CLASSES}")
    if isinstance(gov, dict) and "approval_required" in gov and not isinstance(gov["approval_required"], bool):
        errors.append("governance.approval_required must be boolean")
    enf = ctx.get("enforcement", {})
    if isinstance(enf, dict) and "mode" in enf and enf["mode"] not in ENFORCEMENT_MODES:
        errors.append(f"enforcement.mode must be one of {ENFORCEMENT_MODES}")
    return errors


def _ctx_semantic_errors(ctx):
    errors = []
    lifecycle = ctx.get("lifecycle")
    review_status = ctx.get("review_status")
    if lifecycle == "candidate" and not review_status:
        errors.append("R1: candidate context requires review_status")
    if lifecycle == "active":
        if not ctx.get("effective_date"):
            errors.append("R1: active context requires effective_date")
        if not ctx.get("enforcement"):
            errors.append("R1: active context requires enforcement")
    if lifecycle == "deprecated" and not ctx.get("deprecated_date"):
        errors.append("R1: deprecated context requires deprecated_date")
    if lifecycle == "archived" and not ctx.get("deprecated_date"):
        errors.append("R1: archived context requires deprecated_date")
    gov = ctx.get("governance", {})
    if str(gov.get("classification", "")).startswith("hardened-") and lifecycle == "active":
        if gov.get("approval_required") is not True:
            errors.append("R3: hardened active context must set approval_required: true")
    eff = ctx.get("effective_date")
    dep = ctx.get("deprecated_date")
    if eff and dep and eff >= dep:
        errors.append("R4: effective_date must be before deprecated_date")
    if lifecycle == "active" and eff and _as_datetime(eff) and _as_datetime(eff) > datetime.now(timezone.utc):
        errors.append("R4: effective_date must be in the past for active context")
    return errors


def context_warnings(ctx):
    warnings = []
    level = ctx.get("authority", {}).get("level", 0)
    lifecycle = ctx.get("lifecycle")
    if level >= 3 and lifecycle == "active":
        mode = ctx.get("enforcement", {}).get("mode")
        if mode != "block":
            warnings.append(
                f"R2: active context with authority level {level} should use block "
                f"enforcement (uses {mode}); justify if intentional"
            )
    return warnings


def context_errors(ctx):
    return _ctx_field_errors(ctx) + _ctx_semantic_errors(ctx)


def _pdk_errors(pack_name, kind, doc, store, check_pack=True):
    errors = []
    if not kind_exists(kind):
        errors.append(f"unknown PKD kind {kind!r}")
        return errors
    schema = store.get(f"https://opencraft.dev/schema/knowledge/{kind}/v1")
    if schema is None:
        errors.append(f"no schema for PKD kind {kind!r}")
        return errors
    path = f"project/{kind}.yaml"
    for error in jsonschema_mini.validate(doc, schema, store=store, path=f"${path}"):
        errors.append(error)
    if check_pack and doc.get("pack") not in (None, pack_name):
        errors.append(f"{path}: pack field {doc.get('pack')!r} does not match {pack_name!r}")
    return errors


def validate_pack(pack, store):
    """Validate a loaded pack dict. Returns (errors, warnings)."""
    errors = []
    warnings = []
    manifest = pack["manifest"]
    name = manifest.get("name")
    if not PACK_NAME_RE.fullmatch(name or ""):
        errors.append("name must be kebab-case and end with '-pack'")
    if not SEMVER_RE.fullmatch(str(manifest.get("version", ""))):
        errors.append(f"version {manifest.get('version')!r} is not strict SemVer")

    schema = store.get("https://opencraft.dev/schema/context-pack/v1")
    if schema is None:
        errors.append("context-pack schema not loaded")
    else:
        for error in jsonschema_mini.validate(manifest, schema, store=store):
            errors.append(error)

    seen_ids = set()
    for ctx in pack["contexts"]:
        cid = ctx.get("id")
        if cid in seen_ids:
            errors.append(f"duplicate context id {cid!r}")
        seen_ids.add(cid)
        for error in context_errors(ctx):
            errors.append(f"context {cid}: {error}")
        for warning in context_warnings(ctx):
            warnings.append(f"context {cid}: {warning}")
        meta = ctx.get("metadata", {})
        if isinstance(meta, dict) and meta.get("pack") not in (None, name):
            errors.append(f"context {cid}: metadata.pack {meta.get('pack')!r} does not match {name!r}")

    provides = manifest.get("provides", {})
    if isinstance(provides, dict):
        for cid in provides.get("contexts", []):
            if cid not in seen_ids:
                errors.append(f"provides.contexts references unknown context {cid!r}")

    for kind, docs in pack["pkds"].items():
        for doc in docs:
            errors.extend(_pdk_errors(name, kind, doc, store))
            for key, value in doc.items():
                if isinstance(value, str):
                    warnings.extend(f"{kind}.{key}: {w}" for w in secret_warnings(value))

    for ctx in pack["contexts"]:
        for field in ("title", "description"):
            value = ctx.get(field)
            if isinstance(value, str):
                warnings.extend(f"context {ctx.get('id')}: {w}" for w in secret_warnings(value))

    if pack.get("ai_prose"):
        warnings.extend(f"ai/AGENTS.md: {w}" for w in secret_warnings(pack["ai_prose"]))

    return errors, warnings


def validate_project(project, store):
    errors = []
    schema = store.get("https://opencraft.dev/schema/project-packs/v1")
    if schema is None:
        return ["project-packs schema not loaded"]
    for error in jsonschema_mini.validate(project, schema, store=store):
        errors.append(error)
    return errors


def validate_effective(merged, ordered, project, store):
    """Validate the merged effective set. Returns (errors, blocking_conflicts)."""
    errors = []
    warnings = []
    for cid, ctx in merged["contexts"].items():
        for error in context_errors(ctx):
            errors.append(f"context {cid}: {error}")
        warnings.extend(f"context {cid}: {w}" for w in context_warnings(ctx))
    for kind, doc in merged["knowledge"].items():
        errors.extend(_pdk_errors("merged", kind, doc, store, check_pack=False))
    blocking = [c for c in merged["report"]["conflicts"] if c["status"] == "blocking-unresolved"]
    for conflict in blocking:
        errors.append(
            f"unresolved hardened conflict for {conflict['id']} "
            f"between {', '.join(conflict['packs'])}; add an explicit override"
        )
    if project.get("conflict_policy") == "fail":
        for conflict in merged["report"]["conflicts"]:
            if conflict["status"] == "pending":
                errors.append(
                    f"conflict for {conflict['id']} between "
                    f"{', '.join(conflict['packs'])} (policy: fail)"
                )
    return errors, blocking
