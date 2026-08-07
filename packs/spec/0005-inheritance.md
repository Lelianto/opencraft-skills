# 0005 — Inheritance (extends)

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

`extends` is inheritance for living context. A pack built on another pack inherits its contexts and Project Knowledge, and can narrow, deepen, or replace them — always in a deterministic, auditable way.

## Precedence model

Precedence is a total ordering over the resolved pack set. Lower precedence = more general; higher precedence = more specific. In conflicts the higher-precedence definition wins.

```
project extends:  [base-pack, app-pack]        # app-pack > base-pack
app-pack extends: [react-pack, typescript-pack]
react-pack extends: [typescript-pack]           # shared parent
```

Precedence: `typescript-pack (parent) < react-pack (parent) < base-pack (root@0) < app-pack (root@1)`.

Assignment rule: root entry `i` → `i`; parent → `min(child) - 1`.

## What is inherited

- Every **context** from every ancestor (by `id`).
- Every **PKD** from every ancestor (by `kind`).
- The **dependency set** (union, resolved transitively).

## What is NOT inherited

- `version`, `name`, `owner`, `license`, `description` of the parent (each pack declares its own).
- `lifecycle` of the parent — a deprecated parent does not deprecate the child, though it warns on install.

## Overriding inherited content

A child overrides an inherited context by defining the same `id` in its own `contexts/`. Natural override semantics:

| Case | Behavior |
|---|---|
| Child defines same `id`, no `override` entry | Whole-record replacement (child wins). |
| Child adds `override: patch` for that `id` | Field-level deep-merge; child fields win per key. |
| Child adds `override: disable` for that `id` | Context removed from the effective set. |
| Child adds `override: defer` for that `id` | Context kept but demoted to `lifecycle: draft` (non-enforcing). |

`override` entries may live in the **pack manifest** (author intent, ships with the pack) or in the **project `packs.yaml`** (consumer intent, highest precedence).

## Example

```yaml
# fintech-pack/pack.yaml
name: fintech-pack
version: 1.0.0
extends:
  - security-pack@^1
  - testing-pack@^1
override:
  - id: ctx-security-scanning
    action: patch
    patch:
      severity: critical
      enforcement:
        mode: block
  - id: ctx-testing-coverage-gate
    action: defer
    reason: Coverage gate relaxed during migration; re-enable in Q3.
```

## Rules

1. A pack MUST NOT extend itself, directly or transitively (cycle → error).
2. Overriding a `hardened-*` context with different semantics requires `approval_required` in the pack governance and is a MAJOR version event.
3. `disable`/`defer` on a hardened context require an explicit reason; the reason is preserved in the merge report.
4. Every effective context records its origin pack in `metadata.pack`; overridden records keep a `metadata.overridden_from` trail.

## References

- [0004 — Dependency System](0004-dependency-system.md)
- [0006 — Override Rules](0006-override-rules.md)
- [0007 — Conflict Resolution](0007-conflict-resolution.md)
