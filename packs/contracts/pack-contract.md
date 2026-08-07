# Pack Content Contract

Every published Context Pack MUST satisfy this contract. Validation (RFC 0008) enforces it.

## Mandatory files

| File | Requirement |
|---|---|
| `pack.yaml` | Valid manifest per [context-pack.schema.json](../schemas/context-pack.schema.json). |
| `README.md` | Human documentation: purpose, included contexts, provenance, usage. |
| `contexts/*.yaml` | One or more LCDD Context records. Each MUST be valid against the LCDD Context Schema and carry `metadata.pack` equal to the pack name. Context IDs MUST be unique within the pack. |
| `project/` | One or more Project Knowledge Documents. Each MUST have a `kind` in the known set and validate against the corresponding schema. |
| `ai/AGENTS.md` | Optional agent prose fragment. Must not include secrets or absolute local paths. |
| `evals/cases.yaml` | Optional validation fixtures (see below). |
| `LICENSE` | Recommended. Required for publication. |

## Pack name

- Lowercase kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`).
- MUST end with `-pack` so pack identities are unambiguous.
- MUST be globally unique in the registry. Scoped npm package is `@opencraft/<name>`.

## Version

- Strict SemVer `MAJOR.MINOR.PATCH`.
- MAJOR bumps for removed/breaking contexts or artifacts; MINOR for additive; PATCH for corrections.

## Governance provenance

- Every context MUST record `source` and `authority` per the LCDD schema, plus `metadata.pack`.
- Pack `owner` and `governance` MUST be set so responsibility is always attributable.

## PKD kinds

Each `project/*.yaml` MUST declare `kind:` and conform to the matching schema in `packs/schemas/knowledge/`:

`vision`, `architecture`, `conventions`, `folder-structure`, `tech-stack`, `security`, `testing`, `business-constraints`, `ai-rules`, `review-checklist`, `deployment`, `observability`, `lifecycle`, `ownership`.

## Quality expectations

- Contexts describe a verifiable constraint (with `enforcement` where applicable), not vague advice.
- PKDs are factual and bounded: no invented metrics, no credentials, no private operational detail.
- `ai-rules` entries use imperative `MUST`/`MUST NOT`/`SHOULD` language and cite a rationale.
- A pack that extends another MUST NOT contradict a hardened (`hardened-*`) parent context silently; it must use an explicit `override`.
- Evals, when present, provide positive, negative, and ambiguous discovery prompts plus assertion checks, mirroring the skills collection standard.
