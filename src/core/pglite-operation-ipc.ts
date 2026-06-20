import { chmodSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, unlinkSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import net from 'net';

export const OPERATION_IPC_UNAVAILABLE = Symbol.for('gbrain.operationIpc.unavailable');

export type OperationIpcCaller = 'cli' | 'mcp-stdio';
export type OperationIpcOperation = 'query' | 'search' | 'think';
export type OperationIpcClass = 'interactive' | 'maintenance';
export type OperationIpcStatus =
  | 'served'
  | 'owner_unreachable'
  | 'lock_safety_blocked'
  | 'broker_timeout'
  | 'completion_unknown'
  | 'stale_socket_recovered'
  | 'invalid_request'
  | 'protocol_error'
  | 'handler_error';

export interface OperationIpcContext {
  remote: boolean;
  sourceId?: string;
  output?: 'json' | 'text';
  [key: string]: unknown;
}

export interface OperationIpcRequest {
  protocolVersion: 1;
  requestId: string;
  caller: OperationIpcCaller;
  operation: OperationIpcOperation;
  class: OperationIpcClass;
  priority: number;
  params: Record<string, unknown>;
  context: OperationIpcContext;
}

export type OperationIpcHandlerResult =
  | { ok: true; result: unknown }
  | { ok: false; status?: OperationIpcStatus; message?: string; result?: unknown };

export type OperationIpcResponse =
  | {
      ok: true;
      status: 'served';
      requestId: string;
      ownerPid: number;
      queuedMs: number;
      servedMs: number;
      result: unknown;
    }
  | {
      ok: false;
      status: Exclude<OperationIpcStatus, 'served'>;
      requestId?: string;
      ownerPid?: number;
      queuedMs?: number;
      servedMs?: number;
      message: string;
      result?: unknown;
    };

export type OperationIpcForwardResult = OperationIpcResponse | typeof OPERATION_IPC_UNAVAILABLE;
export type OperationIpcHandler = (request: OperationIpcRequest) => Promise<OperationIpcHandlerResult> | OperationIpcHandlerResult;
export type OperationIpcStartupStatus = 'started' | 'stale_socket_recovered';
export interface OperationIpcDiagnostic {
  status: 'stale_socket_recovered';
  socketPath: string;
}

export type OperationIpcServer = net.Server & {
  operationIpcStartupStatus: OperationIpcStartupStatus;
};

export interface OperationStartupHandle {
  lockDir: string;
  token: string;
}

interface QueuedRequest {
  request: OperationIpcRequest;
  socket: net.Socket;
  enqueuedAt: number;
  sequence: number;
  closed: boolean;
}

const DEFAULT_CONNECT_TIMEOUT_MS = 800;
const DEFAULT_BROKER_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024;
const LIVE_SOCKET_PROBE_TIMEOUT_MS = 250;
const PRIORITY_DRAIN_WINDOW_MS = 5;
const VALID_OPERATIONS = new Set<OperationIpcOperation>(['query', 'search', 'think']);
const VALID_CALLERS = new Set<OperationIpcCaller>(['cli', 'mcp-stdio']);
const VALID_CLASSES = new Set<OperationIpcClass>(['interactive', 'maintenance']);
const STARTUP_LOCK_DIR = '.gbrain-operation-starting';
const STARTUP_LOCK_STALE_MS = 10_000;

export function operationSocketPath(dataDir: string): string {
  return join(dataDir, '.gbrain-operation.sock');
}

export function tryAcquireOperationStartup(dataDir: string, opts?: { staleMs?: number }): OperationStartupHandle | null {
  const lockDir = join(dataDir, STARTUP_LOCK_DIR);
  const token = `${process.pid}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
  const staleMs = opts?.staleMs ?? STARTUP_LOCK_STALE_MS;

  try {
    mkdirSync(lockDir, { recursive: false });
  } catch {
    try {
      const raw = JSON.parse(readFileSync(join(lockDir, 'lock'), 'utf-8'));
      const pid = typeof raw.pid === 'number' ? raw.pid : null;
      const startedAt = typeof raw.started_at === 'number' ? raw.started_at : 0;
      const alive = pid !== null && isPidAlive(pid);
      if (!alive || Date.now() - startedAt > staleMs) {
        rmSync(lockDir, { recursive: true, force: true });
        mkdirSync(lockDir, { recursive: false });
      } else {
        return null;
      }
    } catch {
      return null;
    }
  }

  try {
    writeFileSync(join(lockDir, 'lock'), JSON.stringify({
      pid: process.pid,
      started_at: Date.now(),
      token,
    }), { mode: 0o600 });
    return { lockDir, token };
  } catch {
    try { rmSync(lockDir, { recursive: true, force: true }); } catch { /* noop */ }
    return null;
  }
}

export function releaseOperationStartup(handle: OperationStartupHandle | null): void {
  if (!handle) return;
  try {
    const raw = JSON.parse(readFileSync(join(handle.lockDir, 'lock'), 'utf-8'));
    if (raw.token !== handle.token) return;
    rmSync(handle.lockDir, { recursive: true, force: true });
  } catch {
    try { rmSync(handle.lockDir, { recursive: true, force: true }); } catch { /* noop */ }
  }
}

export async function forwardOperationViaIpc(
  socketPath: string,
  request: OperationIpcRequest,
  opts?: {
    connectTimeoutMs?: number;
    brokerTimeoutMs?: number;
    maxResponseBytes?: number;
  }
): Promise<OperationIpcForwardResult> {
  if (!existsSync(socketPath)) return OPERATION_IPC_UNAVAILABLE;

  const connectTimeoutMs = opts?.connectTimeoutMs ?? DEFAULT_CONNECT_TIMEOUT_MS;
  const brokerTimeoutMs = opts?.brokerTimeoutMs ?? DEFAULT_BROKER_TIMEOUT_MS;
  const maxResponseBytes = opts?.maxResponseBytes ?? DEFAULT_MAX_RESPONSE_BYTES;

  return await new Promise<OperationIpcForwardResult>((resolve) => {
    const socket = net.createConnection(socketPath);
    let settled = false;
    let connected = false;
    let requestSent = false;
    let buffer = '';

    const settle = (value: OperationIpcForwardResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(connectTimer);
      clearTimeout(brokerTimer);
      socket.destroy();
      resolve(value);
    };

    const connectTimer = setTimeout(() => {
      settle(OPERATION_IPC_UNAVAILABLE);
    }, connectTimeoutMs);
    (connectTimer as { unref?: () => void }).unref?.();

    const brokerTimer = setTimeout(() => {
      settle({
        ok: false,
        status: requestSent ? 'completion_unknown' : 'broker_timeout',
        requestId: request.requestId,
        message: requestSent
          ? 'Operation broker timed out after accepting the request; completion is unknown.'
          : 'Operation broker timed out before accepting the request.',
      });
    }, brokerTimeoutMs);
    (brokerTimer as { unref?: () => void }).unref?.();

    socket.setEncoding('utf-8');
    socket.on('connect', () => {
      connected = true;
      clearTimeout(connectTimer);
      socket.write(`${JSON.stringify(request)}\n`);
      requestSent = true;
    });
    socket.on('data', (chunk) => {
      buffer += chunk;
      if (buffer.length > maxResponseBytes) {
        settle({
          ok: false,
          status: 'protocol_error',
          requestId: request.requestId,
          message: 'Operation broker response exceeded the maximum size.',
        });
        return;
      }
      const newline = buffer.indexOf('\n');
      if (newline === -1) return;
      const line = buffer.slice(0, newline);
      try {
        settle(JSON.parse(line) as OperationIpcResponse);
      } catch {
        settle({
          ok: false,
          status: 'protocol_error',
          requestId: request.requestId,
          message: 'Operation broker returned malformed JSON.',
        });
      }
    });
    socket.on('error', () => {
      settle(connected
        ? {
            ok: false,
            status: 'owner_unreachable',
            requestId: request.requestId,
            message: 'Operation broker connection failed before completion.',
          }
        : OPERATION_IPC_UNAVAILABLE);
    });
    socket.on('close', () => {
      if (settled) return;
      settle({
        ok: false,
        status: connected ? 'completion_unknown' : 'owner_unreachable',
        requestId: request.requestId,
        message: 'Operation broker closed the connection before returning a result.',
      });
    });
  });
}

export async function startPgliteOperationIpcServer(
  socketPath: string,
  handler: OperationIpcHandler,
  opts?: { onDiagnostic?: (event: OperationIpcDiagnostic) => void },
): Promise<OperationIpcServer | null> {
  mkdirSync(dirname(socketPath), { recursive: true });
  let startupStatus: OperationIpcStartupStatus = 'started';
  if (existsSync(socketPath)) {
    let before: ReturnType<typeof statSync> | null = null;
    try { before = statSync(socketPath); } catch { before = null; }
    const live = await canConnectToSocket(socketPath);
    if (live) return null;
    try {
      const stat = statSync(socketPath);
      if (before && (stat.dev !== before.dev || stat.ino !== before.ino)) return null;
      if (stat.isSocket() || stat.isFIFO() || stat.isFile()) unlinkSync(socketPath);
      else return null;
      startupStatus = 'stale_socket_recovered';
    } catch {
      return null;
    }
  }

  let processing = false;
  let sequence = 0;
  const queue: QueuedRequest[] = [];

  const server = net.createServer((socket) => {
    socket.setEncoding('utf-8');
    let buffer = '';
    socket.on('data', (chunk) => {
      buffer += chunk;
      const newline = buffer.indexOf('\n');
      if (newline === -1) return;
      const line = buffer.slice(0, newline);
      buffer = buffer.slice(newline + 1);

      let parsed: unknown;
      try {
        parsed = JSON.parse(line);
      } catch {
        writeResponse(socket, {
          ok: false,
          status: 'protocol_error',
          ownerPid: process.pid,
          message: 'Operation broker request was not valid JSON.',
        });
        return;
      }

      const validation = validateRequest(parsed);
      if (!validation.ok) {
        writeResponse(socket, validation.response);
        return;
      }

      const item: QueuedRequest = {
        request: validation.request,
        socket,
        enqueuedAt: Date.now(),
        sequence: sequence++,
        closed: false,
      };
      socket.once('close', () => { item.closed = true; });
      queue.push(item);
      void processQueue();
    });
  });

  const processQueue = async () => {
    if (processing) return;
    processing = true;
    try {
      while (queue.length > 0) {
        await new Promise((resolve) => setTimeout(resolve, PRIORITY_DRAIN_WINDOW_MS));
        queue.sort(compareQueuedRequests);
        const item = queue.shift()!;
        if (item.closed || item.socket.destroyed) continue;
        const startedAt = Date.now();
        try {
          const result = await handler(item.request);
          if (result.ok) {
            writeResponse(item.socket, {
              ok: true,
              status: 'served',
              requestId: item.request.requestId,
              ownerPid: process.pid,
              queuedMs: startedAt - item.enqueuedAt,
              servedMs: Date.now() - startedAt,
              result: result.result,
            });
          } else {
            writeResponse(item.socket, {
              ok: false,
              status: sanitizeFailureStatus(result.status),
              requestId: item.request.requestId,
              ownerPid: process.pid,
              queuedMs: startedAt - item.enqueuedAt,
              servedMs: Date.now() - startedAt,
              message: result.message ?? 'Operation broker handler returned a failure.',
              result: result.result,
            });
          }
        } catch {
          writeResponse(item.socket, {
            ok: false,
            status: 'handler_error',
            requestId: item.request.requestId,
            ownerPid: process.pid,
            queuedMs: startedAt - item.enqueuedAt,
            servedMs: Date.now() - startedAt,
            message: 'Operation broker handler failed.',
          });
        }
      }
    } finally {
      processing = false;
    }
  };

  return await new Promise<OperationIpcServer | null>((resolve) => {
    const onError = () => {
      server.removeListener('listening', onListening);
      resolve(null);
    };
    const onListening = () => {
      server.removeListener('error', onError);
      try { chmodSync(socketPath, 0o600); } catch { /* best-effort local socket hardening */ }
      const operationServer = server as OperationIpcServer;
      operationServer.operationIpcStartupStatus = startupStatus;
      if (startupStatus === 'stale_socket_recovered') {
        opts?.onDiagnostic?.({ status: 'stale_socket_recovered', socketPath });
      }
      resolve(operationServer);
    };
    server.once('error', onError);
    server.once('listening', onListening);
    server.listen(socketPath);
  });
}

function compareQueuedRequests(a: QueuedRequest, b: QueuedRequest): number {
  const priorityDiff = effectivePriority(b.request) - effectivePriority(a.request);
  if (priorityDiff !== 0) return priorityDiff;
  return a.sequence - b.sequence;
}

function effectivePriority(request: OperationIpcRequest): number {
  const classBoost = request.class === 'interactive' ? 1000 : 0;
  const finitePriority = Number.isFinite(request.priority) ? request.priority : 0;
  return classBoost + finitePriority;
}

function writeResponse(socket: net.Socket, response: OperationIpcResponse): void {
  try {
    socket.end(`${JSON.stringify(response)}\n`);
  } catch {
    socket.destroy();
  }
}

function sanitizeFailureStatus(status: OperationIpcStatus | undefined): Exclude<OperationIpcStatus, 'served'> {
  if (!status || status === 'served') return 'handler_error';
  return status;
}

function validateRequest(value: unknown): { ok: true; request: OperationIpcRequest } | { ok: false; response: OperationIpcResponse } {
  if (!value || typeof value !== 'object') {
    return invalidRequest('Operation broker request must be an object.');
  }
  const candidate = value as Partial<OperationIpcRequest>;
  if (candidate.protocolVersion !== 1) return invalidRequest('Unsupported operation broker protocol version.');
  if (typeof candidate.requestId !== 'string' || candidate.requestId.length === 0) return invalidRequest('Missing operation broker request id.');
  if (!VALID_CALLERS.has(candidate.caller as OperationIpcCaller)) return invalidRequest('Unsupported operation broker caller.');
  if (!VALID_OPERATIONS.has(candidate.operation as OperationIpcOperation)) return invalidRequest('Unsupported operation broker operation.');
  if (!VALID_CLASSES.has(candidate.class as OperationIpcClass)) return invalidRequest('Unsupported operation broker request class.');
  if (!Number.isFinite(candidate.priority)) return invalidRequest('Operation broker priority must be numeric.');
  if (!candidate.params || typeof candidate.params !== 'object' || Array.isArray(candidate.params)) return invalidRequest('Operation broker params must be an object.');
  if (!candidate.context || typeof candidate.context !== 'object' || Array.isArray(candidate.context)) return invalidRequest('Operation broker context must be an object.');
  if (typeof (candidate.context as OperationIpcContext).remote !== 'boolean') return invalidRequest('Operation broker context must include remote.');

  return { ok: true, request: candidate as OperationIpcRequest };
}

function invalidRequest(message: string): { ok: false; response: OperationIpcResponse } {
  return {
    ok: false,
    response: {
      ok: false,
      status: 'invalid_request',
      ownerPid: process.pid,
      message,
    },
  };
}

async function canConnectToSocket(socketPath: string): Promise<boolean> {
  return await new Promise<boolean>((resolve) => {
    const socket = net.createConnection(socketPath);
    let settled = false;
    const settle = (value: boolean) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      resolve(value);
    };
    const timer = setTimeout(() => settle(false), LIVE_SOCKET_PROBE_TIMEOUT_MS);
    (timer as { unref?: () => void }).unref?.();
    socket.once('connect', () => settle(true));
    socket.once('error', () => settle(false));
  });
}

function isPidAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}
