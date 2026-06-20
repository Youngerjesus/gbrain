---
requirement_id: 001-pglite-owner-broker
feature_name: PGLite Owner Broker
created_by: requirement-clarifier
created_at: 2026-06-20T03:11:00Z
updated_at: 2026-06-20T03:11:00Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Owner Broker

## Readiness Status

Ready. The post-draft reviewer returned structured `SHIP` with no findings. The user has confirmed the material product boundaries: PGLite only, gbrain behavior only, queue/serve concurrency rather than unsafe direct multi-process database access, interactive priority over maintenance, unchanged CLI command surfaces, direct-open fallback when no owner exists, and at least five simultaneous MCP/CLI callers without PGLite lock timeout.

## User Story

As a gbrain user running the default PGLite engine, I can use multiple MCP servers and CLI commands at the same time without normal interactive operations failing on the PGLite file lock.

## Problem / Intent / Outcome

GBrain's PGLite backend is intentionally single-process. Today, that safety boundary can surface as user-visible lock failures such as `Timed out waiting for PGLite lock` or `Another gbrain process is using the database` when multiple MCP servers or CLI commands compete for the same brain. The desired outcome is user-observable concurrent access: competing callers are routed through one live owner process that opens PGLite, queues or serves requests safely, and preserves the existing trust and source-scope contracts.

The first implementation slice must establish the owner-broker contract and dispatch boundary for PGLite. It must not weaken PGLite's exclusive file lock or pretend that PGLite itself became safe for direct multi-process database access.

## Acceptance Criteria

- AC1. When a PGLite owner process is alive, a competing gbrain CLI or MCP caller must not attempt a second direct PGLite open for `query`, `search`, or `think`; it must route through the owner or return a broker-specific actionable error if the owner cannot be reached.
  - Verification: automated test starts a PGLite owner, invokes a second-process `gbrain query`, `gbrain search`, and `gbrain think`, and asserts no `Timed out waiting for PGLite lock`, no `Could not acquire PGLite lock`, and no `Another gbrain process is using the database`.
- AC2. When no PGLite owner exists and no live lock is held, existing CLI behavior remains direct-open compatible for `gbrain query "x"`, `gbrain search "x"`, and `gbrain think "x"`.
  - Verification: automated CLI test runs each command against a PGLite brain with no owner daemon and asserts successful operation or the command's existing non-lock failure mode when the brain lacks content/model configuration.
- AC3. At least five simultaneous mixed MCP/CLI callers can request `query`, `search`, and `think` against one PGLite brain without any caller failing solely because of the PGLite file lock.
  - Verification: concurrency test launches one owner plus at least five concurrent callers, waits for all, and fails on PGLite lock timeout strings or direct-open contention errors.
- AC4. Interactive operations `query`, `search`, and `think` are prioritized ahead of long maintenance classes `sync`, `embed`, and `extract` when they contend for the owner.
  - Verification: scheduler or integration test creates a long-running maintenance request, submits an interactive read/synthesis request after it, and asserts the interactive request is served or explicitly queued ahead of maintenance within a bounded latency budget.
- AC5. The broker preserves the MCP trust boundary: MCP-dispatched calls continue to execute with `remote=true`, `takesHoldersAllowList: ['world']`, and existing source/federated-read scoping.
  - Verification: unit or integration test calls through the brokered MCP path and asserts the dispatched operation context has the same remote and source-scope behavior as direct `startMcpServer` dispatch.
- AC6. The broker preserves CLI compatibility: public command syntax for `gbrain query "x"`, `gbrain search "x"`, and `gbrain think "x"` does not change.
  - Verification: CLI smoke test uses the existing command forms without new flags or daemon commands and succeeds through either direct-open fallback or owner forwarding.
- AC7. Stale owner recovery remains conservative: a live, heartbeat-refreshing owner is never force-stolen, and a dead owner can be recovered without manual deletion in normal cases.
  - Verification: tests cover live owner heartbeat, dead owner cleanup, stale socket cleanup, and ownership-token protection; no test should require deleting `.gbrain-lock` while a live owner is refreshing.
- AC8. The implementation exposes enough operator diagnostics to distinguish owner-unreachable, stale-owner-recovered, queued, served, and lock-safety-blocked outcomes.
  - Verification: tests or captured logs assert structured status fields or deterministic stderr messages for each outcome.

## Out of Scope / Avoid

- Do not make PGLite accept unsafe direct multi-process access to the same data directory.
- Do not remove, weaken, or bypass the exclusive PGLite file lock as the safety primitive.
- Do not change Postgres behavior except for shared abstractions that remain behavior-preserving for Postgres.
- Do not require users to change the command syntax for `gbrain query`, `gbrain search`, or `gbrain think`.
- Do not prioritize `sync`, `embed`, `extract`, dream/cycle, or other long maintenance work over interactive `query`, `search`, or `think`.
- Do not route remote MCP calls through a trusted local CLI path that would erase `remote=true`.
- Do not silently downgrade `think` into a read-only search result; remote save/take blocking must stay intact.

## Success Metrics

