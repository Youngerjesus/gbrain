import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';

type InventoryRow = {
  id: string;
  accepted_behavior_class: 'broker_success_read' | 'serialized_owner_mutation' | 'typed_guard_fail_fast';
};

type Representative = {
  row_id: string;
  behavior_class: InventoryRow['accepted_behavior_class'];
  surface: string;
  owner_state: string;
  evidence: string;
};

type Manifest = {
  requirement_id: string;
  status: string;
  inventory_ref: string;
  representatives: Representative[];
  owner_state_representatives: Array<{ owner_state: string; evidence: string }>;
};

describe('PGLite broker representative coverage manifest', () => {
  test('references accepted inventory rows and covers required targeted dimensions', () => {
    const manifest = yaml.load(readFileSync('requirements/007-pglite-broker-guard-implementation/representative-coverage.yml', 'utf8')) as Manifest;
    const inventory = yaml.load(readFileSync(manifest.inventory_ref, 'utf8')) as { rows: InventoryRow[] };
    const rowsById = new Map(inventory.rows.map((row) => [row.id, row]));

    expect(manifest.requirement_id).toBe('007-pglite-broker-guard-implementation');
    expect(manifest.status).toBe('in_progress');
    expect(manifest.representatives.length).toBeGreaterThanOrEqual(9);

    for (const rep of manifest.representatives) {
      const row = rowsById.get(rep.row_id);
      expect(row, rep.row_id).toBeDefined();
      if (!row) continue;
      expect(rep.behavior_class, rep.row_id).toBe(row.accepted_behavior_class);
      expect(rep.evidence, rep.row_id).toContain('test/');
    }

    const classes = new Set(manifest.representatives.map((rep) => rep.behavior_class));
    expect(classes).toEqual(new Set(['broker_success_read', 'serialized_owner_mutation', 'typed_guard_fail_fast']));

    const surfaces = new Set(manifest.representatives.map((rep) => rep.surface));
    for (const required of ['gbrain-call', 'local-cli', 'mcp-stdio', 'mcp-http']) {
      expect(surfaces.has(required), required).toBe(true);
    }

    const ownerStates = new Set(manifest.owner_state_representatives.map((rep) => rep.owner_state));
    for (const required of ['healthy_live_owner', 'live_missing_socket', 'corrupt_lock', 'owner_starting', 'completion_unknown']) {
      expect(ownerStates.has(required), required).toBe(true);
    }
  });
});
