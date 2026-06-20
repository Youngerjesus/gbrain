import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import type { BrainEngine } from '../core/engine.ts';
import { operations } from '../core/operations.ts';
import type { AuthInfo } from '../core/operations.ts';
import { VERSION } from '../version.ts';
import { buildToolDefs } from './tool-defs.ts';
import { dispatchToolCall, validateParams, buildOperationContext } from './dispatch.ts';
import { getBrainHotMemoryMeta } from '../core/facts/meta-hook.ts';
import { loadConfig } from '../core/config.ts';
import { assertValidSourceId } from '../core/source-id.ts';
import {
  resolveSocketPath,
  startResolveIpcServer,
  cleanupStaleSocket,
} from '../core/context/resolve-ipc.ts';
import { resolveEntitiesToPointers, logDeliveredReflexPointers } from '../core/context/retrieval-reflex.ts';
import {
  OPERATION_IPC_UNAVAILABLE,
  forwardOperationViaIpc,
  operationSocketPath,
  startPgliteOperationIpcServer,
} from '../core/pglite-operation-ipc.ts';
import { dispatchBrokeredOperation } from './pglite-operation-dispatch.ts';

export const GBRAIN_FEDERATED_READ_ENV = 'GBRAIN_FEDERATED_READ';
const remoteMcpOperations = operations.filter((op) => !op.localOnly);

export interface StdioSourceScope {
  sourceId: string;
  allowedSources?: string[];
}

export function parseStdioFederatedRead(raw: string | undefined): string[] | undefined {
  if (!raw || raw.trim().length === 0) return undefined;
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(',')) {
    const sourceId = part.trim();
    if (!sourceId) continue;
    try {
      assertValidSourceId(sourceId);
    } catch (error) {
      throw new Error(`${GBRAIN_FEDERATED_READ_ENV} contains invalid source id ${JSON.stringify(sourceId)}: ${(error as Error).message}`);
    }
    if (!seen.has(sourceId)) {
      seen.add(sourceId);
      out.push(sourceId);
    }
  }
  return out.length > 0 ? out : undefined;
}

export function resolveStdioSourceScope(env: { [key: string]: string | undefined } = process.env): StdioSourceScope {
  const sourceId = env.GBRAIN_SOURCE || 'default';
  assertValidSourceId(sourceId);
  const allowedSources = parseStdioFederatedRead(env[GBRAIN_FEDERATED_READ_ENV]);
  return {
    sourceId,
    ...(allowedSources ? { allowedSources } : {}),
  };
}

function stdioAuthForScope(scope: StdioSourceScope): AuthInfo | undefined {
  if (!scope.allowedSources) return undefined;
  return {
    token: 'stdio',
    clientId: 'stdio',
    clientName: 'stdio',
    scopes: [],
    sourceId: scope.sourceId,
    allowedSources: scope.allowedSources,
  };
}

