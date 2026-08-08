"""Context Health report — parity with LCDD 0.5.0 `lcd doctor`.

Reimplements the eight metrics and scoring used by `@lcdd/core` (doctor.js,
trigger-evaluator.js) so `packs doctor` and `lcd doctor` report the same
format, scores, and grades over the same `.lcdd/` registry:

  1. Stale Contexts            (max 15)
  2. Missing Owners            (max 15)
  3. Enforcement Conflicts     (max 10)
  4. Deprecation Backlog       (max 10)
  5. Draft Stagnation          (max 10)
  6. Authority Gaps            (max 10)
  7. Tag Hygiene               (max 10)
  8. Review Backlog            (max 20)

The trigger evaluator is also ported so `triggers` and `dormant_triggers`
match `lcd doctor --triggers`.
"""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["compute_health", "days_since", "patterns_overlap"]

STALE_DAYS = 90
FALSE_POSITIVE_RATE = 0.2
HIGH_VIOLATION_RATE = 0.2
AI_DRIFT_RATIO = 2.0
MIN_EVENTS_FOR_RATE = 10
MIN_EVENTS_FOR_DRIFT = 20
MIN_EVENTS_PER_ACTOR = 5
MIN_EVENTS_FOR_TREND = 6
CONFIDENCE_THRESHOLD = 0.7

DAYS_STALE_THRESHOLD = 90
DEPRECATION_STALE_DAYS = 180
DRAFT_STALL_DAYS = 30


def days_since(date_str):
    """Days elapsed since an ISO timestamp. Returns Infinity when absent."""
    if not date_str:
        return float("inf")
    try:
        ms = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return float("inf")
    now = datetime.now(timezone.utc)
    if ms.tzinfo is None:
        ms = ms.replace(tzinfo=timezone.utc)
    return (now - ms).total_seconds() / 86400.0


def patterns_overlap(a, b):
    """Mirror @lcdd/core doctor.patternsOverlap exactly."""
    if a == "**/*" or b == "**/*":
        return True
    import re

    strip = lambda p: re.sub(r"/?\*\*?/?\*?$", "", p)
    a_dir = strip(a)
    b_dir = strip(b)
    return a_dir.startswith(b_dir) or b_dir.startswith(a_dir)


def _read_jsonl(path):
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        import json

        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def _recommendation_id(trigger, context_id=None):
    scope = context_id or "registry"
    return f"rec-{trigger.lower().replace('_', '-')}-{scope}"


