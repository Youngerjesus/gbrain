#!/usr/bin/env bun

import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import yaml from 'js-yaml';
import {
  sourceFingerprint,
  validateInventoryObject,
} from './validate-pglite-access-inventory.ts';

type Diagnostic = {
  code: string;
  message: string;
  row_id?: string;
  field?: string;
};

type ValidationResult = {
  ok: boolean;
  errors: Diagnostic[];
  warnings: Diagnostic[];
  summary?: Record<string, unknown>;
};

type MatrixOptions = {
  repoRoot?: string;
  inventorySha256?: string;
};

type MatrixValidationOptions = {
  inventory?: unknown;
  repoRoot?: string;
};

const REQUIRED_TRUST_FIELDS = [
  'local_only',
  'mcp_exposed',
  'operation_context_remote',
  'filesystem_confinement',
  'caller_surface',
  'transport',
] as const;

const EXECUTION_MODES = new Set([
  'live_concurrent',
  'typed_guard_concurrent',
  'dry_run_concurrent',
  'fixture_concurrent',
  'safe_non_execution',
]);

const BEHAVIOR_CLASSES = new Set([
  'broker_success_read',
  'serialized_owner_mutation',
  'typed_guard_fail_fast',
]);

const RAW_TIMEOUT_RE = /Timed out waiting for PGLite lock|Could not acquire PGLite lock|PGLite.*lock.*timeout|connect.*PGLite.*timeout/i;
const CONTROLLED_DISPATCH_SOURCE = 'scripts/run-pglite-all-access-matrix.ts:runControlledDispatchFixture';
const SHA256_RE = /^[a-f0-9]{64}$/;

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, any> : {};
}

function asRows(value: unknown): Array<Record<string, any>> {
  return Array.isArray(value) ? value.filter((row): row is Record<string, any> => !!row && typeof row === 'object' && !Array.isArray(row)) : [];
}

function diagnostic(errors: Diagnostic[], code: string, message: string, extra: Omit<Diagnostic, 'code' | 'message'> = {}): void {
  errors.push({ code, message, ...extra });
}

function sha256(text: string): string {
  return createHash('sha256').update(text).digest('hex');
}

function stableJson(value: unknown): string {
  return JSON.stringify(sortKeys(value));
}

export function matrixIdentitySha256(matrix: unknown): string {
  return sha256(stableJson(matrix));
}

export function resultsIdentitySha256(results: unknown[]): string {
  return sha256(`${results.map((result) => JSON.stringify(result)).join('\n')}\n`);
}

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value as Record<string, unknown>)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, child]) => [key, sortKeys(child)]));
}

function inventoryRows(inventory: unknown): Array<Record<string, any>> {
  return asRows(asRecord(inventory).rows);
}

function executionModeForInventoryRow(row: Record<string, any>): string {
  const gauntletMode = String(asRecord(row.gauntlet).mode ?? '');
  if (gauntletMode === 'safe_non_execution') return 'safe_non_execution';
  if (gauntletMode === 'dry_run') return 'dry_run_concurrent';
  if (gauntletMode === 'runnable' && row.accepted_behavior_class === 'typed_guard_fail_fast') return 'typed_guard_concurrent';
  if (gauntletMode === 'runnable') return 'live_concurrent';
  return 'fixture_concurrent';
}

function fixtureProfileForInventoryRow(row: Record<string, any>): string {
  const id = String(row.id ?? '');
  const preconditions = Array.isArray(row.data_preconditions) ? row.data_preconditions.map(String).join(' ') : '';
  if (/apply-migrations|upgrade|migrate|schema|repair-jsonb/.test(id)) return 'migration_pending_schema';
  if (/seeded|source|page/.test(preconditions) || row.scope === 'read') return 'seeded_source_page';
  return 'empty_initialized';
}

function ownerSequenceForInventoryRow(row: Record<string, any>): Record<string, string> | null {
  if (row.entry_kind !== 'owner_startup') return null;
  if (row.id === 'serve:duplicate-owner-start') {
    return {
      actor_a: 'existing_owner',
      actor_b: 'duplicate_owner_start',
      initial_state: 'owner_live',
      next_state: 'duplicate_start_rejected',
      expected_outcome: 'typed_guard_fail_fast',
    };
  }
  return {
    actor_a: 'owner_process',
    actor_b: 'client_probe',
    initial_state: 'no_owner',
    next_state: 'owner_ready',
    expected_outcome: 'serialized_owner_mutation',
  };
}

