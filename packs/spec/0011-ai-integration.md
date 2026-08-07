# 0011 — AI Integration

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Context Packs exist so AI coding agents code *against* current, enforced project context instead of stale assumptions. Integration is filesystem-first (no API key, no network, works with every agent) with an optional MCP server for structured querying.

## What agents consume

Materialization writes an agent-consumable surface under `.lcdd/`:

| File | Purpose |
|---|---|
| `CONTEXT.md` | Concise living-context summary: vision, stack, conventions, active contexts, AI rules, pointers. |
| `contexts/*.yaml` | Machine-readable LCDD governance, queryable and enforceable. |
| `project/*.yaml` | Structured knowledge (tech-stack, conventions, testing, deployment…). |
| `ai/AGENTS.md` | Merged AI coding rules fragment. |
| `packs.lock.json` | Version + integrity state. |

Agents that read `AGENTS.md`/`CLAUDE.md` are pointed at `.lcdd/CONTEXT.md` by the project template, so rules become part of the agent's working instructions.

## Filesystem-first flow

```
agent prompt ──► reads AGENTS.md ──► sees: "read .lcdd/CONTEXT.md"
                                  ──► reads contexts/, project/ as needed
                                  ──► obeys enforced rules; queries locally
```

No tooling, no credentials, no API key. Any agent that can read the repository benefits.

## AI coding rules

`project/ai-rules.yaml` is the structured, mergeable source of AI rules:

```yaml
kind: ai-rules
pack: nextjs-pack
rules:
  - id: ai-route-handlers
    level: must
    instruction: Prefer route handlers over API routes; colocate with app router segments.
    rationale: App Router is the supported model in Next.js 15.
```

Rules merge by precedence across packs. `ai/AGENTS.md` prose fragments append with attribution. `.lcdd/ai/AGENTS.md` is the rendered, final fragment.

## Optional MCP server

An optional `@opencraft/mcp` server exposes structured tools for MCP-capable agents (Claude Desktop, Cursor, Cline):

| Tool | Behavior |
|---|---|
| `opencraft_ctx_list` | List active contexts, optionally by category. |
| `opencraft_ctx_get` | Fetch a context by id. |
| `opencraft_artifact_validate` | Validate an artifact against active enforcement contexts. |
| `opencraft_packs_status` | Effective pack set, precedence, conflicts. |
| `opencraft_packs_doctor` | Context health over `.lcdd/`. |

The MCP server reads `.lcdd/` directly (mirroring `@lcdd/mcp`'s zero-config design). It is optional; the filesystem surface is the baseline.

## Precedence with other instructions

Consistent with the OpenCraft Skill Standard and LCDD:

1. Client system policy, safety policy, permissions.
2. User's latest request.
3. Repository instructions (`AGENTS.md`, `CLAUDE.md`), which include the pointer to `.lcdd/CONTEXT.md`.
4. Active skills.
5. Generic references.

Pack-derived contexts enter at level 3 — repository instructions — and remain enforced, versioned, and auditable.

## Hardened enforcement

`hardened-*` contexts are immutable to AI: agents are instructed not to modify `.lcdd/contexts/` records, and the engine's `packs doctor` flags drift if they are changed. Enforcement hooks (CI/`lcd validate`) remain the authoritative gate.

## References

- [0012 — LCDD Integration](0012-lcdd-integration.md)
- LCDD 0010 — AI Agent Governance
- OpenCraft Skills — STANDARD.md (instruction precedence)
