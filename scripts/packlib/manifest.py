"""Pack manifest and project declaration loading, plus SemVer range matching."""

from __future__ import annotations

import re
from pathlib import Path

from .yamlmini import YAMLError, load_file

__all__ = [
    "PackError",
    "parse_ref",
    "parse_version",
    "version_satisfies",
    "load_pack",
    "load_project_declaration",
    "PACK_NAME_RE",
    "PACK_TYPES",
]

PACK_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-pack$")
PACK_TYPES = ["technology", "framework", "baas", "cross-cutting", "domain"]
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CONTEXT_SCHEMA_URL = "https://livingcontext.dev/schema/context/v0.1.0"


class PackError(ValueError):
    pass


def parse_version(version: str):
    core = version.split("-")[0].split("+")[0]
    parts = core.split(".")
    nums = [int(p) for p in parts]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def _as_range(spec: str):
    spec = spec.strip()
    if spec in ("", "*"):
        return None
    if spec.startswith("^"):
        return ("^", spec[1:])
    if spec.startswith("~"):
        return ("~", spec[1:])
    if spec.startswith(">=") or spec.startswith("<=") or spec.startswith(">") or spec.startswith("<"):
        return ("op", spec)
    if "," in spec:
        return ("comma", spec)
    return ("exact", spec)


def version_satisfies(version: str, spec: str) -> bool:
    """Whether ``version`` (SemVer string) satisfies ``spec`` (range string)."""
    if not spec or spec.strip() in ("", "*"):
        return True
    pieces = spec.split()
    for piece in pieces:
        if not version_satisfies_single(version, piece):
            return False
    return True


def version_satisfies_single(version: str, piece: str) -> bool:
    v = parse_version(version)
    kind, arg = _as_range(piece)
    if kind is None:
        return True
    if kind == "exact":
        if "." not in arg:
            return v[0] == int(arg)
        if arg.count(".") == 1:
            a, b = (int(x) for x in arg.split("."))
            return v[0] == a and v[1] == b
        return v == parse_version(arg)
    if kind == "op":
        operator = re.match(r"^(>=|<=|>|<)", piece).group(1)
        target = parse_version(piece[len(operator):])
        return {
            ">": v > target,
            ">=": v >= target,
            "<": v < target,
            "<=": v <= target,
        }[operator]
    if kind == "^":
        target = parse_version(arg)
        low = target
        if target[0] > 0:
            high = (target[0] + 1, 0, 0)
        elif target[1] > 0:
            high = (0, target[1] + 1, 0)
        else:
            high = (0, 0, target[2] + 1)
        return low <= v < high
    if kind == "~":
        target = parse_version(arg)
        low = target
        high = (target[0], target[1] + 1, 0)
        return low <= v < high
    if kind == "comma":
        return all(version_satisfies(version, c.strip()) for c in arg.split(","))
    return True


def parse_ref(ref: str):
    """Split 'name@range' into (name, range)."""
    if "@" in ref:
        name, spec = ref.split("@", 1)
        return name.strip(), (spec.strip() or "*")
    return ref.strip(), "*"


def _scan_pack_dir(pack_dir: Path):
    manifest_data = load_file(pack_dir / "pack.yaml")
    if not isinstance(manifest_data, dict):
        raise PackError(f"{pack_dir}/pack.yaml is not a mapping")
    name = manifest_data.get("name")
    if pack_dir.name != name:
        raise PackError(f"pack directory {pack_dir.name} does not match manifest name {name!r}")
    contexts_dir = pack_dir / "contexts"
    contexts = []
    if contexts_dir.is_dir():
        for path in sorted(contexts_dir.glob("*.yaml")):
            data = load_file(path)
            if not isinstance(data, dict):
                raise PackError(f"{path} is not a mapping")
            contexts.append(data)
    project_dir = pack_dir / "project"
    pkds = {}
    if project_dir.is_dir():
        for path in sorted(project_dir.glob("*.yaml")):
            data = load_file(path)
            if not isinstance(data, dict):
                raise PackError(f"{path} is not a mapping")
            kind = data.get("kind")
            if kind is None:
                raise PackError(f"{path} is missing 'kind'")
            pkds.setdefault(kind, []).append(data)
    ai_dir = pack_dir / "ai"
    ai_prose = None
    if ai_dir.is_dir():
        ag = ai_dir / "AGENTS.md"
        if ag.is_file():
            ai_prose = ag.read_text(encoding="utf-8")
    return {
        "name": name,
        "version": manifest_data.get("version"),
        "dir": str(pack_dir),
        "manifest": manifest_data,
        "contexts": contexts,
        "pkds": pkds,
        "ai_prose": ai_prose,
        "files": {str(p.relative_to(pack_dir)) for p in pack_dir.rglob("*") if p.is_file()},
    }


def load_pack(pack_dir, manifest_data=None):
    """Load a pack tree from a directory. Returns a pack dict (see _scan_pack_dir)."""
    return _scan_pack_dir(Path(pack_dir))


def load_project_declaration(project_dir):
    path = Path(project_dir) / "packs.yaml"
    if not path.is_file():
        raise PackError(f"no packs.yaml found in {project_dir}")
    try:
        data = load_file(path)
    except YAMLError as exc:
        raise PackError(f"invalid packs.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise PackError("packs.yaml must be a mapping")
    if data.get("schema") != "https://opencraft.dev/schema/project-packs/v1":
        raise PackError("packs.yaml is missing or has an invalid schema URL")
    extends = data.get("extends")
    if not isinstance(extends, list) or not extends:
        raise PackError("packs.yaml 'extends' must be a non-empty list")
    return data