export function generateAllAccessMatrixObject(inventory: unknown, options: MatrixOptions = {}): Record<string, any> {
  const repoRoot = options.repoRoot ?? process.cwd();
  const inv = asRecord(inventory);
  const rows = inventoryRows(inventory).map((row) => {
    const executionMode = executionModeForInventoryRow(row);
    const gauntlet = asRecord(row.gauntlet);
    const ownerSequence = ownerSequenceForInventoryRow(row);
    return {
      row_id: String(row.id),
      command_or_operation: String(row.command_or_operation ?? ''),
      surface: String(row.entry_kind ?? ''),
      caller: String(row.caller_surface ?? ''),
      transport: String(row.transport ?? ''),
      local_only: row.local_only,
      mcp_exposed: row.mcp_exposed,
      operation_context_remote: row.operation_context_remote,
      filesystem_confinement: String(row.filesystem_confinement ?? ''),
      caller_surface: String(row.caller_surface ?? ''),
      accepted_behavior_class: String(row.accepted_behavior_class ?? ''),
      expected_final_outcome: String(row.accepted_behavior_class ?? ''),
      execution_mode: executionMode,
      attempts: executionMode === 'safe_non_execution' ? 0 : 3,
      timeout_ms: executionMode === 'safe_non_execution' ? 0 : 35_000,
      fixture_profile: fixtureProfileForInventoryRow(row),
      ...(ownerSequence ? { owner_sequence: ownerSequence } : {}),
      ...(row.transport === 'mcp-http' ? { http_owner_topology: 'http_owner_server' } : {}),
      args_or_params_profile: String(row.argument_profile ?? ''),
      data_preconditions: Array.isArray(row.data_preconditions) ? row.data_preconditions.map(String) : [],
      safety_rationale: executionMode === 'safe_non_execution'
        ? String(gauntlet.safe_non_execution_reason ?? '')
        : `Executes ${executionMode} in an isolated temporary PGLite home or controlled fixture.`,
      evidence_source_refs: Array.isArray(row.evidence_refs) ? row.evidence_refs.map(String) : [],
      inventory_gauntlet_mode: String(gauntlet.mode ?? ''),
    };
  });

  return {
    requirement_id: '008-pglite-all-access-concurrency-verification',
    schema_version: 1,
    inventory_ref: 'requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml',
    inventory_sha256: options.inventorySha256 ?? sha256(stableJson(inventory)),
    source_fingerprints: inv.source_fingerprints ?? {
      'src/core/operations.ts': sourceFingerprint(repoRoot, 'src/core/operations.ts'),
      'src/cli.ts': sourceFingerprint(repoRoot, 'src/cli.ts'),
      'src/mcp/server.ts': sourceFingerprint(repoRoot, 'src/mcp/server.ts'),
      'src/commands/serve-http.ts': sourceFingerprint(repoRoot, 'src/commands/serve-http.ts'),
    },
    attempts_expected: 3,
    raw_lock_timeout_allowed: false,
    rows,
  };
}

