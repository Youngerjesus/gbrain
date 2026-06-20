import { afterEach, describe, expect, test } from 'bun:test';
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  operationSocketPath,
  releaseOperationStartup,
  startPgliteOperationIpcServer,
  tryAcquireOperationStartup,
  type OperationIpcRequest,
} from '../src/core/pglite-operation-ipc.ts';
import { createEngine } from '../src/core/engine-factory.ts';
import { dispatchBrokeredOperation } from '../src/mcp/pglite-operation-dispatch.ts';

const servers: Array<{ close: () => void }> = [];

afterEach(() => {
  for (const server of servers.splice(0)) {
    try { server.close(); } catch { /* noop */ }
  }
});

function makeHome(): { home: string; dbPath: string } {
  const home = mkdtempSync('/tmp/gbrain-cli-broker-');
  const dbPath = join(home, 'brain.db');
  mkdirSync(join(home, '.gbrain'), { recursive: true });
  mkdirSync(dbPath, { recursive: true });
  writeFileSync(join(home, '.gbrain', 'config.json'), JSON.stringify({
    engine: 'pglite',
    database_path: dbPath,
  }));
  return { home, dbPath };
}

function writeLiveLock(dbPath: string, command = 'test owner'): void {
  const lockDir = join(dbPath, '.gbrain-lock');
  mkdirSync(lockDir, { recursive: true });
  const now = Date.now();
  writeFileSync(join(lockDir, 'lock'), JSON.stringify({
    pid: process.pid,
    acquired_at: now,
    refreshed_at: now,
    command,
  }));
}

function writeCorruptLock(dbPath: string): void {
  const lockDir = join(dbPath, '.gbrain-lock');
  mkdirSync(lockDir, { recursive: true });
  writeFileSync(join(lockDir, 'lock'), '{not-json');
}

function runCli(
  args: string[],
  home: string,
  cwd = process.cwd(),
  env: Record<string, string> = {},
): Promise<{ stdout: string; stderr: string; status: number | null }> {
  return new Promise((resolve) => {
    const child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), ...args], {
      cwd,
      env: {
        ...process.env,
        NODE_ENV: 'test',
        GBRAIN_HOME: home,
        DATABASE_URL: '',
        GBRAIN_DATABASE_URL: '',
        ...env,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf-8');
    child.stderr.setEncoding('utf-8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (status) => resolve({ stdout, stderr, status }));
  });
}

function runCliBounded(
  args: string[],
  home: string,
  timeoutMs = 1500,
): Promise<{ stdout: string; stderr: string; status: number | null; timedOut: boolean }> {
  return new Promise((resolve) => {
    const child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), ...args], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        NODE_ENV: 'test',
        GBRAIN_HOME: home,
        DATABASE_URL: '',
        GBRAIN_DATABASE_URL: '',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
    }, timeoutMs);
    child.stdout.setEncoding('utf-8');
    child.stderr.setEncoding('utf-8');
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (status) => {
      clearTimeout(timer);
      resolve({ stdout, stderr, status, timedOut });
    });
  });
}

function waitForJsonLine(child: ReturnType<typeof spawn>, id: number, timeoutMs = 5000): Promise<any> {
  return new Promise((resolve, reject) => {
    let stdout = '';
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error(`timed out waiting for JSON-RPC response ${id}; stdout=${stdout}`));
    }, timeoutMs);
    const onData = (chunk: Buffer | string) => {
      stdout += chunk.toString();
      let idx: number;
      while ((idx = stdout.indexOf('\n')) !== -1) {
        const line = stdout.slice(0, idx).trim();
        stdout = stdout.slice(idx + 1);
        if (!line) continue;
        const msg = JSON.parse(line);
        if (msg.id === id) {
          cleanup();
          resolve(msg);
          return;
        }
      }
    };
    const onExit = () => {
      cleanup();
      reject(new Error(`child exited before JSON-RPC response ${id}`));
    };
    const cleanup = () => {
      clearTimeout(timer);
      child.stdout?.off('data', onData);
      child.off('exit', onExit);
    };
    child.stdout?.on('data', onData);
    child.once('exit', onExit);
  });
}

