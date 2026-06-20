#!/usr/bin/env bun

import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import yaml from 'js-yaml';
import ts from 'typescript';

type Diagnostic = {
  code: string;
  message: string;
  row_id?: string;
  field?: string;
  source?: string;
};

type ValidationResult = {
  ok: boolean;
  errors: Diagnostic[];
  warnings: Diagnostic[];
};

type Candidate = {
  id: string;
  source: string;
  scope?: string;
  mutating?: boolean;
  localOnly?: boolean;
  stdioAdvertised?: boolean;
};

type ValidationOptions = {
  repoRoot?: string;
  candidates?: Candidate[];
  allowSyntheticFingerprints?: boolean;
};

type GauntletValidationOptions = {
  inventory?: unknown;
};

const BEHAVIOR_CLASSES = new Set([
  'broker_success_read',
  'serialized_owner_mutation',
  'typed_guard_fail_fast',
  'existing_direct_when_no_owner',
  'out_of_scope_with_user_approval',
]);

const ENTRY_KINDS = new Set(['operation', 'cli_command', 'mcp_transport', 'owner_startup']);
const CALLER_SURFACES = new Set(['cli', 'mcp', 'owner', 'test_harness']);
const TRANSPORTS = new Set(['local-cli', 'gbrain-call', 'mcp-stdio', 'mcp-http', 'owner-stdio', 'owner-http']);
const GAUNTLET_MODES = new Set(['runnable', 'dry_run', 'fixture_only', 'safe_non_execution', 'not_applicable']);
const SCOPES = new Set(['read', 'write', 'admin', 'sources_admin', 'agent', 'none']);
const SAFE_NON_EXECUTION_RISK_TYPES = new Set([
  'filesystem_mutation',
  'schema_or_migration',
  'destructive_data_mutation',
  'remote_authority_sensitive',
  'maintenance_or_background_job',
  'irreversible_brain_reinit',
]);

const TYPED_ERROR_CODES = [
  'maintenance_deferred',
  'owner_unreachable',
  'owner_starting',
  'broker_timeout',
  'completion_unknown',
  'lock_safety_blocked',
  'invalid_params',
  'permission_denied',
];

const REQUIRED_ROW_FIELDS = [
  'id',
  'command_or_operation',
  'subcommand_or_mode',
  'argument_profile',
  'entry_kind',
  'caller_surface',
  'transport',
  'implementation_entrypoint',
  'database_open_site',
  'current_owner_behavior',
  'no_owner_baseline',
  'accepted_behavior_class',
  'scope',
  'local_only',
  'mcp_exposed',
  'operation_context_remote',
  'filesystem_confinement',
  'side_effects',
  'data_preconditions',
  'gauntlet',
  'evidence_refs',
];

function result(errors: Diagnostic[], warnings: Diagnostic[] = []): ValidationResult {
  return { ok: errors.length === 0, errors, warnings };
}

function push(errors: Diagnostic[], code: string, message: string, extra: Omit<Diagnostic, 'code' | 'message'> = {}): void {
  errors.push({ code, message, ...extra });
}

function asRecord(value: unknown): Record<string, any> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, any> : {};
}

function asRows(value: unknown): Array<Record<string, any>> {
  return Array.isArray(value) ? value.filter((row): row is Record<string, any> => !!row && typeof row === 'object' && !Array.isArray(row)) : [];
}

