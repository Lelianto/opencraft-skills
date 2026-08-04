---
name: facilitate-product-decision
description: Structure and record material human decisions about product scope, design direction, architecture, cost, security, data, risk, release, or other consequential trade-offs. Use when an AI agent reaches a decision that requires human judgment or authority, when human-loop mode requires approval, when options and consequences need comparison, or when resuming work after a pending decision.
---

# Facilitate Product Decision

Turn a material choice into a concise, evidence-backed human decision. Do not outsource analysis to the user and do not manufacture options when one safe path is already required.

## Workflow

1. Read `.product/human-loop.json`, `.product/human-loop-state.json`, existing decisions, and the artifacts affected by the choice. If configuration is absent, use `guided` behavior without creating files unless durable project work is in scope.
2. Classify the decision using [references/decision-policy.md](references/decision-policy.md): `D0` informational, `D1` reversible, `D2` material judgment, or `D3` authority/irreversible.
3. Continue without interruption for `D0`. For `D1`, follow the configured mode. Always stop for unresolved `D2` in `guided` or `approval-gated` mode and for every `D3` decision.
4. Separate facts, constraints, assumptions, and unknowns. Perform safe analysis before asking the human; never ask them to discover information available in the repository.
5. Present two to four genuinely different options when alternatives exist. For each, state user impact, delivery impact, risk, reversibility, and cost or dependency consequences. Include `defer` or `research first` when credible.
6. Recommend one option and explain why it best fits current evidence. State what remains unchanged and the cost or trigger for revisiting the choice.
7. Ask one bounded question that accepts a short answer. Do not continue dependent implementation while the decision is unresolved.
8. Persist substantial decisions using [references/decision-record.md](references/decision-record.md). When the OpenCraft CLI is available, create a reviewed draft outside `.product/decisions/` and run `opencraft-skills decision add <draft.json>` so the record and orchestration state change atomically. Otherwise write `.product/decisions/<ID>.json` and update the state consistently. Set `DECISION_REQUIRED` or `APPROVAL_REQUIRED` while pending.
9. When the human responds, validate that the selected option exists or record a clearly described custom option. Capture the human's rationale without embellishment, mark the record `accepted` or `rejected`, and update affected artifact IDs.
10. Resume only when no blocking decision remains. Report the accepted choice, consequences, next bounded action, and any revisit condition.

## Decision brief

Use this order:

- decision ID, level, stage, and status;
- one plain-language question;
- why the decision matters now;
- evidence and constraints;
- options with meaningful trade-offs;
- recommendation and rationale;
- unchanged scope and reversal cost;
- one explicit request to choose, revise, defer, or research first.

## Guardrails

- Ask humans for judgment, values, risk acceptance, and authority—not routine implementation details.
- Never treat silence, elapsed time, a default option, or an AI recommendation as human approval.
- Never bundle independent material decisions into one forced choice.
- Never offer an unsafe or policy-violating option merely for symmetry.
- Never proceed past a production, destructive, purchasing, external-communication, sensitive-data, or accepted-residual-risk gate without explicit authority.
- Avoid decision fatigue: batch only tightly related choices and preserve one clear decision per record.
- Keep old projects compatible. Missing HITL files do not invalidate existing artifacts or authorize material decisions.
