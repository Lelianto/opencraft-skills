# Implementation readiness gate

Mark each `pass`, `concern`, `fail`, or `not applicable`.

- PRD baseline is approved or exceptions have named owners.
- Must-have requirements have stable IDs and acceptance evidence.
- Primary journeys and responsive interaction states are defined.
- Architecture resolves trust boundaries, data, contracts, migrations, and operations.
- Threats and required security controls map to implementation or tests.
- Every task is bounded, ordered, independently verifiable, and traceable.
- Test environment, fixtures, and commands are available or planned before dependent work.
- External dependencies, production authority, and irreversible actions are explicit.
- Rollout, observation, rollback, and ownership work is included.

Any unresolved `fail` produces `not ready`.
