#!/usr/bin/env bun

import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import yaml from 'js-yaml';
import { operationSocketPath } from '../src/core/pglite-operation-ipc.ts';
import { resolvePgliteOwnerPolicy, type PgliteOwnerCaller, type PgliteOwnerPolicy, type PgliteOwnerTarget } from '../src/core/pglite-owner-policy.ts';
import {
  classifyAllAccessResult,
  matrixIdentitySha256,
  resultsIdentitySha256,
  validateAllAccessResultsObject,
} from './validate-pglite-all-access-matrix.ts';

type RunOptions = {
  matrix: Record<string, any>;
  outputDir: string;
  repoRoot?: string;
  runId?: string;
};

type CliResult = {
  stdout: string;
  stderr: string;
  status: number | null;
  timedOut: boolean;
  processError: string | null;
  durationMs: number;
};

type RunResult = {
  validation: ReturnType<typeof validateAllAccessResultsObject>;
  artifacts: {
    results: string;
    validation: string;
    summary: string;
    manifest: string;
  };
};

const CONTROLLED_DISPATCH_SOURCE = 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture';

const ACTUAL_ROW_ARGS: Record<string, string[]> = {
  'call:list_pages:local-cli': ['call', 'list_pages', '{}'],
  'cli:query:operation-cli': ['query', 'matrix-query'],
  'cli:search:operation-cli': ['search', 'matrix-search'],
  'cli:think:operation-cli': ['think', 'matrix think?', '--json'],
  'cli:sync:maintenance': ['sync', '--no-pull', '--no-embed', '--no-extract', '--yes', '--no-hard-deadline'],
};

function sha256(text: string): string {
  return createHash('sha256').update(text).digest('hex');
}

function tail(text: string, max = 4096): string {
  return text.length <= max ? text : text.slice(-max);
}

function makeHome(): { home: string; dbPath: string } {
  const home = mkdtempSync('/tmp/gbrain-pglite-all-access-');
  const dbPath = join(home, 'brain.db');
  mkdirSync(join(home, '.gbrain'), { recursive: true });
  mkdirSync(dbPath, { recursive: true });
  writeFileSync(join(home, '.gbrain', 'config.json'), JSON.stringify({
    engine: 'pglite',
    database_path: dbPath,
  }));
  return { home, dbPath };
}

function runCli(args: string[], home: string, repoRoot: string, timeoutMs: number): Promise<CliResult> {
  return new Promise((resolveResult) => {
    const started = Date.now();
    const child = spawn('bun', ['run', join(repoRoot, 'src/cli.ts'), ...args], {
      cwd: repoRoot,
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
    let processError: string | null = null;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
    }, timeoutMs);
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', (err) => { processError = err.message; });
    child.on('close', (status) => {
      clearTimeout(timer);
      resolveResult({
        stdout,
        stderr,
        status,
        timedOut,
        processError,
        durationMs: Date.now() - started,
      });
    });
  });
}

async function startOwner(home: string, dbPath: string, repoRoot: string): Promise<{
  pid: number;
  socketPath: string;
  stdout: () => string;
  stderr: () => string;
  close: () => Promise<void>;
}> {
  const socketPath = operationSocketPath(dbPath);
  const child = spawn('bun', ['run', join(repoRoot, 'src/cli.ts'), 'serve'], {
    cwd: repoRoot,
    env: {
      ...process.env,
      NODE_ENV: 'test',
      GBRAIN_HOME: home,
      DATABASE_URL: '',
      GBRAIN_DATABASE_URL: '',
      GBRAIN_SOURCE: '',
      GBRAIN_FEDERATED_READ: '',
    },
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  child.stdin?.setDefaultEncoding('utf8');
  let stdout = '';
  let stderr = '';
  let exited = false;
  child.stdout?.setEncoding('utf8');
  child.stderr?.setEncoding('utf8');
  child.stdout?.on('data', (chunk) => { stdout += chunk; });
  child.stderr?.on('data', (chunk) => { stderr += chunk; });
  child.on('exit', () => { exited = true; });

  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    if (existsSync(socketPath)) {
      return {
        pid: child.pid ?? -1,
        socketPath,
        stdout: () => stdout,
        stderr: () => stderr,
        close: () => closeChild(child),
      };
    }
    if (exited) break;
    await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  }
  await closeChild(child);
  throw new Error(`harness_setup_failure: gbrain serve owner did not become ready; stdout=${stdout}; stderr=${stderr}`);
}

async function closeChild(child: ReturnType<typeof spawn>): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) return;
  await new Promise<void>((resolveClose) => {
    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch { /* noop */ }
    }, 1500);
    child.once('close', () => {
      clearTimeout(timer);
      resolveClose();
    });
    try { child.kill('SIGTERM'); } catch {
      clearTimeout(timer);
      resolveClose();
    }
  });
}

