#!/usr/bin/env node

/**
 * Smoke-test the packs-aware MCP server (scripts/pack-mcp.mjs).
 *
 * Materializes a sample `.lcdd/` in a temp project, then exercises the MCP
 * stdio transport: initialize, tools/list, and every tool call, asserting the
 * JSON-RPC responses carry the expected shape.
 */

import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const mcpBin = join(repository, "scripts", "pack-mcp.mjs");

function expect(condition, message) {
  if (!condition) throw new Error(message);
}

function materialize(projectDir) {
  writeFileSync(
    join(projectDir, "packs.yaml"),
    [
      "schema: https://opencraft.dev/schema/project-packs/v1",
      "extends:",
      "  - nextjs-pack@^1",
      "  - security-pack@^1",
      "  - fintech-pack@^1",
      "conflict_policy: fail",
      "",
    ].join("\n")
  );
  const result = spawnSync(process.execPath, [join(repository, "scripts", "packtool.mjs"), "packs", "install", "--project", projectDir], {
    cwd: repository,
    encoding: "utf8",
  });
  expect(result.status === 0, `materialize failed: ${result.stderr || result.stdout}`);
}

const messages = [
  { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "opencraft-mcp-test", version: "1" } } },
  { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} },
  { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "packs_list", arguments: {} } },
  { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "packs_resolve", arguments: {} } },
  { jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "packs_validate", arguments: { pack: "--all" } } },
  { jsonrpc: "2.0", id: 6, method: "tools/call", params: { name: "packs_doctor", arguments: {} } },
  { jsonrpc: "2.0", id: 7, method: "tools/call", params: { name: "contexts_query", arguments: { tags: "fintech,compliance" } } },
];

try {
  const projectDir = mkdtempSync(join(tmpdir(), "opencraft-packs-mcp-"));
  materialize(projectDir);

  const result = spawnSync(process.execPath, [mcpBin], {
    cwd: repository,
    env: { ...process.env, LCDD_PROJECT_ROOT: projectDir },
    input: messages.map((m) => JSON.stringify(m)).join("\n"),
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
  });
  expect(result.status === 0, `MCP server exited ${result.status}: ${result.stderr}`);

  const lines = result.stdout.split("\n").filter((l) => l.trim());
  const byId = new Map(lines.map((l) => [JSON.parse(l).id, JSON.parse(l)]));

  expect(byId.has(1) && byId.get(1).result?.capabilities?.tools, "initialize did not negotiate tools");

  const toolNames = (byId.get(2).result.tools || []).map((t) => t.name);
  for (const expected of ["packs_list", "packs_resolve", "packs_validate", "packs_doctor", "contexts_query"]) {
    expect(toolNames.includes(expected), `missing tool ${expected}`);
  }

  const body = (id) => JSON.parse(byId.get(id).result.content[0].text);

  expect(body(3).ok === true && Array.isArray(body(3).packs) && body(3).packs.length > 0, "packs_list did not return packs");
  expect(body(4).ok === true && Array.isArray(body(4).graph), "packs_resolve did not return a graph");
  expect(body(5).ok === true && Array.isArray(body(5).failures), "packs_validate did not return failures list");
  expect(body(6).overall_score > 0 && body(6).metrics.length === 8, "packs_doctor did not return 8 metrics");
  expect(body(7).total >= 4, `contexts_query tags=fintech,compliance returned ${body(7).total}, expected >= 4`);

  console.log(`PASS packs MCP server (${toolNames.length} tools, ${body(6).metrics.length} doctor metrics)`);
} catch (error) {
  console.error(`FAIL packs MCP: ${error.message}`);
  process.exitCode = 1;
}
