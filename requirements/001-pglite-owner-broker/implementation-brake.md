---
requirement_id: 001-pglite-owner-broker
status: SHIP
review_mode: recent_diff_review
reviewed_worktree: /Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker
reviewed_branch: codex/001-pglite-owner-broker
reviewed_at: 2026-06-20 16:20 KST
---

# Implementation Brake

## Implementation Under Review

This review covers the PGLite owner-broker slice for local `query`, `search`, and `think` concurrency:

- non-acquiring PGLite lock classification
- local operation IPC queue and priority transport
- CLI pre-connect broker routing and direct-open fallback
- stdio MCP proxy routing when an owner already exists
- shared broker dispatch for CLI-owned and MCP-owned brokers
- focused docs and regression tests

The implementation lives in `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker` on branch `codex/001-pglite-owner-broker`.

## Findings

No unresolved `must fix now` findings remain for requirement 001.

Accepted companion findings were repaired:

- Cold-start race: added startup election so simultaneous no-owner eligible callers do not all direct-open.
- Timeout ambiguity: request-sent broker timeout now reports `completion_unknown`.
- Closed queued clients: owner skips queued requests whose clients close before handler start.
- Corrupt/unknown lock states: CLI emits `lock_safety_blocked` instead of falling into normal PGLite lock wait.
- MCP dispatch parity: both CLI-owned and MCP-owned brokers now use shared broker dispatch; `mcp-stdio` requests route through `dispatchToolCall`.
- `think` parity: brokered CLI `think` preserves JSON/text output, calibration flags, and `--save` failure semantics.
- Stale operation socket recovery: startup emits `stale_socket_recovered` diagnostic state and owner-visible stderr diagnostic.
- Coverage gaps: added tests for no-owner `query`/`think`, mixed CLI+MCP five-caller concurrency, second stdio MCP proxy `query/search/think`, stale recovery diagnostics, source handoff, corrupt lock safety, and MCP invalid params envelope.

## Open Blockers

None for this slice.

## What Can Be Deferred

Full public forwarding/yield behavior for real `sync`, `embed`, and `extract` maintenance commands remains deferred to later sequence slices. Requirement 001 only ships the operation broker boundary, request class/priority fields, and queue-priority seam; `test/pglite-operation-ipc.test.ts` verifies interactive queue priority over synthetic maintenance work.

## Verification Result

Executed in `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`:

```bash
bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts --timeout 60000 && bun run typecheck
```

Result: 79 tests passed, 0 failures; `tsc --noEmit` passed.

Targeted earlier repair verification:

```bash
bun test test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts --timeout 60000
bun run typecheck
```

Result: 18 tests passed, 0 failures; `tsc --noEmit` passed.

## UltraQA Matrix Result

UltraQA scenario matrix was triggered because this change touches queueing, restart/recovery, local service boundaries, CLI/MCP protocol behavior, and operator diagnostics.

| ID | Scenario | Expected signal | Actual result | Evidence |
| --- | --- | --- | --- | --- |
| U1 | Five concurrent CLI callers while owner is live | Requests queue/serve without PGLite lock timeout | Passed | `five concurrent query callers proxy...` |
| U2 | Mixed `query`/`search`/`think` callers | Interactive requests all route to owner broker | Passed | `mixed concurrent query search and think...` |
| U3 | Five simultaneous mixed CLI and MCP callers | Shared live owner broker handles all callers | Passed | `five simultaneous mixed CLI and MCP callers...` |
| U4 | No owner exists | CLI can direct-open for `query` and `think` | Passed | `no-owner query and think keep direct-open CLI behavior` |
| U5 | Corrupt lock file | Fast `lock_safety_blocked`, no normal lock wait | Passed | `corrupt lock state fails fast...` |
| U6 | Stale operation socket | Socket recovery reports `stale_socket_recovered` | Passed | `server start reports stale socket recovery...` |
| U7 | Client timeout after request accepted | Reports `completion_unknown` | Passed | `broker timeout after request send...` |
| U8 | Client closes while queued | Handler is not run for dropped request | Passed | `closed clients are removed from the queue...` |
| U9 | MCP invalid params through CLI-owned broker | Preserves MCP `invalid_params` envelope | Passed | `CLI-owned broker dispatch preserves MCP invalid_params envelope` |
| U10 | Second stdio MCP server while owner exists | Proxies `query/search/think`, does not open PGLite directly | Passed | `second stdio MCP serve proxies...` |

No temporary runtime debris is intentionally retained outside tracked/untracked implementation files.

## Ship-Readiness Verdict

[SHIP]

Requirement 001 is ready for closeout. The remaining sequence outcome still depends on later slices for broader maintenance command priority behavior and production-readiness review.
