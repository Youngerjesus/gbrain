import type { BrainEngine } from './engine.ts';
import { operations } from './operations.ts';
import { resolveSourceId } from './source-resolver.ts';
import { dispatchToolCall, buildOperationContext, validateParams } from '../mcp/dispatch.ts';
import { getBrainHotMemoryMeta } from './facts/meta-hook.ts';
import type { OperationIpcRequest } from './pglite-operation-ipc.ts';

export async function dispatchBrokeredOperation(
  engine: BrainEngine,
  request: OperationIpcRequest,
): Promise<{ ok: true; result: unknown } | { ok: false; status: 'invalid_request' | 'handler_error'; message: string }> {
  const op = operations.find((candidate) => candidate.name === request.operation);
  if (!op) return { ok: false, status: 'invalid_request', message: 'Unknown brokered operation.' };

  if (request.caller === 'mcp-stdio') {
    return {
      ok: true,
      result: await dispatchToolCall(engine, request.operation, request.params, {
        remote: true,
        takesHoldersAllowList: ['world'],
        sourceId: typeof request.context.sourceId === 'string' ? request.context.sourceId : process.env.GBRAIN_SOURCE || 'default',
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
    return { ok: true, result: await op.handler(ctx, request.params) };
  } catch {
    return { ok: false, status: 'handler_error', message: 'Brokered operation failed.' };
  }
}

async function resolveBrokeredCliSourceId(
  engine: BrainEngine,
  request: OperationIpcRequest,
): Promise<string> {
  const explicit = (request.params.source as string | undefined) ?? null;
  const cwd = typeof request.context.cwd === 'string' ? request.context.cwd : process.cwd();
  const envSourceId = typeof request.context.envSourceId === 'string' ? request.context.envSourceId : null;
  return resolveSourceId(engine, explicit ?? envSourceId, cwd);
}
