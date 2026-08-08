# Skill evaluation

`cases.json` contains discovery prompts and output assertions for every canonical skill.

Validate fixture completeness:

```bash
python3 scripts/evaluate.py
```

## Real-agent baseline harness

`scripts/run-evals.mjs` runs every skill's end-to-end `scenario` against a real
Agent Skills client (Claude Code, OpenAI Codex, ...) in two conditions and
captures the outputs into the layout below. It does not embed vendor
credentials — it uses the client's own auth.

```bash
# Scaffold prompts for every skill without invoking any agent (no credentials, no spend)
npm run eval:dry-run

# Run the full baseline (requires `claude` or `codex` on PATH with valid auth)
npm run eval:run -- --agent claude --model sonnet

# Run a subset
npm run eval:run -- --skills analyze-product,write-product-prd

# Grade the captured outputs into a deterministic assertion benchmark
npm run eval:grade
```

Captured outputs land in:

```text
runs/
├── with-skill/<skill>.md
├── without-skill/<skill>.md
└── benchmark.json        # created by eval:grade
```

The harness installs **only the target skill** in the with-skill project so the
delta isolates that skill's effect. Grade a subset with `--skills`:

```bash
python3 scripts/evaluate.py --runs runs --benchmark benchmark.json --skills analyze-product,write-product-prd
```

Review subjective qualities such as judgment, visual quality, and usefulness
manually and blind to variant names. Trigger prompts still require a compatible
Claude, Codex, Copilot, Cursor, or other Agent Skills harness; this repository
does not embed vendor credentials.
