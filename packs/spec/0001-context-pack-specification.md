# 0001 — Context Pack Specification

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

A Context Pack is a versioned, distributable bundle of LCDD Contexts and Project Knowledge Documents that installs production-ready project context into any project. This document is the normative definition of what a pack is, what it contains, and the guarantees it makes. It is the top-level RFC; every other RFC refines one aspect.

## The pack as a unit of governance

LCDD establishes two artifacts: the **Context** (atomic governance unit) and the **Registry** (versioned store). Context Packs complete the picture by defining a **composable distribution unit**. A pack is to governance what a package is to code:

- **Reusable** — install the same conventions across many projects.
- **Versioned** — SemVer with an immutable release per version.
- **Composable** — `extends` builds richer packs from base packs.
- **Accountable** — every context carries authority, ownership, and lifecycle.
- **Verifiable** — validated on authoring and on install; integrity-pinned.

## What a pack provides

When installed, a pack automatically contributes the following to the project's living context (the `provides` matrix):

| Concern | Form | Where |
|---|---|---|
| Project vision | PKD `vision` | `.lcdd/project/vision.yaml` |
| Architecture decisions | PKD `architecture` + contexts | `.lcdd/project/architecture.yaml` |
| Coding conventions | PKD `conventions` + contexts | `.lcdd/project/conventions.yaml` |
| Folder structure | PKD `folder-structure` | `.lcdd/project/folder-structure.yaml` |
| Technology stack | PKD `tech-stack` | `.lcdd/project/tech-stack.yaml` |
| Security rules | PKD `security` + contexts | `.lcdd/project/security.yaml` |
| Testing strategy | PKD `testing` | `.lcdd/project/testing.yaml` |
| Business constraints | PKD `business-constraints` | `.lcdd/project/business-constraints.yaml` |
| AI coding rules | PKD `ai-rules` + `ai/AGENTS.md` | `.lcdd/ai/AGENTS.md` |
| Review checklist | PKD `review-checklist` | `.lcdd/project/review-checklist.yaml` |
| Deployment guidelines | PKD `deployment` | `.lcdd/project/deployment.yaml` |
| Observability practices | PKD `observability` | `.lcdd/project/observability.yaml` |
| Lifecycle metadata | PKD `lifecycle` | `.lcdd/project/lifecycle.yaml` |
| Ownership metadata | PKD `ownership` | `.lcdd/project/ownership.yaml` |
| Enforceable constraints | LCDD Contexts | `.lcdd/contexts/<id>.yaml` |

The materialized `.lcdd/` directory is the **effective project context**: a git-backed LCDD Context Registry plus the merged Project Knowledge base.

## Pack types

Packs are classified by `type` to make the ecosystem navigable:

| Type | Purpose | Examples |
|---|---|---|
| `technology` | Language / runtime baseline | typescript-pack, node-pack |
| `framework` | Application framework | react-pack, nextjs-pack |
| `baas` | Backend-as-a-service | supabase-pack, firebase-pack |
| `cross-cutting` | Concern spanning all projects | security-pack, testing-pack, accessibility-pack |
| `domain` | Industry / domain constraints | fintech-pack, healthcare-pack, ecommerce-pack, education-pack |

`extends` is expected across types: a `domain` pack typically extends `cross-cutting` and `technology` packs.

## Lifecycle

Packs follow the LCDD lifecycle: `draft → candidate → approved → active → deprecated → archived`.

- Only `active` packs are installable by default.
- `deprecated` packs warn on install; `archived` packs are not installable.
- Lifecycle transitions are recorded; a pack's `lifecycle` reflects its current stage.

## Guarantees

1. **Determinism** — same `packs.yaml` + same registry state → byte-identical `.lcdd/` (except timestamps).
2. **Validation on both ends** — packs are validated at authoring time (CI) and at install time.
3. **Integrity** — every resolved file is verified against `packs.lock.json` sha256 hashes.
4. **No silent resolution of hardened conflicts** — hardened contexts always require explicit resolution.
5. **Zero-key, zero-dependency, offline-capable** — the engine is pure local computation.

## References

- [0002 — Manifest](0002-manifest.md)
- [0005 — Inheritance](0005-inheritance.md)
- [0007 — Conflict Resolution](0007-conflict-resolution.md)
- LCDD 0012 — Context Schema
- LCDD 0005 — Context Registry
