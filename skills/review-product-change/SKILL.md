---
name: review-product-change
description: Review a code or product change for specification compliance, correctness, regressions, security, data safety, accessibility, maintainability, and verification quality. Use for pull requests, local diffs, pre-merge reviews, or independent assessment after implementation. Review only unless the user separately asks for fixes.
---

# Review Product Change

Review in two passes: first whether the right product behavior was built, then whether it was built safely and clearly.

## Workflow

1. Read the PRD, task contract, architecture, experience spec, threat model, acceptance criteria, and actual diff.
2. Map changed behavior to requirement IDs. Identify missing, extra, or contradictory scope before code-style concerns.
3. Trace critical paths and boundary failures through UI, server, authorization, data, integrations, and operations.
4. Inspect tests for meaningful behavior, regression coverage, false positives, brittle implementation coupling, and missing failure cases.
5. Review security/privacy controls, migrations, compatibility, responsive/accessibility behavior, performance, observability, and rollback impact proportionally to risk.
6. Run focused checks only when needed to confirm a suspected issue; do not mutate the code during review.
7. Report actionable findings ordered by severity with precise location, impact, evidence, and minimal remediation direction.
8. If no findings exist, state residual untested areas and avoid claiming broader readiness than the evidence supports.

Use [references/review-gate.md](references/review-gate.md) for the two-pass checklist.

## Finding rule

Report defects and material risks, not personal style preferences. Each finding must describe a concrete failing scenario or maintenance hazard introduced by the change.

When HITL artifacts exist, verify that implementation follows accepted `DEC-*` records, pending decisions were not implemented speculatively, human rationales were preserved, and no AI recommendation is represented as approval.
