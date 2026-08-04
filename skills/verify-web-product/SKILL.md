---
name: verify-web-product
description: Verify a web application, feature, pull request, or release candidate for functional correctness, regressions, accessibility, responsive UX, security, privacy, performance, observability, and deployment readiness. Use for QA, pre-release checks, code review, bug reproduction, release gates, or when asked whether a web change is truly done.
---

# Verify Web Product

Produce evidence, not reassurance. Review is read-only unless the user also asks for fixes.

## Workflow

1. Read acceptance criteria, repository instructions, changed files, and the actual diff. Identify the highest-risk user journeys and boundaries.
2. Discover repository-provided commands. Run the smallest relevant tests first, then required lint, types, broader tests, and production build.
3. Exercise critical flows through the real app when feasible. Include loading, empty, invalid, unauthorized, failure/retry, success, refresh, and back/forward behavior as relevant.
4. Inspect representative mobile and desktop layouts, keyboard operation, focus, labels, semantics, contrast, zoom/reflow, and reduced motion.
5. Trace untrusted data through validation, authorization, output encoding, storage, logs, redirects, uploads, and external requests.
6. Check request volume, payload size, render churn, query patterns, caching, bundle impact, and slow/failure behavior proportionally to risk.
7. Verify migration safety, configuration, health signals, rollback, and feature controls for release-impacting changes.
8. Report findings ordered by severity, with precise location, user impact, reproduction/evidence, and a minimal remediation direction.

Use [references/release-gates.md](references/release-gates.md) for release candidates. Use [references/finding-format.md](references/finding-format.md) when writing review findings.

## Rules

- Distinguish verified facts, inferences, and untested areas.
- Do not mark a gate passed when its command did not run or the environment prevented meaningful coverage.
- Do not report theoretical style preferences as defects.
- Prioritize exploitable security issues, data loss, broken primary journeys, and regressions over polish.
- If no actionable findings exist, say so and list residual test gaps.
- Treat unresolved `D2` or `D3` decisions, inconsistent human-loop state, implementation that contradicts accepted decisions, or missing production/risk authority as release blockers. Report them by `DEC-*` ID.
