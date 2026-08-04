# Security and data checklist

Record the selected profile and versioned control identifiers, such as `ASVS-v5.0.0-<requirement>` and, for AI-enabled systems, `AISVS-v<version>-<control>`.

Adapt to the architecture and authorized scope. Do not perform destructive or intrusive testing against production without explicit approval.

## Identity and access

- Registration, verification, login, logout, recovery, revocation, expiry, and concurrent sessions.
- Horizontal, vertical, object-level, action-level, and tenant authorization.
- Privileged actions require appropriate reauthentication and audit evidence.

## Input and execution boundaries

- Injection, unsafe rendering, request forgery, path traversal, uploads, redirects, deserialization, and command execution paths.
- Server-side validation, size/type limits, rate limits, idempotency, and safe error responses.
- Dependencies, build pipeline, secrets, configuration, headers, cookies, and transport settings.

## Data protection

- Classification, minimization, consent or lawful basis where applicable, encryption, masking, logs, analytics, retention, deletion, and export.
- Tenant isolation, database policies, backups, restore evidence, audit integrity, and least-privilege service access.
- Fixtures and non-production environments contain no unauthorized production data.

## Integrity and recovery

- Constraints, transactions, concurrent writes, duplicate delivery, partial failure, migrations, rollback, reconciliation, and disaster recovery.
