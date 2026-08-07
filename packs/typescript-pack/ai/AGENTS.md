# TypeScript pack AI rules

Follow the conventions declared by typescript-pack:

- Keep `strict: true`. Never relax tsconfig to silence errors.
- Never write explicit `any`.
- Use `import type` for type-only imports.
- Run type-check and lint; only claim completion with fresh passing output.
