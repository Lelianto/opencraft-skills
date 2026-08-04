#!/usr/bin/env node

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const product = join(repository, "templates/product");

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function fail(message) {
  throw new Error(message);
}

try {
  const config = readJson(join(product, "human-loop.json"));
  const state = readJson(join(product, "human-loop-state.json"));
  const example = readJson(join(product, "decisions/DEC-EXAMPLE-001.json"));
  const schemas = readdirSync(join(product, "schemas")).filter((name) => name.endsWith(".schema.json"));
  if (schemas.length !== 3) fail(`expected 3 HITL schemas, found ${schemas.length}`);
  for (const name of schemas) {
    const schema = readJson(join(product, "schemas", name));
    if (schema.$schema !== "https://json-schema.org/draft/2020-12/schema") fail(`${name}: unsupported schema draft`);
    if (!schema.$id || !schema.title || schema.type !== "object") fail(`${name}: incomplete schema identity`);
  }
  if (!new Set(["off", "autonomous", "guided", "approval-gated"]).has(config.mode)) fail("invalid template mode");
  if (state.status !== "IN_PROGRESS" || !Array.isArray(state.active_decision_ids)) fail("invalid initial HITL state");
  if (example.status !== "example" || !/^DEC-[A-Z0-9]+-[0-9]{3,}$/.test(example.id)) fail("invalid decision example");
  console.log("PASS HITL templates and schemas");
} catch (error) {
  console.error(`FAIL HITL validation: ${error.message}`);
  process.exitCode = 1;
}
