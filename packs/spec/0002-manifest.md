# 0002 — Pack Manifest

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

The pack manifest (`pack.yaml`) is the machine-readable declaration of a Context Pack. It names the pack, versions it, describes its content, declares its relationships (`extends`, `dependencies`), and records governance and ownership metadata.

## Location and schema

- Location: `pack.yaml` at the pack root.
- Schema: [context-pack.schema.json](../schemas/context-pack.schema.json).

## Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `schema` | yes | string | Schema URL, `https://opencraft.dev/schema/context-pack/v1`. |
| `name` | yes | string | Kebab-case, ends in `-pack`, globally unique. |
| `version` | yes | string | Strict SemVer. |
| `type` | yes | enum | `technology` \| `framework` \| `baas` \| `cross-cutting` \| `domain`. |
| `description` | yes | string | One-line purpose. |
| `license` | yes | string | SPDX license identifier. |
| `author` | yes | object | `{type, id, name, uri?}` of the authoring entity. |
| `tags` | no | string[] | Discoverability tags. |
| `extends` | no | string[] | Pack references `name@range`, ordered by increasing precedence. |
| `dependencies` | no | string[] | Required sibling packs `name@range`. |
| `provides` | no | object | Optional declaration of contexts and PKD kinds this pack contributes. |
| `lifecycle` | yes | enum | `draft` \| `candidate` \| `approved` \| `active` \| `deprecated` \| `archived`. |
| `governance` | yes | object | `{classification, approval_required}` per LCDD governance model. |
| `owner` | yes | object | `{type, id, name, email?}` responsible party. |
| `repository` | no | string | Source repository URL. |
| `deprecated` | no | object | `{superseded_by, reason}` when lifecycle is `deprecated`. |

## Example

```yaml
schema: https://opencraft.dev/schema/context-pack/v1
name: nextjs-pack
version: 1.2.0
type: framework
description: Living context for Next.js App Router applications
license: MIT
author:
  type: organization
  id: opencraft
  name: OpenCraft
tags: [nextjs, react, web, app-router, ssr]
extends:
  - react-pack@^1
  - typescript-pack@^1
dependencies:
  - node-pack@^20
provides:
  contexts:
    - ctx-nextjs-app-router
    - ctx-nextjs-data-fetching
  knowledge:
    - tech-stack
    - conventions
    - architecture
    - ai-rules
lifecycle: active
governance:
  classification: local-standard
  approval_required: false
owner:
  type: organization
  id: opencraft-web
  name: OpenCraft Web
repository: https://github.com/Lelianto/opencraft-skills
```

## `provides` vs actual content

`provides` is advisory metadata (used for cataloging and discovery). The validator additionally verifies that every `provides.contexts` id exists in `contexts/`. The **actual** content is the files on disk; `provides` must not diverge from them.

## Governance rules for the manifest itself

- `governance.classification` uses the LCDD set: `hardened-mandate`, `hardened-standard`, `hardened-local`, `local-standard`, `local-guideline`, `local-experimental`.
- When `classification` starts with `hardened-`, `approval_required` MUST be `true`.
- `owner` MUST be set for any non-`archived` pack.

## References

- [0003 — Versioning](0003-versioning.md)
- [0004 — Dependency System](0004-dependency-system.md)
- [0008 — Validation](0008-validation.md)
