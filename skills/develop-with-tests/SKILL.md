---
name: develop-with-tests
description: Implement or change software behavior using a risk-proportional red-green-refactor loop with regression evidence. Use for feature development, bug fixes, domain rules, APIs, data behavior, and critical UI interactions when tests can demonstrate the intended behavior.
---

# Develop With Tests

Make behavior observable before relying on implementation claims.

## Workflow

1. Select the narrowest observable behavior from the requirement and choose the lowest test level that proves it without excessive mocking.
2. Write or identify a test that fails for the intended reason. Run it and read the failure.
3. Implement the minimum production behavior needed to pass.
4. Run the focused test and confirm it passes for the expected reason.
5. Refactor only while tests remain green; remove duplication without broadening scope.
6. Add boundary cases proportional to risk: invalid input, permissions, concurrency, failure/retry, data integrity, accessibility, or responsive interaction.
7. Run adjacent and repository-required checks before completion.

Use [references/test-selection.md](references/test-selection.md) when choosing test level or handling hard-to-test behavior.

## Guardrails

- Do not write an implementation and then create a test that merely mirrors it.
- Do not mock the unit under test or assert private implementation details.
- Do not delete or weaken a legitimate test to obtain green output.
- For visual, exploratory, infrastructure, or disposable prototype work where test-first is impractical, state the exception and define alternative evidence before implementation.
