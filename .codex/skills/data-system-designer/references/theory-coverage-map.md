# DDIA Theory Coverage Map

Use this file to activate the right theory. Do not paste theory into the answer; convert it into design questions, red flags, and proof tests.

## Reliability, Scalability, Maintainability

Use when any stateful system is being designed.

Force questions:
- What can fail independently, and what does the user observe?
- What load grows: writes, reads, fan-out, storage, indexes, backlog, or backfill?
- What must be easy to change later: schema, access pattern, topology, or dependency?

Red flags:
- Design names components but not failure behavior.
- Capacity plan ignores recovery, replay, and backfill load.
- Maintainability is reduced to "use a managed service."

## Data Models and Query Patterns

Use when choosing relational, document, graph, event, aggregate, or denormalized models.

Force questions:
- What are the top read and write queries?
- Which relationships are one-to-one, one-to-many, many-to-many, or graph-like?
- Which data is canonical and which is derived?
- What denormalization must be repaired or rebuilt?

Red flags:
- Model chosen before access patterns and invariants.
- Document embedding used where independent updates and queries dominate.
- Relational joins avoided by duplicating data without reconciliation.

## Storage Engines and Indexing

Use when storage performance or database choice matters.

Force questions:
- Is the workload read-heavy, write-heavy, range-heavy, point-lookup-heavy, or append-heavy?
- Are B-tree-like or LSM/log-structured tradeoffs relevant?
- What indexes are required, and what write amplification do they add?
- What compaction, vacuum, retention, or tombstone behavior can hurt latency?

Red flags:
- "Add an index" without write cost, cardinality, or query plan.
- Append-heavy workload placed on a store that cannot compact within SLO.
- Search/index store treated as source of truth.

## Encoding and Schema Evolution

Use when data crosses services, queues, files, APIs, or rolling deploy boundaries.

Force questions:
- Can old readers read new data, and can new readers read old data?
- Can old and new producers/consumers run together?
- Are unknown fields preserved or dropped?
- Is the compatibility contract tested?

Red flags:
- One-shot schema change in a distributed deployment.
- Required field added without default or migration.
- Event schema changes without replay compatibility.

## Replication

Use when HA, read scaling, failover, multi-region, or replica reads appear.

Force questions:
- Is this single-leader, multi-leader, or leaderless?
- What happens under replication lag?
- Which reads require read-your-writes, monotonic reads, or linearizability?
- How does failover avoid lost writes or split brain?
- If quorum is used, what are N/R/W and failure assumptions?

Red flags:
- Replica reads on correctness-critical paths without freshness guarantee.
- Multi-region writes without conflict detection and resolution.
- "Replication for HA" without failover semantics.

## Partitioning

Use when scaling storage, throughput, or multi-tenant data.

Force questions:
- What is the partition key, and can it create hot partitions?
- Are secondary indexes local or global?
- What queries become cross-partition fan-out?
- How are rebalancing, tenant growth, and skew handled?

Red flags:
- Partitioning only by entity id when access is tenant/time/order centric.
- Global secondary index assumed cheap.
- Rebalancing ignored until after hot keys appear.

## Transactions and Isolation

Use when multiple records, constraints, counters, inventory, money, permissions, or workflow state must change together.

Force questions:
- Which invariant requires a transaction?
- What anomaly breaks the product: lost update, write skew, phantom, dirty read, stale read?
- What isolation level is actually provided?
- What happens after timeout or unknown commit result?

Red flags:
- "Use a transaction" without naming the invariant and boundary.
- Cross-service transaction hidden behind synchronous calls.
- Retry after timeout without idempotency.

## Distributed Failures, Clocks, and Timeouts

Use for any networked dependency, lease, scheduler, lock, or timeout.

Force questions:
- Is timeout treated as unknown rather than failure?
- Can the process pause while holding a lease or lock?
- Does the design depend on clock sync or timing assumptions?
- What happens under retry storms and partial dependency failures?

Red flags:
- Local timeout interpreted as remote rollback.
- Clock time used for ordering correctness.
- Retry policy lacks jitter, cap, idempotency, or backpressure.

## Consistency, Consensus, and Linearizability

Use when correctness depends on latest value, single leader, membership, lock ownership, or total ordering.

Force questions:
- Which operations require linearizability?
- Is total order broadcast, consensus, or leader election actually needed?
- Can the product accept stale, monotonic, or read-your-writes consistency instead?
- How are leadership changes and split brain prevented?

Red flags:
- Distributed lock used as consensus substitute.
- Strong consistency claimed over eventually consistent storage.
- Leader election without fencing or epoch checks.

## Batch, Stream, Event Logs, and Derived Data

Use when jobs, event buses, CDC, projections, read models, analytics, or search indexes appear.

Force questions:
- Is the event log the source of truth or a derived stream?
- Are consumers at-least-once, at-most-once, or effectively-once through idempotency?
- Can jobs be replayed from a checkpoint?
- How are poison messages, late events, and backfills handled?

Red flags:
- Exactly-once assumed from infrastructure alone.
- No dedupe key or idempotent consumer.
- Backfill path differs from live path without reconciliation.

## Unbundled Databases and End-to-End Correctness

Use when the system combines DB, cache, search, queue, stream processor, and application logic.

Force questions:
- Which component owns correctness, and which only accelerates access?
- What end-to-end property must hold across components?
- Can derived state be rebuilt from canonical input?
- How are cross-component lag and divergence detected?

Red flags:
- Each component is locally correct but the whole workflow can duplicate or lose data.
- No audit path from output back to source event or record.
- Reconciliation is manual and undefined.
