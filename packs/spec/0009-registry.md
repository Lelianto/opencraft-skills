# 0009 — Registry Architecture

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

The registry is the discoverability + distribution layer. OpenCraft distributes packs as scoped npm packages for supply-chain hardening (Trusted Publishing, provenance, integrity) and layers a lightweight catalog + resolver protocol on top.

## Components

```
┌──────────────────────────────┐
│         CONSUMERS            │
│  packtool CLI / SDK          │
└──────────────┬───────────────┘
               │ resolve(name, range)
               ▼
┌──────────────────────────────┐
│   RESOLUTION LAYER           │
│  1. local cache ~/.opencraft/│
│  2. built-in packs/ tree     │
│  3. remote catalog+transport │
└──────────────┬───────────────┘
               │
      ┌────────┴─────────┐
      ▼                  ▼
┌───────────┐   ┌───────────────────────┐
│ CATALOG   │   │ TRANSPORT             │
│ index.json│   │ npm @opencraft/<name> │
│ (metadata)│   │ tarball + sha256      │
└───────────┘   └───────────────────────┘
```

## Catalog

`packs/registry/index.json` is the canonical catalog:

```json
{
  "schema": "https://opencraft.dev/schema/registry/v1",
  "packs": [
    {
      "name": "nextjs-pack",
      "type": "framework",
      "description": "Living context for Next.js App Router applications",
      "latest": "1.2.0",
      "versions": {
        "1.2.0": {
          "npm": "@opencraft/nextjs-pack",
          "integrity": "sha256-...",
          "extends": ["react-pack@^1", "typescript-pack@^1"],
          "dependencies": ["node-pack@^20"]
        }
      }
    }
  ]
}
```

The catalog enables resolution, search, `latest` tracking, and deprecation signals without fetching every tarball.

## Transport

- **Publication:** each pack publishes as `@opencraft/<name>` via npm Trusted Publishing, with provenance and a recorded integrity hash.
- **Fetch:** the resolver downloads the npm tarball and verifies the `sha256` before unpacking to the cache.
- **Offline:** a populated cache or the built-in `packs/` tree needs no network.

## Cache

- Location: `~/.opencraft/packs/<name>/<version>/`.
- Layout mirrors the pack; an `installed.json` records integrity + provenance.
- Cache entries are immutable; a re-fetch verifies hashes.

## Resolver precedence

1. Cache `~/.opencraft/packs/` (exact versions).
2. Built-in `packs/` tree (reference packs ship with the source).
3. Remote catalog + npm transport (with integrity verification).

## Deprecation and supersession

- A `deprecated` version stays in the catalog with `superseded_by`.
- Resolving a deprecated pack warns; resolving an archived pack fails.
- The catalog records maintainer info and security reporting channel per pack.

## Security model

- **Integrity:** every fetch is verified against the recorded `sha256`.
- **Provenance:** npm provenance + OIDC for official packs; the catalog records the publisher.
- **Namespace:** only `@opencraft` scopes are published from this repository; forks/community packs use their own scopes and are tagged as such in the catalog.
- **No secrets:** packs must not contain credentials; the pack validator rejects likely secrets in `contexts/` and `ai/`.

## References

- [0003 — Versioning](0003-versioning.md)
- [0004 — Dependency System](0004-dependency-system.md)
- [packs/registry/RESOLVER.md](../registry/RESOLVER.md)
