# OpenCraft Context Packs

Install production-ready project context instead of rewriting the same project knowledge repeatedly. Context Packs are the composability layer of **Living Context Driven Development (LCDD)** — the methodology at [github.com/Lelianto/living-context-driven-development](https://github.com/Lelianto/living-context-driven-development).

```yaml
# packs.yaml  (project root)
extends:
  - nextjs-pack
  - security-pack
  - fintech-pack
```

One command materializes the resolved, merged, validated context into `.lcdd/`:

```text
.lcdd/
├── contexts/           # LCDD Context Registry (machine-readable governance)
├── project/            # merged Project Knowledge (vision, stack, conventions, …)
├── ai/AGENTS.md        # merged AI coding rules
├── CONTEXT.md          # generated living-context summary for agents
├── packs.lock.json     # resolved versions + integrity hashes
└── report.json         # merge/conflict/override report
```

## Requirements

- Python 3.10+ **or** Node.js 18+ (both CLIs are behaviorally equivalent).
- No API keys. No cloud account. No `@lcdd/cli` required (optional, interoperable).
- Offline-friendly: the built-in `packs/` tree makes the 14 reference packs installable with no network.

## Quick start

**LCDD applies automatically.** `--with-project-files` (skills installer) or `packs bootstrap` applies the baseline `core-pack` and materializes `.lcdd/` with zero configuration:

```bash
# Apply LCDD to a project (baseline core-pack + .lcdd/)
python3 scripts/packtool.py packs bootstrap --project .
# or, equivalently: node scripts/packtool.mjs packs bootstrap --project .

# Add more context
python3 scripts/packtool.py packs add nextjs-pack --project .
python3 scripts/packtool.py packs add security-pack --project .
python3 scripts/packtool.py packs add fintech-pack --project .
python3 scripts/packtool.py packs install --project .
```

Or after `npm install --global opencraft-skills`:

```bash
opencraft-packs packs bootstrap --project .
opencraft-packs packs add nextjs-pack --project .
opencraft-packs packs install --project .
```

## Command reference

| Command | Description |
|---|---|
| `packs bootstrap` | Apply LCDD: baseline `core-pack` + materialize `.lcdd/` (automatic on install). |
| `packs init` | Create an empty `packs.yaml` + `.lcdd/` skeleton. |
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

Options: `--project <dir>` (default `.`), `--json` (machine-readable), `--force`, `--dry-run`.

## How it works

1. **Resolve** — the `extends` + `dependencies` graph is built, SemVer ranges are satisfied, cycles are rejected, and each pack gets a deterministic **precedence**.
2. **Merge** — contexts merge by `id` (later/higher precedence binds tighter); Project Knowledge merges by `kind` (lists dedupe, maps deep-merge, scalars highest wins).
3. **Override** — explicit `override` entries (`replace`, `patch`, `disable`, `defer`, `resolve`) modify inherited content; hardened contexts can never be silently changed.
4. **Validate** — JSON Schema + LCDD context semantics (R1–R5) + pack rules + integrity.
5. **Materialize** — writes `.lcdd/`, the lockfile, `CONTEXT.md`, and an audit report.

## Conflict resolution

A conflict is two definitions of the same context `id` at the same precedence level. Policies (project `conflict_policy`, default `fail`):

- `fail` — installation stops with a conflict report.
- `highest-precedence-wins` — later `extends` entries win.
- `keep-first` — earlier entries win.
- `human` — installation pauses for an explicit human decision.

**Hardened contexts** (`governance.classification` starting with `hardened-`) are never auto-resolved. Add an explicit `override` or a `resolve` entry in `packs.yaml`:

```yaml
overrides:
  - id: ctx-security-scanning
    action: resolve
    pack: security-pack
    reason: "Adopt the security-pack baseline for scanning."
```

## The reference packs

| Type | Packs |
|---|---|
| technology | `typescript-pack`, `node-pack` |
| framework | `react-pack`, `nextjs-pack` |
| baas | `supabase-pack`, `firebase-pack` |
| cross-cutting | `security-pack`, `testing-pack`, `accessibility-pack` |
| domain | `fintech-pack`, `healthcare-pack`, `ecommerce-pack`, `education-pack` |

Example composition:

```yaml
extends:
  - nextjs-pack@^1     # + react-pack + typescript-pack
  - security-pack@^1
  - fintech-pack@^1    # + node-pack + testing-pack; patches security rules
```

## AI integration

After install, agents read `.lcdd/CONTEXT.md` and the machine-readable `contexts/` and `project/`. The merged AI coding rules land in `.lcdd/ai/AGENTS.md`. No API key is involved — the filesystem is the interface. An optional MCP server can expose structured querying for MCP-capable agents.

## LCDD interoperability

- `.lcdd/contexts/` is a git-backed **LCDD Context Registry** (Topology 1); every file is a valid LCDD Context record.
- `@lcdd/cli` (`lcd validate`, `lcd doctor`) and `@lcdd/mcp` operate on `.lcdd/` unchanged — optional enhancements, never prerequisites.
- Contexts satisfy the LCDD Context Schema and validation rules R1–R5.

## Specification and RFCs

- [packs/SPEC.md](../packs/SPEC.md) — the Context Pack Specification.
- [packs/spec/](../packs/spec/) — 14 numbered RFCs (manifest, versioning, dependencies, inheritance, overrides, conflicts, validation, registry, CLI, AI, LCDD).
- [packs/schemas/](../packs/schemas/) — JSON Schemas (manifest, project, lockfile, 14 knowledge kinds).

## FAQ

**Do I need an API key?** No. The engine is deterministic, local, and dependency-free.

**Do I need `@lcdd/cli`?** No. It is optional and interoperable with the materialized `.lcdd/`.

**What if two packs conflict?** Installation reports the conflict and, for hardened contexts, requires an explicit override or human decision.

**Can I author my own pack?** Yes — `packs create <name>` scaffolds one; validate with `packs validate --all`.
