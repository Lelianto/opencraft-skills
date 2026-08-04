# OpenCraft Skill Standard v1

## Skill contract

Every skill must:

1. Live at `skills/<name>/SKILL.md`.
2. Use a lowercase kebab-case name of at most 64 characters that matches its directory.
3. Include only `name` and `description` in portable YAML frontmatter.
4. Describe both capability and activation context in `description`.
5. Use imperative instructions and a workflow with verifiable outcomes.
6. Keep `SKILL.md` below 500 lines and move conditional detail into one-level `references/` files.
7. Avoid duplicating rules that belong in repository-level instructions.
8. Avoid assuming a framework, package manager, provider, or external authorization.
9. Define an output contract or definition of done.
10. Never authorize unsupported completion claims.
11. Include positive, negative, ambiguous, and realistic end-to-end evaluation prompts with reviewable assertions.
12. State environment dependencies and authorization boundaries when the workflow requires them.
13. Reject generic AI-generated design and copy patterns unless product evidence gives them a specific purpose.
14. Ground originality in product meaning, domain context, truthful content, and user behavior rather than novelty alone.
15. Treat mobile web as a distinct touch-first composition, not a vertically stacked desktop layout.
16. Classify material human choices as `D0`–`D3`, follow the configured HITL mode, and never infer approval from silence or an AI recommendation.

`agents/openai.yaml` is optional Codex/OpenAI UI metadata. Other clients may ignore it. Client-specific extensions must not change the portable workflow's meaning.

## Instruction precedence

When instructions conflict, apply this order:

1. Client system policy, safety policy, and permissions.
2. The user's latest request.
3. Repository instructions such as `AGENTS.md`, `CLAUDE.md`, or equivalent.
4. The active skill.
5. Generic references and baselines.

## Lifecycle

1. Edit only canonical source under `skills/`.
2. Run `python3 scripts/validate.py`.
3. Test positive, negative, ambiguous, and realistic end-to-end scenarios.
4. Reinstall with `scripts/install.py --force` only after reviewing the destination.
5. Version-control canonical sources and templates; treat installed client directories as generated output when they live in the same repository.
6. Regenerate `skills.lock.json` and run evaluations before release.

## Artifact and traceability contract

- Use `.product/` for intent, decisions, and evidence that must survive across agents or sessions.
- Use stable `REQ`, `EXP`, `ARCH`, `TASK`, `THREAT`, `CTRL`, `TEST`, `RISK`, and `DEC` identifiers.
- Link every must-have requirement to an implementation task and test or release evidence.
- Feed production findings back into relevant artifacts; specifications must not become stale snapshots.
- Select one delivery mode: `greenfield-product`, `brownfield-feature`, `prototype`, `production-hardening`, or `incident-fix`.
- When `.product/human-loop.json` exists, keep decision records and `.product/human-loop-state.json` consistent. Do not continue dependent work while a required human decision is pending.

## Human-in-the-loop contract

- Support `off`, `autonomous`, `guided`, and `approval-gated` modes without weakening existing safety gates.
- Treat `D0` as informational, `D1` as reversible, `D2` as material judgment, and `D3` as authority-bound or difficult to reverse.
- Always require explicit human authority for production, destructive, purchasing, external communication, sensitive-data transmission, permission changes, and material residual-risk acceptance.
- Present evidence, constraints, two to four meaningful options when alternatives exist, consequences, reversibility, and a recommendation before asking.
- Persist one material choice per `DEC-*` record. Preserve rejected alternatives and record the human rationale without embellishment.
- Store a resume checkpoint before pausing and reread affected artifacts after the choice is resolved.
- Missing HITL files in an existing project preserve legacy compatibility; they never imply additional authority.

## Trigger evaluation

Maintain at least the following for every skill:

- three prompts that should trigger it;
- two nearby prompts that should not trigger it;
- one ambiguous prompt;
- one end-to-end scenario that tests workflow compliance and output quality;
- two objective assertions for deterministic benchmarking.

Revise `description` when discovery fails. Revise the instruction body when discovery succeeds but execution diverges. Use a with-skill versus without-skill comparison for consequential changes and review subjective quality blind to the variant name.

## Evidence standard

- A completion claim requires fresh command output or direct observation.
- Record unexecuted checks as `not run`, never as pass.
- Separate verified facts, inferences, assumptions, and unresolved risks.
- Preserve commands, environment, version, and artifact identity for release evidence.
- Treat user-visible completion, release readiness, and production health as separate claims.

## Security and distribution

- Verify canonical skill content against `skills.lock.json` before installation.
- Review scripts and instructions that can invoke tools or mutate external state.
- Do not embed credentials, production data, or private operational details.
- Pin external security standards to a published version.
- Require explicit user authority for deployment, destructive operations, intrusive testing, purchasing, messaging, or production mutation.
- Keep the Python and Node.js installers behaviorally equivalent and dependency-free at runtime.
- Publish npm packages only from a clean, validated source whose version matches `collection.json` and `skills.lock.json`.

## Product craft standard

- Define the meaningful core and a domain-specific design thesis before choosing a visual direction.
- Retain only one or two deliberate signature ideas; keep supporting design restrained and coherent.
- Remove fake metrics, testimonials, logos, awards, activity feeds, and unsupported marketing claims.
- Reject interchangeable SaaS compositions, decorative gradients, excessive glass/card treatments, arbitrary icons, and motion without product-specific purpose.
- Preserve hierarchy, accessibility, legibility, performance, and task completion over decoration.
- Recompose mobile navigation, density, actions, forms, overlays, and state recovery around constrained attention, touch, browser behavior, and the software keyboard.