class _TriggerEvaluator:
    def events_for(self, context_id, enforcements):
        return [e for e in enforcements if e.get("context_id") == context_id]

    def evaluate(self, contexts, enforcements, dismissals=None):
        dismissals = dismissals or []
        recommendations = []
        recommendations.extend(self.stale_no_violation(contexts, enforcements))
        recommendations.extend(self.high_violation_rate(contexts, enforcements))
        recommendations.extend(self.increasing_violations(contexts, enforcements))
        recommendations.extend(self.ai_drift(enforcements))
        recommendations.extend(self.new_source_detected(contexts))
        dormant = []
        if len(dismissals) == 0:
            dormant.append(
                {
                    "trigger": "HIGH_FALSE_POSITIVE",
                    "reason": (
                        "No dismissal events recorded. False positive rate requires dismissals/violations; "
                        "violation rate is reported separately as HIGH_VIOLATION_RATE."
                    ),
                }
            )
        else:
            recommendations.extend(self.high_false_positive(contexts, enforcements, dismissals))
        return {
            "triggers_fired": len({r["trigger"] for r in recommendations}),
            "recommendations": recommendations,
            "dormant": dormant,
        }

    def stale_no_violation(self, contexts, enforcements):
        recs = []
        for ctx in contexts:
            if ctx.get("lifecycle") != "active":
                continue
            recent = [e for e in self.events_for(ctx.get("id"), enforcements)
                      if days_since(e.get("timestamp")) <= STALE_DAYS]
            if not recent:
                continue
            if any(e.get("status") == "violation" for e in recent):
                continue
            recs.append(self._rec("STALE_NO_VIOLATION", ctx, "short-term", "medium", "deprecate",
                "Active context with no recent violations",
                f'"{ctx.get("title")}" has been active with no violations in the last {STALE_DAYS} days across {len(recent)} check(s).',
                f"Zero violations in {STALE_DAYS} days suggests the rule is either universally followed or no longer relevant.",
                0.75 if len(recent) >= MIN_EVENTS_FOR_RATE else 0.5,
                {"lifecycle": "deprecated"}))
        return recs

    def high_violation_rate(self, contexts, enforcements):
        recs = []
        for ctx in contexts:
            if ctx.get("lifecycle") == "archived":
                continue
            events = self.events_for(ctx.get("id"), enforcements)
            if len(events) < MIN_EVENTS_FOR_RATE:
                continue
            violations = [e for e in events if e.get("status") == "violation"]
            rate = len(violations) / len(events)
            if rate <= HIGH_VIOLATION_RATE:
                continue
            recs.append(self._rec("HIGH_VIOLATION_RATE", ctx, "short-term", "high", "refine-scope",
                "High violation rate",
                f'"{ctx.get("title")}" has a {rate * 100:.0f}% violation rate ({len(violations)}/{len(events)}).',
                "A sustained high violation rate means either the rule is too broadly scoped or the codebase genuinely does not comply. Narrowing scope is the safe first response.",
                0.6, None))
        return recs

    def high_false_positive(self, contexts, enforcements, dismissals):
        recs = []
        for ctx in contexts:
            if ctx.get("lifecycle") == "archived":
                continue
            violations = [e for e in self.events_for(ctx.get("id"), enforcements)
                          if e.get("status") == "violation"]
            if len(violations) < MIN_EVENTS_FOR_RATE:
                continue
            dismissed = [d for d in dismissals if d.get("context_id") == ctx.get("id")]
            rate = len(dismissed) / len(violations)
            if rate <= FALSE_POSITIVE_RATE:
                continue
            recs.append(self._rec("HIGH_FALSE_POSITIVE", ctx, "immediate", "high", "refine-scope",
                "High false positive rate",
                f'"{ctx.get("title")}" has a {rate * 100:.0f}% false positive rate ({len(dismissed)} dismissed of {len(violations)} violations).',
                "Developers are dismissing this rule as inapplicable more than one time in five. The scope is wrong, not the codebase.",
                min(0.9, 0.6 + rate), None))
        return recs

    def increasing_violations(self, contexts, enforcements):
        recs = []
        for ctx in contexts:
            if ctx.get("lifecycle") == "archived":
                continue
            events = sorted(self.events_for(ctx.get("id"), enforcements),
                            key=lambda e: e.get("timestamp", ""), reverse=True)
            if len(events) < MIN_EVENTS_FOR_TREND:
                continue
            window = MIN_EVENTS_FOR_TREND // 2
            recent = [e for e in events[:window] if e.get("status") == "violation"]
            earlier = [e for e in events[window:window * 2] if e.get("status") == "violation"]
            if len(recent) <= len(earlier):
                continue
            recs.append(self._rec("INCREASING_VIOLATIONS", ctx, "immediate", "medium", "review-clarity",
                "Increasing violation trend",
                f'"{ctx.get("title")}" violations rose from {len(earlier)}/{window} to {len(recent)}/{window} in the most recent checks.',
                "A rising trend usually means the rule is being misunderstood or the codebase is drifting away from it. Both need a human to read the wording.",
                0.5, None))
        return recs

    def ai_drift(self, enforcements):
        if len(enforcements) < MIN_EVENTS_FOR_DRIFT:
            return []
        human = [e for e in enforcements if (e.get("actor") or {}).get("type") == "human"]
        ai = [e for e in enforcements if (e.get("actor") or {}).get("type") == "ai-agent"]
        if len(human) < MIN_EVENTS_PER_ACTOR or len(ai) < MIN_EVENTS_PER_ACTOR:
            return []
        human_rate = len([e for e in human if e.get("status") == "violation"]) / len(human)
        ai_rate = len([e for e in ai if e.get("status") == "violation"]) / len(ai)
        if human_rate <= 0 or ai_rate / human_rate <= AI_DRIFT_RATIO:
            return []
        return [self._rec("AI_DRIFT", None, "immediate", "critical", "review-clarity",
            "AI specification drift detected",
            f"AI agent violation rate ({ai_rate * 100:.0f}%) is {ai_rate / human_rate:.1f}x the human rate ({human_rate * 100:.0f}%).",
            "AI agents violate rules at a materially higher rate than humans, which points to ambiguous context wording or inadequate prompt injection rather than agent malice.",
            0.65, None)]

    def new_source_detected(self, contexts):
        recs = []
        for ctx in contexts:
            source = ctx.get("source") or {}
            if source.get("type") != "unknown" or ctx.get("lifecycle") == "archived":
                continue
            if not source.get("uri"):
                continue
            recs.append(self._rec("NEW_SOURCE_DETECTED", ctx, "long-term", "low", "register-source",
                "Unregistered external source",
                f'"{ctx.get("title")}" references "{source.get("uri")}" but that source is not registered for change detection.',
                "An unregistered source cannot be watched, so changes upstream will not be noticed.",
                0.8, None))
        return recs

    def _rec(self, trigger, ctx, priority, severity, action, title, description, reason, confidence, proposed):
        return {
            "recommendation_id": _recommendation_id(trigger, (ctx or {}).get("id")),
            "trigger": trigger,
            "priority": priority,
            "severity": severity,
            "action": action,
            "context_id": (ctx or {}).get("id"),
            "title": title,
            "description": description,
            "reason": reason,
            "confidence": confidence,
            "auto_apply": False,
            "proposed_change": proposed,
            "suggested_command": f"lcd review show {(ctx or {}).get('id')}",
        }


