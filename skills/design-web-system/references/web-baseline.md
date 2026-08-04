# Default web engineering baseline

Apply only when the repository has no stronger convention.

- Use one language across adjacent client/server surfaces when practical, with strict static checking.
- Keep domain logic independent from transport and rendering details.
- Validate untrusted input at every server or persistence boundary.
- Use server-enforced authorization, least privilege, secure cookies, CSRF protection where applicable, and parameterized queries.
- Prefer server-rendered or progressively enhanced pages for content-heavy flows; add client state only where interaction requires it.
- Make URLs, forms, and browser navigation work predictably.
- Design APIs around stable domain operations, not database tables.
- Use schema migrations and seed data that are deterministic and reviewable.
- Emit structured errors and correlation identifiers without leaking secrets or personal data.
- Establish lint, type-check, unit/integration tests, production build, and a critical-path browser test.
