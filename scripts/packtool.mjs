#!/usr/bin/env node
// OpenCraft Context Packs CLI (Node, zero-dependency, behaviorally equivalent
// to scripts/packtool.py). Usage: node scripts/packtool.mjs packs <command>

import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PACKS_ROOT = join(REPO_ROOT, "packs");
const SCHEMA_URL = "https://opencraft.dev/schema/project-packs/v1";
const CORE_PACK = "core-pack@^1";

function ensurePacksYaml(projectDir) {
  const path = join(projectDir, "packs.yaml");
  if (existsSync(path)) return false;
  writeFileSync(
    path,
    "schema: https://opencraft.dev/schema/project-packs/v1\n" +
      `extends:\n  - ${CORE_PACK}\nconflict_policy: fail\n`,
    "utf8"
  );
  return true;
}

// ---------------------------------------------------------------------------
// Minimal YAML subset (mirrors packlib/yamlmini.py)
// ---------------------------------------------------------------------------

class YAMLError extends Error {}

const PLAIN_NULL = new Set(["null", "Null", "NULL", "~"]);
const PLAIN_TRUE = new Set(["true", "True", "TRUE"]);
const PLAIN_FALSE = new Set(["false", "False", "FALSE"]);
const BLOCK_MARKERS = new Set(["|", ">", "|-", "|+", ">-", ">+"]);

function indentOf(line) {
  return line.length - line.trimStart().length;
}

function skipBlank(lines, i) {
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }
    if (line.trimStart().startsWith("#")) {
      i += 1;
      continue;
    }
    break;
  }
  return i;
}

function parseQuoted(s, i) {
  const q = s[i];
  i += 1;
  const out = [];
  while (i < s.length) {
    const c = s[i];
    if (q === "'") {
      if (c === "'") {
        if (s[i + 1] === "'") {
          out.push("'");
          i += 2;
          continue;
        }
        return [out.join(""), i + 1];
      }
      out.push(c);
      i += 1;
    } else {
      if (c === "\\") {
        const nxt = s[i + 1] ?? "";
        const map = { n: "\n", t: "\t", "\\": "\\", '"': '"', 0: "\0", "'": "'" };
        if (nxt in map) {
          out.push(map[nxt]);
          i += 2;
        } else if (nxt === "u") {
          out.push(String.fromCharCode(parseInt(s.slice(i + 2, i + 6), 16)));
          i += 6;
        } else if (nxt) {
          out.push(nxt);
          i += 2;
        } else throw new YAMLError("unterminated escape");
        continue;
      }
      if (c === '"') return [out.join(""), i + 1];
      out.push(c);
      i += 1;
    }
  }
  throw new YAMLError("unterminated quoted string");
}

function findKeyColon(s) {
  if (!s) return -1;
  if (s[0] === '"' || s[0] === "'") {
    const [, end] = parseQuoted(s, 0);
    let e = end;
    while (e < s.length && s[e] === " ") e += 1;
    return e < s.length && s[e] === ":" ? e : -1;
  }
  let depth = 0;
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === '"' || c === "'") {
      [, i] = parseQuoted(s, i);
      continue;
    }
    if (c === "[" || c === "{") depth += 1;
    else if (c === "]" || c === "}") depth -= 1;
    else if (c === ":" && depth === 0) {
      const key = s.slice(0, i);
      const nxt = s.slice(i + 1);
      if (key && !key.includes(" ") && !key.includes("://") && (nxt === "" || nxt.startsWith(" "))) return i;
      return -1;
    }
    i += 1;
  }
  return -1;
}

function plain(s) {
  if (PLAIN_NULL.has(s)) return null;
  if (PLAIN_TRUE.has(s)) return true;
  if (PLAIN_FALSE.has(s)) return false;
  if (/^[-+]?[0-9]+$/.test(s)) return parseInt(s, 10);
  if (/^[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+[eE][-+]?[0-9]+)$/.test(s)) return parseFloat(s);
  return s;
}

function marker(rest) {
  const literal = rest.startsWith("|");
  const chomp = rest.endsWith("-") ? "strip" : rest.endsWith("+") ? "keep" : "clip";
  return [literal, chomp];
}

function fold(lines) {
  const out = [];
  let prevEmpty = true;
  for (const ln of lines) {
    if (ln === "") {
      out.push("");
      prevEmpty = true;
    } else if (out.length && !prevEmpty && out[out.length - 1] !== "") {
      out[out.length - 1] += " " + ln;
      prevEmpty = false;
    } else {
      out.push(ln);
      prevEmpty = false;
    }
  }
  let text = out.join("\n");
  if (lines.length) text += "\n";
  return text;
}

function scalarBody(lines, i, parentIndent, literal, chomp) {
  const raw = [];
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      raw.push("");
      i += 1;
      continue;
    }
    const ind = indentOf(line);
    if (ind <= parentIndent) break;
    raw.push(line);
    i += 1;
  }
  let minIndent = null;
  for (const ln of raw) {
    if (ln.trim()) {
      const ind = indentOf(ln);
      if (minIndent === null || ind < minIndent) minIndent = ind;
    }
  }
  let body = raw.map((ln) => (ln.trim() ? ln.slice(minIndent) : ""));
  while (body.length && body[0] === "") body.shift();
  if (chomp !== "keep") while (body.length && body[body.length - 1] === "") body.pop();
  if (literal) {
    const text = body.join("\n");
    return [body.length ? text + "\n" : text, i];
  }
  return [fold(body), i];
}

function inline(s) {
  s = s.trim();
  if (!s) return null;
  if (s[0] === "[") return flowSeq(s, 0)[0];
  if (s[0] === "{") return flowMap(s, 0)[0];
  if (s[0] === '"' || s[0] === "'") return parseQuoted(s, 0)[0];
  if (s.includes(" #")) s = s.split(" #", 1)[0].trim();
  return plain(s);
}

function flowSeq(s, i) {
  while (s[i] === " " || s[i] === "\t") i += 1;
  if (s[i] !== "[") throw new YAMLError("expected [ for flow sequence");
  i += 1;
  const result = [];
  for (;;) {
    while (s[i] === " " || s[i] === "\t") i += 1;
    if (i >= s.length) throw new YAMLError("unterminated flow sequence");
    const c = s[i];
    if (c === "]") return [result, i + 1];
    if (c === "[") {
      const [v, ni] = flowSeq(s, i);
      result.push(v);
      i = ni;
    } else if (c === "{") {
      const [v, ni] = flowMap(s, i);
      result.push(v);
      i = ni;
    } else if (c === '"' || c === "'") {
      const [v, ni] = parseQuoted(s, i);
      result.push(v);
      i = ni;
    } else {
      const start = i;
      while (i < s.length && s[i] !== "," && s[i] !== "]") i += 1;
      const tok = s.slice(start, i).trim();
      if (!tok) throw new YAMLError("empty flow sequence item");
      result.push(plain(tok));
    }
    while (s[i] === " " || s[i] === "\t") i += 1;
    if (s[i] === ",") {
      i += 1;
      continue;
    }
    if (s[i] === "]") return [result, i + 1];
    throw new YAMLError("expected , or ] in flow sequence");
  }
}

function flowMap(s, i) {
  while (s[i] === " " || s[i] === "\t") i += 1;
  if (s[i] !== "{") throw new YAMLError("expected { for flow map");
  i += 1;
  const result = {};
  for (;;) {
    while (s[i] === " " || s[i] === "\t") i += 1;
    if (i >= s.length) throw new YAMLError("unterminated flow map");
    if (s[i] === "}") return [result, i + 1];
    let key;
    if (s[i] === '"' || s[i] === "'") [key, i] = parseQuoted(s, i);
    else {
      const start = i;
      while (i < s.length && s[i] !== ":" && s[i] !== "," && s[i] !== "}") i += 1;
      key = s.slice(start, i).trim();
    }
    while (s[i] === " " || s[i] === "\t") i += 1;
    if (s[i] !== ":") throw new YAMLError("expected : in flow map");
    i += 1;
    while (s[i] === " " || s[i] === "\t") i += 1;
    const c = s[i];
    let v;
    if (c === "[") [v, i] = flowSeq(s, i);
    else if (c === "{") [v, i] = flowMap(s, i);
    else if (c === '"' || c === "'") [v, i] = parseQuoted(s, i);
    else {
      const start = i;
      while (i < s.length && s[i] !== "," && s[i] !== "}") i += 1;
      const tok = s.slice(start, i).trim();
      v = tok ? plain(tok) : null;
    }
    result[key] = v;
    while (s[i] === " " || s[i] === "\t") i += 1;
    if (s[i] === ",") {
      i += 1;
      continue;
    }
    if (s[i] === "}") return [result, i + 1];
    throw new YAMLError("expected , or } in flow map");
  }
}

