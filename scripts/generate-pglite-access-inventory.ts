#!/usr/bin/env bun

import { writeFileSync } from 'node:fs';
import yaml from 'js-yaml';
import {
  discoverInventoryCandidates,
  sourceFingerprint,
} from './validate-pglite-access-inventory.ts';

function opName(id: string): string {
  if (id.startsWith('call:')) return id.split(':')[1] ?? id;
  if (id.startsWith('mcp-')) return id.split(':')[1] ?? id;
  if (id.startsWith('cli:')) return id.split(':')[1] ?? id;
  if (id.startsWith('serve:')) return id.split(':').slice(1).join(':');
  return id;
}

function modeName(id: string): string {
  const parts = id.split(':');
  if (id.startsWith('cli:')) return parts[2] ?? parts[1] ?? id;
  if (id.startsWith('serve:')) return parts.slice(1).join(':');
  return parts[1] ?? id;
}

function commandFor(id: string): string {
  const op = opName(id);
  const mode = modeName(id);
  if (id.startsWith('cli:')) {
    if (op === 'doctor' && mode === 'default') return 'gbrain doctor';
    if (op === 'doctor' && ['fast', 'fix', 'locks', 'remediation-plan', 'remediate'].includes(mode)) return `gbrain doctor --${mode}`;
    if (op === 'search' && mode === 'modes-reset') return 'gbrain search modes --reset';
    if (op === 'search' && mode === 'tune-apply') return 'gbrain search tune --apply';
    if (['operation-cli', 'pglite-surface', 'maintenance', 'module-open-site'].includes(mode)) return `gbrain ${op}`;
    return `gbrain ${op} ${mode}`;
  }
  if (id.startsWith('serve:')) return `gbrain serve ${op}`;
  if (id.startsWith('call:')) return `gbrain call ${op}`;
  return op;
}

function databaseOpenSiteFor(candidate: { source?: string }): string {
  const source = candidate.source ?? '';
  if ((candidate as any).id === 'cli:doctor:fast') return 'not_applicable_pre_engine_fast_path';
  if (source.includes('pre-dispatch-connectEngine')) return 'src/cli.ts:connectEngine';
  if (source.includes('module-open-site')) return source;
  if (source.includes('src/commands/cache.ts')) return 'src/commands/cache.ts:createEngine';
  if (source.includes('src/commands/reinit-pglite.ts')) return 'src/commands/reinit-pglite.ts:createEngine';
  return 'src/core/pglite-engine.ts:PGLiteEngine.connect';
}

const LIVE_RUNNABLE_ROWS = new Set([
  'cli:query:operation-cli',
  'cli:search:operation-cli',
  'cli:think:operation-cli',
  'cli:sync:maintenance',
  'call:list_pages:local-cli',
]);

const CLI_LIVE_OWNER_TYPED_GUARD_PREFIXES = [
  'cli:autopilot',
  'cli:claw-test',
  'cli:frontmatter',
  'cli:init',
  'cli:integrity',
  'cli:mounts',
  'cli:reinit-pglite',
  'cli:repair-jsonb',
  'cli:schema',
  'cli:watch',
];

function scopeFor(id: string, candidate?: { scope?: string }): string {
  if (candidate?.scope) return candidate.scope;
  if (/query|search|list|get|find|stats|health|whoami|refs|def|callers|callees|trajectory|anomalies|salience|recall|skills|schema_(stats|lint|graph|explain|review)|sources_list|status|versions|chunks|links|tags|timeline|takes/.test(id)) {
    return 'read';
  }
  if (/sources_|schema_apply|run_|submit|cancel|retry|pause|resume|replay|purge|file_|sync|embed|extract|migrations|upgrade|doctor|delete|put|add|remove|restore|revert|forget|log_|reload|send/.test(id)) {
    return 'admin';
  }
  return 'write';
}

function behaviorFor(id: string, candidate?: { scope?: string; mutating?: boolean }): string {
  if (
    id.includes(':local-only-rejected') ||
    id.startsWith('cli:sync') ||
    id.startsWith('cli:embed') ||
    id.startsWith('cli:extract') ||
    id.startsWith('cli:apply-migrations') ||
    id.startsWith('cli:upgrade') ||
    CLI_LIVE_OWNER_TYPED_GUARD_PREFIXES.some((prefix) => id.startsWith(prefix)) ||
    id.startsWith('serve:duplicate')
  ) {
    return 'typed_guard_fail_fast';
  }
  if (!candidate?.mutating && (scopeFor(id, candidate) === 'read' || id.includes(':query') || id.includes(':search') || id.includes(':think'))) {
    return 'broker_success_read';
  }
  return 'serialized_owner_mutation';
}

