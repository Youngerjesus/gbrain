# Cache Consistency Lens

Use when reviewing cache-aside, write-through, write-behind, CDN, local memory cache, or distributed cache behavior.

## Review Questions

- What data may be stale, for whom, and for how long?
- Is the cache an optimization, a derived read model, or part of correctness?
- What invalidates the cache: write path, TTL, event, version, lease, or manual purge?
- What happens if invalidation fails after the database write succeeds?
- What happens if cache write succeeds and database write fails?
- Are negative results, permissions, and tenant data cached safely?
- Can cache stampede, hot key, or dogpile behavior overload the source store?

## Red Flags

- Cache used on correctness-critical reads without freshness guarantee.
- TTL is the only consistency strategy for permission or entitlement data.
- Write-behind can lose acknowledged writes.
- Cache key omits tenant, auth scope, locale, or version.
- No plan for stale value detection or emergency purge.

## Proof Tests

- DB write succeeds and invalidation fails.
- Concurrent read during write.
- Permission revoke and cached authorization.
- Hot key/stampede load test.
- Emergency purge drill.
