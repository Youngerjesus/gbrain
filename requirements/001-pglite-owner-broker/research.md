# Technical Research: PGLite Owner Broker

Created: 2026-06-20
Status: Complete
Requirement source: requirements/001-pglite-owner-broker/requirements.md

## Research Decisions

### RD-001: Preserve PGLite single-owner access through local operation IPC

- Question: How can multiple callers avoid PGLite lock failures without weakening the existing exclusive file lock?
- Decision: Add a sibling local-only operation broker IPC beside the existing resolve IPC. The owner process continues to be the only process that opens file-backed PGLite; competing callers detect the broker before direct connect and forward typed operation requests for the accepted operation classes.
- Rationale: `PGLiteEngine.connect()` acquires the file lock before `PGlite.create()`, and `pglite-lock.ts` intentionally protects a live heartbeat holder. The existing `resolve-ipc.ts` already establishes the safe pattern: local Unix socket, mode `0600`, newline-delimited JSON, no raw SQL crossing the transport, and owner-side use of the already-open engine.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Weaken or bypass the file lock | Simple caller code | Violates PGLite safety and accepted non-goal | Rejected |
  | Wait for the lock timeout then retry | Minimal architecture | Still exposes long waits and timeout failures; does not queue/serve | Rejected |
  | Reuse `resolve-ipc.ts` directly | Fastest implementation | Protocol is intentionally narrow for pointer resolution and should not grow into generic op dispatch | Rejected |
  | Add sibling operation IPC | Reuses proven transport shape while keeping protocol explicit | Requires CLI/MCP dispatch integration and tests | Accepted |
- Risk: Broker request serialization must preserve trust and source context exactly, not infer it on the wrong side.
- Evidence: `src/core/pglite-lock.ts`; `src/core/pglite-engine.ts`; `src/core/context/resolve-ipc.ts`; `src/mcp/server.ts`.

### RD-002: Route before `connectEngine()` for brokered PGLite callers

- Question: Should a competing caller connect locally first and fallback to broker on lock error, or discover the broker before opening PGLite?
- Decision: Broker-eligible PGLite CLI/MCP paths must attempt owner discovery before direct `connectEngine()` when config is PGLite and `database_path` is present. If no broker is reachable and no live owner is implied, the caller keeps existing direct-open fallback.
- Rationale: The accepted user outcome is no normal lock timeout for `query`, `search`, and `think`. A fallback after `connectEngine()` would still sit behind `acquireLock()`'s 30 second timeout on live owners and would be indistinguishable from today's pain.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Fallback after lock timeout | Smallest CLI change | Preserves 30s user-visible wait and timeout shape | Rejected |
  | Always require daemon | Clear ownership | Violates direct-open fallback when no owner exists | Rejected |
  | Pre-connect broker probe, direct-open fallback | Avoids lock timeout and keeps no-daemon CLI behavior | Requires early command classification | Accepted |
- Risk: Probe timeout must be short enough not to degrade no-owner commands, but not so short that a healthy busy owner is missed.
- Evidence: `src/cli.ts` parses shared op params before connect; `src/cli.ts` read-only command timeout branch currently wraps `connectEngine()`; `src/core/context/resolve-ipc.ts` uses a short client timeout and fail-soft semantics.

### RD-003: Owner-side dispatch should reuse operation handlers and MCP dispatch where possible

- Question: Which code path should the broker owner use to execute forwarded `query`, `search`, and `think`?
- Decision: Owner-side broker dispatch should route MCP-shaped requests through `dispatchToolCall()` with forwarded `DispatchOpts`, and CLI-shaped requests through the same operation handlers plus CLI formatting for operation-backed commands. `think` CLI should be normalized to the existing `think` operation parameter shape where possible, preserving local `save`/`take` semantics only for trusted local CLI callers.
- Rationale: `dispatchToolCall()` is already the single source of truth for MCP validation, `remote=true`, takes-holder allow-list, source scope, auth, and `_meta` injection. `query` and MCP `search`/`think` already exist as operations. CLI `think` currently has a separate wrapper, so the forwarding seam must avoid accidentally routing trusted local CLI intent as remote MCP.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Implement broker-specific SQL/search logic | Direct control | High drift risk and privacy/source bugs | Rejected |
  | Use `dispatchToolCall()` for every caller | Simple | Local CLI `remote=false` formatting and `think --save/--take` behavior need explicit handling | Partially accepted |
  | Reuse operation handlers with explicit caller context | Preserves contracts | More typed request fields required | Accepted |