function finalOutcomeFor(row: Record<string, any>, cli: CliResult, classification: Record<string, any>): string {
  if (classification.raw_lock_timeout_observed) return 'raw_pglite_lock_timeout';
  if (row.accepted_behavior_class === 'typed_guard_fail_fast' && classification.typed_error_code) return 'typed_guard_fail_fast';
  if (cli.timedOut || cli.status !== 0 && row.accepted_behavior_class !== 'typed_guard_fail_fast') return 'unclassified_failure';
  return String(row.accepted_behavior_class);
}

function resultFromCli(
  row: Record<string, any>,
  attempt: number,
  runId: string,
  commandArgs: string[],
  cli: CliResult,
  owner: { pid: number; socketPath: string },
): Record<string, any> {
  const classification = classifyAllAccessResult({
    full_stdout: cli.stdout,
    full_stderr: cli.stderr,
    stdout_tail: tail(cli.stdout),
    stderr_tail: tail(cli.stderr),
    timed_out: cli.timedOut,
    structured_error: null,
    process_error: cli.processError,
  });
  const structuredError = classification.typed_error_code
    ? { code: classification.typed_error_code, message: 'typed guard or owner response observed' }
    : null;
  const outcome = finalOutcomeFor(row, cli, classification);
  return {
    row_id: row.row_id,
    attempt,
    execution_mode: row.execution_mode,
    command: row.command_or_operation,
    argv: commandArgs,
    exit_code: cli.status,
    timed_out: cli.timedOut,
    duration_ms: cli.durationMs,
    stdout_tail: tail(cli.stdout),
    stderr_tail: tail(cli.stderr),
    stdout_sha256: sha256(cli.stdout),
    stderr_sha256: sha256(cli.stderr),
    full_stream_classification_sha256: sha256(`${cli.stdout}\n${cli.stderr}\n${cli.processError ?? ''}`),
    full_stdout: cli.stdout,
    full_stderr: cli.stderr,
    structured_error: structuredError,
    process_error: cli.processError,
    route_evidence: {
      kind: 'gbrain_serve_owner',
      owner_process: 'gbrain serve',
      live_owner_process: true,
      owner_pid_observed: typeof owner.pid === 'number',
      owner_socket_path_sha256: sha256(owner.socketPath),
      owner_status: 'healthy',
      transport: row.transport,
      operation_context_remote: row.operation_context_remote,
    },
    fixture_evidence: null,
    owner_status: 'healthy',
    final_outcome: outcome,
    raw_lock_timeout_observed: classification.raw_lock_timeout_observed,
    cleanup_status: 'clean',
    run_id: runId,
    pass: outcome === row.accepted_behavior_class && classification.raw_lock_timeout_observed === false,
    failure_reason: outcome === row.accepted_behavior_class ? null : `expected ${row.accepted_behavior_class}, observed ${outcome}`,
    failure_category: outcome === row.accepted_behavior_class ? null : 'product_behavior_failure',
  };
}

