import { afterAll, beforeAll, describe, expect, test } from 'bun:test';
import { spawn, spawnSync, type ChildProcess } from 'node:child_process';
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { join, resolve } from 'node:path';
import { operationSocketPath } from '../src/core/pglite-operation-ipc.ts';
import { classifyPgliteLock } from '../src/core/pglite-lock.ts';

const REPO_ROOT = resolve(import.meta.dir, '..');
const BIN_CACHE = join(REPO_ROOT, 'test', '.cache');
const SHIM_PATH = join(BIN_CACHE, 'gbrain-pglite-concurrent-shim.sh');
const MARKER = 'CONCURRENCYMARKER';

let tmpHome: string;
let sourceDir: string;
let runEnv: NodeJS.ProcessEnv;

const children = new Set<ChildProcess>();
const childOutput = new WeakMap<ChildProcess, { stdout: string; stderr: string }>();

beforeAll(() => {
  mkdirSync(BIN_CACHE, { recursive: true });
  writeFileSync(SHIM_PATH, `#!/bin/sh\nexec bun run "${join(REPO_ROOT, 'src', 'cli.ts')}" "$@"\n`, 'utf-8');
  chmodSync(SHIM_PATH, 0o755);

  tmpHome = mkdtempSync('/tmp/gpc-');
  sourceDir = mkdtempSync('/tmp/gpcs-');

  writeFileSync(
    join(sourceDir, 'alpha.md'),
    `---\ntitle: Alpha ${MARKER}\n---\nAlpha page mentions ${MARKER} for query and search proof.\n`,
  );
  writeFileSync(
    join(sourceDir, 'beta.md'),
    `---\ntitle: Beta ${MARKER}\n---\nBeta page repeats ${MARKER} so retrieval has more than one local hit.\n`,
  );
  spawnSync('git', ['init', '-q', '-b', 'main'], { cwd: sourceDir });
  spawnSync('git', ['config', 'user.email', 'test@example.com'], { cwd: sourceDir });
  spawnSync('git', ['config', 'user.name', 'Test'], { cwd: sourceDir });
  spawnSync('git', ['add', '-A'], { cwd: sourceDir });
  spawnSync('git', ['commit', '-q', '-m', 'seed'], { cwd: sourceDir });

  runEnv = cleanEnv({ ...process.env, NODE_ENV: 'test', GBRAIN_HOME: tmpHome });

  const init = spawnSync(
    SHIM_PATH,
    ['init', '--pglite', '--repo', sourceDir, '--no-embedding', '--yes'],
    { cwd: REPO_ROOT, env: runEnv, encoding: 'utf-8', timeout: 60_000 },
  );
  if (init.status !== 0) {
    throw new Error(`gbrain init failed (${init.status})\nSTDOUT:\n${init.stdout}\nSTDERR:\n${init.stderr}`);
  }

  const cfg = readConfig();
  expect(cfg.engine).toBe('pglite');

  const sync = spawnSync(
    SHIM_PATH,
    ['sync', '--repo', sourceDir, '--no-pull', '--no-embed', '--no-extract', '--yes', '--no-hard-deadline'],
    { cwd: REPO_ROOT, env: runEnv, encoding: 'utf-8', timeout: 90_000 },
  );
  if (sync.status !== 0) {
    throw new Error(`gbrain sync failed (${sync.status})\nSTDOUT:\n${sync.stdout}\nSTDERR:\n${sync.stderr}`);
  }
}, 180_000);

afterAll(async () => {
  await cleanupChildren();
  try {
    rmSync(tmpHome, { recursive: true, force: true });
    rmSync(sourceDir, { recursive: true, force: true });
  } catch {
    /* best effort */
  }
});

function cleanEnv(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  for (const key of [
    'DATABASE_URL',
    'GBRAIN_DATABASE_URL',
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'GOOGLE_API_KEY',
    'VOYAGE_API_KEY',
    'ZEROENTROPY_API_KEY',
    'GBRAIN_SOURCE',
    'GBRAIN_FEDERATED_READ',
  ]) {
    delete env[key];
  }
  return env;
}

function readConfig(): any {
  return JSON.parse(readFileSync(join(tmpHome, '.gbrain', 'config.json'), 'utf-8'));
}

function spawnGbrain(args: string[], extraEnv: NodeJS.ProcessEnv = {}): ChildProcess {
  const child = spawn(SHIM_PATH, args, {
    cwd: REPO_ROOT,
    env: cleanEnv({ ...runEnv, ...extraEnv }),
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  const output = { stdout: '', stderr: '' };
  childOutput.set(child, output);
  child.stdout?.setEncoding('utf-8');
  child.stderr?.setEncoding('utf-8');
  child.stdout?.on('data', (chunk) => { output.stdout += chunk.toString(); });
  child.stderr?.on('data', (chunk) => { output.stderr += chunk.toString(); });
  children.add(child);
  child.once('exit', () => children.delete(child));
  return child;
}

function runCli(args: string[], timeoutMs = 30_000): Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  return new Promise((resolveOut) => {
    const child = spawnGbrain(args);
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    child.stdout?.setEncoding('utf-8');
    child.stderr?.setEncoding('utf-8');
    child.stdout?.on('data', (chunk) => { stdout += chunk; });
    child.stderr?.on('data', (chunk) => { stderr += chunk; });
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGKILL');
    }, timeoutMs);
    child.once('exit', (code) => {
      clearTimeout(timer);
      resolveOut({ code, stdout, stderr, timedOut });
    });
  });
}

function sendJson(child: ChildProcess, message: Record<string, unknown>): void {
  child.stdin?.write(`${JSON.stringify(message)}\n`);
}