def _to_trigger_result(rec):
    return {
        "trigger": rec["trigger"],
        "severity": rec["severity"],
        "context_id": rec["context_id"],
        "description": rec["description"],
        "recommendation": rec["suggested_command"] + f" — {rec['reason']}" if rec.get("suggested_command") else rec["reason"],
    }


def compute_health(contexts, report=None, lcdd_dir=None):
    """Compute the Context Health report. `contexts` is a dict {id: ctx}.

    Returns a dict mirroring `lcd doctor --json`:
    overall_score, max_score, grade, timestamp, total_contexts, metrics,
    recommendations, triggers, dormant_triggers.
    """
    report = report or {}
    events = _read_jsonl((lcdd_dir / "contexts" / ".events.log")) if lcdd_dir else []
    enforcements = _read_jsonl((lcdd_dir / "contexts" / ".enforcements.log")) if lcdd_dir else []
    dismissals = _read_jsonl((lcdd_dir / "contexts" / ".dismissals.log")) if lcdd_dir else []

    ctx_list = list(contexts.values())
    metrics = []
    recommendations = []
    evaluator = _TriggerEvaluator()

    def activity_events():
        return [e for e in events if (e.get("actor_role") or "") != "improve-engine"]

    # 1. Stale Contexts
    stale_ids = []
    activity = activity_events()
    for ctx in ctx_list:
        if ctx.get("lifecycle") in ("archived", "draft"):
            continue
        ctx_events = sorted(
            [e for e in activity if e.get("context_id") == ctx.get("id")],
            key=lambda e: e.get("timestamp", ""), reverse=True,
        )
        last_date = ctx_events[0]["timestamp"] if ctx_events else (ctx.get("updated_at") or ctx.get("created_at"))
        if days_since(last_date) > DAYS_STALE_THRESHOLD:
            stale_ids.append(ctx.get("id"))
    if len(stale_ids) == 0:
        stale_score, stale_status = 15, "ok"
    elif len(stale_ids) <= 2:
        stale_score, stale_status = 10, "warning" if len(stale_ids) <= 3 else "warning"
    elif len(stale_ids) <= 5:
        stale_score, stale_status = 5, "critical"
    else:
        stale_score, stale_status = 0, "critical"
    metrics.append({
        "name": "Stale Contexts", "score": stale_score, "max_score": 15, "status": stale_status,
        "details": ["All active contexts have recent activity."] if not stale_ids
            else [f"{len(stale_ids)} context(s) with no activity in {DAYS_STALE_THRESHOLD}+ days: {', '.join(stale_ids)}"],
    })

    # 2. Missing Owners
    missing_owners = [c.get("id") for c in ctx_list if not c.get("owner") and c.get("lifecycle") != "archived"]
    if len(missing_owners) == 0:
        mo_score, mo_status = 15, "ok"
    elif len(missing_owners) <= 2:
        mo_score, mo_status = 10, "warning"
    elif len(missing_owners) <= 5:
        mo_score, mo_status = 5, "critical"
    else:
        mo_score, mo_status = 0, "critical"
    metrics.append({
        "name": "Missing Owners", "score": mo_score, "max_score": 15, "status": mo_status,
        "details": ["All non-archived contexts have assigned owners."] if not missing_owners
            else [f"{len(missing_owners)} context(s) without owner: {', '.join(missing_owners)}"],
    })

    # 3. Enforcement Conflicts
    enforceable = [c for c in ctx_list if c.get("lifecycle") in ("active", "approved", "deprecated")]
    conflicts = []
    for i in range(len(enforceable)):
        for j in range(i + 1, len(enforceable)):
            a, b = enforceable[i], enforceable[j]
            a_patterns = a.get("applies_to") or ["**/*"]
            b_patterns = b.get("applies_to") or ["**/*"]
            overlap = any(patterns_overlap(ap, bp) for ap in a_patterns for bp in b_patterns)
            if overlap and (a.get("enforcement") or {}).get("mode") == "block" and (b.get("enforcement") or {}).get("mode") == "block":
                pair = sorted([a.get("id"), b.get("id")])
                conflicts.append(f"{pair[0]} ↔ {pair[1]}")
    conflicts = list(dict.fromkeys(conflicts))
    conflicts.sort()
    if len(conflicts) == 0:
        ec_score, ec_status = 10, "ok"
    elif len(conflicts) <= 2:
        ec_score, ec_status = 5, "warning"
    else:
        ec_score, ec_status = 0, "warning"
    metrics.append({
        "name": "Enforcement Conflicts", "score": ec_score, "max_score": 10, "status": ec_status,
        "details": ["No overlapping enforcement conflicts detected."] if not conflicts
            else [f"{len(conflicts)} potential enforcement overlap(s): {', '.join(conflicts)}"],
    })

    # 4. Deprecation Backlog
    deprecated = [c for c in ctx_list if c.get("lifecycle") == "deprecated"]
    old_deprecated = [c for c in deprecated if days_since(c.get("deprecated_date")) > DEPRECATION_STALE_DAYS]
    if not deprecated:
        db_score, db_status = 10, "ok"
    elif not old_deprecated:
        db_score, db_status = 5, "warning"
    else:
        db_score, db_status = 0, "critical"
    db_details = ["No deprecated contexts — backlog clean."] if not deprecated else (
        [f"{len(deprecated)} deprecated context(s), {len(old_deprecated)} stale >{DEPRECATION_STALE_DAYS} days: {', '.join(c.get('id') for c in old_deprecated)}"]
        if old_deprecated else [f"{len(deprecated)} deprecated context(s) pending archive: {', '.join(c.get('id') for c in deprecated)}"])
    metrics.append({"name": "Deprecation Backlog", "score": db_score, "max_score": 10, "status": db_status, "details": db_details})

    # 5. Draft Stagnation
    drafts = [c for c in ctx_list if c.get("lifecycle") == "draft"]
    stalled = []
    for c in drafts:
        last = sorted([e for e in activity if e.get("context_id") == c.get("id")],
                      key=lambda e: e.get("timestamp", ""), reverse=True)
        base = last[0]["timestamp"] if last else (c.get("updated_at") or c.get("created_at"))
        if days_since(base) > DRAFT_STALL_DAYS:
            stalled.append(c.get("id"))
    if not drafts:
        ds_score, ds_status = 10, "ok"
    elif not stalled:
        ds_score, ds_status = 7, "ok"
    elif len(stalled) <= 3:
        ds_score, ds_status = 3, "warning"
    else:
        ds_score, ds_status = 0, "critical"
    ds_details = (["No draft contexts."] if not drafts else
                  (["{} draft context(s) — all within {} day threshold.".format(len(drafts), DRAFT_STALL_DAYS)] if not stalled
                   else [f"{len(stalled)} draft context(s) stalled >{DRAFT_STALL_DAYS} days: {', '.join(stalled)}"]))
    metrics.append({"name": "Draft Stagnation", "score": ds_score, "max_score": 10, "status": ds_status, "details": ds_details})

    # 6. Authority Gaps
    weak = [c for c in ctx_list if (c.get("authority") or {}).get("level") == 0 and c.get("lifecycle") not in ("archived", "draft")]
    moderate = [c for c in ctx_list if (c.get("authority") or {}).get("level") == 1 and c.get("lifecycle") not in ("archived", "draft")]
    if not weak and not moderate:
        ag_score, ag_status = 10, "ok"
    elif not weak:
        ag_score, ag_status = 7, "ok" if len(moderate) <= 2 else "warning"
    elif len(weak) <= 2:
        ag_score, ag_status = 4, "critical"
    else:
        ag_score, ag_status = 0, "critical"
    ag_details = ["All non-archived contexts have sufficient authority levels."] if (not weak and not moderate) else (
        [f"{len(weak)} context(s) with authority level 0 (weakest): {', '.join(c.get('id') for c in weak)}"]
        if weak else [f"{len(moderate)} context(s) with authority level 1: {', '.join(c.get('id') for c in moderate)}"])
    metrics.append({"name": "Authority Gaps", "score": ag_score, "max_score": 10, "status": ag_status, "details": ag_details})

    # 7. Tag Hygiene
    untagged = [c.get("id") for c in ctx_list
                if (not c.get("tags") or len(c.get("tags") or []) == 0) and c.get("lifecycle") != "archived"]
    if not untagged:
        th_score, th_status = 10, "ok"
    elif len(untagged) <= 3:
        th_score, th_status = 6, "warning"
    elif len(untagged) <= 8:
        th_score, th_status = 3, "critical"
    else:
        th_score, th_status = 0, "critical"
    metrics.append({
        "name": "Tag Hygiene", "score": th_score, "max_score": 10, "status": th_status,
        "details": ["All non-archived contexts are tagged."] if not untagged
            else [f"{len(untagged)} context(s) without tags: {', '.join(untagged)}"],
    })

    # 8. Review Backlog
    pending = [c.get("id") for c in ctx_list if c.get("review_status") in ("pending", "in-review", "needs-revision")]
    if not pending:
        rb_score, rb_status = 20, "ok"
    elif len(pending) <= 3:
        rb_score, rb_status = 12, "warning"
    elif len(pending) <= 7:
        rb_score, rb_status = 6, "critical"
    else:
        rb_score, rb_status = 0, "critical"
    metrics.append({
        "name": "Review Backlog", "score": rb_score, "max_score": 20, "status": rb_status,
        "details": ["No contexts pending review."] if not pending
            else [f"{len(pending)} context(s) awaiting review: {', '.join(pending)}"],
    })

    # Unresolved pack conflicts surface as an OpenCraft-specific recommendation.
    unresolved = [c["id"] for c in report.get("conflicts", []) if c.get("status") == "blocking-unresolved"]

    for m in metrics:
        if m["status"] in ("warning", "critical"):
            recommendations.extend(m["details"])
    if unresolved:
        recommendations.append(f"{len(unresolved)} unresolved hardened conflict(s): {', '.join(unresolved)}")

    evaluation = evaluator.evaluate(ctx_list, enforcements, dismissals)
    triggers = [_to_trigger_result(r) for r in evaluation["recommendations"]]
    for t in triggers:
        recommendations.append(f"[{t['trigger']}] {t['recommendation']}")

    total_score = sum(m["score"] for m in metrics)
    max_score = sum(m["max_score"] for m in metrics)
    ratio = total_score / max_score if max_score else 1.0
    grade = "A" if ratio >= 0.9 else "B" if ratio >= 0.75 else "C" if ratio >= 0.6 else "D" if ratio >= 0.4 else "F"

    return {
        "overall_score": total_score,
        "max_score": max_score,
        "grade": grade,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "total_contexts": len(ctx_list),
        "metrics": metrics,
        "recommendations": list(dict.fromkeys(recommendations)),
        "triggers": triggers,
        "dormant_triggers": evaluation["dormant"],
        "unresolved_conflicts": unresolved,
    }