export function validateInventoryObject(input: unknown, options: ValidationOptions = {}): ValidationResult {
  const doc = asRecord(input);
  const errors: Diagnostic[] = [];
  const warnings: Diagnostic[] = [];

  if (doc.requirement_id !== '006-pglite-access-path-inventory') {
    push(errors, 'invalid_requirement_id', 'requirement_id must be 006-pglite-access-path-inventory', { field: 'requirement_id' });
  }
  if (doc.schema_version !== 1) {
    push(errors, 'invalid_schema_version', 'schema_version must be 1', { field: 'schema_version' });
  }
  if (!Array.isArray(doc.generated_from) || doc.generated_from.length === 0) {
    push(errors, 'missing_generated_from', 'generated_from must name source inputs', { field: 'generated_from' });
  }

  const later = asRecord(doc.later_sequence_standard);
  if (later.attempts !== 3 || later.raw_lock_timeout_allowed !== false) {
    push(errors, 'invalid_later_standard', 'later_sequence_standard must require 3 attempts and disallow raw lock timeout', {
      field: 'later_sequence_standard',
    });
  }

  const rows = asRows(doc.rows);
  if (rows.length === 0) {
    push(errors, 'missing_rows', 'rows must contain at least one inventory row', { field: 'rows' });
  }

  const rowIds = new Set<string>();
  for (const row of rows) {
    const id = typeof row.id === 'string' ? row.id : '<missing-id>';
    if (rowIds.has(id)) {
      push(errors, 'duplicate_row_id', `duplicate row id: ${id}`, { row_id: id });
    }
    rowIds.add(id);

    for (const field of REQUIRED_ROW_FIELDS) {
      if (!(field in row)) push(errors, 'missing_field', `row ${id} is missing ${field}`, { row_id: id, field });
    }

    checkEnum(errors, row, 'entry_kind', ENTRY_KINDS, id);
    checkEnum(errors, row, 'caller_surface', CALLER_SURFACES, id);
    checkEnum(errors, row, 'transport', TRANSPORTS, id);
    checkEnum(errors, row, 'accepted_behavior_class', BEHAVIOR_CLASSES, id);
    checkEnum(errors, row, 'scope', SCOPES, id);

    if (typeof row.local_only !== 'boolean') push(errors, 'invalid_boolean', 'local_only must be boolean', { row_id: id, field: 'local_only' });
    if (typeof row.mcp_exposed !== 'boolean') push(errors, 'invalid_boolean', 'mcp_exposed must be boolean', { row_id: id, field: 'mcp_exposed' });
    if (typeof row.operation_context_remote !== 'boolean') {
      push(errors, 'invalid_boolean', 'operation_context_remote must be boolean', { row_id: id, field: 'operation_context_remote' });
    }
    if (!Array.isArray(row.side_effects) || row.side_effects.length === 0) {
      push(errors, 'missing_side_effects', 'side_effects must be a non-empty array', { row_id: id, field: 'side_effects' });
    }
    if (!Array.isArray(row.evidence_refs) || row.evidence_refs.length === 0) {
      push(errors, 'missing_evidence_refs', 'evidence_refs must be a non-empty array', { row_id: id, field: 'evidence_refs' });
    }
    if (!Array.isArray(row.data_preconditions) || row.data_preconditions.length === 0) {
      push(errors, 'missing_data_preconditions', 'data_preconditions must be a non-empty array', { row_id: id, field: 'data_preconditions' });
    }

    const gauntlet = asRecord(row.gauntlet);
    checkEnum(errors, gauntlet, 'mode', GAUNTLET_MODES, id);
    if (gauntlet.mode === 'runnable' && gauntlet.attempts !== 3) {
      push(errors, 'invalid_attempt_count', 'runnable gauntlet rows must use attempts: 3', { row_id: id, field: 'gauntlet.attempts' });
    }
    if (gauntlet.mode === 'safe_non_execution') {
      const reason = String(gauntlet.safe_non_execution_reason ?? '');
      if (!reason) {
        push(errors, 'missing_safe_non_execution_reason', 'safe_non_execution rows need a concrete reason', { row_id: id });
      }
      if (reason === 'destructive_or_remote_authority_sensitive_path' || reason.length < 24) {
        push(errors, 'unbounded_safe_non_execution', 'safe_non_execution rows need a row-specific bounded reason', { row_id: id });
      }
      if (!SAFE_NON_EXECUTION_RISK_TYPES.has(String(gauntlet.safe_non_execution_risk_type))) {
        push(errors, 'unbounded_safe_non_execution', 'safe_non_execution rows need a recognized risk type', {
          row_id: id,
          field: 'gauntlet.safe_non_execution_risk_type',
        });
      }
      if (!String(gauntlet.safe_non_execution_source_ref ?? '').includes(':')) {
        push(errors, 'unbounded_safe_non_execution', 'safe_non_execution rows need a source reference for the risk decision', {
          row_id: id,
          field: 'gauntlet.safe_non_execution_source_ref',
        });
      }
      if (!gauntlet.future_required_outcome) {
        push(errors, 'missing_future_required_outcome', 'safe_non_execution rows need a future replacement expectation', { row_id: id });
      }
    }
    if (gauntlet.mode === 'runnable' && (!gauntlet.current_expected_outcome || !gauntlet.future_required_outcome)) {
      push(errors, 'missing_expected_outcome', 'runnable rows require current_expected_outcome and future_required_outcome', { row_id: id });
    }

    if (row.accepted_behavior_class === 'out_of_scope_with_user_approval' && !row.user_approval_decision_ref) {
      push(errors, 'missing_out_of_scope_approval', 'out_of_scope_with_user_approval requires a decision ref', { row_id: id });
    }

    if (row.command_or_operation && !row.subcommand_or_mode) {
      push(errors, 'coarse_command_row', 'rows must name subcommand_or_mode for mode-sensitive coverage', { row_id: id });
    }

    if (row.accepted_behavior_class !== 'existing_direct_when_no_owner' && !String(row.current_owner_behavior ?? '').trim()) {
      push(errors, 'missing_live_owner_evidence', 'non-no-owner rows must record current live-owner behavior', { row_id: id });
    }
  }

  const requiredSurfaceIds = Array.isArray(doc.required_surface_ids) ? doc.required_surface_ids : [];
  for (const required of requiredSurfaceIds) {
    if (!rowIds.has(required)) {
      push(errors, 'missing_required_surface', `required surface ${required} is missing`, { row_id: String(required) });
    }
  }

  const candidates = options.candidates ?? discoverInventoryCandidates(options.repoRoot ?? process.cwd());
  for (const candidate of candidates) {
    const row = rows.find((candidateRow) => candidateRow.id === candidate.id);
    if (!row) {
      push(errors, 'missing_candidate_row', `source-derived candidate ${candidate.id} is missing`, {
        row_id: candidate.id,
        source: candidate.source,
      });
      continue;
    }
    if (candidate.scope && row.scope !== candidate.scope) {
      push(errors, 'candidate_metadata_mismatch', `row scope ${row.scope} does not match source scope ${candidate.scope}`, {
        row_id: candidate.id,
        field: 'scope',
        source: candidate.source,
      });
    }
    if (candidate.localOnly !== undefined && row.local_only !== candidate.localOnly) {
      push(errors, 'candidate_metadata_mismatch', `row local_only ${row.local_only} does not match source localOnly ${candidate.localOnly}`, {
        row_id: candidate.id,
        field: 'local_only',
        source: candidate.source,
      });
    }
    if (candidate.stdioAdvertised && row.mcp_exposed !== true) {
      push(errors, 'candidate_metadata_mismatch', 'stdio MCP rows are advertised by tools/list and must record mcp_exposed: true', {
        row_id: candidate.id,
        field: 'mcp_exposed',
        source: candidate.source,
      });
    }
    if (candidate.mutating === true) {
      if (row.accepted_behavior_class === 'broker_success_read' || row.scope === 'read' || Array.isArray(row.side_effects) && row.side_effects.includes('none')) {
        push(errors, 'candidate_metadata_mismatch', 'mutating operation row cannot be classified as read/no-side-effect', {
          row_id: candidate.id,
          field: 'accepted_behavior_class',
          source: candidate.source,
        });
      }
    }
    const expectedCommand = expectedCommandForCandidate(candidate.id);
    if (expectedCommand && row.command_or_operation !== expectedCommand) {
      push(errors, 'candidate_metadata_mismatch', `row command_or_operation ${row.command_or_operation} does not match ${expectedCommand}`, {
        row_id: candidate.id,
        field: 'command_or_operation',
        source: candidate.source,
      });
    }
    if (row.database_open_site !== expectedOpenSiteForCandidate(candidate)) {
      push(errors, 'candidate_metadata_mismatch', 'row database_open_site does not match derived PGLite open site', {
        row_id: candidate.id,
        field: 'database_open_site',
        source: candidate.source,
      });
    }
  }

  if (!options.allowSyntheticFingerprints) {
    const fingerprints = asRecord(doc.source_fingerprints);
    for (const source of ['src/core/operations.ts', 'src/cli.ts', 'src/mcp/server.ts', 'src/commands/serve-http.ts']) {
      if (!fingerprints[source]) {
        push(errors, 'missing_source_fingerprint', `missing source fingerprint for ${source}`, { source });
      } else {
        try {
          const actual = sourceFingerprint(options.repoRoot ?? process.cwd(), source);
          if (fingerprints[source] !== actual) {
            push(errors, 'stale_source_fingerprint', `source fingerprint for ${source} does not match current source`, { source });
          }
        } catch (err) {
          push(errors, 'source_fingerprint_unavailable', err instanceof Error ? err.message : String(err), { source });
        }
      }
    }
  }

  return result(errors, warnings);
}

