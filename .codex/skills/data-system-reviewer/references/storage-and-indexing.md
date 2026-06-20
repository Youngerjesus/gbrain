# Storage and Indexing Lens

Use when reviewing database choice, index additions, storage performance, query paths, or persistence for high read/write volume.

## Review Questions

- What are the dominant access patterns: point lookup, range scan, search, aggregation, graph traversal, append, update-in-place?
- Which queries must be served online, and which can be asynchronous or precomputed?
- What indexes are required for the top queries, and what write cost do they add?
- What data shape creates high cardinality, low selectivity, or unbounded scans?
- Does the storage engine favor append/LSM-style writes, B-tree/range access, full-text search, or analytical scans?
- What happens during compaction, vacuum, index rebuild, or storage growth?

## Red Flags

- Database chosen before access patterns.
- Search index, cache, or analytics store treated as source of truth.
- Index proposal lacks cardinality, selectivity, sort order, and write amplification.
- Query requires cross-partition scan or N+1 fan-out under normal usage.
- Storage cleanup and retention are left to ad hoc scripts.

## Proof Tests

- Query plan or benchmark for top reads.
- Write throughput with all planned indexes.
- Backfill or index rebuild dry run on realistic volume.
- Hot-key or skew simulation.
- Retention/tombstone cleanup verification.
