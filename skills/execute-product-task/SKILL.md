---
name: execute-product-task
description: Execute one bounded product-delivery task from an approved plan, preserving requirement traceability and producing fresh verification evidence. Use when implementing the next task or vertical slice, resuming planned work, or when an agent must avoid broad autonomous changes across an entire product roadmap.
---

# Execute Product Task

Complete one task contract at a time and leave the repository in a verifiable state.

## Workflow

1. Read the task, linked requirement/control/risk IDs, relevant artifacts, local instructions, current code, tests, and git state.
2. Confirm preconditions. Stop only for a failed readiness condition that changes the task materially; otherwise record a reversible assumption.
3. Establish the current test baseline and reproduce the target behavior or failure.
4. Apply `develop-with-tests` for behavioral code and `debug-platform` for unexpected failures.
5. Make the smallest coherent implementation that satisfies the task without unrelated refactoring.
6. Run focused verification after each meaningful boundary, then the task's exact completion commands.
7. Inspect the diff for scope, secrets, placeholders, generated noise, compatibility, and missing states.
8. Update traceability and task status with commands and evidence. Mark `blocked` or `partial` rather than claiming completion when a required gate did not pass.
9. Hand off changed behavior, decisions, evidence, residual risk, and the next unblocked task.

Use [references/task-record.md](references/task-record.md) to persist execution evidence.

## Guardrails

- Never silently expand task scope.
- Never weaken a test or security control merely to make a check pass.
- Never claim completion from stale output.
- Do not deploy or mutate production unless the task and user explicitly authorize it.
- Before execution or resume, inspect `.product/human-loop-state.json` and linked `DEC-*` records when present. Stop dependent work in `DECISION_REQUIRED`, `APPROVAL_REQUIRED`, or `BLOCKED`; use `facilitate-product-decision` instead of guessing.
