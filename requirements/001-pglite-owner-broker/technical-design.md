# Technical Design: PGLite Owner Broker

Created: 2026-06-20
Status: Complete
Requirement source: requirements/001-pglite-owner-broker/requirements.md
Research source: requirements/001-pglite-owner-broker/research.md
Architecture artifact: requirements/001-pglite-owner-broker/architecture.md

## Requirement Coverage

| Requirement / Acceptance Criterion | Design mapping |
| --- | --- |
| AC1 owner alive prevents second direct open | `src/cli.ts` and MCP startup paths run a pre-connect broker probe for eligible PGLite commands. If broker is reachable, caller forwards to owner and never calls `connectEngine()`. If a live lock exists but broker is unreachable, caller returns `lock_safety_blocked` / `owner_unreachable` without waiting for PGLite lock timeout. |
| AC2 no owner direct-open fallback | Broker client returns `unavailable` quickly when no socket/owner exists. Existing `connectEngine()` path remains unchanged and opens PGLite directly. |
| AC3 five simultaneous mixed callers | Operation IPC server accepts multiple local connections, enqueues request objects, executes them through the owner engine, and responds per request. Integration tests launch one owner plus at least five CLI/MCP-shaped callers and assert no lock timeout strings. |
| AC4 interactive priority over maintenance | Request schema includes `class: interactive | maintenance` and `priority`. Broker queue orders interactive ahead of maintenance and this slice must prove that ordering with a synthetic or real maintenance request admitted through the same queue. Full `sync`/`embed`/`extract` command forwarding/yield behavior is completed in the later priority-scheduler slice and must not be claimed complete here. |
| AC5 MCP trust boundary | Forwarded MCP requests carry `DispatchOpts` fields: `remote: true`, `takesHoldersAllowList: ['world']`, `sourceId`, and optional `auth.allowedSources`. Owner calls `dispatchToolCall(engine, name, params, opts)` rather than reconstructing trust from its own process defaults. |
| AC6 CLI compatibility | Public command syntax is unchanged. CLI parser builds the same params before forwarding. Forwarded CLI responses return stdout/stderr/exitCode envelopes that the original command path prints/applies. |
| AC7 stale owner recovery | Owner bind cleans stale socket files. Database lock recovery remains in `pglite-lock.ts`; live heartbeat locks are never removed by broker code. Optional lock classification helper may be added for diagnostics only. |
| AC8 diagnostics | Broker response envelope includes `ok`, `status`, `queued_ms`, `served_ms`, `owner_pid`, and `message`. CLI/MCP tests assert deterministic statuses/messages for queued, served, owner-unreachable, stale-socket-recovered, and lock-safety-blocked cases. |

## Module Design

