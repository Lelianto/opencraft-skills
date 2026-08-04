#!/usr/bin/env python3
"""Validate skill trigger fixtures and optionally grade captured outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


def load_cases(path: Path) -> dict[str, dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evals/cases.json must be an object keyed by skill name")
    return data


def validate_case(name: str, case: dict[str, object]) -> list[str]:
    errors: list[str] = []
    expected_counts = {"should_trigger": 3, "should_not_trigger": 2, "ambiguous": 1}
    for field, minimum in expected_counts.items():
        prompts = case.get(field)
        if not isinstance(prompts, list) or len(prompts) < minimum:
            errors.append(f"{name}: {field} requires at least {minimum} prompts")
        elif any(not isinstance(prompt, str) or len(prompt.strip()) < 12 for prompt in prompts):
            errors.append(f"{name}: {field} contains an invalid prompt")
    assertions = case.get("assertions")
    if not isinstance(assertions, list) or len(assertions) < 2:
        errors.append(f"{name}: requires at least two output assertions")
    elif any(not isinstance(item, str) or not item.strip() for item in assertions):
        errors.append(f"{name}: assertions must be non-empty strings")
    scenario = case.get("scenario")
    if not isinstance(scenario, str) or len(scenario.strip()) < 20:
        errors.append(f"{name}: requires one realistic end-to-end scenario")
    return errors


def score_output(case: dict[str, object], output: str) -> tuple[int, list[dict[str, object]]]:
    results: list[dict[str, object]] = []
    passed = 0
    for assertion in case["assertions"]:
        matched = bool(re.search(str(assertion), output, flags=re.IGNORECASE | re.MULTILINE))
        passed += int(matched)
        results.append({"assertion": assertion, "passed": matched})
    return passed, results


def benchmark_runs(cases: dict[str, dict[str, object]], run_root: Path) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    records: dict[str, object] = {}
    total_with = 0
    total_without = 0
    total_assertions = 0
    for name, case in cases.items():
        variants: dict[str, object] = {}
        for variant in ("with-skill", "without-skill"):
            output_path = run_root / variant / f"{name}.md"
            if not output_path.is_file():
                errors.append(f"{name}: missing captured output {output_path}")
                continue
            passed, assertions = score_output(case, output_path.read_text(encoding="utf-8"))
            variants[variant] = {"passed": passed, "assertions": assertions}
            if variant == "with-skill":
                total_with += passed
            else:
                total_without += passed
        total_assertions += len(case["assertions"])
        records[name] = variants
    summary = {
        "skills": len(cases),
        "assertions_per_variant": total_assertions,
        "with_skill_passed": total_with,
        "without_skill_passed": total_without,
        "skill_delta": total_with - total_without,
    }
    return errors, {"summary": summary, "results": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, help="Directory containing with-skill/ and without-skill/ outputs")
    parser.add_argument("--benchmark", type=Path, help="Write benchmark JSON; requires --runs")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    cases = load_cases(repository / "evals/cases.json")
    skill_names = {path.name for path in (repository / "skills").iterdir() if (path / "SKILL.md").is_file()}
    errors: list[str] = []
    if set(cases) != skill_names:
        errors.append(f"eval coverage mismatch: missing={sorted(skill_names - set(cases))}, extra={sorted(set(cases) - skill_names)}")
    for name, case in cases.items():
        errors.extend(validate_case(name, case))
    benchmark: dict[str, object] | None = None
    if args.benchmark and not args.runs:
        errors.append("--benchmark requires --runs")
    if args.runs:
        run_errors, benchmark = benchmark_runs(cases, args.runs)
        errors.extend(run_errors)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"PASS {len(cases)} skill eval fixtures")
    if benchmark is not None:
        if args.benchmark:
            args.benchmark.write_text(json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"WROTE {args.benchmark}")
        print(json.dumps(benchmark["summary"], sort_keys=True))
    else:
        print("INFO trigger prompts require a compatible agent harness; use --runs to compare captured outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