function assign(lines, i, indent, target, key, rest) {
  if (BLOCK_MARKERS.has(rest)) {
    const [literal, chomp] = marker(rest);
    const [body, ni] = scalarBody(lines, i + 1, indent, literal, chomp);
    target[key] = body;
    return ni;
  }
  if (rest === "") {
    const ni = skipBlank(lines, i + 1);
    if (ni < lines.length && indentOf(lines[ni]) > indent) {
      const [sub, after] = node(lines, ni, indentOf(lines[ni]));
      target[key] = sub;
      return after;
    }
    target[key] = null;
    return i + 1;
  }
  target[key] = inline(rest);
  return i + 1;
}

function node(lines, i, indent) {
  i = skipBlank(lines, i);
  if (i >= lines.length) return [null, i];
  const ind = indentOf(lines[i]);
  if (ind < indent) return [null, i];
  const content = lines[i].slice(ind);
  if (content === "-" || content.startsWith("- ")) return sequence(lines, i, ind);
  if (findKeyColon(content) >= 0) return mapping(lines, i, ind);
  if (!content.trim()) return [null, i];
  throw new YAMLError(`cannot parse block at line ${i + 1}: ${JSON.stringify(content)}`);
}

function mapping(lines, i, indent) {
  const result = {};
  for (;;) {
    i = skipBlank(lines, i);
    if (i >= lines.length) break;
    const ind = indentOf(lines[i]);
    if (ind !== indent) break;
    const content = lines[i].slice(ind);
    if (content === "-" || content.startsWith("- ")) break;
    const idx = findKeyColon(content);
    if (idx < 0) break;
    let key = content.slice(0, idx);
    if (key[0] === '"' || key[0] === "'") [key] = parseQuoted(key, 0);
    key = key.trim();
    const rest = content.slice(idx + 1).trim();
    i = assign(lines, i, indent, result, key, rest);
  }
  return [result, i];
}

function sequence(lines, i, indent) {
  const result = [];
  for (;;) {
    i = skipBlank(lines, i);
    if (i >= lines.length) break;
    const ind = indentOf(lines[i]);
    if (ind !== indent) break;
    const content = lines[i].slice(ind);
    if (content !== "-" && !content.startsWith("- ")) break;
    const rest = content.length > 1 ? content.slice(2).trim() : "";
    if (rest === "") {
      const ni = skipBlank(lines, i + 1);
      if (ni < lines.length && indentOf(lines[ni]) > indent) {
        const [sub, after] = node(lines, ni, indentOf(lines[ni]));
        result.push(sub);
        i = after;
      } else {
        result.push(null);
        i += 1;
      }
      continue;
    }
    const idx = findKeyColon(rest);
    if (idx < 0) {
      result.push(inline(rest));
      i += 1;
      continue;
    }
    const item = {};
    let key = rest.slice(0, idx).trim();
    if (key[0] === '"' || key[0] === "'") [key] = parseQuoted(key, 0);
    const r2 = rest.slice(idx + 1).trim();
    i = assign(lines, i, indent, item, key, r2);
    const keyIndent = indent + 2;
    for (;;) {
      const j = skipBlank(lines, i);
      if (j >= lines.length) {
        i = j;
        break;
      }
      if (indentOf(lines[j]) !== keyIndent) break;
      const c2 = lines[j].slice(keyIndent);
      if (c2 === "-" || c2.startsWith("- ")) break;
      const idx2 = findKeyColon(c2);
      if (idx2 < 0) break;
      let k2 = c2.slice(0, idx2).trim();
      if (k2[0] === '"' || k2[0] === "'") [k2] = parseQuoted(k2, 0);
      const r3 = c2.slice(idx2 + 1).trim();
      i = assign(lines, j, keyIndent, item, k2, r3);
    }
    result.push(item);
  }
  return [result, i];
}

function parseYaml(text) {
  if (!text) return null;
  if (text.startsWith("\ufeff")) text = text.slice(1);
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = text.split("\n");
  return node(lines, 0, 0)[0];
}

function loadYamlFile(path) {
  return parseYaml(readFileSync(path, "utf8"));
}

