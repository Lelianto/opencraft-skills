import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { join, resolve } from "node:path";

const MODES = new Set(["off", "autonomous", "guided", "approval-gated"]);
const STATES = new Set([
  "IN_PROGRESS",
  "DECISION_REQUIRED",
  "APPROVAL_REQUIRED",
  "BLOCKED",
  "READY_TO_RESUME",
  "VERIFICATION_REQUIRED",
  "COMPLETE",
]);

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function timestamp() {
  return new Date().toISOString();
}

function parseOptions(tokens) {
  const options = { project: process.cwd(), json: false, force: false };
  const positionals = [];
  while (tokens.length) {
    const token = tokens.shift();
    if (token === "--json") options.json = true;
    else if (token === "--force") options.force = true;
    else if (["--project", "--mode", "--option", "--rationale", "--decided-by"].includes(token)) {
      if (!tokens.length) throw new Error(`${token} requires a value`);
      options[token.slice(2).replaceAll("-", "_")] = tokens.shift();
    } else if (token.startsWith("--")) throw new Error(`unknown argument: ${token}`);
    else positionals.push(token);
  }
  return { options, positionals };
}

function paths(projectInput) {
  const project = resolve(projectInput);
  const product = join(project, ".product");
  return {
    project,
    product,
    configPath: join(product, "human-loop.json"),
    statePath: join(product, "human-loop-state.json"),
    decisions: join(product, "decisions"),
  };
}

function requireWorkspace(projectInput) {
  const target = paths(projectInput);
  if (!existsSync(target.configPath) || !existsSync(target.statePath)) {
    throw new Error(`human loop is not initialized in ${target.project}; run opencraft-skills hitl init`);
  }
  const config = readJson(target.configPath);
  const state = readJson(target.statePath);
  if (!MODES.has(config.mode)) throw new Error(`invalid human-loop mode: ${config.mode}`);
  if (typeof config.enabled !== "boolean" || config.enabled !== (config.mode !== "off")) throw new Error("human-loop enabled flag must match mode");
  if (!STATES.has(state.status)) throw new Error(`invalid human-loop state: ${state.status}`);
  if (!Array.isArray(state.active_decision_ids)) throw new Error("human-loop active_decision_ids must be an array");
  return { ...target, config, state };
}

function decisionFiles(directory) {
  if (!existsSync(directory)) return [];
  return readdirSync(directory)
    .filter((name) => name.startsWith("DEC-") && name.endsWith(".json") && name !== "DEC-EXAMPLE-001.json")
    .sort()
    .map((name) => join(directory, name));
}

function validateDecision(decision, path) {
  const required = ["schema_version", "id", "level", "stage", "status", "question", "why_now", "options", "affected_artifacts", "created_at"];
  for (const field of required) if (!(field in decision)) throw new Error(`${path}: missing ${field}`);
  if (!/^DEC-[A-Z0-9]+-[0-9]{3,}$/.test(decision.id)) throw new Error(`${path}: invalid decision id`);
  if (!new Set(["D0", "D1", "D2", "D3"]).has(decision.level)) throw new Error(`${path}: invalid decision level`);
  if (!new Set(["example", "pending", "accepted", "rejected", "deferred", "superseded"]).has(decision.status)) throw new Error(`${path}: invalid decision status`);
  if (!Array.isArray(decision.options) || decision.options.length < 1) throw new Error(`${path}: options must not be empty`);
  for (const option of decision.options) {
    if (!option || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(option.id ?? "")) throw new Error(`${path}: invalid option id`);
    if (!option.label?.trim() || !option.tradeoffs?.trim()) throw new Error(`${path}: every option requires label and tradeoffs`);
  }
  const optionIds = new Set(decision.options.map((option) => option.id));
  if (optionIds.size !== decision.options.length) throw new Error(`${path}: option ids must be unique`);
  if (decision.recommendation && !optionIds.has(decision.recommendation)) throw new Error(`${path}: recommendation must reference an option`);
  if (decision.status === "accepted" && (!decision.decision || !optionIds.has(decision.decision))) throw new Error(`${path}: accepted decision must reference an option`);
  if (["accepted", "rejected", "deferred"].includes(decision.status)) {
    for (const field of ["decided_by", "decided_at", "rationale"]) if (!decision[field]) throw new Error(`${path}: ${decision.status} decision requires ${field}`);
  }
  return decision;
}

