#!/usr/bin/env python3
"""Security-focused tests for the Context Packs engine.

Covers: path traversal on materialization, YAML nesting DoS (block + flow),
YAML alias/billion-laughs resistance, malicious context ids, and secret-scan
heuristics.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib import manifest, merger, resolver, validator, yamlmini  # noqa: E402
from packlib.materialize import safe_context_filename  # noqa: E402
from packlib.registry import Registry  # noqa: E402


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_pack(root: Path, name: str, cid: str, extra_context=""):
    dirpath = root / name
    write(
        dirpath / "pack.yaml",
        "schema: https://opencraft.dev/schema/context-pack/v1\n"
        f"name: {name}\nversion: 1.0.0\ntype: technology\ndescription: t\n"
        "license: MIT\nauthor:\n  type: organization\n  id: o\n  name: O\n"
        "lifecycle: active\ngovernance:\n  classification: local-standard\n  approval_required: false\n"
        "owner:\n  type: organization\n  id: o\n  name: O\n",
    )
    write(
        dirpath / "contexts" / f"{cid}.yaml",
        f"id: {cid}\nversion: 1\ntitle: {cid}\ndescription: test\n"
        "source:\n  type: organization\n  uri: https://example.test\n"
        "authority:\n  source:\n    type: organization\n    id: o\n    name: O\n  level: 2\n"
        "lifecycle: active\ngovernance:\n  classification: local-standard\n  approval_required: false\n"
        "owner: o\neffective_date: 2026-01-01T00:00:00Z\nenforcement:\n  mode: warn\n"
        "metadata:\n  pack: " + name + "\n" + extra_context,
    )
    return dirpath


class PathTraversalTests(unittest.TestCase):
    def test_safe_filename_rejects_traversal(self):
        for bad in ["../evil", "..", "a/b", "a\\b", "a\0b", "", ".", "..", "a..b/../../x"]:
            with self.assertRaises(ValueError, msg=f"should reject {bad!r}"):
                safe_context_filename(bad)
        for good in ["ctx-a-b", "ctx_1", "ctx.x-y"]:
            self.assertEqual(safe_context_filename(good), f"{good}.yaml")

    def test_materialize_blocks_malicious_context_id(self):
        from packlib import materialize as mat

        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(packs_root, "evil-pack", "ctx-ok")
        reg = Registry(packs_root)
        proj = tmp / "proj"
        write(proj / "packs.yaml", "schema: https://opencraft.dev/schema/project-packs/v1\nextends:\n  - evil-pack@^1\n")
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        # Inject a context id that would escape the directory.
        ordered[0]["pack"]["contexts"][0]["id"] = "../../pwned"
        merged = merger.merge(ordered, project)
        with self.assertRaises(ValueError):
            mat.materialize(proj, merged, ordered, project)

    def test_validator_rejects_bad_context_id(self):
        errors = validator.context_errors({"id": "../../evil", "version": 1})
        self.assertTrue(any("id must be" in e for e in errors))


class YAMLDoSTests(unittest.TestCase):
    def test_deep_block_nesting_rejected(self):
        lines = []
        indent = 0
        for _ in range(1000):
            lines.append(" " * indent + "a:")
            indent += 2
        lines.append(" " * indent + "b: 1")
        with self.assertRaises(yamlmini.YAMLError):
            yamlmini.parse("\n".join(lines))

    def test_deep_flow_nesting_rejected(self):
        with self.assertRaises(yamlmini.YAMLError):
            yamlmini.parse("a: " + "[" * 5000)

    def test_alias_billion_laughs_is_inert(self):
        doc = "a: &x\n  value: ok\nb: *x\nc: *x\nd: *x\n"
        data = yamlmini.parse(doc)
        # Anchors/aliases are not expanded (subset does not support them), so a
        # billion-laughs payload cannot allocate exponential structures.
        self.assertEqual(data.get("a"), "&x")
        self.assertIn("a", data)

    def test_huge_flat_document_fast(self):
        payload = "\n".join(f"key{i}: value{i}" for i in range(50000))
        data = yamlmini.parse(payload)
        self.assertEqual(len(data), 50000)


class SecretScanTests(unittest.TestCase):
    def test_flags_secrets(self):
        self.assertTrue(validator.secret_warnings('api_key: sk-live-abc1234567890xyz'))
        self.assertTrue(validator.secret_warnings("password = hunter2superSecretValue"))
        self.assertTrue(validator.secret_warnings("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.xxxxx.yyyyy"))

    def test_ignores_legitimate_text(self):
        self.assertEqual(validator.secret_warnings("Secrets must never be committed to source."), [])
        self.assertEqual(validator.secret_warnings("Use a secret manager for credentials."), [])
        self.assertEqual(validator.secret_warnings("provision from a secret manager at runtime"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
