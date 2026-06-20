# Plan: PGLite Priority Scheduler

Status: accepted

## Source Artifacts

- Requirement: `requirements/003-pglite-priority-scheduler/requirements.md`
- Research: `requirements/003-pglite-priority-scheduler/research.md`
- Technical design: `requirements/003-pglite-priority-scheduler/technical-design.md`
- Task worktree: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`

## Objective

Add bounded PGLite maintenance contention behavior so `sync`, `embed`, and `extract` do not produce raw PGLite lock timeouts when another live owner exists, while preserving interactive `query`, `search`, and `think` priority through the existing owner broker.

## Implementation Steps

1. Add a scoped maintenance command set in `src/cli.ts` for `sync`, `embed`, and `extract`.
2. Add a `maybeDeferPgliteMaintenanceCommand()` helper that:
   - ignores non-maintenance and non-PGLite configs
   - allows absent locks to proceed only when startup election is acquired
   - returns deterministic `owner_starting` when a PGLite owner appears to be starting before the socket is bound
   - allows stale/dead locks to proceed through existing recovery
   - emits deterministic `maintenance_deferred` for live locks
   - emits deterministic `lock_safety_blocked` for corrupt/unknown locks
3. Call the helper in `handleCliOnly()` after help/no-DB bypasses and before watchdog setup plus `connectEngine()`.
4. Add CLI tests in `test/cli-pglite-operation-broker.test.ts` for real `sync`, `embed`, and `extract` command dispatch under a live owner lock.
5. Add focused tests for startup-election-held and corrupt-lock maintenance fallback.
6. Add no-owner direct-open smoke evidence for `sync`, `embed`, and `extract` or record why an existing command test covers it.
7. Preserve existing IPC priority tests and requirement 002 regression tests.
8. In closeout, classify `sync`, `embed`, and `extract` as `deferred_safe_fallback` unless implementation actually adds and verifies real maintenance queuing.

## Acceptance Evidence Targets

| AC | Evidence target |
| --- | --- |
| AC1 | Add or preserve an automated maintenance-owner or maintenance-like-owner test proving interactive callers proxy while the owner is live and do not direct-open into lock timeout. |
| AC2 | `test/pglite-operation-ipc.test.ts` priority test stays green. |
| AC3 | Closeout states priority is queue-boundary only. |
| AC4 | New real command tests show no raw PGLite lock timeout for second maintenance calls. |
| AC5 | Closeout matrix classifies `sync`, `embed`, and `extract` as `deferred_safe_fallback`. |
| AC6 | No public syntax changes. |
| AC7 | No network/raw SQL forwarding added. |
| AC8 | Requirement 002 regression suite rerun. |

## Verification Commands

```bash
bun test test/cli-pglite-operation-broker.test.ts --test-name-pattern "maintenance" --timeout 60000
bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000
bun run typecheck
```

## Risks

- The fallback copy could overpromise queueing. Use `maintenance_deferred`, not `maintenance_queued`.
- Tests must fail if the fallback copy implies the command was queued or completed.
- Guard placement could accidentally affect help/no-DB commands. Keep it after existing help bypasses.
- Guard could block stale recovery. Let `dead_or_stale_recoverable` proceed through existing lock acquisition.
- Startup election could be held while no socket exists. Return `owner_starting` rather than direct-opening.
