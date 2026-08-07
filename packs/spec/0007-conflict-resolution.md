# 0007 — Conflict Resolution

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

LCDD's tenth principle: *conflicting contexts must be resolved, not hidden.* This RFC defines exactly what a conflict is, when silent resolution is allowed, and how the engine surfaces unresolved conflicts for human judgment.

## What is a conflict

A **conflict** is two different definitions of the same context `id` at the **same precedence level** — i.e. neither one inherits from the other.

```
project extends: [pack-a, pack-b]
pack-a defines ctx-http-security
pack-b defines ctx-http-security   # conflict (siblings)
```

By contrast, a child overriding an ancestor's same `id` is **not** a conflict; it is inheritance (RFC 0005).

PKD conflicts follow the same rule by `kind`: two sibling packs defining the same `kind` with differing scalars/keys conflict.

## Policies

Set `conflict_policy` in project `packs.yaml` (default `fail`).

| Policy | Behavior |
|---|---|
| `fail` | Installation fails; a conflict report lists every conflict with the two sources and a diff hint. |
| `highest-precedence-wins` | For ties, the later entry in `extends` wins; the loser is recorded as a "superseded" note in the report. |
| `keep-first` | The earlier entry wins. |
| `human` | Installation stops at the first conflict; the user must add an explicit `override` or choose via HITL. |

## Hardened contexts are never silent

Regardless of policy, a conflict involving a `hardened-*` context (either side) **always** stops with an explicit resolution requirement:

- The user MUST add an explicit `override` entry (RFC 0006) OR
- Run `opencraft packs install --resolve <id> <pack-name>` to record an explicit, audited choice.

No policy auto-resolves hardened conflicts. This is a hard guarantee, not a preference.

## Diff hints

Each conflict report includes a structural diff between the two definitions (added/removed/changed fields at JSON-pointer granularity) so a human can decide quickly.

## Report

All conflict outcomes — resolved, superseded, or blocking — are written to `.lcdd/report.json`:

```json
{
  "conflicts": [
    {
      "id": "ctx-http-security",
      "kind": "context",
      "packs": ["pack-a", "pack-b"],
      "policy": "fail",
      "status": "blocking",
      "diff_hint": "authority.level: 3 vs 4; enforcement.mode: warn vs block"
    }
  ]
}
```

## Ordering of resolution steps

1. Apply natural inheritance (precedence order).
2. Detect same-precedence conflicts.
3. Apply pack-manifest `override` entries.
4. Apply project `overrides`.
5. Evaluate hardened guarantee; stop if unresolved.
6. Apply `conflict_policy` to remaining non-hardened conflicts.
7. Validate the effective set; write report.

## References

- [0006 — Override Rules](0006-override-rules.md)
- [0008 — Validation](0008-validation.md)
- [0010 — CLI](0010-cli.md)
- LCDD 0001 — Core Principles (principle 10)
