---
name: ship-web-product
description: Orchestrate an AI-assisted product end to end from product analysis and PRD through architecture, complete platform implementation, responsive web validation, E2E/security/data testing, and deployment readiness. Use when the user asks to build or ship a complete web app, MVP, SaaS platform, website, dashboard, or multi-stage product and wants the agent to own the full delivery loop.
---

# Ship Web Product

Run an evidence-driven idea-to-release loop. Keep artifacts proportional: a small feature may need a short inline brief; a new product may need persisted decisions.

## Workflow

1. Discover local instructions, product context, repository state, runtime, available tools, and authorization boundaries.
2. Select a delivery mode from [references/delivery-modes.md](references/delivery-modes.md), read `.product/human-loop.json` when present, and persist proportional artifacts under `.product/` when the repository uses the provided contract.
3. Apply `analyze-product` to establish evidence, users, opportunity, hypotheses, success measures, and a proceed/research/no-go recommendation.
4. Apply `shape-product` to select the smallest valuable end-to-end scope and expose consequential decisions.
5. Apply `write-product-prd` to create the approved source of truth, traceable requirements, acceptance criteria, quality constraints, metrics, and rollout expectations.
6. Apply `design-product-experience` and `craft-distinctive-product` for information architecture, meaningful visual direction, flows, component states, originality, mobile app-quality behavior, responsiveness, and accessibility when user experience is in scope.
7. Apply `design-web-system` for boundaries, contracts, data lifecycle, identity and access, operations, migrations, and implementation sequence.
8. Apply `threat-model-platform` for trust boundaries, abuse cases, versioned security controls, verification, and residual risk.
9. Apply `plan-product-delivery` to produce traceable vertical slices and bounded tasks. Do not implement while its readiness result is `not ready`.
10. Establish a working baseline. Apply `execute-product-task` and `build-web-feature` one task at a time; use `develop-with-tests` for behavior and `debug-platform` for failures.
11. Validate continuously with focused checks and real browser flows. For websites, verify responsive behavior and accessibility across representative mobile, tablet, and desktop states.
12. Apply `review-product-change` first for specification compliance and then implementation quality.
13. Apply `test-platform` for requirement traceability, E2E journeys, multi-role permissions, security boundaries, privacy, data integrity, migrations, failure recovery, and residual risk.
14. Apply `verify-web-product` as an independent release-quality pass. Fix authorized in-scope defects, then rerun every affected gate.
15. Apply `prepare-deployment` to produce a go/conditional-go/no-go record, exact rollout and smoke-test steps, observability, abort thresholds, backup, and rollback.
16. Execute deployment only when explicitly authorized. After deployment, run smoke tests, inspect health signals, and complete the observation window before claiming operational readiness.
17. Feed production metrics, incidents, and support findings back into product artifacts. Finish with delivered behavior, requirement evidence, release identity, known risks, and the next smallest iteration.

If another named skill is unavailable, read its `SKILL.md` from the same parent skills directory and follow it directly. Do not duplicate its detailed workflow here.

Use [references/delivery-ledger.md](references/delivery-ledger.md) for work spanning multiple phases or sessions.

## Human-loop orchestration

1. Treat missing HITL configuration as legacy-compatible guided judgment: existing safety gates remain mandatory, but do not require files for small work.
2. Classify emerging choices as `D0`–`D3` using `facilitate-product-decision`.
3. Before pausing, store a resume checkpoint with the current stage, next bounded action, intended skill, and task ID when available.
4. Set state to `DECISION_REQUIRED` for gated `D2`, `APPROVAL_REQUIRED` for `D3`, and `BLOCKED` when no safe option can proceed.
5. Stop after presenting a complete decision brief. Do not continue dependent implementation in the same turn.
6. Resume only after the decision record is resolved and the state is `READY_TO_RESUME`; reread affected artifacts because a decision may invalidate prior plans.
7. Set `VERIFICATION_REQUIRED` after implementation and `COMPLETE` only when required evidence and release claims are current.

Supported states are `IN_PROGRESS`, `DECISION_REQUIRED`, `APPROVAL_REQUIRED`, `BLOCKED`, `READY_TO_RESUME`, `VERIFICATION_REQUIRED`, and `COMPLETE`.

## Control points

- Treat phase gates as evidence checkpoints, not document ceremonies. A small product may keep artifacts concise, but must preserve their decisions and verification.
- Ask for a decision only when options materially change scope, irreversible architecture, external cost, production data, risk acceptance, or external state.
- Never deploy, purchase, message, delete, or mutate production without explicit authority.
- Keep facts, assumptions, decisions, and evidence distinguishable.
- Prefer a smaller working product with verified behavior over a broad scaffold of placeholders.
- Treat user-visible completion and operational readiness as separate claims.
