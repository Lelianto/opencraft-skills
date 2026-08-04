# Mobile web that behaves like a mobile application

## Recompose the experience

- Prioritize the one task most likely in the mobile context; defer secondary analysis and administration.
- Reorder, combine, or remove content instead of stacking every desktop region vertically.
- Use task-appropriate navigation. Keep persistent bottom navigation to a small set of primary destinations; use drill-down navigation for deep structures.
- Place frequent actions within comfortable thumb reach without obscuring content or platform controls.
- Convert dense tables into prioritized records, progressive disclosure, or focused detail views. Preserve comparison when comparison is the real job.
- Turn large desktop dialogs into sheets or full-screen flows when forms, keyboards, or complex decisions require space.

## Touch, viewport, and device behavior

- Provide comfortably sized touch targets and spacing; do not rely on hover.
- Respect safe-area insets, browser chrome, orientation changes, and dynamic viewport units.
- Keep primary actions visible when appropriate, but ensure sticky elements never cover errors, fields, or final content.
- Use the correct input type, input mode, autocomplete, labels, and validation timing so the software keyboard helps rather than obstructs.
- Preserve scroll position and user input across validation, navigation, backgrounding, refresh, and recoverable failures where practical.
- Offer visible alternatives for swipe, drag, long-press, and other non-obvious gestures.

## App-quality states

- Design first launch, signed-out, loading, skeleton, empty, populated, partial, offline or degraded, validation, permission, conflict, failure, retry, and success states.
- Make latency legible; use optimistic behavior only when rollback and conflict handling are safe.
- Preserve focus and announce meaningful asynchronous changes for assistive technology.
- Respect reduced motion, text resizing, zoom/reflow, high contrast, and device theme when the product supports it.

## Performance and validation

- Budget JavaScript, fonts, media, animation, and third-party scripts for real mobile networks and devices.
- Avoid layout shifts and interaction delays on the primary journey.
- Test at narrow and wide mobile widths, with long content, the software keyboard open, slow network, and at least one real or device-emulated touch flow.
- Check reachability, focus, browser back behavior, deep links, refresh, installability when promised, and recovery after interruption.

The standard is not “desktop but responsive.” The standard is a coherent mobile task model delivered through the web.