export function validateAllAccessMatrixObject(input: unknown, options: MatrixValidationOptions = {}): ValidationResult {
  const matrix = asRecord(input);
  const inventory = asRecord(options.inventory);
  const rows = asRows(matrix.rows);
  const acceptedRows = inventoryRows(inventory);
  const errors: Diagnostic[] = [];
  const warnings: Diagnostic[] = [];

  if (matrix.requirement_id !== '008-pglite-all-access-concurrency-verification') {
    diagnostic(errors, 'invalid_requirement_id', 'matrix requirement_id must be 008-pglite-all-access-concurrency-verification', { field: 'requirement_id' });
  }
  if (matrix.schema_version !== 1) {
    diagnostic(errors, 'invalid_schema_version', 'matrix schema_version must be 1', { field: 'schema_version' });
  }
  if (matrix.attempts_expected !== 3) {
    diagnostic(errors, 'invalid_attempts_expected', 'matrix attempts_expected must be 3', { field: 'attempts_expected' });
  }
  if (matrix.raw_lock_timeout_allowed !== false) {
    diagnostic(errors, 'raw_timeout_allowed', 'matrix must disallow raw PGLite lock/connect timeouts', { field: 'raw_lock_timeout_allowed' });
  }

  if (options.inventory) {
    const expectedInventorySha = sha256(stableJson(inventory));
    if (matrix.inventory_sha256 !== expectedInventorySha) {
      diagnostic(errors, 'inventory_stale', 'matrix inventory_sha256 differs from accepted inventory identity', { field: 'inventory_sha256' });
    }
    const fingerprints = asRecord(matrix.source_fingerprints);
    for (const source of ['src/core/operations.ts', 'src/cli.ts', 'src/mcp/server.ts', 'src/commands/serve-http.ts']) {
      const actual = sourceFingerprint(options.repoRoot ?? process.cwd(), source);
      if (fingerprints[source] !== actual) {
        diagnostic(errors, 'stale_source_fingerprint', `matrix source fingerprint for ${source} is stale`, {
          field: `source_fingerprints.${source}`,
        });
      }
    }
    const inventoryValidation = validateInventoryObject(inventory, { repoRoot: options.repoRoot ?? process.cwd() });
    for (const error of inventoryValidation.errors) {
      diagnostic(errors, 'inventory_stale', error.message, { row_id: error.row_id, field: error.field });
    }
  }

  const seen = new Set<string>();
  const rowById = new Map<string, Record<string, any>>();
  for (const row of rows) {
    const rowId = String(row.row_id ?? '');
    if (!rowId) {
      diagnostic(errors, 'missing_row_id', 'matrix row is missing row_id');
      continue;
    }
    if (seen.has(rowId)) diagnostic(errors, 'duplicate_row_id', `duplicate matrix row ${rowId}`, { row_id: rowId });
    seen.add(rowId);
    rowById.set(rowId, row);

    if (!EXECUTION_MODES.has(String(row.execution_mode))) {
      diagnostic(errors, 'invalid_execution_mode', 'row execution_mode is invalid', { row_id: rowId, field: 'execution_mode' });
    }
    if (!BEHAVIOR_CLASSES.has(String(row.accepted_behavior_class))) {
      diagnostic(errors, 'matrix_class_mismatch', 'row accepted_behavior_class is invalid', { row_id: rowId, field: 'accepted_behavior_class' });
    }
    if (row.expected_final_outcome !== row.accepted_behavior_class) {
      diagnostic(errors, 'behavior_class_mismatch', 'row expected_final_outcome must equal accepted behavior class', { row_id: rowId, field: 'expected_final_outcome' });
    }
    if (row.execution_mode === 'safe_non_execution') {
      if (row.attempts !== 0) diagnostic(errors, 'wrong_attempt_count', 'safe_non_execution rows must have attempts: 0', { row_id: rowId, field: 'attempts' });
      const rationale = String(row.safety_rationale ?? '');
      if (rationale.length < 24 || /generic/i.test(rationale)) {
        diagnostic(errors, 'safe_non_execution_unbounded', 'safe_non_execution rows need bounded row-specific rationale', { row_id: rowId, field: 'safety_rationale' });
      }
    } else if (row.attempts !== matrix.attempts_expected) {
      diagnostic(errors, 'wrong_attempt_count', 'executable rows must have attempts equal to matrix attempts_expected', { row_id: rowId, field: 'attempts' });
    }
    if (!String(row.fixture_profile ?? '')) {
      diagnostic(errors, 'invalid_fixture_profile', 'row must name a fixture_profile', { row_id: rowId, field: 'fixture_profile' });
    }
    if (row.surface === 'owner_startup' && !row.owner_sequence) {
      diagnostic(errors, 'missing_owner_sequence', 'owner-startup rows require an owner_sequence', { row_id: rowId, field: 'owner_sequence' });
    }
    if (row.transport === 'mcp-http' && row.http_owner_topology !== 'http_owner_server') {
      diagnostic(errors, 'http_topology_mismatch', 'HTTP MCP rows must use explicit http_owner_server topology', { row_id: rowId, field: 'http_owner_topology' });
    }
  }

  for (const accepted of acceptedRows) {
    const rowId = String(accepted.id);
    const row = rowById.get(rowId);
    if (!row) {
      diagnostic(errors, 'matrix_row_missing', `accepted inventory row ${rowId} is missing from matrix`, { row_id: rowId });
      continue;
    }
    if (row.accepted_behavior_class !== accepted.accepted_behavior_class) {
      diagnostic(errors, 'matrix_class_mismatch', 'matrix behavior class differs from accepted inventory', { row_id: rowId, field: 'accepted_behavior_class' });
    }
    for (const field of REQUIRED_TRUST_FIELDS) {
      if (row[field] !== accepted[field]) {
        diagnostic(errors, 'trust_boundary_drift', `matrix ${field} differs from inventory`, { row_id: rowId, field });
      }
    }
    const gauntletMode = String(asRecord(accepted.gauntlet).mode ?? '');
    if (gauntletMode === 'runnable' && ['fixture_concurrent', 'safe_non_execution'].includes(String(row.execution_mode))) {
      diagnostic(errors, 'execution_mode_downgrade', 'runnable inventory row cannot be downgraded to fixture/non-execution without requirement-impact evidence', {
        row_id: rowId,
        field: 'execution_mode',
      });
    }
  }

  for (const row of rows) {
    if (!acceptedRows.some((accepted) => accepted.id === row.row_id)) {
      diagnostic(errors, 'unknown_matrix_row', `matrix row ${row.row_id} is not in accepted inventory`, { row_id: String(row.row_id) });
    }
  }

  for (const check of requiredSurfaceChecks()) {
    if (!rows.some(check.predicate)) {
      diagnostic(errors, 'missing_required_surface', `matrix is missing required surface group ${check.name}`, { field: check.name });
    }
  }

  return {
    ok: errors.length === 0,
    errors,
    warnings,
    summary: summarizeMatrix(rows),
  };
}

