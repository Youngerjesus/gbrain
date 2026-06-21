import type { BrainEngine } from '../core/engine.ts';
import type { OperationIpcRequest, OperationIpcTarget } from '../core/pglite-operation-ipc.ts';
import { resolvePgliteOwnerPolicy } from '../core/pglite-owner-policy.ts';
import { withGatewayEnvOverlay } from '../core/ai/gateway.ts';

export interface BrokeredCliCommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

class CliCommandExit extends Error {
  constructor(readonly code: number) {
    super(`CLI command exited with ${code}`);
  }
}

export async function dispatchBrokeredCliCommand(
  engine: BrainEngine,
  request: OperationIpcRequest,
): Promise<{ ok: true; result: BrokeredCliCommandResult } | { ok: false; status: 'invalid_request' | 'handler_error' | 'local_only_remote_rejected'; message: string }> {
  const target = request.target;
  if (!isCliCommandTarget(target)) {
    return { ok: false, status: 'invalid_request', message: 'Brokered CLI command target is missing or invalid.' };
  }
  const policy = resolvePgliteOwnerPolicy({
    surfaceId: target.surfaceId,
    target,
    caller: request.caller === 'mcp-stdio' ? 'mcp-stdio' : 'cli',
  });
  if (!policy) return { ok: false, status: 'invalid_request', message: 'Unknown brokered CLI command target.' };
  if (!policy.remoteAllowed) {
    return {
      ok: false,
      status: 'local_only_remote_rejected',
      message: `CLI command target ${target.surfaceId} is localOnly and cannot be called by remote MCP clients.`,
    };
  }

  try {
    const cwd = typeof request.context.cwd === 'string' ? request.context.cwd : undefined;
    const result = await withGatewayEnvOverlay(request.context.callerEnv, () =>
      runCliCommandAdapter(engine, target, cwd),
    );
    return { ok: true, result };
  } catch {
    return { ok: false, status: 'handler_error', message: 'Brokered CLI command failed.' };
  }
}

function isCliCommandTarget(target: OperationIpcTarget | undefined): target is Extract<OperationIpcTarget, { kind: 'cli_command' }> {
  return Boolean(
    target &&
    target.kind === 'cli_command' &&
    typeof target.surfaceId === 'string' &&
    typeof target.command === 'string' &&
    Array.isArray(target.args),
  );
}

