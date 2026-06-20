# Derived Data Lens

Use for caches, search indexes, materialized views, read models, analytics tables, denormalized records, and projections.

## Review Questions

- What is the source of truth?
- What derived stores exist, and what freshness does each promise?
- Can derived data be rebuilt from canonical input?
- How is divergence detected, measured, and repaired?
- Does the read path expose stale, partial, or missing derived state to users?
- What happens when derivation fails halfway?
- Are deletes, privacy changes, and permission changes propagated?

## Red Flags

- Derived store becomes the only practical source of truth.
- Rebuild requires unavailable historical events.
- Delete or permission changes do not invalidate derived state.
- Read model has no version, watermark, or freshness indicator.
- Manual repair is required but no runbook exists.

## Proof Tests

- Rebuild from scratch.
- Incremental replay after failure.
- Source-derived reconciliation query.
- Delete and permission propagation test.
- Freshness/watermark alert test.