function safeNonExecutionFor(id: string, behavior: string, candidate?: { source?: string }): Record<string, unknown> | null {
  const sourceRef = candidate?.source ?? 'source:unknown';
  if (id.includes(':local-only-rejected')) {
    return {
      safe_non_execution_reason: 'remote MCP local-only path is represented without weakening OperationContext.remote authorization',
      safe_non_execution_risk_type: 'remote_authority_sensitive',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: 'typed_guard_fail_fast',
    };
  }
  if (id.startsWith('cli:apply-migrations') || id.startsWith('cli:upgrade') || id.includes('schema_apply')) {
    return {
      safe_non_execution_reason: 'schema and migration path requires exclusive ownership and is not executed in the inventory gauntlet',
      safe_non_execution_risk_type: 'schema_or_migration',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: 'typed_guard_fail_fast',
    };
  }
  if (id.startsWith('cli:reinit-pglite')) {
    return {
      safe_non_execution_reason: 'brain reinitialization can wipe and recreate the local PGLite store and is represented without destructive live execution',
      safe_non_execution_risk_type: 'irreversible_brain_reinit',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: 'typed_guard_fail_fast',
    };
  }
  if (id.startsWith('cli:cache:clear') || id.includes('delete') || id.includes('purge') || id.includes('forget') || id.includes('remove') || id.includes('revert')) {
    return {
      safe_non_execution_reason: 'destructive data mutation path is represented without changing temporary gauntlet data state',
      safe_non_execution_risk_type: 'destructive_data_mutation',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: behavior,
    };
  }
  if (id === 'cli:doctor:fix' || id === 'cli:search:modes-reset' || id === 'cli:search:tune-apply') {
    return {
      safe_non_execution_reason: 'settings or repair mutation flag profile is represented without applying live configuration or repair changes',
      safe_non_execution_risk_type: 'destructive_data_mutation',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: behavior,
    };
  }
  if (id.startsWith('cli:files') || id.includes('file_upload') || id.includes('file_')) {
    return {
      safe_non_execution_reason: 'filesystem-touching path is represented without live destructive or host-file mutation',
      safe_non_execution_risk_type: 'filesystem_mutation',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: behavior,
    };
  }
  if (
    id.includes('run_skillopt') ||
    id.includes('submit') ||
    id.includes('cancel') ||
    id.includes('retry') ||
    id.includes('replay') ||
    id.includes('send_job') ||
    id.startsWith('cli:embed') ||
    id.startsWith('cli:extract')
  ) {
    return {
      safe_non_execution_reason: 'background job or heavy maintenance path is represented without starting durable asynchronous work',
      safe_non_execution_risk_type: 'maintenance_or_background_job',
      safe_non_execution_source_ref: sourceRef,
      future_required_outcome: behavior === 'broker_success_read' ? 'typed_guard_fail_fast' : behavior,
    };
  }
  return null;
}

function gauntletFor(id: string, candidate?: { scope?: string; mutating?: boolean; source?: string }): Record<string, unknown> {
  const behavior = behaviorFor(id, candidate);
  const safeNonExecution = safeNonExecutionFor(id, behavior, candidate);
  if (safeNonExecution) {
    return {
      mode: 'safe_non_execution',
      ...safeNonExecution,
      current_expected_outcome: 'not_executed_in_requirement_006',
    };
  }
  if (id.startsWith('cli:sync') || id.startsWith('cli:embed') || id.startsWith('cli:extract')) {
    return {
      mode: 'runnable',
      attempts: 3,
      current_expected_outcome: 'maintenance_deferred',
      future_required_outcome: 'typed_guard_fail_fast',
    };
  }
  if (id.startsWith('serve:')) {
    return {
      mode: 'fixture_only',
      current_expected_outcome: id.includes('duplicate') ? 'typed_duplicate_owner_state' : 'owner_starts',
      future_required_outcome: id.includes('duplicate') ? 'typed_guard_fail_fast' : 'owner_ready',
    };
  }
  if (LIVE_RUNNABLE_ROWS.has(id) && id === 'call:list_pages:local-cli') {
    return {
      mode: 'runnable',
      attempts: 3,
      current_expected_outcome: 'raw_lock_timeout',
      future_required_outcome: 'broker_success',
    };
  }
  if (LIVE_RUNNABLE_ROWS.has(id) && (id.includes(':query') || id.includes(':search') || id.includes(':think'))) {
    return {
      mode: 'runnable',
      attempts: 3,
      current_expected_outcome: 'existing_broker_success',
      future_required_outcome: 'broker_success',
    };
  }
  return {
    mode: 'fixture_only',
    current_expected_outcome: 'classified_from_source_inventory',
    future_required_outcome: behavior,
  };
}

