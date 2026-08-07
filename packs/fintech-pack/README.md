# Fintech pack

Living context for fintech applications: regulatory framing, KYC/AML, immutable audit, data residency, and disclosure.

## Included contexts

- `ctx-fintech-kyc` — identity verified before transactions (hardened-mandate, block).
- `ctx-fintech-audit` — immutable, retained audit trail (hardened-mandate, block).
- `ctx-fintech-data-residency` — data in approved jurisdiction (hardened-mandate, block).
- `ctx-fintech-disclosure` — full fee/rate/cost/schedule disclosure (hardened-mandate, block).

## Extends

- `node-pack@^1`
- `security-pack@^1`
- `testing-pack@^1`

Overrides `ctx-security-dependency-hygiene` to `critical` severity (financial services treat vulnerabilities as release-blocking).

## Provenance

- Author: OpenCraft Fintech · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
