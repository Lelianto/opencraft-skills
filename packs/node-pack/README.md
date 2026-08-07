# Node pack

Living context for Node.js services: runtime versioning, ESM discipline, deployment, and observability.

## Included contexts

- `ctx-node-runtime-version` — engines.node declared and LTS honored (hardened-standard).
- `ctx-node-esm` — new modules are ESM (warn).

## Provenance

- Author: OpenCraft
- License: MIT
- Source: https://github.com/Lelianto/opencraft-skills

## Usage

```yaml
# packs.yaml
extends:
  - node-pack@^1
```
