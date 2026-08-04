---
name: plan-product-delivery
description: Convert an approved PRD, experience design, and architecture into an executable delivery plan of traceable vertical slices, tasks, dependencies, risks, and verification commands. Use after solution design and before implementation, when breaking an MVP or feature into work, checking implementation readiness, or recovering an unbounded plan.
---

# Plan Product Delivery

Create the smallest ordered task graph that can produce demonstrable value safely.

## Workflow

1. Read product artifacts and repository conventions. Reject planning against conflicting or materially incomplete requirements.
2. Map each must-have requirement to architecture, experience states, security controls, data changes, and acceptance evidence.
3. Identify dependency order, irreversible decisions, external prerequisites, migrations, and high-risk unknowns.
4. Divide work into vertical slices that cross required UI, server, data, and test boundaries. Avoid layer-only milestones unless they unblock multiple slices.
5. Define bounded tasks with stable IDs, preconditions, exact scope, likely files or components, required tests, verification commands, and completion evidence.
6. Put discovery spikes before dependent implementation and time-box them around a decision.
7. Add rollout, documentation, observability, and cleanup tasks; do not hide them inside a final catch-all task.
8. Run the readiness gate and classify `ready`, `ready with concerns`, or `not ready`.

Use [references/delivery-plan.md](references/delivery-plan.md) for the artifact and [references/readiness-gate.md](references/readiness-gate.md) before implementation.

## Rules

- Keep one task independently reviewable and usually completable in one focused agent session.
- Reference requirement IDs rather than paraphrasing them.
- Do not mark tasks complete in this skill; execution owns status and evidence.
- Prefer explicit dependencies over implied ordering.
- Mark readiness `not ready` when a blocking `D2` or `D3` decision is pending. Apply `facilitate-product-decision`, link its `DEC-*` ID from dependent tasks, and do not plan around an invented answer.