function checkEnum(errors: Diagnostic[], row: Record<string, any>, field: string, allowed: Set<string>, rowId: string): void {
  if (!allowed.has(String(row[field]))) {
    push(errors, 'invalid_enum', `${field} must be one of ${Array.from(allowed).join(', ')}`, { row_id: rowId, field });
  }
}

export function classifyPgliteAccessOutput(input: {
  stdout?: string;
  stderr?: string;
  timed_out?: boolean;
}): { kind: string; raw_timeout_detected: boolean; typed_error_code?: string } {
  if (input.timed_out) return { kind: 'harness_timeout', raw_timeout_detected: false };
  const text = `${input.stdout ?? ''}\n${input.stderr ?? ''}`;
  if (/Timed out waiting for PGLite lock|Could not acquire PGLite lock/i.test(text)) {
    return { kind: 'raw_pglite_lock_timeout', raw_timeout_detected: true };
  }
  const typed = TYPED_ERROR_CODES.find((code) => text.includes(code));
  if (typed) return { kind: 'typed_owner_or_guard_error', raw_timeout_detected: false, typed_error_code: typed };
  return { kind: 'other', raw_timeout_detected: false };
}

export function validateGauntletManifestObject(input: unknown, options: GauntletValidationOptions = {}): ValidationResult {
  const manifest = asRecord(input);
  const errors: Diagnostic[] = [];
  const rowIds = Array.isArray(manifest.inventory_row_ids) ? manifest.inventory_row_ids.map(String) : [];
  const expected = Number(manifest.attempts_expected);
  const results = asRows(manifest.results);
  const safeRows = asRows(manifest.safe_non_execution);
  const harness = asRecord(manifest.harness);
  const rowCommands = asRecord(manifest.row_commands);
  const inventoryRows = asRows(asRecord(options.inventory).rows);
  const inventoryRowById = new Map(inventoryRows.map((row) => [String(row.id), row]));
  const expectedRunnableRows = inventoryRows
    .filter((row) => asRecord(row.gauntlet).mode === 'runnable')
    .map((row) => String(row.id));
  const expectedSafeRows = inventoryRows
    .filter((row) => asRecord(row.gauntlet).mode === 'safe_non_execution')
    .map((row) => String(row.id));

  if (rowIds.length === 0) push(errors, 'missing_manifest_rows', 'manifest must name inventory_row_ids');
  if (!Number.isInteger(expected) || expected <= 0) push(errors, 'invalid_attempts_expected', 'attempts_expected must be a positive integer');
  for (const field of ['owner_pid', 'lock_observed', 'broker_ready', 'backend_confirmed', 'harness_phase', 'teardown_status', 'cleanup_required']) {
    if (!(field in harness)) push(errors, 'missing_harness_field', `manifest harness is missing ${field}`, { field: `harness.${field}` });
  }

  const grouped = new Map<string, Set<number>>();
  for (const entry of results) {
    const rowId = String(entry.row_id ?? '');
    const attempt = Number(entry.attempt);
    const inventoryRow = inventoryRowById.get(rowId);
    if (!rowIds.includes(rowId)) push(errors, 'unknown_manifest_row', `manifest result row ${rowId} is not in inventory_row_ids`, { row_id: rowId });
    if (inventoryRows.length > 0 && !inventoryRow) {
      push(errors, 'unknown_manifest_row', `manifest result row ${rowId} is not in inventory rows`, { row_id: rowId });
    }
    if (inventoryRow && asRecord(inventoryRow.gauntlet).mode !== 'runnable') {
      push(errors, 'manifest_mode_mismatch', `manifest result row ${rowId} is not runnable in inventory`, { row_id: rowId });
    }
    if (!Number.isInteger(attempt) || attempt <= 0) push(errors, 'invalid_manifest_attempt', 'manifest attempt must be positive integer', { row_id: rowId });
    const expectedCommand = rowCommands[rowId] ?? inventoryRow?.command_or_operation;
    if (expectedCommand && entry.command !== expectedCommand) {
      push(errors, 'row_command_mismatch', `row ${rowId} command ${entry.command} does not match ${expectedCommand}`, { row_id: rowId });
    }
    for (const field of ['exit_code', 'timed_out', 'stdout', 'stderr', 'execution_classification', 'raw_timeout_detected']) {
      if (!(field in entry)) {
        push(errors, 'missing_manifest_result_field', `manifest result row ${rowId} is missing ${field}`, { row_id: rowId, field });
      }
    }
    const observed = classifyPgliteAccessOutput({
      stdout: typeof entry.stdout === 'string' ? entry.stdout : '',
      stderr: typeof entry.stderr === 'string' ? entry.stderr : '',
      timed_out: entry.timed_out === true,
    });
    if (entry.execution_classification !== observed.kind || entry.raw_timeout_detected !== observed.raw_timeout_detected) {
      push(errors, 'manifest_classification_mismatch', 'manifest classification must match captured stdout/stderr/timed_out', { row_id: rowId });
    }
    if ((entry.typed_error_code ?? null) !== (observed.typed_error_code ?? null)) {
      push(errors, 'manifest_classification_mismatch', 'manifest typed_error_code must match captured stdout/stderr/timed_out', { row_id: rowId });
    }
    if (inventoryRow) validateExpectedManifestOutcome(errors, inventoryRow, entry, rowId);
    if (!grouped.has(rowId)) grouped.set(rowId, new Set());
    grouped.get(rowId)!.add(attempt);
  }

  for (const rowId of rowIds) {
    const attempts = grouped.get(rowId)?.size ?? 0;
    const safe = safeRows.find((row) => row.row_id === rowId);
    const inventoryRow = inventoryRowById.get(rowId);
    if (inventoryRows.length > 0 && !inventoryRow) {
      push(errors, 'unknown_manifest_row', `manifest row ${rowId} is not in inventory rows`, { row_id: rowId });
      continue;
    }
    if (safe) {
      if (inventoryRow && asRecord(inventoryRow.gauntlet).mode !== 'safe_non_execution') {
        push(errors, 'manifest_mode_mismatch', `safe non-execution row ${rowId} is not safe_non_execution in inventory`, { row_id: rowId });
      }
      if (!safe.reason || !safe.future_required_outcome) {
        push(errors, 'incomplete_safe_non_execution', 'safe non-execution rows need reason and future_required_outcome', { row_id: rowId });
      }
      continue;
    }
    if (attempts !== expected) {
      push(errors, 'wrong_attempt_count', `row ${rowId} has ${attempts} attempts; expected ${expected}`, { row_id: rowId });
    }
  }

  for (const rowId of expectedRunnableRows) {
    if (!rowIds.includes(rowId)) {
      push(errors, 'missing_runnable_manifest_row', `runnable inventory row ${rowId} is missing from manifest`, { row_id: rowId });
    }
  }
  for (const rowId of expectedSafeRows) {
    if (!rowIds.includes(rowId)) {
      push(errors, 'missing_safe_non_execution', `safe_non_execution inventory row ${rowId} is missing from manifest`, { row_id: rowId });
    }
  }

  return result(errors);
}

