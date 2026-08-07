# TypeScript pack

Living context for TypeScript projects: strict typing, lint/format discipline, and AI coding rules.

## Included contexts

- `ctx-typescript-strict` — `strict: true` is enforced (hardened-standard).
- `ctx-typescript-no-explicit-any` — no new explicit `any` (warn).
- `ctx-typescript-path-aliases` — imports use aliases (comment).

## Provenance

- Author: OpenCraft
- License: MIT
- Source: https://github.com/Lelianto/opencraft-skills

## Usage

```yaml
# packs.yaml
extends:
  - typescript-pack@^1
```
