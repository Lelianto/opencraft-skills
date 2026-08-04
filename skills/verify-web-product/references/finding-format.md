# Finding format

Use one entry per actionable issue:

```text
[severity] Short title
Location: path:line or route/component
Impact: What a user, operator, or system experiences
Evidence: Reproduction, failing check, trace, or concrete code path
Remediation: Smallest safe direction; avoid a full patch unless requested
```

Severity:

- `critical`: active compromise, irreversible data loss, or release-stopping outage.
- `high`: broken primary journey, material security/privacy exposure, or likely data corruption.
- `medium`: significant edge-case failure, accessibility barrier, or material operational risk.
- `low`: bounded defect with limited impact; exclude taste-only feedback.