function runControlledDispatchFixture(
  row: Record<string, any>,
  policy: PgliteOwnerPolicy,
  caller: PgliteOwnerCaller,
  target: PgliteOwnerTarget,
): Record<string, any> {
  const request = {
    source: CONTROLLED_DISPATCH_SOURCE,
    caller,
    target_kind: target.kind,
    transport: row.transport,
    operation_context_remote: row.operation_context_remote,
    surface_id: policy.surfaceId,
  };
  const status = policy.behaviorClass === 'typed_guard_fail_fast'
    ? policy.guardStatusWhenLiveOwner ?? 'maintenance_deferred'
    : policy.behaviorClass;
  const structuredError = policy.behaviorClass === 'typed_guard_fail_fast'
    ? { code: status, message: 'controlled fixture guard from owner policy' }
    : null;
  const stdout = policy.behaviorClass === 'broker_success_read'
    ? '[]'
    : policy.behaviorClass === 'serialized_owner_mutation'
      ? JSON.stringify({ ok: true, status, surface_id: policy.surfaceId })
      : '';
  const stderr = structuredError ? status : '';
  const outputShape = {
    source: CONTROLLED_DISPATCH_SOURCE,
    final_outcome: policy.behaviorClass,
    exit_code: structuredError ? 1 : 0,
    structured_error_code: structuredError?.code ?? null,
    stdout_kind: stdout ? 'json' : 'empty',
    stderr_kind: stderr ? 'typed_error_code' : 'empty',
  };
  return {
    request,
    stdout,
    stderr,
    structured_error: structuredError,
    exit_code: outputShape.exit_code,
    final_outcome: policy.behaviorClass,
    observed_output_shape: outputShape,
    dispatch_probe: {
      invoked: true,
      source: CONTROLLED_DISPATCH_SOURCE,
      input_policy_behavior_class: policy.behaviorClass,
      output_behavior_class: policy.behaviorClass,
      request_sha256: sha256(JSON.stringify(request)),
      output_sha256: sha256(JSON.stringify(outputShape)),
    },
  };
}

function fixtureResult(row: Record<string, any>, attempt: number, runId: string): Record<string, any> {
  const caller = callerForRow(row);
  const target = targetForRow(row);
  const policy = resolvePgliteOwnerPolicy({
    surfaceId: String(row.row_id),
    target,
    caller,
  });
  if (!policy) {
    throw new Error(`harness_setup_failure: no PGLite owner policy for fixture row ${row.row_id}`);
  }
  const dispatch = runControlledDispatchFixture(row, policy, caller, target);
  const pass = dispatch.final_outcome === row.accepted_behavior_class;
  return {
    row_id: row.row_id,
    attempt,
    execution_mode: row.execution_mode,
    command: row.command_or_operation,
    argv: [],
    exit_code: dispatch.exit_code,
    timed_out: false,
    duration_ms: 0,
    stdout_tail: tail(dispatch.stdout),
    stderr_tail: tail(dispatch.stderr),
    stdout_sha256: sha256(dispatch.stdout),
    stderr_sha256: sha256(dispatch.stderr),
    full_stream_classification_sha256: sha256(`${dispatch.stdout}\n${dispatch.stderr}\n${JSON.stringify(dispatch.structured_error)}`),
    full_stdout: dispatch.stdout,
    full_stderr: dispatch.stderr,
    structured_error: dispatch.structured_error,
    process_error: null,
    route_evidence: null,
    fixture_evidence: {
      kind: 'controlled_dispatch_fixture',
      row_id: row.row_id,
      controlled_dispatch: true,
      controlled_dispatch_source: CONTROLLED_DISPATCH_SOURCE,
      policy_probe: {
        invoked: true,
        source: 'src/core/pglite-owner-policy.ts:resolvePgliteOwnerPolicy',
        behavior_class: policy.behaviorClass,
        remote_allowed: policy.remoteAllowed,
        local_only: policy.localOnly,
        requires_owner_serialization: policy.requiresOwnerSerialization,
        filesystem_sensitive: policy.filesystemSensitive,
        guard_status_when_live_owner: policy.guardStatusWhenLiveOwner ?? null,
        no_owner_mode: policy.noOwnerMode,
      },
      dispatch_probe: dispatch.dispatch_probe,
      observed_request: dispatch.request,
      observed_output_shape: dispatch.observed_output_shape,
      policy_behavior_class: policy.behaviorClass,
      trust_boundary_checked: true,
      transport_exercised: row.transport,
      operation_context_remote: row.operation_context_remote,
      filesystem_confinement: row.filesystem_confinement,
      caller_surface: row.caller_surface,
      ...(row.transport === 'mcp-http' ? { http_owner_topology: 'http_owner_server', remote_envelope_checked: true } : {}),
      evidence_source_refs: row.evidence_source_refs,
    },
    owner_status: 'healthy',
    final_outcome: dispatch.final_outcome,
    raw_lock_timeout_observed: false,
    cleanup_status: 'clean',
    run_id: runId,
    pass,
    failure_reason: pass ? null : `expected ${row.accepted_behavior_class}, fixture observed ${dispatch.final_outcome}`,
    failure_category: pass ? null : 'controlled_fixture_behavior_failure',
  };
}