// Emitter (deterministic)
function needsQuote(s) {
  if (s === "" || s !== s.trim()) return true;
  if (/[{}[\],:&*#?|>!%@`"'\\\n\t]/.test(s)) return true;
  if (/^[-?:,[\]{}#&*!|>'\"%@`]/.test(s)) return true;
  if (/^[-+]?[0-9]+$/.test(s)) return true;
  if (/^[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+[eE][-+]?[0-9]+)$/.test(s)) return true;
  if (PLAIN_NULL.has(s) || PLAIN_TRUE.has(s) || PLAIN_FALSE.has(s)) return true;
  return false;
}

function quote(s) {
  let out = '"';
  for (const c of s) {
    if (c === '"') out += '\\"';
    else if (c === "\\") out += "\\\\";
    else if (c === "\n") out += "\\n";
    else if (c === "\t") out += "\\t";
    else out += c;
  }
  return out + '"';
}

function keyStr(k) {
  const s = String(k);
  return needsQuote(s) ? quote(s) : s;
}

function valStr(v) {
  if (v === null || v === undefined) return "null";
  if (v === true) return "true";
  if (v === false) return "false";
  if (typeof v === "number") return String(v);
  const s = String(v);
  return needsQuote(s) ? quote(s) : s;
}

function emitBlockLines(text, level, indent, out) {
  const pad = " ".repeat(indent * level);
  for (const ln of text.split("\n")) out.push(pad + ln);
}

function emitList(value, level, indent, out) {
  const pad = " ".repeat(indent * level);
  for (const item of value) {
    if (item && typeof item === "object" && !Array.isArray(item)) {
      if (Object.keys(item).length === 0) {
        out.push(`${pad}- {}`);
        continue;
      }
      let first = true;
      for (const key of Object.keys(item)) {
        const k = keyStr(key);
        const val = item[key];
        const head = first ? `${pad}- ${k}` : `${pad}${" ".repeat(indent)}${k}`;
        if (val && typeof val === "object" && !Array.isArray(val)) {
          if (Object.keys(val).length === 0) out.push(`${head}: {}`);
          else {
            out.push(`${head}:`);
            emit(val, level + 2, indent, out);
          }
        } else if (Array.isArray(val)) {
          if (val.length === 0) out.push(`${head}: []`);
          else {
            out.push(`${head}:`);
            emitList(val, level + 2, indent, out);
          }
        } else if (typeof val === "string" && val.includes("\n")) {
          out.push(`${head}: |`);
          emitBlockLines(val, level + 2, indent, out);
        } else {
          out.push(`${head}: ${valStr(val)}`);
        }
        first = false;
      }
    } else if (Array.isArray(item)) {
      out.push(`${pad}-`);
      emitList(item, level + 1, indent, out);
    } else if (typeof item === "string" && item.includes("\n")) {
      out.push(`${pad}- |`);
      emitBlockLines(item, level + 1, indent, out);
    } else {
      out.push(`${pad}- ${valStr(item)}`);
    }
  }
}

function emit(value, level, indent, out) {
  const pad = " ".repeat(indent * level);
  if (value && typeof value === "object" && !Array.isArray(value)) {
    if (Object.keys(value).length === 0) {
      out.push(`${pad}{}`);
      return;
    }
    for (const key of Object.keys(value)) {
      const k = keyStr(key);
      const val = value[key];
      if (val && typeof val === "object" && !Array.isArray(val)) {
        if (Object.keys(val).length === 0) out.push(`${pad}${k}: {}`);
        else {
          out.push(`${pad}${k}:`);
          emit(val, level + 1, indent, out);
        }
      } else if (Array.isArray(val)) {
        if (val.length === 0) out.push(`${pad}${k}: []`);
        else {
          out.push(`${pad}${k}:`);
          emitList(val, level + 1, indent, out);
        }
      } else if (typeof val === "string" && val.includes("\n")) {
        out.push(`${pad}${k}: |`);
        emitBlockLines(val, level + 1, indent, out);
      } else {
        out.push(`${pad}${k}: ${valStr(val)}`);
      }
    }
  } else if (Array.isArray(value)) {
    emitList(value, level, indent, out);
  } else {
    out.push(pad + valStr(value));
  }
}

function dumpYaml(data) {
  const out = [];
  emit(data, 0, 2, out);
  return out.join("\n") + "\n";
}

// ---------------------------------------------------------------------------
// Mini JSON Schema validator (mirrors packlib/jsonschema_mini.py)
// ---------------------------------------------------------------------------

function validateSchema(data, schema, store, errors, path, root) {
  if (schema === true) return;
  if (schema === false) {
    errors.push(`${path}: must not validate against false schema`);
    return;
  }
  if (typeof schema !== "object") return;
  root = root || schema;

  if (schema.not !== undefined) {
    const sub = [];
    validateSchema(data, schema.not, store, sub, path, root);
    if (sub.length === 0) errors.push(`${path}: must not validate against 'not' schema`);
  }
  if (schema.$ref !== undefined) {
    let target;
    try {
      target = deref(schema.$ref, store, root);
    } catch (e) {
      errors.push(`${path}: ${e.message}`);
      return;
    }
    validateSchema(data, target, store, errors, path, root);
  }
  for (const [kw, sub] of [["allOf", schema.allOf], ["anyOf", schema.anyOf], ["oneOf", schema.oneOf]]) {
    if (sub === undefined) continue;
    if (kw === "allOf") for (const s of sub) validateSchema(data, s, store, errors, path, root);
    else if (kw === "anyOf") {
      const inner = [];
      for (const s of sub) {
        const list = [];
        validateSchema(data, s, store, list, path, root);
        if (list.length === 0) {
          inner.length = 0;
          break;
        }
        inner.push(list);
      }
      if (inner.length) errors.push(`${path}: must match one of anyOf (${inner.length} failed)`);
    } else {
      let matches = 0;
      for (const s of sub) {
        const list = [];
        validateSchema(data, s, store, list, path, root);
        if (list.length === 0) matches += 1;
      }
      if (matches !== 1) errors.push(`${path}: must match exactly one of oneOf (matched ${matches})`);
    }
  }
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((t) => isType(data, t))) errors.push(`${path}: expected type ${JSON.stringify(types)}`);
  }
  if (schema.const !== undefined && data !== schema.const) errors.push(`${path}: expected const ${JSON.stringify(schema.const)}`);
  if (schema.enum !== undefined && !schema.enum.includes(data)) errors.push(`${path}: value not in enum ${JSON.stringify(schema.enum)}`);

  if (data !== null && typeof data === "object" && !Array.isArray(data)) {
    for (const name of schema.required || []) if (!(name in data)) errors.push(`${path}: missing required property ${name}`);
    const props = schema.properties || {};
    for (const name of Object.keys(props)) if (name in data) validateSchema(data[name], props[name], store, errors, `${path}/${name}`, root);
    const additional = schema.additionalProperties === undefined ? true : schema.additionalProperties;
    for (const name of Object.keys(data)) {
      if (name in props) continue;
      if (additional === false) errors.push(`${path}: unexpected property ${name}`);
      else if (typeof additional === "object") validateSchema(data[name], additional, store, errors, `${path}/${name}`, root);
    }
  }
  if (Array.isArray(data)) {
    if (schema.items) for (const [i, item] of data.entries()) validateSchema(item, schema.items, store, errors, `${path}/${i}`, root);
    if (schema.minItems !== undefined && data.length < schema.minItems) errors.push(`${path}: fewer than ${schema.minItems} items`);
    if (schema.maxItems !== undefined && data.length > schema.maxItems) errors.push(`${path}: more than ${schema.maxItems} items`);
  }
  if (typeof data === "string") {
    if (schema.minLength !== undefined && data.length < schema.minLength) errors.push(`${path}: shorter than ${schema.minLength} chars`);
    if (schema.maxLength !== undefined && data.length > schema.maxLength) errors.push(`${path}: longer than ${schema.maxLength} chars`);
    if (schema.pattern !== undefined && !new RegExp(schema.pattern).test(data)) errors.push(`${path}: does not match pattern ${schema.pattern}`);
    if (schema.format !== undefined && !checkFormat(data, schema.format)) errors.push(`${path}: invalid ${schema.format} format`);
  }
  if (typeof data === "number") {
    if (schema.minimum !== undefined && data < schema.minimum) errors.push(`${path}: below minimum ${schema.minimum}`);
    if (schema.maximum !== undefined && data > schema.maximum) errors.push(`${path}: above maximum ${schema.maximum}`);
  }
}

function isType(value, typeName) {
  switch (typeName) {
    case "object": return value !== null && typeof value === "object" && !Array.isArray(value);
    case "array": return Array.isArray(value);
    case "string": return typeof value === "string";
    case "integer": return typeof value === "number" && Number.isInteger(value);
    case "number": return typeof value === "number";
    case "boolean": return typeof value === "boolean";
    case "null": return value === null;
    default: return true;
  }
}

function checkFormat(value, fmt) {
  if (fmt === "date-time") return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/.test(value);
  if (fmt === "date") return /^\d{4}-\d{2}-\d{2}$/.test(value);
  if (fmt === "uri") return /^[a-zA-Z][a-zA-Z0-9+.-]*:[^\s]*$/.test(value);
  if (fmt === "email") return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);
  return true;
}

// ---------------------------------------------------------------------------
// Semver + manifest helpers (mirror packlib/manifest.py)
// ---------------------------------------------------------------------------

function parseVersion(version) {
  const core = String(version).split("-")[0].split("+")[0];
  const nums = core.split(".").map((p) => parseInt(p, 10));
  while (nums.length < 3) nums.push(0);
  return nums.slice(0, 3);
}

function cmpVersion(a, b) {
  const A = parseVersion(a);
  const B = parseVersion(b);
  for (let i = 0; i < 3; i++) {
    if (A[i] !== B[i]) return A[i] - B[i];
  }
  return 0;
}

function satisfiesSingle(version, piece) {
  piece = piece.trim();
  if (!piece || piece === "*") return true;
  const v = parseVersion(version);
  if (piece.startsWith("^")) {
    const t = parseVersion(piece.slice(1));
    let hi;
    if (t[0] > 0) hi = [t[0] + 1, 0, 0];
    else if (t[1] > 0) hi = [0, t[1] + 1, 0];
    else hi = [0, 0, t[2] + 1];
    return cmpVersion(version, piece.slice(1)) >= 0 && cmpVersion(version, hi.join(".")) < 0;
  }
  if (piece.startsWith("~")) {
    const t = parseVersion(piece.slice(1));
    const hi = [t[0], t[1] + 1, 0];
    return cmpVersion(version, piece.slice(1)) >= 0 && cmpVersion(version, hi.join(".")) < 0;
  }
  const op = piece.match(/^(>=|<=|>|<)/)?.[1];
  if (op) {
    const t = parseVersion(piece.slice(op.length));
    const c = cmpVersion(version, piece.slice(op.length));
    return op === ">" ? c > 0 : op === ">=" ? c >= 0 : op === "<" ? c < 0 : c <= 0;
  }
  if (piece.includes(".")) {
    const t = piece.split(".");
    if (t.length === 2) return v[0] === Number(t[0]) && v[1] === Number(t[1]);
    return cmpVersion(version, piece) === 0;
  }
  return v[0] === Number(piece);
}

function versionSatisfies(version, spec) {
  if (!spec || spec.trim() === "" || spec.trim() === "*") return true;
  const pieces = String(spec).trim().split(/\s+/);
  for (const piece of pieces) if (!satisfiesSingle(version, piece)) return false;
  return true;
}

function parseRef(ref) {
  const at = ref.indexOf("@");
  if (at >= 0) return [ref.slice(0, at).trim(), ref.slice(at + 1).trim() || "*"];
  return [ref.trim(), "*"];
}

function loadProjectDeclaration(dir) {
  const path = join(dir, "packs.yaml");
  if (!existsSync(path)) throw new Error(`no packs.yaml found in ${dir}`);
  const data = loadYamlFile(path);
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("packs.yaml must be a mapping");
  if (data.schema !== SCHEMA_URL) throw new Error("packs.yaml is missing or has an invalid schema URL");
  if (!Array.isArray(data.extends)) throw new Error("packs.yaml 'extends' must be a list");
  return data;
}

// ---------------------------------------------------------------------------
// Registry + pack loading (mirror packlib/registry.py + manifest.py)
// ---------------------------------------------------------------------------

function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function packIntegrity(dir) {
  const digest = createHash("sha256");
  const files = walk(dir).sort();
  for (const path of files) {
    const rel = path.slice(dir.length + 1);
    digest.update(rel);
    digest.update("\0");
    digest.update(sha256File(path));
    digest.update("\0");
  }
  return "sha256-" + digest.digest("hex");
}

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(path));
    else if (entry.isFile()) out.push(path);
  }
  return out;
}