function requiredSurfaceChecks(): Array<{ name: string; predicate: (row: Record<string, any>) => boolean }> {
  return [
    { name: 'sync', predicate: (row) => /(^|:)sync(:|$)/.test(row.row_id) },
    { name: 'embed', predicate: (row) => /(^|:)embed(:|$)/.test(row.row_id) },
    { name: 'extract', predicate: (row) => /extract/.test(row.row_id) },
    { name: 'doctor', predicate: (row) => /(^|:)doctor(:|$)/.test(row.row_id) },
    { name: 'migrations', predicate: (row) => /apply-migrations|upgrade|migrate/.test(row.row_id) },
    { name: 'file_upload', predicate: (row) => /file_upload|files:upload/.test(row.row_id) },
    { name: 'local-cli', predicate: (row) => row.transport === 'local-cli' },
    { name: 'gbrain-call', predicate: (row) => row.transport === 'gbrain-call' },
    { name: 'mcp-stdio', predicate: (row) => row.transport === 'mcp-stdio' },
    { name: 'mcp-http', predicate: (row) => row.transport === 'mcp-http' },
    { name: 'owner-startup', predicate: (row) => row.surface === 'owner_startup' },
  ];
}

function summarizeMatrix(rows: Array<Record<string, any>>): Record<string, unknown> {
  return {
    row_count: rows.length,
    behavior_class_counts: countBy(rows, 'accepted_behavior_class'),
    execution_mode_counts: countBy(rows, 'execution_mode'),
  };
}

function countBy(rows: Array<Record<string, any>>, field: string): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const row of rows) counts[String(row[field])] = (counts[String(row[field])] ?? 0) + 1;
  return counts;
}

export function classifyAllAccessResult(input: Record<string, any>): Record<string, any> {
  const structured = input.structured_error ? JSON.stringify(input.structured_error) : '';
  const text = [
    input.full_stdout,
    input.full_stderr,
    input.stdout_tail,
    input.stderr_tail,
    structured,
    input.process_error,
    input.timeout_error,
  ].filter((part) => typeof part === 'string').join('\n');

  if (RAW_TIMEOUT_RE.test(text)) {
    return { kind: 'raw_pglite_lock_timeout', raw_lock_timeout_observed: true };
  }
  if (input.timed_out === true) {
    return { kind: 'harness_timeout', raw_lock_timeout_observed: false };
  }
  const typed = [
    'maintenance_deferred',
    'owner_unreachable',
    'owner_starting',
    'broker_timeout',
    'completion_unknown',
    'lock_safety_blocked',
    'invalid_params',
    'permission_denied',
    'local_only_remote_rejected',
    'live_owner_command_guard',
    'duplicate_owner_start_blocked',
  ].find((code) => text.includes(code));
  if (typed) return { kind: 'typed_guard_fail_fast', raw_lock_timeout_observed: false, typed_error_code: typed };
  if (String(input.stderr_tail ?? input.full_stderr ?? '').trim()) {
    if (/PGLite owner broker recovered stale operation socket/i.test(String(input.stderr_tail ?? input.full_stderr ?? ''))) {
      return { kind: 'owner_broker_diagnostic', raw_lock_timeout_observed: false };
    }
    return { kind: 'unclassified_output', raw_lock_timeout_observed: false };
  }
  return { kind: 'classified_product_outcome', raw_lock_timeout_observed: false };
}