function expectedCommandForCandidate(id: string): string | undefined {
  if (id.startsWith('cli:')) {
    const [, command, mode] = id.split(':');
    if (!command || !mode) return undefined;
    if (command === 'doctor' && mode === 'default') return 'gbrain doctor';
    if (command === 'doctor' && ['fast', 'fix', 'locks', 'remediation-plan', 'remediate'].includes(mode)) return `gbrain doctor --${mode}`;
    if (command === 'search' && mode === 'modes-reset') return 'gbrain search modes --reset';
    if (command === 'search' && mode === 'tune-apply') return 'gbrain search tune --apply';
    if (['operation-cli', 'pglite-surface', 'maintenance', 'module-open-site'].includes(mode)) return `gbrain ${command}`;
    return `gbrain ${command} ${mode}`;
  }
  if (id.startsWith('call:')) return `gbrain call ${id.split(':')[1]}`;
  if (id.startsWith('serve:')) return `gbrain serve ${id.split(':').slice(1).join(':')}`;
  if (id.startsWith('mcp-')) return id.split(':')[1];
  return undefined;
}

function expectedOpenSiteForCandidate(candidate: Candidate): string {
  if (candidate.id === 'cli:doctor:fast') return 'not_applicable_pre_engine_fast_path';
  if (candidate.source.includes('pre-dispatch-connectEngine')) return 'src/cli.ts:connectEngine';
  if (candidate.source.includes('module-open-site')) return candidate.source;
  if (candidate.source.includes('src/commands/cache.ts')) return 'src/commands/cache.ts:createEngine';
  if (candidate.source.includes('src/commands/reinit-pglite.ts')) return 'src/commands/reinit-pglite.ts:createEngine';
  return 'src/core/pglite-engine.ts:PGLiteEngine.connect';
}

