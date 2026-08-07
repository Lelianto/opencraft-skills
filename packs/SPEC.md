# Context Pack Specification

**Status:** Candidate  
**Version:** 1.0.0  
**Specification:** OpenCraft Skills — Context Packs  
**Last Updated:** 2026-08-07

---

## Abstract

A **Context Pack** is a versioned, distributable bundle of Living Contexts and Project Knowledge that can be installed into any project to establish production-ready governance, conventions, and AI coding rules. Context Packs are the composability layer of Living Context Driven Development (LCDD): they let teams and communities share governance context the same way packages share code.

This specification defines the pack format, manifest, versioning, dependency system, inheritance, override rules, conflict resolution, validation, registry, CLI, AI integration, and LCDD integration. It is the canonical normative document; each numbered RFC in `spec/` deepens one area.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **Context Pack** | A versioned bundle of LCDD Contexts and Project Knowledge Documents. |
| **Pack Manifest** | `pack.yaml`, the machine-readable declaration of a pack. |
| **Context** | An atomic governance unit conforming to the LCDD Context Schema. |
| **PKD** | Project Knowledge Document; a typed, mergeable YAML artifact (vision, tech-stack, …). |
| **Project Declaration** | `packs.yaml` in a project root: the `extends` list and overrides. |
| **Resolution** | Computing the concrete, ordered set of packs from `extends` + dependencies. |
| **Materialization** | Writing the resolved, merged, validated context to `.lcdd/`. |
| **Registry** | A catalog + transport for discovering and fetching packs. |

## 2. Design goals

1. **Installable living context** — one line in `packs.yaml` installs production context.
2. **Deterministic** — the same declaration always resolves to the same effective context.
3. **Machine-readable first** — every rule is structured, queryable, and enforceable.
4. **Composable** — packs extend and depend on other packs; the graph is a DAG.
5. **Provable** — every pack and every merged context is validated and integrity-pinned.
6. **Agent-aware** — AI coding rules and living context are materialized for agents to consume.
7. **Self-hostable, offline, key-free** — no API keys, no cloud mandate, no `@lcdd/cli` prerequisite.

## 3. The pack

```yaml
# pack.yaml
schema: https://opencraft.dev/schema/context-pack/v1
name: nextjs-pack
version: 1.0.0
type: framework
description: Living context for Next.js App Router applications
license: MIT
author:
  type: organization
  id: opencraft
  name: OpenCraft
tags: [nextjs, react, web, app-router]
extends:
  - react-pack@^1
  - typescript-pack@^1
dependencies:
  - node-pack@^20
lifecycle: active
governance:
  classification: local-standard
  approval_required: false
owner:
  type: organization
  id: opencraft-web
  name: OpenCraft Web
```

```text
nextjs-pack/
├── pack.yaml               # manifest
├── README.md               # human documentation
├── contexts/               # LCDD Context records
│   ├── ctx-nextjs-app-router.yaml
│   └── ctx-nextjs-data-fetching.yaml
├── project/                # Project Knowledge Documents
│   ├── tech-stack.yaml
│   ├── conventions.yaml
│   ├── architecture.yaml
│   └── ai-rules.yaml
├── ai/AGENTS.md            # optional agent prose fragment
├── evals/cases.yaml        # validation fixtures
└── LICENSE                 # pack license
```

## 4. Core semantics

### 4.1 Precedence

Every pack in a resolved graph gets a numeric precedence. Later declarations bind tighter:

- Project `extends` entries are ordered; **later entries have higher precedence**.
- A pack's own `extends` parents have **lower precedence** than the pack itself.
- Shared parents in a diamond resolve to the lowest precedence that keeps them below all children.
- Project-local `overrides` in `packs.yaml` have the **highest** precedence.

### 4.2 Merge

- **Contexts** merge by `id`. When two packs define the same context `id`, the higher-precedence record replaces the lower by default; `patch` actions deep-merge fields instead.
- **PKDs** merge by `kind` within `project/`. Lists concatenate and dedupe by a stable key (`id` or `name`); maps deep-merge; scalars are taken from the higher-precedence pack.

