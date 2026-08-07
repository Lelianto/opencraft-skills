# 0006 — Override Rules

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Overrides are the controlled mechanism by which a child pack or a consumer project modifies inherited content. They are explicit, reason-bearing, and audited — the opposite of silent replacement.

## Override locations

| Location | Precedence | Scope |
|---|---|---|
| Pack manifest `override:` | Medium | Ships with the pack; applies whenever the pack is used. |
| Project `packs.yaml` `overrides:` | Highest | Consumer intent; wins over everything. |

## Actions

| Action | Target | Effect |
|---|---|---|
| `replace` | context, PKD | Swap the inherited record for a local file referenced by `path`. |
| `patch` | context, PKD | Deep-merge field-level changes. Child/project keys win per field. |
| `disable` | context | Remove from the effective set. |
| `defer` | context | Keep, but set `lifecycle: draft` (non-enforcing). |

## Schema

```yaml
overrides:
  - id: ctx-security-scanning        # required
    action: patch                    # replace | patch | disable | defer
    path: local/ctx-custom.yaml      # required for replace
    patch:                           # required for patch (deep-merged)
      severity: critical
      enforcement:
        mode: block
    reason: "..."                    # recommended; required for hardened targets
```

## Merge semantics for `patch`

`patch` performs a recursive deep-merge:

- **Maps:** merged key-by-key; the patch's values win.
- **Lists:** replaced wholesale by the patch's list when present (override of lists is explicit, not union). Use a whole-record `replace` to re-express a list.
- **Scalars:** the patch's value wins.

`patch` never introduces an ordering ambiguity for lists, which is why lists are replaced rather than merged.

## Hardened protection

A context whose `governance.classification` starts with `hardened-`:

- MAY be `patch`ed only when the pack manifest's `governance.approval_required` is satisfied and the change does not weaken enforcement without an explicit reason.
- MUST NOT be `disabled` or `deferred` silently — a `reason` is required, and the override is recorded in `.lcdd/report.json` for audit.
- A `patch` that changes `enforcement.mode` from `block` toward `warn`/`comment` on a hardened context is a MAJOR pack version event.

## Example (project)

```yaml
# packs.yaml
schema: https://opencraft.dev/schema/project-packs/v1
extends:
  - fintech-pack@^1
conflict_policy: fail
overrides:
  - id: ctx-ojk-kyc
    action: replace
    path: project-contexts/kyc.yaml
    reason: Vendor KYC SDK enforces verification upstream.
  - id: ctx-ojk-interest-transparency
    action: disable
    reason: Disclosures handled by compliance contract outside this repo.
```

## Audit trail

Every applied override is recorded in `.lcdd/report.json`:

```json
{
  "overrides_applied": [
    { "id": "ctx-ojk-kyc", "action": "replace", "source": "project", "reason": "..." }
  ]
}
```

## References

- [0005 — Inheritance](0005-inheritance.md)
- [0007 — Conflict Resolution](0007-conflict-resolution.md)
- [0013 — Reference Implementation](0013-reference-implementation.md)
