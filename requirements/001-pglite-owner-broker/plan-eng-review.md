# Plan Engineering Review: PGLite Owner Broker

Created: 2026-06-20
Status: GO WITH CHANGES
Plan under review: plans/001-pglite-owner-broker/plan.md

## Plan Under Review

Accepted requirement, research, technical design, architecture, UX review, DevEx review, and draft plan for the first PGLite owner-broker sequence slice.

## Scope Challenge

The direction is correct and should reuse existing repo seams:

- Reuse the local Unix socket framing pattern from `resolve-ipc.ts`, but not its fully fail-soft semantics.
- Reuse `dispatchToolCall()` for MCP owner-side execution.
- Reuse CLI parsing/formatting seams where possible; extract `think` parse/render helpers rather than duplicating `runThinkCli()`.
- Keep `pglite-lock.ts` as the lock authority.

Scope changes required before implementation:

- Add an MCP stdio proxy path for a second `gbrain serve` process; CLI-style pre-connect forwarding alone cannot cover MCP startup because `serve` connects before receiving a tool call.
- Exclude `serve --http` from this first slice unless a later requirement explicitly adds HTTP binding and tests.
- Do not publicly forward `sync`, `embed`, or `extract` in this slice; prove queue priority through the same queue's maintenance-class seam and leave real maintenance command behavior for `requirements/003-pglite-priority-scheduler`.

## Architecture Findings

- Must change plan: lock state classification is mandatory. Broker-unavailable plus live lock must produce `lock_safety_blocked` without entering `acquireLock()`'s normal 30 second wait.
- Must change plan: broker transport must accept an injected owner handler and must not import CLI/MCP dispatch directly.
- Must change plan: CLI-only `think` needs a named pre-connect forwarding seam.
- Must change plan: forwarded CLI source behavior must carry caller source-resolution inputs so the owner resolves against its connected engine without silently using owner-only environment state.
- Must change plan: positive broker-routing evidence is required; absence of lock-timeout strings alone is not proof.

## Test Findings

- Required unit coverage:
  - operation IPC framing, size limits, invalid JSON, status matrix, stale socket cleanup.
  - priority queue ordering with interactive ahead of maintenance-class requests.
  - non-acquiring lock classifier: absent, live, dead/stale recoverable, corrupt recoverable, unknown.
  - broker module dependency boundary through injected handler.
- Required integration/E2E coverage:
  - second-process CLI `query`, `search`, and `think` with live owner.
  - second MCP stdio proxy startup and brokered `query`, `search`, and `think`.
  - at least five concurrent mixed callers with per-caller broker status/request evidence.
  - live lock with no broker returns `lock_safety_blocked` quickly.
  - owner dies after discovery, stale socket, and broker timeout are bounded and observable.
  - MCP trust/source preservation: `remote=true`, `takesHoldersAllowList`, `GBRAIN_SOURCE`, federated read grants, and remote `think` save/take blocking.
  - privacy sentinel: a unique query string must not appear in diagnostics/debug/status/error output.

## Failure Modes

- Misleading green test: no timeout string appears, but a caller direct-opened or test used only fake broker requests.
- Live lock with missing broker socket: caller waits on `acquireLock()` and recreates today's user pain.
- Owner dies mid-request: caller retries direct-open before lock state is safe.
- Stale socket collapse: missing socket, stale socket, owner unreachable, and live lock/no broker all become generic unavailable.
- Trust/source drift: owner reconstructs context from owner process defaults and widens remote access.

## Companion Review Synthesis

- Scope/reuse reviewer: GO WITH CHANGES. Accepted findings: MCP stdio proxy gap, AC4 ambiguity, tighter source/trust reuse, defer HTTP.
- Architecture/contract reviewer: GO WITH CHANGES. Accepted findings: mandatory lock classifier, CLI-only `think` seam, caller source-resolution inputs, injected handler boundary, defer HTTP.
- Verification/failure reviewer: GO WITH CHANGES. Accepted findings: positive broker-routing evidence, lock classifier proof, owner/stale/timeout tests, brokered MCP trust/source tests, privacy sentinel tests, AC4 overclaim fix.
- Rejected findings: none. All companion findings were plan-changing or verification-changing and were incorporated into the draft plan/design artifacts.

## Scenario Review Decision

scenario-brake: used next. Required because this work has multiple entry paths, owner states, recovery paths, runtime timing changes, and operator-visible failure modes.

## RALPLAN-DR Decision Review

Used lightly. The chosen path is acceptable after changes:

- Principles: single-owner PGLite safety, local-only IPC, explicit trust/source context, deterministic diagnostics, positive concurrency proof.
- Decision drivers: avoid lock timeouts without unsafe direct multi-process PGLite access; preserve command syntax; preserve MCP remote semantics.
- Viable options: direct lock weakening rejected; post-lock fallback rejected; local operation broker accepted.
- Required consequence: later scheduler slice must complete real `sync`/`embed`/`extract` priority behavior before the full sequence can be production-ready.

## Recommendation

GO WITH CHANGES.

Implementation must not start until the draft plan and technical design include the accepted changes above. The current artifacts have been updated to include them; next gate is scenario-brake.
