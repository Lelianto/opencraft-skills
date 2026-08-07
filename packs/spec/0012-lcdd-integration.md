# 0012 — LCDD Integration

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Context Packs are the composability layer of Living Context Driven Development (LCDD), formalized by [living-context-driven-development](https://github.com/Lelianto/living-context-driven-development). This RFC defines the exact points of integration so that a project installed with Context Packs is natively an LCDD-governed project.

## The LCDD principles realized

| LCDD principle | Realized by |
|---|---|
| 1. Context is a first-class artifact | Contexts are LCDD Context Schema records. |
| 2. Contexts are discovered, not assumed | Resolution + registry discovery. |
| 3. Every context has provenance | `source`, `authority`, `metadata.pack`. |
| 4. Contexts have a lifecycle | Pack + context lifecycles mirror LCDD stages. |
| 5. Governance matches rate of change | `governance.classification` per LCDD. |
| 6. Sources heterogeneous, model unified | Any pack contributes to one context model. |
| 7. AI agents consume and respect contexts | `CONTEXT.md` + optional MCP (RFC 0011). |
| 8. Enforcement is pluggable | `@lcdd/cli` and CI can enforce `.lcdd/`. |
| 9. Observability closes the loop | `packs doctor` + LCDD observability. |
| 10. Conflicts resolved, not hidden | RFC 0007 conflict policy + reports. |
| 11. Contexts are composable | **Context Packs — this specification.** |
| 12. The methodology applies to itself | The pack ecosystem is governed by packs. |

## Integration points

### `.lcdd/` is an LCDD Context Registry

The materialized `.lcdd/contexts/` directory is a git-backed LCDD Context Registry (Reference Architecture Topology 1). Each `*.yaml` is a valid LCDD Context record.

```text
.lcdd/
├── contexts/             # LCDD Context records (one file per id)
├── project/              # PKD knowledge base (LCDD complements)
├── CONTEXT.md            # agent-facing summary
└── packs.lock.json
```

### Interoperability with `@lcdd/cli` and `@lcdd/mcp`

`@lcdd/cli` and `@lcdd/mcp` operate on `.lcdd/` unchanged. They are **optional enhancements**, never prerequisites:

```bash
# Optional — once a team adopts LCDD tooling:
lcd validate          # enforces .lcdd/contexts/ in CI
lcd doctor            # context health over the same store
```

The OpenCraft engine never depends on them; it performs resolution, merging, validation, and materialization itself.

### Context schema compliance

Every context satisfies the LCDD Context Schema (v0.1.0) plus semantic rules R1–R5, enforced by the shared validation engine (RFC 0008). Future LCDD schema versions are tracked via the `schema` URL.

### Lifecycle mapping

```
pack.yaml lifecycle:        draft → candidate → approved → active → deprecated → archived
LCDD context lifecycle:     draft → candidate → approved → active → deprecated → archived
```

Pack lifecycle governs installability; context lifecycle governs enforceability.

### Governance model

`governance.classification` uses the exact LCDD set:

| Classification | Authority | AI can modify? | Default enforcement |
|---|---|---|---|
| `hardened-mandate` | 4 | No | block |
| `hardened-standard` | 3 | No | block |
| `hardened-local` | 2 | Suggest | warn |
| `local-standard` | 2 | With review | warn |
| `local-guideline` | 1 | Auto-merge | comment |
| `local-experimental` | 0 | Yes | silent |

## Enforcement

- **Authoring:** packs are validated in CI; broken packs cannot publish.
- **Install:** projects validate on every materialization.
- **Runtime:** teams may add `lcd validate` / CI hooks; `packs doctor` flags drift.
- **Hardened guarantee:** hardened contexts cannot be silently weakened at any point.

## Relationship to the OpenCraft `.product/` layer

OpenCraft Skills also maintains a durable intent/evidence layer (`.product/`: PRD, decisions, threat models, release evidence). Context Packs govern *how* work is done; `.product/` records *what* was decided and verified. They are complementary:

- Packs → `.lcdd/` (governance, conventions, AI rules).
- Skills + `.product/` (delivery, traceability, evidence).

## References

- LCDD Repository: https://github.com/Lelianto/living-context-driven-development
- LCDD 0012 — Context Schema
- LCDD 0005 — Context Registry
- LCDD 0015 — Reference Architecture
- [0005 — Inheritance](0005-inheritance.md)
- [0007 — Conflict Resolution](0007-conflict-resolution.md)
