# Security pack

Living context for application security: input validation, server-side authorization, secrets, and dependency hygiene.

## Included contexts

- `ctx-security-input-validation` — validate input at boundaries (hardened-mandate, block).
- `ctx-security-authz-server` — server-side authorization, deny-by-default (hardened-mandate, block).
- `ctx-security-secrets` — secrets never committed (hardened-mandate, block).
- `ctx-security-dependency-hygiene` — lockfile + scanning (hardened-standard, block).

## Provenance

- Author: OpenCraft Security · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
- Standards: OWASP ASVS 5.0.0, OWASP AISVS 1.0.0

## Usage

```yaml
extends:
  - security-pack@^1
```
