# Implementation Brake: PGLite Concurrency Verification

Date: 2026-06-20
Task worktree: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`
Requirement: `requirements/004-pglite-concurrency-verification/requirements.md`
Verdict: `[SHIP]`

## Implementation Under Review

Requirement 004 added integrated verification and documentation for local
PGLite concurrent access:

- `test/pglite-concurrent-access.serial.test.ts` proves a real stdio MCP owner,
  a second stdio MCP proxy, and concurrent CLI/MCP `query`/`search`/`think`
  callers against a seeded PGLite brain.
- `test/cli-pglite-operation-broker.test.ts` now covers stale/dead lock
  direct-open recovery, post-`completion_unknown` queue usability,
  startup-election interactive status, and privacy-safe broker/status
  diagnostics.
- `README.md`, `docs/ENGINES.md`, and
  `docs/architecture/serve-sync-concurrency.md` now describe interactive owner
  broker routing separately from maintenance deferral.

## Findings

No implementation defects found that block ship-readiness.

### Conformance Finding Reconciled

- Finding: AC8 closeout matrix is not yet present.
- Source: Requirement Conformance Reviewer `019ee3df-06be-7041-ac00-d81179eee06c`.
- Disposition: accepted as a closeout-gate obligation, not an implementation
  defect. AC8 explicitly asks for the closeout evidence matrix, so it must be
  satisfied in `closeout.md` before requirement 004 can be marked
  `[CLOSED_COMMITTED]`.
- Ship impact: does not block implementation-brake `[SHIP]`; blocks closeout
  completion until the matrix exists.

## What Must Be Fixed Now

None.

## Open Blockers

None for implementation-brake. Closeout remains blocked until it records the
AC8 evidence matrix with behavior, evidence type, exact path, and CLI/MCP
coverage.

## What Can Be Deferred

- Multi-machine or networked PGLite concurrency remains out of scope.
- True maintenance command broker execution remains out of scope and would need
  a separate requirement.

## Verification Result

- `bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000`
  - Result: 1 pass, 0 fail.
  - Proves: real subprocess owner/proxy topology, six mixed CLI/MCP interactive
    calls, proxy-only tool surface, seeded marker results, post-teardown
    direct-open re-entry, and no raw PGLite lock timeout.
- `bun test test/cli-pglite-operation-broker.test.ts --timeout 60000`
  - Result: 27 pass, 0 fail.
  - Proves: command-level broker forwarding, no-owner direct-open,
    stale/dead-lock direct-open recovery, missing owner socket, corrupt lock,
    startup-election status, `completion_unknown` queue recovery, maintenance
    deferral, MCP proxy source/auth preservation, and privacy-safe diagnostics.
- `bun test test/pglite-concurrent-access.serial.test.ts test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000`
  - Result: 103 pass, 0 fail.
  - Proves: requirement 001-003 regression surface stayed green.
- `bun run typecheck`
  - Result: `tsc --noEmit` passed.

## UltraQA Matrix Result

UltraQA matrix was triggered because this implementation changes CLI/MCP
operator-facing behavior, subprocess E2E, timeouts, stale state, and diagnostics.

| ID | Scenario | User/attacker model | Setup | Expected signal | Actual result | Evidence | Cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U1 | Real owner/proxy mixed concurrency | Local user with MCP server plus CLI | Real stdio owner, second stdio proxy, three MCP calls, three CLI calls | Served marker results, proxy-only tools, no raw lock timeout | Pass | `test/pglite-concurrent-access.serial.test.ts`; serial test passed | Test kills owner/proxy and removes temp dirs |
| U2 | Ambient DB env bypass | Developer shell has DB env | E2E fixture clears `DATABASE_URL` / `GBRAIN_DATABASE_URL` and asserts `engine: pglite` | PGLite path only | Pass | E2E env and config assertions | Temp `GBRAIN_HOME` removed |
| U3 | Stale/dead lock direct-open | Stale owner left lock file | Dead pid lock before CLI query | Direct-open result, no broker/safety status | Pass | `dead or stale PGLite lock recovers...`; broker suite passed | Temp home removed |
| U4 | Timeout recovery | Owner accepts request but caller times out | Handler gated until after `completion_unknown` | Later request served normally | Pass | `CLI caller surfaces completion_unknown...`; broker suite passed | IPC server closed |
| U5 | Startup race | Caller arrives while owner election held | `tryAcquireOperationStartup` held during CLI query | Deterministic non-lock status | Pass | `interactive caller during owner startup election...`; broker suite passed | Startup lock released |
| U6 | Privacy sentinels | User-controlled query/source/auth/path-ish values | Private sentinels in query/env/lock command | Status diagnostics do not echo sentinels | Pass | `broker failure diagnostics do not echo...`; broker suite passed | Temp homes removed |
| U7 | Stale docs | Operator reads old serve/sync guidance | README, ENGINES, serve-sync docs inspected | Interactive broker and maintenance deferral separated | Pass | `rg` check found no stale blanket guidance; docs updated | N/A |

No matrix row is failed, skipped, or missing evidence.

## Requirement Conformance Evidence

- Conformance reviewer status: `FINDINGS`.
- AC1-AC7: reviewer found covered.
- AC8: reviewer found missing because closeout had not yet been created.
- Reconciliation: AC8 is a closeout artifact requirement. Closeout must include
  the required evidence matrix before requirement 004 can close.
- Residual risk: local-only subprocess behavior is proven; multi-machine and
  network broker behavior are explicitly out of scope.

## Ship-Readiness Verdict

`[SHIP]`

Implementation is ready for closeout. Closeout must satisfy the accepted AC8
finding before marking requirement 004 `[CLOSED_COMMITTED]`.
