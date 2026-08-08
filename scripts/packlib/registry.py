"""Pack registry: resolution over the built-in packs tree, a local cache, and
the remote npm transport."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

from .manifest import PackError, load_pack, parse_version

__all__ = ["Registry", "file_sha256", "pack_integrity", "fetch_remote_pack"]

REGISTRY_CATALOG = "https://raw.githubusercontent.com/Lelianto/opencraft-skills/main/packs/registry/index.json"
NPM_REGISTRY = "https://registry.npmjs.org"


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
        # npm always injects package.json/package-lock.json into a published
        # tarball; excluding them keeps the integrity stable across publish and
        # re-fetch.
        if rel.name in ("package.json", "package-lock.json"):
            continue
        digest.update(str(rel).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("utf-8"))
        digest.update(b"\0")
    return "sha256-" + digest.hexdigest()


def _catalog_versions(catalog_data, name):
    for entry in catalog_data.get("packs", []):
        if entry.get("name") == name:
            return entry.get("versions", {})
    return {}


def fetch_remote_pack(catalog: dict, name: str, version: str, cache_dir: Path, timeout: float = 30.0) -> Path:
    """Fetch @opencraft/<name>@<version> from the npm registry, verify the
    content integrity, and unpack it into <cache_dir>/<name>/<version>/.

    The catalog pins `pack_integrity` (sha256 over the unpacked pack content),
    so the tarball is unpacked first and then verified; on mismatch the fetch
    fails and the partial cache entry is removed. Returns the unpacked dir.
    """
    versions = _catalog_versions(catalog, name)
    meta = versions.get(version)
    if meta is None:
        raise PackError(f"pack {name}@{version} is not in the remote catalog")
    npm_pkg = meta.get("npm")
    expected = meta.get("integrity", "")
    if not expected.startswith("sha256-"):
        raise PackError(f"pack {name}@{version}: catalog integrity is missing or not sha256")

    tarball_url = f"{NPM_REGISTRY}/{npm_pkg}/-/{name}-{version}.tgz"
    try:
        with urllib.request.urlopen(tarball_url, timeout=timeout) as response:
            payload = response.read()
    except Exception as error:
        raise PackError(f"fetch {tarball_url} failed: {error}") from error

    target = cache_dir / name / version
    target.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            for member in members:
                # npm tarballs prefix every path with package/; strip it.
                parts = Path(member.name).parts
                if parts and parts[0] in ("package", "pack"):
                    relative = Path(*parts[1:])
                else:
                    relative = Path(member.name)
                if not relative.parts or ".." in relative.parts:
                    continue
                out_path = target / relative
                out_path.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                out_path.write_bytes(extracted.read())
    except Exception as error:
        raise PackError(f"unpack {name}@{version} failed: {error}") from error

    if not (target / "pack.yaml").is_file():
        raise PackError(f"fetched {name}@{version} has no pack.yaml (not a Context Pack)")

    actual = pack_integrity(target)
    if actual != expected:
        import shutil

        shutil.rmtree(target, ignore_errors=True)
        raise PackError(
            f"integrity mismatch for {name}@{version}: unpacked content {actual} != catalog {expected}"
        )
    return target


class Registry:
    """Resolves pack names to concrete pack directories.

    Sources are consulted in order: cache directory, then built-in tree, then
    the remote npm transport (only when explicitly enabled and a catalog entry
    exists). Remote resolution is opt-in so the reference implementation stays
    offline and key-free by default.
    """

    def __init__(self, builtin_dir, cache_dir=None, catalog=None, remote=False):
        self.builtin = Path(builtin_dir)
        self.cache = Path(cache_dir) if cache_dir else None
        self.catalog = catalog if isinstance(catalog, dict) else {}
        self.remote = remote

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
        if self.remote:
            for version in _catalog_versions(self.catalog, name):
                if version not in found:
                    found[version] = {"version": version}
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
        if self.remote and self.cache is not None:
            return fetch_remote_pack(self.catalog, name, version, self.cache)
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
