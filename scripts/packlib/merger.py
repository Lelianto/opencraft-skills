"""Precedence merge of contexts and Project Knowledge Documents, with overrides
and conflict resolution."""

from __future__ import annotations

from .knowledge import merge_docs

__all__ = ["merge"]


def _deep_merge(left, right):
    for key, value in right.items():
        if key in left and isinstance(left[key], dict) and isinstance(value, dict):
            _deep_merge(left[key], value)
        else:
            left[key] = value
    return left


def _diff_hint(a, b):
    hints = []
    for key in ("authority", "enforcement", "severity", "lifecycle"):
        va = a.get(key)
        vb = b.get(key)
        if va != vb:
            hints.append(f"{key}: {va!r} vs {vb!r}")
    return "; ".join(hints) or "content differs"


def _classification(ctx):
    return str(ctx.get("governance", {}).get("classification", ""))


def _is_hardened(ctx):
    return _classification(ctx).startswith("hardened-")


def merge(ordered, project, replace_map=None):
    """Merge resolved packs (low to high precedence) into an effective context.

    Returns ``{'contexts': {id: ctx}, 'knowledge': {kind: doc},
    'ai_rules': [rule, ...], 'report': {...}}``.
    """
    replace_map = replace_map or {}
    policy = project.get("conflict_policy", "fail")
    project_overrides = list(project.get("overrides", []))
    project_override_ids = {ov.get("id") for ov in project_overrides}

    # ---- contexts ---------------------------------------------------------
    by_id = {}
    order = []
    for item in ordered:
        prec, name = item["precedence"], item["name"]
        for ctx in item["pack"]["contexts"]:
            cid = ctx.get("id")
            if not cid:
                continue
            if cid not in by_id:
                by_id[cid] = []
                order.append(cid)
            by_id[cid].append((prec, name, ctx))

    effective = {}
    conflicts = []
    overrides_applied = []
    disabled = []
    deferred = []

    # Overrides gathered from every resolved pack (by precedence) plus the project.
    pack_overrides = []
    for item in sorted(ordered, key=lambda o: o["precedence"]):
        for ov in item["pack"]["manifest"].get("override", []):
            pack_overrides.append((item["precedence"], item["name"], ov))

    for cid in order:
        entries = sorted(by_id[cid], key=lambda e: e[0])
        max_prec = entries[-1][0]
        top = [e for e in entries if e[0] == max_prec]
        winner_ctx = dict(top[0][2])
        origin = top[0][1]
        hardened = any(_is_hardened(e[2]) for e in top)
        conflict_status = None

        if len(top) > 1:
            conflict_status = "blocking" if hardened else "pending"
            conflicts.append(
                {
                    "id": cid,
                    "kind": "context",
                    "packs": sorted(e[1] for e in top),
                    "policy": policy,
                    "hardened": hardened,
                    "status": conflict_status,
                    "diff_hint": _diff_hint(top[0][2], top[-1][2]),
                }
            )

        # Apply overrides in precedence order; project overrides bind last.
        def apply_override(ov, source):
            nonlocal winner_ctx
            action = ov.get("action")
            record = {"id": cid, "action": action, "source": source, "reason": ov.get("reason")}
            if action == "disable":
                disabled.append(record)
                winner_ctx = None
            elif action == "defer":
                winner_ctx["lifecycle"] = "draft"
                deferred.append(record)
            elif action == "patch":
                _deep_merge(winner_ctx, ov.get("patch", {}))
                overrides_applied.append(record)
            elif action == "replace":
                if cid in replace_map:
                    winner_ctx = dict(replace_map[cid])
                    overrides_applied.append(record)
                else:
                    conflicts.append(
                        {
                            "id": cid,
                            "kind": "context",
                            "packs": [origin],
                            "policy": policy,
                            "hardened": hardened,
                            "status": "blocking",
                            "diff_hint": f"override replace missing source for {cid}",
                        }
                    )
            elif action == "resolve":
                chosen = ov.get("pack")
                match = next((e[2] for e in entries if e[1] == chosen), None) if chosen else None
                if match is not None:
                    winner_ctx = dict(match)
                    overrides_applied.append(record)
                else:
                    conflicts.append(
                        {
                            "id": cid,
                            "kind": "context",
                            "packs": [origin],
                            "policy": policy,
                            "hardened": hardened,
                            "status": "blocking",
                            "diff_hint": f"resolve override references unknown pack {chosen!r}",
                        }
                    )

        for prec, pack_name, ov in pack_overrides:
            if ov.get("id") == cid:
                apply_override(ov, f"pack:{pack_name}")
        for ov in project_overrides:
            if ov.get("id") == cid:
                apply_override(ov, "project")

        if winner_ctx is not None:
            effective[cid] = winner_ctx
        if conflict_status == "blocking" and cid not in project_override_ids:
            conflicts[-1]["status"] = "blocking-unresolved"

    # ---- knowledge --------------------------------------------------------
    knowledge = {}
    for item in ordered:
        for kind, docs in item["pack"]["pkds"].items():
            knowledge.setdefault(kind, []).append(docs)
    merged_knowledge = {}
    for kind, doc_groups in knowledge.items():
        docs = []
        for group in doc_groups:
            docs.extend(group)
        docs.sort(key=lambda d: 0)
        merged_knowledge[kind] = merge_docs(kind, docs)

    # ---- ai rules ---------------------------------------------------------
    ai_rules = []
    ai_doc = merged_knowledge.get("ai-rules")
    if ai_doc and isinstance(ai_doc.get("rules"), list):
        ai_rules = list(ai_doc["rules"])

    report = {
        "conflicts": conflicts,
        "overrides_applied": overrides_applied,
        "disabled": disabled,
        "deferred": deferred,
    }
    return {
        "contexts": effective,
        "knowledge": merged_knowledge,
        "ai_rules": ai_rules,
        "report": report,
    }
