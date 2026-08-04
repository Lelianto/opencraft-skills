# Security policy

## Scope

Treat every skill, reference, script, installer change, and generated lockfile as supply-chain-sensitive agent instruction.

## Reporting

Report suspected vulnerabilities privately through GitHub Security Advisories for `Lelianto/opencraft-skills`. Do not include live credentials, personal data, or exploitable production details in a public issue.

## Maintainer checks

- Review changes to executable scripts and instructions that authorize tools or external state.
- Require generated `skills.lock.json` to match canonical source before release.
- Pin external security-control references to a published version.
- Keep production mutation, deployment, destructive testing, and secret access behind explicit user authorization.
- Reject skills that download or execute unverified remote code as part of normal activation.

## Consumer guidance

Review source provenance and checksums before installation. Prefer copy mode for auditable project snapshots. Do not install untrusted forks into agents that can access credentials or production systems.