const repoRoot = process.cwd();
const candidates = discoverInventoryCandidates(repoRoot);
const rows = candidates.map((candidate) => {
  const id = candidate.id;
  const op = opName(id);
  const mode = modeName(id);
  const mcp = id.startsWith('mcp-');
  const localOnlyRejected = id.includes(':local-only-rejected');
  const scope = scopeFor(id, candidate);
  const mutating = candidate.mutating === true;
  return {
    id,
    command_or_operation: commandFor(id),
    subcommand_or_mode: mode,
    argument_profile: id.startsWith('call:') || id.startsWith('mcp-') ? 'operation_schema' : 'mode_specific',
    entry_kind: id.startsWith('call:') || id.startsWith('mcp-')
      ? 'operation'
      : id.startsWith('serve:')
        ? 'owner_startup'
        : 'cli_command',
    caller_surface: id.startsWith('serve:') ? 'owner' : mcp ? 'mcp' : 'cli',
    transport: id.startsWith('mcp-http')
      ? 'mcp-http'
      : id.startsWith('mcp-stdio')
        ? 'mcp-stdio'
        : id.startsWith('call:')
          ? 'gbrain-call'
          : id.startsWith('serve:http')
            ? 'owner-http'
            : id.startsWith('serve:')
              ? 'owner-stdio'
              : 'local-cli',
    implementation_entrypoint: candidate.source,
    database_open_site: databaseOpenSiteFor(candidate),
    current_owner_behavior: localOnlyRejected
      ? 'local_only_rejected_before_remote_execution'
      : id === 'call:list_pages:local-cli'
        ? 'raw_lock_timeout_expected_red_under_live_owner'
      : id.includes(':query') || id.includes(':search') || id.includes(':think')
        ? (LIVE_RUNNABLE_ROWS.has(id) ? 'existing_owner_broker_path' : 'source_open_site_or_transport_variant_requires_requirement_007_verification')
        : id.startsWith('cli:sync') || id.startsWith('cli:embed') || id.startsWith('cli:extract')
          ? (LIVE_RUNNABLE_ROWS.has(id) ? 'maintenance_deferred_under_live_owner' : 'maintenance_path_classified_without_live_execution')
          : id.startsWith('serve:')
            ? 'owner_startup_or_duplicate_owner_state'
            : 'source_open_site_classified_without_live_execution',
    no_owner_baseline: id.startsWith('mcp-')
      ? 'not_applicable_remote_transport'
      : 'direct_open_valid_when_no_owner_where_command_supports_it',
    accepted_behavior_class: behaviorFor(id, candidate),
    scope,
    local_only: candidate.localOnly === true ||
      localOnlyRejected ||
      id.includes('file_') ||
      id.includes('sync_brain') ||
      id.includes('purge_deleted') ||
      id.includes('code_traversal_cache_clear') ||
      id.includes('get_recent_transcripts'),
    mcp_exposed: mcp && (id.startsWith('mcp-stdio') || !localOnlyRejected),
    operation_context_remote: mcp,
    filesystem_confinement: id.includes('file')
      ? (mcp ? 'remote_strict_confinement_or_local_only_rejection' : 'trusted_local_filesystem')
      : 'not_applicable',
    side_effects: scope === 'read' && !mutating ? ['none'] : id.includes('file') ? ['filesystem'] : scope === 'admin' ? ['admin_or_schema_or_job_state'] : ['db_write'],
    data_preconditions: id.startsWith('serve:') ? ['temp_pglite_home'] : ['temp_pglite_home', 'seeded_source_or_page_when_runnable'],
    gauntlet: gauntletFor(id, candidate),
    evidence_refs: [candidate.source],
  };
});

const doc = {
  requirement_id: '006-pglite-access-path-inventory',
  schema_version: 1,
  generated_from: [
    'src/core/operations.ts',
    'src/cli.ts',
    'src/mcp/server.ts',
    'src/commands/serve-http.ts',
    'src/core/pglite-engine.ts',
    'src/core/pglite-lock.ts',
  ],
  later_sequence_standard: {
    attempts: 3,
    raw_lock_timeout_allowed: false,
    allowed_final_outcomes: ['broker_success_read', 'serialized_owner_mutation', 'typed_guard_fail_fast'],
  },
  source_fingerprints: {
    'src/core/operations.ts': sourceFingerprint(repoRoot, 'src/core/operations.ts'),
    'src/cli.ts': sourceFingerprint(repoRoot, 'src/cli.ts'),
    'src/mcp/server.ts': sourceFingerprint(repoRoot, 'src/mcp/server.ts'),
    'src/commands/serve-http.ts': sourceFingerprint(repoRoot, 'src/commands/serve-http.ts'),
  },
  required_surface_ids: candidates.map((candidate) => candidate.id),
  rows,
};

writeFileSync(
  'requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml',
  yaml.dump(doc, { lineWidth: 120, noRefs: true }),
  'utf-8',
);
