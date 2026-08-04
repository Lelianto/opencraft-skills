# Frontend quality checklist

## Interaction

- Use native controls before recreating them.
- Keep keyboard order aligned with visual order.
- Preserve focus across dialogs, navigation, validation, and async updates.
- Give every action immediate, unambiguous feedback.
- Confirm destructive actions and make recovery possible where practical.

## Responsive layout

- Verify narrow mobile, wide mobile, tablet, and desktop widths.
- Let content reflow; avoid shrinking essential controls below usable sizes.
- Handle long names, localization expansion, empty data, and dense data.
- Avoid hidden horizontal overflow and viewport-height traps.

## Visual system

- Reuse tokens and components.
- Establish clear hierarchy, consistent spacing, and restrained emphasis.
- Do not use arbitrary colors, gradients, shadows, or radii that conflict with the product language.
- Keep skeletons and loading indicators structurally close to final content.

## Accessibility

- Use semantic landmarks and heading order.
- Associate labels, descriptions, and errors with controls.
- Ensure focus is visible and overlays trap/restore focus correctly.
- Do not encode meaning by color alone.
- Respect reduced motion and zoom/reflow.

## Evidence

- Exercise the real route and primary interaction.
- Check the browser console and network failures.
- Capture or inspect representative desktop and mobile states when visual tooling is available.
