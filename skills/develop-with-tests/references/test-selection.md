# Test selection guide

Choose the lowest level that provides meaningful confidence:

- Unit: pure domain rules, transformations, validation, and state machines.
- Integration: database constraints, adapters, service boundaries, jobs, and framework wiring.
- Contract/API: request/response schema, authentication, authorization, compatibility, and error taxonomy.
- Browser E2E: critical user journeys and browser/framework integration.
- Visual/manual: responsive layout, usability, animation, and assistive-technology behavior not captured reliably in automation.

Avoid testing the same detail at every level. Preserve at least one end-to-end proof for critical journeys and focused tests for complex rules.
