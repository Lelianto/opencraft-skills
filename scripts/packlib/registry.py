"""Pack registry: resolution over the built-in packs tree and a local cache."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .manifest import PackError, load_pack, parse_version

__all__ = ["Registry", "file_sha256", "pack_integrity"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_integrity(pack_dir: Path) -> str:
    files = sorted(p for p in pack_dir.rglob("*") if p.is_file())
    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(pack_dir)
        digest.update(str(rel).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return "sha256-" + digest.hexdigest()


class Registry:
    """Resolves pack names to concrete pack directories.

    Sources are consulted in order: cache directory, then built-in tree.
    Remote transport is intentionally not required for the reference
    implementation (offline, key-free guarantee); a remote transport can be
    layered in behind the same interface.
    """

    def __init__(self, builtin_dir, cache_dir=None):
        self.builtin = Path(builtin_dir)
        self.cache = Path(cache_dir) if cache_dir else None

    def _candidates(self, name):
        dirs = []
        if self.cache is not None:
            dirs.append(self.cache / name)
        dirs.append(self.builtin / name)
        return dirs

    def versions(self, name: str):
        found = {}
        if self.cache is not None:
            base = self.cache / name
            for version_dir in base.glob("*/"):
                if (version_dir / "pack.yaml").is_file():
                    manifest = _read_version(base, version_dir.name)
                    found[version_dir.name] = manifest
        builtin = self.builtin / name
        if (builtin / "pack.yaml").is_file():
            manifest = _read_version(builtin, None)
            found[manifest.get("version")] = manifest
        return found

    def has(self, name: str, version: str) -> bool:
        try:
            self._locate(name, version)
            return True
        except PackError:
            return False

    def _locate(self, name, version):
        if self.cache is not None:
            candidate = self.cache / name / version
            if (candidate / "pack.yaml").is_file():
                return candidate
        candidate = self.builtin / name
        if (candidate / "pack.yaml").is_file():
            manifest = _read_version(candidate, None)
            if manifest.get("version") == version:
                return candidate
        raise PackError(f"pack {name}@{version} is not available in the local registry")

    def load(self, name: str, version: str):
        pack_dir = self._locate(name, version)
        pack = load_pack(pack_dir)
        return pack

    def integrity(self, name: str, version: str) -> str:
        return pack_integrity(self._locate(name, version))


def _read_version(base: Path, version_dir_name):
    from .yamlmini import load_file

    path = base if version_dir_name is None else base / version_dir_name
    data = load_file(path / "pack.yaml")
    if not isinstance(data, dict):
        raise PackError(f"{path}/pack.yaml is not a mapping")
    return data
