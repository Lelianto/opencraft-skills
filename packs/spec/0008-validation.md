# 0008 — Validation System

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Validation runs at authoring time (CI on the pack repository) and at install time (every project materialization). Both share one engine so a pack that passes CI cannot break a project install.

## Validation layers

### 1. JSON Schema

| Artifact | Schema |
|---|---|
| Pack manifest `pack.yaml` | `packs/schemas/context-pack.schema.json` |
| Project declaration `packs.yaml` | `packs/schemas/project-packs.schema.json` |
| Lockfile `packs.lock.json` | `packs/schemas/packs.lock.schema.json` |
| PKD `project/<kind>.yaml` | `packs/schemas/knowledge/<kind>.schema.json` |
| Context `contexts/*.yaml` | LCDD Context Schema |

The engine ships a dependency-free validator supporting the JSON Schema subset used by these schemas (`type`, `properties`, `required`, `items`, `enum`, `const`, `pattern`, `min/max`, `additionalProperties`, `oneOf/anyOf/allOf/not`, `$ref` to `$defs`/`definitions`).

### 2. LCDD semantic rules

Every context additionally satisfies LCDD validation rules R1–R5:

- **R1** lifecycle-dependent required fields (e.g. `Active` needs `effective_date` + `enforcement`).
- **R2** authority–enforcement consistency (level ≥ 3 active → `block` unless justified).
- **R3** governance–lifecycle consistency (hardened active → `approval_required: true`).
- **R4** temporal consistency (`effective_date` < `deprecated_date`, etc.).
- **R5** supersedes chain integrity (referenced IDs exist).

### 3. Pack rules

- Name matches `^[a-z0-9]+(?:-[a-z0-9]+)*$` and ends in `-pack`.
- Strict SemVer version; no duplicate versions in one pack.
- Context IDs unique within the pack; `metadata.pack` equals the pack name.
- `extends` / `dependencies` resolve; graph is acyclic; ranges satisfiable.
- `provides.contexts` IDs exist on disk.
- `override` targets exist in the inherited set (unless `replace` with a `path` that exists).
- PKD `kind` is known and the file validates; PKD `pack` field matches the pack name.
- `evals/cases.yaml`, when present, has positive, negative, ambiguous, and assertion fixtures.

### 4. Integrity

`packs.lock.json` pins `sha256` per file. Install fails on mismatch with a clear message. The generator (`scripts/generate_pack_lock.py`) writes and checks the lock.

## Command surface

| Command | Scope |
|---|---|
| `opencraft packs validate` | Validate one pack or the whole `packs/` tree. |
| `opencraft packs verify` | Integrity-check the lockfile for the source tree. |
| `opencraft packs doctor` | Health report over installed `.lcdd/` (stale, missing owners, conflicts, drift). |

## Error model

Errors are grouped and machine-readable (`--json`):

- `schema` — JSON Schema violations.
- `semantic` — LCDD R1–R5 and pack rule violations.
- `resolution` — unknown pack, unsatisfiable range, cycle.
- `integrity` — hash mismatch.
- `conflict` — unresolved conflicts.

Installation fails fast at the first blocking layer but reports all findings in the layer it stops at.

## References

- [0013 — Reference Implementation](0013-reference-implementation.md)
- LCDD 0012 — Context Schema
- [packs/schemas/](../schemas/)
