# Registry Resolver Protocol

This document specifies how OpenCraft Context Pack resolution consults the registry. It is the companion to [RFC 0009](../spec/0009-registry.md).

## Resolution order

The resolver (`scripts/packlib/registry.py` and `scripts/packtool.mjs`) consults sources in this order:

1. **Local cache** `~/.opencraft/packs/<name>/<version>/` — offline, immutable, integrity-verified.
2. **Built-in tree** `packs/` — the 14 reference packs ship with the repository.
3. **Remote transport** — scoped npm packages `@opencraft/<name>` via the catalog + npm tarball, with sha256 verification. Enabled with `--remote`; the tarball is fetched, unpacked, and the unpacked content is verified against the catalog's `pack_integrity` before the cache entry is accepted.

## Version selection

Given a reference `name@range`:

1. Enumerate available versions (cache + built-in tree).
2. Keep versions satisfying the range (SemVer, see RFC 0003).
3. Select the **highest** satisfying version (SemVer ordering).
4. Fail with an explicit error listing available versions if none match.

## Integrity

- Every pack records `sha256-<hex>` computed over all files, namespaced by relative path (see `pack_integrity` in `scripts/packlib/registry.py`).
- The catalog (`index.json`) pins integrity per version; the lockfile (`packs.lock.json`) pins the resolved graph.
- A fetched tarball MUST be verified against the recorded integrity before unpacking; on mismatch, installation fails.

## Catalog schema

`packs/registry/index.json`:

```json
{
  "schema": "https://opencraft.dev/schema/registry/v1",
  "packs": [
    {
      "name": "nextjs-pack",
      "type": "framework",
      "description": "Living context for Next.js App Router applications",
      "license": "MIT",
      "author": "OpenCraft",
      "tags": ["nextjs", "react", "app-router", "ssr", "web"],
      "latest": "1.0.0",
      "lifecycle": "active",
      "versions": {
        "1.0.0": {
          "npm": "@opencraft/nextjs-pack",
          "integrity": "sha256-...",
          "extends": ["react-pack@^1", "typescript-pack@^1"],
          "dependencies": ["node-pack@^1"]
        }
      }
    }
  ]
}
```

## Transport interface (for a hosted implementation)

A remote registry MUST expose:

| Operation | Endpoint | Purpose |
|---|---|---|
| Search/list | `GET /packs` | Discover packs by type/tag. |
| Metadata | `GET /packs/:name` | Latest + version list. |
| Version metadata | `GET /packs/:name/versions` | Per-version integrity, extends, deps. |
| Tarball | `GET /packs/:name/-/:version.tgz` | Pack content, integrity-verified. |
| Deprecation | field on version metadata | `deprecated` + `superseded_by`. |

The npm registry satisfies this contract: `@opencraft/<name>` package metadata
(`GET /@opencraft/<name>`) serves search/list/metadata, and the tarball URL
`GET /@opencraft/<name>/-/<name>-<version>.tgz` serves the content. The
reference implementation keeps the same interface behind `Registry` so a
remote source can replace the built-in tree without changing the resolver.

## Deprecation

- `deprecated` versions remain resolvable but warn on install.
- `archived` versions fail with a migration note.
- The catalog records `lifecycle` per pack; the resolver enforces it.
