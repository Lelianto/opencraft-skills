---
name: test-platform
description: Plan and execute risk-based testing for a web or software platform across unit, integration, API, browser end-to-end, responsive UI, accessibility, security, privacy, and data integrity. Use when validating a complete platform, creating a test strategy, testing critical user journeys, checking multi-role permissions, verifying migrations, or producing evidence for release readiness.
---

# Test Platform

Test the behavior users depend on and the boundaries attackers or failures can exploit. Operate only on authorized systems and data.

## Workflow

1. Read the PRD, acceptance criteria, architecture, threat boundaries, changed code, and repository test commands.
2. Build a risk matrix from user impact, likelihood, detectability, and recovery cost. Prioritize authentication, authorization, money, sensitive data, destructive operations, and critical journeys.
3. Map requirements to test levels; avoid duplicating every assertion at every level.
4. Run static checks and focused tests first. Then run integration, API, and browser E2E journeys with representative roles and data.
5. Verify responsive behavior at narrow mobile, wide mobile, tablet, and desktop widths; cover keyboard, focus, semantics, zoom/reflow, contrast, and reduced motion.
6. Test input boundaries, session lifecycle, horizontal and vertical authorization, tenant isolation, rate/abuse controls, safe errors, uploads, redirects, outbound requests, and dependency/configuration exposure where relevant.
7. Validate schema constraints, transaction behavior, concurrency, duplicate requests, migrations, rollback, backup/restore evidence, retention, deletion, export, and audit records.
8. Check slow networks, timeouts, retries, partial failure, refresh, navigation history, offline behavior when promised, and recovery after interruption.
9. Record commands, environment, test data, expected/actual results, screenshots or traces, and reproducible defects.
10. Rerun affected checks after fixes and report coverage gaps honestly.

Use [references/test-strategy.md](references/test-strategy.md) to plan coverage. Use [references/security-data-checklist.md](references/security-data-checklist.md) for high-risk platforms.

## Exit contract

Return a requirement traceability matrix, test results, defects ordered by severity, security/data observations, untested areas, residual risk, and a release recommendation. Never equate a passing happy path with platform readiness.

Include HITL state integrity when configured: pending records must match active decision IDs, gated work must not proceed, accepted choices must trace to implementation, and production or residual-risk authority must be explicit.