function loadDecisions(workspace) {
  return decisionFiles(workspace.decisions).map((path) => ({ path, decision: validateDecision(readJson(path), path) }));
}

function pendingSummary(workspace) {
  const pending = loadDecisions(workspace).filter(({ decision }) => decision.status === "pending").map(({ decision }) => decision);
  return {
    ids: pending.map((decision) => decision.id),
    status: pending.some((decision) => decision.level === "D3") ? "APPROVAL_REQUIRED" : "DECISION_REQUIRED",
  };
}

function saveState(workspace, status, activeIds, resume = workspace.state.resume) {
  workspace.state.status = status;
  workspace.state.active_decision_ids = [...new Set(activeIds)].sort();
  workspace.state.resume = resume;
  workspace.state.updated_at = timestamp();
  writeJson(workspace.statePath, workspace.state);
}

function initialize(repository, options) {
  const target = paths(options.project);
  const mode = options.mode ?? "guided";
  if (!MODES.has(mode)) throw new Error(`invalid mode: ${mode}`);
  mkdirSync(target.decisions, { recursive: true });
  const schemaTarget = join(target.product, "schemas");
  mkdirSync(schemaTarget, { recursive: true });
  const mappings = [
    [join(repository, "templates/product/human-loop.json"), target.configPath],
    [join(repository, "templates/product/human-loop-state.json"), target.statePath],
    [join(repository, "templates/product/decisions/README.md"), join(target.decisions, "README.md")],
    [join(repository, "templates/product/schemas/human-loop.schema.json"), join(schemaTarget, "human-loop.schema.json")],
    [join(repository, "templates/product/schemas/human-loop-state.schema.json"), join(schemaTarget, "human-loop-state.schema.json")],
    [join(repository, "templates/product/schemas/decision-record.schema.json"), join(schemaTarget, "decision-record.schema.json")],
  ];
  for (const [source, destination] of mappings) {
    if (!existsSync(destination) || options.force) copyFileSync(source, destination);
  }
  const config = readJson(target.configPath);
  config.enabled = mode !== "off";
  config.mode = mode;
  writeJson(target.configPath, config);
  console.log(`OK human loop initialized in ${target.product} (${mode})`);
}

function listDecisions(workspace, options) {
  const records = loadDecisions(workspace).map(({ decision }) => ({
    id: decision.id,
    level: decision.level,
    status: decision.status,
    stage: decision.stage,
    question: decision.question,
    decision: decision.decision ?? null,
  }));
  if (options.json) return console.log(JSON.stringify({ mode: workspace.config.mode, state: workspace.state.status, decisions: records }, null, 2));
  console.log(`Human loop: ${workspace.config.mode} · ${workspace.state.status}`);
  if (!records.length) return console.log("No decision records.");
  for (const record of records) console.log(`${record.id}  ${record.level}  ${record.status.padEnd(10)}  ${record.question}`);
}

function findDecision(workspace, id) {
  const path = join(workspace.decisions, `${id}.json`);
  if (!existsSync(path)) throw new Error(`decision not found: ${id}`);
  return { path, decision: validateDecision(readJson(path), path) };
}

function showDecision(workspace, id, options) {
  const { decision } = findDecision(workspace, id);
  if (options.json) return console.log(JSON.stringify(decision, null, 2));
  console.log(`${decision.id} · ${decision.level} · ${decision.status}`);
  console.log(`Question: ${decision.question}`);
  console.log(`Why now: ${decision.why_now}`);
  for (const option of decision.options) console.log(`- ${option.id}: ${option.label} — ${option.tradeoffs}`);
  if (decision.recommendation) console.log(`Recommendation: ${decision.recommendation}`);
  if (decision.decision) console.log(`Decision: ${decision.decision}`);
}

