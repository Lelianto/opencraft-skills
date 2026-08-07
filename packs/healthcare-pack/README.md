# Healthcare pack

Living context for healthcare applications: PHI protection, consent, audit, accessibility, and availability.

## Included contexts

- `ctx-healthcare-phi` — PHI encrypted and access-minimized (hardened-mandate, block).
- `ctx-healthcare-consent` — consent checked at point of access (hardened-mandate, block).
- `ctx-healthcare-audit` — every PHI access logged (hardened-mandate, block).

## Extends

- `node-pack@^1`
- `security-pack@^1`
- `accessibility-pack@^1`

Overrides `ctx-a11y-wcag-aa` to `critical` severity (healthcare interfaces serve vulnerable users).

## Provenance

- Author: OpenCraft Healthcare · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