function validateExpectedManifestOutcome(
  errors: Diagnostic[],
  inventoryRow: Record<string, any>,
  entry: Record<string, any>,
  rowId: string,
): void {
  const expectedOutcome = String(asRecord(inventoryRow.gauntlet).current_expected_outcome ?? '');
  if (expectedOutcome === 'raw_lock_timeout') {
    if (entry.execution_classification !== 'raw_pglite_lock_timeout' || entry.raw_timeout_detected !== true) {
      push(errors, 'manifest_expected_outcome_mismatch', 'raw-lock expected row must record raw_pglite_lock_timeout', { row_id: rowId });
    }
    if (entry.exit_code === 0) {
      push(errors, 'manifest_expected_outcome_mismatch', 'raw-lock expected-red row must not exit 0', { row_id: rowId, field: 'exit_code' });
    }
    return;
  }
  if (expectedOutcome === 'maintenance_deferred') {
    if (entry.typed_error_code !== 'maintenance_deferred' || entry.raw_timeout_detected !== false || entry.timed_out !== false) {
      push(errors, 'manifest_expected_outcome_mismatch', 'maintenance row must record typed maintenance_deferred without raw timeout', { row_id: rowId });
    }
    return;
  }
  if (expectedOutcome === 'existing_broker_success') {
    if (entry.exit_code !== 0 || entry.raw_timeout_detected !== false || entry.timed_out !== false) {
      push(errors, 'manifest_expected_outcome_mismatch', 'broker-success row must exit 0 without timeout or raw lock text', { row_id: rowId });
    }
  }
}

export function discoverInventoryCandidates(repoRoot: string): Candidate[] {
  const root = resolve(repoRoot);
  const operationCandidates = discoverOperationCandidates(root);
  const ownerCandidates: Candidate[] = [
    { id: 'serve:stdio:owner-startup', source: 'src/cli.ts:serve' },
    { id: 'serve:http:owner-startup', source: 'src/commands/serve-http.ts:serve-http' },
    { id: 'serve:duplicate-owner-start', source: 'src/core/pglite-lock.ts' },
  ];
  const maintenance: Candidate[] = [];
  const cliOnly: Candidate[] = discoverCliOnlyDbCandidates(root);
  const specialPreDispatch = discoverSpecialPreDispatchCandidates();
  return [...operationCandidates, ...maintenance, ...cliOnly, ...specialPreDispatch, ...ownerCandidates].sort((a, b) => a.id.localeCompare(b.id));
}