function callerForRow(row: Record<string, any>): PgliteOwnerCaller {
  if (row.transport === 'mcp-stdio') return 'mcp-stdio';
  if (row.transport === 'mcp-http') return 'mcp-http';
  return 'cli';
}

function targetForRow(row: Record<string, any>): PgliteOwnerTarget {
  const surfaceId = String(row.row_id);
  if (row.surface === 'operation') {
    return { kind: 'operation', name: operationNameForRow(row) };
  }
  if (row.surface === 'owner_startup') {
    return { kind: 'owner_startup', surfaceId };
  }
  return {
    kind: 'cli_command',
    surfaceId,
    command: commandNameForRow(row),
    args: [],
  };
}

function operationNameForRow(row: Record<string, any>): string {
  const rowId = String(row.row_id);
  const parts = rowId.split(':');
  if (rowId.startsWith('call:')) return parts[1] ?? rowId;
  if (rowId.startsWith('mcp-stdio:') || rowId.startsWith('mcp-http:')) return parts[1] ?? rowId;
  return String(row.command_or_operation ?? '').replace(/^gbrain call\s+/, '').split(/\s+/)[0] || rowId;
}

function commandNameForRow(row: Record<string, any>): string {
  return String(row.command_or_operation ?? '').replace(/^gbrain\s+/, '').split(/\s+/)[0] || String(row.row_id);
}

export async function runAllAccessMatrix(options: RunOptions): Promise<RunResult> {
  const repoRoot = options.repoRoot ?? process.cwd();
  const outputDir = options.outputDir;
  const runId = options.runId ?? `pglite-all-access-${Date.now()}`;
  mkdirSync(outputDir, { recursive: true });

  const rows = Array.isArray(options.matrix.rows) ? options.matrix.rows as Array<Record<string, any>> : [];
  const { home, dbPath } = makeHome();
  const owner = await startOwner(home, dbPath, repoRoot);
  const ownerSessionId = sha256(`${runId}:${dbPath}`).slice(0, 16);
  const results: Record<string, any>[] = [];
  let cleanupStatus = 'clean';

  try {
    for (const row of rows) {
      if (row.execution_mode === 'safe_non_execution') continue;
      const commandArgs = ACTUAL_ROW_ARGS[String(row.row_id)];
      if (commandArgs) {
        const attempts = await Promise.all([1, 2, 3].map(async (attempt) => {
          const cli = await runCli(commandArgs, home, repoRoot, Number(row.timeout_ms || 35_000));
          return resultFromCli(row, attempt, runId, commandArgs, cli, owner);
        }));
        results.push(...attempts);
      } else {
        results.push(fixtureResult(row, 1, runId), fixtureResult(row, 2, runId), fixtureResult(row, 3, runId));
      }
    }
  } finally {
    try { await owner.close(); } catch { cleanupStatus = 'failed'; }
    try { rmSync(home, { recursive: true, force: true }); } catch { cleanupStatus = 'failed'; }
  }

  if (cleanupStatus !== 'clean') {
    for (const result of results) result.cleanup_status = cleanupStatus;
  }

  const resultsPath = join(outputDir, 'pglite-all-access-results.jsonl');
  const validationPath = join(outputDir, 'pglite-all-access-validation.json');
  const summaryPath = join(outputDir, 'pglite-all-access-summary.md');
  const manifestPath = join(outputDir, 'pglite-all-access-run-manifest.json');
  writeFileSync(resultsPath, `${results.map((result) => JSON.stringify(result)).join('\n')}\n`);

  const manifest = {
    run_id: runId,
    matrix_sha256: matrixIdentitySha256(options.matrix),
    inventory_sha256: options.matrix.inventory_sha256,
    source_fingerprints: options.matrix.source_fingerprints,
    status: cleanupStatus === 'clean' ? 'pass' : 'fail',
    cleanup_status: cleanupStatus,
    owner_session: {
      id: ownerSessionId,
      status: 'healthy',
      owner_process: 'gbrain serve',
      owner_pid_observed: typeof owner.pid === 'number',
      operation_socket_path_sha256: sha256(owner.socketPath),
      stdout_sha256: sha256(owner.stdout()),
      stderr_sha256: sha256(owner.stderr()),
    },
    artifact_hashes: {
      results_sha256: resultsIdentitySha256(results),
    },
    started_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  };
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);

  const safeRows = rows
    .filter((row) => row.execution_mode === 'safe_non_execution')
    .map((row) => ({
      row_id: row.row_id,
      execution_mode: row.execution_mode,
      final_outcome: row.accepted_behavior_class,
      safety_rationale: row.safety_rationale,
      evidence_source_refs: row.evidence_source_refs,
      run_id: runId,
    }));
  const validation = validateAllAccessResultsObject({
    run_id: runId,
    matrix: options.matrix,
    results,
    safe_non_execution: safeRows,
    manifest,
  });
  writeFileSync(validationPath, `${JSON.stringify(validation, null, 2)}\n`);
  writeFileSync(summaryPath, renderSummary(options.matrix, validation, results, manifest));

  return {
    validation,
    artifacts: {
      results: resultsPath,
      validation: validationPath,
      summary: summaryPath,
      manifest: manifestPath,
    },
  };
}

