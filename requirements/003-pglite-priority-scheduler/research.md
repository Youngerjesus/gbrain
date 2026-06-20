# Research: PGLite Priority Scheduler

## Status

Complete.

## Requirement

- Source: `requirements/003-pglite-priority-scheduler/requirements.md`
- Gate: research
- Date: 2026-06-20

## Decision Summary

1. Reuse the existing local operation IPC broker as the priority boundary.
2. Treat priority as enqueue/drain ordering only; do not attempt mid-transaction preemption.
3. Keep brokered operation execution limited to `query`, `search`, and `think`.
4. Add a pre-connect PGLite live-lock guard for `sync`, `embed`, and `extract` so a second maintenance caller gets deterministic bounded fallback instead of waiting on the PGLite lock.
5. Verify real command behavior with command-level tests for `sync`, `embed`, and `extract`; generic IPC priority tests remain necessary but insufficient.

## Evidence Reviewed

| Source | Evidence | Finding | Confidence |
| --- | --- | --- | --- |
| `src/core/pglite-operation-ipc.ts` | `OperationIpcClass = 'interactive' | 'maintenance'`; `effectivePriority()` adds a class boost for interactive work; `processQueue()` sorts queued items after a short drain window. | Queue priority already exists and is explicitly bounded to the queue boundary. | High |
| `src/core/pglite-operation-ipc.ts` | `VALID_OPERATIONS` accepts only `query`, `search`, and `think`. | The broker cannot currently execute maintenance commands. This is consistent with operation-level forwarding, but synthetic maintenance-class IPC tests do not prove real maintenance command behavior. | High |
| `src/cli.ts` | `handleCliOnly()` calls `connectEngine()` and then `maybeStartCliOperationBroker(engine)` for all remaining CLI-only commands except `serve`. | A real `sync`, `embed`, or `extract` process that successfully owns PGLite already exposes the broker while its command body runs. | High |
| `src/cli.ts` | `sync --help` is intercepted before `connectEngine()`; other `sync` modes fall through to the DB-bound path. | Help paths should remain direct and unaffected by contention handling. | High |
| `src/commands/sync.ts`, `src/commands/embed.ts`, `src/commands/extract.ts` | Command bodies run substantial DB work after receiving an already-connected `BrainEngine`; several paths call `process.exit()`. | The safest contention boundary is before `connectEngine()` in CLI dispatch, not inside every command body. | High |
| `src/core/pglite-lock.ts` | `classifyPgliteLock()` can distinguish absent, live, stale/dead, corrupt, and unknown lock states without acquiring or cleaning the lock. | The existing classifier is the correct guard for deciding whether maintenance should direct-open or return deterministic fallback. | High |
| `test/pglite-operation-ipc.test.ts` | Existing test `interactive priority beats lower-priority queued work`. | Generic scheduler correctness is already testable and should be preserved/expanded only if needed. | High |
| `test/cli-pglite-operation-broker.test.ts` | Existing tests cover five concurrent CLI callers, mixed CLI/MCP callers, owner-missing socket, corrupt lock safety, and source/auth parity. | Requirement 002 regression coverage is a good base for requirement 003, but lacks real `sync`/`embed`/`extract` contention cases. | High |

## Decisions

### D1. Reuse the existing local owner broker

The current broker is local filesystem socket IPC, has no network listener, and forwards only operation-level `query`, `search`, and `think` requests. This matches AC7 and avoids inventing a new scheduler.

Implementation should not introduce raw SQL forwarding, a network service, or a second persistence layer.

### D2. Priority is honest queue priority, not interruption

`processQueue()` can choose which waiting item runs next, but once the handler is running it is not preempted. This satisfies AC3 if the closeout states the boundary clearly.

Implementation must not claim that interactive calls can interrupt an already-running PGLite transaction. They can be served by a live owner at broker queue boundaries, and they can beat queued maintenance-class IPC work.

### D3. Do not broker real maintenance commands in this slice

`OperationIpcOperation` currently supports only `query`, `search`, and `think`, and `dispatchBrokeredOperation()` dispatches through the existing operation registry or MCP tool dispatcher. Adding `sync`, `embed`, or `extract` as brokered operations would require command-specific parameter schemas, output semantics, cancellation behavior, and job lifecycle semantics.

For this requirement, maintenance commands should be treated as PGLite owners when they start successfully, and as bounded/deferred callers when another owner is already live.

### D4. Add pre-connect maintenance deferral

When `command` is one of `sync`, `embed`, or `extract` and config is PGLite:

- absent lock: allow direct open, preserving current no-owner behavior
- dead/stale recoverable lock: allow direct open, preserving stale recovery behavior
- live lock: emit a deterministic non-lock-timeout fallback before `connectEngine()`
- corrupt/unknown lock: emit `lock_safety_blocked` before `connectEngine()`

This prevents the second maintenance caller from waiting on `acquireLock()` and producing raw PGLite timeout text. The fallback can be `maintenance_deferred` with a concise message that the command did not run because another PGLite owner is live and interactive requests should use the owner broker.

### D5. Per-command evidence can use lightweight real command entry

The requirement's matrix needs real command-level evidence, not full expensive maintenance work. Good tests can create a live lock and run:

- `gbrain sync --no-pull --no-embed --no-extract --yes`
- `gbrain embed --stale --dry-run`
- `gbrain extract --stale --dry-run`

With a live lock, the new pre-connect guard should return before any command-specific DB work, so these tests remain fast and prove the real dispatch path is protected. Help-only paths should not be used as evidence because they bypass DB ownership.

## Requirement Impact

None. The accepted requirements already permit `deferred_safe_fallback` for commands whose safe integration is too large for the slice. Research confirms that `sync`, `embed`, and `extract` should use `deferred_safe_fallback` for second maintenance callers in this slice, while successful maintenance owners continue to expose the broker for interactive requests.

## Open Questions

None blocking.

## Verification Obligations For Design

- Add or retain a queue-priority test showing interactive work beats maintenance-class queued work.
- Add real command-level tests for second `sync`, `embed`, and `extract` attempts under a live PGLite owner lock.
- Assert fallback output does not include raw PGLite lock timeout text.
- Assert help/no-owner public syntax remains unchanged.
- Rerun requirement 002 regression tests after implementation.