export function validateAllAccessResultsObject(input: unknown): ValidationResult {
  const doc = asRecord(input);
  const matrix = asRecord(doc.matrix);
  const rows = asRows(matrix.rows);
  const results = asRows(doc.results);
  const safeRows = asRows(doc.safe_non_execution);
  const manifest = asRecord(doc.manifest);
  const runId = String(doc.run_id ?? manifest.run_id ?? '');
  const errors: Diagnostic[] = [];
  const warnings: Diagnostic[] = [];

  if (!runId) diagnostic(errors, 'stale_or_mixed_artifact', 'result bundle must name run_id', { field: 'run_id' });
  if (!manifest.run_id) diagnostic(errors, 'stale_or_mixed_artifact', 'result validation requires a run manifest', { field: 'manifest.run_id' });
  if (manifest.run_id && manifest.run_id !== runId) {
    diagnostic(errors, 'stale_or_mixed_artifact', 'manifest run_id differs from result bundle run_id', { field: 'manifest.run_id' });
  }
  const expectedMatrixSha = matrixIdentitySha256(matrix);
  if (manifest.matrix_sha256 !== expectedMatrixSha) {
    diagnostic(errors, 'stale_or_mixed_artifact', 'manifest matrix hash differs from supplied matrix', { field: 'manifest.matrix_sha256' });
  }
  const expectedResultsSha = resultsIdentitySha256(results);
  if (asRecord(manifest.artifact_hashes).results_sha256 !== expectedResultsSha) {
    diagnostic(errors, 'stale_or_mixed_artifact', 'manifest results hash differs from supplied results', { field: 'manifest.artifact_hashes.results_sha256' });
  }
  if (manifest.inventory_sha256 && manifest.inventory_sha256 !== matrix.inventory_sha256) {
    diagnostic(errors, 'stale_or_mixed_artifact', 'manifest inventory hash differs from matrix inventory hash', { field: 'manifest.inventory_sha256' });
  }
  if (manifest.status && manifest.status !== 'pass') {
    diagnostic(errors, 'harness_setup_failure', 'manifest status is not pass', { field: 'manifest.status' });
  }
  if (manifest.cleanup_status && manifest.cleanup_status !== 'clean') {
    diagnostic(errors, 'cleanup_failed', 'manifest cleanup status is not clean', { field: 'manifest.cleanup_status' });
  }
  if (asRecord(manifest.owner_session).status === 'lost') {
    diagnostic(errors, 'owner_lost', 'manifest owner session was lost', { field: 'manifest.owner_session.status' });
  }

  const resultGroups = new Map<string, Record<string, any>[]>();
  for (const result of results) {
    const rowId = String(result.row_id ?? '');
    const attempt = Number(result.attempt);
    const row = rows.find((candidate) => candidate.row_id === rowId);
    if (!row) {
      diagnostic(errors, 'unknown_result_row', `result row ${rowId} is not in matrix`, { row_id: rowId });
      continue;
    }
    if (result.run_id !== runId) {
      diagnostic(errors, 'stale_or_mixed_artifact', 'result run_id differs from bundle run_id', { row_id: rowId, field: 'run_id' });
    }
    if (result.execution_mode !== row.execution_mode) {
      diagnostic(errors, 'invalid_execution_mode', 'result execution_mode differs from matrix', { row_id: rowId, field: 'execution_mode' });
    }
    if (result.command !== row.command_or_operation) {
      diagnostic(errors, 'row_command_mismatch', 'result command differs from matrix command', { row_id: rowId, field: 'command' });
    }
    if (result.pass !== true || result.failure_reason != null || result.failure_category != null) {
      diagnostic(errors, 'result_marked_failed', 'result carries explicit failure state', { row_id: rowId, field: 'pass' });
    }
    const classification = classifyAllAccessResult(result);
    if (classification.raw_lock_timeout_observed || result.raw_lock_timeout_observed === true) {
      diagnostic(errors, 'raw_timeout_observed', 'raw PGLite lock/connect timeout observed in full captured result stream', { row_id: rowId });
    }
    if (classification.kind === 'unclassified_output') {
      diagnostic(errors, 'unclassified_output', 'result contains unclassified stderr or product-boundary text', { row_id: rowId });
    }
    if (result.final_outcome !== row.accepted_behavior_class) {
      diagnostic(errors, 'behavior_class_mismatch', 'result final_outcome differs from accepted behavior class', { row_id: rowId, field: 'final_outcome' });
    }
    if (row.accepted_behavior_class === 'typed_guard_fail_fast') {
      const typedCode = classification.typed_error_code ?? asRecord(result.structured_error).code;
      if (result.exit_code === 0 || !typedCode) {
        diagnostic(errors, 'typed_guard_shape_mismatch', 'typed_guard_fail_fast rows require nonzero exit and typed error evidence', {
          row_id: rowId,
          field: 'structured_error',
        });
      }
    } else if (result.exit_code !== 0) {
      diagnostic(errors, 'behavior_class_mismatch', 'non-typed rows require successful exit shape', { row_id: rowId, field: 'exit_code' });
    }
    if ((row.execution_mode === 'live_concurrent' || row.execution_mode === 'typed_guard_concurrent')) {
      const route = asRecord(result.route_evidence);
      if (route.kind !== 'gbrain_serve_owner' || route.live_owner_process !== true) {
        diagnostic(errors, 'owner_route_evidence_missing', 'live/typed concurrent rows require gbrain serve owner route evidence', {
          row_id: rowId,
          field: 'route_evidence',
        });
      }
    }
    if (row.execution_mode === 'fixture_concurrent') {
      const fixture = asRecord(result.fixture_evidence);
      const policyProbe = asRecord(fixture.policy_probe);
      const dispatchProbe = asRecord(fixture.dispatch_probe);
      const observedRequest = asRecord(fixture.observed_request);
      const observedOutput = asRecord(fixture.observed_output_shape);
      if (
        fixture.kind !== 'controlled_dispatch_fixture' ||
        fixture.controlled_dispatch !== true ||
        fixture.controlled_dispatch_source !== CONTROLLED_DISPATCH_SOURCE ||
        fixture.policy_behavior_class !== row.accepted_behavior_class
      ) {
        diagnostic(errors, 'fixture_evidence_missing', 'fixture_concurrent rows require row-specific controlled dispatch fixture evidence', {
          row_id: rowId,
          field: 'fixture_evidence',
        });
      }
      if (
        policyProbe.invoked !== true ||
        policyProbe.source !== 'src/core/pglite-owner-policy.ts:resolvePgliteOwnerPolicy' ||
        policyProbe.behavior_class !== row.accepted_behavior_class ||
        policyProbe.local_only !== row.local_only ||
        policyProbe.requires_owner_serialization !== (row.accepted_behavior_class === 'serialized_owner_mutation')
      ) {
        diagnostic(errors, 'fixture_evidence_missing', 'fixture evidence must include independent owner-policy probe output', {
          row_id: rowId,
          field: 'fixture_evidence.policy_probe',
        });
      }
      if (
        dispatchProbe.invoked !== true ||
        dispatchProbe.source !== CONTROLLED_DISPATCH_SOURCE ||
        dispatchProbe.input_policy_behavior_class !== policyProbe.behavior_class ||
        dispatchProbe.output_behavior_class !== row.accepted_behavior_class ||
        !SHA256_RE.test(String(dispatchProbe.request_sha256 ?? '')) ||
        !SHA256_RE.test(String(dispatchProbe.output_sha256 ?? ''))
      ) {
        diagnostic(errors, 'fixture_evidence_missing', 'fixture evidence must include controlled dispatch/output provenance', {
          row_id: rowId,
          field: 'fixture_evidence.dispatch_probe',
        });
      }
      if (
        dispatchProbe.request_sha256 !== sha256(JSON.stringify(observedRequest)) ||
        dispatchProbe.output_sha256 !== sha256(JSON.stringify(observedOutput))
      ) {
        diagnostic(errors, 'fixture_dispatch_hash_mismatch', 'fixture dispatch hashes must match observed request and output shape', {
          row_id: rowId,
          field: 'fixture_evidence.dispatch_probe',
        });
      }
      if (
        observedRequest.source !== CONTROLLED_DISPATCH_SOURCE ||
        observedRequest.transport !== row.transport ||
        observedRequest.operation_context_remote !== row.operation_context_remote ||
        !observedRequest.caller ||
        observedRequest.surface_id !== row.row_id
      ) {
        diagnostic(errors, 'trust_boundary_evidence_mismatch', 'fixture observed request must preserve caller transport and remote flag', {
          row_id: rowId,
          field: 'fixture_evidence.observed_request',
        });
      }
      if (
        observedOutput.source !== CONTROLLED_DISPATCH_SOURCE ||
        observedOutput.final_outcome !== row.accepted_behavior_class ||
        typeof observedOutput.exit_code !== 'number' ||
        observedOutput.final_outcome !== dispatchProbe.output_behavior_class ||
        (row.accepted_behavior_class === 'typed_guard_fail_fast' && !observedOutput.structured_error_code)
      ) {
        diagnostic(errors, 'fixture_evidence_missing', 'fixture observed output shape must support the accepted behavior class', {
          row_id: rowId,
          field: 'fixture_evidence.observed_output_shape',
        });
      }
      if (
        fixture.transport_exercised !== row.transport ||
        fixture.operation_context_remote !== row.operation_context_remote ||
        fixture.trust_boundary_checked !== true
      ) {
        diagnostic(errors, 'trust_boundary_evidence_mismatch', 'fixture evidence must preserve transport and remote trust-boundary fields', {
          row_id: rowId,
          field: 'fixture_evidence',
        });
      }
      if (row.transport === 'mcp-http' && fixture.http_owner_topology !== 'http_owner_server') {
        diagnostic(errors, 'http_topology_mismatch', 'HTTP fixture evidence must record http_owner_server topology', {
          row_id: rowId,
          field: 'fixture_evidence.http_owner_topology',
        });
      }
    }
    if (result.owner_status === 'lost') {
      diagnostic(errors, 'owner_lost', 'owner was lost during result attempt', { row_id: rowId, field: 'owner_status' });
    }
    if (result.cleanup_status !== 'clean') {
      diagnostic(errors, 'cleanup_failed', 'result cleanup_status is not clean', { row_id: rowId, field: 'cleanup_status' });
    }
    for (const field of ['exit_code', 'timed_out', 'stdout_tail', 'stderr_tail', 'stdout_sha256', 'stderr_sha256', 'full_stream_classification_sha256', 'structured_error', 'full_stdout', 'full_stderr']) {
      if (!(field in result)) diagnostic(errors, 'missing_result_field', `result is missing ${field}`, { row_id: rowId, field });
    }
    if (!resultGroups.has(rowId)) resultGroups.set(rowId, []);
    resultGroups.get(rowId)!.push(result);
  }

  for (const row of rows) {
    if (row.execution_mode === 'safe_non_execution') {
      const safe = safeRows.find((candidate) => candidate.row_id === row.row_id);
      if (!safe) {
        diagnostic(errors, 'safe_non_execution_unbounded', 'safe_non_execution row has no result rationale entry', { row_id: row.row_id });
        continue;
      }
      if (safe.run_id !== runId || safe.final_outcome !== row.accepted_behavior_class) {
        diagnostic(errors, 'behavior_class_mismatch', 'safe_non_execution entry does not preserve run id/final outcome', { row_id: row.row_id });
      }
      if (!String(safe.safety_rationale ?? '') || !Array.isArray(safe.evidence_source_refs) || safe.evidence_source_refs.length === 0) {
        diagnostic(errors, 'safe_non_execution_unbounded', 'safe_non_execution entry lacks rationale or evidence refs', { row_id: row.row_id });
      }
      continue;
    }
    const attempts = resultGroups.get(row.row_id) ?? [];
    const expectedAttempts = new Set([1, 2, 3]);
    const observed = new Set(attempts.map((attemptResult) => Number(attemptResult.attempt)).filter((attempt) => Number.isInteger(attempt)));
    const missing = Array.from(expectedAttempts).filter((attempt) => !observed.has(attempt));
    const invalidAttempts = attempts.filter((attemptResult) => !expectedAttempts.has(Number(attemptResult.attempt)));
    if (attempts.length !== 3 || observed.size !== 3 || missing.length > 0 || invalidAttempts.length > 0) {
      diagnostic(errors, 'wrong_attempt_count', `row ${row.row_id} must have exactly attempts 1,2,3`, { row_id: row.row_id });
    }
  }

  const rawTimeoutCount = errors.filter((error) => error.code === 'raw_timeout_observed').length;
  const executableRows = rows.filter((row) => row.execution_mode !== 'safe_non_execution');
  const safeNonExecutionRows = rows.filter((row) => row.execution_mode === 'safe_non_execution');
  return {
    ok: errors.length === 0,
    errors,
    warnings,
    summary: {
      executable_row_count: executableRows.length,
      safe_non_execution_row_count: safeNonExecutionRows.length,
      result_count: results.length,
      raw_timeout_count: rawTimeoutCount,
      failed_row_ids: Array.from(new Set(errors.map((error) => error.row_id).filter(Boolean))),
    },
  };
}

