#!/usr/bin/env node

import { createHash } from "node:crypto";
import {
  copyFileSync,
  cpSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  realpathSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const targets = {
  agents: ".agents/skills",
  claude: ".claude/skills",
  codex: ".codex/skills",
  cursor: ".cursor/skills",
  github: ".github/skills",
};

function usage() {
  console.log(`OpenCraft Skills ${readCollection().version}

Usage:
  opencraft-skills install [options]

Options:
  --project <path>       Target project root (default: current directory)
  --target <client>      agents, claude, codex, cursor, github, or all
  --mode <mode>          copy or link (default: copy)
  --with-project-files   Initialize AGENTS.md, PROJECT_CONTEXT.md, and .product/
  --force                Replace same-named installed skills
  --version              Print the package version
  --help                 Show this help
`);
}

function readCollection() {
  return JSON.parse(readFileSync(join(repository, "collection.json"), "utf8"));
}

function parseArgs(argv) {
  const args = { project: process.cwd(), target: "agents", mode: "copy", force: false, withProjectFiles: false };
  const tokens = [...argv];
  if (tokens[0] === "install") tokens.shift();
  while (tokens.length) {
    const token = tokens.shift();
    if (token === "--help" || token === "-h") return { help: true };
    if (token === "--version" || token === "-v") return { version: true };
    if (token === "--force") args.force = true;
    else if (token === "--with-project-files") args.withProjectFiles = true;
    else if (["--project", "--target", "--mode"].includes(token)) {
      if (!tokens.length) throw new Error(`${token} requires a value`);
      const key = token.slice(2);
      args[key] = tokens.shift();
    } else throw new Error(`unknown argument: ${token}`);
  }
  if (![...Object.keys(targets), "all"].includes(args.target)) throw new Error(`invalid target: ${args.target}`);
  if (!["copy", "link"].includes(args.mode)) throw new Error(`invalid mode: ${args.mode}`);
  return args;
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function verifyLock() {
  const lock = JSON.parse(readFileSync(join(repository, "skills.lock.json"), "utf8"));
  for (const [path, expected] of Object.entries(lock.files)) {
    const source = join(repository, path);
    if (!existsSync(source) || sha256(source) !== expected) throw new Error(`source integrity check failed: ${path}`);
  }
  return lock;
}

function removeExactTarget(path) {
  const stat = lstatSync(path);
  rmSync(path, { recursive: stat.isDirectory() && !stat.isSymbolicLink(), force: false });
}

function installSkill(source, destination, mode, force) {
  const target = join(destination, source.name);
  if (existsSync(target)) {
    if (!force) return `SKIP ${target} (exists; use --force to replace)`;
    removeExactTarget(target);
  }
  mkdirSync(destination, { recursive: true });
  if (mode === "copy") cpSync(source.path, target, { recursive: true });
  else {
    const sourceRelative = relative(destination, realpathSync(source.path));
    symlinkSync(sourceRelative, target, process.platform === "win32" ? "junction" : "dir");
  }
  return `OK   ${target}`;
}

function initializeProjectFiles(project) {
  const mappings = [
    [join(repository, "templates/AGENTS.md"), join(project, "AGENTS.md")],
    [join(repository, "templates/PROJECT_CONTEXT.md"), join(project, "PROJECT_CONTEXT.md")],
  ];
  for (const [source, target] of mappings) {
    if (existsSync(target)) console.log(`SKIP ${target} (exists)`);
    else {
      copyFileSync(source, target);
      console.log(`OK   ${target}`);
    }
  }
  const productTarget = join(project, ".product");
  if (existsSync(productTarget)) console.log(`SKIP ${productTarget} (exists)`);
  else {
    cpSync(join(repository, "templates/product"), productTarget, { recursive: true });
    console.log(`OK   ${productTarget}`);
  }
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
    if (args.help) return usage();
    if (args.version) return console.log(readCollection().version);
    const project = resolve(args.project);
    if (!existsSync(project) || !lstatSync(project).isDirectory()) throw new Error(`project does not exist: ${project}`);
    const lock = verifyLock();
    const skillRoot = join(repository, "skills");
    const skills = readdirSync(skillRoot, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && existsSync(join(skillRoot, entry.name, "SKILL.md")))
      .map((entry) => ({ name: entry.name, path: join(skillRoot, entry.name) }))
      .sort((a, b) => a.name.localeCompare(b.name));
    const selected = args.target === "all" ? Object.entries(targets) : [[args.target, targets[args.target]]];
    for (const [client, destination] of selected) {
      console.log(`[${client}]`);
      for (const skill of skills) console.log(installSkill(skill, join(project, destination), args.mode, args.force));
    }
    if (args.withProjectFiles) {
      console.log("[project]");
      initializeProjectFiles(project);
    }
    const receipt = {
      collection: lock.collection,
      mode: args.mode,
      skills: skills.map(({ name }) => name),
      source: lock.source,
      targets: selected.map(([name]) => name),
      version: lock.version,
    };
    writeFileSync(join(project, ".ai-skills-install.json"), `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  } catch (error) {
    console.error(`ERROR ${error.message}`);
    process.exitCode = 2;
  }
}

main();
