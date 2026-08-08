#!/usr/bin/env python3
"""Unit tests for the Context Packs engine."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib import jsonschema_mini, manifest, merger, resolver, validator, yamlmini  # noqa: E402
from packlib import doctor as doctor_engine  # noqa: E402
from packlib.materialize import materialize, render_context_md  # noqa: E402
from packlib.registry import Registry, pack_integrity  # noqa: E402


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_pack(root: Path, name: str, version: str, extra_manifest="", contexts=None, pkds=None):
    dirpath = root / name
    manifest_text = (
        "schema: https://opencraft.dev/schema/context-pack/v1\n"
        f"name: {name}\n"
        f"version: {version}\n"
        "type: technology\n"
        "description: test pack\n"
        "license: MIT\n"
        "author:\n"
        "  type: organization\n"
        "  id: opencraft\n"
        "  name: OpenCraft\n"
        "lifecycle: active\n"
        "governance:\n"
        "  classification: local-standard\n"
        "  approval_required: false\n"
        "owner:\n"
        "  type: organization\n"
        "  id: opencraft\n"
        "  name: OpenCraft\n"
        + extra_manifest
    )
    write(dirpath / "pack.yaml", manifest_text)
    for cid, body in (contexts or {}).items():
        text = (
            f"id: {cid}\n"
            "version: 1\n"
            f"title: {cid}\n"
            "description: test\n"
            "source:\n"
            "  type: organization\n"
            "  uri: https://example.test\n"
            "authority:\n"
            "  source:\n"
            "    type: organization\n"
            "    id: opencraft\n"
            "    name: OpenCraft\n"
            "  level: 2\n"
            "lifecycle: active\n"
            "governance:\n"
            "  classification: local-standard\n"
            "  approval_required: false\n"
            "owner: opencraft\n"
            "effective_date: 2026-01-01T00:00:00Z\n"
            "enforcement:\n"
            "  mode: warn\n"
            "metadata:\n"
            f"  pack: {name}\n"
        )
        text += body or ""
        write(dirpath / "contexts" / f"{cid}.yaml", text)
    for kind, doc in (pkds or {}).items():
        text = f"kind: {kind}\npack: {name}\n"
        text += doc or ""
        write(dirpath / "project" / f"{kind}.yaml", text)
    return dirpath


def make_project(dirpath: Path, extends, overrides="", policy="fail"):
    text = "schema: https://opencraft.dev/schema/project-packs/v1\n"
    if extends:
        text += "extends:\n"
        for ref in extends:
            text += f"  - {ref}\n"
    else:
        text += "extends: []\n"
    text += f"conflict_policy: {policy}\n"
    text += overrides
    write(dirpath / "packs.yaml", text)
    return dirpath


class YamlTests(unittest.TestCase):
    def test_roundtrip(self):
        data = {
            "a": 1,
            "b": 1.5,
            "c": True,
            "d": None,
            "e": "x: y",
            "f": [1, "two", {"k": "v"}],
            "g": {"nested": {"deep": [True, None]}},
            "h": "multi\nline\n",
        }
        text = yamlmini.dump(data)
        self.assertEqual(yamlmini.parse(text), data)

    def test_flow(self):
        self.assertEqual(yamlmini.parse("l: [a, b, {x: 1}]\n"), {"l": ["a", "b", {"x": 1}]})

    def test_block_scalars(self):
        text = "a: |\n  line1\n  line2\n"
        self.assertEqual(yamlmini.parse(text), {"a": "line1\nline2\n"})
        text = "a: >-\n  folded line\n  two\n"
        self.assertEqual(yamlmini.parse(text), {"a": "folded line two\n"})

    def test_comments_and_blanks(self):
        text = "# top\n\na: 1  # inline\n\n  \nb: two\n"
        self.assertEqual(yamlmini.parse(text), {"a": 1, "b": "two"})

    def test_quoted_keys(self):
        self.assertEqual(yamlmini.parse('"a b": 1\n'), {"a b": 1})


class SchemaTests(unittest.TestCase):
    def test_validate(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string", "pattern": "^[a-z]+$"}, "n": {"type": "integer", "minimum": 2}},
            "additionalProperties": False,
        }
        self.assertEqual(jsonschema_mini.validate({"id": "ok", "n": 3}, schema), [])
        errors = jsonschema_mini.validate({"id": "NO", "n": 1, "x": 1}, schema)
        self.assertTrue(any("pattern" in e for e in errors))
        self.assertTrue(any("minimum" in e for e in errors))
        self.assertTrue(any("unexpected property" in e for e in errors))

    def test_ref(self):
        schema = {
            "$defs": {"entity": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
            "$ref": "#/$defs/entity",
        }
        self.assertEqual(jsonschema_mini.validate({"id": "x"}, schema), [])
        self.assertTrue(jsonschema_mini.validate({"id": 1}, schema))

    def test_enum_oneof(self):
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        self.assertEqual(jsonschema_mini.validate("x", schema), [])
        self.assertTrue(jsonschema_mini.validate([1], schema))


class VersionTests(unittest.TestCase):
    def test_ranges(self):
        self.assertTrue(manifest.version_satisfies("1.2.0", "^1.0.0"))
        self.assertFalse(manifest.version_satisfies("2.0.0", "^1.0.0"))
        self.assertTrue(manifest.version_satisfies("1.2.9", "~1.2.0"))
        self.assertFalse(manifest.version_satisfies("1.3.0", "~1.2.0"))
        self.assertTrue(manifest.version_satisfies("2.4.0", ">=2 <3"))
        self.assertTrue(manifest.version_satisfies("1.0.0", "1"))
        self.assertTrue(manifest.version_satisfies("1.0.0", "*"))
        self.assertTrue(manifest.version_satisfies("0.2.3", "^0.2.0"))
        self.assertFalse(manifest.version_satisfies("0.3.0", "^0.2.0"))


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.packs_root = self.tmp / "packs"
        make_pack(self.packs_root, "typescript-pack", "1.0.0", contexts={"ctx-ts": "category: code-style\n"})
        make_pack(
            self.packs_root,
            "react-pack",
            "1.0.0",
            extra_manifest="extends:\n  - typescript-pack@^1\n",
            contexts={"ctx-react": "category: code-style\n"},
        )
        make_pack(
            self.packs_root,
            "nextjs-pack",
            "1.0.0",
            extra_manifest="extends:\n  - react-pack@^1\n  - typescript-pack@^1\n",
            contexts={"ctx-nextjs": "category: code-style\n"},
        )
        self.registry = Registry(self.packs_root)

    def test_diamond_single_instance(self):
        project = make_project(self.tmp / "proj", ["nextjs-pack@^1"])
        ordered = resolver.resolve(manifest.load_project_declaration(self.tmp / "proj"), self.registry)
        names = [item["name"] for item in ordered]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("typescript-pack", names)
        ts = next(i for i in ordered if i["name"] == "typescript-pack")
        self.assertEqual(ts["precedence"], min(i["precedence"] for i in ordered if i["name"] != "typescript-pack") - 1)
        self.assertEqual(ordered[-1]["name"], "nextjs-pack")

    def test_cycle_detected(self):
        make_pack(
            self.packs_root,
            "a-pack",
            "1.0.0",
            extra_manifest="extends:\n  - b-pack@^1\n",
        )
        make_pack(
            self.packs_root,
            "b-pack",
            "1.0.0",
            extra_manifest="extends:\n  - a-pack@^1\n",
        )
        project = make_project(self.tmp / "cyc", ["a-pack@^1"])
        with self.assertRaises(resolver.ResolutionError):
            resolver.resolve(manifest.load_project_declaration(self.tmp / "cyc"), self.registry)

    def test_empty_extends_resolves_empty(self):
        make_pack(self.packs_root, "typescript-pack", "1.0.0")
        project = make_project(self.tmp / "empty", [])
        ordered = resolver.resolve(manifest.load_project_declaration(self.tmp / "empty"), self.registry)
        self.assertEqual(ordered, [])

    def test_unsatisfiable_range(self):
        project = make_project(self.tmp / "bad", ["react-pack@^2"])
        with self.assertRaises(resolver.ResolutionError):
            resolver.resolve(manifest.load_project_declaration(self.tmp / "bad"), self.registry)


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.packs_root = self.tmp / "packs"
        make_pack(self.packs_root, "typescript-pack", "1.0.0", contexts={"ctx-common": "category: code-style\n"})
        make_pack(
            self.packs_root,
            "base-pack",
            "1.0.0",
            extra_manifest="extends:\n  - typescript-pack@^1\n",
            contexts={
                "ctx-rule": "category: security\nenforcement:\n  mode: warn\n",
                "ctx-base": "category: testing\n",
            },
            pkds={"ai-rules": "rules:\n  - id: ai-one\n    level: must\n    instruction: Do a thing.\n"},
        )
        make_pack(
            self.packs_root,
            "override-pack",
            "1.0.0",
            extra_manifest="extends:\n  - base-pack@^1\n",
            contexts={"ctx-rule": "category: security\nseverity: critical\n"},
        )
        self.registry = Registry(self.packs_root)

    def _resolve_merge(self, extends, overrides="", policy="fail"):
        project = make_project(self.tmp / "p", extends, overrides, policy)
        ordered = resolver.resolve(manifest.load_project_declaration(self.tmp / "p"), self.registry)
        merged = merger.merge(ordered, manifest.load_project_declaration(self.tmp / "p"))
        return merged

    def test_inheritance_replace(self):
        merged = self._resolve_merge(["override-pack@^1"])
        self.assertEqual(merged["contexts"]["ctx-rule"]["severity"], "critical")
        self.assertIn("ctx-base", merged["contexts"])
        self.assertIn("ctx-common", merged["contexts"])

    def test_project_disable(self):
        merged = self._resolve_merge(
            ["override-pack@^1"],
            "overrides:\n  - id: ctx-base\n    action: disable\n    reason: not needed\n",
        )
        self.assertNotIn("ctx-base", merged["contexts"])

    def test_project_patch(self):
        merged = self._resolve_merge(
            ["override-pack@^1"],
            "overrides:\n  - id: ctx-rule\n    action: patch\n    patch:\n      enforcement:\n        mode: block\n",
        )
        self.assertEqual(merged["contexts"]["ctx-rule"]["enforcement"]["mode"], "block")

    def test_project_defer(self):
        merged = self._resolve_merge(
            ["override-pack@^1"],
            "overrides:\n  - id: ctx-rule\n    action: defer\n    reason: during migration\n",
        )
        self.assertEqual(merged["contexts"]["ctx-rule"]["lifecycle"], "draft")

    def test_conflict_fail(self):
        make_pack(self.packs_root, "sibling-a", "1.0.0", contexts={"ctx-dup": "category: a\n"})
        make_pack(self.packs_root, "sibling-b", "1.0.0", contexts={"ctx-dup": "category: b\n"})
        make_pack(
            self.packs_root,
            "combo-pack",
            "1.0.0",
            extra_manifest="extends:\n  - sibling-a@^1\n  - sibling-b@^1\n",
        )
        merged = self._resolve_merge(["combo-pack@^1"])
        statuses = [c["status"] for c in merged["report"]["conflicts"] if c["id"] == "ctx-dup"]
        self.assertTrue(statuses)
        self.assertEqual(statuses[0], "pending")

    def test_hardened_conflict_blocking(self):
        make_pack(
            self.packs_root,
            "hard-a",
            "1.0.0",
            contexts={
                "ctx-h": "category: security\n"
                "governance:\n"
                "  classification: hardened-standard\n"
                "  approval_required: true\n"
            },
        )
        make_pack(self.packs_root, "plain-b", "1.0.0", contexts={"ctx-h": "category: security\n"})
        make_pack(
            self.packs_root,
            "hard-combo",
            "1.0.0",
            extra_manifest="extends:\n  - hard-a@^1\n  - plain-b@^1\n",
        )
        merged = self._resolve_merge(["hard-combo@^1"])
        conflict = next(c for c in merged["report"]["conflicts"] if c["id"] == "ctx-h")
        self.assertTrue(conflict["hardened"])
        self.assertEqual(conflict["status"], "blocking-unresolved")

    def test_resolve_override_unblocks_hardened(self):
        make_pack(
            self.packs_root,
            "hard-a",
            "1.0.0",
            contexts={
                "ctx-h": "category: security\n"
                "governance:\n"
                "  classification: hardened-standard\n"
                "  approval_required: true\n"
            },
        )
        make_pack(self.packs_root, "plain-b", "1.0.0", contexts={"ctx-h": "category: security\n"})
        make_pack(
            self.packs_root,
            "hard-combo",
            "1.0.0",
            extra_manifest="extends:\n  - hard-a@^1\n  - plain-b@^1\n",
        )
        merged = self._resolve_merge(
            ["hard-combo@^1"],
            "overrides:\n  - id: ctx-h\n    action: resolve\n    pack: plain-b\n    reason: explicit choice\n",
        )
        self.assertEqual(merged["contexts"]["ctx-h"]["category"], "security")
        conflict = next(c for c in merged["report"]["conflicts"] if c["id"] == "ctx-h")
        self.assertEqual(conflict["status"], "blocking")

    def test_ai_rules_merged(self):
        merged = self._resolve_merge(["override-pack@^1"])
        self.assertEqual(merged["ai_rules"][0]["id"], "ai-one")


class MaterializeTests(unittest.TestCase):
    def test_materialize_deterministic(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(packs_root, "typescript-pack", "1.0.0", contexts={"ctx-ts": "category: code-style\n"})
        make_pack(
            packs_root,
            "node-pack",
            "1.0.0",
            contexts={"ctx-node": "category: code-style\n"},
            pkds={"tech-stack": "language: typescript\nentries:\n  - name: Node.js\n    role: runtime\n"},
        )
        reg = Registry(packs_root)
        proj = tmp / "proj"
        make_project(proj, ["typescript-pack@^1", "node-pack@^1"])
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        merged = merger.merge(ordered, project)
        lcdd1 = materialize(proj, merged, ordered, project)
        contexts1 = (lcdd1 / "contexts" / "ctx-ts.yaml").read_text(encoding="utf-8")
        md1 = (lcdd1 / "CONTEXT.md").read_text(encoding="utf-8")
        lock1 = json.loads((lcdd1 / "packs.lock.json").read_text(encoding="utf-8"))
        materialize(proj, merged, ordered, project)
        contexts2 = (lcdd1 / "contexts" / "ctx-ts.yaml").read_text(encoding="utf-8")
        md2 = (lcdd1 / "CONTEXT.md").read_text(encoding="utf-8")
        lock2 = json.loads((lcdd1 / "packs.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(contexts1, contexts2)
        self.assertEqual(md1, md2)
        self.assertEqual(lock1["resolved"], lock2["resolved"])
        self.assertEqual(lock1["algorithm"], "sha256")
        self.assertIn("ctx-ts", (lcdd1 / "CONTEXT.md").read_text(encoding="utf-8"))

    def test_materialize_cleans_stale_contexts(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(packs_root, "typescript-pack", "1.0.0", contexts={"ctx-ts": "category: code-style\n"})
        reg = Registry(packs_root)
        proj = tmp / "proj"
        make_project(proj, ["typescript-pack@^1"])
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        merged = merger.merge(ordered, project)
        lcdd = materialize(proj, merged, ordered, project)
        self.assertTrue((lcdd / "contexts" / "ctx-ts.yaml").is_file())
        # Reinstall with the context disabled; the stale file must be removed.
        make_project(
            proj,
            ["typescript-pack@^1"],
            "overrides:\n  - id: ctx-ts\n    action: disable\n    reason: test\n",
        )
        project2 = manifest.load_project_declaration(proj)
        ordered2 = resolver.resolve(project2, reg)
        merged2 = merger.merge(ordered2, project2)
        materialize(proj, merged2, ordered2, project2)
        self.assertFalse((lcdd / "contexts" / "ctx-ts.yaml").exists())
        self.assertEqual(len(list((lcdd / "contexts").glob("*.yaml"))), 0)

    def test_render_context_md(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(packs_root, "typescript-pack", "1.0.0", contexts={"ctx-ts": "category: code-style\n"})
        reg = Registry(packs_root)
        proj = tmp / "proj"
        make_project(proj, ["typescript-pack@^1"])
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        merged = merger.merge(ordered, project)
        md = render_context_md(merged)
        self.assertIn("Living Context", md)
        self.assertIn("ctx-ts", md)


class DoctorTests(unittest.TestCase):
    def test_health_8_metrics_parity(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(
            packs_root,
            "typescript-pack",
            "1.0.0",
            contexts={
                "ctx-ts": (
                    "category: code-style\n"
                    "severity: high\n"
                    "created_at: 2026-08-07T00:00:00Z\n"
                    "updated_at: 2026-08-07T00:00:00Z\n"
                    "tags: [typescript, code-style]\n"
                )
            },
        )
        reg = Registry(packs_root)
        proj = tmp / "proj"
        make_project(proj, ["typescript-pack@^1"])
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        merged = merger.merge(ordered, project)
        lcdd = materialize(proj, merged, ordered, project)
        contexts = {}
        for path in (lcdd / "contexts").glob("*.yaml"):
            data = yamlmini.load_file(path)
            if isinstance(data, dict) and data.get("id"):
                contexts[data["id"]] = data
        report = json.loads((lcdd / "report.json").read_text(encoding="utf-8"))
        health = doctor_engine.compute_health(contexts, report=report, lcdd_dir=lcdd)
        self.assertEqual(health["total_contexts"], 1)
        self.assertEqual(health["max_score"], 100)
        names = [m["name"] for m in health["metrics"]]
        self.assertEqual(
            names,
            [
                "Stale Contexts",
                "Missing Owners",
                "Enforcement Conflicts",
                "Deprecation Backlog",
                "Draft Stagnation",
                "Authority Gaps",
                "Tag Hygiene",
                "Review Backlog",
            ],
        )
        self.assertEqual(health["grade"], "A")
        self.assertGreaterEqual(health["overall_score"], 90)

    def test_health_flags_missing_tags_and_owners(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        make_pack(
            packs_root,
            "typescript-pack",
            "1.0.0",
            contexts={"ctx-untagged": "category: code-style\n"},
        )
        reg = Registry(packs_root)
        proj = tmp / "proj"
        make_project(proj, ["typescript-pack@^1"])
        project = manifest.load_project_declaration(proj)
        ordered = resolver.resolve(project, reg)
        merged = merger.merge(ordered, project)
        lcdd = materialize(proj, merged, ordered, project)
        contexts = {}
        for path in (lcdd / "contexts").glob("*.yaml"):
            data = yamlmini.load_file(path)
            if isinstance(data, dict) and data.get("id"):
                contexts[data["id"]] = data
        health = doctor_engine.compute_health(contexts, report={}, lcdd_dir=lcdd)
        tag_metric = next(m for m in health["metrics"] if m["name"] == "Tag Hygiene")
        self.assertEqual(tag_metric["status"], "warning")
        self.assertIn("ctx-untagged", tag_metric["details"][0])

    def test_patterns_overlap(self):
        self.assertTrue(doctor_engine.patterns_overlap("**/*", "app/**/*.ts"))
        self.assertTrue(doctor_engine.patterns_overlap("**/*.ts", "**/*.tsx"))
        self.assertFalse(doctor_engine.patterns_overlap("app/**/*.ts", "app/**/route.ts"))
        self.assertFalse(doctor_engine.patterns_overlap("app/**/*.ts", "lib/**/*.ts"))
        self.assertTrue(doctor_engine.patterns_overlap("app/**", "app/**/*.ts"))


class PackValidationTests(unittest.TestCase):
    def test_bad_pack_rejected(self):
        tmp = Path(tempfile.mkdtemp())
        packs_root = tmp / "packs"
        dirpath = make_pack(packs_root, "typescript-pack", "1.0.0")
        # corrupt the context: missing required fields
        write(dirpath / "contexts" / "ctx-ts.yaml", "id: ctx-ts\n")
        pack = manifest.load_pack(dirpath)
        errors = []
        for ctx in pack["contexts"]:
            errors.extend(validator.context_errors(ctx))
        self.assertTrue(any("missing required field" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
