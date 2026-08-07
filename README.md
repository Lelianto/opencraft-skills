<h1 align="center">
  <img src="https://raw.githubusercontent.com/Lelianto/opencraft-skills/main/site/assets/icon-512.png" width="36" height="36" alt="OpenCraft carpenter mark" align="absmiddle" />&nbsp;OpenCraft Skills
</h1>

<p align="center">
  Install portable Agent Skills for Claude Code, OpenAI Codex, Cursor, GitHub Copilot, and other compatible clients.
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/opencraft-skills"><img src="https://img.shields.io/npm/v/opencraft-skills?color=cb3837" alt="npm" /></a>
  <a href="https://github.com/Lelianto/opencraft-skills/actions/workflows/quality.yml"><img src="https://github.com/Lelianto/opencraft-skills/actions/workflows/quality.yml/badge.svg" alt="Quality" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e.svg" alt="License: MIT" /></a>
</p>

## Quick start

Install the skills into every supported client directory in the current project:

```bash
npx opencraft-skills install --target all --project . --with-project-files
```

Or install the CLI globally:

```bash
npm install --global opencraft-skills
opencraft-skills install --target all --project . --with-project-files
```

Requires Node.js 18 or newer. The CLI has no runtime dependencies.

## Install command

```bash
opencraft-skills install [options]
```

| Option | Description |
|---|---|
| `--project <path>` | Target project root. Defaults to the current directory. |
| `--target <client>` | Install for `agents`, `claude`, `codex`, `cursor`, `github`, or `all`. |
| `--mode <mode>` | Use `copy` (default) or `link`. |
| `--with-project-files` | Initialize `AGENTS.md`, `PROJECT_CONTEXT.md`, and `.product/`. |
| `--human-loop <mode>` | Set `off`, `autonomous`, `guided`, or `approval-gated`. Defaults to `guided`. |
| `--force` | Replace installed skills with the same names. |
| `--version` | Print the package version. |
| `--help` | Show CLI help. |

The installer verifies the bundled skills against `skills.lock.json`, protects existing files unless `--force` is supplied, and writes `.ai-skills-install.json` as an installation receipt.

## Installation targets

| Target | Destination | Client |
|---|---|---|
| `agents` | `.agents/skills` | Agent Skills-compatible clients |
| `claude` | `.claude/skills` | Claude Code |
| `codex` | `.codex/skills` | OpenAI Codex |
| `cursor` | `.cursor/skills` | Cursor |
| `github` | `.github/skills` | GitHub Copilot |
| `all` | All destinations above | Multi-client projects |

Examples:

```bash
# Install only for Codex
npx opencraft-skills install --target codex --project .

# Keep installed skills linked to a local package checkout
npx opencraft-skills install --target all --mode link --project .

# Replace existing same-named skills
npx opencraft-skills install --target all --project . --force
```

## Human-in-the-loop commands

OpenCraft can store and enforce durable product decisions in initialized projects:

```bash
npx opencraft-skills hitl init --mode guided --project .
npx opencraft-skills hitl validate --project .
npx opencraft-skills decisions --project .
npx opencraft-skills decision add .product/drafts/DEC-DESIGN-003.json --project .
npx opencraft-skills decision show DEC-DESIGN-003 --project .
npx opencraft-skills decision resolve DEC-DESIGN-003 \
  --option bottom-navigation \
  --rationale "Best fit for frequent one-handed use" \
  --project .
npx opencraft-skills resume --project .
```

Available decision actions are `add`, `show`, `resolve`, `defer`, and `revise`. Use `--json` on supported commands for automation. AI recommendations never count as human approval.

## Package contents

The npm package includes:

- 18 portable Agent Skills;
- adapters and project artifact templates;
- Node.js and Python installers;
- evaluation fixtures and validation scripts;
- integrity metadata and security guidance.

For the skills catalog, delivery lifecycle, artifact model, contribution guide, security model, and release workflow, read the [full project documentation](https://github.com/Lelianto/opencraft-skills/blob/main/DOCUMENTATION.md).

## Context Packs (Living Context)

Beyond portable skills, OpenCraft ships **Context Packs** — reusable Living Context packages for [Living Context Driven Development](https://github.com/Lelianto/living-context-driven-development) (LCDD). Instead of rewriting project knowledge, declare it:

```yaml
# packs.yaml
extends:
  - nextjs-pack
  - security-pack
  - fintech-pack
```

`opencraft packs install` resolves, merges, validates, and materializes the pack graph into `.lcdd/` — an LCDD Context Registry with merged conventions, security rules, testing strategy, AI coding rules, and more. No API keys, no `@lcdd/cli` prerequisite, fully offline-capable.

```bash
opencraft-packs packs add nextjs-pack --project .
opencraft-packs packs install --project .
```

See [packs/README.md](packs/README.md), the [specification](packs/SPEC.md), and [docs/CONTEXT_PACKS.md](docs/CONTEXT_PACKS.md).

## License

[MIT](LICENSE)
