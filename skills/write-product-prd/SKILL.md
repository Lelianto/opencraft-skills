---
name: write-product-prd
description: Create, refine, or review a build-ready product requirements document from product analysis, research, stakeholder input, or a validated idea. Use when asked for a PRD, product specification, functional requirements, user stories, acceptance criteria, MVP scope, metrics, launch criteria, or a source of truth for design and engineering.
---

# Write Product PRD

Write a decision document that design, engineering, QA, security, data, and operations can execute and verify.

## Workflow

1. Read the product analysis and source evidence. Preserve disagreements and unknowns rather than silently resolving them.
2. Define background, problem, target users, outcome, success metrics, baseline, scope, and non-goals.
3. Describe prioritized user journeys, permissions, business rules, and data lifecycle.
4. Specify observable functional requirements with stable IDs. Avoid dictating implementation unless it is a true constraint.
5. Define non-functional requirements for accessibility, responsive behavior, security, privacy, performance, reliability, compatibility, observability, and localization as applicable.
6. Add acceptance criteria for happy paths and relevant loading, empty, invalid, unauthorized, forbidden, conflict, failure, retry, offline, and recovery states.
7. Define analytics events and success evaluation without collecting unnecessary personal data.
8. Document dependencies, rollout, migration, support, rollback, risks, open questions, and owners.
9. Check that every must-have requirement maps to acceptance evidence and that the MVP is an end-to-end slice.

Use [references/prd-template.md](references/prd-template.md) for the deliverable and [references/prd-quality-gate.md](references/prd-quality-gate.md) before marking it ready.

## Output contract

Produce a concise PRD with version/status, evidence links, numbered requirements, measurable acceptance criteria, explicit non-goals, decisions, assumptions, and unresolved questions. Do not present assumptions as approved requirements.

Before marking the PRD approved, apply `facilitate-product-decision` to unresolved `D2` scope, role, permission, success-measure, data-lifecycle, or rollout choices. List pending decision IDs rather than silently selecting a product direction.
