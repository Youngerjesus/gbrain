import { afterEach, describe, expect, test } from 'bun:test';
import { spawn } from 'node:child_process';
import { readFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import yaml from 'js-yaml';
import {
  operationSocketPath,
  startPgliteOperationIpcServer,
  type OperationIpcRequest,
} from '../src/core/pglite-operation-ipc.ts';
import {
  classifyPgliteAccessOutput,
  validateGauntletManifestObject,
} from '../scripts/validate-pglite-access-inventory.ts';

const servers: Array<{ close: () => void }> = [];

afterEach(() => {
  for (const server of servers.splice(0)) {
    try { server.close(); } catch { /* noop */ }
  }
});

function makeHome(): { home: string; dbPath: string } {
  const home = mkdtempSync('/tmp/gbrain-pglite-inventory-');
  const dbPath = join(home, 'brain.db');
  mkdirSync(join(home, '.gbrain'), { recursive: true });
  mkdirSync(dbPath, { recursive: true });
  writeFileSync(join(home, '.gbrain', 'config.json'), JSON.stringify({
    engine: 'pglite',
    database_path: dbPath,
  }));
  return { home, dbPath };
}

function writeLiveLock(dbPath: string, command = 'gbrain serve'): void {
  const lockDir = join(dbPath, '.gbrain-lock');
  mkdirSync(lockDir, { recursive: true });
  const now = Date.now();
  writeFileSync(join(lockDir, 'lock'), JSON.stringify({
    pid: process.pid,
    acquired_at: now,
    refreshed_at: now,
    command,
  }));
}

function runCli(
  args: string[],
  home: string,
  timeoutMs = 5000,
): Promise<{ stdout: string; stderr: string; status: number | null; timedOut: boolean }> {
  return new Promise((resolve) => {
    const child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), ...args], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        NODE_ENV: 'test',
        GBRAIN_HOME: home,
        DATABASE_URL: '',
        GBRAIN_DATABASE_URL: '',
        GBRAIN_SOURCE: '',
        GBRAIN_FEDERATED_READ: '',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
    }, timeoutMs);
    child.stdout.setEncoding('utf-8');
    child.stderr.setEncoding('utf-8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (status) => {
      clearTimeout(timer);
      resolve({ stdout, stderr, status, timedOut });
    });
  });
}

describe('PGLite all-access inventory minimal gauntlet', () => {
  test('records row-id keyed live-owner results without conflating split-brain or safe-non-execution rows', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: request.operation === 'think'
          ? {
              answer: 'inventory gauntlet answer',
              gaps: [],
              modelUsed: 'test',
              pagesGathered: 0,
              takesGathered: 0,
              graphHits: 0,
              citations: [],
              warnings: [],
              saved_slug: null,
              evidence_inserted: 0,
            }
          : [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const runnableRows = [
        { row_id: 'cli:query:operation-cli', args: ['query', 'inventory-query'], command: 'gbrain query inventory-query' },
        { row_id: 'cli:search:operation-cli', args: ['search', 'inventory-search'], command: 'gbrain search inventory-search' },
        { row_id: 'cli:think:operation-cli', args: ['think', 'inventory think?', '--json'], command: 'gbrain think inventory think? --json' },
        { row_id: 'cli:sync:maintenance', args: ['sync', '--no-pull', '--no-embed', '--no-extract', '--yes', '--no-hard-deadline'], command: 'gbrain sync --no-pull --no-embed --no-extract --yes --no-hard-deadline' },
        { row_id: 'call:list_pages:local-cli', args: ['call', 'list_pages', '{}'], command: 'gbrain call list_pages {}' },
      ];
      const inventory = yaml.load(readFileSync('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml', 'utf-8')) as any;
      const safeRows = inventory.rows
        .filter((row: any) => row.gauntlet?.mode === 'safe_non_execution')
        .map((row: any) => ({
          row_id: row.id,
          reason: row.gauntlet.safe_non_execution_reason,
          future_required_outcome: row.gauntlet.future_required_outcome,
        }));
      expect(inventory.rows.filter((row: any) => row.gauntlet?.mode === 'runnable').map((row: any) => row.id).sort()).toEqual(
        runnableRows.map((row) => row.row_id).sort(),
      );

      const results: Array<Record<string, unknown>> = [];
      for (const row of runnableRows) {
        const attempts = await Promise.all(Array.from({ length: 3 }, (_, i) => runCli(row.args, home, 35_000).then((cli) => ({
          cli,
          attempt: i + 1,
        }))));
        for (const { cli, attempt } of attempts) {
          const classification = classifyPgliteAccessOutput({
            stdout: cli.stdout,
            stderr: cli.stderr,
            timed_out: cli.timedOut,
          });
          results.push({
            row_id: row.row_id,
            attempt,
            command: row.command,
            exit_code: cli.status,
            timed_out: cli.timedOut,
            stdout: cli.stdout,
            stderr: cli.stderr,
            execution_classification: classification.kind,
            raw_timeout_detected: classification.raw_timeout_detected,
            typed_error_code: classification.typed_error_code ?? null,
          });
        }
      }

      expect(seen.map((request) => request.operation).sort()).toEqual([
        'query', 'query', 'query',
        'search', 'search', 'search',
        'think', 'think', 'think',
      ]);
      for (const entry of results.filter((entry) => entry.row_id !== 'call:list_pages:local-cli')) {
        expect(entry.raw_timeout_detected).toBe(false);
        expect(entry.execution_classification).not.toBe('harness_timeout');
      }
      const listPages = results.filter((entry) => entry.row_id === 'call:list_pages:local-cli');
      expect(listPages).toHaveLength(3);
      expect(listPages.every((entry) => entry.execution_classification === 'raw_pglite_lock_timeout')).toBe(true);
      expect(listPages.every((entry) => entry.raw_timeout_detected === true)).toBe(true);
      const maintenance = results.filter((entry) => entry.row_id === 'cli:sync:maintenance');
      expect(maintenance.every((entry) => entry.typed_error_code === 'maintenance_deferred')).toBe(true);

      const manifest = validateGauntletManifestObject({
        inventory_row_ids: [...runnableRows.map((row) => row.row_id), ...safeRows.map((row: any) => row.row_id)],
        attempts_expected: 3,
        row_commands: Object.fromEntries(runnableRows.map((row) => [row.row_id, row.command])),
        harness: {
          owner_pid: process.pid,
          lock_observed: true,
          broker_ready: true,
          backend_confirmed: 'pglite-temp',
          harness_phase: 'rows',
          teardown_status: 'clean',
          cleanup_required: false,
        },
        results,
        safe_non_execution: safeRows,
      }, { inventory });
      expect(manifest).toEqual({ ok: true, errors: [], warnings: [] });
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  }, 100_000);

  test('classifies lock-held missing-socket state separately from raw PGLite timeout', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath);

      const result = await runCli(['--timeout=300ms', 'query', 'inventory-missing-socket'], home, 3000);
      const classification = classifyPgliteAccessOutput({
        stdout: result.stdout,
        stderr: result.stderr,
        timed_out: result.timedOut,
      });

      expect(result.timedOut).toBe(false);
      expect(result.status).toBe(1);
      expect(classification).toEqual({
        kind: 'typed_owner_or_guard_error',
        raw_timeout_detected: false,
        typed_error_code: 'owner_unreachable',
      });
      expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  }, 10_000);
});
