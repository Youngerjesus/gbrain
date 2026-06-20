import { describe, test, expect, beforeEach, afterEach } from 'bun:test';
import { runThinkCli } from '../src/commands/think.ts';

let helpText = '';
const origLog = console.log;

beforeEach(() => {
  helpText = '';
  console.log = (message?: unknown) => {
    helpText += String(message ?? '');
  };
});

afterEach(() => {
  console.log = origLog;
});

describe('gbrain think help', () => {
  test('points default synthesis setup at the Gemini API key', async () => {
    await runThinkCli({} as never, ['--help']);

    expect(helpText).toContain('GOOGLE_GENERATIVE_AI_API_KEY');
    expect(helpText).not.toContain('ANTHROPIC_API_KEY');
    expect(helpText).not.toContain('anthropic_api_key');
  });
});
