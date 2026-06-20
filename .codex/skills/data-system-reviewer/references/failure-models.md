# Failure Models Lens

Use for any design or implementation with networked dependencies, retries, async jobs, schedulers, caches, queues, or distributed coordination.

## Review Questions

- Which failures are possible: timeout, partial success, delayed success, duplicate response, stale response, dependency overload, process crash, clock skew?
- Is timeout interpreted as unknown rather than failure?
- What state is durable before and after each external side effect?
- Can retry create duplicate effects or reorder operations?
- Can recovery load exceed normal load?
- What can operators observe and safely do?

## Red Flags

- Local timeout assumed to mean remote failure.
- Retry loop lacks idempotency, cap, jitter, backoff, or dead-letter path.
- Process memory holds state required for recovery.
- Partial failure is converted into a generic error with no repair path.
- Operators cannot distinguish duplicate, delayed, stale, and missing states.

## Proof Tests

- Timeout with remote success.
- Crash after durable write and before response.
- Dependency slow/partial outage.
- Retry storm and backpressure.
- Manual recovery runbook drill.
