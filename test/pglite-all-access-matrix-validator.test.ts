import { describe, expect, test } from 'bun:test';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';
import {
  classifyAllAccessResult,
  generateAllAccessMatrixObject,
  matrixIdentitySha256,
  resultsIdentitySha256,
  validateAllAccessMatrixObject,
  validateAllAccessResultsObject,
} from '../scripts/validate-pglite-all-access-matrix.ts';

const inventory = yaml.load(
  readFileSync('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml', 'utf8'),
) as any;

function generatedMatrix(overrides: Record<string, unknown> = {}) {
  return {
    ...generateAllAccessMatrixObject(inventory, { repoRoot: process.cwd() }),
    ...overrides,
  };
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function sha256(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}

function resultFor(row: any, attempt: number, runId = 'run-008-unit') {
  const observedRequest = {
    source: 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture',
    caller: row.transport === 'mcp-stdio' ? 'mcp-stdio' : row.transport === 'mcp-http' ? 'mcp-http' : 'cli',
    transport: row.transport,
    operation_context_remote: row.operation_context_remote,
    surface_id: row.row_id,
  };
  const observedOutputShape = {
    source: 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture',
    final_outcome: row.accepted_behavior_class,
    exit_code: row.accepted_behavior_class === 'typed_guard_fail_fast' ? 1 : 0,
    structured_error_code: row.accepted_behavior_class === 'typed_guard_fail_fast' ? 'maintenance_deferred' : null,
  };
  return {
    row_id: row.row_id,
    attempt,
    execution_mode: row.execution_mode,
    command: row.command_or_operation,
    exit_code: row.accepted_behavior_class === 'typed_guard_fail_fast' ? 1 : 0,
    timed_out: false,
    duration_ms: 12,
    stdout_tail: row.accepted_behavior_class === 'broker_success_read' ? '[]' : '',
    stderr_tail: row.accepted_behavior_class === 'typed_guard_fail_fast' ? 'maintenance_deferred' : '',
    stdout_sha256: '0'.repeat(64),
    stderr_sha256: '1'.repeat(64),
    full_stream_classification_sha256: '2'.repeat(64),
    full_stdout: row.accepted_behavior_class === 'broker_success_read' ? '[]' : '',
    full_stderr: row.accepted_behavior_class === 'typed_guard_fail_fast' ? 'maintenance_deferred' : '',
    structured_error: row.accepted_behavior_class === 'typed_guard_fail_fast'
      ? { code: 'maintenance_deferred', message: 'deferred under live owner' }
      : null,
    route_evidence: row.execution_mode === 'live_concurrent' || row.execution_mode === 'typed_guard_concurrent'
      ? { kind: 'gbrain_serve_owner', owner_process: 'gbrain serve', live_owner_process: true, owner_status: 'healthy' }
      : null,
    fixture_evidence: row.execution_mode === 'fixture_concurrent'
      ? {
          kind: 'controlled_dispatch_fixture',
          row_id: row.row_id,
          controlled_dispatch: true,
          controlled_dispatch_source: 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture',
          policy_probe: {
            invoked: true,
            source: 'src/core/pglite-owner-policy.ts:resolvePgliteOwnerPolicy',
            behavior_class: row.accepted_behavior_class,
            remote_allowed: !row.local_only || row.operation_context_remote === false,
            local_only: row.local_only,
            requires_owner_serialization: row.accepted_behavior_class === 'serialized_owner_mutation',
          },
          dispatch_probe: {
            invoked: true,
            source: 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture',
            input_policy_behavior_class: row.accepted_behavior_class,
            output_behavior_class: row.accepted_behavior_class,
            request_sha256: sha256(JSON.stringify(observedRequest)),
            output_sha256: sha256(JSON.stringify(observedOutputShape)),
          },
          observed_request: observedRequest,
          observed_output_shape: observedOutputShape,
          policy_behavior_class: row.accepted_behavior_class,
          trust_boundary_checked: true,
          transport_exercised: row.transport,
          operation_context_remote: row.operation_context_remote,
          ...(row.transport === 'mcp-http' ? { http_owner_topology: 'http_owner_server', remote_envelope_checked: true } : {}),
          evidence_source_refs: row.evidence_source_refs,
        }
      : null,
    owner_status: 'healthy',
    final_outcome: row.accepted_behavior_class,
    raw_lock_timeout_observed: false,
    cleanup_status: 'clean',
    run_id: runId,
    pass: true,
    failure_reason: null,
    failure_category: null,
  };
}

describe('PGLite all-access matrix validator', () => {
  test('generates a matrix row for every accepted inventory row with preserved classes and trust fields', () => {
    const matrix = generatedMatrix();
    const validation = validateAllAccessMatrixObject(matrix, { inventory, repoRoot: process.cwd() });

    expect(validation).toEqual(expect.objectContaining({ ok: true, errors: [], warnings: [] }));
    expect(matrix.rows).toHaveLength(468);
    expect(matrix.attempts_expected).toBe(3);
    expect(matrix.raw_lock_timeout_allowed).toBe(false);
    expect(matrix.rows.filter((row: any) => row.accepted_behavior_class === 'broker_success_read')).toHaveLength(217);
    expect(matrix.rows.filter((row: any) => row.accepted_behavior_class === 'serialized_owner_mutation')).toHaveLength(223);
    expect(matrix.rows.filter((row: any) => row.accepted_behavior_class === 'typed_guard_fail_fast')).toHaveLength(28);

    const fileUpload = matrix.rows.find((row: any) => row.row_id === 'mcp-stdio:file_upload:local-only-rejected');
    const inventoryFileUpload = inventory.rows.find((row: any) => row.id === 'mcp-stdio:file_upload:local-only-rejected');
    expect(fileUpload).toEqual(expect.objectContaining({
      local_only: inventoryFileUpload.local_only,
      mcp_exposed: inventoryFileUpload.mcp_exposed,
      operation_context_remote: inventoryFileUpload.operation_context_remote,
      filesystem_confinement: inventoryFileUpload.filesystem_confinement,
      caller_surface: inventoryFileUpload.caller_surface,
      transport: inventoryFileUpload.transport,
      accepted_behavior_class: inventoryFileUpload.accepted_behavior_class,
    }));
  });

  test('rejects missing rows, class drift, trust-boundary drift, execution downgrades, and ambiguous HTTP evidence', () => {
    const matrix = generatedMatrix();
    const damaged = clone(matrix);
    damaged.rows = damaged.rows.filter((row: any) => row.row_id !== 'cli:query:operation-cli');
    const classDrift = damaged.rows.find((row: any) => row.row_id === 'cli:search:operation-cli');
    classDrift.accepted_behavior_class = 'typed_guard_fail_fast';
    const trustDrift = damaged.rows.find((row: any) => row.row_id === 'mcp-stdio:file_upload:local-only-rejected');
    trustDrift.operation_context_remote = false;
    const downgrade = damaged.rows.find((row: any) => row.row_id === 'cli:sync:maintenance');
    downgrade.execution_mode = 'safe_non_execution';
    downgrade.safety_rationale = 'generic maintenance command';
    const httpRow = damaged.rows.find((row: any) => row.transport === 'mcp-http');
    httpRow.http_owner_topology = 'stdio_proxy';

    const validation = validateAllAccessMatrixObject(damaged, { inventory, repoRoot: process.cwd() });

    expect(validation.ok).toBe(false);
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'matrix_row_missing', row_id: 'cli:query:operation-cli' }));
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'matrix_class_mismatch', row_id: 'cli:search:operation-cli' }));
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'trust_boundary_drift', row_id: 'mcp-stdio:file_upload:local-only-rejected' }));
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'execution_mode_downgrade', row_id: 'cli:sync:maintenance' }));
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'http_topology_mismatch', row_id: httpRow.row_id }));
  });

  test('classifies raw PGLite lock text from full streams even when retained tails are clean', () => {
    const classification = classifyAllAccessResult({
      stdout_tail: 'clean tail',
      stderr_tail: 'clean tail',
      full_stdout: 'earlier output',
      full_stderr: 'prefix Timed out waiting for PGLite lock suffix',
      timed_out: false,
      structured_error: null,
      process_error: null,
    });

    expect(classification).toEqual(expect.objectContaining({
      kind: 'raw_pglite_lock_timeout',
      raw_lock_timeout_observed: true,
    }));
  });

  test('validates result bundles for exact attempts, coherent run identity, no raw timeout, and behavior class preservation', () => {
    const matrix = generatedMatrix();
    const executableRows = matrix.rows.filter((row: any) => row.execution_mode !== 'safe_non_execution');
    const safeRows = matrix.rows.filter((row: any) => row.execution_mode === 'safe_non_execution');
    const results = executableRows.flatMap((row: any) => [1, 2, 3].map((attempt) => resultFor(row, attempt)));
    const validation = validateAllAccessResultsObject({
      run_id: 'run-008-unit',
      matrix,
      results,
      safe_non_execution: safeRows.map((row: any) => ({
        row_id: row.row_id,
        execution_mode: row.execution_mode,
        final_outcome: row.accepted_behavior_class,
        safety_rationale: row.safety_rationale,
        evidence_source_refs: row.evidence_source_refs,
        run_id: 'run-008-unit',
      })),
      manifest: {
        run_id: 'run-008-unit',
        matrix_sha256: matrixIdentitySha256(matrix),
        inventory_sha256: matrix.inventory_sha256,
        status: 'pass',
        cleanup_status: 'clean',
        artifact_hashes: {
          results_sha256: resultsIdentitySha256(results),
        },
        owner_session: { status: 'healthy' },
      },
    });

    expect(validation).toEqual(expect.objectContaining({
      ok: true,
      summary: expect.objectContaining({
        executable_row_count: executableRows.length,
        safe_non_execution_row_count: safeRows.length,
        raw_timeout_count: 0,
      }),
    }));

    const broken = clone(results);
    broken.pop();
    broken[0].full_stderr = 'Could not acquire PGLite lock';
    broken[1].final_outcome = 'typed_guard_fail_fast';
    broken[2].run_id = 'other-run';
    broken[3].owner_status = 'lost';
    broken[4].cleanup_status = 'failed';
    broken[5].pass = false;
    broken[5].failure_reason = 'controlled failure flag';
    broken[5].failure_category = 'harness_failure';
    broken.push({ ...results[5], attempt: 1 });
    const typedGuard = broken.find((entry: any) => entry.row_id === 'cli:sync:maintenance');
    typedGuard.exit_code = 0;
    typedGuard.structured_error = null;
    typedGuard.full_stderr = '';
    typedGuard.stderr_tail = '';
    const tailRawTimeout = { ...results[6] };
    delete tailRawTimeout.full_stdout;
    delete tailRawTimeout.full_stderr;
    tailRawTimeout.stderr_tail = 'GBrain: Timed out waiting for PGLite lock';
    broken.push(tailRawTimeout);
    const fixture = broken.find((entry: any) => entry.execution_mode === 'fixture_concurrent');
    fixture.fixture_evidence.dispatch_probe = null;
    delete fixture.fixture_evidence.controlled_dispatch_source;
    const mcpFixture = broken.find((entry: any) => entry.fixture_evidence && entry.fixture_evidence.transport_exercised?.startsWith('mcp-'));
    if (mcpFixture) mcpFixture.fixture_evidence.transport_exercised = 'local-cli';

    const brokenValidation = validateAllAccessResultsObject({
      run_id: 'run-008-unit',
      matrix,
      results: broken,
      safe_non_execution: [],
      manifest: {
        run_id: 'run-008-unit',
        matrix_sha256: 'b'.repeat(64),
        inventory_sha256: 'c'.repeat(64),
        status: 'pass',
        cleanup_status: 'clean',
        artifact_hashes: {
          results_sha256: 'd'.repeat(64),
        },
        owner_session: { status: 'healthy' },
      },
    });

    expect(brokenValidation.ok).toBe(false);
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'raw_timeout_observed' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'behavior_class_mismatch' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'stale_or_mixed_artifact' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'owner_lost' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'cleanup_failed' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'result_marked_failed' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'wrong_attempt_count' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'missing_result_field', field: 'full_stdout' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'typed_guard_shape_mismatch' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'fixture_evidence_missing' }));
    expect(brokenValidation.errors).toContainEqual(expect.objectContaining({ code: 'trust_boundary_evidence_mismatch' }));
  });

  test('rejects stale fixture dispatch provenance hashes in an otherwise coherent bundle', () => {
    const matrix = generatedMatrix();
    const executableRows = matrix.rows.filter((row: any) => row.execution_mode !== 'safe_non_execution');
    const safeRows = matrix.rows.filter((row: any) => row.execution_mode === 'safe_non_execution');
    const results = executableRows.flatMap((row: any) => [1, 2, 3].map((attempt) => resultFor(row, attempt)));
    const fixture = results.find((entry: any) => entry.execution_mode === 'fixture_concurrent');
    fixture.fixture_evidence.dispatch_probe.request_sha256 = 'a'.repeat(64);
    fixture.fixture_evidence.dispatch_probe.output_sha256 = 'b'.repeat(64);

    const validation = validateAllAccessResultsObject({
      run_id: 'run-008-unit',
      matrix,
      results,
      safe_non_execution: safeRows.map((row: any) => ({
        row_id: row.row_id,
        execution_mode: row.execution_mode,
        final_outcome: row.accepted_behavior_class,
        safety_rationale: row.safety_rationale,
        evidence_source_refs: row.evidence_source_refs,
        run_id: 'run-008-unit',
      })),
      manifest: {
        run_id: 'run-008-unit',
        matrix_sha256: matrixIdentitySha256(matrix),
        inventory_sha256: matrix.inventory_sha256,
        status: 'pass',
        cleanup_status: 'clean',
        artifact_hashes: {
          results_sha256: resultsIdentitySha256(results),
        },
        owner_session: { status: 'healthy' },
      },
    });

    expect(validation.ok).toBe(false);
    expect(validation.errors).toContainEqual(expect.objectContaining({
      code: 'fixture_dispatch_hash_mismatch',
      row_id: fixture.row_id,
    }));
  });

  test('rejects stale matrix inventory identity and source fingerprints', () => {
    const matrix = generatedMatrix({
      inventory_sha256: 'not-current',
      source_fingerprints: {
        'src/core/operations.ts': 'stale',
        'src/cli.ts': 'stale',
        'src/mcp/server.ts': 'stale',
        'src/commands/serve-http.ts': 'stale',
      },
    });
    const validation = validateAllAccessMatrixObject(matrix, { inventory, repoRoot: process.cwd() });

    expect(validation.ok).toBe(false);
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'inventory_stale', field: 'inventory_sha256' }));
    expect(validation.errors).toContainEqual(expect.objectContaining({ code: 'stale_source_fingerprint', field: 'source_fingerprints.src/core/operations.ts' }));
  });

  test('CLI entrypoints return structured missing-inventory errors instead of stack traces', () => {
    for (const args of [
      ['run', 'scripts/generate-pglite-all-access-matrix.ts', '--inventory', '/tmp/gbrain-missing-inventory.yml', '--out', '/tmp/gbrain-matrix.yml', '--json'],
      ['run', 'scripts/validate-pglite-all-access-matrix.ts', '--matrix', 'requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-command-matrix.yml', '--inventory', '/tmp/gbrain-missing-inventory.yml', '--json'],
    ]) {
      const result = spawnSync('bun', args, {
        cwd: process.cwd(),
        encoding: 'utf8',
      });
      expect(result.status).toBe(1);
      expect(result.stderr).not.toContain('ENOENT');
      const body = JSON.parse(result.stdout);
      expect(body.ok).toBe(false);
      expect(body.errors).toContainEqual(expect.objectContaining({
        code: 'missing_inventory',
      }));
    }
  });

  test('runner returns structured missing-matrix errors instead of stack traces', () => {
    const result = spawnSync('bun', [
      'run',
      'scripts/run-pglite-all-access-matrix.ts',
      '--matrix',
      '/tmp/gbrain-missing-matrix.yml',
      '--output_dir',
      '/tmp/gbrain-008-missing-matrix',
      '--json',
    ], {
      cwd: process.cwd(),
      encoding: 'utf8',
    });
    expect(result.status).toBe(1);
    expect(result.stderr).not.toContain('ENOENT');
    const body = JSON.parse(result.stdout);
    expect(body.ok).toBe(false);
    expect(body.errors).toContainEqual(expect.objectContaining({
      code: 'missing_matrix',
    }));
  });

  test('CLI entrypoints provide non-mutating usage help', () => {
    for (const args of [
      ['run', 'scripts/generate-pglite-all-access-matrix.ts', '--help'],
      ['run', 'scripts/validate-pglite-all-access-matrix.ts', '--help'],
      ['run', 'scripts/run-pglite-all-access-matrix.ts', '--help'],
    ]) {
      const result = spawnSync('bun', args, {
        cwd: process.cwd(),
        encoding: 'utf8',
      });
      expect(result.status).toBe(0);
      expect(result.stdout).toContain('Usage:');
      expect(result.stdout).toContain(args[1]);
      expect(result.stderr).toBe('');
    }
  });
});
