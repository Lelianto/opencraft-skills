# Education pack

Living context for education products: learner privacy, content integrity, accessibility, and availability at scale.

## Included contexts

- `ctx-education-learner-privacy` — learner data protected and minimized (hardened-mandate, block).
- `ctx-education-content-integrity` — content versioned and reviewed (hardened-standard, warn).
- `ctx-education-availability` — core paths available under load (warn).

## Extends

- `node-pack@^1`
- `accessibility-pack@^1`
- `testing-pack@^1`

Overrides `ctx-a11y-keyboard` to `critical` severity (learning products serve diverse learners).

## Provenance

- Author: OpenCraft Education · License: MIT · Source: https://github.com/Lelianto/opencraft-skills
