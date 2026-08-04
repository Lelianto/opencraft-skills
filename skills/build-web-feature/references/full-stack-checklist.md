# Full-stack change checklist

## Contract

- Request and response shapes are explicit.
- Validation is duplicated at trust boundaries, not assumed from the client.
- Error codes are stable and safe for users.
- Compatibility or versioning impact is understood.

## Data

- Invariants and transaction boundaries are enforced.
- Queries are scoped, parameterized, and indexed for expected access paths.
- Migrations are deterministic and have a rollout/rollback story.
- Personal or sensitive data has an explicit lifecycle.

## Security

- Authentication identity is verified server-side.
- Authorization checks resource, action, and tenant.
- Secrets remain outside client bundles and logs.
- Uploads, redirects, rendered content, and outbound requests are constrained.

## Reliability

- Timeouts, retries, idempotency, and duplicate submissions are handled where relevant.
- Partial failures do not leave silent corrupt state.
- Logs and metrics make the path diagnosable.

## Tests

- Domain rules have focused tests.
- Boundary integration covers success and representative failure.
- One browser-level test covers the critical journey when valuable.
