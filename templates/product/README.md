# Product artifacts

This directory is the persistent intent and evidence layer for AI-assisted delivery.

- `constitution.md`: durable project principles and exception rules.
- `product-analysis.md`: evidence, opportunity, and recommendation.
- `prd.md`: approved requirements and acceptance criteria.
- `experience.md`: user flows, interaction states, responsiveness, and accessibility.
- `architecture.md`: boundaries, contracts, data, and operational decisions.
- `threat-model.md`: threats, versioned controls, verification, and residual risk.
- `delivery-plan.md`: vertical slices and bounded tasks.
- `traceability.yaml`: requirement-to-release links.
- `test-evidence.md`: executed checks and results.
- `human-loop.json`: opt-in decision mode and level policy.
- `human-loop-state.json`: resumable orchestration state and active decision IDs.
- `decisions/`: durable human decisions, alternatives, consequences, and authority.
- `schemas/`: machine-readable validation contracts for HITL records.
- `releases/<version>/deployment-readiness.md`: immutable release readiness record.

Use stable IDs: `REQ`, `EXP`, `ARCH`, `TASK`, `THREAT`, `CTRL`, `TEST`, and `RISK`. Do not recycle identifiers after they are referenced.