function scanPack(packDir) {
  const manifestData = loadYamlFile(join(packDir, "pack.yaml"));
  if (!manifestData || typeof manifestData !== "object") throw new Error(`${packDir}/pack.yaml is not a mapping`);
  const contexts = [];
  const contextsDir = join(packDir, "contexts");
  if (existsSync(contextsDir)) {
    for (const name of readdirSync(contextsDir).sort()) {
      if (!name.endsWith(".yaml")) continue;
      const data = loadYamlFile(join(contextsDir, name));
      if (!data || typeof data !== "object") throw new Error(`${join(contextsDir, name)} is not a mapping`);
      contexts.push(data);
    }
  }
  const pkds = {};
  const projectDir = join(packDir, "project");
  if (existsSync(projectDir)) {
    for (const name of readdirSync(projectDir).sort()) {
      if (!name.endsWith(".yaml")) continue;
      const data = loadYamlFile(join(projectDir, name));
      if (!data || typeof data !== "object") throw new Error(`${join(projectDir, name)} is not a mapping`);
      const kind = data.kind;
      if (!kind) throw new Error(`${join(projectDir, name)} is missing 'kind'`);
      (pkds[kind] = pkds[kind] || []).push(data);
    }
  }
  let aiProse = null;
  const aiFile = join(packDir, "ai", "AGENTS.md");
  if (existsSync(aiFile)) aiProse = readFileSync(aiFile, "utf8");
  return {
    name: manifestData.name,
    version: manifestData.version,
    dir: packDir,
    manifest: manifestData,
    contexts,
    pkds,
    ai_prose: aiProse,
  };
}

class Registry {
  constructor(builtinDir, cacheDir) {
    this.builtin = builtinDir;
    this.cache = cacheDir;
  }
  versions(name) {
    const found = {};
    if (this.cache) {
      const base = join(this.cache, name);
      if (existsSync(base)) {
        for (const version of readdirSync(base)) {
          if (existsSync(join(base, version, "pack.yaml"))) found[version] = loadYamlFile(join(base, version, "pack.yaml"));
        }
      }
    }
    const builtin = join(this.builtin, name);
    if (existsSync(join(builtin, "pack.yaml"))) {
      const m = loadYamlFile(join(builtin, "pack.yaml"));
      found[m.version] = m;
    }
    return found;
  }
  _locate(name, version) {
    if (this.cache) {
      const candidate = join(this.cache, name, version);
      if (existsSync(join(candidate, "pack.yaml"))) return candidate;
    }
    const builtin = join(this.builtin, name);
    if (existsSync(join(builtin, "pack.yaml"))) {
      const m = loadYamlFile(join(builtin, "pack.yaml"));
      if (m.version === version) return builtin;
    }
    throw new Error(`pack ${name}@${version} is not available in the local registry`);
  }
  load(name, version) {
    return scanPack(this._locate(name, version));
  }
  integrity(name, version) {
    return packIntegrity(this._locate(name, version));
  }
}

// ---------------------------------------------------------------------------
// Resolver (mirror packlib/resolver.py)
// ---------------------------------------------------------------------------

function resolvePack(project, registry) {
  const roots = project.extends.map((ref) => parseRef(ref));
  if (roots.length === 0) return [];
  const graph = {};
  const color = {};
  for (const [name] of roots) graph[name] = newNode();

  const visit = (name, path) => {
    color[name] = "gray";
    const node = graph[name];
    const pack = peekManifest(registry, name);
    for (const ref of pack.extends || []) {
      const [parent, spec] = parseRef(ref);
      if (!graph[parent]) graph[parent] = newNode();
      node.extends.push([parent, spec]);
      graph[parent].specs.push([name, spec]);
      graph[parent].parents.add(name);
      if (color[parent] === "gray") throw new Error(`circular extends detected: ${[...path, parent].join(" -> ")}`);
      if (color[parent] !== "black") visit(parent, [...path, parent]);
    }
    for (const ref of pack.dependencies || []) {
      const [dep, spec] = parseRef(ref);
      if (!graph[dep]) graph[dep] = newNode();
      node.dependencies.push([dep, spec]);
      graph[dep].specs.push([name, spec]);
      if (color[dep] === "gray") throw new Error(`circular dependency detected: ${[...path, dep].join(" -> ")}`);
      if (color[dep] !== "black") visit(dep, [...path, dep]);
    }
    color[name] = "black";
  };

  for (const [name, spec] of roots) {
    graph[name].specs.push(["project", spec]);
    visit(name, [name]);
  }

  for (const name of Object.keys(graph)) {
    const specs = graph[name].specs.map(([, s]) => s);
    graph[name].version = resolveVersion(registry, name, specs);
  }

  for (const [i, [name]] of roots.entries()) graph[name].precedence = i + 1;
  for (const name of Object.keys(graph)) {
    const node = graph[name];
    if (node.precedence === undefined) node.precedence = 0;
  }
  let stable = false;
  while (!stable) {
    stable = true;
    for (const name of Object.keys(graph)) {
      const node = graph[name];
      if (node.precedence === undefined) continue;
      for (const [parent] of node.extends) {
        const newPrec = node.precedence - 1;
        if (graph[parent].precedence === undefined || newPrec < graph[parent].precedence) {
          graph[parent].precedence = newPrec;
          stable = false;
        }
      }
    }
  }

  const ordered = Object.keys(graph).map((name) => {
    const node = graph[name];
    return { name, version: node.version, precedence: node.precedence, pack: registry.load(name, node.version) };
  });
  ordered.sort((a, b) => a.precedence - b.precedence);
  return ordered;
}

function peekManifest(registry, name) {
  const versions = registry.versions(name);
  const keys = Object.keys(versions);
  if (keys.length === 0) throw new Error(`pack ${name} is not available in the local registry`);
  keys.sort((a, b) => cmpVersion(a, b));
  return registry.load(name, keys[keys.length - 1]).manifest;
}

function resolveVersion(registry, name, specs) {
  const versions = Object.keys(registry.versions(name));
  if (versions.length === 0) throw new Error(`pack ${name} is not available in the local registry`);
  const candidates = versions.filter((v) => specs.every((s) => versionSatisfies(v, s)));
  if (candidates.length === 0) throw new Error(`no version of ${name} satisfies ${JSON.stringify([...new Set(specs)])} (available: ${JSON.stringify(versions)})`);
  candidates.sort((a, b) => cmpVersion(a, b));
  return candidates[candidates.length - 1];
}

function newNode() {
  return { specs: [], extends: [], dependencies: [], parents: new Set(), precedence: undefined, version: undefined, pack: undefined };
}

// ---------------------------------------------------------------------------
// Merger (mirror packlib/merger.py + knowledge.py)
// ---------------------------------------------------------------------------

const KNOWLEDGE_KINDS = [
  "vision", "architecture", "conventions", "folder-structure", "tech-stack",
  "security", "testing", "business-constraints", "ai-rules", "review-checklist",
  "deployment", "observability", "lifecycle", "ownership",
];

const LIST_KEY = {
  vision: { principles: "id", success_signals: null, non_goals: null, target_users: null },
  architecture: { patterns: "id", decisions: "id" },
  conventions: { naming: "id", formatting: "id", imports: "id", state: "id", structure: "id" },
  "folder-structure": { directories: "path", files: "path" },
  "tech-stack": { entries: "name" },
  security: { standards: "name", rules: "id", sensitive_data: null, trust_boundaries: null, references: null },
  testing: { tools: null, gates: "name", fixtures: null },
  "business-constraints": { constraints: "id", compliance: "name", kpis: null },
  "ai-rules": { rules: "id" },
  "review-checklist": { categories: "name" },
  deployment: { environments: "name", rollout: null, smoke_tests: null, rollback: null },
  observability: { metrics: "name", logs: null, traces: null, alerts: "name", slos: "name", dashboards: null },
  lifecycle: { transitions: "to" },
  ownership: { areas: "name", contexts: "id" },
};

function appendOrReplace(target, item, idkey) {
  if (idkey && item && typeof item === "object" && item[idkey] !== undefined) {
    const i = target.findIndex((e) => e && typeof e === "object" && e[idkey] === item[idkey]);
    if (i >= 0) {
      target[i] = item;
      return;
    }
    target.push(item);
    return;
  }
  if (!target.includes(item)) target.push(item);
}

function deepMerge(left, right) {
  for (const key of Object.keys(right)) {
    if (left[key] && typeof left[key] === "object" && !Array.isArray(left[key]) &&
        right[key] && typeof right[key] === "object" && !Array.isArray(right[key])) {
      deepMerge(left[key], right[key]);
    } else left[key] = right[key];
  }
  return left;
}