- Module boundaries:
  - `src/core/pglite-operation-ipc.ts`
    - Exports socket path helper, request/response types, `forwardOperationViaIpc()`, `startPgliteOperationIpcServer()`, stale socket cleanup, and queue scheduler.
    - Owns protocol limits: short connect timeout, max message bytes, one response line, local-only socket permissions.
    - Accepts an injected owner handler. It must not import `src/mcp/dispatch.ts`, CLI command modules, or operation business logic directly.
  - `src/core/pglite-lock.ts`
    - Exposes a non-acquiring, non-stealing lock classifier such as `classifyPgliteLock(dataDir)` for broker preflight diagnostics and direct-open decisions.
    - Authoritative statuses should include at least: `absent`, `live`, `dead_or_stale_recoverable`, `corrupt_recoverable`, and `unknown`.
    - The classifier never deletes a live heartbeat lock and never waits on the normal `acquireLock()` timeout loop.
    - `unknown` and live-lock-with-unreachable-broker states must not fall through to direct `connectEngine()`; they return bounded broker/lock-safety diagnostics.
  - `src/mcp/server.ts`
    - Starts operation IPC server for file-backed PGLite after MCP transport is connected.
    - Builds owner-side handlers that call `dispatchToolCall()` for MCP requests and shared operation handlers for CLI-shaped requests.
    - Closes both resolve IPC and operation IPC on shutdown.
  - `src/cli.ts`
    - Adds a pre-connect broker routing seam after argument parsing/thin-client handling and before `connectEngine()`.
    - Classifies only accepted command surfaces for this slice: `query`, `ask`, `search` free-text where mapped to the search operation, and `think`.
    - Adds a concrete pre-connect branch for CLI-only `think`, because today `think` reaches the generic CLI-only `connectEngine()` path before `runThinkCli()`.
    - Carries raw source-resolution inputs such as caller cwd, explicit `--source` or operation param, and relevant env-derived source defaults so the owner can resolve source scope with its connected engine instead of recomputing from owner-only process state.
    - Falls back to existing direct-open path when no broker is reachable and no live lock safety condition blocks direct open.
    - Returns `lock_safety_blocked` without direct-open when lock classifier reports a live owner and broker is unreachable.
  - `src/commands/think.ts`
    - Extracts parse/build/render helpers so CLI `think` can forward a typed `think` operation request and render the owner response without duplicated parsing.
  - `src/commands/search.ts`
    - Keeps `modes/stats/tune/diagnose` behavior explicit. Free-text `gbrain search "<query>"` forwarding maps to operation `search` with parsed limit/offset/mode if supported by CLI parser.
  - `src/mcp/server.ts` proxy path
    - Adds an owner-proxy mode for a second stdio MCP process that cannot open PGLite because a live owner exists. The proxy must expose the same broker-eligible tool definitions and forward `query`, `search`, and `think` over operation IPC.
    - `serve --http` is not part of this first slice's broker wire contract unless a later requirement explicitly adds HTTP owner binding and tests.
- Public interfaces:
  - `operationSocketPath(dataDir: string): string`
  - `forwardOperationViaIpc(socketPath, req, opts): Promise<OperationIpcResponse | typeof OPERATION_IPC_UNAVAILABLE>`
  - `startPgliteOperationIpcServer(socketPath, handler, opts): Promise<net.Server | null>`
  - `OperationIpcRequest`
    - `requestId`
    - `protocolVersion`
    - `caller: 'cli' | 'mcp-stdio'`
    - `operation: 'query' | 'search' | 'think'` for the first public wire contract
    - `params`
    - `class: 'interactive' | 'maintenance'`
    - `priority: number`
    - `context`: remote, sourceId, auth allowedSources, takesHoldersAllowList, cli options subset, output mode
    - The queue implementation supports maintenance-class requests through an injected/testable scheduler seam now; public `sync`/`embed`/`extract` forwarding is reserved for `requirements/003-pglite-priority-scheduler`.
  - `OperationIpcResponse`
    - success: `ok: true`, `status: 'queued' | 'served'`, `result` or CLI output envelope, diagnostics
    - failure: `ok: false`, `status: 'owner_unreachable' | 'lock_safety_blocked' | 'broker_timeout' | 'completion_unknown' | 'stale_socket_recovered' | 'invalid_request' | 'protocol_error' | 'handler_error'`, message, diagnostics
- Dependency direction:
  - CLI/MCP imports broker; broker does not import CLI main.
  - Owner-side adapter may import `dispatchToolCall`, `operationsByName`, `formatResult`, and extracted command helpers.
  - Broker transport receives that adapter as an injected handler and does not import dispatch/CLI helpers itself.
  - PGLite engine/lock remain independent.
- Data flow:
  - Caller loads config without connecting.
  - Caller identifies file-backed PGLite + eligible operation.
  - Caller sends typed request to socket.
  - Owner enqueues request; scheduler selects next request by class/priority then arrival order.
  - Owner executes handler using its already-open engine.
  - Owner returns JSON response; caller renders/returns it.

## Interactions