- Five or more simultaneous mixed MCP/CLI callers complete without PGLite lock timeout or direct-open contention errors.
- `query`, `search`, and `think` keep their existing command surfaces.
- Interactive requests submitted during maintenance do not wait behind an unbounded maintenance window.
- Existing source isolation, remote trust boundary, and MCP privacy posture remain covered by automated tests.

## Failure Condition

This requirement fails if normal multi-caller use still produces `Timed out waiting for PGLite lock`, `Could not acquire PGLite lock`, or `Another gbrain process is using the database` for `query`, `search`, or `think`, or if the implementation achieves concurrency by allowing multiple processes to open the same file-backed PGLite database directly.

## Edge Cases

- Owner process alive but IPC socket missing, stale, permission-denied, or not yet bound.
- Owner process dies after caller discovery but before dispatch completes.
- A stale socket file remains after an unclean owner shutdown.
- Caller starts before any owner exists and should direct-open safely.
- Multiple callers race to become owner when no owner exists.
- `think` runs longer than simple search and must not monopolize all interactive capacity forever.
- Maintenance work is already running when interactive calls arrive.
- MCP caller passes save/take parameters to `think`; remote persistence remains blocked.
- Federated read environment is configured; brokered calls preserve allowed sources.

## Constraints

- Scope is PGLite only and must improve gbrain's behavior.
- Actual PGLite database access must remain single-owner safe.
- The existing `search`, `query`, and `think` operations are the minimum supported interactive surface.
- The first implementation path should reuse the existing local Unix socket IPC pattern where practical, because gbrain already uses it for PGLite retrieval reflex.
- Socket or broker transport must be local-only, not a network surface.
- Tests must avoid private brain content and use synthetic fixtures.

## Contract Preservation

- Requested behavior / artifact: PGLite user-observable concurrent access through a single owner broker for gbrain `query`, `search`, and `think`.
- Execution boundary: one owner process opens file-backed PGLite; competing callers forward operation requests to that owner instead of directly opening the database.
- Required evidence level: automated concurrency tests, CLI/MCP smoke tests, trust-boundary assertions, and stale-owner recovery tests.
- Known capability gaps: PGLite itself remains single-process; brokered concurrency may serialize actual SQL execution.
- Allowed substitutions: local Unix socket IPC, equivalent local-only IPC, or in-process owner reuse, if they preserve the same security and behavior contract.
- Disallowed substitutions: direct multi-process PGLite access, force-unlocking live owners, changing command syntax, or routing MCP through trusted local context.
- Downgrade approval rule: any reduction in supported caller count, supported operations, trust-boundary guarantees, or interactive-over-maintenance priority requires explicit user approval.

## Iteration Policy

### Continue when

- The next implementation step preserves single-owner safety and moves at least one accepted operation class closer to no-lock-failure concurrent use.
- Automated tests can reproduce a prior lock failure and then prove the new forwarding/queueing path avoids it.

### Stop when

- A design requires weakening the PGLite lock, allowing direct multi-process PGLite opens, or erasing MCP remote semantics.
- A maintenance scheduling design can starve `query`, `search`, or `think`.

### Ask user when

- Expanding the supported operation set beyond `query`, `search`, `think`, `sync`, `embed`, and `extract`.
- Changing public CLI syntax or requiring users to manually start a daemon.
- Accepting a latency tradeoff that makes interactive calls noticeably slower to preserve safety.
- Treating this as production-ready without a final readiness gate.

### Checkpoint cadence

After each sequence slice, record which operation classes are brokered, which still direct-open, which tests prove the behavior, and which lock-failure cases remain.

## Decision Boundaries

### Agent may decide

- The internal broker transport shape, as long as it is local-only and preserves trust/source context.
- Queue data structures, timeout defaults, and diagnostic field names, as long as acceptance criteria remain testable.
- Whether the first implementation reuses the existing resolve IPC module or creates a sibling operation IPC module.
- Test fixture details and synthetic query content.

### User must confirm

- Any public command syntax change.
- Any support reduction below five simultaneous mixed MCP/CLI callers.
- Any change that weakens PGLite file-lock safety.
- Any expansion to network-accessible broker surfaces.
- Any decision to defer `think` or maintenance priority out of the launch boundary.

## Verification Method

- Unit tests for owner discovery, live/stale owner classification, request forwarding, and trust/source context construction.
- Integration tests using a file-backed PGLite brain with one owner and at least five simultaneous mixed callers.
- CLI smoke tests for `gbrain query "x"`, `gbrain search "x"`, and `gbrain think "x"` with no owner and with an owner.
- MCP dispatch tests proving `remote=true`, takes-holder allow-list, and source/federated-read scoping survive broker forwarding.
- Regression tests that fail if PGLite lock timeout strings appear in accepted concurrent interactive paths.

## Evidence Reviewed

- source_type: code
  location_or_reference: `src/core/pglite-lock.ts:1`
  extracted_fact: PGLite file locking exists because file-backed PGLite supports only one connection at a time, and concurrent direct access can crash with `Aborted()`.
  confidence: high
- source_type: code
  location_or_reference: `src/core/pglite-lock.ts:27`
  extracted_fact: The current lock implementation intentionally treats a live, recently-heartbeating holder as alive and never steals it; this protects against WAL corruption and PID reuse.
  confidence: high