function mergeDocs(kind, docs) {
  const acc = { kind, pack: null };
  const lk = LIST_KEY[kind] || {};
  for (const doc of docs) {
    if (!doc) continue;
    for (const key of Object.keys(doc)) {
      if (key === "kind") continue;
      if (key === "pack") {
        acc.pack = doc.pack;
        continue;
      }
      const value = doc[key];
      if (Array.isArray(value)) {
        if (!Array.isArray(acc[key])) acc[key] = [];
        for (const item of value) appendOrReplace(acc[key], item, lk[key]);
      } else if (value && typeof value === "object") {
        if (!acc[key] || typeof acc[key] !== "object" || Array.isArray(acc[key])) acc[key] = {};
        deepMerge(acc[key], value);
      } else acc[key] = value;
    }
  }
  return acc;
}

function classification(ctx) {
  return String(ctx?.governance?.classification ?? "");
}

function isHardened(ctx) {
  return classification(ctx).startsWith("hardened-");
}

function diffHint(a, b) {
  const hints = [];
  for (const key of ["authority", "enforcement", "severity", "lifecycle"]) {
    if (JSON.stringify(a[key]) !== JSON.stringify(b[key])) hints.push(`${key}: ${JSON.stringify(a[key])} vs ${JSON.stringify(b[key])}`);
  }
  return hints.join("; ") || "content differs";
}

function mergeAll(ordered, project, replaceMap = {}) {
  const policy = project.conflict_policy || "fail";
  const projectOverrides = project.overrides || [];
  const projectOverrideIds = new Set(projectOverrides.map((o) => o.id));

  const byId = {};
  const order = [];
  for (const item of ordered) {
    for (const ctx of item.pack.contexts) {
      const cid = ctx?.id;
      if (!cid) continue;
      if (!byId[cid]) {
        byId[cid] = [];
        order.push(cid);
      }
      byId[cid].push([item.precedence, item.name, ctx]);
    }
  }

  const packOverrides = [];
  for (const item of [...ordered].sort((a, b) => a.precedence - b.precedence)) {
    for (const ov of item.pack.manifest.override || []) packOverrides.push([item.precedence, item.name, ov]);
  }

  const effective = {};
  const conflicts = [];
  const overridesApplied = [];
  const disabled = [];
  const deferred = [];

  for (const cid of order) {
    const entries = [...byId[cid]].sort((a, b) => a[0] - b[0]);
    const maxPrec = entries[entries.length - 1][0];
    const top = entries.filter((e) => e[0] === maxPrec);
    let winnerCtx = { ...top[0][2] };
    const origin = top[0][1];
    const hardened = top.some((e) => isHardened(e[2]));
    let conflictStatus = null;

    if (top.length > 1) {
      conflictStatus = hardened ? "blocking" : "pending";
      conflicts.push({
        id: cid, kind: "context", packs: [...new Set(top.map((e) => e[1]))].sort(),
        policy, hardened, status: conflictStatus, diff_hint: diffHint(top[0][2], top[top.length - 1][2]),
      });
    }

    const applyOverride = (ov, source) => {
      const action = ov.action;
      const record = { id: cid, action, source, reason: ov.reason };
      if (action === "disable") {
        disabled.push(record);
        winnerCtx = null;
      } else if (action === "defer") {
        winnerCtx.lifecycle = "draft";
        deferred.push(record);
      } else if (action === "patch") {
        deepMerge(winnerCtx, ov.patch || {});
        overridesApplied.push(record);
      } else if (action === "replace") {
        if (replaceMap[cid]) {
          winnerCtx = { ...replaceMap[cid] };
          overridesApplied.push(record);
        } else {
          conflicts.push({ id: cid, kind: "context", packs: [origin], policy, hardened, status: "blocking", diff_hint: `override replace missing source for ${cid}` });
        }
      } else if (action === "resolve") {
        const match = ov.pack ? entries.find((e) => e[1] === ov.pack)?.[2] : undefined;
        if (match) {
          winnerCtx = { ...match };
          overridesApplied.push(record);
        } else {
          conflicts.push({ id: cid, kind: "context", packs: [origin], policy, hardened, status: "blocking", diff_hint: `resolve override references unknown pack ${ov.pack}` });
        }
      }
    };

    for (const [, packName, ov] of packOverrides) if (ov.id === cid) applyOverride(ov, `pack:${packName}`);
    for (const ov of projectOverrides) if (ov.id === cid) applyOverride(ov, "project");

    if (winnerCtx) effective[cid] = winnerCtx;
    if (conflictStatus === "blocking" && !projectOverrideIds.has(cid)) conflicts[conflicts.length - 1].status = "blocking-unresolved";
  }

  const knowledge = {};
  const mergedKnowledge = {};
  for (const item of ordered) {
    for (const [kind, docs] of Object.entries(item.pack.pkds)) {
      (knowledge[kind] = knowledge[kind] || []).push(...docs);
    }
  }
  for (const [kind, docs] of Object.entries(knowledge)) mergedKnowledge[kind] = mergeDocs(kind, docs);

  const aiRules = Array.isArray(mergedKnowledge["ai-rules"]?.rules) ? [...mergedKnowledge["ai-rules"].rules] : [];

  return {
    contexts: effective,
    knowledge: mergedKnowledge,
    ai_rules: aiRules,
    report: { conflicts, overrides_applied: overridesApplied, disabled, deferred },
  };
}

// ---------------------------------------------------------------------------
// Validator (mirror packlib/validator.py)
// ---------------------------------------------------------------------------

const CONTEXT_LIFECYCLES = ["draft", "candidate", "approved", "active", "deprecated", "archived"];
const SOURCE_TYPES = ["individual", "organization", "standard-body", "ai-system", "community", "automated", "regulatory", "documentation", "meeting", "incident", "unknown"];
const GOVERNANCE_CLASSES = ["hardened-mandate", "hardened-standard", "hardened-local", "local-standard", "local-guideline", "local-experimental"];
const ENFORCEMENT_MODES = ["block", "warn", "comment", "silent"];

function loadSchemaStore() {
  const store = {};
  const schemasDir = join(PACKS_ROOT, "schemas");
  for (const file of walk(schemasDir).filter((p) => p.endsWith(".json"))) {
    const schema = JSON.parse(readFileSync(file, "utf8"));
    if (schema.$id) store[schema.$id] = schema;
  }
  return store;
}

function deref(ref, store, root) {
  if (ref.startsWith("#/")) {
    const parts = ref.slice(2).split("/").map((p) => p.replace(/~1/g, "/").replace(/~0/g, "~"));
    let node = root;
    for (const part of parts) {
      if (!node || typeof node !== "object" || !(part in node)) throw new Error(`unresolvable $ref: ${ref}`);
      node = node[part];
    }
    return node;
  }
  const uri = ref.split("#")[0];
  const node = store[uri];
  if (!node) throw new Error(`external $ref not in schema store: ${ref}`);
  return node;
}

function contextFieldErrors(ctx) {
  const errors = [];
  for (const field of ["id", "version", "title", "description", "source", "authority", "lifecycle", "governance"]) {
    if (ctx[field] === undefined) errors.push(`missing required field '${field}'`);
  }
  if (ctx.id !== undefined && !/^[a-zA-Z0-9_-]+$/.test(ctx.id)) errors.push("id must be ^[a-zA-Z0-9_-]+$");
  if (ctx.version !== undefined && !Number.isInteger(ctx.version)) errors.push("version must be an integer");
  if (ctx.title !== undefined && !(typeof ctx.title === "string" && ctx.title.length >= 1 && ctx.title.length <= 256)) errors.push("title must be a string of 1-256 chars");
  if (ctx.description !== undefined && !(typeof ctx.description === "string" && ctx.description.length >= 1)) errors.push("description must be a non-empty string");
  if (ctx.source !== undefined && !(ctx.source && SOURCE_TYPES.includes(ctx.source.type))) errors.push("source.type is missing or invalid");
  if (ctx.authority !== undefined) {
    if (!Number.isInteger(ctx.authority?.level) || ctx.authority.level < 0 || ctx.authority.level > 4) errors.push("authority.level must be an integer 0-4");
    if (!ctx.authority?.source?.id) errors.push("authority.source.id is required");
  }
  if (ctx.lifecycle !== undefined && !CONTEXT_LIFECYCLES.includes(ctx.lifecycle)) errors.push(`lifecycle must be one of ${CONTEXT_LIFECYCLES}`);
  if (!GOVERNANCE_CLASSES.includes(ctx.governance?.classification)) errors.push(`governance.classification must be one of ${GOVERNANCE_CLASSES}`);
  if (ctx.enforcement !== undefined && ctx.enforcement.mode !== undefined && !ENFORCEMENT_MODES.includes(ctx.enforcement.mode)) errors.push("invalid enforcement.mode");
  return errors;
}

