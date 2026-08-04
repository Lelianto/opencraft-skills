---
name: shape-product
description: Turn an ambiguous product idea, customer problem, feature request, or MVP concept into a small build-ready product brief with outcomes, users, journeys, requirements, risks, and acceptance criteria. Use before implementation when scope is unclear, when creating a PRD or user stories, or when deciding what belongs in a web product release.
---

# Shape Product

Convert intent into the smallest coherent, testable product slice.

## Workflow

1. Inspect repository context, existing behavior, issues, designs, and constraints before proposing scope.
2. State known facts, assumptions, and unresolved decisions separately. Ask only about decisions that would materially change the build; otherwise make and label a reversible assumption.
3. Define the target user, problem, current alternative, desired outcome, and observable success signal.
4. Describe the primary happy path and the highest-value failure or empty states.
5. Split scope into `must`, `later`, and `out`. Prefer one end-to-end vertical slice over many partial capabilities.
6. Write requirements as observable behavior, not implementation choices.
7. Add acceptance criteria covering permissions, validation, loading, empty, error, retry, responsive, and accessibility behavior where relevant.
8. Identify privacy, security, legal, migration, operational, and dependency risks. Do not invent facts about customers or systems.
9. End with a build sequence whose first increment is demonstrable.

Use [references/product-brief.md](references/product-brief.md) when producing a formal build brief.

## Output contract

Return or create a concise artifact containing:

- outcome and success signals;
- target user and core job;
- scope and non-goals;
- user journey;
- functional and quality requirements;
- acceptance criteria;
- assumptions, decisions, and risks;
- thin-slice delivery plan.

Do not begin implementation unless the user asked for it. Preserve explicit product decisions in the repository's established documentation location.

When MVP boundaries, target users, success measures, or consequential non-goals remain unresolved, apply `facilitate-product-decision`. In guided mode, pause dependent PRD or implementation work until each `D2` choice is recorded.
