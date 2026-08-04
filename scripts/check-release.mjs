#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function readJson(name) {
  return JSON.parse(readFileSync(resolve(repository, name), "utf8"));
}

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index === -1) return undefined;
  if (!process.argv[index + 1]) throw new Error(`${name} requires a value`);
  return process.argv[index + 1];
}

try {
  const packageManifest = readJson("package.json");
  const collection = readJson("collection.json");
  const lock = readJson("skills.lock.json");
  const versions = new Set([packageManifest.version, collection.version, lock.version]);
  if (versions.size !== 1) {
    throw new Error(
      `version mismatch: package=${packageManifest.version}, collection=${collection.version}, lock=${lock.version}`,
    );
  }
  const tag = argument("--tag");
  if (tag && tag !== `v${packageManifest.version}`) {
    throw new Error(`release tag ${tag} must equal v${packageManifest.version}`);
  }
  if (packageManifest.name !== lock.collection || packageManifest.name !== collection.name) {
    throw new Error("package, collection, and lock names must match");
  }
  if (packageManifest.repository?.url !== `git+${collection.source}.git`) {
    throw new Error("package repository URL must match collection source for npm provenance");
  }
  console.log(`PASS release identity: ${packageManifest.name}@${packageManifest.version}${tag ? ` (${tag})` : ""}`);
} catch (error) {
  console.error(`ERROR ${error.message}`);
  process.exitCode = 1;
}
