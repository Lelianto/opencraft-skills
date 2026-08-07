#!/usr/bin/env python3
"""OpenCraft Context Packs CLI (Python, zero-dependency).

Usage:
  packtool.py packs <command> [options]

Commands: init, add, remove, install, update, list, status, doctor,
resolve, validate, verify, lock, create, publish
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packlib import (  # noqa: E402
    manifest,
    merger,
    materialize,
    registry,
    resolver,
    validator,
)
from packlib.manifest import PackError, parse_ref  # noqa: E402
from packlib.registry import Registry, pack_integrity  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS_ROOT = REPO_ROOT / "packs"
SCHEMA_URL = "https://opencraft.dev/schema/project-packs/v1"


def out_json(payload):
    print(json.dumps(payload, indent=2, sort_keys=True))


def project_path(value):
    return Path(value or os.getcwd()).resolve()


def load_or_init(project: Path):
    declaration = {"schema": SCHEMA_URL, "extends": []}
    packs_yaml = project / "packs.yaml"
    if packs_yaml.is_file():
        data = manifest.load_project_declaration(project)
        declaration = dict(data)
    else:
        declaration["conflict_policy"] = "fail"
    return declaration, packs_yaml


def write_declaration(project: Path, declaration):
    from packlib import yamlmini

    (project / "packs.yaml").write_text(yamlmini.dump(declaration), encoding="utf-8")


def build_registry():
    cache = Path.home() / ".opencraft" / "packs"
    return Registry(PACKS_ROOT, cache_dir=cache)


def run_pipeline(project_dir, force=False):
    """Resolve + merge + validate. Returns a dict with the full result."""
    project = manifest.load_project_declaration(project_dir)
    store = validator.load_schema_store(REPO_ROOT)
    errors = validator.validate_project(project, store)
    if errors:
        return {"ok": False, "errors": errors}

    reg = build_registry()
    ordered = resolver.resolve(project, reg)

    replace_map = {}
    for ov in project.get("overrides", []):
        if ov.get("action") == "replace" and ov.get("path"):
            target = Path(project_dir) / ov["path"]
            if not target.is_file():
                return {"ok": False, "errors": [f"override replace source not found: {target}"]}
            data = load_yaml(target)
            if not isinstance(data, dict) or not data.get("id"):
                return {"ok": False, "errors": [f"replace source {target} is not a valid context"]}
            replace_map[data["id"]] = data
    for item in ordered:
        for ov in item["pack"]["manifest"].get("override", []):
            if ov.get("action") == "replace" and ov.get("path"):
                target = Path(item["pack"]["dir"]) / ov["path"]
                if not target.is_file():
                    return {"ok": False, "errors": [f"override replace source not found: {target}"]}
                data = load_yaml(target)
                if isinstance(data, dict) and data.get("id"):
                    replace_map[data["id"]] = data

    merged = merger.merge(ordered, project, replace_map=replace_map)
    validation_errors, blocking = validator.validate_effective(merged, ordered, project, store)
    lock_integrity = {item["name"]: pack_integrity(Path(item["pack"]["dir"])) for item in ordered}

    return {
        "ok": not validation_errors,
        "ordered": ordered,
        "merged": merged,
        "project": project,
        "errors": validation_errors,
        "blocking": blocking,
        "lock_integrity": lock_integrity,
        "store": store,
    }


def load_yaml(path):
    from packlib import yamlmini

    return yamlmini.load_file(path)


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------


def cmd_init(project, argv):
    declaration = {"schema": SCHEMA_URL, "extends": [], "conflict_policy": "fail"}
    for ref in argv:
        name, spec = parse_ref(ref)
        declaration["extends"].append(f"{name}@{spec}" if spec != "*" else name)
    write_declaration(project, declaration)
    (project / ".lcdd" / "contexts").mkdir(parents=True, exist_ok=True)
    print(f"OK   {project / 'packs.yaml'}")
    print("OK   .lcdd/ initialized")


def cmd_add(project, argv, json_out):
    if not argv:
        raise PackError("usage: packs add <name[@range]>")
    declaration, _ = load_or_init(project)
    name, spec = parse_ref(argv[0])
    ref = f"{name}@{spec}" if spec != "*" else name
    existing = declaration.get("extends", [])
    existing_names = {parse_ref(r)[0] for r in existing}
    if name in existing_names:
        raise PackError(f"{name} is already declared")
    existing.append(ref)
    declaration["extends"] = existing
    write_declaration(project, declaration)
    if json_out:
        out_json({"ok": True, "added": ref})
    else:
        print(f"OK   added {ref}")


def cmd_remove(project, argv, json_out):
    if not argv:
        raise PackError("usage: packs remove <name>")
    declaration, _ = load_or_init(project)
    name = argv[0]
    remaining = [r for r in declaration.get("extends", []) if parse_ref(r)[0] != name]
    if len(remaining) == len(declaration.get("extends", [])):
        raise PackError(f"{name} is not declared")
    declaration["extends"] = remaining
    write_declaration(project, declaration)
    if json_out:
        out_json({"ok": True, "removed": name})
    else:
        print(f"OK   removed {name}")


def cmd_install(project, argv, json_out):
    force = "--force" in argv
    resolve_arg = None
    for index, token in enumerate(argv):
        if token == "--resolve":
            if index + 2 < len(argv):
                resolve_arg = (argv[index + 1], argv[index + 2])
    result = run_pipeline(project, force=force)
    if not result["ok"]:
        payload = {"ok": False, "errors": result["errors"], "conflicts": result["merged"]["report"]["conflicts"]}
        if json_out:
            out_json(payload)
        else:
            for error in result["errors"]:
                print(f"ERROR {error}")
        return 1

    lcdd = materialize.materialize(
        project, result["merged"], result["ordered"], result["project"], lock_integrity=result["lock_integrity"]
    )
    payload = {
        "ok": True,
        "lcdd": str(lcdd),
        "packs": [{"name": i["name"], "version": i["version"], "precedence": i["precedence"]} for i in result["ordered"]],
        "contexts": sorted(result["merged"]["contexts"]),
        "conflicts": result["merged"]["report"]["conflicts"],
    }
    if json_out:
        out_json(payload)
    else:
        print(f"OK   materialized {len(result['merged']['contexts'])} contexts into {lcdd}")
        for item in result["ordered"]:
            print(f"  - {item['name']}@{item['version']} (precedence {item['precedence']})")
        for conflict in result["merged"]["report"]["conflicts"]:
            print(f"WARN conflict {conflict['id']}: {', '.join(conflict['packs'])}")
    return 0


def cmd_update(project, argv, json_out):
    return cmd_install(project, ["--force"], json_out)


def cmd_list(project, argv, json_out):
    declaration, _ = load_or_init(project)
    reg = build_registry()
    rows = []
    for ref in declaration.get("extends", []):
        name, spec = parse_ref(ref)
        available = sorted(reg.versions(name))
        latest = available[-1] if available else None
        rows.append({"ref": ref, "name": name, "range": spec, "latest": latest, "available": available})
    if json_out:
        out_json({"declared": rows})
    else:
        for row in rows:
            print(f"{row['name']} {row['range']} -> latest {row['latest']}")
    return 0


def cmd_status(project, argv, json_out):
    result = run_pipeline(project)
    payload = {
        "ok": result["ok"],
        "packs": [{"name": i["name"], "version": i["version"], "precedence": i["precedence"]} for i in result["ordered"]],
        "contexts": sorted(result["merged"]["contexts"]),
        "knowledge": sorted(result["merged"]["knowledge"]),
        "conflicts": result["merged"]["report"]["conflicts"],
        "errors": result["errors"],
    }
    if json_out:
        out_json(payload)
    else:
        for item in result["ordered"]:
            print(f"{item['name']}@{item['version']} (precedence {item['precedence']})")
        print(f"contexts: {len(result['merged']['contexts'])}  knowledge: {sorted(result['merged']['knowledge'])}")
        for conflict in result["merged"]["report"]["conflicts"]:
            print(f"conflict {conflict['id']}: {'blocking-unresolved' if conflict['status'] == 'blocking-unresolved' else conflict['status']}")
    return 0


def cmd_doctor(project, argv, json_out):
    lcdd = project / ".lcdd"
    if not (lcdd / "contexts").is_dir():
        if json_out:
            out_json({"ok": False, "error": "no .lcdd installed"})
        else:
            print("ERROR no .lcdd installed")
        return 1
    from packlib import yamlmini

    contexts = {}
    for path in (lcdd / "contexts").glob("*.yaml"):
        data = yamlmini.load_file(path)
        if isinstance(data, dict) and data.get("id"):
            contexts[data["id"]] = data
    report = {}
    if (lcdd / "report.json").is_file():
        report = json.loads((lcdd / "report.json").read_text(encoding="utf-8"))

    missing_owners = [cid for cid, ctx in contexts.items() if not ctx.get("owner")]
    no_metadata = [cid for cid, ctx in contexts.items() if not ctx.get("updated_at")]
    deprecation_backlog = [cid for cid, ctx in contexts.items() if ctx.get("lifecycle") == "deprecated"]
    unresolved = [c["id"] for c in report.get("conflicts", []) if c.get("status") == "blocking-unresolved"]

    score = 100
    score -= 10 * min(10, len(missing_owners))
    score -= 10 * min(10, len(unresolved))
    health = {
        "ok": score >= 70 and not unresolved,
        "score": max(0, score),
        "contexts": len(contexts),
        "missing_owners": missing_owners,
        "untracked_updated_at": no_metadata,
        "deprecation_backlog": deprecation_backlog,
        "unresolved_conflicts": unresolved,
    }
    if json_out:
        out_json(health)
    else:
        print(f"Context Health: {health['score']}/100")
        print(f"contexts: {health['contexts']}")
        for cid in missing_owners:
            print(f"  missing owner: {cid}")
        for cid in unresolved:
            print(f"  unresolved conflict: {cid}")
    return 0 if health["ok"] else 1


def cmd_resolve_dryrun(project, argv, json_out):
    result = run_pipeline(project)
    graph = []
    for item in result["ordered"]:
        graph.append(
            {
                "name": item["name"],
                "version": item["version"],
                "precedence": item["precedence"],
                "extends": list(item["pack"]["manifest"].get("extends", [])),
                "dependencies": list(item["pack"]["manifest"].get("dependencies", [])),
            }
        )
    payload = {"ok": result["ok"], "graph": graph, "conflicts": result["merged"]["report"]["conflicts"], "errors": result["errors"]}
    if json_out:
        out_json(payload)
    else:
        for item in sorted(graph, key=lambda g: g["precedence"]):
            print(f"{item['precedence']:>3}  {item['name']}@{item['version']}")
        for conflict in result["merged"]["report"]["conflicts"]:
            print(f"conflict {conflict['id']}: {', '.join(conflict['packs'])} ({conflict['status']})")
    return 0


def cmd_validate(project, argv, json_out):
    store = validator.load_schema_store(REPO_ROOT)
    target = None
    all_packs = "--all" in argv
    for token in argv:
        if not token.startswith("--"):
            target = token
    if all_packs or target is None:
        failures = []
        reg = build_registry()
        pack_names = sorted(p for p in PACKS_ROOT.iterdir() if (p / "pack.yaml").is_file())
        for pack_dir in pack_names:
            pack = manifest.load_pack(pack_dir)
            errors, warnings = validator.validate_pack(pack, store)
            for ref in pack["manifest"].get("extends", []) + pack["manifest"].get("dependencies", []):
                name, _ = parse_ref(ref)
                if not reg.versions(name):
                    errors.append(f"extends/dependency references unknown pack {name}")
            for warning in warnings:
                print(f"WARN {pack['name']}: {warning}")
            if errors:
                failures.append({"pack": pack["name"], "errors": errors})
                print(f"FAIL {pack['name']}")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"PASS {pack['name']}")
        if json_out:
            out_json({"ok": not failures, "failures": failures})
        return 0 if not failures else 1
    pack_dir = PACKS_ROOT / target
    if not (pack_dir / "pack.yaml").is_file():
        print(f"ERROR unknown pack {target}")
        return 1
    pack = manifest.load_pack(pack_dir)
    errors, warnings = validator.validate_pack(pack, store)
    for warning in warnings:
        print(f"WARN {target}: {warning}")
    if json_out:
        out_json({"ok": not errors, "errors": errors})
    else:
        if errors:
            print(f"FAIL {target}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {target}")
    return 0 if not errors else 1


def cmd_verify(project, argv, json_out):
    lock_path = REPO_ROOT / "packs.lock.json"
    if not lock_path.is_file():
        if json_out:
            out_json({"ok": False, "error": "no packs.lock.json"})
        else:
            print("ERROR no packs.lock.json")
        return 1
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    mismatches = []
    for name, expected in lock.get("packs", {}).items():
        pack_dir = PACKS_ROOT / name
        if not (pack_dir / "pack.yaml").is_file():
            mismatches.append({"name": name, "error": "missing"})
            continue
        actual = pack_integrity(pack_dir)
        if actual != expected.get("integrity"):
            mismatches.append({"name": name, "error": "integrity mismatch"})
    if json_out:
        out_json({"ok": not mismatches, "mismatches": mismatches})
    else:
        print("OK integrity verified" if not mismatches else "FAIL integrity mismatch")
        for mismatch in mismatches:
            print(f"  - {mismatch['name']}: {mismatch['error']}")
    return 0 if not mismatches else 1


def cmd_lock(project, argv, json_out):
    result = run_pipeline(project)
    lock = {
        "schema": "https://opencraft.dev/schema/packs.lock/v1",
        "algorithm": "sha256",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved": [],
    }
    for item in result["ordered"]:
        manifest_data = item["pack"]["manifest"]
        lock["resolved"].append(
            {
                "name": item["name"],
                "version": item["version"],
                "integrity": pack_integrity(Path(item["pack"]["dir"])),
                "precedence": item["precedence"],
                "extends": list(manifest_data.get("extends", [])),
                "dependencies": list(manifest_data.get("dependencies", [])),
            }
        )
    lcdd = project / ".lcdd"
    lcdd.mkdir(parents=True, exist_ok=True)
    (lcdd / "packs.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if json_out:
        out_json({"ok": True, "resolved": len(lock["resolved"])})
    else:
        print(f"OK wrote lock for {len(lock['resolved'])} packs")
    return 0


def cmd_create(project, argv, json_out):
    if not argv:
        raise PackError("usage: packs create <name> [--type T] [--dir OUT]")
    name = argv[0]
    if not name.endswith("-pack"):
        raise PackError("pack name must end with '-pack'")
    pack_type = "technology"
    if "--type" in argv:
        pack_type = argv[argv.index("--type") + 1]
    out_dir = Path(project)
    if "--dir" in argv:
        out_dir = Path(argv[argv.index("--dir") + 1])
    target = out_dir / name
    if target.exists():
        raise PackError(f"{target} already exists")
    (target / "contexts").mkdir(parents=True)
    (target / "project").mkdir()
    (target / "ai").mkdir()
    (target / "evals").mkdir()
    (target / "pack.yaml").write_text(
        "schema: https://opencraft.dev/schema/context-pack/v1\n"
        f"name: {name}\n"
        "version: 0.1.0\n"
        f"type: {pack_type}\n"
        f"description: Living context for {name}.\n"
        "license: MIT\n"
        "author:\n"
        "  type: organization\n"
        "  id: opencraft\n"
        "  name: OpenCraft\n"
        "extends: []\n"
        "dependencies: []\n"
        "lifecycle: draft\n"
        "governance:\n"
        "  classification: local-standard\n"
        "  approval_required: false\n"
        "owner:\n"
        "  type: organization\n"
        "  id: opencraft\n"
        "  name: OpenCraft\n",
        encoding="utf-8",
    )
    cid = "ctx-" + name.replace("-pack", "").replace("-", "-") + "-rule"
    (target / "contexts" / f"{cid}.yaml").write_text(
        "id: " + cid + "\n"
        "version: 1\n"
        "title: Describe the rule enforced by this context\n"
        "description: >\n"
        "  Describe the constraint, why it exists, and how it is enforced.\n"
        "source:\n"
        "  type: organization\n"
        "  uri: https://github.com/Lelianto/opencraft-skills\n"
        "authority:\n"
        "  source:\n"
        "    type: organization\n"
        "    id: opencraft\n"
        "    name: OpenCraft\n"
        "  level: 2\n"
        "category: code-style\n"
        "lifecycle: draft\n"
        "governance:\n"
        "  classification: local-standard\n"
        "  approval_required: false\n"
        "owner: opencraft\n"
        "metadata:\n"
        f"  pack: {name}\n",
        encoding="utf-8",
    )
    (target / "project" / "ai-rules.yaml").write_text(
        "kind: ai-rules\n"
        f"pack: {name}\n"
        "rules:\n"
        f"  - id: ai-{name.replace('-pack', '')}-baseline\n"
        "    level: should\n"
        "    instruction: Follow the conventions declared by this pack.\n"
        "    rationale: Consistent output across agents and sessions.\n",
        encoding="utf-8",
    )
    (target / "ai" / "AGENTS.md").write_text(f"# {name}\n\nFollow the conventions declared in this pack.\n", encoding="utf-8")
    (target / "evals" / "cases.yaml").write_text(
        "positive:\n"
        "  - Describe a task relevant to this pack.\n"
        "negative:\n"
        "  - Describe an unrelated task.\n"
        "assertions: []\n",
        encoding="utf-8",
    )
    (target / "README.md").write_text(f"# {name}\n\nLiving context for projects using {name}.\n", encoding="utf-8")
    print(f"OK   scaffolded {target}")
    return 0


def cmd_publish(project, argv, json_out):
    dry_run = "--dry-run" not in argv
    if not argv:
        raise PackError("usage: packs publish <name>")
    name = argv[0]
    pack_dir = PACKS_ROOT / name
    if not (pack_dir / "pack.yaml").is_file():
        raise PackError(f"unknown pack {name}")
    store = validator.load_schema_store(REPO_ROOT)
    pack = manifest.load_pack(pack_dir)
    errors, _ = validator.validate_pack(pack, store)
    if errors:
        raise PackError(f"pack {name} failed validation: {'; '.join(errors[:5])}")
    payload = {
        "ok": True,
        "name": name,
        "npm": f"@opencraft/{name}",
        "version": pack["manifest"]["version"],
        "integrity": pack_integrity(pack_dir),
        "dry_run": dry_run,
        "note": "Automated publishing is handled by the CI workflow (npm Trusted Publishing).",
    }
    if json_out:
        out_json(payload)
    else:
        print(f"publish {name}@{pack['manifest']['version']} -> @opencraft/{name}")
        print(f"  integrity {payload['integrity']}")
    return 0


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------


def usage():
    print("OpenCraft Context Packs CLI")
    print("")
    print("Usage: packtool.py packs <command> [options]")
    print("")
    print("Commands:")
    print("  init                  Create packs.yaml + .lcdd/ skeleton")
    print("  add <name[@range]>    Declare a pack")
    print("  remove <name>         Remove a declared pack")
    print("  install               Resolve, merge, validate, materialize")
    print("  update                Re-resolve and re-materialize")
    print("  list                  List declared packs")
    print("  status                Show effective context")
    print("  doctor                Context health report")
    print("  resolve --dry-run     Show resolved graph and conflicts")
    print("  validate [name|--all] Validate pack(s)")
    print("  verify                Integrity-check packs.lock.json")
    print("  lock                  Regenerate the lockfile")
    print("  create <name>         Scaffold a new pack")
    print("  publish <name>        Prepare a pack for publication")
    print("")
    print("Options: --project <dir>  --json  --force  --dry-run")


def main(argv):
    if not argv or argv[0] in ("--help", "-h", "help"):
        usage()
        return 0
    if argv[0] != "packs":
        print(f"ERROR unknown command group {argv[0]!r}")
        return 2
    command = argv[1] if len(argv) > 1 else "help"
    json_out = "--json" in argv
    project_value = None
    for index, token in enumerate(argv):
        if token == "--project" and index + 1 < len(argv):
            project_value = argv[index + 1]
    project = project_path(project_value)
    command_argv = []
    skip_next = False
    for token in argv[2:]:
        if skip_next:
            skip_next = False
            continue
        if token == "--project":
            skip_next = True
            continue
        if token == "--json":
            continue
        command_argv.append(token)
    try:
        handlers = {
            "init": lambda: cmd_init(project, command_argv),
            "add": lambda: cmd_add(project, command_argv, json_out),
            "remove": lambda: cmd_remove(project, command_argv, json_out),
            "install": lambda: cmd_install(project, command_argv, json_out),
            "update": lambda: cmd_update(project, command_argv, json_out),
            "list": lambda: cmd_list(project, command_argv, json_out),
            "status": lambda: cmd_status(project, command_argv, json_out),
            "doctor": lambda: cmd_doctor(project, command_argv, json_out),
            "resolve": lambda: cmd_resolve_dryrun(project, command_argv, json_out),
            "validate": lambda: cmd_validate(project, command_argv, json_out),
            "verify": lambda: cmd_verify(project, command_argv, json_out),
            "lock": lambda: cmd_lock(project, command_argv, json_out),
            "create": lambda: cmd_create(project, command_argv, json_out),
            "publish": lambda: cmd_publish(project, command_argv, json_out),
        }
        if command in ("help",):
            usage()
            return 0
        return handlers[command]()
    except (PackError, ValueError, KeyError) as error:
        print(f"ERROR {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