export async function startMcpServer(engine: BrainEngine) {
  const stdioSourceScope = resolveStdioSourceScope(process.env);
  const stdioAuth = stdioAuthForScope(stdioSourceScope);
  const server = new Server(
    { name: 'gbrain', version: VERSION },
    { capabilities: { tools: {} } },
  );

  // Generate tool definitions from operations. Extracted to buildToolDefs so
  // the subagent tool registry (v0.15+) can call the same mapper against a
  // filtered OPERATIONS subset instead of duplicating this shape.
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: buildToolDefs(remoteMcpOperations),
  }));

  // Dispatch tool calls via shared dispatch.ts (parity with HTTP transport).
  // MCP stdio callers are remote/untrusted; dispatch defaults remote=true.
  // The MCP SDK's response type widened in 1.29 to allow a managed-task wrapper;
  // gbrain ops are synchronous, so we return the legacy `{ content, isError? }`
  // shape and cast through `any` (the SDK accepts it via the ServerResult union).
  server.setRequestHandler(CallToolRequestSchema, async (request: any): Promise<any> => {
    const { name, arguments: params } = request.params;
    // v0.28: stdio MCP has no per-token auth (local pipe). Default the
    // takes-holder allow-list to ['world'] so agent-facing callers don't
    // see private hunches via takes_list / takes_search / query. Operators
    // who want stdio to see everything should call ops directly via
    // `gbrain call <op>` (sets remote=false in src/cli.ts).
    return dispatchToolCall(engine, name, params, {
      remote: true,
      takesHoldersAllowList: ['world'],
      // v0.31: source defaults to 'default' for stdio (no per-token scope).
      // Operators who want a different source on stdio MCP should set
      // GBRAIN_SOURCE in the env or use --source via `gbrain call`.
      sourceId: stdioSourceScope.sourceId,
      ...(stdioAuth ? { auth: stdioAuth } : {}),
      // v0.31 (eD3): _meta.brain_hot_memory injection so Claude Desktop /
      // Code see the brain's relevant hot memory automatically alongside
      // every tool-call response. Best-effort; absorbs errors.
      metaHook: getBrainHotMemoryMeta,
    });
  });

  let operationServer: import('node:net').Server | null = null;
  let operationSocket: string | null = null;
  try {
    const cfg = loadConfig();
    if (cfg?.engine === 'pglite' && cfg.database_path) {
      operationSocket = operationSocketPath(cfg.database_path);
      operationServer = await startPgliteOperationIpcServer(operationSocket, (req) =>
        dispatchBrokeredOperation(engine, req),
        { onDiagnostic: emitOperationBrokerDiagnostic },
      );
    }
  } catch {
    /* operation IPC is best-effort; direct owner serve remains available */
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Retrieval Reflex (#1981, D9=C): on a PGLite brain, serve owns the single
  // connection, so the context engine resolves salient entities THROUGH us over
  // a local unix socket rather than opening a second (impossible) connection.
  // Best-effort; failure to bind never blocks the MCP server.
  let resolveServer: import('node:net').Server | null = null;
  let resolveSocket: string | null = null;
  try {
    const cfg = loadConfig();
    if (cfg?.engine === 'pglite' && cfg.database_path) {
      resolveSocket = resolveSocketPath(cfg.database_path);
      resolveServer = await startResolveIpcServer(
        resolveSocket,
        (req) => {
          const explicitSourceId = typeof req.sourceId === 'string' && req.sourceId.length > 0 ? req.sourceId : null;
          return resolveEntitiesToPointers(
            engine,
            explicitSourceId || stdioSourceScope.sourceId,
            req.candidates ?? [],
            {
              priorContextText: req.priorContextText,
              maxPointers: req.maxPointers,
              suppression: req.suppression,
              ...(!explicitSourceId && stdioSourceScope.allowedSources ? { sourceIds: stdioSourceScope.allowedSources } : {}),
            },
          );
        },
        // The IPC resolve path IS the ambient reflex channel. Logging happens
        // at DELIVERY (post-write), not inside the resolver — a block the
        // client's 250ms budget abandoned was never injected, and counting it
        // would corrupt the volunteered-vs-used precision stats (red-team).
        (block) => logDeliveredReflexPointers(engine, block.pointers),
      );
    }
  } catch {
    /* resolve IPC is best-effort; never block serve */
  }

  // Exit cleanly when MCP client disconnects (stdin EOF) or on signals.
  // Without this, orphaned serve processes accumulate and contend for the
  // PGLite write lock, causing ingest jobs (email-sync) to time out.
  let shuttingDown = false;
  const shutdown = (reason: string, code = 0) => {
    if (shuttingDown) return;
    shuttingDown = true;
    process.stderr.write(`[gbrain-serve] shutdown: ${reason}\n`);
    try { operationServer?.close(); } catch { /* noop */ }
    try { resolveServer?.close(); } catch { /* noop */ }
    if (resolveSocket) cleanupStaleSocket(resolveSocket);
    Promise.resolve(engine.disconnect?.())
      .catch(() => {})
      .finally(() => process.exit(code));
  };
  // v0.34.1 (#870): when MCP_STDIO=1, the wrapping gateway (OpenClaw's
  // bundle-mcp layer, others) often pipes the JSON-RPC handshake then
  // closes its stdin half. Treating that as a permanent disconnect kills
  // the server before the first tool call arrives. Signal handlers and
  // transport.onclose still cover the legitimate shutdown paths.
  if (process.env.MCP_STDIO !== '1') {
    process.stdin.on('end', () => shutdown('stdin end'));
    process.stdin.on('close', () => shutdown('stdin close'));
  }
  // @ts-ignore — SDK exposes onclose on transport
  transport.onclose = () => shutdown('transport close');
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGHUP', () => shutdown('SIGHUP'));
}

function emitOperationBrokerDiagnostic(event: { status: string; socketPath: string }): void {
  if (event.status === 'stale_socket_recovered') {
    console.error(`PGLite owner broker recovered stale operation socket: ${event.socketPath}`);
  }
}

export async function startMcpOperationProxyServer(socketPath: string): Promise<void> {
  const stdioSourceScope = resolveStdioSourceScope(process.env);
  const stdioAuth = stdioAuthForScope(stdioSourceScope);
  const server = new Server(
    { name: 'gbrain', version: VERSION },
    { capabilities: { tools: {} } },
  );
  const brokerOperationNames = new Set(operations.filter((op) => !op.localOnly).map((op) => op.name));
  const brokerOps = operations.filter((op) => brokerOperationNames.has(op.name));

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: buildToolDefs(brokerOps),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request: any): Promise<any> => {
    const { name, arguments: params } = request.params;
    if (!brokerOperationNames.has(name)) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ error: 'unknown_tool', message: `Unknown tool: ${name}` }, null, 2) }],
        isError: true,
      };
    }

    const response = await forwardOperationViaIpc(socketPath, {
      protocolVersion: 1,
      requestId: `mcp-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      caller: 'mcp-stdio',
      operation: name,
      class: 'interactive',
      priority: 100,
      params: params ?? {},
      context: {
        remote: true,
        takesHoldersAllowList: ['world'],
        sourceId: stdioSourceScope.sourceId,
        ...(stdioAuth ? { auth: stdioAuth } : {}),
        output: 'json',
      },
    });

    if (response === OPERATION_IPC_UNAVAILABLE) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ error: 'owner_unreachable', message: 'PGLite owner broker is not reachable.' }, null, 2) }],
        isError: true,
      };
    }
    if (!response.ok) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ error: response.status, message: response.message }, null, 2) }],
        isError: true,
      };
    }
    if (isToolResult(response.result)) return response.result;
    return { content: [{ type: 'text', text: JSON.stringify(response.result, null, 2) }] };
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

function isToolResult(value: unknown): value is { content: { type: 'text'; text: string }[]; isError?: boolean; _meta?: Record<string, unknown> } {
  return Boolean(value && typeof value === 'object' && Array.isArray((value as any).content));
}

// Backward compat: used by `gbrain call` command (trusted local path).
// v0.31.8 (D22): accept opts.sourceId so `gbrain call --source X <op> <json>`
// can scope the op handler to that source. resolveSourceId() in call.ts is
// the upstream resolver; this layer just passes the resolved id through.
export async function handleToolCall(
  engine: BrainEngine,
  tool: string,
  params: Record<string, unknown>,
  opts?: { sourceId?: string },
): Promise<unknown> {
  const op = operations.find(o => o.name === tool);
  if (!op) throw new Error(`Unknown tool: ${tool}`);

  const validationError = validateParams(op, params);
  if (validationError) throw new Error(validationError);

  const ctx = buildOperationContext(engine, params, {
    remote: false,
    logger: { info: console.log, warn: console.warn, error: console.error },
    ...(opts?.sourceId ? { sourceId: opts.sourceId } : {}),
  });

  return op.handler(ctx, params);
}
