# 0013 — Reference Implementation

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

The reference implementation proves the specification is implementable and testable. It is dependency-free (Python stdlib + Node core only), runs offline, and requires no API keys. Python is the authoritative engine; the Node CLI is behaviorally equivalent so the npm package keeps its "no runtime dependencies" promise.

## Packages and layout

```text
scripts/
├── packlib/                 # Python engine
│   ├── yamlmini.py          # YAML subset parser + emitter (no PyYAML)
│   ├── jsonschema_mini.py   # JSON Schema validator subset
│   ├── manifest.py          # pack.yaml / packs.yaml load + parse
│   ├── resolver.py          # graph resolution + precedence
│   ├── merger.py            # context + PKD merge, overrides, conflicts
│   ├── validator.py         # schema + semantic + pack rules
│   ├── knowledge.py         # PKD typing + merge helpers
│   ├── registry.py          # catalog + cache + fetch
│   └── materialize.py       # .lcdd/ writer, lockfile, CONTEXT.md
├── packtool.py              # Python CLI (packs namespace)
├── packtool.mjs             # Node CLI (equivalent core)
├── packlib_test.py          # unit tests
├── pack-evaluate.py         # pack eval fixture checker
└── generate_pack_lock.py    # source-tree integrity lock
```

## Engine pipeline

```
resolve (resolver.py) → merge (merger.py) → validate (validator.py) → materialize (materialize.py)
   │        │                │                    │                       │
   │  extends+deps,     precedence merge,    schema + semantic +      write .lcdd/,
   │  semver, cycles,   overrides,           integrity                  lockfile,
   │  diamonds          conflict policy                               CONTEXT.md, report
```

## YAML subset (why we ship our own parser)

Neither Python stdlib nor Node core includes YAML. The engine ships `yamlmini` supporting the documented subset used by packs:

- Block mappings and sequences (2-space indentation).
- Plain / single- / double-quoted scalars; ints, floats, booleans, null.
- Inline flow `[a, b]` and `{k: v}`.
- Block scalars `|` (literal) and `>` (folded), including chomping indicators.
- Comments; no anchors, aliases, or multi-document streams.

All canonical packs are validated to stay within the subset (unknown constructs fail authoring validation). Emitting is fully controlled by the engine, so `.lcdd/` output is always parseable by any YAML tool.

## JSON Schema subset

`jsonschema_mini` implements the keywords the schemas use: `type`, `properties`, `required`, `items`, `enum`, `const`, `pattern`, `minLength/maxLength`, `minimum/maximum`, `additionalProperties`, `oneOf/anyOf/allOf/not`, and `$ref` into `$defs`/`definitions`. Unknown keywords are ignored so schemas remain compatible with full validators.

## Registry and caching

`registry.py` resolves in order: cache → built-in `packs/` tree → remote npm transport. The built-in tree makes all 14 reference packs installable offline and key-free. Remote fetch verifies `sha256` before unpacking; network failures degrade gracefully to a clear error, never partial state.

## Determinism

- Materialization is stable: same input → same files (timestamps excluded).
- Lists are emitted in precedence order; maps sorted for byte-stable output.
- `.lcdd/packs.lock.json` and `.lcdd/report.json` round-trip deterministically.

## Parity between Python and Node

The Node CLI (`packtool.mjs`) implements the same pipeline: YAML subset parser, JSON Schema subset, resolver, merger, validator, and materializer. A parity smoke test installs the same project with both CLIs and diffs `.lcdd/` output.

## Test coverage

`packlib_test.py` covers:

- YAML subset parsing (all constructs) and emission round-trips.
- JSON Schema validator (all supported keywords).
- Resolution: cycles, diamonds, unsatisfiable ranges, precedence ordering.
- Merge: context replacement, `patch`, `disable`, `defer`; PKD list/map/scalar merge.
- Conflicts: `fail`, `highest-precedence-wins`, `keep-first`, hardened guarantee.
- Materialization determinism and lockfile integrity.

### Security tests

`security_test.py` covers the attack surface of the engine:

- **Path traversal** — context ids that would escape `contexts/` are rejected at
  materialization and validation; verified with `../`, `..`, `.`, separators,
  and null bytes.
- **YAML DoS** — maximum nesting depth enforced for block and flow parsing;
  deep payloads raise instead of exhausting the stack.
- **Alias/billion-laughs resistance** — anchors/aliases are not expanded, so
  exponential-alias payloads cannot allocate; large flat documents parse in
  bounded time.
- **Secret heuristics** — pack content (contexts, PKDs, AI prose) is scanned
  for likely secrets (`api_key:`, `password =`, `Authorization: Bearer …`).

### Performance benchmark

`pack-bench.py` asserts loose upper bounds (fail in CI on regression):

| Scenario | Measured (reference) | Bound |
|---|---|---|
| `validate --all` (14 packs) | ~0.1s | 15s |
| `install` into a project (Python) | ~0.14s | 10s |
| `install` into a project (Node) | ~0.09s | 10s |
| Resolve 100-pack diamond | ~0.09s | 5s |

## References

- [0008 — Validation](0008-validation.md)
- [0009 — Registry](0009-registry.md)
- [0010 — CLI](0010-cli.md)
- [packs/SPEC.md](../SPEC.md)
