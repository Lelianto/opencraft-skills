# 0004 — Dependency System

**Status:** Candidate · **Version:** 1.0.0 · **Spec:** OpenCraft Skills — Context Packs

## Abstract

Packs form a directed graph of `extends` (inheritance) and `dependencies` (peer requirements) edges. The dependency system resolves this graph to a concrete, ordered, cycle-free set of pack versions.

## Edge kinds

| Edge | Declared in | Semantics |
|---|---|---|
| `extends` | `pack.yaml` (pack author) and `packs.yaml` (project) | Inheritance. Parent contexts and PKDs are inherited; the child binds tighter. |
| `dependencies` | `pack.yaml` | Peer requirement. The named pack MUST be present in the resolved set, but its content is not inherited by the declaring pack. |
| project `extends` | `packs.yaml` | The root edges. Order defines precedence (later = higher). |

`dependencies` expresses "this pack requires these to be installed" (e.g. `nextjs-pack` depends on `node-pack`), while `extends` expresses "this pack is built from these" (e.g. `nextjs-pack extends react-pack`).

## Resolution algorithm

1. **Roots.** Read project `packs.yaml` `extends` entries in order. Assign root precedence `0..n-1`.
2. **Expand.** For each pack, expand its own `extends` (parents) and `dependencies` (peers). A pack may be referenced by `name@range` or `name` (any version).
3. **Resolve versions.** For each reference, select the highest version satisfying the range from the registry/cache. Unresolvable → error listing available versions.
4. **Assign precedence.**
   - Project root entry at index `i` → precedence `i`.
   - A parent of pack `P` → precedence `min(prec(P)) - 1` across all children, ensuring a shared (diamond) parent sits below every child.
   - `dependencies` edges do not change precedence; they only require presence.
5. **Cycle detection.** Any path that revisits a pack is an error; report the cycle path.
6. **Diamond handling.** A pack reached via multiple paths resolves to a single instance at the lowest required precedence. If two different versions are demanded by different branches, prefer the highest satisfying all ranges; otherwise surface a version conflict.

## Project declaration

```yaml
# packs.yaml
schema: https://opencraft.dev/schema/project-packs/v1
extends:
  - nextjs-pack@^1
  - security-pack@^2
  - fintech-pack@^1
conflict_policy: fail
```

## Determinism and reproducibility

- The resolved graph is written to `.lcdd/packs.lock.json` with exact versions and integrity hashes.
- Reinstalls from the lockfile reproduce the same graph without re-resolving ranges.
- `opencraft packs update` re-resolves ranges; `opencraft packs install` prefers the lockfile.

## Failure modes

| Condition | Behavior |
|---|---|
| Unknown pack | Error: no version available. |
| Range unsatisfiable | Error with available versions. |
| Cycle | Error with the cycle path. |
| Version conflict (diamond) | Error or downgrade per registry policy; never silent. |
| Deprecated dependency | Warning on install. |
| Archived dependency | Blocked with migration note. |

## References

- [0003 — Versioning](0003-versioning.md)
- [0005 — Inheritance](0005-inheritance.md)
- [0009 — Registry](0009-registry.md)
- [0010 — CLI](0010-cli.md)
