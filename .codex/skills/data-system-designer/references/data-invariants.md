# Data Invariants Lens

Use when correctness depends on uniqueness, ownership, authorization, ordering, monotonic state, counters, balances, quotas, one-time actions, or lifecycle transitions.

## Force Questions

- What must never be duplicated, lost, reordered, or observed stale?
- Is the invariant enforced by database constraint, transaction, idempotency key, compare-and-set, application logic, or reconciliation?
- What happens if the same command/event/request is processed twice?
- What happens if two actors update the same entity concurrently?
- Which state transitions are legal, terminal, reversible, or monotonic?
- Can the invariant be checked offline with an audit query?

## Red Flags

- "Business logic prevents this" without a durable enforcement point.
- Idempotency key exists but is not scoped to the real side effect.
- Uniqueness is checked before write without an atomic constraint.
- Counter or quota updates depend on read-modify-write under weak isolation.
- Reconciliation is mentioned but has no source of truth or audit rule.

## Proof Tests

- Duplicate request/event test.
- Concurrent update test.
- Retry after timeout or process crash.
- Illegal transition attempt.
- Offline invariant audit over real or fixture data.