function sendJson(child: ReturnType<typeof spawn>, message: Record<string, unknown>): void {
  child.stdin?.write(`${JSON.stringify(message)}\n`);
}

describe('CLI PGLite operation broker routing', () => {
  const maintenanceCommands: Array<{ name: string; args: string[] }> = [
    { name: 'sync', args: ['sync', '--no-pull', '--no-embed', '--no-extract', '--yes', '--no-hard-deadline'] },
    { name: 'embed', args: ['embed', '--stale', '--dry-run'] },
    { name: 'extract', args: ['extract', '--stale', '--dry-run'] },
  ];

  function expectNoRawPgliteLockFailure(result: { stderr: string }): void {
    expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
    expect(result.stderr).not.toContain('Could not acquire PGLite lock');
  }

  function expectNoMisleadingMaintenanceSuccess(result: { stderr: string; stdout: string }): void {
    const combined = `${result.stdout}\n${result.stderr}`.toLowerCase();
    expect(combined).not.toContain('queued');
    expect(combined).not.toContain('completed');
    expect(combined).not.toContain('successfully run');
  }

  test('CLI-owned broker dispatch preserves MCP invalid_params envelope', async () => {
    const { home, dbPath } = makeHome();
    try {
      const engine = await createEngine({ engine: 'pglite', database_path: dbPath });
      await engine.connect({ engine: 'pglite', database_path: dbPath });
      await engine.initSchema();
      try {
        const result = await dispatchBrokeredOperation(engine, {
          protocolVersion: 1,
          requestId: 'invalid-mcp-search',
          caller: 'mcp-stdio',
          operation: 'search',
          class: 'interactive',
          priority: 100,
          params: {},
          context: { remote: true, sourceId: 'default', output: 'json' },
        });
        expect(result.ok).toBe(true);
        const tool = (result as any).result;
        expect(tool.isError).toBe(true);
        const body = JSON.parse(tool.content[0].text);
        expect(body.error).toBe('invalid_params');
      } finally {
        await engine.disconnect();
      }
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('five concurrent query callers proxy to the live owner without PGLite lock timeout', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const results = await Promise.all(
        Array.from({ length: 5 }, (_, i) => runCli(['query', `broker-test-${i}`], home)),
      );

      expect(results.map((r) => r.status)).toEqual([0, 0, 0, 0, 0]);
      for (const r of results) {
        expect(r.stdout).toContain('No results.');
        expect(r.stderr).not.toContain('Timed out waiting for PGLite lock');
      }
      expect(seen).toHaveLength(5);
      expect(seen.every((r) => r.operation === 'query')).toBe(true);
      expect(seen.every((r) => r.caller === 'cli')).toBe(true);
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('mixed concurrent query search and think callers proxy to the live owner', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        if (request.operation === 'think') {
          return {
            ok: true,
            result: {
              answer: 'brokered answer',
              gaps: [],
              modelUsed: 'test',
              pagesGathered: 0,
              takesGathered: 0,
              graphHits: 0,
              citations: [],
              warnings: [],
              saved_slug: null,
              evidence_inserted: 0,
            },
          };
        }
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const results = await Promise.all([
        runCli(['query', 'mixed-query-a'], home),
        runCli(['search', 'mixed-search-a'], home),
        runCli(['think', 'mixed think?', '--json'], home),
        runCli(['query', 'mixed-query-b'], home),
        runCli(['search', 'mixed-search-b'], home),
      ]);

      expect(results.map((r) => r.status)).toEqual([0, 0, 0, 0, 0]);
      for (const r of results) expect(r.stderr).not.toContain('Timed out waiting for PGLite lock');
      expect(seen.map((r) => r.operation).sort()).toEqual(['query', 'query', 'search', 'search', 'think']);
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('maintenance-like PGLite owner exposes broker for interactive callers', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath, 'gbrain sync');
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: request.operation === 'think'
          ? {
              answer: 'maintenance owner answer',
              gaps: [],
              modelUsed: 'test',
              pagesGathered: 0,
              takesGathered: 0,
              graphHits: 0,
              citations: [],
              warnings: [],
              saved_slug: null,
              evidence_inserted: 0,
            }
          : [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const [query, search, think] = await Promise.all([
        runCli(['query', 'maintenance-owner-query'], home),
        runCli(['search', 'maintenance-owner-search'], home),
        runCli(['think', 'maintenance owner think?', '--json'], home),
      ]);

      expect([query.status, search.status, think.status]).toEqual([0, 0, 0]);
      for (const result of [query, search, think]) expectNoRawPgliteLockFailure(result);
      expect(seen.map((r) => r.operation).sort()).toEqual(['query', 'search', 'think']);
      expect(seen.every((r) => r.class === 'interactive')).toBe(true);
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  }, 30_000);

  test('no-owner query search and think keep direct-open CLI behavior', async () => {
    const { home } = makeHome();
    try {
      const query = await runCli(['query', 'no-owner-query'], home);
      expect(query.status).toBe(0);
      expect(query.stdout).toContain('No results.');
      expect(query.stderr).not.toContain('PGLite owner broker error');
      expect(query.stderr).not.toContain('Timed out waiting for PGLite lock');

      const search = await runCli(['search', 'no-owner-search'], home);
      expect(search.status).toBe(0);
      expect(search.stdout).not.toContain('PGLite owner broker error');
      expect(search.stderr).not.toContain('PGLite owner broker error');
      expect(search.stderr).not.toContain('Timed out waiting for PGLite lock');

      const think = await runCli(['think', 'no owner think?', '--json'], home);
      expect(think.status).toBe(0);
      expect(think.stdout).toContain('"answer"');
      expect(think.stderr).not.toContain('PGLite owner broker error');
      expect(think.stderr).not.toContain('Timed out waiting for PGLite lock');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  }, 30_000);

  test('CLI caller reports owner_unreachable when a live owner lock has no broker socket', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeLiveLock(dbPath);

      const result = await runCli(['--timeout=300ms', 'query', 'owner-missing-socket'], home);

      expect(result.status).toBe(1);
      expect(result.stderr).toContain('owner_unreachable');
      expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
      expect(result.stderr).not.toContain('Could not acquire PGLite lock');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('CLI caller surfaces completion_unknown after the owner accepts but times out', async () => {
    const { home, dbPath } = makeHome();
    let release!: () => void;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    try {
      writeLiveLock(dbPath);
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async () => {
        await gate;
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const result = await runCli(['--timeout=20ms', 'query', 'completion-unknown'], home);
      release();

      expect(result.status).toBe(124);
      expect(result.stderr).toContain('completion_unknown');
      expect(result.stderr).toContain('completion is unknown');
      expect(result.stdout).not.toContain('No results.');
    } finally {
      release?.();
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('five simultaneous mixed CLI and MCP callers share the live owner broker', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      await waitForJsonLine(child, 1);
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      const mcpQuery = waitForJsonLine(child, 10);
      const mcpThink = waitForJsonLine(child, 11);
      sendJson(child, {
        jsonrpc: '2.0',
        id: 10,
        method: 'tools/call',
        params: { name: 'query', arguments: { query: 'mixed-mcp-query' } },
      });
      sendJson(child, {
        jsonrpc: '2.0',
        id: 11,
        method: 'tools/call',
        params: { name: 'think', arguments: { question: 'mixed mcp think' } },
      });

      const [cliQuery, cliSearch, cliThink, mcpQueryResult, mcpThinkResult] = await Promise.all([
        runCli(['query', 'mixed-cli-query'], home),
        runCli(['search', 'mixed-cli-search'], home),
        runCli(['think', 'mixed cli think?', '--json'], home),
        mcpQuery,
        mcpThink,
      ]);

      expect([cliQuery.status, cliSearch.status, cliThink.status]).toEqual([0, 0, 0]);
      expect(mcpQueryResult.error).toBeUndefined();
      expect(mcpThinkResult.error).toBeUndefined();
      expect(mcpQueryResult.result.content[0].text).toBe('[]');
      expect(mcpThinkResult.result.content[0].text).toBe('[]');
      expect(seen).toHaveLength(5);
      expect(new Set(seen.map((r) => r.caller))).toEqual(new Set(['cli', 'mcp-stdio']));
      expect(seen.map((r) => r.operation).sort()).toEqual(['query', 'query', 'search', 'think', 'think']);
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      rmSync(home, { recursive: true, force: true });
    }
  }, 30_000);

  test('brokered CLI requests carry caller cwd for owner-side source resolution', async () => {
    const { home, dbPath } = makeHome();
    const sourceDir = join(home, 'source-a');
    try {
      mkdirSync(sourceDir, { recursive: true });
      writeFileSync(join(sourceDir, '.gbrain-source'), 'source-a\n');
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      const result = await runCli(['query', 'source-context-test'], home, sourceDir);

      expect(result.status).toBe(0);
      expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
      expect(seen).toHaveLength(1);
      expect(seen[0].context.cwd).toBe(realpathSync(sourceDir));
      expect(seen[0].context).not.toHaveProperty('sourceId', 'default');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('corrupt lock state fails fast with lock_safety_blocked instead of direct PGLite open', async () => {
    const { home, dbPath } = makeHome();
    try {
      const lockDir = join(dbPath, '.gbrain-lock');
      mkdirSync(lockDir, { recursive: true });
      writeFileSync(join(lockDir, 'lock'), '{not-json');

      const result = await runCli(['query', 'lock-safety-test'], home);

      expect(result.status).toBe(1);
      expect(result.stderr).toContain('lock_safety_blocked');
      expect(result.stderr).not.toContain('owner_unreachable');
      expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  for (const command of maintenanceCommands) {
    test(`second ${command.name} maintenance caller defers under live PGLite owner`, async () => {
      const { home, dbPath } = makeHome();
      try {
        writeLiveLock(dbPath, 'gbrain sync');

        const result = await runCliBounded(command.args, home, 2000);

        expect(result.timedOut).toBe(false);
        expect(result.status).toBe(1);
        expect(result.stderr).toContain('maintenance_deferred');
        expect(result.stderr).toContain(`gbrain ${command.name}`);
        expectNoRawPgliteLockFailure(result);
        expectNoMisleadingMaintenanceSuccess(result);
      } finally {
        rmSync(home, { recursive: true, force: true });
      }
    }, 10_000);
  }

  test('maintenance caller reports owner_starting when startup election is held', async () => {
    const { home, dbPath } = makeHome();
    const startup = tryAcquireOperationStartup(dbPath);
    expect(startup).not.toBeNull();
    try {
      const result = await runCliBounded(['embed', '--stale', '--dry-run'], home, 2000);

      expect(result.timedOut).toBe(false);
      expect(result.status).toBe(1);
      expect(result.stderr).toContain('owner_starting');
      expectNoRawPgliteLockFailure(result);
      expectNoMisleadingMaintenanceSuccess(result);
    } finally {
      releaseOperationStartup(startup);
      rmSync(home, { recursive: true, force: true });
    }
  }, 10_000);

  test('maintenance caller fails fast on corrupt lock instead of opening PGLite', async () => {
    const { home, dbPath } = makeHome();
    try {
      writeCorruptLock(dbPath);

      const result = await runCliBounded(['extract', '--stale', '--dry-run'], home, 2000);

      expect(result.timedOut).toBe(false);
      expect(result.status).toBe(1);
      expect(result.stderr).toContain('lock_safety_blocked');
      expectNoRawPgliteLockFailure(result);
      expectNoMisleadingMaintenanceSuccess(result);
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  }, 10_000);

  for (const command of maintenanceCommands) {
    test(`no-owner ${command.name} maintenance caller reaches direct command path`, async () => {
      const { home } = makeHome();
      try {
        const result = await runCliBounded(command.args, home, 5000);

        expect(result.timedOut).toBe(false);
        expect(result.stderr).not.toContain('maintenance_deferred');
        expect(result.stderr).not.toContain('owner_starting');
        expect(result.stderr).not.toContain('lock_safety_blocked');
        expectNoRawPgliteLockFailure(result);
      } finally {
        rmSync(home, { recursive: true, force: true });
      }
    }, 15_000);
  }

  test('stdio MCP serve fails fast on corrupt lock instead of opening or cleaning PGLite', async () => {
    const { home, dbPath } = makeHome();
    try {
      const lockDir = join(dbPath, '.gbrain-lock');
      const lockFile = join(lockDir, 'lock');
      mkdirSync(lockDir, { recursive: true });
      writeFileSync(lockFile, '{not-json');

      const result = await runCliBounded(['serve'], home);

      expect(result.timedOut).toBe(false);
      expect(result.status).toBe(1);
      expect(result.stderr).toContain('lock_safety_blocked');
      expect(result.stderr).not.toContain('Timed out waiting for PGLite lock');
      expect(existsSync(lockFile)).toBe(true);
      expect(readFileSync(lockFile, 'utf-8')).toBe('{not-json');
    } finally {
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('second stdio MCP proxy returns owner_unreachable when live owner socket is absent', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    try {
      writeLiveLock(dbPath);
      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      await waitForJsonLine(child, 1);
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: 'query', arguments: { query: 'mcp-owner-missing-socket' } },
      });
      const call = await waitForJsonLine(child, 2);
      expect(call.error).toBeUndefined();
      expect(call.result.isError).toBe(true);
      const body = JSON.parse(call.result.content[0].text);
      expect(body.error).toBe('owner_unreachable');
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('second stdio MCP proxy preserves source auth scope when federated read is configured', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          GBRAIN_SOURCE: 'ai-notes',
          GBRAIN_FEDERATED_READ: 'default,ai-notes,gstack',
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      await waitForJsonLine(child, 1);
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: 'query', arguments: { query: 'mcp-federated-source' } },
      });
      const call = await waitForJsonLine(child, 2);
      expect(call.error).toBeUndefined();
      expect(seen).toHaveLength(1);
      expect(seen[0].context.sourceId).toBe('ai-notes');
      expect(seen[0].context.auth).toMatchObject({
        clientId: 'stdio',
        sourceId: 'ai-notes',
        allowedSources: ['default', 'ai-notes', 'gstack'],
      });
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('direct stdio MCP no-owner search honors federated read source auth scope', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    let engine: Awaited<ReturnType<typeof createEngine>> | null = null;
    try {
      engine = await createEngine({ engine: 'pglite', database_path: dbPath });
      await engine.connect({ engine: 'pglite', database_path: dbPath });
      await engine.initSchema();
      await engine.executeRaw(
        `INSERT INTO sources (id, name) VALUES
         ('ai-notes', 'ai-notes'),
         ('gstack', 'gstack')
         ON CONFLICT (id) DO NOTHING`,
        [],
      );
      await engine.setConfig('search.mcp_keyword_only', 'true');
      for (const sourceId of ['default', 'gstack']) {
        await engine.putPage(`notes/${sourceId}-federated`, {
          type: 'note',
          title: `${sourceId} federated`,
          compiled_truth: `FEDERATEDSCOPE ${sourceId}`,
          timeline: '',
        }, { sourceId });
        await engine.upsertChunks(`notes/${sourceId}-federated`, [
          { chunk_index: 0, chunk_text: `FEDERATEDSCOPE ${sourceId}`, chunk_source: 'compiled_truth' },
        ], { sourceId });
      }
      await engine.putPage('notes/ai-notes-federated', {
        type: 'note',
        title: 'ai-notes federated',
        compiled_truth: 'FEDERATEDSCOPE ai-notes',
        timeline: '',
      }, { sourceId: 'ai-notes' });
      await engine.upsertChunks('notes/ai-notes-federated', [
        { chunk_index: 0, chunk_text: 'FEDERATEDSCOPE ai-notes', chunk_source: 'compiled_truth' },
      ], { sourceId: 'ai-notes' });
      await engine.disconnect();
      engine = null;

      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          GBRAIN_SOURCE: 'ai-notes',
          GBRAIN_FEDERATED_READ: 'default,gstack',
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      await waitForJsonLine(child, 1);
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: 'search', arguments: { query: 'FEDERATEDSCOPE', limit: 10 } },
      });
      const call = await waitForJsonLine(child, 2);
      expect(call.error).toBeUndefined();
      expect(call.result.isError).toBeUndefined();
      const rows = JSON.parse(call.result.content[0].text);
      const sourceIds = rows.map((row: any) => row.source_id).sort();
      expect(sourceIds).toEqual(['default', 'gstack']);
      expect(sourceIds).not.toContain('ai-notes');
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      await engine?.disconnect();
      rmSync(home, { recursive: true, force: true });
    }
  }, 30_000);

  test('second stdio MCP proxy preserves invalid_params envelope from owner dispatch', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    let engine: Awaited<ReturnType<typeof createEngine>> | null = null;
    try {
      engine = await createEngine({ engine: 'pglite', database_path: dbPath });
      await engine.connect({ engine: 'pglite', database_path: dbPath });
      await engine.initSchema();
      const ownerEngine = engine;
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), (request) =>
        dispatchBrokeredOperation(ownerEngine, request),
      );
      expect(server).not.toBeNull();
      servers.push(server!);

      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      await waitForJsonLine(child, 1);
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      sendJson(child, {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: 'search', arguments: {} },
      });
      const call = await waitForJsonLine(child, 2);
      expect(call.error).toBeUndefined();
      expect(call.result.isError).toBe(true);
      const body = JSON.parse(call.result.content[0].text);
      expect(body.error).toBe('invalid_params');
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      await engine?.disconnect();
      rmSync(home, { recursive: true, force: true });
    }
  });

  test('second stdio MCP serve proxies query search and think tools through the live owner', async () => {
    const { home, dbPath } = makeHome();
    let child: ReturnType<typeof spawn> | null = null;
    try {
      writeLiveLock(dbPath);
      const seen: OperationIpcRequest[] = [];
      const server = await startPgliteOperationIpcServer(operationSocketPath(dbPath), async (request) => {
        seen.push(request);
        return { ok: true, result: [] };
      });
      expect(server).not.toBeNull();
      servers.push(server!);

      child = spawn('bun', ['run', join(process.cwd(), 'src/cli.ts'), 'serve'], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          NODE_ENV: 'test',
          GBRAIN_HOME: home,
          DATABASE_URL: '',
          GBRAIN_DATABASE_URL: '',
        },
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      child.stderr?.setEncoding('utf-8');

      sendJson(child, {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2025-11-25',
          capabilities: {},
          clientInfo: { name: 'gbrain-test', version: '0.0.0' },
        },
      });
      const init = await waitForJsonLine(child, 1);
      expect(init.result.serverInfo.name).toBe('gbrain');
      sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });

      sendJson(child, { jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} });
      const tools = await waitForJsonLine(child, 2);
      const names = tools.result.tools.map((tool: any) => tool.name).sort();
      expect(names).toEqual(['query', 'search', 'think']);

      sendJson(child, {
        jsonrpc: '2.0',
        id: 3,
        method: 'tools/call',
        params: { name: 'query', arguments: { query: 'mcp-proxy-test' } },
      });
      const call = await waitForJsonLine(child, 3);
      expect(call.error).toBeUndefined();
      expect(call.result.content[0].text).toBe('[]');
      sendJson(child, {
        jsonrpc: '2.0',
        id: 4,
        method: 'tools/call',
        params: { name: 'search', arguments: { query: 'mcp-search-test' } },
      });
      const searchCall = await waitForJsonLine(child, 4);
      expect(searchCall.result.content[0].text).toBe('[]');
      sendJson(child, {
        jsonrpc: '2.0',
        id: 5,
        method: 'tools/call',
        params: { name: 'think', arguments: { question: 'mcp think test' } },
      });
      const thinkCall = await waitForJsonLine(child, 5);
      expect(thinkCall.result.content[0].text).toBe('[]');
      expect(seen.map((r) => r.operation).sort()).toEqual(['query', 'search', 'think']);
      expect(seen.every((r) => r.caller === 'mcp-stdio')).toBe(true);
    } finally {
      if (child) {
        child.kill('SIGTERM');
        await new Promise((resolve) => child!.once('exit', resolve));
      }
      rmSync(home, { recursive: true, force: true });
    }
  });
});
