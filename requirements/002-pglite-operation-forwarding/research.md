---
requirement_id: 002-pglite-operation-forwarding
status: Complete
created_at: 2026-06-20 16:45 KST
---

# Research

## Question

Does requirement 002 need new implementation, or can it close by revalidating requirement 001's current owner-forwarding implementation?

## Findings

### R1. Current implementation already owns the required forwarding seam

- Evidence: `src/cli.ts` calls `maybeRunBrokeredOperation` before shared operation dispatch and `maybeRunBrokeredThink` before CLI-only `think` execution.
- Evidence: `src/cli.ts` uses `classifyPgliteLock` and forwards live-lock `query`, `search`, and `think` through `forwardToLivePgliteOwner`.
- Evidence: `src/mcp/server.ts` starts a PGLite operation IPC server for owner stdio MCP and a second stdio MCP proxy for `query`, `search`, and `think` when a live lock exists.
- Decision: no new owner-discovery module is required for this slice unless later review finds a missed caller path.

### R2. Forwarding transport is local-only and operation-level

- Evidence: `src/core/pglite-operation-ipc.ts` uses a filesystem socket path under the PGLite data directory via `operationSocketPath(dataDir)`.
- Evidence: the protocol carries operation names, params, caller type, request class, priority, and context; it does not expose raw SQL.
- Decision: AC5 is satisfiable by current code evidence plus IPC tests.

### R3. Owner-side dispatch parity is implemented through a shared broker dispatch helper

- Evidence: `src/core/pglite-operation-dispatch.ts` routes `mcp-stdio` broker requests through `dispatchToolCall` with `remote: true`, `takesHoldersAllowList: ['world']`, source id, and hot-memory meta hook.
- Evidence: CLI broker requests validate params, build local operation context, and resolve source id from explicit source, env source, or caller cwd.
- Decision: AC4 is satisfiable by current code and tests.

### R4. Existing tests cover the forwarding acceptance surface

- Evidence: `test/cli-pglite-operation-broker.test.ts` covers:
  - CLI-owned MCP invalid params envelope
  - five concurrent query callers through a live owner
  - mixed concurrent query/search/think callers
  - no-owner query and think direct-open behavior
  - five simultaneous mixed CLI and MCP callers
  - caller cwd source handoff
  - corrupt lock `lock_safety_blocked`
  - second stdio MCP proxy query/search/think tools
- Evidence: `test/pglite-operation-ipc.test.ts` covers absent socket, stale socket recovery, request-sent timeout as `completion_unknown`, and closed-client queue skip.
- Decision: AC1, AC2, AC3, AC4, and AC6 are covered by current test names and should be re-run during this slice.

## AC-To-Evidence Map

| AC | Current evidence | Research conclusion |
| --- | --- | --- |
| AC1 CLI owner discovery before direct PGLite open | `src/cli.ts` `maybeRunBrokeredOperation`, `maybeRunBrokeredThink`; `mixed concurrent query search and think callers proxy...` | Covered, re-run tests |
| AC2 second stdio MCP proxy | `src/cli.ts` `maybeRunBrokeredMcpServe`; `src/mcp/server.ts` `startMcpOperationProxyServer`; `second stdio MCP serve proxies...` | Covered, re-run tests |
| AC3 no-owner direct-open compatibility | `no-owner query and think keep direct-open CLI behavior`; search direct-open remains existing command behavior from prior search dispatch tests | Covered enough for planning; plan should mention search no-owner evidence is indirect unless broadened |
| AC4 caller semantic preservation | `dispatchBrokeredOperation`; `CLI-owned broker dispatch preserves MCP invalid_params envelope`; `brokered CLI requests carry caller cwd...`; takes allow-list tests in related suite | Covered, re-run tests |
| AC5 local-only operation-level forwarding | `operationSocketPath`; IPC protocol types; no SQL fields in request | Covered by code evidence |
| AC6 deterministic safe failure states | IPC tests for unavailable socket, completion_unknown, stale recovery, closed client; CLI corrupt lock test | Covered, re-run tests |
| AC7 reuse current implementation only with mapping | this research artifact | Covered |

## Decision

This slice should proceed as a verification/revalidation-heavy requirement. New implementation is not currently required. The draft plan should focus on:

1. preserving the AC-to-evidence map,
2. re-running focused forwarding tests,
3. adding only small missing test evidence if reviewers reject indirect coverage, and
4. closing through implementation-brake if no fresh gaps appear.

## Residual Risk

- No-owner `search` direct-open compatibility is less directly asserted than no-owner `query` and `think`; existing `cli-search-dispatch` tests prove direct command dispatch but not the exact no-owner PGLite setup used for `query`/`think`.
- HTTP MCP forwarding remains out of scope.
- Maintenance priority/yield behavior remains out of scope for requirement 003.

## Requirement Impact

None. The accepted requirement remains valid.

## Next Step

Evaluate technical-design. Because no new implementation boundary appears necessary, technical-design may be marked `not_required` if the plan records current design reuse and the residual no-owner search evidence question.
