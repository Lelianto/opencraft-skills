# Next.js pack

Living context for Next.js App Router applications: server-first data fetching, Server Actions, structure, security, and AI coding rules.

## Included contexts

- `ctx-nextjs-app-router` — App Router only (block).
- `ctx-nextjs-data-fetching` — server-first fetching with declared caching (warn).
- `ctx-nextjs-server-actions` — mutations run server-side with validation, auth, revalidation (hardened-standard, block).

## Extends

- `react-pack@^1`
- `typescript-pack@^1`
- depends on `node-pack@^1`

## Project knowledge

`vision`, `architecture`, `conventions`, `folder-structure`, `tech-stack`, `security`, `testing`, `ai-rules`, `review-checklist`, `deployment`, `observability`, `lifecycle`, `ownership`.

## Provenance

- Author: OpenCraft · License: MIT · Source: https://github.com/Lelianto/opencraft-skills

## Usage

```yaml
extends:
  - nextjs-pack@^1
  - security-pack@^2
  - fintech-pack@^1
```
