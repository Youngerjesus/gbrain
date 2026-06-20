# Scenario Brake: PGLite Concurrency Verification

Status: SCENARIOS MISSING, reconciled into plan
Date: 2026-06-20
Reviewed plan: `plans/004-pglite-concurrency-verification/plan.md`

## Scenario Classes Reviewed

- Entry path: CLI direct-open, CLI brokered, stdio MCP owner, stdio MCP proxy, maintenance command.
- Actor: local CLI caller, first stdio MCP owner, second stdio MCP proxy, maintenance caller.
- State: absent lock, startup election held, live owner lock, live lock without socket, stale/dead lock, corrupt/unknown lock, stale operation socket.
- Dependency behavior: missing API keys, seeded keyword data, empty/no-result output, broker timeout, owner hang/exit.
- Runtime context: hermetic PGLite env, inherited DB env, JSON-RPC ordering, subprocess cleanup.
- Recovery/observability: stale socket recovery, post-timeout queue health, post-teardown re-entry, privacy-safe diagnostics.

## Key Parameters Identified

- Owner readiness before proxy starts.
- Whether `.gbrain-operation.sock` exists and is bound.
- Whether the second server is proxy mode or a direct owner race.
- Whether each operation is covered through CLI and MCP proxy paths.
- Whether results prove served data or merely absence of lock text.
- Whether stale/recovery statuses are asserted at command level or only primitive level.
- Whether diagnostics leak query text, params, source env, auth material, or local paths.

## Parameter Mutations Explored

- Proxy starts before owner socket is ready.
- Ambient `DATABASE_URL` or `GBRAIN_DATABASE_URL` bypasses PGLite.
- `think` has no model key.
- Seed import fails or returns empty results.
- Existing stale operation socket is present before real owner startup.
- Handler accepts a request, caller times out, handler later releases.
- Owner/proxy teardown leaves a stale live-looking lock/socket.
- Interactive caller arrives while operation startup election is held.

## Scenario Links And Separations

- CLI brokered and MCP proxy are separate entry paths, even when they share the IPC operation vocabulary.
- Covering `search` through CLI does not cover MCP proxy `search`.
- Lock primitive stale recovery is not the same as a command-level direct-open result after stale-lock recovery.
- Maintenance deferral is separate from interactive broker concurrency.
- `owner_starting` and `maintenance_deferred` are CLI preflight statuses, not IPC broker response statuses.

## What The Plan Already Covered

- One real owner stdio process.
- One second stdio MCP process.
- Concurrent CLI `query`, `search`, and `think`.
- Existing unit/integration evidence for stale socket, owner unreachable, completion unknown, lock safety, maintenance deferral, and no-owner direct-open.
- Docs update targets for architecture and engine docs.

## Missing Or Conflated Scenarios

- MCP proxy `search` missing from the real E2E.
- Positive proxy-mode proof missing: lock/socket readiness and proxy-only `tools/list`.
- Hermetic PGLite assertion missing: DB env must be cleared and config must be checked.
- Stale-lock recovery needs command-level direct-open evidence.
- Post-owner/proxy teardown re-entry missing.
- `completion_unknown` needs a follow-up request to prove queue health.
- Interactive startup race/status behavior needs command-level evidence.
- Privacy-safe diagnostics need broader evidence than private query text.
- README contains known stale operator guidance and must be updated.

## Recommended Scenario Additions

- Serial E2E should run three MCP proxy calls (`query`, `search`, `think`) and at least three CLI calls concurrently.
- Serial E2E should assert seeded marker results for at least proxy/CLI `query` or `search`.
- Serial E2E should fail on `owner_unreachable`, `broker_timeout`, or `completion_unknown` during AC1/AC2 proof.
- Serial E2E should terminate owner/proxy and then prove fresh direct-open or fresh-owner re-entry.
- Command-level tests should cover stale-lock direct-open, post-timeout queue usability, startup-election interactive status, and privacy redaction/status safety.

## Companion Review Synthesis

All three scenario companions returned `[SCENARIOS MISSING]`. Findings were accepted except for broadening the E2E into MCP owner direct-user-call coverage, which is separable if closeout claims remain narrow. JSON-RPC out-of-order responses are not a separate scenario if helpers match responses by `id`.

## Overall Verdict

`[SCENARIOS MISSING]` before reconciliation. The missing scenarios have been reconciled into `technical-design.md` and `plan.md`; implementation may proceed once the primary and secondary plans are accepted.
