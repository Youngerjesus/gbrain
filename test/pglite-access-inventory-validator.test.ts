import { describe, expect, test } from 'bun:test';
import {
  classifyPgliteAccessOutput,
  discoverInventoryCandidates,
  sourceFingerprint,
  validateGauntletManifestObject,
  validateInventoryObject,
} from '../scripts/validate-pglite-access-inventory.ts';

const baseRow = {
  id: 'call:list_pages:local-cli',
  command_or_operation: 'call list_pages',
  subcommand_or_mode: 'list_pages',
  argument_profile: '{}',
  entry_kind: 'operation',
  caller_surface: 'cli',
  transport: 'local-cli',
  implementation_entrypoint: 'src/core/operations.ts:list_pages',
  database_open_site: 'src/core/pglite-engine.ts:PGLiteEngine.connect',
  current_owner_behavior: 'raw_lock_timeout_expected_red',
  no_owner_baseline: 'direct_open_valid',
  accepted_behavior_class: 'broker_success_read',
  scope: 'read',
  local_only: false,
  mcp_exposed: true,
  operation_context_remote: false,
  filesystem_confinement: 'not_applicable',
  side_effects: ['none'],
  data_preconditions: ['seeded_page'],
  gauntlet: {
    mode: 'runnable',
    current_expected_outcome: 'raw_lock_timeout',
    future_required_outcome: 'broker_success',
    attempts: 3,
  },
  evidence_refs: ['src/core/operations.ts:list_pages'],
};

