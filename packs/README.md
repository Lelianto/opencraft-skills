# OpenCraft Context Packs

### *Install living project context instead of rewriting it.*

**Context decays.** Your README says PostgreSQL 14; you run 16. Your architecture decisions live in a Slack thread from March. Your compliance requirements changed in June. AI agents keep coding against stale assumptions. Context Packs fix this: they package production-ready **Living Context** — conventions, security rules, testing strategy, AI coding rules, and more — that installs into any project, stays versioned and enforced, and is consumed directly by your AI agents.

Context Packs are the **composability layer** of **Living Context Driven Development (LCDD)**. The methodology is defined in the reference repository:

> **[github.com/Lelianto/living-context-driven-development](https://github.com/Lelianto/living-context-driven-development)**

LCDD treats context as a first-class artifact — versioned, governed, enforced, and evolved. Context Packs make that context *reusable*: one line in `packs.yaml` installs a whole project's worth of governance.

---

## Table of Contents

- [■ The Problem](#the-problem)
- [◈ What is a Context Pack?](#what-is-a-context-pack)
- [◆ The Pack — Content and Format](#the-pack--content-and-format)
- [▶ The Fourteen Concerns](#the-fourteen-concerns)
- [↻ Precedence and Inheritance](#precedence-and-inheritance)
- [◉ Overrides and Conflicts](#overrides-and-conflicts)
- [☰ Quick Start](#quick-start)
- [▤ CLI Reference](#cli-reference)
- [⊞ The Reference Packs](#the-reference-packs)
- [◈ Validation](#validation)
- [→ Registry and Versioning](#registry-and-versioning)
- [✈ AI Integration](#ai-integration)
- [⇔ LCDD Integration](#lcdd-integration)
- [※ Core Philosophy](#core-philosophy)
- [☗ Roadmap](#roadmap)
- [✎ Contributing](#contributing)
- [⚖ License](#license)

---

## The Problem

**Documentation dies. Specifications drift. Knowledge changes. Yet AI keeps coding as if nothing happened.**

Every README, every architecture decision, every compliance document, every coding standard — all of it becomes outdated the moment it is written. The consequences:

### 1. Context Debt

Your codebase has Technical Debt. Your knowledge base has Context Debt. The Postgres version you document is not the one you run. The regulation you cite was amended last month. **Nobody measures this debt. Nobody pays it down.** Every decision made against stale context becomes a liability.

### 2. Specification Drift

AI agents optimize for "all tests pass." When context is absent or outdated, they fill the gap — rewriting tests, relaxing schemas, removing validation. The specification silently drifts to match the code, not the other way around.

> The LCDD repository ([living-context-driven-development](https://github.com/Lelianto/living-context-driven-development)) names this problem precisely and defines the artifact model that fixes it. Context Packs are that model made installable.

## What is a Context Pack?

A **Context Pack** is a versioned, distributable bundle of:

- **LCDD Contexts** — the atomic governance units (structured, enforceable rules).
- **Project Knowledge Documents (PKDs)** — typed, mergeable knowledge (vision, stack, conventions, testing, deployment, observability…).
- **AI coding rules** — structured rules rendered into an agent-consumable `AGENTS.md`.

A pack is to governance what a package is to code:

- **Reusable** — install the same conventions across many projects.
- **Versioned** — SemVer with immutable releases.
- **Composable** — `extends` builds richer packs from base packs.
- **Accountable** — every context carries authority, ownership, and lifecycle.
- **Verifiable** — validated on authoring and on install; integrity-pinned.

```yaml
# packs.yaml  (project root)
extends:
  - nextjs-pack
  - security-pack
  - fintech-pack
```

## The Pack — Content and Format

```text
nextjs-pack/
├── pack.yaml               # manifest: name, version, extends, governance, ownership
├── README.md               # human documentation
├── contexts/               # LCDD Context records (one YAML per enforceable rule)
├── project/                # Project Knowledge Documents (14 typed kinds)
├── ai/AGENTS.md            # optional agent prose fragment
├── evals/cases.yaml        # discovery/validation fixtures
└── LICENSE
```

### The manifest

```yaml
schema: https://opencraft.dev/schema/context-pack/v1
name: nextjs-pack
version: 1.0.0
type: framework
description: Living context for Next.js App Router applications
license: MIT
extends:
  - react-pack@^1
  - typescript-pack@^1
dependencies:
  - node-pack@^1
lifecycle: active
governance:
  classification: local-standard
  approval_required: false
owner:
  type: organization
  id: opencraft-web
  name: OpenCraft Web
```

### A context (LCDD Context Schema record)

```yaml
id: ctx-nextjs-server-actions
version: 1
title: Mutations must be Server Actions with server-side validation and authorization
description: >
  Mutations MUST run in Server Actions or route handlers with server-side
  validation, authorization, and cache revalidation.
category: security
severity: critical
authority:
  source: { type: organization, id: opencraft, name: OpenCraft }
  level: 3
lifecycle: active
governance:
  classification: hardened-standard
  approval_required: true
enforcement:
  mode: block
metadata:
  pack: nextjs-pack
```

## The Fourteen Concerns

Every pack automatically contributes to the project's living context (the `provides` matrix):

| # | Concern | Where it lands |
|---|---|---|
| 1 | Project vision | `.lcdd/project/vision.yaml` |
| 2 | Architecture decisions | `.lcdd/project/architecture.yaml` + contexts |
| 3 | Coding conventions | `.lcdd/project/conventions.yaml` + contexts |
| 4 | Folder structure | `.lcdd/project/folder-structure.yaml` |
| 5 | Technology stack | `.lcdd/project/tech-stack.yaml` |
| 6 | Security rules | `.lcdd/project/security.yaml` + contexts |
| 7 | Testing strategy | `.lcdd/project/testing.yaml` |
| 8 | Business constraints | `.lcdd/project/business-constraints.yaml` |
| 9 | AI coding rules | `.lcdd/ai/AGENTS.md` |
| 10 | Code review checklist | `.lcdd/project/review-checklist.yaml` |
| 11 | Deployment guidelines | `.lcdd/project/deployment.yaml` |
| 12 | Observability practices | `.lcdd/project/observability.yaml` |
| 13 | Lifecycle metadata | `.lcdd/project/lifecycle.yaml` |
| 14 | Ownership metadata | `.lcdd/project/ownership.yaml` |

Each PKD has a JSON Schema (`packs/schemas/knowledge/`) and merge semantics (lists dedupe by identity key, maps deep-merge, scalars highest-precedence wins).

## Precedence and Inheritance

`extends` is inheritance for living context. Every pack in a resolved graph gets a deterministic **precedence**:

- Project `extends` entries are ordered — **later entries bind tighter**.
- A pack's `extends` parents have **lower precedence** than the pack itself.
- Shared parents in a diamond resolve to the lowest precedence that keeps them below all children.
- Project `overrides` bind tighter than anything.

```
project extends:  [base-pack, app-pack]        # app-pack > base-pack
app-pack extends: [react-pack, typescript-pack]
react-pack extends: [typescript-pack]
```

A child overrides an inherited context by defining the same `id`; the higher-precedence definition wins. `patch` deep-merges fields instead of replacing wholesale.

## Overrides and Conflicts

### Override actions

| Action | Effect |
|---|---|
| `replace` | Swap a context with a local file. |
| `patch` | Deep-merge field-level changes. |
| `disable` | Remove from the effective set. |
| `defer` | Keep but mark non-enforcing (`lifecycle: draft`). |
| `resolve` | Explicitly choose which pack wins (audited). |

### Conflict policy

A conflict is two definitions of the same context `id` at the same precedence level. Policies (project `conflict_policy`, default `fail`): `fail`, `highest-precedence-wins`, `keep-first`, `human`.

**Hardened contexts** (`governance.classification` starting with `hardened-`) are never silently resolved — they always require an explicit override or a human decision. Conflicts, overrides, and resolutions are all recorded in `.lcdd/report.json`.

## Quick Start

No API keys. No cloud account. No `@lcdd/cli` required. Python 3.10+ or Node.js 18+.

```bash
# Init a project pack declaration
python3 scripts/packtool.py packs init --project .

# Declare packs
python3 scripts/packtool.py packs add nextjs-pack --project .
python3 scripts/packtool.py packs add security-pack --project .
python3 scripts/packtool.py packs add fintech-pack --project .

# Resolve, merge, validate, materialize
python3 scripts/packtool.py packs install --project .
```

The Node CLI is behaviorally identical:

```bash
node scripts/packtool.mjs packs install --project .
```

Result:

```text
.lcdd/
├── contexts/           # LCDD Context Registry
├── project/            # merged Project Knowledge
├── ai/AGENTS.md        # merged AI coding rules
├── CONTEXT.md          # generated living-context summary
├── packs.lock.json     # resolved versions + integrity
└── report.json         # merge/conflict/override report
```

The whole engine runs locally: the 13 reference packs ship with the repository, so the demo above works **with no network**.

## CLI Reference

| Command | Description |
|---|---|
| `packs init` | Create `packs.yaml` + `.lcdd/` skeleton. |
| `packs add <name[@range]>` | Declare a pack. |
| `packs remove <name>` | Remove a declared pack. |
| `packs install` | Resolve, merge, validate, materialize into `.lcdd/`. |
| `packs update` | Re-resolve ranges and re-materialize. |
| `packs list` | List declared packs and available versions. |
| `packs status` | Show effective contexts and knowledge. |
| `packs doctor` | Context Health report over `.lcdd/`. |
| `packs resolve --dry-run` | Show the resolved graph, precedence, and conflicts. |
| `packs validate [name\|--all]` | Validate pack(s). |
| `packs verify` | Integrity-check `packs.lock.json`. |
| `packs lock` | Regenerate the lockfile. |
| `packs create <name>` | Scaffold a new pack. |
| `packs publish <name>` | Prepare a pack for publication. |

Options: `--project <dir>` (default `.`), `--json`, `--force`, `--dry-run`.

## The Reference Packs

| Pack | Type | Extends | Focus |
|---|---|---|---|
| `typescript-pack` | technology | — | Strict typing, tsconfig, lint, path aliases. |
| `node-pack` | technology | — | Runtime versioning, ESM, process hygiene. |
| `react-pack` | framework | typescript-pack | Components, hooks, state, keys. |
| `nextjs-pack` | framework | react-pack + typescript-pack | App Router, data fetching, Server Actions. |
| `supabase-pack` | baas | typescript-pack + security-pack | RLS, migrations, realtime. |
| `firebase-pack` | baas | typescript-pack + security-pack | Security rules, Firestore modeling, functions. |
| `security-pack` | cross-cutting | — | Input validation, authz, secrets, dependency hygiene. |
| `testing-pack` | cross-cutting | — | Risk-proportional testing, CI gates. |
| `accessibility-pack` | cross-cutting | — | WCAG 2.2 AA, keyboard, labels. |
| `fintech-pack` | domain | node + security + testing | KYC, audit, data residency, disclosure. |
| `healthcare-pack` | domain | node + security + accessibility | PHI, consent, audit. |
| `ecommerce-pack` | domain | node + security + testing | Checkout, inventory, abuse. |
| `education-pack` | domain | node + accessibility + testing | Learner privacy, content integrity, availability. |

Domain packs demonstrate inheritance and overrides: `fintech-pack` patches `ctx-security-dependency-hygiene` to `critical`; `healthcare-pack` patches accessibility to `critical`; `ecommerce-pack` promotes the testing gate to `block`.

## Validation

Every pack and every materialized project passes four layers:

1. **JSON Schema** — manifest, project declaration, lockfile, and each PKD kind.
2. **LCDD Context Schema** — required fields, enums, authority levels.
3. **Semantic rules** — LCDD R1–R5 (lifecycle consistency, authority–enforcement, governance–lifecycle, temporal, supersedes) plus pack rules (name, SemVer, unique context IDs, provenance, resolvable graph, acyclic).
4. **Integrity** — `packs.lock.json` sha256 pinning.

```bash
python3 scripts/packtool.py packs validate --all
python3 scripts/generate_pack_lock.py --check
python3 scripts/packlib_test.py        # engine unit tests
python3 scripts/security_test.py       # path traversal, YAML DoS, secret scan
python3 scripts/pack-bench.py          # performance benchmark (fail on regression)
```

## Registry and Versioning

- **Packs use strict SemVer.** `MAJOR` breaks compatibility, `MINOR` adds, `PATCH` fixes.
- **Dependencies use SemVer ranges** (`^1`, `~1.2.0`, `>=2 <3`); resolution picks the highest satisfying version and pins it.
- **Distribution** is npm-scoped (`@opencraft/<name>`) with recorded sha256 integrity; the catalog lives at `packs/registry/index.json`.
- **Resolution order:** local cache → built-in `packs/` tree → remote transport.

## AI Integration

The filesystem is the interface — no API key, no network, works with every agent:

- Agents read `.lcdd/CONTEXT.md` (concise living-context summary).
- Machine-readable governance lives in `.lcdd/contexts/*.yaml` and `.lcdd/project/*.yaml`.
- Merged AI coding rules land in `.lcdd/ai/AGENTS.md` (structured `must`/`should`/`must-not` rules, rendered for the agent window).

An optional MCP server can expose structured querying for MCP-capable agents (Claude Desktop, Cursor, Cline). Hardened contexts are immutable to AI; the engine's `packs doctor` flags drift.

## LCDD Integration

Context Packs are the **composability layer** of Living Context Driven Development, defined at:

> **[https://github.com/Lelianto/living-context-driven-development](https://github.com/Lelianto/living-context-driven-development)**

| LCDD principle | Realized by Context Packs |
|---|---|
| 1. Context is a first-class artifact | Contexts are LCDD Context Schema records. |
| 3. Every context has provenance | `source`, `authority`, `metadata.pack`. |
| 4. Contexts have a lifecycle | Pack + context lifecycles mirror LCDD stages. |
| 5. Governance matches rate of change | `governance.classification` per LCDD. |
| 9. Observability closes the loop | `packs doctor` + LCDD observability. |
| 10. Conflicts resolved, not hidden | Explicit policy + audited reports. |
| 11. Contexts are composable | **Context Packs.** |
| 12. The methodology applies to itself | The ecosystem is governed by packs. |

- `.lcdd/contexts/` is a **git-backed LCDD Context Registry** (Reference Architecture Topology 1).
- `@lcdd/cli` and `@lcdd/mcp` operate on `.lcdd/` unchanged — **optional enhancements, never prerequisites**.
- Contexts satisfy the LCDD Context Schema and validation rules R1–R5.

## Core Philosophy

1. **Context is the bottleneck.** In the age of AI-assisted development, constraint governance matters more than code production.
2. **Reusable beats rewritten.** Project knowledge that is generic should be installed, versioned, and shared — not re-authored per project.
3. **Machine-readable first.** If an AI agent cannot consume a rule, it will be ignored at scale.
4. **Explicit beats implicit.** Provenance, authority, ownership, and lifecycle are declared, never assumed.
5. **Deterministic and local.** No API keys, no cloud mandate, no `@lcdd/cli` prerequisite — the reference engine is pure local computation.

## Roadmap

| Milestone | Status | Focus |
|---|---|---|
| Specification + schemas | ✅ | 14 RFCs, JSON Schemas, pack contract. |
| Reference engine | ✅ | Zero-dependency Python + Node CLIs, 23 unit tests. |
| Reference packs | ✅ | 13 installable packs exercising inheritance/overrides. |
| Registry + publishing | 🟡 | Catalog + npm transport; automated publish via CI Trusted Publishing. |
| MCP server | 🔴 | Structured querying for MCP-capable agents. |
| Community ecosystem | 🔴 | Contribution SDK, maturity levels, compatibility matrix. |

## Contributing

Contributions of all kinds are welcome:

- **New packs** — scaffold with `packs create <name>`, validate with `packs validate --all`, add evals.
- **RFCs** — challenge or extend `packs/spec/`.
- **Engine** — extend `scripts/packlib/` (Python) and keep `scripts/packtool.mjs` behaviorally equivalent.
- **Docs** — clarity fixes and examples.

## Acknowledgements

Context Packs are the **building-block implementation** of **Living Context Driven Development (LCDD)**, the governing methodology defined at:

> **[github.com/Lelianto/living-context-driven-development](https://github.com/Lelianto/living-context-driven-development)**

LCDD establishes the Context Schema, Context Registry, lifecycle, governance-by-rate-of-change, and the composability principle this module makes installable. Acknowledgements also to the Agent Skills specification ([agentskills.io](https://agentskills.io/specification)), OWASP (ASVS/AISVS), and the wider constraint-driven-development literature that informs the governance model.

## License

The Context Pack Specification is Apache-2.0 (matching LCDD); individual packs carry their own licenses; this module's code and examples are MIT.
