#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const context = JSON.parse(process.argv[4] || "{}");
const relPath = context.vars && context.vars.path;

if (!relPath || path.isAbsolute(relPath) || relPath.includes("..")) {
  console.error(`invalid relative path: ${relPath || ""}`);
  process.exit(2);
}

const repoRoot = path.resolve(__dirname, "..", "..", "..", "..");
const fullPath = path.join(repoRoot, relPath);
process.stdout.write(fs.readFileSync(fullPath, "utf8"));
