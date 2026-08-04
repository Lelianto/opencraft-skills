# Human decision policy

## Decision levels

| Level | Meaning | Default handling |
|---|---|---|
| `D0` | Informational; no meaningful choice | Record when useful and continue |
| `D1` | Low-risk and readily reversible | AI may decide in autonomous or guided mode; explain the assumption |
| `D2` | Material product, design, architecture, cost, privacy, or delivery trade-off | Human decision in guided and approval-gated modes |
| `D3` | Irreversible, production, destructive, external, regulated, risk-acceptance, or authority-bound action | Explicit human approval in every mode |

## Modes

- `off`: preserve legacy behavior, except existing safety and production permission gates still apply.
- `autonomous`: AI may resolve `D0`–`D2` when safely reversible and within existing authority; `D3` always stops.
- `guided`: AI resolves `D0`–`D1`; `D2`–`D3` stop for the human.
- `approval-gated`: every choice that changes scope or implementation direction stops; routine execution inside an approved task may continue.

## Mandatory gates

Treat these as at least `D2`:

- target user, product outcome, MVP boundary, success measure, or explicit non-goal;
- selection of a visual or interaction direction;
- architecture choices with migration, vendor, cost, lock-in, or operational consequences;
- privacy model, retention, tenancy, access policy, or residual security risk;
- release scope, degraded acceptance criteria, or readiness exception.

Treat these as `D3`:

- production deployment or migration;
- deletion or destructive mutation of material data;
- purchase, public message, permission change, or external side effect;
- use or transmission of sensitive data outside existing authority;
- acceptance of material residual security, privacy, legal, or compliance risk.

## Escalation rules

- Upgrade a decision when uncertainty increases blast radius or reversibility is unclear.
- Do not downgrade a decision because delivery is urgent.
- If options cannot be compared with current evidence, recommend a time-boxed research step and record its exit criterion.
- If a human choice conflicts with a non-negotiable safety constraint, explain the constraint and request a safe alternative rather than recording false approval.
