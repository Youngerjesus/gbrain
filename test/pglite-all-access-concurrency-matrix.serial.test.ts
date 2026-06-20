import { afterEach, describe, expect, test } from 'bun:test';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import yaml from 'js-yaml';
import {
  generateAllAccessMatrixObject,
  validateAllAccessResultsObject,
} from '../scripts/validate-pglite-all-access-matrix.ts';
import { runAllAccessMatrix } from '../scripts/run-pglite-all-access-matrix.ts';

const tempDirs: string[] = [];

afterEach(() => {
  for (const dir of tempDirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe('PGLite all-access concurrency matrix runner', () => {
  test('writes one coherent N=3 result bundle with no raw timeout or behavior-class downgrade', async () => {
    const inventory = yaml.load(readFileSync('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml', 'utf8')) as any;
    const matrix = generateAllAccessMatrixObject(inventory, { repoRoot: process.cwd() });
    const outputDir = mkdtempSync('/tmp/gbrain-pglite-all-access-results-');
    tempDirs.push(outputDir);

    const run = await runAllAccessMatrix({
      matrix,
      outputDir,
      repoRoot: process.cwd(),
      runId: 'run-008-serial-test',
    });

    expect(run.validation.ok).toBe(true);
    expect(run.artifacts.results).toBe(join(outputDir, 'pglite-all-access-results.jsonl'));
    expect(run.artifacts.validation).toBe(join(outputDir, 'pglite-all-access-validation.json'));
    expect(run.artifacts.summary).toBe(join(outputDir, 'pglite-all-access-summary.md'));
    expect(run.artifacts.manifest).toBe(join(outputDir, 'pglite-all-access-run-manifest.json'));

    const results = readFileSync(run.artifacts.results, 'utf8')
      .trim()
      .split('\n')
      .map((line) => JSON.parse(line));
    const executableRows = matrix.rows.filter((row: any) => row.execution_mode !== 'safe_non_execution');
    expect(results).toHaveLength(executableRows.length * 3);
    expect(results.every((entry: any) => entry.run_id === 'run-008-serial-test')).toBe(true);
    expect(results.some((entry: any) => entry.row_id === 'cli:sync:maintenance' && entry.structured_error?.code === 'maintenance_deferred')).toBe(true);
    expect(results.some((entry: any) => entry.row_id === 'call:list_pages:local-cli' && entry.exit_code === 0)).toBe(true);
    expect(results.every((entry: any) => entry.raw_lock_timeout_observed === false)).toBe(true);

    const manifest = JSON.parse(readFileSync(run.artifacts.manifest, 'utf8'));
    const validation = validateAllAccessResultsObject({
      run_id: manifest.run_id,
      matrix,
      results,
      safe_non_execution: matrix.rows
        .filter((row: any) => row.execution_mode === 'safe_non_execution')
        .map((row: any) => ({
          row_id: row.row_id,
          execution_mode: row.execution_mode,
          final_outcome: row.accepted_behavior_class,
          safety_rationale: row.safety_rationale,
          evidence_source_refs: row.evidence_source_refs,
          run_id: manifest.run_id,
        })),
      manifest,
    });
    expect(validation.ok).toBe(true);
  }, 120_000);
});
