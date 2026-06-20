import { operationsByName } from './operations.ts';

export type PgliteOwnerBehaviorClass =
  | 'broker_success_read'
  | 'serialized_owner_mutation'
  | 'typed_guard_fail_fast';

export type PgliteOwnerCaller = 'cli' | 'mcp-stdio' | 'mcp-http';

export type PgliteOwnerTarget =
  | { kind: 'operation'; name: string }
  | { kind: 'cli_command'; surfaceId: string; command: string; args: string[]; profile?: string }
  | { kind: 'owner_startup'; surfaceId: string };

export interface PgliteOwnerPolicyInput {
  surfaceId: string;
  target: PgliteOwnerTarget;
  caller: PgliteOwnerCaller;
}

export interface PgliteOwnerPolicy {
  surfaceId: string;
  target: PgliteOwnerTarget;
  behaviorClass: PgliteOwnerBehaviorClass;
  allowedCallers: PgliteOwnerCaller[];
  remoteAllowed: boolean;
  localOnly: boolean;
  filesystemSensitive: boolean;
  requiresOwnerSerialization: boolean;
  guardStatusWhenLiveOwner?: string;
  noOwnerMode: 'direct_open_allowed' | 'not_applicable';
}

const CLI_BROKER_SUCCESS_READ = new Set<string>([
  'cli:anomalies:operation-cli', 'cli:backlinks:operation-cli', 'cli:brain-skillpack:operation-cli',
  'cli:cache:stats', 'cli:config:get', 'cli:config:show', 'cli:doctor:default', 'cli:doctor:fast',
  'cli:doctor:remediation-plan', 'cli:eval:brainstorm', 'cli:eval:code-retrieval', 'cli:eval:compare',
  'cli:eval:export', 'cli:eval:gate', 'cli:eval:replay', 'cli:eval:retrieval-quality', 'cli:eval:run-all',
  'cli:eval:suspected-contradictions', 'cli:eval:takes-quality', 'cli:eval:trajectory', 'cli:eval:whoknows',
  'cli:files:list', 'cli:files:signed-url', 'cli:files:status', 'cli:files:verify',
  'cli:find-contradictions:operation-cli', 'cli:find-trajectory:operation-cli', 'cli:get:operation-cli',
  'cli:graph:operation-cli', 'cli:history:operation-cli', 'cli:jobs:get', 'cli:jobs:list',
  'cli:jobs:smoke', 'cli:jobs:stats', 'cli:jobs:watch', 'cli:link-sources:operation-cli',
  'cli:list:operation-cli', 'cli:query:operation-cli', 'cli:salience:operation-cli',
  'cli:search-by-image:operation-cli', 'cli:search:diagnose', 'cli:search:modes',
  'cli:search:operation-cli', 'cli:search:stats', 'cli:search:tune', 'cli:skill:operation-cli',
  'cli:skills:operation-cli', 'cli:sources:archived', 'cli:sources:audit', 'cli:sources:current',
  'cli:sources:list', 'cli:sources:status', 'cli:storage:status', 'cli:tags:operation-cli',
  'cli:takes-calibration:operation-cli', 'cli:takes-list:operation-cli', 'cli:takes-scorecard:operation-cli',
  'cli:takes-search:operation-cli', 'cli:takes:calibration', 'cli:takes:list', 'cli:takes:scorecard',
  'cli:takes:search', 'cli:timeline:operation-cli', 'cli:volunteer-context:operation-cli',
  'cli:whoami:operation-cli', 'cli:whoknows:operation-cli',
]);

