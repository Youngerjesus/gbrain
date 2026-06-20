# Closeout: PGLite Concurrency Verification

Date: 2026-06-20
Verdict: `[CLOSED_COMMITTED]`
Task worktree: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`
Requirement: `requirements/004-pglite-concurrency-verification/requirements.md`

## Summary

Requirement 004 is complete at the implementation level. The slice adds
real-subprocess proof for local PGLite concurrent interactive access, strengthens
recovery/diagnostic command-level coverage, and updates operator docs so
interactive broker routing is no longer confused with maintenance deferral.

## Evidence Matrix

| Behavior | Evidence type | Exact path | CLI coverage | MCP coverage | Result |
| --- | --- | --- | --- | --- | --- |
| Real stdio owner and second stdio proxy serve mixed interactive callers with no raw PGLite lock timeout | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` | CLI `query`, `search`, `think --json` run concurrently and exit 0 | Proxy MCP `query`, `search`, `think` run concurrently through second stdio server | Covered; serial test passed |
| Second stdio MCP server is actually proxy mode | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` | N/A | `tools/list` exposes only `query`, `search`, `think` | Covered; serial test passed |
| Seeded owner-served results prove route success rather than absence of lock text | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` | CLI `query`/`search` stdout includes seeded marker | Proxy MCP `query`/`search` result includes seeded marker | Covered; serial test passed |
| Post-teardown re-entry after owner/proxy exits | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` | Fresh direct-open CLI `query` succeeds after owner/proxy termination | N/A | Covered; serial test passed |
| No-owner direct-open fallback remains intact | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query`, `search`, `think --json`, plus maintenance direct paths | Direct stdio no-owner source-scope search covered separately in same file | Covered; broker suite passed |
| Dead/stale PGLite lock recovers into normal direct-open command behavior | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query` succeeds with no broker/safety/raw lock error | N/A | Covered; broker suite passed |
| Live owner lock with missing broker socket reports `owner_unreachable` | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query` returns `owner_unreachable` without raw lock timeout | Second stdio MCP proxy returns MCP error envelope with `owner_unreachable` | Covered; broker suite passed |
| Accepted request timeout reports `completion_unknown` and queue remains usable | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query` returns `completion_unknown`; later CLI `query` is served normally | IPC-level timeout status covered in `test/pglite-operation-ipc.test.ts` | Covered; broker suite and IPC suite passed |
| Corrupt/unknown PGLite lock reports `lock_safety_blocked` and does not clean/open unsafely | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query`, maintenance caller paths | stdio MCP `serve` corrupt-lock path | Covered; broker suite passed |
| Interactive caller during startup election gets deterministic non-lock status | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `query` returns `owner_unreachable` without raw lock timeout | N/A | Covered; broker suite passed |
| Maintenance commands defer under live owner and do not claim queued/completed execution | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI `sync`, `embed`, `extract` return `maintenance_deferred` | N/A | Covered; broker suite passed |
| MCP proxy preserves source/auth context | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts`, `test/mcp-stdio-source-scope.test.ts` | Brokered CLI cwd/source resolution covered | Proxy MCP forwards `GBRAIN_SOURCE` and `GBRAIN_FEDERATED_READ` auth context | Covered; broker/source-scope suites passed |
| Diagnostics do not echo private query text, params, source/federated env, auth, or maintenance sentinels | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` | CLI failure/status diagnostics covered | MCP/auth sentinel path covered through proxy context tests | Covered; broker suite passed |
| Stale operation socket recovery emits `stale_socket_recovered` and new owner serves request | `ipc_unit` | `test/pglite-operation-ipc.test.ts` | N/A | IPC owner startup recovers stale socket and serves request | Covered; IPC suite passed |
| Live socket is not unlinked by another owner | `ipc_unit` | `test/pglite-operation-ipc.test.ts` | N/A | IPC startup does not steal live socket | Covered; IPC suite passed |
| Priority ordering keeps interactive work ahead of lower-priority queued work | `ipc_unit` | `test/pglite-operation-ipc.test.ts` | Applies to IPC broker requests | Applies to IPC broker requests | Covered; IPC suite passed |
| Live PGLite lock is not stolen; dead/stale lock recovery remains safe | `ipc_unit` | `test/pglite-lock.test.ts` | Lock primitive used by CLI preflight | Lock primitive used by MCP serve/proxy preflight | Covered; lock suite passed |
| Operator docs separate interactive broker routing from maintenance deferral | `doc_update` | `docs/architecture/serve-sync-concurrency.md` | CLI examples and status/action table | stdio MCP owner/proxy behavior documented | Covered; docs updated and stale text check passed |
| Engine docs describe current PGLite concurrency contract | `doc_update` | `docs/ENGINES.md` | CLI direct-open and broker routing documented | second stdio proxy test/behavior documented | Covered; docs updated |
| README troubleshooting no longer gives blanket stop-serve guidance | `doc_update` | `README.md` | interactive vs maintenance behavior clarified | MCP owner guidance linked to triage doc | Covered; docs updated |

## Verification Run

- `bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000`
  - Result: 1 pass, 0 fail.
- `bun test test/cli-pglite-operation-broker.test.ts --timeout 60000`
  - Result: 27 pass, 0 fail.
- `bun test test/pglite-concurrent-access.serial.test.ts test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000`
  - Result: 103 pass, 0 fail.
- `bun run typecheck`
  - Result: `tsc --noEmit` passed.
- `rg -n 'stop \`gbrain serve\` before|stop .*gbrain serve.*sync|Maintenance forwarding/yield|maintenance_deferred|owner broker|owner_unreachable|completion_unknown|stale_socket_recovered' README.md docs/ENGINES.md docs/architecture/serve-sync-concurrency.md -S`
  - Result: no stale blanket guidance remained; remaining hits describe the new contract/status vocabulary.

## TDD / Red-Green Notes

- Red proof: the new real-subprocess E2E initially failed because the owner held
  a live PGLite lock but no operation socket was observed. This proved the new
  positive owner/proxy assertion could catch a gap that absence-of-lock-text
  checks would miss.
- Green proof: the fixture moved to short `/tmp` paths to avoid macOS Unix
  socket path length issues; the E2E then passed without product-code changes.
- Command-level recovery and diagnostic tests passed on first run after being
  added, confirming existing implementation already satisfied those stricter
  contracts.
- Documentation changes used the pragmatic exception path; they were constrained
  by `rg` inspection and the verification suite above.

## Implementation-Brake Result

- `requirements/004-pglite-concurrency-verification/implementation-brake.md`
  returned `[SHIP]`.
- Conformance reviewer found AC1-AC7 covered and AC8 pending closeout matrix.
- This closeout satisfies AC8.

## Context Sync

Active context changed in product/operator documentation only. Updated:

- `README.md`
- `docs/ENGINES.md`
- `docs/architecture/serve-sync-concurrency.md`

No AGENTS/CLAUDE workflow policy change was required.

## Refactor Notes

Code work was limited to tests. A bounded touched-area review found no safe,
useful behavior-preserving refactor worth taking in closeout. The new E2E
helpers are local to the serial test because they are fixture-specific and avoid
introducing shared test abstractions before a second real consumer exists.

## Follow-Up Routing

- Requirement 005 remains the next sequence item and owns production readiness.
- True broker execution for maintenance commands remains out of scope and should
  require a separate requirement if desired later.

## Commit

Local commit created in the task worktree during closeout.
