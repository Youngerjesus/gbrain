# Transactions and Consistency Lens

Use when multiple records, counters, balances, permissions, workflow state, or correctness-critical reads/writes are involved.

## Force Questions

- Which invariant requires a transaction or stronger consistency?
- What anomaly matters: lost update, write skew, phantom, stale read, dirty read, non-repeatable read?
- What isolation level is actually provided by the chosen store?
- Is the transaction boundary local to one database or spread across services?
- After timeout, is the outcome success, failure, or unknown?
- Can idempotency, unique constraints, conditional writes, or reconciliation replace a broader transaction?
- Which reads require linearizable, read-your-writes, monotonic, bounded-stale, or eventual consistency?

## Red Flags

- "Use transaction" without invariant, boundary, and isolation level.
- Cross-service synchronous calls treated as one transaction.
- Timeout handled as rollback.
- Eventual consistency used on paths that enforce permissions, quotas, or money movement.
- Read-modify-write under weak isolation without compare-and-set or constraint.

## Proof Tests

- Concurrency test for the target anomaly.
- Retry after unknown commit result.
- Isolation-level specific test.
- Read freshness test for user-visible paths.
- Reconciliation test for weaker consistency paths.
