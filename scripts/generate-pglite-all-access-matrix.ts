#!/usr/bin/env bun

import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import yaml from 'js-yaml';
import {
  generateAllAccessMatrixObject,
  validateAllAccessMatrixObject,
} from './validate-pglite-all-access-matrix.ts';

function parseArgs(argv: string[]): Record<string, string | boolean> {
  const parsed: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) continue;
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      parsed[key] = true;
    } else {
      parsed[key] = next;
      i += 1;
    }
  }
  return parsed;
}

if (import.meta.main) {
  const args = parseArgs(Bun.argv.slice(2));
  if (args.help === true || args.h === true) {
    process.stdout.write([
      'Usage: bun run scripts/generate-pglite-all-access-matrix.ts --inventory <inventory.yml> --out <matrix.yml> [--json]',
      '',
      'Generates the requirement 008 all-access matrix from the accepted requirement 006 inventory.',
      '',
    ].join('\n'));
    process.exit(0);
  }
  const inventoryPath = typeof args.inventory === 'string'
    ? resolve(args.inventory)
    : resolve('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml');
  const outPath = typeof args.out === 'string'
    ? resolve(args.out)
    : resolve('requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-command-matrix.yml');
  if (!existsSync(inventoryPath)) {
    process.stdout.write(`${JSON.stringify({
      ok: false,
      errors: [{
        code: 'missing_inventory',
        message: '--inventory must point to an existing inventory YAML file',
        path: inventoryPath,
      }],
      warnings: [],
    }, null, args.json ? 2 : 0)}\n`);
    process.exit(1);
  }
  const inventoryText = readFileSync(inventoryPath, 'utf8');
  const inventory = yaml.load(inventoryText);
  const matrix = generateAllAccessMatrixObject(inventory, {
    repoRoot: process.cwd(),
  });
  const validation = validateAllAccessMatrixObject(matrix, { inventory, repoRoot: process.cwd() });
  if (!validation.ok) {
    process.stdout.write(`${JSON.stringify(validation, null, args.json ? 2 : 0)}\n`);
    process.exit(1);
  }
  writeFileSync(outPath, yaml.dump(matrix, { lineWidth: 120, noRefs: true }));
  const output = {
    ok: true,
    matrix: outPath,
    summary: validation.summary,
  };
  process.stdout.write(`${JSON.stringify(output, null, args.json ? 2 : 0)}\n`);
}