- Main CLI flow:
  - Parse command and params as today.
  - If thin-client, keep remote routing unchanged.
  - If config is PGLite with `database_path` and command is broker-eligible, call `forwardOperationViaIpc()`.
  - If response `served`/`queued`, render response and return without `connectEngine()`.
  - If response unavailable and no live owner safety blocker is known, continue to existing `connectEngine()` direct-open path.
  - If response `lock_safety_blocked`, print broker-specific actionable error and set non-zero exit.
- Main MCP flow:
  - `gbrain serve` connects engine once.
  - `startMcpServer()` binds operation IPC for PGLite.
  - A second MCP stdio process that detects a live owner before connecting starts a proxy server using existing tool metadata for broker-eligible tools and forwards `query`, `search`, and `think` calls to the owner instead of opening another PGLite connection.
  - Forwarded MCP calls execute through `dispatchToolCall()` with original remote/source options.
- Alternate flows:
  - No socket: direct-open fallback.
  - Stale socket: client reports unavailable; owner bind cleanup removes stale socket on next owner startup.
  - Live lock but broker unreachable: lock classifier returns live and caller returns actionable broker error rather than waiting for PGLite lock timeout.
  - Owner dies before request is sent: client gets `owner_unreachable`; direct-open retry is allowed only if lock classification says no live owner remains.
  - Owner dies while request is queued but not started: client can treat the request as not executed if the broker response or connection phase proves handler did not start.
  - Owner dies or times out after handler start, or response is lost after handler completion: client gets `completion_unknown`; automatic retry is forbidden for mutating local CLI `think --save/--take`, and retry of read-only operations must preserve positive broker/lock-safety evidence.
- Handoffs:
  - Later priority-scheduler requirement extends maintenance forwarding for `sync`, `embed`, and `extract` using the already-present class/priority fields.

## State And Invariants

- States:
  - `no_owner`: no socket and no live lock; caller direct-opens.
  - `owner_ready`: socket accepts broker requests; caller forwards.
  - `owner_busy`: requests queue in owner; caller waits for broker response, not PGLite lock.
  - `owner_unreachable`: socket/lock state implies owner may exist but broker cannot be reached.
  - `broker_timeout`: broker connection or owner handler did not respond within the caller's bounded timeout.
  - `completion_unknown`: request may have reached or started owner-side handler, so side effects are ambiguous.
  - `stale_recovered`: stale socket or dead lock recovered conservatively.
  - `lock_safety_blocked`: live lock exists and no safe broker path is available.
- Invariants:
  - One file-backed PGLite opener per data dir.
  - No live heartbeat lock stealing.
  - No raw SQL over broker IPC.
  - No network listener for operation IPC.
  - MCP forwarded calls keep `remote=true`.
  - CLI forwarded calls keep `remote=false`.
  - Source/federated scope travels with the request.
- Consistency rules:
  - Request IDs are echoed in responses and diagnostics.
  - Queue ordering is deterministic: higher priority first, then FIFO among equal priority.
  - Handler errors are serialized as operation/broker errors, not process crashes.
  - Broker timeout/cancellation semantics are phase-aware: a timed-out request that might still execute must be reported as ambiguous, not silently retried.

## Error Handling And Edge Cases

- Errors:
  - Invalid JSON or over-size payload -> `invalid_request`.
  - Unknown/unbrokered operation -> `invalid_request`.
  - Socket missing/connection refused/timeout -> unavailable marker, not throw.
  - Partial/truncated/malformed owner response -> `protocol_error` or `broker_timeout`, no direct-open retry while live lock may exist, and no private payload leakage.
  - Owner handler exception -> `handler_error` with existing JSON error envelope where applicable.
  - Live lock with no broker -> `lock_safety_blocked`.
  - Broker connect/handler timeout -> `broker_timeout`, not a PGLite lock timeout.
  - Socket permission denied or not yet bound while live lock exists -> `lock_safety_blocked` or `owner_unreachable`, not no-owner direct-open.