function waitForJsonLine(child: ChildProcess, id: number, timeoutMs = 15_000): Promise<any> {
  return new Promise((resolveOut, reject) => {
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
          resolveOut(msg);
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

async function initializeMcp(child: ChildProcess): Promise<void> {
  const init = waitForJsonLine(child, nextId());
  const id = currentId;
  sendJson(child, {
    jsonrpc: '2.0',
    id,
    method: 'initialize',
    params: {
      protocolVersion: '2025-11-25',
      capabilities: {},
      clientInfo: { name: 'gbrain-concurrent-test', version: '0.0.0' },
    },
  });
  const response = await init;
  expect(response.error).toBeUndefined();
  expect(response.result.serverInfo.name).toBe('gbrain');
  sendJson(child, { jsonrpc: '2.0', method: 'notifications/initialized', params: {} });
}

let currentId = 0;
function nextId(): number {
  currentId += 1;
  return currentId;
}

function callTool(child: ChildProcess, name: string, args: Record<string, unknown>): Promise<any> {
  const id = nextId();
  const response = waitForJsonLine(child, id, 30_000);
  sendJson(child, { jsonrpc: '2.0', id, method: 'tools/call', params: { name, arguments: args } });
  return response;
}

async function listTools(child: ChildProcess): Promise<string[]> {
  const id = nextId();
  const response = waitForJsonLine(child, id);
  sendJson(child, { jsonrpc: '2.0', id, method: 'tools/list', params: {} });
  const tools = await response;
  expect(tools.error).toBeUndefined();
  return tools.result.tools.map((tool: any) => tool.name).sort();
}

async function waitForOwnerSocket(dbPath: string, timeoutMs = 15_000): Promise<void> {
  const socket = operationSocketPath(dbPath);
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const lock = classifyPgliteLock(dbPath);
    if (lock.status === 'live' && existsSync(socket)) return;
    await new Promise((resolveOut) => setTimeout(resolveOut, 100));
  }
  const lock = classifyPgliteLock(dbPath);
  const output = Array.from(children).map((child) => childOutput.get(child)).filter(Boolean);
  throw new Error(
    `owner socket not ready; lock=${JSON.stringify(lock)} socketExists=${existsSync(socket)} ` +
    `children=${JSON.stringify(output)}`,
  );
}

function expectNoRawPgliteLockFailure(text: string): void {
  expect(text).not.toContain('Timed out waiting for PGLite lock');
  expect(text).not.toContain('Could not acquire PGLite lock');
}

function expectNoBrokerFailure(text: string): void {
  expect(text).not.toContain('owner_unreachable');
  expect(text).not.toContain('broker_timeout');
  expect(text).not.toContain('completion_unknown');
}

async function killChild(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.killed) return;
  await new Promise<void>((resolveOut) => {
    const timer = setTimeout(() => {
      try { child.kill('SIGKILL'); } catch { /* noop */ }
    }, 2_000);
    child.once('exit', () => {
      clearTimeout(timer);
      resolveOut();
    });
    try { child.kill('SIGTERM'); } catch { resolveOut(); }
  });
}

async function cleanupChildren(): Promise<void> {
  await Promise.all(Array.from(children).map((child) => killChild(child)));
}

describe('PGLite real subprocess concurrent access', () => {
  test('real stdio owner and proxy serve mixed CLI/MCP interactive callers without PGLite lock timeout', async () => {
    const cfg = readConfig();
    expect(cfg.engine).toBe('pglite');
    const dbPath = cfg.database_path as string;

    const owner = spawnGbrain(['serve']);
    await initializeMcp(owner);
    await waitForOwnerSocket(dbPath);

    const proxy = spawnGbrain(['serve']);
    await initializeMcp(proxy);
    await expect(listTools(proxy)).resolves.toEqual(['query', 'search', 'think']);

    const mcpQuery = callTool(proxy, 'query', { query: MARKER, limit: 3 });
    const mcpSearch = callTool(proxy, 'search', { query: MARKER, limit: 3 });
    const mcpThink = callTool(proxy, 'think', { question: `What mentions ${MARKER}?` });

    const [cliQuery, cliSearch, cliThink, proxyQuery, proxySearch, proxyThink] = await Promise.all([
      runCli(['query', MARKER, '--limit', '3']),
      runCli(['search', MARKER, '--limit', '3']),
      runCli(['think', `What mentions ${MARKER}?`, '--json']),
      mcpQuery,
      mcpSearch,
      mcpThink,
    ]);

    for (const result of [cliQuery, cliSearch, cliThink]) {
      expect(result.timedOut).toBe(false);
      expect(result.code).toBe(0);
      expectNoRawPgliteLockFailure(`${result.stdout}\n${result.stderr}`);
      expectNoBrokerFailure(`${result.stdout}\n${result.stderr}`);
    }
    expect(cliQuery.stdout).toContain(MARKER);
    expect(cliSearch.stdout).toContain(MARKER);

    for (const response of [proxyQuery, proxySearch, proxyThink]) {
      expect(response.error).toBeUndefined();
      expect(response.result.isError).toBeUndefined();
      const text = JSON.stringify(response.result);
      expectNoRawPgliteLockFailure(text);
      expectNoBrokerFailure(text);
    }
    expect(JSON.stringify(proxyQuery.result)).toContain(MARKER);
    expect(JSON.stringify(proxySearch.result)).toContain(MARKER);

    await killChild(proxy);
    await killChild(owner);

    const after = await runCli(['query', MARKER, '--limit', '1'], 30_000);
    expect(after.timedOut).toBe(false);
    expect(after.code).toBe(0);
    expect(after.stdout).toContain(MARKER);
    expectNoRawPgliteLockFailure(`${after.stdout}\n${after.stderr}`);
    expect(after.stderr).not.toContain('owner_unreachable');
  }, 120_000);
});
