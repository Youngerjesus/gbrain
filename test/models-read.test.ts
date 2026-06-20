import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import { runModels } from '../src/commands/models.ts';

class StubEngine {
  readonly kind = 'pglite' as const;
  private cfg = new Map<string, string>();
  set(key: string, value: string) { this.cfg.set(key, value); }
  async getConfig(key: string) { return this.cfg.get(key) ?? null; }
}

let stdoutCapture = '';
const origStdoutWrite = process.stdout.write.bind(process.stdout);
let origGbrainModel: string | undefined;

beforeEach(() => {
  stdoutCapture = '';
  origGbrainModel = process.env.GBRAIN_MODEL;
  process.stdout.write = ((chunk: string | Uint8Array) => {
    stdoutCapture += typeof chunk === 'string' ? chunk : Buffer.from(chunk).toString();
    return true;
  }) as typeof process.stdout.write;
  delete process.env.GBRAIN_MODEL;
});

afterEach(() => {
  process.stdout.write = origStdoutWrite;
  if (origGbrainModel === undefined) delete process.env.GBRAIN_MODEL;
  else process.env.GBRAIN_MODEL = origGbrainModel;
});

describe('gbrain models read report', () => {
  test('reports the same default model that gbrain think uses', async () => {
    const engine = new StubEngine();

    await runModels(engine as never, ['models', '--json']);
    const report = JSON.parse(stdoutCapture);
    const thinkEntry = report.per_task.find((entry: { key: string }) => entry.key === 'models.think');

    expect(thinkEntry?.resolved).toBe('google:gemini-3.5-flash');
    expect(thinkEntry?.source).toBe('task.default');
  });

  test('attributes models.think to the configured deep tier when it wins', async () => {
    const engine = new StubEngine();
    engine.set('models.tier.deep', 'anthropic:claude-opus-4-7');

    await runModels(engine as never, ['models', '--json']);
    const report = JSON.parse(stdoutCapture);
    const thinkEntry = report.per_task.find((entry: { key: string }) => entry.key === 'models.think');

    expect(thinkEntry?.resolved).toBe('anthropic:claude-opus-4-7');
    expect(thinkEntry?.source).toBe('config: models.tier.deep');
  });

  test('attributes tier rows to GBRAIN_MODEL when env wins', async () => {
    const engine = new StubEngine();
    process.env.GBRAIN_MODEL = 'haiku';

    await runModels(engine as never, ['models', '--json']);
    const report = JSON.parse(stdoutCapture);

    expect(report.tiers.deep.resolved).toBe('anthropic:claude-haiku-4-5-20251001');
    expect(report.tiers.deep.source).toBe('env: GBRAIN_MODEL');
  });
});
