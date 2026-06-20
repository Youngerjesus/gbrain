---
name: data-system-reviewer
description: Use when reviewing data-intensive architecture, system designs, data correctness risks, code paths, migrations, incidents, storage/cache/queue/stream choices, replication, partitioning, transactions, distributed locks, or consistency-sensitive behavior. Finds DDIA-style failure modes, missing invariants, and proof gaps before shipping.
---

# Data System Reviewer

This skill reviews data-intensive designs, code, migrations, and incidents through DDIA-style correctness and operability lenses. Findings come first. Prioritize bugs, data loss, invariant violations, silent corruption, unsafe retries, unbounded recovery cost, and missing proof.

## Trigger

Use this skill when the user asks for:

- architecture review, design review, data correctness review, or distributed systems risk review
- review of cache, database, queue, stream, batch, read model, search index, migration, or backfill design
- review of transactions, isolation, replication, partitioning, consistency, idempotency, ordering, or distributed locks
- incident review for duplicate, missing, stale, inconsistent, reordered, or corrupted data
- code review where correctness depends on storage, transactions, queues, caches, retries, locks, or schema compatibility

## Mode Selection

Choose the mode before reviewing:

- `architecture review`: inspect assumptions, invariants, failure scenarios, and design tradeoffs.
- `code review`: verify actual enforcement points such as constraints, transaction boundaries, ack timing, retry loops, idempotency keys, and cache invalidation.
- `migration review`: inspect compatibility, expand/contract rollout, rollback, backfill, throttling, and verification.
- `incident review`: reconstruct timeline, violated invariant, blast radius, recovery proof, and recurrence prevention.
- `data correctness review`: focus on duplicates, omissions, stale reads, ordering, conflicts, and reconciliation.

If evidence is missing, report `missing evidence` instead of pretending the design is safe.

## Evidence Rule

- For design documents, review assumptions and scenario coverage.
- For code, review the exact line or component where correctness is enforced or can fail.
- For incidents, separate symptom, invariant violation, root cause candidate, recovery action, and prevention.
- For migrations, verify old/new producer-consumer compatibility and rollback before data rewrite.

## Workflow

1. State the review mode, artifact under review, and evidence inspected.
2. Identify source of truth, derived stores, write paths, read paths, and named invariants.
3. Trace the main write path and read path. Mark where consistency is guaranteed, weakened, or assumed.
4. Mutate high-risk parameters: duplicate, reorder, retry, timeout, unknown commit, stale replica, cache miss/hit, backlog, hot key, partial deploy, old/new schema.
5. Check DDIA theory axes via `references/theory-coverage-map.md`; open only the focused references needed for the artifact.
6. Produce severity-ordered findings. Each finding must include risk, evidence, failure scenario, recommended fix, and proof test.
7. End with open questions, missing evidence, and residual risk.

## Required Review Questions

- What data invariant exists, and where is it actually enforced?
- Is timeout treated as success, failure, or unknown?
- Can the same request, command, or event run twice without corrupting state?
- Does event order affect correctness? If so, where is ordering guaranteed or repaired?
- Can a stale cache, replica, read model, or search index violate user-visible or business correctness?
- Is a distributed lock being used without fencing or idempotent side effects?
- Can old and new schema versions, producers, and consumers run together during rollout?
- Can derived data be rebuilt, replayed, reconciled, and audited?
- Does peak load differ from recovery load or backfill load?
- Can operators distinguish duplicate, delayed, missing, partial, and stale states from logs/metrics?

## Reference Selection

- Always use `references/theory-coverage-map.md` as the DDIA coverage checklist.
- Use `references/data-invariants.md` when correctness depends on uniqueness, ownership, ordering, or monotonic state.
- Use `references/storage-and-indexing.md` for storage and query-path claims.
- Use `references/replication-partitioning.md` for HA, replica reads, failover, multi-region, sharding, and skew.
- Use `references/transactions-consistency.md` for isolation anomalies, transaction boundaries, and consistency guarantees.
- Use `references/events-streams-batch.md` for events, queues, streams, batch jobs, replay, and backfill.
- Use `references/derived-data.md` for read models, search indexes, materialized views, analytics tables, and caches.
- Use `references/cache-consistency.md` for cache-specific invalidation and freshness risk.
- Use `references/distributed-locking.md` for locks, leases, leader election, singleton workers, and Redlock-style designs.
- Use `references/failure-models.md` for timeout, retry, network, clock, process pause, and dependency failure risks.
- Use `references/schema-evolution-migrations.md` for compatibility, migration, rollout, and rollback.

## Output Shape

Use this shape by default:

1. **Findings**
   - severity ordered; each item includes `risk`, `evidence`, `failure scenario`, `recommended fix`, and `proof test`
2. **Open Questions**
   - only questions that change the risk judgment or implementation path
3. **Missing Evidence**
   - code, logs, metrics, schema, config, or runbook evidence needed to close the review
4. **Residual Risk**
   - risks still present after the recommended fixes

If there are no findings, say so directly and name the remaining test or evidence gaps.

## Constraints

- Do not accept "eventual consistency" as an explanation unless the stale states, bounds, user impact, and repair path are named.
- Do not accept "retry" unless duplicate side effects and unknown outcomes are handled.
- Do not accept "transactional" unless the transaction boundary and isolation level address the relevant anomaly.
- Do not accept "lock protects this" unless lease expiry, fencing, process pause, and idempotency are addressed.
- Prefer concrete failure scenarios over generic best-practice advice.