function addDecision(workspace, source, options) {
  const sourcePath = resolve(source);
  if (!existsSync(sourcePath)) throw new Error(`decision source not found: ${sourcePath}`);
  const decision = validateDecision(readJson(sourcePath), sourcePath);
  if (decision.status !== "pending") throw new Error("new decision records must have pending status");
  const target = join(workspace.decisions, `${decision.id}.json`);
  if (existsSync(target) && !options.force) throw new Error(`${decision.id} already exists; use --force only after reviewing its history`);
  writeJson(target, decision);
  const pending = pendingSummary(workspace);
  saveState(workspace, pending.status, pending.ids);
  console.log(`OK ${decision.id} added and workflow paused`);
}

function resolveDecision(workspace, id, options) {
  if (!options.option) throw new Error("decision resolve requires --option <id>");
  const { path, decision } = findDecision(workspace, id);
  if (decision.status !== "pending") throw new Error(`${id} is ${decision.status}; revise it before selecting a new option`);
  if (!decision.options.some((option) => option.id === options.option)) throw new Error(`unknown option ${options.option} for ${id}`);
  decision.status = "accepted";
  decision.decision = options.option;
  decision.decided_by = options.decided_by ?? "human";
  decision.decided_at = timestamp();
  decision.rationale = options.rationale ?? "Selected by the human decision owner.";
  writeJson(path, decision);
  const remaining = pendingSummary(workspace);
  saveState(workspace, remaining.ids.length ? remaining.status : "READY_TO_RESUME", remaining.ids);
  console.log(`OK ${id} accepted: ${options.option}`);
}

function deferDecision(workspace, id, options) {
  const { path, decision } = findDecision(workspace, id);
  if (decision.status !== "pending") throw new Error(`${id} is ${decision.status}; only pending decisions can be deferred`);
  decision.status = "deferred";
  decision.decided_by = options.decided_by ?? "human";
  decision.decided_at = timestamp();
  decision.rationale = options.rationale ?? "Deferred by the human decision owner.";
  writeJson(path, decision);
  const remaining = pendingSummary(workspace);
  saveState(workspace, remaining.ids.length ? remaining.status : "BLOCKED", remaining.ids);
  console.log(`OK ${id} deferred`);
}

function reviseDecision(workspace, id, options) {
  const { path, decision } = findDecision(workspace, id);
  decision.status = "pending";
  delete decision.decision;
  delete decision.decided_at;
  decision.decided_by = options.decided_by ?? "human";
  decision.rationale = options.rationale ?? "Reopened for revision by the human decision owner.";
  writeJson(path, decision);
  const pending = pendingSummary(workspace);
  saveState(workspace, pending.status, pending.ids);
  console.log(`OK ${id} reopened for revision`);
}

function resume(workspace, options) {
  const pending = loadDecisions(workspace).filter(({ decision }) => decision.status === "pending");
  if (pending.length) throw new Error(`cannot resume: pending decisions ${pending.map(({ decision }) => decision.id).join(", ")}`);
  if (["APPROVAL_REQUIRED", "DECISION_REQUIRED", "BLOCKED"].includes(workspace.state.status)) throw new Error(`cannot resume from ${workspace.state.status} without resolving the blocking condition`);
  const checkpoint = workspace.state.resume;
  const prompt = checkpoint
    ? `Resume OpenCraft at ${checkpoint.stage}. Next action: ${checkpoint.next_action}${checkpoint.skill ? ` Use $${checkpoint.skill}.` : ""}`
    : "Resume the OpenCraft workflow from current product artifacts. Inspect the decision ledger and choose the next bounded, unblocked action.";
  saveState(workspace, "IN_PROGRESS", [], checkpoint);
  if (options.json) console.log(JSON.stringify({ status: "IN_PROGRESS", prompt, checkpoint }, null, 2));
  else console.log(prompt);
}

