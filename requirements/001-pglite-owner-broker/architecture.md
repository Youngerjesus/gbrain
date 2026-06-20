# Architecture Design: PGLite Owner Broker

Requirement source: requirements/001-pglite-owner-broker/requirements.md
Technical design source: requirements/001-pglite-owner-broker/technical-design.md

## Architecture Boundary

File-backed PGLite remains a single-owner storage boundary. Only the owner process opens the PGLite data directory and holds `.gbrain-lock`. Other local gbrain processes can become direct owners only when no broker is reachable and no live lock safety condition blocks direct open.

The new boundary is a local operation broker:

- Transport: Unix-domain socket under the PGLite `database_path`, local-only, permission `0600`.
- Protocol: newline-delimited JSON, one request per connection, bounded request/response bytes.
- Payload: typed operation request and caller context, never raw SQL.
- Owner: `gbrain serve` in the first implementation path, with an internal helper that can be reused by future owner daemons.

## Components And Ownership

- `src/core/pglite-operation-ipc.ts`: Owns socket path, request/response schema, client probe/forwarding, server binding, stale socket cleanup, queue diagnostics, queue ordering, protocol limits, and non-business transport validation. It must accept injected owner handlers and must not import CLI or MCP dispatch modules.
- `src/mcp/server.ts`: Starts the operation broker when serving a file-backed PGLite brain, alongside the existing resolve IPC.
- `src/mcp/dispatch.ts`: Remains the MCP dispatch and trust-boundary owner.
- `src/cli.ts`: Performs pre-connect broker probing for eligible CLI commands and preserves direct-open fallback when no owner exists.
- `src/commands/think.ts`: Exposes a parameter parser/result renderer seam so CLI `think` can be forwarded before the current `CLI_ONLY` `connectEngine()` path without changing command syntax.
- `src/commands/search.ts`: Keeps dashboard subcommands local; free-text search forwarding maps to the `search` operation where supported by the current CLI command surface.
- `src/core/pglite-lock.ts`: Remains the only database lock safety owner; broker code must not force-steal live locks.

## Dependency Direction

Higher-level transports depend on broker helpers; broker helpers depend only on Node primitives, protocol types, queue helpers, and local config/lock-classification types. Lower-level PGLite lock and engine modules do not import CLI, MCP server, or broker dispatch code.

Allowed direction:

`cli.ts` / `mcp/server.ts` -> `pglite-operation-ipc.ts` -> injected owner handler -> `operations.ts` / `dispatch.ts` -> `BrainEngine`.

Disallowed direction:

`pglite-lock.ts`, `pglite-engine.ts`, or `pglite-operation-ipc.ts` importing CLI/MCP dispatch code directly.

## Runtime / Agent / Schema / Evidence Handoffs

- Owner startup: after `startMcpServer()` binds stdio transport, it binds operation IPC if config engine is PGLite and `database_path` exists.
- Caller startup: before `connectEngine()` on broker-eligible PGLite commands, caller probes operation socket with a short timeout.
- Second MCP stdio startup: when a `gbrain serve` process sees a live PGLite owner before it can safely connect, it starts a stdio MCP proxy/forwarder that serves tool definitions locally and forwards broker-eligible `query`, `search`, and `think` calls to the owner instead of opening PGLite.
- Direct fallback: no socket/unreachable broker means direct-open fallback, unless lock classification shows a live owner and no broker path, in which case return an actionable broker-specific lock-safety error.
- MCP forwarding: request carries `remote=true`, `takesHoldersAllowList`, `sourceId`, and optional auth/allowedSources fields; owner executes through `dispatchToolCall()`.
- CLI forwarding: request carries `remote=false`, parsed params, source context, output mode, and timeout; owner executes the operation handler and returns a formatted stdout/stderr/exitCode envelope.
- Diagnostics: responses include deterministic `status` values such as `queued`, `served`, `owner_unreachable`, `stale_socket_recovered`, and `lock_safety_blocked`.

## Cross-Layer Invariants

- At most one process opens a file-backed PGLite data directory at a time.
- A live, heartbeat-refreshing `.gbrain-lock` is never force-stolen by broker code.
- Direct-open fallback decisions use a non-acquiring, non-stealing PGLite lock classifier; callers never use `acquireLock()` as the probe for broker fallback.
- Broker transport is local-only and never network-bound.
- Raw SQL never crosses the operation IPC.
- MCP forwarded calls remain remote/untrusted.
- Local CLI forwarded calls remain trusted local CLI calls.
- Source scope and federated-read grants are serialized explicitly, not recomputed from the owner process environment when the caller supplied them.
- Direct-open fallback remains available when no live owner exists.
- Broker probe failure must not become a 30-second PGLite lock wait for normal `query`, `search`, or `think` contention.
- HTTP MCP is not part of the first owner-broker wire contract unless a later accepted requirement/design explicitly adds `serve --http` owner binding and tests.

## Risks And Rollback

- Risk: Owner process runs without operation IPC but holds the lock. Mitigation: caller returns a broker-specific actionable error rather than waiting for PGLite lock timeout.
- Risk: CLI and MCP semantics drift. Mitigation: tests cover both forwarded MCP dispatch and forwarded CLI command surfaces.
- Risk: Priority scheduling under long maintenance work requires additional operation classes. Mitigation: request schema includes priority/class fields now; later scheduler slice adds maintenance forwarding/yield tests.
- Rollback: Disable broker probing via a kill-switch environment variable if needed; direct-open behavior remains the fallback when no broker is used.
