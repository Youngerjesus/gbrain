import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';
import { resolvePgliteOwnerPolicy } from '../src/core/pglite-owner-policy.ts';

type InventoryRow = {
  id: string;
  command_or_operation: string;
  entry_kind: string;
  accepted_behavior_class: 'broker_success_read' | 'serialized_owner_mutation' | 'typed_guard_fail_fast';
  local_only: boolean;
  transport: string;
};

function operationNameFor(row: InventoryRow): string {
  const parts = row.id.split(':');
  return parts[1] ?? row.id;
}

function cliCommandFor(row: InventoryRow): string {
  return row.command_or_operation.replace(/^gbrain\s+/, '').split(/\s+/)[0] ?? row.command_or_operation;
}

function callerFor(row: InventoryRow): 'cli' | 'mcp-stdio' | 'mcp-http' {
  if (row.transport === 'mcp-stdio') return 'mcp-stdio';
  if (row.transport === 'mcp-http') return 'mcp-http';
  return 'cli';
}

function targetFor(row: InventoryRow) {
  if (row.entry_kind === 'operation') return { kind: 'operation' as const, name: operationNameFor(row) };
  if (row.entry_kind === 'cli_command') return { kind: 'cli_command' as const, surfaceId: row.id, command: cliCommandFor(row), args: [] };
  return { kind: 'owner_startup' as const, surfaceId: row.id };
}

describe('PGLite owner policy', () => {
  test('covers every accepted inventory row with matching behavior class', () => {
    const inventory = yaml.load(readFileSync('requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml', 'utf8')) as { rows: InventoryRow[] };
    const policyRows = inventory.rows;

    expect(policyRows).toHaveLength(468);

    for (const row of policyRows) {
      const policy = resolvePgliteOwnerPolicy({
        surfaceId: row.id,
        target: targetFor(row),
        caller: callerFor(row),
      });

      expect(policy, row.id).not.toBeNull();
      expect(policy?.surfaceId).toBe(row.id);
      expect(policy?.behaviorClass, row.id).toBe(row.accepted_behavior_class);
      expect(policy?.localOnly, row.id).toBe(row.local_only);
      if (row.transport.startsWith('mcp-') && row.local_only) {
        expect(policy?.remoteAllowed, row.id).toBe(false);
      }
    }
  });
});
