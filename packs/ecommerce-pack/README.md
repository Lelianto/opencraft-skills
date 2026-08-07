# E-commerce pack

Living context for e-commerce applications: server-priced checkout, atomic inventory, payments, and abuse defense.

## Included contexts

- `ctx-ecommerce-checkout` — server-priced, idempotent, settlement-gated (hardened-mandate, block).
- `ctx-ecommerce-inventory` — atomic inventory with orders (hardened-standard, block).
- `ctx-ecommerce-abuse` — rate limits and abuse controls (hardened-standard, warn).

## Extends

- `node-pack@^1`
- `security-pack@^1`
- `testing-pack@^1`

Overrides `ctx-testing-gates` to `block` enforcement and `critical` severity (checkout/inventory are high-risk money paths).

## Provenance

- Author: OpenCraft E-commerce · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