function contextSemanticErrors(ctx) {
  const errors = [];
  const lifecycle = ctx.lifecycle;
  if (lifecycle === "candidate" && !ctx.review_status) errors.push("R1: candidate context requires review_status");
  if (lifecycle === "active") {
    if (!ctx.effective_date) errors.push("R1: active context requires effective_date");
    if (!ctx.enforcement) errors.push("R1: active context requires enforcement");
  }
  if (lifecycle === "deprecated" && !ctx.deprecated_date) errors.push("R1: deprecated context requires deprecated_date");
  if (lifecycle === "archived" && !ctx.deprecated_date) errors.push("R1: archived context requires deprecated_date");
  if (String(ctx.governance?.classification ?? "").startsWith("hardened-") && lifecycle === "active") {
    if (ctx.governance.approval_required !== true) errors.push("R3: hardened active context must set approval_required: true");
  }
  const eff = ctx.effective_date;
  const dep = ctx.deprecated_date;
  if (eff && dep && eff >= dep) errors.push("R4: effective_date must be before deprecated_date");
  if (lifecycle === "active" && eff && new Date(eff) > new Date()) errors.push("R4: effective_date must be in the past for active context");
  return errors;
}

function contextWarnings(ctx) {
  const warnings = [];
  const level = ctx.authority?.level ?? 0;
  if (level >= 3 && ctx.lifecycle === "active") {
    const mode = ctx.enforcement?.mode;
    if (mode !== "block") warnings.push(`R2: active context with authority level ${level} should use block enforcement (uses ${mode}); justify if intentional`);
  }
  return warnings;
}

function validateProject(project, store) {
  const schema = store["https://opencraft.dev/schema/project-packs/v1"];
  if (!schema) return ["project-packs schema not loaded"];
  const errors = [];
  validateSchema(project, schema, store, errors, "$");
  return errors;
}

function validatePack(pack, store) {
  const errors = [];
  const warnings = [];
  const name = pack.manifest.name;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*-pack$/.test(name || "")) errors.push("name must be kebab-case and end with '-pack'");
  if (!/^[0-9]+\.[0-9]+\.[0-9]+$/.test(String(pack.manifest.version ?? ""))) errors.push(`version ${pack.manifest.version} is not strict SemVer`);
  const schema = store["https://opencraft.dev/schema/context-pack/v1"];
  if (!schema) errors.push("context-pack schema not loaded");
  else validateSchema(pack.manifest, schema, store, errors, "$");

  const seen = new Set();
  for (const ctx of pack.contexts) {
    const cid = ctx.id;
    if (seen.has(cid)) errors.push(`duplicate context id ${cid}`);
    seen.add(cid);
    for (const e of [...contextFieldErrors(ctx), ...contextSemanticErrors(ctx)]) errors.push(`context ${cid}: ${e}`);
    for (const w of contextWarnings(ctx)) warnings.push(`context ${cid}: ${w}`);
    if (ctx.metadata?.pack !== undefined && ctx.metadata.pack !== null && ctx.metadata.pack !== name) errors.push(`context ${cid}: metadata.pack does not match ${name}`);
  }
  for (const cid of pack.manifest.provides?.contexts || []) if (!seen.has(cid)) errors.push(`provides.contexts references unknown context ${cid}`);
  for (const kind of Object.keys(pack.pkds)) {
    const schema = store[`https://opencraft.dev/schema/knowledge/${kind}/v1`];
    if (!schema) {
      errors.push(`no schema for PKD kind ${kind}`);
      continue;
    }
    for (const doc of pack.pkds[kind]) {
      validateSchema(doc, schema, store, errors, `$project/${kind}.yaml`);
      if (doc.pack !== undefined && doc.pack !== null && doc.pack !== name) errors.push(`project/${kind}.yaml: pack field does not match ${name}`);
    }
  }
  return [errors, warnings];
}

// ---------------------------------------------------------------------------
// Materialize (mirror packlib/materialize.py)
// ---------------------------------------------------------------------------

function renderAgentsMd(merged, proseSources) {
  const lines = [
    "# AI coding rules (from OpenCraft Context Packs)",
    "",
    "Rules below are structured, merged, and versioned via `.lcdd/contexts/` and `.lcdd/project/ai-rules.yaml`.",
    "",
  ];
  if (merged.ai_rules.length) {
    lines.push("## Rules", "");
    for (const rule of merged.ai_rules) {
      const label = { must: "MUST", "must-not": "MUST NOT", should: "SHOULD" }[rule.level] || rule.level.toUpperCase();
      let line = `- **${label}** \`${rule.id}\` — ${rule.instruction}`;
      if (rule.rationale) line += ` (${rule.rationale})`;
      lines.push(line);
    }
    lines.push("");
  }
  if (proseSources.length) {
    lines.push("## Pack prose", "");
    for (const source of proseSources) {
      lines.push(`### ${source.pack} v${source.version}`, "", source.text.trim(), "");
    }
  }
  return lines.join("\n").replace(/\s+$/, "") + "\n";
}

function renderContextMd(merged) {
  const knowledge = merged.knowledge;
  const out = ["# Living Context", ""];
  out.push("This file is generated from resolved OpenCraft Context Packs. Machine-readable sources live in `contexts/` and `project/`.", "");
  const vision = knowledge.vision;
  if (vision) {
    out.push("## Vision", "", `- **Purpose:** ${vision.purpose || "—"}`);
    if (vision.target_users?.length) out.push(`- **Target users:** ${vision.target_users.join(", ")}`);
    if (vision.primary_journey) out.push(`- **Primary journey:** ${vision.primary_journey}`);
    out.push("");
  }
  const stack = knowledge["tech-stack"];
  if (stack) {
    out.push("## Technology stack", "");
    if (stack.language) out.push(`- Language: ${stack.language}`);
    if (stack.runtime) out.push(`- Runtime: ${stack.runtime}`);
    if (stack.framework) out.push(`- Framework: ${stack.framework}`);
    for (const entry of stack.entries || []) out.push(`- ${entry.name}${entry.version ? " " + entry.version : ""} — ${entry.role}`);
    out.push("");
  }
  const conventions = knowledge.conventions;
  if (conventions) {
    out.push("## Conventions", "");
    for (const section of ["naming", "formatting", "imports", "state", "structure"]) {
      const rules = conventions[section] || [];
      if (rules.length) {
        out.push(`### ${section}`);
        for (const rule of rules) out.push(`- \`${rule.id}\` — ${rule.rule}`);
        out.push("");
      }
    }
  }
  const security = knowledge.security;
  if (security) {
    out.push("## Security", "");
    for (const rule of security.rules || []) out.push(`- **${(rule.severity || "info").toUpperCase()}** \`${rule.id}\` — ${rule.description}`);
    out.push("");
  }
  out.push("## Active contexts", "");
  const ids = Object.keys(merged.contexts).sort();
  if (ids.length) {
    out.push("| ID | Title | Level | Enforcement |", "|---|---|---|---|");
    for (const cid of ids) {
      const ctx = merged.contexts[cid];
      out.push(`| \`${cid}\` | ${ctx.title || ""} | ${ctx.authority?.level ?? "?"} | ${ctx.enforcement?.mode ?? "—"} |`);
    }
  } else out.push("_No active contexts._");
  out.push("", "## AI coding rules", "");
  out.push("See `ai/AGENTS.md` (rendered) and `project/ai-rules.yaml` (structured).", "");
  out.push("## Sources", "");
  out.push("This living context is resolved from the packs declared in `packs.yaml`; versions are pinned in `packs.lock.json`.", "");
  return out.join("\n").replace(/\n+$/, "\n");
}