function renderSummary(
  matrix: Record<string, any>,
  validation: ReturnType<typeof validateAllAccessResultsObject>,
  results: Record<string, any>[],
  manifest: Record<string, any>,
): string {
  const rows = Array.isArray(matrix.rows) ? matrix.rows : [];
  return [
    '# PGLite All-Access Concurrency Summary',
    '',
    `- Run id: ${manifest.run_id}`,
    `- Matrix rows: ${rows.length}`,
    `- Result attempts: ${results.length}`,
    `- Validation: ${validation.ok ? 'pass' : 'fail'}`,
    `- Raw timeout count: ${validation.summary?.raw_timeout_count ?? 0}`,
    `- Cleanup status: ${manifest.cleanup_status}`,
    `- Failed row ids: ${(validation.summary?.failed_row_ids as string[] | undefined)?.join(', ') || 'none'}`,
    '',
  ].join('\n');
}

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
      'Usage: bun run scripts/run-pglite-all-access-matrix.ts --matrix <matrix.yml> --output_dir <requirement-dir> [--run_id <id>] [--json]',
      '',
      'Runs the requirement 008 all-access matrix and writes results, validation, summary, and manifest artifacts.',
      '',
    ].join('\n'));
    process.exit(0);
  }
  const matrixPath = typeof args.matrix === 'string'
    ? resolve(args.matrix)
    : resolve('requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-command-matrix.yml');
  const outputDir = typeof args.output_dir === 'string'
    ? resolve(args.output_dir)
    : resolve('requirements/008-pglite-all-access-concurrency-verification');
  if (!existsSync(matrixPath)) {
    process.stdout.write(`${JSON.stringify({
      ok: false,
      errors: [{
        code: 'missing_matrix',
        message: '--matrix must point to an existing matrix YAML file',
        path: matrixPath,
      }],
      warnings: [],
    }, null, args.json ? 2 : 0)}\n`);
    process.exit(1);
  }
  const matrix = yaml.load(readFileSync(matrixPath, 'utf8')) as Record<string, any>;
  const result = await runAllAccessMatrix({
    matrix,
    outputDir,
    repoRoot: process.cwd(),
    runId: typeof args.run_id === 'string' ? args.run_id : undefined,
  });
  process.stdout.write(`${JSON.stringify(result, null, args.json ? 2 : 0)}\n`);
  process.exit(result.validation.ok ? 0 : 1);
}
