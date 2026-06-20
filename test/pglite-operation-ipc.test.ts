import { afterEach, describe, expect, test } from 'bun:test';
import { mkdtempSync, rmSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import net from 'node:net';
import {
  OPERATION_IPC_UNAVAILABLE,
  forwardOperationViaIpc,
  operationSocketPath,
  releaseOperationStartup,
  startPgliteOperationIpcServer,
  tryAcquireOperationStartup,
  type OperationIpcRequest,
} from '../src/core/pglite-operation-ipc.ts';

const servers: Array<{ close: () => void }> = [];

afterEach(() => {
  for (const s of servers.splice(0)) {
    try { s.close(); } catch { /* noop */ }
  }
});

function tmpDir(): string {
  return mkdtempSync(join(tmpdir(), 'gbrain-op-ipc-'));
}

function req(id: string, operation: 'query' | 'search' | 'think', priority = 100): OperationIpcRequest {
  return {
    protocolVersion: 1,
    requestId: id,
    caller: 'cli',
    operation,
    class: 'interactive',
    priority,
    params: operation === 'think' ? { question: `q-${id}` } : { query: `q-${id}` },
    context: { remote: false, sourceId: 'default', output: 'json' },
  };
}

describe('PGLite operation IPC', () => {
  test('round-trips through an injected owner handler and echoes broker diagnostics', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    const seen: string[] = [];
    const server = await startPgliteOperationIpcServer(sock, async (r) => {
      seen.push(r.requestId);
      return { ok: true, result: { operation: r.operation, params: r.params } };
    });
    expect(server).not.toBeNull();
    servers.push(server!);

    const out = await forwardOperationViaIpc(sock, req('r1', 'query'));
    expect(out).not.toBe(OPERATION_IPC_UNAVAILABLE);
    expect(out).toMatchObject({
      ok: true,
      status: 'served',
      requestId: 'r1',
      ownerPid: process.pid,
    });
    expect((out as any).result.operation).toBe('query');
    expect(seen).toEqual(['r1']);
    rmSync(dir, { recursive: true, force: true });
  });

  test('absent socket returns unavailable instead of throwing', async () => {
    const dir = tmpDir();
    const out = await forwardOperationViaIpc(operationSocketPath(dir), req('missing', 'search'));
    expect(out).toBe(OPERATION_IPC_UNAVAILABLE);
    rmSync(dir, { recursive: true, force: true });
  });

  test('interactive priority beats lower-priority queued work', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    const order: string[] = [];
    let releaseFirst: (() => void) | null = null;
    const firstGate = new Promise<void>((resolve) => { releaseFirst = resolve; });
    const server = await startPgliteOperationIpcServer(sock, async (r) => {
      order.push(r.requestId);
      if (r.requestId === 'slow') await firstGate;
      return { ok: true, result: { id: r.requestId } };
    });
    expect(server).not.toBeNull();
    servers.push(server!);

    const slow = forwardOperationViaIpc(sock, { ...req('slow', 'query', 50), class: 'maintenance' });
    await new Promise((resolve) => setTimeout(resolve, 20));
    const low = forwardOperationViaIpc(sock, { ...req('low', 'query', 10), class: 'maintenance' });
    const high = forwardOperationViaIpc(sock, req('high', 'search', 100));
    releaseFirst!();

    await Promise.all([slow, low, high]);
    expect(order).toEqual(['slow', 'high', 'low']);
    rmSync(dir, { recursive: true, force: true });
  });

  test('oversize or malformed responses fail as protocol_error without echoing request params', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    const privateQuery = 'PRIVATE_QUERY_SENTINEL_DO_NOT_LOG';
    const server = await startPgliteOperationIpcServer(sock, async () => {
      throw new Error(`handler failed for ${privateQuery}`);
    });
    expect(server).not.toBeNull();
    servers.push(server!);

    const out = await forwardOperationViaIpc(sock, {
      ...req('private', 'query'),
      params: { query: privateQuery },
    });
    expect(out).not.toBe(OPERATION_IPC_UNAVAILABLE);
    expect(out).toMatchObject({ ok: false, status: 'handler_error', requestId: 'private' });
    expect(JSON.stringify(out)).not.toContain(privateQuery);
    rmSync(dir, { recursive: true, force: true });
  });

  test('server start does not unlink a live socket it cannot own', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    const s1 = await startPgliteOperationIpcServer(sock, async () => ({ ok: true, result: null }));
    expect(s1).not.toBeNull();
    servers.push(s1!);

    const s2 = await startPgliteOperationIpcServer(sock, async () => ({ ok: true, result: null }));
    expect(s2).toBeNull();
    expect(existsSync(sock)).toBe(true);
    rmSync(dir, { recursive: true, force: true });
  });

  test('server start reports stale socket recovery as a diagnostic status', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    writeFileSync(sock, 'stale owner socket placeholder');
    const diagnostics: unknown[] = [];

    const server = await startPgliteOperationIpcServer(
      sock,
      async () => ({ ok: true, result: null }),
      { onDiagnostic: (event) => diagnostics.push(event) },
    );
    expect(server).not.toBeNull();
    servers.push(server!);

    expect(server!.operationIpcStartupStatus).toBe('stale_socket_recovered');
    expect(diagnostics).toEqual([{ status: 'stale_socket_recovered', socketPath: sock }]);
    const out = await forwardOperationViaIpc(sock, req('after-stale-recovery', 'query'));
    expect(out).toMatchObject({ ok: true, status: 'served', requestId: 'after-stale-recovery' });
    rmSync(dir, { recursive: true, force: true });
  });

  test('broker timeout after request send reports completion_unknown', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const server = await startPgliteOperationIpcServer(sock, async () => {
      await gate;
      return { ok: true, result: null };
    });
    expect(server).not.toBeNull();
    servers.push(server!);

    const out = await forwardOperationViaIpc(sock, req('timeout-started', 'think'), { brokerTimeoutMs: 20 });
    release();

    expect(out).not.toBe(OPERATION_IPC_UNAVAILABLE);
    expect(out).toMatchObject({ ok: false, status: 'completion_unknown', requestId: 'timeout-started' });
    rmSync(dir, { recursive: true, force: true });
  });

  test('closed clients are removed from the queue before handler execution', async () => {
    const dir = tmpDir();
    const sock = operationSocketPath(dir);
    let releaseFirst!: () => void;
    const firstGate = new Promise<void>((resolve) => { releaseFirst = resolve; });
    const handled: string[] = [];
    const server = await startPgliteOperationIpcServer(sock, async (r) => {
      handled.push(r.requestId);
      if (r.requestId === 'slow') await firstGate;
      return { ok: true, result: { id: r.requestId } };
    });
    expect(server).not.toBeNull();
    servers.push(server!);

    const slow = forwardOperationViaIpc(sock, req('slow', 'query'));
    await new Promise((resolve) => setTimeout(resolve, 20));

    const raw = net.createConnection(sock);
    await new Promise<void>((resolve) => raw.once('connect', resolve));
    raw.write(`${JSON.stringify(req('dropped', 'think'))}\n`);
    raw.destroy();

    await new Promise((resolve) => setTimeout(resolve, 20));
    releaseFirst();
    await slow;
    await new Promise((resolve) => setTimeout(resolve, 30));

    expect(handled).toEqual(['slow']);
    rmSync(dir, { recursive: true, force: true });
  });

  test('startup election grants one owner and preserves a live starter', () => {
    const dir = tmpDir();
    const h1 = tryAcquireOperationStartup(dir);
    const h2 = tryAcquireOperationStartup(dir);
    expect(h1).not.toBeNull();
    expect(h2).toBeNull();
    releaseOperationStartup(h1);
    expect(tryAcquireOperationStartup(dir)).not.toBeNull();
    rmSync(dir, { recursive: true, force: true });
  });

  test('startup election recovers a stale starter', () => {
    const dir = tmpDir();
    const lockDir = join(dir, '.gbrain-operation-starting');
    mkdirSync(lockDir, { recursive: true });
    writeFileSync(join(lockDir, 'lock'), JSON.stringify({
      pid: 999999999,
      started_at: Date.now() - 60_000,
      token: 'dead',
    }));

    const h = tryAcquireOperationStartup(dir, { staleMs: 1 });
    expect(h).not.toBeNull();
    releaseOperationStartup(h);
    rmSync(dir, { recursive: true, force: true });
  });
});