function discoverOperationCandidates(repoRoot: string): Candidate[] {
  const file = resolve(repoRoot, 'src/core/operations.ts');
  const text = readFileSync(file, 'utf-8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const operationNamesByIdentifier = new Map<string, { name: string; localOnly: boolean; scope: string; mutating: boolean; cliName?: string; cliHidden?: boolean }>();

  function visit(node: ts.Node): void {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer && ts.isObjectLiteralExpression(node.initializer)) {
      const name = readStringProperty(node.initializer, 'name');
      if (name) {
        operationNamesByIdentifier.set(node.name.text, {
          name,
          localOnly: readBooleanProperty(node.initializer, 'localOnly') === true,
          scope: readStringProperty(node.initializer, 'scope') ?? 'read',
          mutating: readBooleanProperty(node.initializer, 'mutating') === true,
          ...readCliHints(node.initializer),
        });
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);

  const operationIdentifiers = readOperationsArrayIdentifiers(sf);
  const candidates: Candidate[] = [];
  for (const identifier of operationIdentifiers) {
    const op = operationNamesByIdentifier.get(identifier);
    if (!op) {
      candidates.push({ id: `call:${identifier}:local-cli`, source: `src/core/operations.ts:${identifier}:unresolved` });
      continue;
    }
    candidates.push({
      id: `call:${op.name}:local-cli`,
      source: `src/core/operations.ts:${op.name}`,
      scope: op.scope,
      mutating: op.mutating,
      localOnly: op.localOnly,
    });
    if (op.cliName && !op.cliHidden) {
      candidates.push({
        id: `cli:${op.cliName}:operation-cli`,
        source: `src/core/operations.ts:${op.name}:cliHints`,
        scope: op.scope,
        mutating: op.mutating,
        localOnly: op.localOnly,
      });
    }
    if (!op.localOnly) {
      candidates.push({
        id: `mcp-stdio:${op.name}`,
        source: `src/core/operations.ts:${op.name}`,
        scope: op.scope,
        mutating: op.mutating,
        localOnly: false,
        stdioAdvertised: true,
      });
      candidates.push({
        id: `mcp-http:${op.name}`,
        source: `src/commands/serve-http.ts:${op.name}`,
        scope: op.scope,
        mutating: op.mutating,
        localOnly: false,
      });
    } else {
      candidates.push({
        id: `mcp-stdio:${op.name}:local-only-rejected`,
        source: `src/core/operations.ts:${op.name}`,
        scope: op.scope,
        mutating: op.mutating,
        localOnly: true,
        stdioAdvertised: true,
      });
    }
  }
  return candidates;
}

function discoverCliOnlyDbCandidates(repoRoot: string): Candidate[] {
  const file = resolve(repoRoot, 'src/cli.ts');
  const text = readFileSync(file, 'utf-8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const cliOnly = readStringSet(sf, 'CLI_ONLY');
  const modeSensitive = discoverModeSensitiveCliCandidates(repoRoot, cliOnly);
  const modeSensitiveCommands = new Set(modeSensitive.map((candidate) => candidate.id.split(':')[1]));
  const preEngineNoDb = new Set([
    'schema',
    'init',
    'reinit-pglite',
    'auth',
    'remote',
    'connect',
    'post-upgrade',
    'check-update',
    'self-upgrade',
    'integrations',
    'providers',
    'resolvers',
    'integrity',
    'publish',
    'check-backlinks',
    'frontmatter',
    'lint',
    'check-resolvable',
    'mounts',
    'cache',
    'routing-eval',
    'skillify',
    'skillpack',
    'friction',
    'claw-test',
    'report',
    'repair-jsonb',
    'skillpack-check',
    'smoke-test',
    'conversation-parser',
    'connect',
  ]);
  const explicitDb = new Set(['upgrade', 'apply-migrations', 'doctor', 'ze-switch', 'dream', 'eval', 'status', 'sync', 'embed', 'extract']);
  const candidates: Candidate[] = cliOnly
    .filter((name) => !modeSensitiveCommands.has(name))
    .filter((name) => explicitDb.has(name) || !preEngineNoDb.has(name))
    .map((name) => ({
      id: `cli:${name}:${name === 'sync' || name === 'embed' || name === 'extract' ? 'maintenance' : 'pglite-surface'}`,
      source: 'src/cli.ts:CLI_ONLY',
      scope: 'admin',
      mutating: true,
      localOnly: true,
    }));

  candidates.push(...modeSensitive);

  for (const candidate of discoverCommandModuleOpenSiteCandidates(repoRoot, cliOnly.filter((name) => !explicitDb.has(name) && !modeSensitiveCommands.has(name)))) {
    if (!candidates.some((existing) => existing.id === candidate.id)) candidates.push(candidate);
  }
  if (candidates.length === 0) {
    throw new Error('failed to discover CLI_ONLY DB-bound candidates from src/cli.ts');
  }
  return candidates;
}

const MODE_SENSITIVE_CLI: Record<string, Record<string, { scope: string; mutating: boolean }>> = {
  sources: {
    add: { scope: 'admin', mutating: true },
    list: { scope: 'read', mutating: false },
    remove: { scope: 'admin', mutating: true },
    rename: { scope: 'admin', mutating: true },
    default: { scope: 'admin', mutating: true },
    attach: { scope: 'admin', mutating: true },
    detach: { scope: 'admin', mutating: true },
    federate: { scope: 'admin', mutating: true },
    unfederate: { scope: 'admin', mutating: true },
    archive: { scope: 'admin', mutating: true },
    restore: { scope: 'admin', mutating: true },
    purge: { scope: 'admin', mutating: true },
    archived: { scope: 'read', mutating: false },
    current: { scope: 'read', mutating: false },
    status: { scope: 'read', mutating: false },
    webhook: { scope: 'admin', mutating: true },
    'tracked-branch': { scope: 'admin', mutating: true },
    'set-cr-mode': { scope: 'admin', mutating: true },
    audit: { scope: 'read', mutating: false },
    harden: { scope: 'admin', mutating: true },
    pull: { scope: 'admin', mutating: true },
    unharden: { scope: 'admin', mutating: true },
  },
  config: {
    show: { scope: 'read', mutating: false },
    get: { scope: 'read', mutating: false },
    set: { scope: 'admin', mutating: true },
    unset: { scope: 'admin', mutating: true },
  },
  doctor: {
    default: { scope: 'read', mutating: false },
    fast: { scope: 'read', mutating: false },
    fix: { scope: 'admin', mutating: true },
    locks: { scope: 'admin', mutating: true },
    'remediation-plan': { scope: 'read', mutating: false },
    remediate: { scope: 'admin', mutating: true },
  },
  jobs: {
    submit: { scope: 'agent', mutating: true },
    list: { scope: 'read', mutating: false },
    get: { scope: 'read', mutating: false },
    cancel: { scope: 'admin', mutating: true },
    retry: { scope: 'admin', mutating: true },
    delete: { scope: 'admin', mutating: true },
    prune: { scope: 'admin', mutating: true },
    stats: { scope: 'read', mutating: false },
    smoke: { scope: 'read', mutating: false },
    work: { scope: 'agent', mutating: true },
    supervisor: { scope: 'admin', mutating: true },
    watch: { scope: 'read', mutating: false },
  },
  files: {
    list: { scope: 'read', mutating: false },
    upload: { scope: 'admin', mutating: true },
    sync: { scope: 'admin', mutating: true },
    verify: { scope: 'read', mutating: false },
    mirror: { scope: 'admin', mutating: true },
    unmirror: { scope: 'admin', mutating: true },
    redirect: { scope: 'admin', mutating: true },
    restore: { scope: 'admin', mutating: true },
    clean: { scope: 'admin', mutating: true },
    'upload-raw': { scope: 'admin', mutating: true },
    'signed-url': { scope: 'read', mutating: false },
    status: { scope: 'read', mutating: false },
  },
  takes: {
    list: { scope: 'read', mutating: false },
    search: { scope: 'read', mutating: false },
    add: { scope: 'write', mutating: true },
    update: { scope: 'write', mutating: true },
    supersede: { scope: 'write', mutating: true },
    resolve: { scope: 'write', mutating: true },
    scorecard: { scope: 'read', mutating: false },
    calibration: { scope: 'read', mutating: false },
    revisit: { scope: 'write', mutating: true },
    extract: { scope: 'agent', mutating: true },
  },
  storage: {
    status: { scope: 'read', mutating: false },
  },
  eval: {
    export: { scope: 'read', mutating: false },
    replay: { scope: 'read', mutating: false },
    prune: { scope: 'admin', mutating: true },
    gate: { scope: 'read', mutating: false },
    'code-retrieval': { scope: 'read', mutating: false },
    'retrieval-quality': { scope: 'read', mutating: false },
    brainstorm: { scope: 'read', mutating: false },
    whoknows: { scope: 'read', mutating: false },
    'suspected-contradictions': { scope: 'read', mutating: false },
    trajectory: { scope: 'read', mutating: false },
    'run-all': { scope: 'read', mutating: false },
    compare: { scope: 'read', mutating: false },
    'takes-quality': { scope: 'read', mutating: false },
  },
};

function discoverModeSensitiveCliCandidates(repoRoot: string, cliOnly: string[]): Candidate[] {
  const candidates: Candidate[] = [];
  for (const [command, modes] of Object.entries(MODE_SENSITIVE_CLI)) {
    if (!cliOnly.includes(command)) continue;
    const relative = `src/commands/${command}.ts`;
    const commandText = existsSync(resolve(repoRoot, relative)) ? readFileSync(resolve(repoRoot, relative), 'utf-8') : '';
    const cliText = readFileSync(resolve(repoRoot, 'src/cli.ts'), 'utf-8');
    const sourceText = `${commandText}\n${cliText}`;
    for (const [mode, metadata] of Object.entries(modes)) {
      if (
        mode !== 'default' &&
        !sourceText.includes(`'${mode}'`) &&
        !sourceText.includes(`"${mode}"`) &&
        !sourceText.includes(`--${mode}`)
      ) continue;
      candidates.push({
        id: `cli:${command}:${mode}`,
        source: `${relative}:${mode}`,
        scope: metadata.scope,
        mutating: metadata.mutating,
        localOnly: true,
      });
    }
  }
  return candidates;
}

function discoverCommandModuleOpenSiteCandidates(repoRoot: string, cliOnly: string[]): Candidate[] {
  const candidates: Candidate[] = [];
  for (const command of cliOnly) {
    const relative = `src/commands/${command}.ts`;
    const absolute = resolve(repoRoot, relative);
    if (!existsSync(absolute)) continue;
    const text = readFileSync(absolute, 'utf-8');
    if (!/\b(createEngine|connectEngine|engine\.connect|PGLite)\b/.test(text)) continue;
    if (command === 'cache') {
      candidates.push(
        { id: 'cli:cache:stats', source: 'src/commands/cache.ts:runCache:stats', scope: 'read', mutating: false, localOnly: true },
        { id: 'cli:cache:clear', source: 'src/commands/cache.ts:runCache:clear', scope: 'admin', mutating: true, localOnly: true },
        { id: 'cli:cache:prune', source: 'src/commands/cache.ts:runCache:prune', scope: 'admin', mutating: true, localOnly: true },
      );
      continue;
    }
    if (command === 'reinit-pglite') {
      candidates.push(
        { id: 'cli:reinit-pglite:with-sync', source: 'src/commands/reinit-pglite.ts:runReinitPglite:with-sync', scope: 'admin', mutating: true, localOnly: true },
        { id: 'cli:reinit-pglite:no-sync', source: 'src/commands/reinit-pglite.ts:runReinitPglite:no-sync', scope: 'admin', mutating: true, localOnly: true },
      );
      continue;
    }
    candidates.push({
      id: `cli:${command}:module-open-site`,
      source: `${relative}:module-open-site`,
      scope: 'admin',
      mutating: true,
      localOnly: true,
    });
  }
  return candidates;
}

function discoverSpecialPreDispatchCandidates(): Candidate[] {
  const readModes = ['modes', 'stats', 'tune', 'diagnose'].map((mode) => ({
    id: `cli:search:${mode}`,
    source: `src/cli.ts:search:${mode}:pre-dispatch-connectEngine`,
    scope: 'read',
    mutating: false,
    localOnly: false,
  }));
  return [
    ...readModes,
    {
      id: 'cli:search:modes-reset',
      source: 'src/commands/search.ts:modes:--reset',
      scope: 'admin',
      mutating: true,
      localOnly: false,
    },
    {
      id: 'cli:search:tune-apply',
      source: 'src/commands/search.ts:tune:--apply',
      scope: 'admin',
      mutating: true,
      localOnly: false,
    },
  ];
}

function readOperationsArrayIdentifiers(sf: ts.SourceFile): string[] {
  const names: string[] = [];
  function visit(node: ts.Node): void {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.name.text === 'operations' &&
      node.initializer &&
      ts.isArrayLiteralExpression(node.initializer)
    ) {
      for (const element of node.initializer.elements) {
        if (ts.isIdentifier(element)) names.push(element.text);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);
  return names;
}

function readStringSet(sf: ts.SourceFile, variableName: string): string[] {
  let values: string[] | null = null;
  function visit(node: ts.Node): void {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isIdentifier(node.name) &&
      node.name.text === variableName &&
      node.initializer &&
      ts.isNewExpression(node.initializer) &&
      node.initializer.arguments?.[0] &&
      ts.isArrayLiteralExpression(node.initializer.arguments[0])
    ) {
      values = node.initializer.arguments[0].elements
        .filter((element): element is ts.StringLiteral => ts.isStringLiteral(element))
        .map((element) => element.text);
    }
    ts.forEachChild(node, visit);
  }
  visit(sf);
  if (!values) throw new Error(`failed to parse ${variableName}`);
  return values;
}

function readStringProperty(object: ts.ObjectLiteralExpression, propertyName: string): string | undefined {
  const property = object.properties.find((p): p is ts.PropertyAssignment =>
    ts.isPropertyAssignment(p) && propertyNameOf(p.name) === propertyName,
  );
  if (!property) return undefined;
  const initializer = unwrapExpression(property.initializer);
  return ts.isStringLiteral(initializer) ? initializer.text : undefined;
}

function readBooleanProperty(object: ts.ObjectLiteralExpression, propertyName: string): boolean | undefined {
  const property = object.properties.find((p): p is ts.PropertyAssignment =>
    ts.isPropertyAssignment(p) && propertyNameOf(p.name) === propertyName,
  );
  if (!property) return undefined;
  const initializer = unwrapExpression(property.initializer);
  if (initializer.kind === ts.SyntaxKind.TrueKeyword) return true;
  if (initializer.kind === ts.SyntaxKind.FalseKeyword) return false;
  return undefined;
}

function unwrapExpression(expression: ts.Expression): ts.Expression {
  if (ts.isAsExpression(expression) || ts.isTypeAssertionExpression(expression) || ts.isParenthesizedExpression(expression)) {
    return unwrapExpression(expression.expression);
  }
  return expression;
}

function readCliHints(object: ts.ObjectLiteralExpression): { cliName?: string; cliHidden?: boolean } {
  const property = object.properties.find((p): p is ts.PropertyAssignment =>
    ts.isPropertyAssignment(p) && propertyNameOf(p.name) === 'cliHints',
  );
  if (!property || !ts.isObjectLiteralExpression(property.initializer)) return {};
  return {
    cliName: readStringProperty(property.initializer, 'name'),
    cliHidden: readBooleanProperty(property.initializer, 'hidden') === true,
  };
}

function propertyNameOf(name: ts.PropertyName): string | undefined {
  if (ts.isIdentifier(name) || ts.isStringLiteral(name) || ts.isNumericLiteral(name)) return name.text;
  return undefined;
}

export function sourceFingerprint(repoRoot: string, relativePath: string): string {
  const file = resolve(repoRoot, relativePath);
  return createHash('sha256').update(readFileSync(file)).digest('hex');
}

function loadInventoryFile(path: string): unknown {
  return yaml.load(readFileSync(path, 'utf-8'));
}

if (import.meta.main) {
  const inventoryPath = process.argv[2];
  if (!inventoryPath) {
    console.error('Usage: scripts/validate-pglite-access-inventory.ts <inventory-yml> [--json]');
    process.exit(64);
  }
  if (!existsSync(inventoryPath)) {
    console.error(`Inventory file not found: ${inventoryPath}`);
    process.exit(66);
  }
  const repoRoot = process.cwd();
  const validation = validateInventoryObject(loadInventoryFile(inventoryPath), { repoRoot });
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(validation, null, 2));
  } else if (!validation.ok) {
    for (const error of validation.errors) {
      console.error(`${error.code}${error.row_id ? ` ${error.row_id}` : ''}: ${error.message}`);
    }
  }
  process.exit(validation.ok ? 0 : 1);
}
