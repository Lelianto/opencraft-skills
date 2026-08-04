---
name: prepare-deployment
description: Assess and prepare a web or software platform for safe deployment, including build artifacts, environments, configuration, secrets, infrastructure, database migrations, observability, rollout, smoke tests, rollback, backups, incident ownership, and post-release verification. Use for deployment readiness reviews, release plans, staging-to-production promotion, go-live checklists, or production handoff.
---

# Prepare Deployment

Make the release repeatable, observable, and reversible. Preparing is authorized; executing a production deployment requires explicit user authority.

## Workflow

1. Identify the target environment, deployment owner, release artifact, infrastructure, domains/TLS, data stores, external dependencies, and compliance constraints.
2. Verify required quality evidence from the PRD, build, tests, security/data review, and unresolved-risk acceptance.
3. Confirm deterministic build, locked dependencies, artifact provenance, environment parity, configuration schema, secret ownership/rotation, and least privilege.
4. Review database migrations for compatibility, duration, locks, backfill, mixed-version operation, backup, rollback or forward-fix, and restore validation.
5. Define health checks, structured logs, metrics, traces, dashboards, alert thresholds, audit events, and on-call ownership before traffic arrives.
6. Choose rollout strategy: direct, rolling, canary, blue-green, or feature flag. Match it to blast radius and rollback capability.
7. Write pre-deploy checks, exact deployment steps, smoke tests, abort thresholds, rollback steps, and post-deploy validation.
8. Verify DNS, certificates, security headers, cache/CDN behavior, scheduled jobs, queues, rate limits, quotas, email/webhook delivery, and third-party production configuration where relevant.
9. Record known risks, accepted exceptions, owners, communications, support plan, and observation window.
10. Classify readiness as `go`, `conditional go`, or `no-go`, with evidence and blockers.

Use [references/deployment-readiness.md](references/deployment-readiness.md) for the release artifact.

## Guardrails

- Never expose secret values in output, commands, logs, or screenshots.
- Never assume rollback works because a command exists; verify the recovery path safely.
- Never run production deployment, migration, DNS change, or destructive test without explicit authorization.
- Keep release and rollback commands exact enough for another operator to execute.
- Apply `facilitate-product-decision` to conditional-go exceptions and every `D3` production, migration, destructive, external-state, or residual-risk decision. A `go` classification prepares a decision; it does not grant deployment authority.
