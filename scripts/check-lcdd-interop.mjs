#!/usr/bin/env node

/**
 * LCDD interoperability regression check.
 *
 * Materializes a sample `.lcdd/` Context Registry with the pack engine, then
 * proves the claim that the materialized registry is consumable by the real
 * LCDD npm packages (`@lcdd/cli` and `@lcdd/mcp`) without modification:
 *
 *   - `lcd list`        reads every materialized context
 *   - `lcd validate`    accepts the registry (JSON Schema + semantic rules)
 *   - `lcd doctor`      computes a health report from the registry
 *   - `lcdd-mcp`        exposes the contexts over Model Context Protocol tools
 *
 * Usage:
 *   node scripts/check-lcdd-interop.mjs [--lcdd-bin <path>] [--mcp-bin <path>]
 *
 * The `--lcdd-bin` and `--mcp-bin` flags point at the installed binaries
 * (default: `lcd` and `lcdd-mcp` from PATH). The project under test is always
 * created in a temporary directory, so nothing in the working tree is touched.
 */

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, writeFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function parseArgs(argv) {
  const args = { lcddBin: "lcd", mcpBin: "lcdd-mcp" };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--lcdd-bin") args.lcddBin = argv[++i];
    else if (argv[i] === "--mcp-bin") args.mcpBin = argv[++i];
    else throw new Error(`unknown argument: ${argv[i]}`);
  }
  return args;
}

function run(bin, args, options = {}) {
  const result = spawnSync(bin, args, {
    cwd: options.cwd,
    encoding: "utf8",
    env: options.env,
  });
  return { status: result.status, stdout: result.stdout || "", stderr: result.stderr || "" };
}

function materialize(projectDir) {
  mkdirSync(projectDir, { recursive: true });
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
  const result = spawnSync(
    process.execPath,
    [join(repository, "scripts", "packtool.mjs"), "packs", "install", "--project", projectDir],
    { cwd: repository, encoding: "utf8" }
  );
  if (result.status !== 0) {
    throw new Error(`pack engine failed: ${result.stderr || result.stdout}`);
  }
  for (const dir of ["contexts", "project", "ai"]) {
    if (!existsSync(join(projectDir, ".lcdd", dir))) {
      throw new Error(`pack engine did not materialize .lcdd/${dir}`);
    }
  }
}

function expect(condition, message) {
  if (!condition) throw new Error(message);
  return true;
}

function checkCli(bin, projectDir) {
  const env = { ...process.env };
  const list = run(bin, ["list"], { cwd: projectDir, env });
  expect(list.status === 0, `lcd list exited ${list.status}: ${list.stderr}`);
  expect(/\bctx-(?:nextjs|security|fintech|react|typescript|node|testing)-[a-z0-9-]+\b/.test(list.stdout),
    `lcd list did not surface materialized contexts:\n${list.stdout.slice(0, 500)}`);

  const validate = run(bin, ["validate"], { cwd: projectDir, env });
  expect(validate.status === 0, `lcd validate exited ${validate.status}: ${validate.stderr || validate.stdout}`);
  expect(/passed/i.test(validate.stdout) || validate.status === 0,
    `lcd validate did not report a passing result: ${validate.stdout.slice(0, 300)}`);

  const doctor = run(bin, ["doctor", "--json"], { cwd: projectDir, env });
  expect(doctor.status === 0, `lcd doctor exited ${doctor.status}: ${doctor.stderr}`);
  let report;
  try {
    report = JSON.parse(doctor.stdout);
  } catch (error) {
    throw new Error(`lcd doctor --json did not emit valid JSON: ${error.message}`);
  }
  expect(Array.isArray(report.metrics) && report.metrics.length > 0, "lcd doctor: no metrics");
  expect(typeof report.overall_score === "number", "lcd doctor: no overall_score");
}

function mcpSession(bin, projectDir, messages) {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, [], {
      cwd: projectDir,
      env: { ...process.env, LCDD_PROJECT_ROOT: projectDir },
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`lcdd-mcp exited ${code}: ${stderr}`));
        return;
      }
      try {
        resolve(
          stdout
            .split("\n")
            .filter((line) => line.trim())
            .map((line) => JSON.parse(line))
        );
      } catch (error) {
        reject(new Error(`MCP output not valid JSON lines: ${error.message}`));
      }
    });

    let index = 0;
    function writeNext() {
      if (index < messages.length) {
        child.stdin.write(messages[index++] + "\n");
        setTimeout(writeNext, 150);
      } else {
        child.stdin.end();
      }
    }
    writeNext();
  });
}

async function checkMcp(bin, projectDir) {
  const messages = [
    JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "opencraft-interop", version: "1" } } }),
    JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }),
    JSON.stringify({ jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "lcdd_list_contexts", arguments: {} } }),
    JSON.stringify({ jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "lcdd_query_contexts", arguments: { query: "SELECT * FROM contexts WHERE lifecycle = 'active' AND category = 'security'" } } }),
    JSON.stringify({ jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "lcdd_get_health", arguments: {} } }),
  ];

  const lines = await mcpSession(bin, projectDir, messages);

  const byId = new Map(lines.map((line) => [line.id, line]));
  expect(byId.has(1) && byId.get(1).result && byId.get(1).result.capabilities?.tools,
    "MCP: initialize did not negotiate tools capability");

  const toolNames = (byId.get(2).result.tools || []).map((tool) => tool.name);
  for (const expected of ["lcdd_list_contexts", "lcdd_get_context", "lcdd_query_contexts", "lcdd_validate_artifact", "lcdd_get_health"]) {
    expect(toolNames.includes(expected), `MCP: missing tool ${expected}`);
  }

  const listText = byId.get(3).result.content?.[0]?.text || "";
  expect(/\"total\":\s*[1-9][0-9]*/.test(listText), "MCP lcdd_list_contexts returned no contexts");

  const queryText = byId.get(4).result.content?.[0]?.text || "";
  expect(/"id":\s*"ctx-security-/.test(queryText), "MCP lcdd_query_contexts did not filter security contexts");

  const healthText = byId.get(5).result.content?.[0]?.text || "";
  expect(/"overall_score"/.test(healthText), "MCP lcdd_get_health did not return a health report");
}

try {
  const args = parseArgs(process.argv.slice(2));
  const projectDir = mkdtempSync(join(tmpdir(), "opencraft-lcdd-interop-"));

  materialize(projectDir);
  const contextsDir = join(projectDir, ".lcdd", "contexts");
  const count = readdirSync(contextsDir).filter((name) => name.endsWith(".yaml")).length;
  expect(count >= 3, `expected materialized contexts, found ${count}`);

  checkCli(args.lcddBin, projectDir);
  await checkMcp(args.mcpBin, projectDir);

  console.log(`PASS LCDD interop (${count} contexts readable by ${args.lcddBin} + ${args.mcpBin})`);
} catch (error) {
  console.error(`FAIL LCDD interop: ${error.message}`);
  process.exitCode = 1;
}