function materialize(projectDir, merged, ordered, project, lockIntegrity) {
  const lcdd = join(projectDir, ".lcdd");
  for (const dir of ["contexts", "project", "ai"]) mkdirSync(join(lcdd, dir), { recursive: true });
  for (const dir of ["contexts", "project"]) {
    for (const name of readdirSync(join(lcdd, dir))) {
      if (name.endsWith(".yaml")) rmSync(join(lcdd, dir, name), { force: true });
    }
  }
  for (const name of ["CONTEXT.md", "report.json"]) rmSync(join(lcdd, name), { force: true });
  for (const [cid, ctx] of Object.entries(merged.contexts)) writeFileSync(join(lcdd, "contexts", `${cid}.yaml`), dumpYaml(ctx), "utf8");
  for (const [kind, doc] of Object.entries(merged.knowledge)) writeFileSync(join(lcdd, "project", `${kind}.yaml`), dumpYaml(doc), "utf8");
  const prose = ordered.filter((i) => i.pack.ai_prose).map((i) => ({ pack: i.name, version: i.version, text: i.pack.ai_prose }));
  writeFileSync(join(lcdd, "ai", "AGENTS.md"), renderAgentsMd(merged, prose), "utf8");
  writeFileSync(join(lcdd, "CONTEXT.md"), renderContextMd(merged), "utf8");
  const lockfile = {
    schema: "https://opencraft.dev/schema/packs.lock/v1",
    algorithm: "sha256",
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    resolved: ordered.map((item) => ({
      name: item.name,
      version: item.version,
      integrity: lockIntegrity[item.name] || "",
      precedence: item.precedence,
      extends: item.pack.manifest.extends || [],
      dependencies: item.pack.manifest.dependencies || [],
      deprecated: item.pack.manifest.lifecycle === "deprecated",
    })),
  };
  writeFileSync(join(lcdd, "packs.lock.json"), JSON.stringify(lockfile, null, 2) + "\n", "utf8");
  writeFileSync(join(lcdd, "report.json"), JSON.stringify(merged.report, null, 2) + "\n", "utf8");
  return lcdd;
}

// ---------------------------------------------------------------------------
// Pipeline + CLI
// ---------------------------------------------------------------------------

function buildRegistry() {
  const cache = join(process.env.HOME || process.env.USERPROFILE, ".opencraft", "packs");
  return new Registry(PACKS_ROOT, cache);
}

function runPipeline(projectDir) {
  const project = loadProjectDeclaration(projectDir);
  const store = loadSchemaStore();
  const errors = validateProject(project, store);
  if (errors.length) return { ok: false, errors };
  const reg = buildRegistry();
  const ordered = resolvePack(project, reg);

  const replaceMap = {};
  for (const ov of project.overrides || []) {
    if (ov.action === "replace" && ov.path) {
      const target = join(projectDir, ov.path);
      if (!existsSync(target)) return { ok: false, errors: [`override replace source not found: ${target}`] };
      const data = loadYamlFile(target);
      if (!data || !data.id) return { ok: false, errors: [`replace source ${target} is not a valid context`] };
      replaceMap[data.id] = data;
    }
  }
  for (const item of ordered) {
    for (const ov of item.pack.manifest.override || []) {
      if (ov.action === "replace" && ov.path) {
        const target = join(item.pack.dir, ov.path);
        if (!existsSync(target)) return { ok: false, errors: [`override replace source not found: ${target}`] };
        const data = loadYamlFile(target);
        if (data && data.id) replaceMap[data.id] = data;
      }
    }
  }

  const merged = mergeAll(ordered, project, replaceMap);
  const validationErrors = [];
  const blocking = [];
  for (const [cid, ctx] of Object.entries(merged.contexts)) {
    for (const e of [...contextFieldErrors(ctx), ...contextSemanticErrors(ctx)]) validationErrors.push(`context ${cid}: ${e}`);
  }
  for (const [kind, doc] of Object.entries(merged.knowledge)) {
    const schema = store[`https://opencraft.dev/schema/knowledge/${kind}/v1`];
    if (schema) validateSchema(doc, schema, store, validationErrors, `$project/${kind}.yaml`);
  }
  for (const c of merged.report.conflicts) {
    if (c.status === "blocking-unresolved") validationErrors.push(`unresolved hardened conflict for ${c.id} between ${c.packs.join(", ")}; add an explicit override`);
    else if (c.status === "pending" && project.conflict_policy === "fail") validationErrors.push(`conflict for ${c.id} between ${c.packs.join(", ")} (policy: fail)`);
  }
  const lockIntegrity = {};
  for (const item of ordered) lockIntegrity[item.name] = packIntegrity(item.pack.dir);

  return { ok: validationErrors.length === 0, ordered, merged, project, errors: validationErrors, blocking, lockIntegrity };
}

function usage() {
  console.log(`OpenCraft Context Packs CLI

Usage: packtool.mjs packs <command> [options]

Commands:
  init                  Create packs.yaml + .lcdd/ skeleton
  bootstrap             Apply LCDD: baseline core-pack + install (auto on install)
  add <name[@range]>    Declare a pack
  remove <name>         Remove a declared pack
  install               Resolve, merge, validate, materialize
  update                Re-resolve and re-materialize
  list                  List declared packs
  status                Show effective context
  doctor                Context health report
  resolve --dry-run     Show resolved graph and conflicts
  validate [name|--all] Validate pack(s)
  verify                Integrity-check packs.lock.json
  lock                  Regenerate the lockfile
  create <name>         Scaffold a new pack
  publish <name>        Prepare a pack for publication

Options: --project <dir>  --json  --force  --dry-run`);
}

function cmdValidate(argv) {
  const store = loadSchemaStore();
  const reg = buildRegistry();
  const target = argv.find((a) => !a.startsWith("--"));
  const allPacks = argv.includes("--all");
  if (allPacks || !target) {
    let failures = 0;
    for (const name of readdirSync(PACKS_ROOT).sort()) {
      const dir = join(PACKS_ROOT, name);
      if (!existsSync(join(dir, "pack.yaml"))) continue;
      const pack = scanPack(dir);
      const [errors, warnings] = validatePack(pack, store);
      for (const ref of [...(pack.manifest.extends || []), ...(pack.manifest.dependencies || [])]) {
        const [depName] = parseRef(ref);
        if (Object.keys(reg.versions(depName)).length === 0) errors.push(`extends/dependency references unknown pack ${depName}`);
      }
      for (const w of warnings) console.log(`WARN ${pack.name}: ${w}`);
      if (errors.length) {
        failures += 1;
        console.log(`FAIL ${pack.name}`);
        for (const e of errors) console.log(`  - ${e}`);
      } else console.log(`PASS ${pack.name}`);
    }
    return failures ? 1 : 0;
  }
  const pack = scanPack(join(PACKS_ROOT, target));
  const [errors, warnings] = validatePack(pack, store);
  for (const w of warnings) console.log(`WARN ${target}: ${w}`);
  if (errors.length) {
    console.log(`FAIL ${target}`);
    for (const e of errors) console.log(`  - ${e}`);
    return 1;
  }
  console.log(`PASS ${target}`);
  return 0;
}

