# Security pack AI rules

Security rules are non-negotiable:

- Validate and normalize all untrusted input at the server boundary.
- Re-check authorization server-side; deny by default.
- Never emit secrets into code, config, logs, fixtures, or examples.
- Encode output for its context; no injection sinks.
- Flag threat-model implications of features that touch data or boundaries.
