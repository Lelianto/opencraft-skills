# Skill evaluation

`cases.json` contains discovery prompts and output assertions for every canonical skill.

Validate fixture completeness:

```bash
python3 scripts/evaluate.py
```

For behavioral comparison, run each `scenario` once with the target skill available and once without it. Save outputs as:

```text
runs/
├── with-skill/<skill>.md
└── without-skill/<skill>.md
```

Then create a deterministic assertion benchmark:

```bash
python3 scripts/evaluate.py --runs runs --benchmark benchmark.json
```

Review subjective qualities such as judgment, visual quality, and usefulness manually and blind to variant names. Trigger prompts still require a compatible Claude, Codex, Copilot, Cursor, or other Agent Skills harness; this repository does not embed vendor credentials.
