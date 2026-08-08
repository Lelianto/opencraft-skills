#!/usr/bin/env node

/**
 * Real-agent evaluation harness.
 *
 * Runs every skill's end-to-end scenario against a real Agent Skills client
 * (Claude Code, OpenAI Codex, ...) in two conditions:
 *
 *   - with-skill    : the target skill is installed in the project
 *   - without-skill : no skill installed (baseline)
 *
 * Outputs are written to `runs/with-skill/<skill>.md` and
 * `runs/without-skill/<skill>.md`, exactly the layout `evaluate.py --runs`
 * expects. Grade with:
 *
 *   python3 scripts/evaluate.py --runs runs --benchmark benchmark.json
 *
 * Usage:
 *   node scripts/run-evals.mjs [--agent claude|codex] [--skills a,b] [--out runs]
 *                             [--model <model>] [--dry-run]
 *
 * `--dry-run` scaffolds the run tree and a scenario prompt file for every skill
 * without invoking the agent (no credentials, no spend) — useful for CI and for
 * reviewing prompts before a real run.
 *
 * The harness does not embed vendor credentials; it relies on the client's own
 * auth (e.g. `claude` uses the logged-in Anthropic session).
 */

import { existsSync, mkdirSync, writeFileSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cases = JSON.parse(readFileSync(join(repository, "evals", "cases.json"), "utf8"));

function parseArgs(argv) {
  const args = { agent: null, skills: [], out: "runs", model: null, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--agent") args.agent = argv[++i];
    else if (argv[i] === "--skills") args.skills = argv[++i].split(",").map((s) => s.trim()).filter(Boolean);
    else if (argv[i] === "--out") args.out = argv[++i];
    else if (argv[i] === "--model") args.model = argv[++i];
    else if (argv[i] === "--dry-run") args.dryRun = true;
    else throw new Error(`unknown argument: ${argv[i]}`);
  }
  return args;
}

function detectAgent() {
  for (const candidate of ["claude", "codex"]) {
    const result = spawnSync("which", [candidate], { encoding: "utf8" });
    if (result.status === 0) return candidate;
  }
  return null;
}

function installSkill(projectDir, skillName) {
  // Copy the canonical skill into the client-native destination the runner uses.
  const target = detectAgent() === "claude" ? "claude" : "codex";
  const destination = join(projectDir, target === "claude" ? ".claude/skills" : ".codex/skills");
  mkdirSync(destination, { recursive: true });
  const source = join(repository, "skills", skillName);
  const result = spawnSync("cp", ["-R", `${source}/`, join(destination, skillName)], { encoding: "utf8" });
  if (result.status !== 0) throw new Error(`failed to install skill ${skillName}: ${result.stderr}`);
}

function runAgent(agent, projectDir, prompt, model) {
  const base = ["-p", prompt, "--output-format", "text"];
  if (model) base.push("--model", model);
  const result = spawnSync(agent, base, { cwd: projectDir, encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
  return { status: result.status, stdout: result.stdout || "", stderr: result.stderr || "" };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const agent = args.agent || detectAgent();
  if (!args.dryRun && !agent) {
    console.error("FAIL no agent found (claude/codex not on PATH); use --agent or --dry-run");
    process.exitCode = 1;
    return;
  }

  const skills = args.skills.length ? args.skills : Object.keys(cases);
  const outRoot = resolve(args.out);
  const withDir = join(outRoot, "with-skill");
  const withoutDir = join(outRoot, "without-skill");
  mkdirSync(withDir, { recursive: true });
  mkdirSync(withoutDir, { recursive: true });

  const failures = [];
  for (const skill of skills) {
    if (!cases[skill]) {
      failures.push(`unknown skill ${skill} (not in evals/cases.json)`);
      continue;
    }
    const scenario = cases[skill].scenario;
    if (args.dryRun) {
      writeFileSync(join(withDir, `${skill}.md`), `# ${skill} — dry-run (no agent invoked)\n\nPrompt:\n${scenario}\n`);
      writeFileSync(join(withoutDir, `${skill}.md`), `# ${skill} — dry-run (no agent invoked)\n\nPrompt:\n${scenario}\n`);
      console.log(`scaffold ${skill}`);
      continue;
    }

    // with-skill project: install ONLY this skill (isolates its effect).
    const withProject = join(outRoot, ".projects", "with", skill);
    const withoutProject = join(outRoot, ".projects", "without", skill);
    for (const dir of [withProject, withoutProject]) rmSync(dir, { recursive: true, force: true });
    mkdirSync(withProject, { recursive: true });
    mkdirSync(withoutProject, { recursive: true });
    installSkill(withProject, skill);

    const prompt = `You are assisting on a product development task. Follow the task below.\n\nTask: ${scenario}`;
    const withResult = runAgent(agent, withProject, prompt, args.model);
    const withoutResult = runAgent(agent, withoutProject, prompt, args.model);

    const withOutput = withResult.stdout || withResult.stderr || "(no output)";
    const withoutOutput = withoutResult.stdout || withoutResult.stderr || "(no output)";
    writeFileSync(join(withDir, `${skill}.md`), withOutput);
    writeFileSync(join(withoutDir, `${skill}.md`), withoutOutput);
    console.log(`ran ${skill} (with=${withResult.status}, without=${withoutResult.status})`);
  }

  if (failures.length) {
    for (const f of failures) console.error(`FAIL ${f}`);
    process.exitCode = 1;
    return;
  }
  console.log(`\nDone. Grade with:\n  python3 scripts/evaluate.py --runs ${outRoot} --benchmark ${join(outRoot, "benchmark.json")}`);
}

main();
