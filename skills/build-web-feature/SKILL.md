---
name: build-web-feature
description: Build or modify a complete web platform or end-to-end feature, including UI, responsive behavior, accessibility, server logic, APIs or actions, authentication, authorization, persistence, tests, and documentation. Use when asked to implement, code, scaffold, fix, refactor, or complete a web app, website, dashboard, SaaS product, admin platform, or full-stack feature.
---

# Build Web Feature

Deliver a working platform as a sequence of verified vertical slices that follows the repository rather than imposing a generic starter.

## Workflow

1. Read local agent instructions and inspect the relevant source, tests, configuration, scripts, dependency versions, and current git state.
2. Reproduce existing behavior or establish a baseline before editing. Preserve unrelated user changes.
3. Identify the smallest end-to-end slice and the contracts it crosses. Plan briefly for multi-file or risky work.
4. Reuse existing components, tokens, utilities, patterns, and dependencies. Add a dependency only when it clearly reduces risk or maintenance.
5. Implement the domain/server behavior first when it defines the UI contract; otherwise build from the user journey inward.
6. Cover loading, empty, validation, permission, error, retry, success, and destructive confirmation states as applicable.
7. Build semantic, keyboard-operable UI with visible focus, labels, appropriate landmarks, sufficient contrast, reduced-motion support, and responsive layouts without accidental overflow.
8. Validate all untrusted server input and enforce authorization at the server boundary. Avoid exposing secrets or sensitive errors.
9. Add or update tests nearest to the changed behavior. Prefer behavior assertions over implementation-detail snapshots.
10. Run focused checks, then repository-wide required checks. Inspect the final diff and exercise the critical user flow in a browser when available.
11. Report the outcome, important decisions, evidence, and any residual risk. Do not claim checks that were not run.

Apply `craft-distinctive-product` for user-facing work. Preserve the product-specific design thesis, reject generic AI-slop patterns, and implement mobile as a deliberate touch-first composition rather than a collapsed desktop layout.

For a new platform, establish the minimum production-shaped foundation first: configuration and environment validation, application shell and routing, identity and authorization boundaries, data access and migrations, error handling, observability, test harness, and production build. Then deliver prioritized journeys one vertical slice at a time. Do not leave core flows as mock handlers or disconnected screens unless the user explicitly asked for a prototype.

Load [references/frontend-quality.md](references/frontend-quality.md) for UI-heavy work. Load [references/full-stack-checklist.md](references/full-stack-checklist.md) when the change crosses client, server, or data boundaries.

## Definition of done

- Requested behavior works through the real entry point.
- Existing conventions and public contracts remain intact unless change was intentional.
- Important states and boundary failures are handled.
- Relevant tests and static checks pass.
- Production build succeeds when the project defines one.
- No secrets, debug artifacts, placeholder claims, or unrelated edits are introduced.
- When HITL artifacts exist, dependent work follows accepted `DEC-*` records and stops for pending material choices instead of implementing an AI recommendation as if it were approved.
