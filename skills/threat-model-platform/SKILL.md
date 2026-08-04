---
name: threat-model-platform
description: Create or update a practical threat model for a web, SaaS, data, or AI-enabled platform, covering assets, actors, data flows, trust boundaries, abuse cases, threats, controls, verification, and residual risk. Use during architecture, before high-risk implementation, after major trust-boundary changes, or when security requirements need traceable evidence.
---

# Threat Model Platform

Prioritize plausible product-specific threats and verifiable controls rather than producing a generic checklist.

## Workflow

1. Define scope, deployment context, security objectives, assumptions, and authorized trust relationships.
2. Inventory sensitive assets, identities, roles, tenants, secrets, regulated data, availability dependencies, and high-value operations.
3. Draw or describe data flows, entry/exit points, external services, privilege changes, storage, and trust boundaries.
4. Identify attacker capabilities and misuse cases, including business-logic abuse and insider/service compromise.
5. Enumerate threats using an appropriate model such as STRIDE, then rank by impact, likelihood, exploitability, and detectability.
6. Map preventive, detective, and recovery controls to threat IDs and requirement IDs. Reference versioned OWASP ASVS controls where applicable; use AISVS when the product includes AI models, agents, embeddings, or MCP.
7. Define concrete verification and monitoring evidence for every required control.
8. Record accepted, transferred, mitigated, and unresolved residual risks with owners and review triggers.
9. Update the model when architecture, data sensitivity, integrations, identity, or deployment changes.

Use [references/threat-model.md](references/threat-model.md) for the artifact and [references/security-standards.md](references/security-standards.md) for versioning rules.

## Guardrails

- Do not claim a control exists without implementation or configuration evidence.
- Never run intrusive tests against systems outside explicit authorization.
- Do not include secret values, exploitable production details, or unnecessary personal data in the artifact.
- Apply `facilitate-product-decision` before accepting residual security, privacy, tenant-isolation, compliance, or sensitive-data risk. Risk acceptance is `D3`; an AI recommendation or implementation constraint is never approval.
