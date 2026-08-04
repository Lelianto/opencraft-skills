# Decision record contract

Store one JSON file per durable decision under `.product/decisions/`. Validate it against `.product/schemas/decision-record.schema.json` when that schema is installed.

Required fields:

```json
{
  "schema_version": "1.0",
  "id": "DEC-DESIGN-003",
  "level": "D2",
  "stage": "experience-design",
  "status": "pending",
  "question": "Which mobile navigation model should be used?",
  "why_now": "Implementation depends on a stable navigation model.",
  "options": [
    {
      "id": "bottom-navigation",
      "label": "Bottom navigation",
      "tradeoffs": "Easy one-handed access; permanently consumes vertical space."
    }
  ],
  "recommendation": "bottom-navigation",
  "affected_artifacts": ["REQ-NAV-001", "EXP-MOBILE-004"],
  "created_at": "2026-08-04T00:00:00Z"
}
```

When resolved, add `decision`, `decided_by`, `decided_at`, and `rationale`. Preserve rejected alternatives. Never rewrite a human rationale to claim evidence or authority they did not provide.