### 4.3 Override actions

`override:` in a pack manifest or project declaration applies one of:

| Action | Effect |
|---|---|
| `replace` | Swap a context (or PKD) with a local file. |
| `patch` | Deep-merge field-level overrides into the inherited record. |
| `disable` | Remove the context from the effective set. |
| `defer` | Keep the record but mark it non-enforcing (`lifecycle: draft`). |

### 4.4 Conflict policy

A **conflict** is two different definitions of the same context `id` at the **same precedence level**. Policies (from project `conflict_policy`, default `fail`):

| Policy | Behavior |
|---|---|
| `fail` | Installation fails with a conflict report. |
| `highest-precedence-wins` | Later entries in `extends` win. |
| `keep-first` | Earlier entries win. |
| `human` | Installation stops; an explicit human decision is required. |

**Hardened contexts** (`governance.classification` starts with `hardened-`) can never be silently resolved — they always require an explicit `override` or a human decision.

## 5. Versioning

- Packs use strict **SemVer** `MAJOR.MINOR.PATCH`. `MAJOR` breaks compatibility, `MINOR` adds, `PATCH` fixes.
- Contexts use a monotonic **integer version** per LCDD Context Schema.
- Dependency references use SemVer ranges (`^1.2`, `~1.2.0`, `>=2 <3`).
- A resolved graph is pinned by `.lcdd/packs.lock.json` with integrity hashes.

## 6. Registry

- Packs distribute as scoped npm packages: `@opencraft/<name>`.
- `packs/registry/index.json` is the catalog mapping `name → versions → npm package, integrity, requires`.
- The resolver prefers the local cache, then the built-in `packs/` tree, then the remote registry (with sha256 verification).

## 7. Validation

Every pack and every materialized project passes:

1. **JSON Schema** — manifest, project declaration, lockfile, and each PKD kind.
2. **LCDD Context Schema** — every context in `contexts/`.
3. **Semantic rules** — lifecycle consistency, acyclic dependency graph, satisfiable ranges, unique context IDs, provenance (`metadata.pack`).
4. **Integrity** — `packs.lock.json` sha256 pinning.

## 8. AI integration

Materialization produces `.lcdd/CONTEXT.md` (a concise living-context summary), `.lcdd/contexts/` (machine-readable governance), and `.lcdd/ai/AGENTS.md` (AI coding rules). Agents read these directly from the filesystem; an optional MCP server exposes query and validation tools. No API key is involved.

## 9. LCDD integration

- Contexts are LCDD Context Schema records; `.lcdd/contexts/` is an LCDD git-backed registry (Topology 1).
- Pack lifecycle mirrors the LCDD lifecycle: `draft → candidate → approved → active → deprecated → archived`.
- `@lcdd/cli` and `@lcdd/mcp` can operate on the materialized `.lcdd/` unchanged — they are optional enhancements, not prerequisites.

## 10. Normative reading order

1. [0001 — Context Pack Specification](spec/0001-context-pack-specification.md)
2. [0002 — Manifest](spec/0002-manifest.md)
3. [0003 — Versioning](spec/0003-versioning.md)
4. [0004 — Dependency System](spec/0004-dependency-system.md)
5. [0005 — Inheritance](spec/0005-inheritance.md)
6. [0006 — Override Rules](spec/0006-override-rules.md)
7. [0007 — Conflict Resolution](spec/0007-conflict-resolution.md)
8. [0008 — Validation](spec/0008-validation.md)
9. [0009 — Registry](spec/0009-registry.md)
10. [0010 — CLI](spec/0010-cli.md)
11. [0011 — AI Integration](spec/0011-ai-integration.md)
12. [0012 — LCDD Integration](spec/0012-lcdd-integration.md)
13. [0013 — Reference Implementation](spec/0013-reference-implementation.md)
14. [0014 — Examples](spec/0014-examples.md)

---

## License

Apache-2.0 (matching LCDD) for the specification; individual packs carry their own licenses.
