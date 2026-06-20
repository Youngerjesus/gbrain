import { describe, expect, test } from 'bun:test';
import {
  parseStdioFederatedRead,
  resolveStdioSourceScope,
} from '../src/mcp/server.ts';

describe('stdio MCP source scope env', () => {
  test('omitted or blank GBRAIN_FEDERATED_READ keeps scalar source behavior', () => {
    expect(parseStdioFederatedRead(undefined)).toBeUndefined();
    expect(parseStdioFederatedRead('   ')).toBeUndefined();
    expect(resolveStdioSourceScope({}).sourceId).toBe('default');
    expect(resolveStdioSourceScope({}).allowedSources).toBeUndefined();
  });

  test('parses comma-separated federated read sources with trimming and dedupe', () => {
    expect(parseStdioFederatedRead(' default, ai-notes,default,gstack ')).toEqual([
      'default',
      'ai-notes',
      'gstack',
    ]);
  });

  test('GBRAIN_SOURCE remains the scalar write/default source while federated read widens reads', () => {
    expect(resolveStdioSourceScope({
      GBRAIN_SOURCE: 'ai-notes',
      GBRAIN_FEDERATED_READ: 'default,ai-notes,gstack',
    })).toEqual({
      sourceId: 'ai-notes',
      allowedSources: ['default', 'ai-notes', 'gstack'],
    });
  });

  test('invalid source ids fail loud instead of silently widening or narrowing scope', () => {
    expect(() => parseStdioFederatedRead('default,has_underscore')).toThrow(/GBRAIN_FEDERATED_READ/);
    expect(() => parseStdioFederatedRead('default,../escape')).toThrow(/GBRAIN_FEDERATED_READ/);
  });
});