function main() {
  const argv = process.argv.slice(2);
  if (!argv.length || argv[0] === "--help" || argv[0] === "-h" || argv[0] === "help") {
    usage();
    return;
  }
  if (argv[0] !== "packs") {
    console.error(`ERROR unknown command group ${argv[0]}`);
    process.exitCode = 2;
    return;
  }
  const command = argv[1] || "help";
  const jsonOut = argv.includes("--json");
  let projectDir = process.cwd();
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--project") {
      projectDir = resolve(argv[i + 1]);
      break;
    }
  }
  const rest = [];
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--project") {
      i += 1;
      continue;
    }
    if (argv[i] === "--json") continue;
    rest.push(argv[i]);
  }
  const emit = (obj) => console.log(JSON.stringify(obj, null, 2));

  try {
    if (command === "help") {
      usage();
      return;
    }
    if (command === "validate") {
      process.exitCode = cmdValidate(rest);
      return;
    }
    if (command === "install" || command === "update" || command === "bootstrap") {
      if (command === "bootstrap") {
        const packsPath = join(projectDir, "packs.yaml");
        if (existsSync(packsPath)) {
          const declaration = loadProjectDeclaration(projectDir);
          if ((declaration.extends || []).length === 0) {
            declaration.extends = [CORE_PACK];
            writeFileSync(packsPath, dumpYaml(declaration), "utf8");
            if (!jsonOut) console.log(`OK   added baseline ${CORE_PACK} to packs.yaml`);
          }
        } else if (ensurePacksYaml(projectDir) && !jsonOut) {
          console.log(`OK   bootstrapped packs.yaml with ${CORE_PACK}`);
        }
      } else if (ensurePacksYaml(projectDir) && !jsonOut) {
        console.log(`OK   bootstrapped packs.yaml with ${CORE_PACK}`);
      }
      const result = runPipeline(projectDir);
      if (!result.ok) {
        for (const e of result.errors) console.error(`ERROR ${e}`);
        process.exitCode = 1;
        return;
      }
      const lcdd = materialize(projectDir, result.merged, result.ordered, result.project, result.lockIntegrity);
      if (jsonOut) {
        emit({
          ok: true,
          lcdd,
          packs: result.ordered.map((i) => ({ name: i.name, version: i.version, precedence: i.precedence })),
          contexts: Object.keys(result.merged.contexts).sort(),
          conflicts: result.merged.report.conflicts,
        });
      } else {
        console.log(`OK   materialized ${Object.keys(result.merged.contexts).length} contexts into ${lcdd}`);
        for (const i of result.ordered) console.log(`  - ${i.name}@${i.version} (precedence ${i.precedence})`);
        for (const c of result.merged.report.conflicts) console.log(`WARN conflict ${c.id}: ${c.packs.join(", ")}`);
      }
      return;
    }
    if (command === "status") {
      const result = runPipeline(projectDir);
      if (jsonOut) {
        emit({
          ok: result.ok,
          packs: result.ordered.map((i) => ({ name: i.name, version: i.version, precedence: i.precedence })),
          contexts: Object.keys(result.merged.contexts).sort(),
          knowledge: Object.keys(result.merged.knowledge).sort(),
          conflicts: result.merged.report.conflicts,
        });
      } else {
        for (const i of result.ordered) console.log(`${i.name}@${i.version} (precedence ${i.precedence})`);
        console.log(`contexts: ${Object.keys(result.merged.contexts).length}`);
      }
      return;
    }
    if (command === "resolve") {
      const result = runPipeline(projectDir);
      if (jsonOut) {
        emit({ ok: result.ok, graph: result.ordered.map((i) => ({ name: i.name, version: i.version, precedence: i.precedence })), conflicts: result.merged.report.conflicts, errors: result.errors });
      } else {
        for (const i of result.ordered) console.log(`${i.precedence}  ${i.name}@${i.version}`);
        for (const c of result.merged.report.conflicts) console.log(`conflict ${c.id}: ${c.packs.join(", ")} (${c.status})`);
      }
      return;
    }
    if (command === "doctor") {
      const lcdd = join(projectDir, ".lcdd");
      if (!existsSync(join(lcdd, "contexts"))) {
        console.error("ERROR no .lcdd installed");
        process.exitCode = 1;
        return;
      }
      const contexts = {};
      for (const file of readdirSync(join(lcdd, "contexts")).filter((f) => f.endsWith(".yaml"))) {
        const data = loadYamlFile(join(lcdd, "contexts", file));
        if (data?.id) contexts[data.id] = data;
      }
      const report = existsSync(join(lcdd, "report.json")) ? JSON.parse(readFileSync(join(lcdd, "report.json"), "utf8")) : {};
      const missingOwners = Object.entries(contexts).filter(([, c]) => !c.owner).map(([id]) => id);
      const unresolved = (report.conflicts || []).filter((c) => c.status === "blocking-unresolved").map((c) => c.id);
      const score = 100 - 10 * Math.min(10, missingOwners.length) - 10 * Math.min(10, unresolved.length);
      if (jsonOut) emit({ ok: score >= 70 && unresolved.length === 0, score, contexts: Object.keys(contexts).length, missing_owners: missingOwners, unresolved_conflicts: unresolved });
      else {
        console.log(`Context Health: ${score}/100`);
        for (const id of missingOwners) console.log(`  missing owner: ${id}`);
        for (const id of unresolved) console.log(`  unresolved conflict: ${id}`);
      }
      return;
    }
    if (command === "add") {
      if (!rest.length) throw new Error("usage: packs add <name[@range]>");
      const [name, spec] = parseRef(rest[0]);
      const ref = spec === "*" ? name : `${name}@${spec}`;
      const project = loadProjectDeclaration(projectDir);
      if (project.extends.some((r) => parseRef(r)[0] === name)) throw new Error(`${name} is already declared`);
      project.extends.push(ref);
      writeFileSync(join(projectDir, "packs.yaml"), dumpYaml(project), "utf8");
      console.log(`OK   added ${ref}`);
      return;
    }
    if (command === "remove") {
      if (!rest.length) throw new Error("usage: packs remove <name>");
      const project = loadProjectDeclaration(projectDir);
      const before = project.extends.length;
      project.extends = project.extends.filter((r) => parseRef(r)[0] !== rest[0]);
      if (project.extends.length === before) throw new Error(`${rest[0]} is not declared`);
      writeFileSync(join(projectDir, "packs.yaml"), dumpYaml(project), "utf8");
      console.log(`OK   removed ${rest[0]}`);
      return;
    }
    if (command === "init") {
      const declaration = { schema: SCHEMA_URL, extends: [], conflict_policy: "fail" };
      for (const ref of rest) {
        const [name, spec] = parseRef(ref);
        declaration.extends.push(spec === "*" ? name : `${name}@${spec}`);
      }
      writeFileSync(join(projectDir, "packs.yaml"), dumpYaml(declaration), "utf8");
      mkdirSync(join(projectDir, ".lcdd", "contexts"), { recursive: true });
      console.log(`OK   ${join(projectDir, "packs.yaml")}`);
      return;
    }
    if (command === "create") {
      if (!rest.length) throw new Error("usage: packs create <name> [--type T] [--dir OUT]");
      const name = rest[0];
      if (!name.endsWith("-pack")) throw new Error("pack name must end with '-pack'");
      const type = rest.includes("--type") ? rest[rest.indexOf("--type") + 1] : "technology";
      const outDir = rest.includes("--dir") ? resolve(rest[rest.indexOf("--dir") + 1]) : projectDir;
      const target = join(outDir, name);
      if (existsSync(target)) throw new Error(`${target} already exists`);
      for (const dir of ["contexts", "project", "ai", "evals"]) mkdirSync(join(target, dir), { recursive: true });
      writeFileSync(join(target, "pack.yaml"),
        `schema: https://opencraft.dev/schema/context-pack/v1\nname: ${name}\nversion: 0.1.0\ntype: ${type}\ndescription: Living context for ${name}.\nlicense: MIT\nauthor:\n  type: organization\n  id: opencraft\n  name: OpenCraft\nextends: []\ndependencies: []\nlifecycle: draft\ngovernance:\n  classification: local-standard\n  approval_required: false\nowner:\n  type: organization\n  id: opencraft\n  name: OpenCraft\n`, "utf8");
      console.log(`OK   scaffolded ${target}`);
      return;
    }
    if (command === "verify") {
      const lockPath = join(REPO_ROOT, "packs.lock.json");
      if (!existsSync(lockPath)) throw new Error("no packs.lock.json");
      const lock = JSON.parse(readFileSync(lockPath, "utf8"));
      let mismatches = 0;
      for (const [name, entry] of Object.entries(lock.packs || {})) {
        const dir = join(PACKS_ROOT, name);
        if (!existsSync(join(dir, "pack.yaml"))) {
          console.log(`  - ${name}: missing`);
          mismatches += 1;
          continue;
        }
        if (packIntegrity(dir) !== entry.integrity) {
          console.log(`  - ${name}: integrity mismatch`);
          mismatches += 1;
        }
      }
      if (mismatches) {
        console.log("FAIL integrity mismatch");
        process.exitCode = 1;
      } else console.log("OK integrity verified");
      return;
    }
    if (command === "publish") {
      if (!rest.length) throw new Error("usage: packs publish <name>");
      const name = rest[0];
      const dir = join(PACKS_ROOT, name);
      if (!existsSync(join(dir, "pack.yaml"))) throw new Error(`unknown pack ${name}`);
      const pack = scanPack(dir);
      const [errors] = validatePack(pack, loadSchemaStore());
      if (errors.length) throw new Error(`pack ${name} failed validation: ${errors.slice(0, 3).join("; ")}`);
      const payload = { ok: true, name, npm: `@opencraft/${name}`, version: pack.manifest.version, integrity: packIntegrity(dir) };
      if (jsonOut) emit(payload);
      else console.log(`publish ${name}@${pack.manifest.version} -> @opencraft/${name}\n  integrity ${payload.integrity}`);
      return;
    }
    if (command === "list") {
      const project = loadProjectDeclaration(projectDir);
      const reg = buildRegistry();
      for (const ref of project.extends) {
        const [name, spec] = parseRef(ref);
        const versions = Object.keys(reg.versions(name)).sort(cmpVersion);
        console.log(`${name} ${spec} -> latest ${versions[versions.length - 1] ?? "n/a"}`);
      }
      return;
    }
    console.error(`ERROR unknown command ${command}`);
    process.exitCode = 2;
  } catch (error) {
    console.error(`ERROR ${error.message}`);
    process.exitCode = 2;
  }
}

main();
