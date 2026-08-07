# 0014 — Examples

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

The repository ships thirteen reference packs that exercise the full specification: inheritance chains, dependency graphs, override actions, and cross-type composition. They are real, installable living context — not placeholders.

## The packs

### Technology baselines

| Pack | Extends | Focus |
|---|---|---|
| `typescript-pack` | — | TS strictness, typing conventions, tsconfig, lint/format. |
| `node-pack` | — | Node runtime versioning, module discipline, process/stream hygiene. |

### Frameworks

| Pack | Extends | Focus |
|---|---|---|
| `react-pack` | `typescript-pack` | Component conventions, hooks, state, keying, a11y basics. |
| `nextjs-pack` | `react-pack`, `typescript-pack` | App Router, data fetching, server actions, folder structure. |

### Backend-as-a-service

| Pack | Extends | Focus |
|---|---|---|
| `supabase-pack` | `typescript-pack`, `security-pack` | Row-level security, migrations, realtime, auth. |
| `firebase-pack` | `typescript-pack`, `security-pack` | Security rules, Firestore modeling, functions, auth. |

### Cross-cutting

| Pack | Extends | Focus |
|---|---|---|
| `security-pack` | `typescript-pack` | Input validation, authn/authz, secrets, OWASP ASVS, dependency hygiene. |
| `testing-pack` | `typescript-pack` | Test pyramid, risk-based selection, coverage gates, fixtures. |
| `accessibility-pack` | `typescript-pack` | WCAG 2.2 AA, keyboard, semantics, contrast, motion. |

### Domain

| Pack | Extends | Focus |
|---|---|---|
| `fintech-pack` | `node-pack`, `security-pack`, `testing-pack` | Regulatory framing (OJK-style), audit, transparency, data residency. |
| `healthcare-pack` | `node-pack`, `security-pack`, `accessibility-pack` | PHI handling, audit, consent, availability. |
| `ecommerce-pack` | `node-pack`, `security-pack`, `testing-pack` | Cart/payment flows, inventory, tax, abuse. |
| `education-pack` | `node-pack`, `accessibility-pack`, `testing-pack` | Learner privacy, content integrity, offline/scale. |

## Inheritance and composition exercised

```
typescript-pack (technology)
└── react-pack (framework)
    └── nextjs-pack (framework)
        └── (project) security-pack, fintech-pack

security-pack  ─┐
testing-pack   ─┴─► fintech-pack / ecommerce-pack (domain)
node-pack ──────┘

security-pack, accessibility-pack, testing-pack ──► healthcare-pack, education-pack
```

Domain packs override cross-cutting defaults with `override` entries (e.g. fintech `patch`es security contexts to `block` severity, healthcare `disable`s generic caching guidance), demonstrating RFC 0006.

## Authoring workflow

```bash
# Scaffold a pack
opencraft packs create my-pack --type domain --dir packs/

# Validate the whole tree
python3 scripts/packtool.py packs validate --all

# Regenerate + verify the integrity lock
python3 scripts/generate_pack_lock.py
python3 scripts/generate_pack_lock.py --check
```

## Working example

The quickest end-to-end proof:

```bash
project="$(mktemp -d)"
cat > "$project/packs.yaml" <<'YAML'
schema: https://opencraft.dev/schema/project-packs/v1
extends:
  - nextjs-pack@^1
  - security-pack@^2
  - fintech-pack@^1
conflict_policy: fail
YAML
python3 scripts/packtool.py packs install --project "$project"
node scripts/packtool.mjs packs install --project "$project"
ls -R "$project/.lcdd"
```

Both CLIs produce identical `.lcdd/` output (parity requirement).

## Reference

- [packs/](../../packs) — the canonical pack sources.
- [packs/registry/index.json](../../packs/registry/index.json) — the catalog.
- [pack-contract.md](../contracts/pack-contract.md) — content contract.