- Risk: CLI `search` currently has command-wrapper behavior for `modes/stats/tune`; free-text search must map to the operation path, while dashboard subcommands should remain command behavior or be out of this first broker path unless design explicitly includes them.
- Evidence: `src/mcp/dispatch.ts`; `src/core/operations.ts`; `src/commands/think.ts`; `src/commands/search.ts`; `src/cli.ts`.

### RD-004: Priority scheduling can start at broker admission order, not DB parallelism

- Question: What does interactive priority mean when PGLite itself remains single-owner and many handlers are async?
- Decision: Add explicit request classes and a broker queue that admits `query`, `search`, and `think` ahead of maintenance classes once maintenance forwarding is introduced. For the first owner-broker slice, the operation broker protocol should carry priority/class fields and record queued/served diagnostics; later scheduler slice can add maintenance forwarding/yield enforcement without changing the wire contract.
- Rationale: The first requirement includes AC4, but the sequence splits priority scheduler as a later requirement. To avoid rework, the first broker must expose the classification and queue semantics now, while the bounded maintenance behavior is completed in the scheduler slice.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | FIFO-only broker | Easy | Conflicts with accepted priority direction and later slice | Rejected |
  | Full maintenance preemption in first slice | Strong guarantee | Too much scope for owner-broker contract slice; needs sync/embed/extract design | Deferred to later requirement |
  | Priority-aware broker protocol now, maintenance enforcement later | Keeps contract aligned and sequence-sliced | AC4 not fully proven until later scheduler slice | Accepted |
- Risk: Requirement 001 completion must not overclaim maintenance priority beyond the protocol/admission behavior implemented in this slice.
- Evidence: Sequence item 3 reserves priority scheduler outcome; requirement AC4 defines priority verification; `src/commands/sync.ts`, `embed`, and `extract` are CLI command classes rather than MCP read ops.

### RD-005: Stale recovery should distinguish socket staleness from live lock ownership

- Question: How should callers handle stale sockets, missing sockets, and live owners?
- Decision: Socket cleanup may remove stale socket files before owner bind, mirroring resolve IPC, but callers must not remove or steal a live `.gbrain-lock`. Caller diagnostics should distinguish `owner_unreachable`, `stale_socket_recovered`, `queued`, `served`, and `lock_safety_blocked`.
- Rationale: `pglite-lock.ts` already has heartbeat and ownership-token protection for the database lock. Broker code should consume that safety boundary instead of duplicating unsafe lock stealing.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Caller removes `.gbrain-lock` when broker unreachable | Can recover some crashes | Unsafe for live heartbeat owners and violates AC7 | Rejected |
  | Owner bind removes only stale socket path | Matches existing IPC precedent | Does not auto-fix all owner-unreachable cases | Accepted |
  | Lock helper exposes classification for diagnostics | Better messages | Requires small helper surface if tests need exact classification | Accepted if needed |
- Risk: A live owner with no broker socket is a real partial-failure mode. The accepted behavior allows a broker-specific actionable error rather than a PGLite lock timeout.
- Evidence: `src/core/pglite-lock.ts`; `src/core/context/resolve-ipc.ts`.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact operation IPC request/response schema | non_blocking | Required for technical design, but research established the pattern and constraints. | technical-design |
| Exact maintenance-yield latency budget | non_blocking | Sequence reserves a later scheduler slice; first slice must keep protocol/classification extensible. | requirements/003-pglite-priority-scheduler |
| Managed repo isolated worktree setup | non_blocking | `scripts/init_worktree.sh` is missing and must be created before implementation, but does not change research decisions. | implementation preflight |

## Gate Self-Review

- All technical unknowns from the requirement were addressed or classified.
- Every decision has rationale and alternatives.
- Requirement Impact is absent.
- Every unresolved item is classified as blocking or non_blocking.
- Evidence paths/sources are recorded in evidence.md.
