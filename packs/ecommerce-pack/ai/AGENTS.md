# E-commerce pack AI rules

- Compute totals, taxes, and shipping on the server; never trust client values.
- Use idempotency keys for payments and order transitions.
- Keep inventory atomic with orders and reconcile drift.
- Never generate fake scarcity, fabricated reviews, or invented social proof.
- Add rate limits and abuse controls to high-value flows.
