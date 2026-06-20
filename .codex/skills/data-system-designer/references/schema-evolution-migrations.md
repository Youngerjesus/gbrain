# Schema Evolution and Migrations Lens

Use for database schema changes, event/API schema changes, migrations, dual-write, backfill, data cleanup, and compatibility-sensitive rollout.

## Force Questions

- Can old and new code read old and new data?
- What is the expand/contract sequence?
- Are producers and consumers independently deployable?
- Are unknown fields preserved across services and storage?
- Is backfill idempotent, resumable, throttled, and observable?
- What is the rollback point after each step?
- How is migration correctness verified before deleting old paths?

## Red Flags

- One deploy requires all services and workers to update atomically.
- Required field added before all writers populate it.
- Dual-write has no divergence detection.
- Backfill has no checkpoint, throttle, or retry safety.
- Rollback plan ignores already-written new-format data.

## Proof Tests

- Old writer with new reader.
- New writer with old reader.
- Rolling deploy compatibility.
- Backfill resume after crash.
- Dual-write divergence and reconciliation.
- Rollback after partial migration.
