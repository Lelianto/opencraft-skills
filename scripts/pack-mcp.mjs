#!/usr/bin/env node

/**
 * OpenCraft Context Packs MCP server (zero-dependency, stdio transport).
 *
 * Exposes the pack engine to MCP-capable agents (Claude Desktop, Cursor,
 * Cline, ...). Tools map directly onto the packtool CLI:
 *
 *   - packs_list       Declared + resolved packs for a project.
 *   - packs_resolve    Resolved pack graph (extends, deps, precedence, conflicts).
 *   - packs_validate   Validate a pack or the whole collection.
 *   - packs_doctor     Context Health report (LCDD 0.5.0 8-metric parity).
 *   - contexts_query   Query materialized contexts by lifecycle/category/tags.
 *
 * The target project root comes from LCDD_PROJECT_ROOT, then --project, then
 * the current working directory.
 *
 * Run:
 *   node scripts/pack-mcp.mjs
 *
 * Register in claude_desktop_config.json:
 *   {
 *     "mcpServers": {
 *       "opencraft-packs": {
 *         "command": "node",
 *         "args": ["/absolute/path/to/scripts/pack-mcp.mjs"],
 *         "env": { "LCDD_PROJECT_ROOT": "/path/to/your/project" }
 *       }
 *     }
 *   }
 */

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PACKTOOL = join(REPO_ROOT, "scripts", "packtool.mjs");

function projectRoot() {
  const fromEnv = process.env.LCDD_PROJECT_ROOT;
  const projectFlag = (() => {
    const argv = process.argv.slice(2);
    for (let i = 0; i < argv.length; i++) {
      if (argv[i] === "--project" && argv[i + 1]) return argv[i + 1];
    }
    return null;
  })();
  if (fromEnv) return resolve(fromEnv);
  if (projectFlag) return resolve(projectFlag);
  return process.cwd();
}

function runPacktool(args, projectDir) {
  const result = spawnSync(process.execPath, [PACKTOOL, "packs", ...args, "--project", projectDir, "--json"], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    return { ok: false, error: (result.stderr || result.stdout || "packtool failed").trim() };
  }
  try {
    const parsed = JSON.parse(result.stdout);
    return parsed;
  } catch {
    return { ok: false, error: "packtool emitted non-JSON output" };
  }
}

const TOOLS = [
  {
    name: "packs_list",
    description: "List declared and resolved Context Packs for a project.",
    inputSchema: {
      type: "object",
      properties: { project: { type: "string", description: "Project root (defaults to LCDD_PROJECT_ROOT or cwd)" } },
    },
  },
  {
    name: "packs_resolve",
    description: "Resolve the pack graph: extends, dependencies, precedence, versions, and conflicts.",
    inputSchema: {
      type: "object",
      properties: { project: { type: "string" } },
    },
  },
  {
    name: "packs_validate",
    description: "Validate a specific pack (or all reference packs with '--all') against the pack schemas.",
    inputSchema: {
      type: "object",
      properties: {
        pack: { type: "string", description: "Pack name to validate, or '--all' for every reference pack" },
        project: { type: "string" },
      },
      required: ["pack"],
    },
  },
  {
    name: "packs_doctor",
    description: "Context Health report over a project's .lcdd/ registry (LCDD 0.5.0 8-metric format: stale contexts, owners, conflicts, deprecation, drafts, authority, tags, review).",
    inputSchema: {
      type: "object",
      properties: { project: { type: "string" } },
    },
  },
  {
    name: "contexts_query",
    description: "Query materialized contexts in a project's .lcdd/ registry by lifecycle, category, or tags.",
    inputSchema: {
      type: "object",
      properties: {
        lifecycle: { type: "string", enum: ["draft", "candidate", "approved", "active", "deprecated", "archived"] },
        category: { type: "string" },
        tags: { type: "string", description: "Comma-separated tags" },
        project: { type: "string" },
      },
    },
  },
];

