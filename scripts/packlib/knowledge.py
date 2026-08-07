"""Project Knowledge Document (PKD) kinds and merge semantics."""

from __future__ import annotations

__all__ = ["KNOWLEDGE_KINDS", "LIST_KEY", "merge_docs", "kind_exists"]

KNOWLEDGE_KINDS = [
    "vision",
    "architecture",
    "conventions",
    "folder-structure",
    "tech-stack",
    "security",
    "testing",
    "business-constraints",
    "ai-rules",
    "review-checklist",
    "deployment",
    "observability",
    "lifecycle",
    "ownership",
]

# Per-kind, per-field list identity keys. None means dedupe by whole item.
LIST_KEY = {
    "vision": {"principles": "id", "success_signals": None, "non_goals": None, "target_users": None},
    "architecture": {"patterns": "id", "decisions": "id"},
    "conventions": {
        "naming": "id",
        "formatting": "id",
        "imports": "id",
        "state": "id",
        "structure": "id",
    },
    "folder-structure": {"directories": "path", "files": "path"},
    "tech-stack": {"entries": "name"},
    "security": {
        "standards": "name",
        "rules": "id",
        "sensitive_data": None,
        "trust_boundaries": None,
        "references": None,
    },
    "testing": {"tools": None, "gates": "name", "fixtures": None},
    "business-constraints": {"constraints": "id", "compliance": "name", "kpis": None},
    "ai-rules": {"rules": "id"},
    "review-checklist": {"categories": "name"},
    "deployment": {"environments": "name", "rollout": None, "smoke_tests": None, "rollback": None},
    "observability": {"metrics": "name", "logs": None, "traces": None, "alerts": "name", "slos": "name", "dashboards": None},
    "lifecycle": {"transitions": "to"},
    "ownership": {"areas": "name", "contexts": "id"},
}


def _append_or_replace(target, item, idkey):
    if idkey and isinstance(item, dict) and idkey in item:
        for index, existing in enumerate(target):
            if isinstance(existing, dict) and existing.get(idkey) == item[idkey]:
                target[index] = item
                return
        target.append(item)
        return
    if item not in target:
        target.append(item)


def _deep_merge(left, right):
    for key, value in right.items():
        if key in left and isinstance(left[key], dict) and isinstance(value, dict):
            _deep_merge(left[key], value)
        else:
            left[key] = value
    return left


def _merge_doc(acc, doc, kind):
    lk = LIST_KEY.get(kind, {})
    for key, value in doc.items():
        if key == "kind":
            continue
        if key == "pack":
            acc[key] = value
            continue
        if isinstance(value, list):
            if key not in acc or not isinstance(acc[key], list):
                acc[key] = []
            for item in value:
                _append_or_replace(acc[key], item, lk.get(key))
        elif isinstance(value, dict):
            if key not in acc or not isinstance(acc[key], dict):
                acc[key] = {}
            _deep_merge(acc[key], value)
        else:
            acc[key] = value
    return acc


def merge_docs(kind, docs):
    """Merge PKD docs of one kind in precedence order (low to high)."""
    acc = {"kind": kind, "pack": None}
    for doc in docs:
        if doc is None:
            continue
        _merge_doc(acc, doc, kind)
    return acc


def kind_exists(kind: str) -> bool:
    return kind in KNOWLEDGE_KINDS