describe('PGLite access inventory validator', () => {
  test('rejects missing code-derived candidates with row-specific diagnostics', () => {
    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: {
        attempts: 3,
        raw_lock_timeout_allowed: false,
      },
      required_surface_ids: ['call:list_pages:local-cli'],
      source_fingerprints: {
        'src/core/operations.ts': 'fixture',
      },
      rows: [baseRow],
    }, {
      candidates: [
        { id: 'call:list_pages:local-cli', source: 'src/core/operations.ts:list_pages' },
        { id: 'call:get_page:local-cli', source: 'src/core/operations.ts:get_page' },
      ],
      allowSyntheticFingerprints: true,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'missing_candidate_row',
      row_id: 'call:get_page:local-cli',
    }));
  });

  test('discovers DB-bound CLI-only commands beyond the curated known surface list', () => {
    const ids = discoverInventoryCandidates(process.cwd()).map((candidate) => candidate.id);
    expect(ids).toContain('cli:import:pglite-surface');
    expect(ids).toContain('cli:jobs:list');
    expect(ids).toContain('cli:jobs:submit');
    expect(ids).toContain('cli:reindex:pglite-surface');
    expect(ids).toContain('cli:cache:stats');
    expect(ids).toContain('cli:cache:clear');
    expect(ids).toContain('cli:cache:prune');
    expect(ids).toContain('cli:reinit-pglite:with-sync');
    expect(ids).toContain('cli:reinit-pglite:no-sync');
    expect(ids).toContain('cli:search:modes');
    expect(ids).toContain('cli:search:diagnose');
  });

  test('discovers mode-sensitive CLI subcommands with separate side-effect metadata', () => {
    const candidates = discoverInventoryCandidates(process.cwd());
    const ids = candidates.map((candidate) => candidate.id);
    expect(ids).toContain('cli:sources:list');
    expect(ids).toContain('cli:sources:remove');
    expect(ids).not.toContain('cli:sources:pglite-surface');
    expect(candidates.find((candidate) => candidate.id === 'cli:sources:list')).toEqual(expect.objectContaining({
      scope: 'read',
      mutating: false,
    }));
    expect(candidates.find((candidate) => candidate.id === 'cli:sources:remove')).toEqual(expect.objectContaining({
      scope: 'admin',
      mutating: true,
    }));
    expect(ids).toContain('cli:doctor:fast');
    expect(ids).toContain('cli:doctor:fix');
    expect(ids).toContain('cli:doctor:locks');
    expect(ids).toContain('cli:doctor:remediation-plan');
    expect(ids).toContain('cli:doctor:remediate');
    expect(ids).toContain('cli:search:modes-reset');
    expect(ids).toContain('cli:search:tune-apply');
    expect(ids).toContain('cli:eval:gate');
    expect(ids).toContain('cli:eval:code-retrieval');
    expect(ids).toContain('cli:eval:trajectory');
  });

  test('rejects operation rows whose scope and side effects contradict source metadata', () => {
    const mutatingRow = {
      ...baseRow,
      id: 'call:add_timeline_entry:local-cli',
      command_or_operation: 'gbrain call add_timeline_entry',
      subcommand_or_mode: 'add_timeline_entry',
      implementation_entrypoint: 'src/core/operations.ts:add_timeline_entry',
      accepted_behavior_class: 'broker_success_read',
      scope: 'read',
      side_effects: ['none'],
      gauntlet: {
        mode: 'fixture_only',
        current_expected_outcome: 'classified_from_source_inventory',
        future_required_outcome: 'broker_success_read',
      },
    };

    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: { attempts: 3, raw_lock_timeout_allowed: false },
      required_surface_ids: ['call:add_timeline_entry:local-cli'],
      source_fingerprints: { 'src/core/operations.ts': 'fixture' },
      rows: [mutatingRow],
    }, {
      candidates: [{
        id: 'call:add_timeline_entry:local-cli',
        source: 'src/core/operations.ts:add_timeline_entry',
        scope: 'write',
        mutating: true,
      }],
      allowSyntheticFingerprints: true,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'candidate_metadata_mismatch',
      row_id: 'call:add_timeline_entry:local-cli',
    }));
  });

  test('rejects stale source fingerprints', () => {
    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: { attempts: 3, raw_lock_timeout_allowed: false },
      required_surface_ids: ['call:list_pages:local-cli'],
      source_fingerprints: {
        'src/core/operations.ts': 'stale',
        'src/cli.ts': sourceFingerprint(process.cwd(), 'src/cli.ts'),
        'src/mcp/server.ts': sourceFingerprint(process.cwd(), 'src/mcp/server.ts'),
        'src/commands/serve-http.ts': sourceFingerprint(process.cwd(), 'src/commands/serve-http.ts'),
      },
      rows: [baseRow],
    }, {
      candidates: [{ id: 'call:list_pages:local-cli', source: 'src/core/operations.ts:list_pages' }],
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'stale_source_fingerprint',
      source: 'src/core/operations.ts',
    }));
  });

  test('rejects stdio localOnly rows that claim they are not advertised over stdio', () => {
    const row = {
      ...baseRow,
      id: 'mcp-stdio:file_upload:local-only-rejected',
      command_or_operation: 'file_upload',
      subcommand_or_mode: 'file_upload',
      caller_surface: 'mcp',
      transport: 'mcp-stdio',
      implementation_entrypoint: 'src/core/operations.ts:file_upload',
      accepted_behavior_class: 'typed_guard_fail_fast',
      scope: 'admin',
      local_only: true,
      mcp_exposed: false,
      operation_context_remote: true,
      filesystem_confinement: 'remote_strict_confinement_or_local_only_rejection',
      side_effects: ['filesystem'],
      gauntlet: {
        mode: 'safe_non_execution',
        safe_non_execution_reason: 'filesystem mutation path',
        current_expected_outcome: 'not_executed_in_requirement_006',
        future_required_outcome: 'typed_guard_fail_fast',
      },
    };

    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: { attempts: 3, raw_lock_timeout_allowed: false },
      required_surface_ids: [row.id],
      source_fingerprints: { 'src/core/operations.ts': 'fixture' },
      rows: [row],
    }, {
      candidates: [{
        id: row.id,
        source: 'src/core/operations.ts:file_upload',
        scope: 'admin',
        mutating: true,
        localOnly: true,
        stdioAdvertised: true,
      }],
      allowSyntheticFingerprints: true,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'candidate_metadata_mismatch',
      row_id: row.id,
      field: 'mcp_exposed',
    }));
  });

  test('rejects incomplete gauntlet manifests before coverage closure', () => {
    const result = validateGauntletManifestObject({
      inventory_row_ids: ['call:list_pages:local-cli'],
      attempts_expected: 3,
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [
        { row_id: 'call:list_pages:local-cli', attempt: 1, execution_classification: 'expected_red' },
      ],
      safe_non_execution: [],
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'wrong_attempt_count',
      row_id: 'call:list_pages:local-cli',
    }));
  });

  test('rejects gauntlet manifests not bound to the actual inventory rows', () => {
    const safeRow = {
      ...baseRow,
      id: 'call:file_upload:local-cli',
      command_or_operation: 'gbrain call file_upload',
      subcommand_or_mode: 'file_upload',
      accepted_behavior_class: 'serialized_owner_mutation',
      scope: 'admin',
      local_only: true,
      filesystem_confinement: 'trusted_local_filesystem',
      side_effects: ['filesystem'],
      gauntlet: {
        mode: 'safe_non_execution',
        safe_non_execution_reason: 'filesystem mutation path represented without destructive live execution',
        safe_non_execution_risk_type: 'filesystem_mutation',
        safe_non_execution_source_ref: 'src/core/operations.ts:file_upload',
        current_expected_outcome: 'not_executed_in_requirement_006',
        future_required_outcome: 'serialized_owner_mutation',
      },
    };
    const inventory = {
      rows: [baseRow, safeRow],
    };

    const result = validateGauntletManifestObject({
      inventory_row_ids: ['call:list_pages:local-cli', 'call:fake_safe:local-cli'],
      attempts_expected: 3,
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [
        { row_id: 'call:list_pages:local-cli', attempt: 1, command: 'gbrain call list_pages', execution_classification: 'expected_red' },
        { row_id: 'call:list_pages:local-cli', attempt: 2, command: 'gbrain call list_pages', execution_classification: 'expected_red' },
        { row_id: 'call:list_pages:local-cli', attempt: 3, command: 'gbrain call list_pages', execution_classification: 'expected_red' },
      ],
      safe_non_execution: [
        { row_id: 'call:fake_safe:local-cli', reason: 'fake', future_required_outcome: 'typed_guard_fail_fast' },
      ],
    }, { inventory });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'unknown_manifest_row',
      row_id: 'call:fake_safe:local-cli',
    }));
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'missing_safe_non_execution',
      row_id: 'call:file_upload:local-cli',
    }));
  });

  test('rejects gauntlet manifests with missing result shape or wrong expected outcomes', () => {
    const inventory = { rows: [baseRow] };

    const missingShape = validateGauntletManifestObject({
      inventory_row_ids: ['call:list_pages:local-cli'],
      attempts_expected: 3,
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [
        { row_id: 'call:list_pages:local-cli', attempt: 1, command: 'call list_pages', execution_classification: 'other' },
        { row_id: 'call:list_pages:local-cli', attempt: 2, command: 'call list_pages', execution_classification: 'other' },
        { row_id: 'call:list_pages:local-cli', attempt: 3, command: 'call list_pages', execution_classification: 'other' },
      ],
      safe_non_execution: [],
    }, { inventory });

    expect(missingShape.ok).toBe(false);
    expect(missingShape.errors).toContainEqual(expect.objectContaining({
      code: 'missing_manifest_result_field',
      row_id: 'call:list_pages:local-cli',
    }));
    expect(missingShape.errors).toContainEqual(expect.objectContaining({
      code: 'manifest_expected_outcome_mismatch',
      row_id: 'call:list_pages:local-cli',
    }));
  });

  test('rejects claimed manifest classifications that are not supported by captured output', () => {
    const inventory = { rows: [baseRow] };

    const result = validateGauntletManifestObject({
      inventory_row_ids: ['call:list_pages:local-cli'],
      attempts_expected: 3,
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [1, 2, 3].map((attempt) => ({
        row_id: 'call:list_pages:local-cli',
        attempt,
        command: 'call list_pages',
        exit_code: 1,
        timed_out: false,
        stdout: '',
        stderr: '',
        execution_classification: 'raw_pglite_lock_timeout',
        raw_timeout_detected: true,
      })),
      safe_non_execution: [],
    }, { inventory });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'manifest_classification_mismatch',
      row_id: 'call:list_pages:local-cli',
    }));
  });

  test('rejects raw lock timeout rows with successful exit codes', () => {
    const inventory = { rows: [baseRow] };

    const result = validateGauntletManifestObject({
      inventory_row_ids: ['call:list_pages:local-cli'],
      attempts_expected: 3,
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [1, 2, 3].map((attempt) => ({
        row_id: 'call:list_pages:local-cli',
        attempt,
        command: 'call list_pages',
        exit_code: 0,
        timed_out: false,
        stdout: '',
        stderr: 'GBrain: Timed out waiting for PGLite lock. Aborting.',
        execution_classification: 'raw_pglite_lock_timeout',
        raw_timeout_detected: true,
      })),
      safe_non_execution: [],
    }, { inventory });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'manifest_expected_outcome_mismatch',
      row_id: 'call:list_pages:local-cli',
    }));
  });

  test('rejects inventory rows with fake command or database open site', () => {
    const row = {
      ...baseRow,
      command_or_operation: 'fake command',
      database_open_site: 'fake open site',
    };
    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: { attempts: 3, raw_lock_timeout_allowed: false },
      required_surface_ids: [row.id],
      source_fingerprints: { 'src/core/operations.ts': 'fixture' },
      rows: [row],
    }, {
      candidates: [{ id: row.id, source: 'src/core/operations.ts:list_pages', scope: 'read', mutating: false }],
      allowSyntheticFingerprints: true,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'candidate_metadata_mismatch',
      field: 'command_or_operation',
    }));
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'candidate_metadata_mismatch',
      field: 'database_open_site',
    }));
  });

  test('rejects generic unbounded safe non-execution rationale', () => {
    const row = {
      ...baseRow,
      id: 'call:file_upload:local-cli',
      accepted_behavior_class: 'serialized_owner_mutation',
      scope: 'admin',
      local_only: true,
      filesystem_confinement: 'trusted_local_filesystem',
      side_effects: ['filesystem'],
      gauntlet: {
        mode: 'safe_non_execution',
        safe_non_execution_reason: 'destructive_or_remote_authority_sensitive_path',
        current_expected_outcome: 'not_executed_in_requirement_006',
        future_required_outcome: 'serialized_owner_mutation',
      },
    };

    const result = validateInventoryObject({
      requirement_id: '006-pglite-access-path-inventory',
      schema_version: 1,
      generated_from: ['unit fixture'],
      later_sequence_standard: { attempts: 3, raw_lock_timeout_allowed: false },
      required_surface_ids: [row.id],
      source_fingerprints: { 'src/core/operations.ts': 'fixture' },
      rows: [row],
    }, {
      candidates: [{
        id: row.id,
        source: 'src/core/operations.ts:file_upload',
        scope: 'admin',
        mutating: true,
        localOnly: true,
      }],
      allowSyntheticFingerprints: true,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'unbounded_safe_non_execution',
      row_id: row.id,
    }));
  });

  test('rejects gauntlet results whose command does not match the inventory row command', () => {
    const result = validateGauntletManifestObject({
      inventory_row_ids: ['call:query:local-cli'],
      attempts_expected: 1,
      row_commands: {
        'call:query:local-cli': 'gbrain call query',
      },
      harness: {
        owner_pid: 123,
        lock_observed: true,
        broker_ready: true,
        backend_confirmed: 'pglite-temp',
        harness_phase: 'rows',
        teardown_status: 'clean',
        cleanup_required: false,
      },
      results: [
        {
          row_id: 'call:query:local-cli',
          attempt: 1,
          command: 'gbrain query',
          execution_classification: 'other',
        },
      ],
      safe_non_execution: [],
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContainEqual(expect.objectContaining({
      code: 'row_command_mismatch',
      row_id: 'call:query:local-cli',
    }));
  });

  test('classifies raw lock timeouts separately from typed errors and harness timeouts', () => {
    expect(classifyPgliteAccessOutput({
      stderr: 'GBrain: Timed out waiting for PGLite lock. Aborting.',
      timed_out: false,
    })).toEqual({ kind: 'raw_pglite_lock_timeout', raw_timeout_detected: true });

    expect(classifyPgliteAccessOutput({
      stderr: '{"error":"owner_unreachable"}',
      timed_out: false,
    })).toEqual({ kind: 'typed_owner_or_guard_error', raw_timeout_detected: false, typed_error_code: 'owner_unreachable' });

    expect(classifyPgliteAccessOutput({
      stderr: '',
      timed_out: true,
    })).toEqual({ kind: 'harness_timeout', raw_timeout_detected: false });
  });
});
