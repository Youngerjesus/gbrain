# DDIA Theory Coverage Map

Use this file to activate the right theory. Do not paste theory into the answer; convert it into review findings, missing evidence, and proof tests.

## Reliability, Scalability, Maintainability

Use for every stateful design or implementation.

Review questions:
- What fails independently, and is the failure user-visible, silent, or recoverable?
- What load grows: writes, reads, fan-out, storage, indexes, backlog, or backfill?
- What future change will be expensive because of this design?

Red flags:
- Components are named but failure behavior is not.
- Capacity ignores recovery, replay, and backfill load.
- Operational complexity is hidden behind "managed service."

## Data Models and Query Patterns

Use when reviewing schema, aggregates, denormalization, event models, or query paths.

Review questions:
- Does the model match the actual access patterns?
- Which data is canonical and which is duplicated or derived?
- What invariant is enforced by the model versus by application code?
- Can denormalized data be repaired?

Red flags:
- Data duplication without reconciliation.
- Document embedding despite independent update/query needs.
- Query paths require unbounded fan-out.

## Storage Engines and Indexing

Use when reviewing database choice, index additions, storage performance, or query plans.

Review questions:
- Does the index match cardinality, selectivity, sort order, and query pattern?
- What write amplification or compaction cost is introduced?
- Are range scans, point lookups, and append patterns supported within SLO?
- Is a derived index being treated as canonical?

Red flags:
- Index added without considering write cost.
- Search/read model store used as source of truth.
- Latency assumes compaction/vacuum never interferes.

## Encoding and Schema Evolution

Use for API, event, file, database, or message schema changes.

Review questions:
- Can old readers read new data and new readers read old data?
- Can old and new producers/consumers run together?
- Are unknown fields preserved?
- Are compatibility tests present?

Red flags:
- Required field added without default, backfill, or compatibility plan.
- Event schema breaks replay.
- Rolling deploy assumes all components update atomically.

## Replication

Use for HA, read scaling, failover, multi-region, or replica reads.

Review questions:
- What topology is used: single-leader, multi-leader, or leaderless?
- What does replica lag break?
- Which reads require read-your-writes, monotonic reads, or linearizability?
- How does failover handle lost writes and split brain?

Red flags:
- Correctness-critical path reads from replicas without freshness proof.
- Multi-region writes have no conflict policy.
- Failover path is not tested.

## Partitioning

Use for sharding, tenant isolation, high volume, or scaling claims.

Review questions:
- Is the partition key aligned with write distribution and query patterns?
- What creates hot partitions or hot tenants?
- Are secondary indexes local or global?
- Which queries become cross-partition fan-out?
- How is rebalancing verified?

Red flags:
- Global secondary index assumed free.
- Hot key risk ignored.
- Tenant isolation and deletion are afterthoughts.

## Transactions and Isolation

Use for counters, money, inventory, permissions, workflow state, and multi-record updates.

Review questions:
- Which invariant requires the transaction?
- What anomaly can occur under the actual isolation level?
- Are retries safe after timeout or unknown commit?
- Is the boundary local to one database or distributed across services?

Red flags:
- Transaction claim lacks boundary and isolation level.
- Lost update, write skew, or phantom not considered.
- Timeout treated as rollback.

## Distributed Failures, Clocks, and Timeouts

Use for any networked dependency, retry, scheduler, lock, lease, or timeout.

Review questions:
- Is timeout handled as unknown?
- Can a process pause while holding a lease or after side effects?
- Does correctness depend on clock synchronization?
- Can retries amplify an outage?

Red flags:
- Remote state inferred from local timeout.
- Clock timestamp used as correctness order.
- Retry lacks idempotency, jitter, cap, or backpressure.

## Consistency, Consensus, and Linearizability

Use when reviewing latest-value correctness, leadership, membership, locks, total ordering, or singleton work.

Review questions:
- Which operations truly require linearizability?
- Is consensus or total ordering needed, and who provides it?
- Could read-your-writes or monotonic reads be sufficient?
- How are leader changes fenced?

Red flags:
- Distributed lock used as consensus.
- Strong consistency claimed over eventually consistent components.
- Leader election lacks epoch or fencing checks.

## Batch, Stream, Event Logs, and Derived Data

Use for event buses, CDC, stream processors, scheduled jobs, read models, analytics, and search.

Review questions:
- Is the event log canonical or derived?
- What delivery semantics are assumed?
- Are consumers idempotent?
- Can processing restart from a checkpoint?
- How are poison messages, late events, and backfills handled?

Red flags:
- Exactly-once assumed without end-to-end idempotency.
- No dedupe key.
- Backfill path diverges from live path without reconciliation.

## Unbundled Databases and End-to-End Correctness

Use when DB, cache, queue, stream, search, and application logic combine.

Review questions:
- Which component owns correctness?
- What end-to-end property must hold across all components?
- Can outputs be traced to canonical input?
- How is divergence detected and repaired?

Red flags:
- Local correctness in each component but no end-to-end invariant.
- No audit trail or reconciliation job.
- Manual repair process undefined.
