---
name: design-web-system
description: Design or review pragmatic architecture for a web application or feature, including boundaries, data flow, API contracts, persistence, authentication, authorization, caching, background work, observability, deployment, and migrations. Use when starting a web product, making a consequential technical decision, integrating a service, or turning a product brief into an implementation plan.
---

# Design Web System

Choose the simplest architecture that satisfies current evidence and leaves expensive decisions reversible.

## Workflow

1. Inspect the repository, runtime, package manager, framework conventions, deployment model, data stores, and existing tests. Prefer established patterns.
2. Load the product brief or infer the minimum requirements. Separate product constraints from technical preferences.
3. Map the request path from user interaction through UI, server boundary, domain logic, persistence, and external services.
4. Define trust boundaries and ownership. Perform authentication and authorization server-side; never rely on hidden UI alone.
5. Define contracts before implementation: inputs, outputs, validation, error taxonomy, idempotency, pagination, and compatibility.
6. Model data invariants, indexes, lifecycle, tenancy, retention, and migration/rollback needs.
7. Decide synchronous versus asynchronous work, cache behavior, timeout/retry policy, and failure recovery.
8. Specify logs, metrics, traces, audit events, and health signals proportional to operational risk.
9. Record only consequential or hard-to-reverse decisions. Include alternatives and a reversal path.
10. Produce an ordered implementation plan with verification at each boundary.

Use [references/architecture-brief.md](references/architecture-brief.md) for substantial changes. Use [references/web-baseline.md](references/web-baseline.md) when the repository has no explicit engineering baseline.

## Guardrails

- Do not replace the stack merely because another stack is familiar.
- Avoid distributed components until load, isolation, or reliability needs justify them.
- Keep secrets server-side and configuration outside source control.
- Design migrations for mixed-version operation when deployment is not atomic.
- Treat accessibility, security, performance, and operability as architecture inputs.
- Apply `facilitate-product-decision` to `D2` architecture choices involving vendor dependency, recurring cost, data model, migration path, lock-in, operability, or meaningful reversal cost. Production, destructive, sensitive-data, and accepted-risk choices are `D3` and always require explicit authority.
