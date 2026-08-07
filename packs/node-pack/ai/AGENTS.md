# Node pack AI rules

Follow the conventions declared by node-pack:

- Assume the declared Node LTS runtime; no non-LTS-only APIs.
- Write new modules as ESM.
- Handle every rejected promise and stream error.
- Never embed secrets in code, config, logs, or examples.
