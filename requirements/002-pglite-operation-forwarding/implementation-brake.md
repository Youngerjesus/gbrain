---
requirement_id: 002-pglite-operation-forwarding
review_type: implementation-brake
status: completed
verdict: SHIP
created_at: 2026-06-20 18:45 KST
---

# Implementation Brake

## Implementation Under Review

- Mode: recent diff review plus requirement conformance review
- Requirement: `requirements/002-pglite-operation-forwarding/requirements.md`
- Target worktree: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`
- Target branch: `codex/001-pglite-owner-broker`
- Base implementation commit before requirement 002 changes: `d50dc7016319254a941a213534ca4c79d865226f`
- Scope: PGLite operation forwarding for CLI and stdio MCP `query`, `search`, and `think`; no-owner direct-open behavior; MCP source/auth parity; deterministic failure states.

## Findings

### F1 - `gbrain serve` did not block corrupt/unknown PGLite locks

- Finding kind: missing behavior
- Risk category: edge/failure path, lock safety
- Disposition: must fix now
- Issue: `maybeRunBrokeredMcpServe` proxied only on `lock.status === 'live'`; corrupt/unknown lock states fell through to direct `serve` handling, which could open/clean PGLite past an ambiguous lock.
- Fix: Added `lock_safety_blocked` fast-fail for corrupt/unknown lock states in `maybeRunBrokeredMcpServe`.
- Red proof: `bun test test/cli-pglite-operation-broker.test.ts --test-name-pattern "stdio MCP serve fails fast|direct stdio MCP no-owner search" --timeout 60000` failed with `stdio MCP serve fails fast on corrupt lock...` receiving `timedOut: true`.
- Green proof: Same targeted command passed after the fix.

### F2 - Direct stdio MCP source/auth parity needed surface evidence

- Finding kind: verification gap
- Risk category: test gap, trust boundary
- Disposition: must fix now
- Issue: Brokered MCP source/auth forwarding was tested, but direct stdio MCP no-owner behavior did not have JSON-RPC surface evidence proving `GBRAIN_FEDERATED_READ` becomes `auth.allowedSources`.
- Fix/evidence: Added direct stdio MCP no-owner `search` test with `search.mcp_keyword_only=true`, seeded pages across sources, and asserted only `GBRAIN_FEDERATED_READ` sources are returned.
- Red proof: Not applicable for production code because the behavior was already implemented; this was a required evidence-gap test. The same targeted command passed once the evidence test was added.
- Green proof: Full related suite passed.

## What Must Be Fixed Now

All must-fix findings were closed before ship.

## Open Blockers

None.

## What Can Be Deferred

- Permission-denied and not-yet-bound socket states remain covered by lower-level unavailable/owner-unreachable behavior rather than separate surface tests. Conformance re-review accepted this as non-blocking residual risk.
- Requirement 003 maintenance priority/yield for `sync`, `embed`, and `extract` remains explicitly out of scope.

## Verification Result

Targeted red/green:

```bash
bun test test/cli-pglite-operation-broker.test.ts --test-name-pattern "stdio MCP serve fails fast|direct stdio MCP no-owner search" --timeout 60000
```

- Red before F1 fix: failed because corrupt-lock `serve` timed out instead of fast-failing.
- Green after F1 fix: 2 pass, 0 fail.

Full related verification:

```bash
bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000 && bun run typecheck
```

- Result: 90 tests passed, 0 failed; `tsc --noEmit` passed.

## Requirement Conformance

- Initial conformance reviewer: `019ee39c-e57e-7482-add9-dcd9b6848097`
- Initial status: `FINDINGS`
- Findings: F1 corrupt/unknown MCP `serve` lock safety gap; F2 direct stdio MCP source/auth evidence gap.
- Re-review conformance reviewer: `019ee3a4-459a-7ca3-a3e5-ceae8133d0e3`
- Re-review status: `CONFORMANT`
- Unresolved conformance findings: none
- Residual risk accepted: permission-denied/not-yet-bound socket separate surface tests are deferred because current unavailable/connect-failure path maps to `owner_unreachable`; requirement 003 remains out of scope.

## UltraQA Matrix Result

UltraQA scenario matrix was triggered because this change touches CLI/service/control-plane behavior, lock safety, timeout handling, and operator-facing failure output.

| ID | Scenario | Expected signal | Actual result | Evidence |
| --- | --- | --- | --- | --- |
| U1 | Five concurrent CLI `query` callers with live owner | no PGLite lock timeout; all served by owner | pass | `test/cli-pglite-operation-broker.test.ts` |
| U2 | Mixed CLI/MCP `query`/`search`/`think` callers with live owner | five callers complete through owner | pass | `test/cli-pglite-operation-broker.test.ts` |
| U3 | No-owner CLI direct-open for all three operations | direct behavior preserved, no broker-only error | pass | no-owner query/search/think test |
| U4 | Direct stdio MCP no-owner with federated read | allowed sources applied through `auth.allowedSources` | pass | direct MCP federated-read search test |
| U5 | Brokered MCP with federated read | source/auth context forwarded to owner | pass | second stdio MCP proxy source-auth test |
| U6 | Corrupt lock for CLI query | `lock_safety_blocked`, no lock timeout | pass | corrupt lock query test |
| U7 | Corrupt lock for stdio `serve` | `lock_safety_blocked`, no open/cleanup/hang | pass after F1 fix | corrupt lock serve test |
| U8 | Accepted request times out | `completion_unknown`, exit 124, no success-like payload | pass | CLI completion_unknown test |
| U9 | Owner lock live but socket absent | owner_unreachable, no PGLite lock wait | pass | CLI and MCP owner_unreachable tests |
| U10 | Stale socket recovery | safe remove/recreate diagnostic and served request | pass | `test/pglite-operation-ipc.test.ts` |

## Ship-Readiness Verdict

[SHIP]

The implementation satisfies AC1-AC7 with current tests and conformance evidence. No blocking findings remain.
