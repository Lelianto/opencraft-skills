#!/usr/bin/env node

import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cli = join(repository, "scripts/install.mjs");
const project = mkdtempSync(join(tmpdir(), "opencraft-hitl-"));

function run(args) {
  return execFileSync(process.execPath, [cli, ...args, "--project", project], { encoding: "utf8" });
}

run(["hitl", "init", "--mode", "guided"]);
if (!readFileSync(join(project, ".product/schemas/decision-record.schema.json"), "utf8").includes("OpenCraft Decision Record")) throw new Error("decision schema was not initialized");
const decisions = join(project, ".product/decisions");
mkdirSync(decisions, { recursive: true });
const record = {
  schema_version: "1.0",
  id: "DEC-DESIGN-001",
  level: "D2",
  stage: "experience-design",
  status: "pending",
  question: "Which mobile navigation direction should be implemented?",
  why_now: "The first implementation slice depends on this choice.",
  options: [
    { id: "bottom-navigation", label: "Bottom navigation", tradeoffs: "Reachable on mobile; reserves vertical space." },
    { id: "top-navigation", label: "Top navigation", tradeoffs: "More content space; less thumb-reachable." }
  ],
  recommendation: "bottom-navigation",
  affected_artifacts: ["EXP-NAV-001"],
  created_at: new Date().toISOString()
};
const pendingSource = join(project, "pending-decision.json");
writeFileSync(pendingSource, `${JSON.stringify(record, null, 2)}\n`);
const statePath = join(project, ".product/human-loop-state.json");
const state = JSON.parse(readFileSync(statePath, "utf8"));
state.resume = { stage: "experience-design", next_action: "Implement the chosen navigation", skill: "design-product-experience" };
state.updated_at = new Date().toISOString();
writeFileSync(statePath, `${JSON.stringify(state, null, 2)}\n`);
run(["decision", "add", pendingSource]);
const approvalRecord = {
  ...record,
  id: "DEC-SECURITY-002",
  level: "D3",
  stage: "security-review",
  question: "Should the documented residual security risk be accepted for release?",
  why_now: "Release readiness cannot be decided without the risk owner.",
  options: [
    { id: "reject-risk", label: "Reject risk", tradeoffs: "Blocks release; requires mitigation." },
    { id: "accept-risk", label: "Accept risk", tradeoffs: "Allows release; preserves material residual exposure." }
  ],
  recommendation: "reject-risk"
};
const approvalSource = join(project, "pending-approval.json");
writeFileSync(approvalSource, `${JSON.stringify(approvalRecord, null, 2)}\n`);
run(["decision", "add", approvalSource]);

const before = JSON.parse(run(["decisions", "--json"]));
if (before.decisions.length !== 2 || before.state !== "APPROVAL_REQUIRED") throw new Error("pending decisions and D3 approval state were not listed");
run(["hitl", "validate"]);
run(["decision", "resolve", record.id, "--option", "bottom-navigation", "--rationale", "Best fit for frequent one-handed use"]);
const after = JSON.parse(run(["decision", "show", record.id, "--json"]));
if (after.status !== "accepted" || after.decision !== "bottom-navigation") throw new Error("decision was not resolved");
const afterD2State = JSON.parse(run(["decisions", "--json"]));
if (afterD2State.state !== "APPROVAL_REQUIRED") throw new Error("resolving D2 must not clear a pending D3 approval");
run(["decision", "resolve", approvalRecord.id, "--option", "reject-risk", "--rationale", "Mitigation is required before release"]);
const resume = JSON.parse(run(["resume", "--json"]));
if (resume.status !== "IN_PROGRESS" || !resume.prompt.includes("experience-design")) throw new Error("resume checkpoint was not emitted");
run(["decision", "revise", record.id, "--rationale", "New usability evidence"]);
const revised = JSON.parse(run(["decision", "show", record.id, "--json"]));
if (revised.status !== "pending") throw new Error("decision was not reopened");
run(["decision", "defer", record.id, "--rationale", "Awaiting usability evidence"]);
const blocked = spawnSync(process.execPath, [cli, "resume", "--json", "--project", project], { encoding: "utf8" });
if (blocked.status === 0 || !blocked.stderr.includes("cannot resume from BLOCKED")) throw new Error("resume should fail while the workflow is blocked");

console.log("PASS HITL CLI init, add, list, validate, resolve, resume, revise, defer, and blocking");