function validateWorkspace(workspace, options) {
  const records = loadDecisions(workspace);
  const pendingIds = records.filter(({ decision }) => decision.status === "pending").map(({ decision }) => decision.id).sort();
  const activeIds = [...workspace.state.active_decision_ids].sort();
  if (pendingIds.join("\n") !== activeIds.join("\n")) {
    throw new Error(`state active_decision_ids does not match pending records: state=${activeIds.join(",") || "none"}, pending=${pendingIds.join(",") || "none"}`);
  }
  const hasPendingD3 = records.some(({ decision }) => decision.status === "pending" && decision.level === "D3");
  if (pendingIds.length && hasPendingD3 && workspace.state.status !== "APPROVAL_REQUIRED") throw new Error("pending D3 decisions require APPROVAL_REQUIRED state");
  if (pendingIds.length && !hasPendingD3 && !["DECISION_REQUIRED", "APPROVAL_REQUIRED"].includes(workspace.state.status)) throw new Error("pending decisions require a decision or approval state");
  if (!pendingIds.length && ["DECISION_REQUIRED", "APPROVAL_REQUIRED"].includes(workspace.state.status)) throw new Error(`${workspace.state.status} requires at least one pending decision`);
  const result = { mode: workspace.config.mode, state: workspace.state.status, decisions: records.length, pending: pendingIds.length };
  if (options.json) console.log(JSON.stringify(result, null, 2));
  else console.log(`PASS human loop: ${result.mode} · ${result.state} · ${result.decisions} decisions · ${result.pending} pending`);
}

export function decisionUsage() {
  console.log(`Human-in-the-loop commands:
  opencraft-skills hitl init [--mode off|autonomous|guided|approval-gated] [--project <path>] [--force]
  opencraft-skills hitl validate [--project <path>] [--json]
  opencraft-skills decisions [--project <path>] [--json]
  opencraft-skills decision add <record.json> [--project <path>] [--force]
  opencraft-skills decision show <DEC-ID> [--project <path>] [--json]
  opencraft-skills decision resolve <DEC-ID> --option <id> [--rationale <text>] [--decided-by <name>]
  opencraft-skills decision defer <DEC-ID> [--rationale <text>] [--decided-by <name>]
  opencraft-skills decision revise <DEC-ID> [--rationale <text>] [--decided-by <name>]
  opencraft-skills resume [--project <path>] [--json]`);
}

export function runDecisionCommand(repository, argv) {
  const command = argv[0];
  if (command === "hitl") {
    if (!["init", "validate"].includes(argv[1])) throw new Error("expected: hitl init or hitl validate");
    const action = argv[1];
    const { options, positionals } = parseOptions(argv.slice(2));
    if (positionals.length) throw new Error(`unexpected argument: ${positionals[0]}`);
    if (action === "init") return initialize(repository, options);
    return validateWorkspace(requireWorkspace(options.project), options);
  }
  const { options, positionals } = parseOptions(argv.slice(1));
  const workspace = requireWorkspace(options.project);
  if (command === "decisions") {
    if (positionals.length) throw new Error(`unexpected argument: ${positionals[0]}`);
    return listDecisions(workspace, options);
  }
  if (command === "resume") {
    if (positionals.length) throw new Error(`unexpected argument: ${positionals[0]}`);
    return resume(workspace, options);
  }
  if (command === "decision") {
    const [action, id, ...extra] = positionals;
    if (!action || !id || extra.length) throw new Error("decision requires an action and DEC-ID");
    if (action === "add") return addDecision(workspace, id, options);
    if (action === "show") return showDecision(workspace, id, options);
    if (action === "resolve") return resolveDecision(workspace, id, options);
    if (action === "defer") return deferDecision(workspace, id, options);
    if (action === "revise") return reviseDecision(workspace, id, options);
    throw new Error(`unknown decision action: ${action}`);
  }
  throw new Error(`unknown human-loop command: ${command}`);
}