- source_type: code
  location_or_reference: `src/core/pglite-lock.ts:127`
  extracted_fact: The current PGLite lock acquire path has a 30 second default timeout and emits user-visible `Timed out waiting for PGLite lock` errors on contention.
  confidence: high
- source_type: code
  location_or_reference: `src/core/pglite-engine.ts:241`
  extracted_fact: `PGLiteEngine.connect()` acquires the file lock before creating/opening the database and errors when it cannot acquire the lock.
  confidence: high
- source_type: code
  location_or_reference: `src/mcp/server.ts:73`
  extracted_fact: MCP stdio dispatch currently sets `remote: true`, the takes-holder allow-list, and source scope before invoking shared operations.
  confidence: high
- source_type: code
  location_or_reference: `src/mcp/server.ts:116`
  extracted_fact: A PGLite-specific local IPC pattern already exists because `gbrain serve` owns the single connection and other context resolution must go through it rather than opening a second connection.
  confidence: high
- source_type: code
  location_or_reference: `src/core/context/resolve-ipc.ts:1`
  extracted_fact: The existing resolve IPC is local Unix-socket based, mode 0600, newline-delimited JSON, and explicitly avoids passing raw SQL across the wire.
  confidence: high
- source_type: docs
  location_or_reference: `docs/ENGINES.md:166`
  extracted_fact: GBrain documents PGLite concurrency as single process and Postgres concurrency as connection pooling.
  confidence: high
- source_type: code
  location_or_reference: `src/core/operations.ts:1362`
  extracted_fact: `search` is a read operation that routes to keyword or cached hybrid search.
  confidence: high
- source_type: code
  location_or_reference: `src/core/operations.ts:1422`
  extracted_fact: `query` is a read operation with the existing CLI positional query surface and source-scope handling.
  confidence: high
- source_type: code
  location_or_reference: `src/core/operations.ts:1764`
  extracted_fact: `think` is a mutating operation by declaration, but remote MCP callers cannot persist save/take effects because the handler sets safe persistence flags to false when `remote` is true.
  confidence: high
- source_type: user
  location_or_reference: current chat, 2026-06-20
  extracted_fact: User confirmed PGLite-only scope, gbrain behavior as the target, queue/serve semantics rather than literal simultaneous DB transactions, interactive priority over sync/embed/extract, unchanged CLI syntax, direct-open fallback when no owner exists, and at least five simultaneous MCP/CLI callers without lock timeout.
  confidence: high

## Artifact Handoff Contract

- producer role: requirement-clarifier
- consumer role: goal-requirement-orchestrator, technical-design, plan-eng-review, implementation agents, reviewer agents
- artifact path or path-producing rule: `requirements/001-pglite-owner-broker/requirements.md`
- artifact purpose: Source-of-truth requirements for the first PGLite concurrent-access implementation slice.
- failure classification: Missing, stale, reviewer-unaccepted, or contradicted requirements block planning and implementation.
- verification method: Post-draft reviewer gate returns structured `SHIP` or findings are revised and rerun; subsequent gates map implementation plans and tests back to AC1-AC8.

## Ambiguity / Readiness Summary

- Depth used: Standard
- Final ambiguity: 0.05
- Target ambiguity: 0.20
- Unresolved readiness gaps used to score ambiguity: Implementation architecture details are intentionally deferred to technical-design; no product-scope question remains open.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
  - Pressure pass completed: yes; earlier "make PGLite concurrent" was reframed to user-observable concurrency via single-owner broker to avoid unsafe direct multi-process access.
  - Closure audit passed: yes
- Residual risk: The exact broker architecture and scheduling latency budget still require technical-design; preserving `think` behavior while prioritizing interactive work over maintenance is the highest-risk design area.

## Assumptions

- The broker can reuse or parallel the existing local-only Unix socket pattern without introducing a network surface.
- It is acceptable for actual PGLite SQL execution to be serialized internally, as long as callers are queued or served without lock failures.
- The five-caller acceptance target is the minimum launch threshold, not a maximum design capacity.

## Recommended Next Step

- technical-design
- Reason: Requirements are testable and stable, but the next work requires HOW-level module boundaries, owner discovery, request protocol, trust-context preservation, scheduling, timeout, and stale-owner recovery design before implementation planning.

## Planning Handoff

Before writing the final Codex plan or starting implementation, read this requirements document and treat it as the product requirements source of truth only when this document was created or updated in the current planning session, or when the user explicitly selected this exact document for reuse. If the implementation plan conflicts with these requirements, pause and reconcile the conflict before editing code.

Preserve the handoff bridge:

- Do not repeat already-satisfied requirement discovery by default.
- Do preserve intent, non-goals, decision boundaries, acceptance criteria, verification method, and residual risk.
- Do not let the next planning or implementation agent silently turn an assumption into a product decision.
- If residual risk is non-trivial, the next skill must either reduce it or carry it explicitly into its own plan/review artifact.

## Open Questions

None blocking for this requirement. Technical-design must choose the owner discovery and operation IPC design.
