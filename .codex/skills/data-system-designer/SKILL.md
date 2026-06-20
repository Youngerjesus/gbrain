---
name: data-system-designer
description: Use when designing data-intensive systems, data pipelines, storage choices, cache strategies, event or stream processing, migrations, replication, partitioning, transactions, distributed locks, or consistency-critical flows. Produces a DDIA-style design that makes data invariants, read/write paths, failure handling, and operations explicit.
---

# Data System Designer

This skill turns a data-intensive product or engineering goal into an implementation-ready system design. It is not a DDIA lecture. Use the references only to activate the right theory, questions, red flags, and proof tests.

## Trigger

Use this skill when the task includes any of the following:

- database, storage engine, index, cache, queue, stream, batch job, search index, read model, materialized view, or analytics table design
- replication, partitioning, multi-region, consistency, transactions, isolation, idempotency, ordering, or distributed locking
- schema evolution, migration, backfill, replay, reconciliation, or derived data rebuild
- correctness-sensitive flows such as payment, quota, permissions, inventory, account state, entitlement, or one-time actions

Prefer a lighter general architecture approach when the task has no durable state, no derived data, and no correctness-sensitive data invariant.

## Mode Selection

Pick one primary mode before designing:

- `greenfield design`: define the data model and flows from the product goal.
- `existing system change`: preserve current behavior while changing data flow or storage.
- `migration/backfill`: plan compatibility, rollout, rollback, backfill, throttling, and verification.
- `data pipeline`: design event logs, batch/stream jobs, read models, replay, and reconciliation.
- `consistency-critical flow`: make invariants, transaction boundaries, idempotency, and failure outcomes explicit.

If the user has not provided enough facts to choose safely, ask only for the missing facts that change the design. Do not invent latency, scale, or consistency requirements.

## Minimum Facts

Gather or infer these before making irreversible design choices:

- source of truth and derived data stores
- data invariants that must not be violated
- read and write patterns, including peak and recovery load
- consistency requirements by API, screen, job, or workflow
- expected data size, cardinality, growth, and skew risks
- latency/SLO expectations and acceptable degradation
- failure outcomes the product can tolerate
- retry, replay, backfill, reconciliation, and rollback constraints
- deployment, compatibility, and operator constraints

## Workflow

1. State the design mode, goal, non-goals, and assumptions.
2. Separate functional requirements, non-functional requirements, invariants, and failure assumptions.
3. Design the data model from query patterns and invariants, not from technology preference.
4. Split the write path and read path. Name where each invariant is enforced.
5. Choose storage, indexes, cache, queues, streams, and batch jobs only where they serve a named requirement.
6. Specify consistency, transaction boundaries, idempotency keys, deduplication, ordering, and conflict behavior.
7. Check replication, partitioning, schema evolution, and derived data rebuild/replay needs.
8. Mutate failure parameters: timeout, unknown commit, duplicate request, reordered event, partial failure, stale read, clock skew, backlog, hot partition.
9. Include migration, rollout, observability, recovery, and proof tests.
10. Record rejected alternatives with the specific reason: correctness, latency, operability, migration risk, cost, or team familiarity.

## Reference Selection

- Always skim `references/theory-coverage-map.md` for the relevant DDIA theory axes.
- Use `references/data-invariants.md` for correctness-sensitive flows.
- Use `references/storage-and-indexing.md` for database/index/storage choices.
- Use `references/replication-partitioning.md` for scale-out, HA, multi-region, sharding, or replica reads.
- Use `references/transactions-consistency.md` for transaction boundaries, isolation, and read/write guarantees.
- Use `references/events-streams-batch.md` for queues, streams, batch, replay, and event logs.
- Use `references/derived-data.md` for caches, search indexes, materialized views, analytics tables, and read models.
- Use `references/cache-consistency.md` for cache-specific invalidation and staleness decisions.
- Use `references/distributed-locking.md` before proposing locks, leases, leader election, or singleton workers.
- Use `references/failure-models.md` when timeouts, retries, clocks, networks, dependency failures, or recovery paths matter.
- Use `references/schema-evolution-migrations.md` for compatibility, rollout, backfill, and rollback.

## Output Shape

Use this shape unless the user asks for a narrower artifact:

1. **Problem**
   - goal, mode, non-goals, assumptions, open decisions
2. **Data Model & Invariants**
   - source of truth, derived stores, key entities, invariants, enforcement points
3. **Write Path**
   - validation, transaction boundary, idempotency, conflict handling, events emitted
4. **Read Path**
   - query paths, cache/replica/read model use, freshness guarantees
5. **Consistency & Transactions**
   - required guarantees per path, isolation risks, retry/unknown outcome handling
6. **Storage, Index, Cache, Queue Choices**
   - selected components and why they are necessary
7. **Replication, Partitioning, and Scale**
   - partition keys, skew risks, replica lag, failover, rebalancing
8. **Failure Handling**
   - duplicate, reorder, timeout, partial failure, stale read, backlog, dependency failure
9. **Migration & Operations**
   - schema evolution, rollout, rollback, backfill, replay, reconciliation, runbooks
10. **Observability**
   - metrics, logs, traces, audits, invariant checks, alert thresholds
11. **Alternatives Rejected**
   - reasoned tradeoffs, not generic preference
12. **Acceptance Tests**
   - unit, integration, concurrency, replay/backfill, migration, and manual ops checks as relevant

## Constraints

- Do not hide correctness behind "eventual consistency"; name exactly what may be stale and for how long.
- Do not propose a distributed lock as the first correctness mechanism. Prefer idempotency, constraints, fencing tokens, or redesign where applicable.
- Treat timeout as an unknown outcome unless the dependency contract proves otherwise.
- Do not assume exactly-once delivery. Design consumers to tolerate at-least-once unless a concrete system guarantee is provided.
- Do not add a new store, cache, queue, or stream without naming the operational burden and recovery path.
