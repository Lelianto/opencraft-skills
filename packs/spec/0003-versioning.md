# 0003 — Versioning Strategy

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Versioning is the backbone of trust in a context ecosystem. A version identity must be unambiguous, comparable, and carry semantic meaning so that dependents know when an upgrade may break them.

## Pack versions: strict SemVer

Packs use `MAJOR.MINOR.PATCH` (SemVer 2.0.0, no build metadata).

| Bump | Meaning |
|---|---|
| `MAJOR` | Breaking change: a context is removed or its *semantics* change (e.g. a `block` becomes harder, a rule is inverted); a PKD schema changes; an `extends` edge changes in a breaking way. |
| `MINOR` | Additive: new contexts or PKDs, new dependencies, backward-compatible relaxations. |
| `PATCH` | Corrections: typo, provenance fix, enforcement config detail that does not change the rule's meaning. |

### What counts as a breaking context change

A context is semantically identical when its enforced meaning is unchanged. In particular, changing any of these in a `hardened-*` context is a MAJOR event:

- `title` / `description` normative meaning
- `applies_to` scope
- `enforcement.mode` (block → warn is breaking; warn → block is breaking)
- `authority.level`
- `lifecycle` (active → deprecated)

## Context versions

Within a pack, each context has a monotonic integer `version` per the LCDD Context Schema. The pack's `MAJOR` version must bump when any context version is removed or replaced with changed semantics.

## Dependency ranges

References use SemVer ranges:

| Range | Meaning |
|---|---|
| `nextjs-pack` | Any version (warn on install). |
| `nextjs-pack@1` | Any `1.x`. |
| `nextjs-pack@^1.2.0` | `>=1.2.0 <2.0.0`. |
| `nextjs-pack@~1.2.0` | `>=1.2.0 <1.3.0`. |
| `nextjs-pack@>=2 <3` | Explicit interval. |

Resolution picks the **highest** version satisfying the range from the registry (semver preference), then pins it.

## Immutability

- A published version is immutable. If content must change, publish a new version.
- The registry serves each `name@version` as a fixed snapshot with a recorded integrity hash.

## Lockfiles

Two lockfile roles:

| Lockfile | Scope | Purpose |
|---|---|---|
| `packs.lock.json` (repo root) | OpenCraft source | Pins the canonical built-in pack tree for authoring/CI. |
| `.lcdd/packs.lock.json` | Consumer project | Pins the resolved graph + integrity so installs are reproducible. |

Both use `sha256` over every file in the pack.

## Pack lifecycle vs version

Lifecycle and version are orthogonal axes:

- A pack can be `1.2.0` and `deprecated`.
- `deprecated` packs warn on install and MUST declare `superseded_by`.
- `archived` packs cannot be installed.

## References

- [0004 — Dependency System](0004-dependency-system.md)
- [0009 — Registry](0009-registry.md)
- [0008 — Validation](0008-validation.md)
