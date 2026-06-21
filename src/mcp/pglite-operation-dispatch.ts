import type { BrainEngine } from '../core/engine.ts';
import { operations } from '../core/operations.ts';
import type { AuthInfo } from '../core/operations.ts';
import { resolveSourceId } from '../core/source-resolver.ts';
import { dispatchToolCall, buildOperationContext, validateParams } from './dispatch.ts';
import { getBrainHotMemoryMeta } from '../core/facts/meta-hook.ts';
import type { OperationIpcContext, OperationIpcRequest } from '../core/pglite-operation-ipc.ts';
import { resolvePgliteOwnerPolicy } from '../core/pglite-owner-policy.ts';
import { dispatchBrokeredCliCommand } from './pglite-cli-command-dispatch.ts';
import { withGatewayEnvOverlay } from '../core/ai/gateway.ts';

export async function dispatchBrokeredOperation(
  engine: BrainEngine,
  request: OperationIpcRequest,
): Promise<{ ok: true; result: unknown } | { ok: false; status: 'invalid_request' | 'handler_error' | 'local_only_remote_rejected'; message: string }> {
  if (request.operation === '__cli_command__') {
    return dispatchBrokeredCliCommand(engine, request);
  }

  const op = operations.find((candidate) => candidate.name === request.operation);
  if (!op) return { ok: false, status: 'invalid_request', message: 'Unknown brokered operation.' };

  if (request.caller === 'mcp-stdio') {
    const policy = resolvePgliteOwnerPolicy({
      surfaceId: `broker:${request.operation}:mcp-stdio`,
      target: { kind: 'operation', name: request.operation },
      caller: 'mcp-stdio',
    });
    if (policy?.behaviorClass === 'typed_guard_fail_fast') {
      return {
        ok: false,
        status: 'local_only_remote_rejected',
        message: `Operation ${request.operation} is localOnly and cannot be called by remote MCP clients.`,
      };
    }
    return {
      ok: true,
      result: await dispatchToolCall(engine, request.operation, request.params, {
        remote: true,
        takesHoldersAllowList: ['world'],
        sourceId: typeof request.context.sourceId === 'string' ? request.context.sourceId : process.env.GBRAIN_SOURCE || 'default',
        auth: authFromContext(request.context),
        metaHook: getBrainHotMemoryMeta,
      }),
    };
  }

  const validationError = validateParams(op, request.params);
  if (validationError) return { ok: false, status: 'invalid_request', message: validationError };

  try {
    const ctx = buildOperationContext(engine, request.params, {
      remote: false,
      logger: { info: console.log, warn: console.warn, error: console.error },
      sourceId: await resolveBrokeredCliSourceId(engine, request),
    });
    const result = await withGatewayEnvOverlay(request.context.callerEnv, () =>
      op.handler(ctx, request.params),
    );
    return { ok: true, result };
  } catch {
    return { ok: false, status: 'handler_error', message: 'Brokered operation failed.' };
  }
}

async function resolveBrokeredCliSourceId(
  engine: BrainEngine,
  request: OperationIpcRequest,
): Promise<string> {
  const explicit = (request.params.source as string | undefined) ?? null;
  if (!explicit && typeof request.context.sourceId === 'string') return request.context.sourceId;
  const cwd = typeof request.context.cwd === 'string' ? request.context.cwd : process.cwd();
  const envSourceId = typeof request.context.envSourceId === 'string' ? request.context.envSourceId : null;
  return resolveSourceId(engine, explicit ?? envSourceId, cwd);
}

function authFromContext(context: OperationIpcContext): AuthInfo | undefined {
  const auth = context.auth;
  if (!auth || typeof auth !== 'object' || Array.isArray(auth)) return undefined;
  const candidate = auth as Partial<AuthInfo>;
  if (typeof candidate.token !== 'string') return undefined;
  if (typeof candidate.clientId !== 'string') return undefined;
  if (!Array.isArray(candidate.scopes)) return undefined;
  if (candidate.sourceId !== undefined && typeof candidate.sourceId !== 'string') return undefined;
  if (candidate.allowedSources !== undefined && !Array.isArray(candidate.allowedSources)) return undefined;
  return {
    token: candidate.token,
    clientId: candidate.clientId,
    ...(typeof candidate.clientName === 'string' ? { clientName: candidate.clientName } : {}),
    scopes: candidate.scopes.filter((scope): scope is string => typeof scope === 'string'),
    ...(typeof candidate.expiresAt === 'number' ? { expiresAt: candidate.expiresAt } : {}),
    ...(typeof candidate.sourceId === 'string' ? { sourceId: candidate.sourceId } : {}),
    ...(candidate.allowedSources
      ? { allowedSources: candidate.allowedSources.filter((source): source is string => typeof source === 'string') }
      : {}),
  };
}
