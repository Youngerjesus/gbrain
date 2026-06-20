# Distributed Locking Lens

Use before proposing or accepting distributed locks, leases, singleton workers, leader election, or Redlock-style designs.

## Force Questions

- What invariant is the lock supposed to protect?
- Can the same outcome be achieved with idempotency, unique constraints, compare-and-set, queue partitioning, or fencing tokens?
- What happens if the lock holder pauses longer than the lease?
- Can a stale lock holder still write to the protected resource?
- Does the protected resource check a fencing token, epoch, or monotonically increasing version?
- What happens if lock acquisition succeeds but downstream work outcome is unknown?

## Red Flags

- Lock ownership is trusted without fencing at the resource.
- Lease timeout is treated as proof the old holder stopped.
- Lock is used to protect side effects in systems that do not check ownership.
- Clock drift or process pause is ignored.
- Retry after lock failure can duplicate work.

## Proof Tests

- Process pause beyond lease while continuing work.
- Two workers believe they own the lock.
- Stale holder attempts write with old fencing token.
- Crash after side effect before unlock.
- Lock service partition or timeout.