const CLI_SERIALIZED_OWNER_MUTATION = new Set<string>([
  'cli:advisor:pglite-surface', 'cli:agent:pglite-surface', 'cli:anomalies:pglite-surface',
  'cli:auth:module-open-site',
  'cli:book-mirror:pglite-surface', 'cli:brainstorm:pglite-surface', 'cli:cache:clear',
  'cli:cache:prune', 'cli:call:pglite-surface', 'cli:capture:pglite-surface',
  'cli:code-callees:pglite-surface', 'cli:code-callers:pglite-surface',
  'cli:code-def:pglite-surface', 'cli:code-refs:pglite-surface', 'cli:config:set',
  'cli:config:unset', 'cli:delete:operation-cli', 'cli:doctor:fix', 'cli:doctor:locks',
  'cli:doctor:remediate', 'cli:dream:pglite-surface', 'cli:edges-backfill:module-open-site',
  'cli:edges-backfill:pglite-surface', 'cli:enrich:module-open-site', 'cli:enrich:pglite-surface',
  'cli:eval:prune', 'cli:export:pglite-surface', 'cli:features:pglite-surface', 'cli:files:clean',
  'cli:files:mirror', 'cli:files:redirect', 'cli:files:restore', 'cli:files:sync',
  'cli:files:unmirror', 'cli:files:upload', 'cli:files:upload-raw', 'cli:forget:pglite-surface',
  'cli:founder:pglite-surface', 'cli:graph-query:pglite-surface',
  'cli:health:operation-cli', 'cli:import:pglite-surface',
  'cli:jobs:cancel', 'cli:jobs:delete', 'cli:jobs:prune',
  'cli:jobs:retry', 'cli:jobs:submit', 'cli:jobs:supervisor', 'cli:jobs:work',
  'cli:link:operation-cli', 'cli:lint:module-open-site', 'cli:lsd:pglite-surface',
  'cli:migrate:pglite-surface', 'cli:models:pglite-surface',
  'cli:onboard:pglite-surface', 'cli:orphans:module-open-site', 'cli:orphans:pglite-surface',
  'cli:purge-deleted:operation-cli', 'cli:put:operation-cli', 'cli:quarantine:pglite-surface',
  'cli:recall:module-open-site', 'cli:recall:pglite-surface', 'cli:reindex-code:module-open-site',
  'cli:reindex-code:pglite-surface', 'cli:reindex-frontmatter:module-open-site',
  'cli:reindex-frontmatter:pglite-surface', 'cli:reindex:module-open-site', 'cli:reindex:pglite-surface',
  'cli:repos:pglite-surface', 'cli:restore:operation-cli', 'cli:revert:operation-cli',
  'cli:salience:pglite-surface', 'cli:search:modes-reset',
  'cli:search:tune-apply', 'cli:serve:module-open-site', 'cli:serve:pglite-surface',
  'cli:skillopt:module-open-site', 'cli:skillopt:pglite-surface', 'cli:sources:add',
  'cli:sources:archive', 'cli:sources:attach', 'cli:sources:default', 'cli:sources:detach',
  'cli:sources:federate', 'cli:sources:harden', 'cli:sources:pull', 'cli:sources:purge',
  'cli:sources:remove', 'cli:sources:rename', 'cli:sources:restore', 'cli:sources:set-cr-mode',
  'cli:sources:tracked-branch', 'cli:sources:unfederate', 'cli:sources:unharden',
  'cli:sources:webhook', 'cli:stats:operation-cli', 'cli:status:pglite-surface',
  'cli:tag:operation-cli', 'cli:takes:add', 'cli:takes:extract', 'cli:takes:resolve',
  'cli:takes:revisit', 'cli:takes:supersede', 'cli:takes:update', 'cli:think:operation-cli',
  'cli:think:pglite-surface', 'cli:timeline-add:operation-cli', 'cli:transcripts:pglite-surface',
  'cli:unlink:operation-cli', 'cli:untag:operation-cli', 'cli:ze-switch:pglite-surface',
]);

const CLI_TYPED_GUARD_FAIL_FAST = new Set<string>([
  'cli:apply-migrations:pglite-surface',
  'cli:autopilot:module-open-site',
  'cli:autopilot:pglite-surface',
  'cli:claw-test:module-open-site',
  'cli:embed:maintenance',
  'cli:extract-conversation-facts:module-open-site',
  'cli:extract-conversation-facts:pglite-surface',
  'cli:extract:maintenance',
  'cli:frontmatter:module-open-site',
  'cli:init:module-open-site',
  'cli:integrity:module-open-site',
  'cli:mounts:module-open-site',
  'cli:reinit-pglite:no-sync',
  'cli:reinit-pglite:with-sync',
  'cli:repair-jsonb:module-open-site',
  'cli:schema:module-open-site',
  'cli:sync:maintenance',
  'cli:upgrade:pglite-surface',
  'cli:watch:module-open-site',
  'cli:watch:pglite-surface',
]);

const CLI_REMOTE_ALLOWED = new Set<string>([
  'cli:anomalies:operation-cli', 'cli:backlinks:operation-cli', 'cli:brain-skillpack:operation-cli',
  'cli:delete:operation-cli', 'cli:find-contradictions:operation-cli', 'cli:find-trajectory:operation-cli',
  'cli:get:operation-cli', 'cli:graph:operation-cli', 'cli:health:operation-cli', 'cli:history:operation-cli',
  'cli:link-sources:operation-cli', 'cli:link:operation-cli', 'cli:list:operation-cli', 'cli:put:operation-cli',
  'cli:query:operation-cli', 'cli:restore:operation-cli', 'cli:revert:operation-cli',
  'cli:salience:operation-cli', 'cli:search-by-image:operation-cli', 'cli:search:diagnose',
  'cli:search:modes', 'cli:search:modes-reset', 'cli:search:operation-cli', 'cli:search:stats',
  'cli:search:tune', 'cli:search:tune-apply', 'cli:skill:operation-cli', 'cli:skills:operation-cli',
  'cli:stats:operation-cli', 'cli:tag:operation-cli', 'cli:tags:operation-cli',
  'cli:takes-calibration:operation-cli', 'cli:takes-list:operation-cli', 'cli:takes-scorecard:operation-cli',
  'cli:takes-search:operation-cli', 'cli:think:operation-cli', 'cli:timeline-add:operation-cli',
  'cli:timeline:operation-cli', 'cli:unlink:operation-cli', 'cli:untag:operation-cli',
  'cli:volunteer-context:operation-cli', 'cli:whoami:operation-cli', 'cli:whoknows:operation-cli',
]);