async function runCliCommandAdapter(
  engine: BrainEngine,
  target: Extract<OperationIpcTarget, { kind: 'cli_command' }>,
  cwd?: string,
): Promise<BrokeredCliCommandResult> {
  switch (target.surfaceId) {
    case 'cli:config:show':
    case 'cli:config:get':
    case 'cli:config:set':
    case 'cli:config:unset': {
      if (target.command !== 'config') break;
      const { runConfig } = await import('../commands/config.ts');
      return captureCliCommandOutput(async () => {
        await runConfig(engine, target.args);
      }, cwd);
    }
    case 'cli:files:list': {
      if (target.command !== 'files') break;
      const { runFiles } = await import('../commands/files.ts');
      return captureCliCommandOutput(async () => {
        await runFiles(engine, target.args);
      }, cwd);
    }
  }
  if (target.surfaceId.startsWith('cli:files:') && target.command === 'files') {
    const { runFiles } = await import('../commands/files.ts');
    return captureCliCommandOutput(async () => {
      await runFiles(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:jobs:') && target.command === 'jobs') {
    const { runJobs } = await import('../commands/jobs.ts');
    return captureCliCommandOutput(async () => {
      await runJobs(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:sources:') && target.command === 'sources') {
    const { runSources } = await import('../commands/sources.ts');
    return captureCliCommandOutput(async () => {
      await runSources(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId === 'cli:repos:pglite-surface' && target.command === 'repos') {
    const { runSources } = await import('../commands/sources.ts');
    return captureCliCommandOutput(async () => {
      await runSources(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:takes:') && target.command === 'takes') {
    const { runTakes } = await import('../commands/takes.ts');
    return captureCliCommandOutput(async () => {
      await runTakes(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:search:') && target.command === 'search') {
    return captureCliCommandOutput(async () => {
      if (target.surfaceId === 'cli:search:diagnose') {
        const { runSearchDiagnose } = await import('../commands/search-diagnose.ts');
        await runSearchDiagnose(engine, target.args);
        return;
      }
      const { runSearch } = await import('../commands/search.ts');
      await runSearch(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:eval:') && target.command === 'eval') {
    const { runEvalCommand } = await import('../commands/eval.ts');
    return captureCliCommandOutput(async () => {
      await runEvalCommand(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:cache:') && target.command === 'cache') {
    const { runCache } = await import('../commands/cache.ts');
    return captureCliCommandOutput(async () => {
      await runCache(target.args, engine);
    }, cwd);
  }
  if (target.surfaceId.startsWith('cli:doctor:') && target.command === 'doctor') {
    const { runDoctor } = await import('../commands/doctor.ts');
    return captureCliCommandOutput(async () => {
      await runDoctor(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId === 'cli:storage:status' && target.command === 'storage') {
    const { runStorage } = await import('../commands/storage.ts');
    return captureCliCommandOutput(async () => {
      await runStorage(engine, target.args);
    }, cwd);
  }
  if (target.surfaceId === 'cli:status:pglite-surface' && target.command === 'status') {
    const { runStatus } = await import('../commands/status.ts');
    return captureCliCommandOutput(async () => {
      const result = await runStatus(engine, target.args);
      if (result.exitCode !== 0) process.exit(result.exitCode);
    }, cwd);
  }
  if (target.surfaceId === 'cli:lint:module-open-site' && target.command === 'lint') {
    const { runLint } = await import('../commands/lint.ts');
    return captureCliCommandOutput(async () => { await runLint(target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:auth:module-open-site' && target.command === 'auth') {
    const { runAuth } = await import('../commands/auth.ts');
    return captureCliCommandOutput(async () => { await runAuth(target.args, engine); }, cwd);
  }
  if (target.surfaceId === 'cli:advisor:pglite-surface' && target.command === 'advisor') {
    const { runAdvisorCli } = await import('../commands/advisor.ts');
    return captureCliCommandOutput(async () => {
      const result = await runAdvisorCli(engine, target.args);
      if (result.exitCode !== 0) process.exit(result.exitCode);
    }, cwd);
  }
  if (target.surfaceId === 'cli:agent:pglite-surface' && target.command === 'agent') {
    const { runAgent } = await import('../commands/agent.ts');
    return captureCliCommandOutput(async () => { await runAgent(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:anomalies:pglite-surface' && target.command === 'anomalies') {
    const { runAnomalies } = await import('../commands/anomalies.ts');
    return captureCliCommandOutput(async () => { await runAnomalies(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:book-mirror:pglite-surface' && target.command === 'book-mirror') {
    const { runBookMirrorCmd } = await import('../commands/book-mirror.ts');
    return captureCliCommandOutput(async () => { await runBookMirrorCmd(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:brainstorm:pglite-surface' && target.command === 'brainstorm') {
    const { runBrainstormCommand } = await import('../commands/brainstorm.ts');
    return captureCliCommandOutput(async () => { await runBrainstormCommand(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:capture:pglite-surface' && target.command === 'capture') {
    const { runCapture } = await import('../commands/capture.ts');
    return captureCliCommandOutput(async () => { await runCapture(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:code-callees:pglite-surface' && target.command === 'code-callees') {
    const { runCodeCallees } = await import('../commands/code-callees.ts');
    return captureCliCommandOutput(async () => { await runCodeCallees(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:code-callers:pglite-surface' && target.command === 'code-callers') {
    const { runCodeCallers } = await import('../commands/code-callers.ts');
    return captureCliCommandOutput(async () => { await runCodeCallers(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:code-def:pglite-surface' && target.command === 'code-def') {
    const { runCodeDef } = await import('../commands/code-def.ts');
    return captureCliCommandOutput(async () => { await runCodeDef(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:code-refs:pglite-surface' && target.command === 'code-refs') {
    const { runCodeRefs } = await import('../commands/code-refs.ts');
    return captureCliCommandOutput(async () => { await runCodeRefs(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:dream:pglite-surface' && target.command === 'dream') {
    const { runDream } = await import('../commands/dream.ts');
    return captureCliCommandOutput(async () => { await runDream(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:edges-backfill:pglite-surface' && target.command === 'edges-backfill') {
    const { runEdgesBackfill } = await import('../commands/edges-backfill.ts');
    return captureCliCommandOutput(async () => { await runEdgesBackfill(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:enrich:pglite-surface' && target.command === 'enrich') {
    const { runEnrich } = await import('../commands/enrich.ts');
    return captureCliCommandOutput(async () => { await runEnrich(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:export:pglite-surface' && target.command === 'export') {
    const { runExport } = await import('../commands/export.ts');
    return captureCliCommandOutput(async () => { await runExport(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:features:pglite-surface' && target.command === 'features') {
    const { runFeatures } = await import('../commands/features.ts');
    return captureCliCommandOutput(async () => { await runFeatures(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:forget:pglite-surface' && target.command === 'forget') {
    const { runForget } = await import('../commands/recall.ts');
    return captureCliCommandOutput(async () => { await runForget(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:founder:pglite-surface' && target.command === 'founder') {
    const { runFounder } = await import('../commands/founder-scorecard.ts');
    return captureCliCommandOutput(async () => { await runFounder(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:graph-query:pglite-surface' && target.command === 'graph-query') {
    const { runGraphQuery } = await import('../commands/graph-query.ts');
    return captureCliCommandOutput(async () => { await runGraphQuery(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:import:pglite-surface' && target.command === 'import') {
    const { runImport } = await import('../commands/import.ts');
    return captureCliCommandOutput(async () => {
      const result = await runImport(engine, target.args);
      if (result.errors > 0) process.exit(1);
    }, cwd);
  }
  if (target.surfaceId === 'cli:lsd:pglite-surface' && target.command === 'lsd') {
    const { runLsdCommand } = await import('../commands/brainstorm.ts');
    return captureCliCommandOutput(async () => { await runLsdCommand(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:migrate:pglite-surface' && target.command === 'migrate') {
    const { runMigrateEngine } = await import('../commands/migrate-engine.ts');
    return captureCliCommandOutput(async () => { await runMigrateEngine(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:models:pglite-surface' && target.command === 'models') {
    const { runModels } = await import('../commands/models.ts');
    return captureCliCommandOutput(async () => { await runModels(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:onboard:pglite-surface' && target.command === 'onboard') {
    const { runOnboard } = await import('../commands/onboard.ts');
    return captureCliCommandOutput(async () => { await runOnboard(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:orphans:pglite-surface' && target.command === 'orphans') {
    const { runOrphans } = await import('../commands/orphans.ts');
    return captureCliCommandOutput(async () => { await runOrphans(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:quarantine:pglite-surface' && target.command === 'quarantine') {
    const { runQuarantine } = await import('../commands/quarantine.ts');
    return captureCliCommandOutput(async () => { await runQuarantine(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:recall:pglite-surface' && target.command === 'recall') {
    const { runRecall } = await import('../commands/recall.ts');
    return captureCliCommandOutput(async () => { await runRecall(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:reindex:pglite-surface' && target.command === 'reindex') {
    const { runReindex } = await import('../commands/reindex.ts');
    return captureCliCommandOutput(async () => { await runReindex(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:reindex-code:pglite-surface' && target.command === 'reindex-code') {
    const { runReindexCodeCli } = await import('../commands/reindex-code.ts');
    return captureCliCommandOutput(async () => { await runReindexCodeCli(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:reindex-frontmatter:pglite-surface' && target.command === 'reindex-frontmatter') {
    const { runReindexFrontmatter } = await import('../commands/reindex-frontmatter.ts');
    return captureCliCommandOutput(async () => {
      const opts: {
        sourceId?: string;
        slugPrefix?: string;
        dryRun?: boolean;
        yes?: boolean;
        json?: boolean;
        force?: boolean;
        workers?: number;
      } = {};
      for (let i = 0; i < target.args.length; i++) {
        const arg = target.args[i];
        if (arg === '--source') opts.sourceId = target.args[++i];
        else if (arg === '--slug-prefix') opts.slugPrefix = target.args[++i];
        else if (arg === '--dry-run') opts.dryRun = true;
        else if (arg === '--yes' || arg === '-y') opts.yes = true;
        else if (arg === '--json') opts.json = true;
        else if (arg === '--force') opts.force = true;
        else if (arg === '--workers' || arg === '--concurrency') {
          const value = parseInt(target.args[++i] ?? '', 10);
          if (Number.isFinite(value) && value >= 1) opts.workers = value;
        } else {
          console.error(`Unknown arg: ${arg}`);
          process.exit(2);
        }
      }
      const result = await runReindexFrontmatter(engine, opts);
      if (opts.json) {
        console.log(JSON.stringify(result, null, 2));
      } else {
        const noun = result.status === 'dry_run' ? 'would update' : 'updated';
        console.error(
          `\nReindex ${result.status}: examined=${result.examined} ${noun}=${result.updated} ` +
          `fallback=${result.fallback} dur=${result.durationSec.toFixed(1)}s`,
        );
      }
      if (result.status === 'cancelled') process.exit(1);
    }, cwd);
  }
  if (target.surfaceId === 'cli:salience:pglite-surface' && target.command === 'salience') {
    const { runSalience } = await import('../commands/salience.ts');
    return captureCliCommandOutput(async () => { await runSalience(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:skillopt:pglite-surface' && target.command === 'skillopt') {
    const { runSkillOptCommand } = await import('../commands/skillopt.ts');
    return captureCliCommandOutput(async () => { await runSkillOptCommand(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:think:pglite-surface' && target.command === 'think') {
    const { runThinkCli } = await import('../commands/think.ts');
    return captureCliCommandOutput(async () => { await runThinkCli(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:transcripts:pglite-surface' && target.command === 'transcripts') {
    const { runTranscripts } = await import('../commands/transcripts.ts');
    return captureCliCommandOutput(async () => { await runTranscripts(engine, target.args); }, cwd);
  }
  if (target.surfaceId === 'cli:ze-switch:pglite-surface' && target.command === 'ze-switch') {
    const { runZeSwitch } = await import('../commands/ze-switch.ts');
    return captureCliCommandOutput(async () => { await runZeSwitch(target.args, engine); }, cwd);
  }
  return {
    stdout: '',
    stderr: `Unsupported brokered CLI command target: ${target.surfaceId}\n`,
    exitCode: 1,
  };
}

async function captureCliCommandOutput(fn: () => Promise<void>, cwd?: string): Promise<BrokeredCliCommandResult> {
  const oldLog = console.log;
  const oldError = console.error;
  const oldExit = process.exit;
  const oldStdoutWrite = process.stdout.write;
  const oldStderrWrite = process.stderr.write;
  const oldCwd = process.cwd();
  let stdout = '';
  let stderr = '';
  let exitCode = 0;
  const chunkToString = (chunk: unknown, encoding?: BufferEncoding): string => {
    if (typeof chunk === 'string') return chunk;
    if (chunk instanceof Uint8Array) return Buffer.from(chunk).toString(encoding ?? 'utf8');
    return String(chunk);
  };

  console.log = (...args: unknown[]) => {
    stdout += `${args.map(String).join(' ')}\n`;
  };
  console.error = (...args: unknown[]) => {
    stderr += `${args.map(String).join(' ')}\n`;
  };
  process.stdout.write = ((chunk: unknown, encodingOrCallback?: BufferEncoding | ((error?: Error | null) => void), callback?: (error?: Error | null) => void): boolean => {
    stdout += chunkToString(chunk, typeof encodingOrCallback === 'string' ? encodingOrCallback : undefined);
    const cb = typeof encodingOrCallback === 'function' ? encodingOrCallback : callback;
    cb?.();
    return true;
  }) as typeof process.stdout.write;
  process.stderr.write = ((chunk: unknown, encodingOrCallback?: BufferEncoding | ((error?: Error | null) => void), callback?: (error?: Error | null) => void): boolean => {
    stderr += chunkToString(chunk, typeof encodingOrCallback === 'string' ? encodingOrCallback : undefined);
    const cb = typeof encodingOrCallback === 'function' ? encodingOrCallback : callback;
    cb?.();
    return true;
  }) as typeof process.stderr.write;
  process.exit = ((code?: string | number | null | undefined): never => {
    const numeric = typeof code === 'number' ? code : Number(code ?? 0);
    throw new CliCommandExit(Number.isFinite(numeric) ? numeric : 1);
  }) as typeof process.exit;

  try {
    if (cwd) process.chdir(cwd);
    await fn();
  } catch (error) {
    if (error instanceof CliCommandExit) exitCode = error.code;
    else throw error;
  } finally {
    try { process.chdir(oldCwd); } catch { /* best effort: preserve original error/output restoration */ }
    console.log = oldLog;
    console.error = oldError;
    process.stdout.write = oldStdoutWrite;
    process.stderr.write = oldStderrWrite;
    process.exit = oldExit;
  }

  return { stdout, stderr, exitCode };
}
