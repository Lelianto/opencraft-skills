"""Pack graph resolution: extends + dependencies, SemVer ranges, cycles, precedence."""

from __future__ import annotations

from .manifest import PackError, parse_ref, parse_version, version_satisfies

__all__ = ["ResolutionError", "resolve"]


class ResolutionError(PackError):
    pass


def _new_node():
    return {
        "specs": [],
        "extends": [],
        "dependencies": [],
        "parents": set(),
        "precedence": None,
        "version": None,
        "pack": None,
    }


def _resolve_version(registry, name, specs):
    versions = registry.versions(name)
    if not versions:
        raise ResolutionError(f"pack {name} is not available in the local registry")
    candidates = [v for v in versions if all(version_satisfies(v, s) for s in specs)]
    if not candidates:
        raise ResolutionError(
            f"no version of {name} satisfies {sorted(set(specs))} (available: {sorted(versions)})"
        )
    return max(candidates, key=parse_version)


def resolve(project, registry):
    """Resolve a project declaration to an ordered list of concrete packs.

    Returns ``[{'name', 'version', 'precedence', 'pack'}, ...]`` sorted by
    precedence ascending (lowest precedence first).
    """
    roots = []
    for ref in project["extends"]:
        name, spec = parse_ref(ref)
        roots.append((name, spec))
    if not roots:
        raise ResolutionError("project extends is empty")

    graph = {}
    # Pass 1: collect the graph and detect cycles.
    color = {}
    for name, _ in roots:
        graph.setdefault(name, _new_node())

    def visit(name, path):
        color[name] = "gray"
        node = graph[name]
        pack = _peek_manifest(registry, name)
        for ref in pack.get("extends", []):
            parent, spec = parse_ref(ref)
            graph.setdefault(parent, _new_node())
            node["extends"].append((parent, spec))
            graph[parent]["specs"].append((name, spec))
            graph[parent]["parents"].add(name)
            if color.get(parent) == "gray":
                raise ResolutionError(f"circular extends detected: {' -> '.join(path + [parent])}")
            if color.get(parent) != "black":
                visit(parent, path + [parent])
        for ref in pack.get("dependencies", []):
            dep, spec = parse_ref(ref)
            graph.setdefault(dep, _new_node())
            node["dependencies"].append((dep, spec))
            graph[dep]["specs"].append((name, spec))
            if color.get(dep) == "gray":
                raise ResolutionError(f"circular dependency detected: {' -> '.join(path + [dep])}")
            if color.get(dep) != "black":
                visit(dep, path + [dep])
        color[name] = "black"

    for name, spec in roots:
        graph[name]["specs"].append(("project", spec))
        visit(name, [name])

    # Pass 2: resolve versions for every node in the graph.
    for name, node in graph.items():
        node["version"] = _resolve_version(registry, name, [s for _, s in node["specs"]])

    # Pass 3: precedence.
    #   roots: index+1 ; dependency-only nodes: 0 ; parents: min(child)-1
    for index, (name, _) in enumerate(roots):
        graph[name]["precedence"] = index + 1
    for name, node in graph.items():
        if node["precedence"] is None and (node["dependencies"] or node["specs"][0][0] != "project"):
            node["precedence"] = 0
    stable = False
    while not stable:
        stable = True
        for name, node in graph.items():
            if node["precedence"] is None:
                continue
            for parent, _ in node["extends"]:
                pnode = graph[parent]
                new_prec = node["precedence"] - 1
                if pnode["precedence"] is None or new_prec < pnode["precedence"]:
                    pnode["precedence"] = new_prec
                    stable = False
    for name, node in graph.items():
        if node["precedence"] is None:
            node["precedence"] = 0

    # Pass 4: load concrete packs.
    ordered = []
    for name, node in graph.items():
        pack = registry.load(name, node["version"])
        node["pack"] = pack
        ordered.append(
            {
                "name": name,
                "version": node["version"],
                "precedence": node["precedence"],
                "pack": pack,
            }
        )
    ordered.sort(key=lambda item: item["precedence"])
    return ordered


def _peek_manifest(registry, name):
    """Read a pack manifest without full loading (used during graph collection)."""
    versions = registry.versions(name)
    if not versions:
        raise ResolutionError(f"pack {name} is not available in the local registry")
    version = max(versions, key=parse_version)
    pack = registry.load(name, version)
    return pack["manifest"]