export function resolvePgliteOwnerPolicy(input: PgliteOwnerPolicyInput): PgliteOwnerPolicy | null {
  if (input.target.kind === 'cli_command') return resolveCliCommandPolicy(input);
  if (input.target.kind === 'owner_startup') return resolveOwnerStartupPolicy(input);
  if (input.target.kind !== 'operation') return null;
  const op = operationsByName[input.target.name];
  if (!op) return null;

  const localOnly = op.localOnly === true;
  const remoteCaller = input.caller === 'mcp-stdio' || input.caller === 'mcp-http';
  const filesystemSensitive = input.target.name.startsWith('file_') || input.target.name === 'sync_brain';
  const remoteAllowed = !(remoteCaller && localOnly);
  const behaviorClass: PgliteOwnerBehaviorClass = !remoteAllowed
    ? 'typed_guard_fail_fast'
    : op.scope === 'read'
      ? 'broker_success_read'
      : 'serialized_owner_mutation';

  return {
    surfaceId: input.surfaceId,
    target: input.target,
    behaviorClass,
    allowedCallers: remoteAllowed ? ['cli', 'mcp-stdio', 'mcp-http'] : ['cli'],
    remoteAllowed,
    localOnly,
    filesystemSensitive,
    requiresOwnerSerialization: behaviorClass === 'serialized_owner_mutation',
    ...(behaviorClass === 'typed_guard_fail_fast' ? { guardStatusWhenLiveOwner: 'local_only_remote_rejected' } : {}),
    noOwnerMode: input.caller === 'cli' ? 'direct_open_allowed' : 'not_applicable',
  };
}

function resolveCliCommandPolicy(input: PgliteOwnerPolicyInput): PgliteOwnerPolicy | null {
  if (input.target.kind !== 'cli_command') return null;
  const surfaceId = input.target.surfaceId || input.surfaceId;
  const behaviorClass = cliBehaviorClass(surfaceId);
  if (!behaviorClass) return null;

  const localOnly = !CLI_REMOTE_ALLOWED.has(surfaceId);
  const remoteCaller = input.caller === 'mcp-stdio' || input.caller === 'mcp-http';
  const remoteAllowed = !(remoteCaller && localOnly);
  const effectiveBehaviorClass: PgliteOwnerBehaviorClass = remoteAllowed ? behaviorClass : 'typed_guard_fail_fast';

  return {
    surfaceId,
    target: input.target,
    behaviorClass: effectiveBehaviorClass,
    allowedCallers: remoteAllowed ? ['cli'] : ['cli'],
    remoteAllowed,
    localOnly,
    filesystemSensitive: true,
    requiresOwnerSerialization: effectiveBehaviorClass === 'serialized_owner_mutation',
    ...(effectiveBehaviorClass === 'typed_guard_fail_fast' ? { guardStatusWhenLiveOwner: remoteAllowed ? 'live_owner_command_guard' : 'local_only_remote_rejected' } : {}),
    noOwnerMode: input.caller === 'cli' ? 'direct_open_allowed' : 'not_applicable',
  };
}

function cliBehaviorClass(surfaceId: string): PgliteOwnerBehaviorClass | null {
  if (CLI_BROKER_SUCCESS_READ.has(surfaceId)) return 'broker_success_read';
  if (CLI_SERIALIZED_OWNER_MUTATION.has(surfaceId)) return 'serialized_owner_mutation';
  if (CLI_TYPED_GUARD_FAIL_FAST.has(surfaceId)) return 'typed_guard_fail_fast';
  return null;
}

function resolveOwnerStartupPolicy(input: PgliteOwnerPolicyInput): PgliteOwnerPolicy | null {
  if (input.target.kind !== 'owner_startup') return null;
  const behaviorClass = input.target.surfaceId === 'serve:duplicate-owner-start'
    ? 'typed_guard_fail_fast'
    : input.target.surfaceId === 'serve:http:owner-startup' || input.target.surfaceId === 'serve:stdio:owner-startup'
      ? 'serialized_owner_mutation'
      : null;
  if (!behaviorClass) return null;
  return {
    surfaceId: input.target.surfaceId,
    target: input.target,
    behaviorClass,
    allowedCallers: ['cli'],
    remoteAllowed: false,
    localOnly: false,
    filesystemSensitive: false,
    requiresOwnerSerialization: behaviorClass === 'serialized_owner_mutation',
    ...(behaviorClass === 'typed_guard_fail_fast' ? { guardStatusWhenLiveOwner: 'duplicate_owner_start_blocked' } : {}),
    noOwnerMode: input.caller === 'cli' ? 'direct_open_allowed' : 'not_applicable',
  };
}