- Edge cases:
  - `ask` alias maps to `query`.
  - `query --image` must perform the same CLI image-to-base64 transform before forwarding.
  - `think --save/--take` remains local-trusted when forwarded from CLI, and remains blocked when forwarded from MCP.
  - Forwarded CLI `think --save/--take` never auto-retries after `completion_unknown` or ambiguous `broker_timeout`.
  - `GBRAIN_SOURCE` and `GBRAIN_FEDERATED_READ` for MCP stdio are carried explicitly.
  - A sentinel private query string must not appear in broker diagnostics, debug output, or handler-error envelopes.
  - Owner shutdown closes operation IPC and unlinks the operation socket.
- Recovery:
  - Owner bind removes stale socket file like resolve IPC, but cleanup must be race-safe and must not unlink a newly-bound live broker socket during concurrent owner restart/bind.
  - Dead lock recovery remains in `acquireLock()`.
  - If broker is unreachable but lock is dead/stale, caller can direct-open and become owner.
- Observability:
  - Stderr diagnostics are deterministic and grep-friendly.
  - Optional `GBRAIN_PGLITE_BROKER_DEBUG=1` can emit queue/serve diagnostics without logging raw private query text.

## Testability

- Unit:
  - Socket path, stale socket cleanup, unavailable marker, invalid payload, max bytes.
  - Queue ordering interactive before maintenance.
  - Lock classifier statuses without acquiring, waiting, or stealing.
  - Unknown/corrupt lock classifier states never enter the normal 30s lock wait.
  - Partial owner response and permission-denied/not-yet-bound socket handling.
  - Long `think` ahead of quick interactive calls is bounded by operation/broker timeout and cannot monopolize interactive capacity forever.
  - Request schema validation and diagnostics.
  - CLI classification for `query`, `ask`, `search`, and `think`.
- Integration:
  - Start owner operation IPC with a fake engine and assert forwarded MCP calls preserve `remote`, `takesHoldersAllowList`, `sourceId`, and allowed sources.
  - Start a second MCP stdio proxy while a live owner exists and assert brokered `query`, `search`, and `think` tool calls do not open PGLite directly.
  - Start file-backed PGLite owner and run second-process query/search/think without lock timeout strings.
  - At least five concurrent mixed callers return served/queued statuses without PGLite lock failures and include positive broker-routing evidence such as request id, owner pid, or broker status.
  - At least five simultaneous eligible callers from a no-owner cold start do not produce PGLite lock timeout; results converge to one safe owner/direct-open winner plus broker/proxy/lock-safety outcomes or deterministic actionable errors.
  - Live lock/no broker, stale socket, owner dies after discovery, and broker timeout paths are bounded and observable.
  - Owner-death tests split request phases: before send, queued-not-started, handler-started, and response-lost-after-completion.
  - Race-safe stale socket cleanup during concurrent owner restart/bind.
- E2E/manual if relevant:
  - Synthetic brain fixture only; no private content.
  - No-owner direct-open smoke for `query`, `search`, `think`.
  - Live-owner unreachable broker path produces actionable broker error.
- Mockable boundaries:
  - Broker client can inject socket path and timeout.
  - Server handler can inject fake dispatch for queue/diagnostic tests.
  - CLI broker router can be tested with config/forwarder stubs before spawning real processes.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact debug env var name and diagnostic phrasing | non_blocking | Does not affect architecture; implementation can choose deterministic strings and record them in evidence. | implementation |
| Full maintenance operation forwarding/yield behavior | non_blocking | This slice proves broker queue priority with synthetic or same-queue maintenance requests; later scheduler requirement completes real sync/embed/extract command behavior. | requirements/003-pglite-priority-scheduler |

## Self-Review

- Requirement coverage: AC1-AC8 have module and verification mappings.
- Separation of concerns: PGLite lock remains lower-level; broker owns local IPC; existing dispatch owns MCP semantics.
- Testability: Unit, integration, and E2E seams are explicit.
- Security / safety: Local-only socket, no raw SQL, no live lock stealing, and trust/source preservation are explicit invariants.
- Requirement integrity: No accepted requirement was removed or weakened; priority maintenance completion is sequenced without changing the first broker contract.
