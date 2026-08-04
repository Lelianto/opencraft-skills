---
name: debug-platform
description: Diagnose and fix bugs, failing tests, build failures, performance regressions, integration failures, and unexpected platform behavior through reproducible root-cause analysis. Use before proposing a fix whenever a web or software system behaves incorrectly, especially after prior fixes failed or multiple components are involved.
---

# Debug Platform

Find the root cause before changing behavior.

## Workflow

1. Capture the exact symptom, expected behavior, environment, inputs, logs, stack trace, and first known occurrence.
2. Reproduce consistently with the smallest reliable case. If intermittent, gather timing and state evidence instead of guessing.
3. Inspect recent changes and trace data/control flow backward across component boundaries.
4. State one falsifiable root-cause hypothesis and the evidence supporting it.
5. Test the hypothesis with the smallest diagnostic change or observation; vary one factor at a time.
6. If rejected, record the result and form a new hypothesis. After three failed fix attempts, stop and reassess the architecture with the user.
7. Add a failing regression test or deterministic reproduction before the fix when feasible.
8. Implement one root-cause fix without unrelated cleanup.
9. Verify the original symptom, regression test, adjacent behavior, and relevant broader checks with fresh output.
10. Remove temporary diagnostics or convert useful signals into production-safe observability.

Use [references/debug-record.md](references/debug-record.md) when diagnosis spans multiple attempts or components.

## Rules

- Do not patch symptoms without explaining the causal chain.
- Do not combine several speculative fixes.
- Do not weaken assertions to fit current behavior.
- Report environmental or external causes only after recording eliminated hypotheses.
