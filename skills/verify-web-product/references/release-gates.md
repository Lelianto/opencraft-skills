# Web release gates

Adapt gates to product risk and repository conventions.

| Gate | Minimum evidence |
|---|---|
| Scope | Acceptance criteria mapped to implementation and tests |
| Static | Formatter/lint and strict type checks pass |
| Functional | Focused tests and critical journey pass |
| Build | Production build succeeds |
| Accessibility | Keyboard and automated checks; manual screen-reader check for critical complex UI when feasible |
| Responsive | Representative narrow and wide viewports inspected |
| Security | Authn/authz, validation, secrets, dependency, and data exposure review |
| Performance | No unexplained regression in critical route or request pattern |
| Operations | Logs/metrics, configuration, migration, health, and rollback are adequate |
| Deployment | Artifact, rollout, smoke test, abort threshold, backup, and recovery plan are reviewed |

Classify each as `pass`, `fail`, `not run`, or `not applicable`. Include the command or observation supporting the status.
