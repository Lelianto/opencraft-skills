---
name: design-product-experience
description: Design the end-to-end product experience for a website or application, including information architecture, user flows, content hierarchy, interaction contracts, component states, responsive behavior, accessibility, and design-system guidance. Use after product scope or PRD and before UI implementation, or when an existing product journey needs UX redesign.
---

# Design Product Experience

Translate product intent into implementable behavior across devices and ability levels.

## Workflow

1. Read user evidence, PRD, brand/design context, existing UI, and platform constraints.
2. Define information architecture, navigation model, entry points, primary flows, alternate paths, and recovery paths.
3. Specify each screen's purpose, content hierarchy, primary action, secondary actions, permissions, and exit conditions.
4. Define component and page states: default, hover where meaningful, focus, disabled, loading, empty, validation, error, retry, partial success, and success.
5. Design narrow mobile first, then wide mobile, tablet, desktop, zoom/reflow, long content, localization expansion, and reduced-motion behavior.
6. Use semantic controls, logical focus order, visible focus, labels, instructions, error association, landmarks, headings, contrast, and non-color cues.
7. Reuse the existing design system. If none exists, define minimal tokens and primitives without inventing a broad component library.
8. Identify usability assumptions and define prototype or usability checks for consequential uncertainty.
9. Map experience decisions and states to requirement IDs and acceptance evidence.

Apply `craft-distinctive-product` to establish a product-specific design thesis, reject unsupported AI-generated visual conventions, and recompose mobile journeys as app-quality experiences.

Use [references/experience-spec.md](references/experience-spec.md) and [references/responsive-state-matrix.md](references/responsive-state-matrix.md) for UI-heavy products.

## Output contract

Produce behavior and layout guidance precise enough to implement without guessing, while leaving visual exploration flexible where the product has not made a decision.

For material navigation, information-architecture, interaction, or design-direction choices, apply `facilitate-product-decision`. Present genuinely distinct directions with mobile, accessibility, delivery, and reversibility trade-offs; do not implement a preferred direction until the configured human gate is resolved.