function extractContextFields(yamlText) {
  const get = (key) => {
    const match = yamlText.match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
    return match ? match[1].trim().replace(/^["']|["']$/g, "") : undefined;
  };
  const flowMatch = yamlText.match(/^tags:\s*\[(.*)\]$/m);
  const blockMatch = yamlText.match(/^tags:\s*$/m);
  let tags = [];
  if (flowMatch) {
    tags = flowMatch[1].split(",").map((t) => t.trim().replace(/^["']|["']$/g, "")).filter(Boolean);
  } else if (blockMatch) {
    const from = blockMatch.index + blockMatch[0].length;
    const rest = yamlText.slice(from).split(/\n\S/)[0];
    tags = (rest.match(/^\s*-\s*(.+)$/gm) || [])
      .map((t) => t.replace(/^\s*-\s*/, "").replace(/^["']|["']$/g, "").trim())
      .filter(Boolean);
  }
  return { id: get("id"), title: get("title"), category: get("category"), severity: get("severity"), lifecycle: get("lifecycle"), tags };
}

function handleTool(name, args, projectDir) {
  switch (name) {
    case "packs_list": {
      const result = runPacktool(["status"], projectDir);
      return result;
    }
    case "packs_resolve": {
      const result = runPacktool(["resolve", "--dry-run"], projectDir);
      return result;
    }
    case "packs_validate": {
      const target = args.pack || "--all";
      const result = runPacktool(["validate", target], projectDir);
      return result;
    }
    case "packs_doctor": {
      const result = runPacktool(["doctor"], projectDir);
      if (!existsSync(join(projectDir, ".lcdd", "contexts"))) {
        return { ok: false, error: "no .lcdd installed; run `opencraft-packs packs bootstrap` or install with --with-project-files" };
      }
      return result;
    }
    case "contexts_query": {
      const contextsDir = join(projectDir, ".lcdd", "contexts");
      if (!existsSync(contextsDir)) {
        return { ok: false, error: "no .lcdd installed; run `opencraft-packs packs bootstrap` or install with --with-project-files" };
      }
      const results = [];
      for (const file of readdirSync(contextsDir).filter((f) => f.endsWith(".yaml"))) {
        const ctx = extractContextFields(readFileSync(join(contextsDir, file), "utf8"));
        if (!ctx.id) continue;
        if (args.lifecycle && ctx.lifecycle !== args.lifecycle) continue;
        if (args.category && ctx.category !== args.category) continue;
        if (args.tags) {
          const want = args.tags.split(",").map((t) => t.trim()).filter(Boolean);
          if (!want.every((t) => ctx.tags.includes(t))) continue;
        }
        results.push({ id: ctx.id, title: ctx.title, category: ctx.category, severity: ctx.severity, lifecycle: ctx.lifecycle, tags: ctx.tags });
      }
      return { ok: true, total: results.length, contexts: results };
    }
    default:
      return { ok: false, error: `unknown tool ${name}` };
  }
}

function text(content) {
  return { type: "text", text: typeof content === "string" ? content : JSON.stringify(content, null, 2) };
}

function respond(id, result) {
  process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id, result }) + "\n");
}

function respondError(id, error) {
  process.stdout.write(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32603, message: error.message || String(error) } }) + "\n");
}

const rl = createInterface({ input: process.stdin });

rl.on("line", (line) => {
  line = line.trim();
  if (!line) return;
  let message;
  try {
    message = JSON.parse(line);
  } catch {
    return;
  }
  const { id, method, params = {} } = message;

  if (method === "initialize") {
    respond(id, {
      protocolVersion: params.protocolVersion || "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "opencraft-packs", version: "1.0.0" },
    });
    return;
  }
  if (method === "notifications/initialized" || method === "ping") {
    return;
  }
  if (method === "tools/list") {
    respond(id, { tools: TOOLS });
    return;
  }
  if (method === "tools/call") {
    try {
      const result = handleTool(params.name, params.arguments || {}, projectRoot());
      respond(id, { content: [text(result)] });
    } catch (error) {
      respondError(id, error);
    }
    return;
  }
  respondError(id, new Error(`unknown method ${method}`));
});

rl.on("close", () => process.exit(0));
