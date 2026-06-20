# Events, Streams, and Batch Lens

Use for queues, event buses, CDC, stream processors, scheduled jobs, analytics, replay, and backfill.

## Review Questions

- Is the event log canonical or derived from another source of truth?
- What delivery semantics are assumed: at-most-once, at-least-once, or effectively-once through idempotency?
- What is the dedupe key, ordering key, partition key, and checkpoint?
- Can consumers safely restart after processing but before ack/commit?
- How are late, duplicate, missing, malformed, and poison events handled?
- Does backfill use the same logic as live processing?
- Can output be replayed and reconciled against source data?

## Red Flags

- Exactly-once assumed from infrastructure alone.
- Consumer side effects happen before durable idempotency record.
- Queue ack occurs before durable output commit.
- Backfill path differs from live path without comparison.
- Poison messages block a partition with no dead-letter or quarantine policy.

## Proof Tests

- Duplicate event test.
- Reordered and late event test.
- Crash between side effect and ack.
- Replay from checkpoint.
- Backfill and live-path reconciliation.
