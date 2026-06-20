# Replication and Partitioning Lens

Use for HA, read scaling, multi-region, sharding, tenant isolation, failover, and high-volume data.

## Review Questions

- What replication topology is used: single-leader, multi-leader, leaderless, or externally managed?
- Which reads can tolerate replica lag, and which require latest writes?
- What are failover semantics: lost writes, duplicate leadership, client retries, and read routing?
- What partition key matches write distribution, tenant boundaries, and query patterns?
- Which queries become cross-partition fan-out?
- How are hot partitions, rebalancing, tenant growth, and large tenants handled?
- Are secondary indexes local, global, duplicated, or derived?

## Red Flags

- Replica reads on read-your-writes or permission-sensitive paths.
- Multi-region writes without conflict policy.
- Partition key selected only for write distribution while reads require global scans.
- Global secondary index assumed cheap and always consistent.
- Failover path untested or manual with unclear RPO/RTO.

## Proof Tests

- Replica lag behavior test per read path.
- Failover drill.
- Hot partition/load skew test.
- Rebalancing or tenant growth scenario.
- Cross-partition query budget and fallback test.