function loadYaml(path: string): unknown {
  return yaml.load(readFileSync(path, 'utf8'));
}

function loadJsonl(path: string): Array<unknown> {
  return readFileSync(path, 'utf8')
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line));
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
      'Usage: bun run scripts/validate-pglite-all-access-matrix.ts --matrix <matrix.yml> [--inventory <inventory.yml>] [--results <results.jsonl> --manifest <manifest.json>] [--json]',
      '',
      'Validates the requirement 008 matrix and, when provided, its result bundle.',
      '',
    ].join('\n'));
    process.exit(0);
  }
  const repoRoot = process.cwd();
  const matrixPath = typeof args.matrix === 'string' ? resolve(args.matrix) : '';
  const inventoryPath = typeof args.inventory === 'string'
    ? resolve(args.inventory)
    : resolve('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml');
  if (!existsSync(inventoryPath)) {
    const output = {
      ok: false,
      errors: [{
        code: 'missing_inventory',
        message: '--inventory must point to an existing inventory YAML file',
        path: inventoryPath,
      }],
      warnings: [],
    };
    process.stdout.write(`${JSON.stringify(output, null, args.json ? 2 : 0)}\n`);
    process.exit(1);
  }
  if (!matrixPath || !existsSync(matrixPath)) {
    const output = { ok: false, errors: [{ code: 'missing_matrix', message: '--matrix must point to an existing matrix YAML file' }], warnings: [] };
    process.stdout.write(`${JSON.stringify(output, null, args.json ? 2 : 0)}\n`);
    process.exit(1);
  }

  const inventory = loadYaml(inventoryPath);
  const matrix = loadYaml(matrixPath);
  const matrixValidation = validateAllAccessMatrixObject(matrix, { inventory, repoRoot });
  let resultValidation: ValidationResult | null = null;
  if (typeof args.results === 'string') {
    const resultsPath = resolve(args.results);
    const manifestPath = typeof args.manifest === 'string' ? resolve(args.manifest) : '';
    const safeRows = asRows(asRecord(matrix).rows)
      .filter((row) => row.execution_mode === 'safe_non_execution')
      .map((row) => ({
        row_id: row.row_id,
        execution_mode: row.execution_mode,
        final_outcome: row.accepted_behavior_class,
        safety_rationale: row.safety_rationale,
        evidence_source_refs: row.evidence_source_refs,
        run_id: typeof args.run_id === 'string' ? args.run_id : asRecord(loadJsonMaybe(manifestPath)).run_id,
      }));
    const manifest = manifestPath ? loadJsonMaybe(manifestPath) : {};
    resultValidation = validateAllAccessResultsObject({
      run_id: typeof args.run_id === 'string' ? args.run_id : asRecord(manifest).run_id,
      matrix,
      results: loadJsonl(resultsPath),
      safe_non_execution: safeRows,
      manifest,
    });
  }
  const ok = matrixValidation.ok && (!resultValidation || resultValidation.ok);
  const output = {
    ok,
    matrix: matrixValidation,
    ...(resultValidation ? { results: resultValidation } : {}),
  };
  const json = JSON.stringify(output, null, args.json ? 2 : 0);
  if (typeof args.out === 'string') writeFileSync(resolve(args.out), `${json}\n`);
  process.stdout.write(`${json}\n`);
  process.exit(ok ? 0 : 1);
}

function loadJsonMaybe(path: string): unknown {
  if (!path || !existsSync(path)) return {};
  return JSON.parse(readFileSync(path, 'utf8'));
}
