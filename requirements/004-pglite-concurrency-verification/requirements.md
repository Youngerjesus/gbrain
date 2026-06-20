---
requirement_id: 004-pglite-concurrency-verification
feature_name: PGLite Concurrency Verification
created_by: requirement-clarifier
created_at: 2026-06-20T12:25:00Z
updated_at: 2026-06-20T12:55:00Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Concurrency Verification

## Readiness Status

Ready. The post-draft reviewer rerun returned `SHIP`; research and design may proceed.

## User Story

As a gbrain user running PGLite locally, I can have multiple CLI and stdio MCP callers interact with the same brain and see predictable queue/proxy/defer behavior instead of PGLite lock timeout failures or stale documentation telling me to manually stop useful interactive processes.

## Problem / Intent / Outcome

Requirements 001-003 implemented the local owner broker, `query`/`search`/`think` operation forwarding, and bounded maintenance fallback for `sync`, `embed`, and `extract`. Requirement 004 must prove the integrated behavior end-to-end and align diagnostics/documentation with the new contract.

This slice is successful when real subprocess evidence shows local PGLite concurrency works for at least five mixed CLI/MCP interactive callers, stale owner/socket states are recovered or reported deterministically, and operator docs no longer preserve the old blanket guidance that PGLite users must stop `gbrain serve` before any useful concurrent interactive work.

## Acceptance Criteria

- AC1. A real PGLite owner process, not only an injected test socket, can serve at least five simultaneous mixed interactive callers.
  - Verification: automated test starts a real `gbrain serve` or equivalent gbrain CLI owner process against a temporary PGLite brain, then runs at least five simultaneous mixed callers including CLI and stdio MCP paths using `query`, `search`, and `think`. Every caller completes or returns a deterministic broker status without raw PGLite lock timeout text.
- AC2. Multiple stdio MCP server processes against the same PGLite brain route safely.
  - Verification: automated test starts one owner MCP server and at least one additional stdio MCP server/proxy, sends MCP `query`/`search`/`think` calls through the second server while CLI callers are also active, and asserts no direct PGLite open, no lock timeout, and preserved MCP error/result envelope.
- AC3. Stale owner/socket recovery is observable and bounded across named cases.
  - Verification: automated tests must cover every row in this recovery matrix:
    - stale operation socket before owner startup -> `stale_socket_recovered` is emitted or recorded and the new owner can serve a request
    - dead/stale PGLite owner lock -> stale lock is safely recovered and a normal direct-open command result is observed without manual live-lock deletion
    - live owner lock with missing broker socket -> caller returns `owner_unreachable`
    - accepted broker request whose owner does not return in time -> caller returns `completion_unknown`
    - corrupt/unknown PGLite lock -> caller returns `lock_safety_blocked`
  - None of these cases may delete a live heartbeat-refreshing owner lock or emit raw PGLite lock timeout text.
- AC4. Diagnostics are stable, operator-meaningful, and privacy-safe.
  - Verification: tests or docs cover the status vocabulary: `served`, `owner_unreachable`, `completion_unknown`, `lock_safety_blocked`, `owner_starting`, `maintenance_deferred`, and `stale_socket_recovered`. Generic broker errors must not leak private query text, request params, source path contents, or MCP auth material.
- AC5. Documentation reflects the new PGLite concurrency contract.
  - Verification: update stale docs, especially `docs/architecture/serve-sync-concurrency.md`, and any directly contradictory references in `docs/ENGINES.md`, README, or MCP docs. Docs must explain that interactive `query`/`search`/`think` can route through the local owner broker, while `sync`/`embed`/`extract` are deferred under a live PGLite owner in this sequence.
- AC6. The verification suite remains runnable without external services or API keys.
  - Verification: new tests use temporary PGLite brains, local subprocesses, deterministic handlers or seeded local data, and no network/API dependency. If a real command path naturally returns an expected no-key or validation result after direct open, that may be accepted only when the concurrency behavior under test is already proven.
- AC7. Requirement 001-003 behavior does not regress.
  - Verification: rerun the related PGLite lock, IPC, CLI broker, stdio lifecycle, CLI search dispatch, source-scope/auth, and maintenance fallback tests plus `bun run typecheck`.
- AC8. Closeout contains an evidence matrix distinguishing real E2E evidence from synthetic/unit evidence.
  - Verification: closeout must list each required behavior, its evidence type (`real_subprocess_e2e`, `command_level_integration`, `ipc_unit`, `doc_update`), exact test/doc path, and whether it covers CLI, MCP, or both.

## Out Of Scope / Avoid

- Do not introduce network-accessible owner broker behavior.
- Do not weaken, bypass, delete, or auto-force-remove live PGLite locks.
- Do not claim maintenance commands are queued/executed through the broker unless that is implemented and tested.
- Do not require a separate mandatory daemon for normal `gbrain query`, `search`, or `think`.
- Do not require Postgres, Docker, external APIs, or real user brain data for the new verification.
- Do not mark this slice complete on fake-owner or injected-socket tests alone.
- Do not broaden this slice to production readiness; requirement 005 owns final launch/readiness verdict.

## Success Metrics

- At least one real-subprocess test proves five mixed local interactive callers complete or broker deterministically with no PGLite lock timeout.
- At least one test proves two stdio MCP server processes can coexist against one PGLite brain through owner/proxy routing.
- Stale owner/socket and corrupt/safety statuses have direct evidence.
- Docs no longer contradict the implemented broker/defer behavior.
- Requirement 001-003 regression suite remains green.

## Failure Condition

This requirement fails if the only concurrency evidence uses injected sockets or fake owners, if real multi-process CLI/MCP callers still hit raw PGLite lock timeout, if documentation still tells users to stop `gbrain serve` as the blanket answer for interactive PGLite concurrency, or if diagnostics imply maintenance work was queued/completed when it was only deferred.

## Edge Cases

- First owner MCP process is still starting when another CLI or MCP caller arrives.
- Second MCP server starts while the owner process is live but the operation socket is missing.
- Owner accepts a request and exits or hangs before returning.
- Stale operation socket file exists before a new owner starts and must recover with `stale_socket_recovered`.
- Dead/stale PGLite lock exists without a live process and must be safely recoverable.
- Live owner lock exists with no operation socket and must return `owner_unreachable`.
- Owner accepts a brokered request but does not finish before the caller timeout and must return `completion_unknown`.
- Corrupt/unknown PGLite lock exists and must return `lock_safety_blocked`.
- Five callers mix CLI and MCP transports and include all three interactive operations.
- Docs need to explain interactive concurrency separately from maintenance deferral.

## Constraints

- Scope is PGLite only.
- Verification must run locally and hermetically.
- Public command syntax must remain unchanged.
- Trust/source/auth behavior from requirements 001-002 must remain intact.
- Maintenance behavior from requirement 003 remains `deferred_safe_fallback` unless a later accepted requirement changes it.
- The implementation branch baseline is task worktree commit `8a23554a Defer PGLite maintenance under live owner`.
- Prior user-confirmed product constraints remain binding: PGLite only, gbrain behavior only, at least five mixed MCP/CLI callers, `query`/`search`/`think` priority over maintenance, unchanged public command syntax, no mandatory daemon, and direct-open fallback when no owner exists.

## Decision Boundaries

### Agent may decide

- Exact subprocess harness shape for real owner/proxy/CLI concurrency tests.
- Whether the owner process is a stdio MCP `gbrain serve`, a long-running CLI owner fixture, or another real gbrain subprocess path, as long as it owns PGLite through actual gbrain code.
- Which docs need updates beyond the known stale `docs/architecture/serve-sync-concurrency.md`.
- Exact status assertions and timeout budgets for deterministic tests.

### User must confirm

- Any new mandatory daemon or background service requirement.
- Any public command syntax change.
- Any network-facing broker or raw SQL forwarding expansion.
- Any claim that maintenance commands are truly queued/executed through the broker.
- Any decision to drop the minimum five-caller mixed CLI/MCP verification.

## Verification Method

- Inspect existing broker/lock tests and docs for coverage gaps.
- Add real subprocess integration tests for owner/proxy CLI/MCP concurrency.
- Add or preserve tests for stale socket recovery, stale lock recovery, corrupt/unknown lock safety, owner unreachable, and completion unknown.
- Update docs that still describe the old PGLite serve/sync contention model without the broker/defer distinction.
- Rerun the requirement 001-003 related suite and `bun run typecheck`.
- Record an E2E evidence matrix in closeout.

## Contract Preservation

- Requested behavior / artifact: end-to-end proof and docs for local PGLite concurrent access.
- Execution boundary: local PGLite owner broker plus command-level maintenance fallback, not network brokerage or database-level multi-writer access.
- Required evidence level: at least one real-subprocess E2E test for five mixed CLI/MCP interactive callers; synthetic IPC tests may supplement but cannot replace it.
- Known capability gaps: maintenance commands are deferred under a live owner; mid-transaction preemption and true maintenance queue execution remain out of scope.
- Allowed substitutions: a real gbrain subprocess fixture may use seeded local data or deterministic no-key behavior if it still exercises actual owner/proxy routing.
- Disallowed substitutions: injected socket-only tests as final E2E proof; stale docs as accepted operator guidance; broad "stop serve before sync" copy without interactive/maintenance distinction.
- Downgrade approval rule: dropping real five-caller mixed CLI/MCP verification requires explicit user confirmation.

## Iteration Policy

### Continue when

- Work adds real-subprocess evidence, closes stale diagnostics/docs gaps, or preserves requirements 001-003 behavior.
- A test failure reveals a missing status, race, or documentation contradiction within this requirement.

### Stop when

- A proposed fix would weaken PGLite lock safety or introduce network/raw SQL forwarding.
- A proposed test requires real user data, external APIs, or non-hermetic services.
- The minimum five-caller mixed CLI/MCP proof cannot be achieved without changing public behavior.

### Ask user when

- Reducing the five-caller mixed CLI/MCP proof.
- Introducing a mandatory daemon, new command syntax, or network broker behavior.
- Reclassifying maintenance commands from deferred to queued/executed.

### Checkpoint cadence

Update `progress.md`, `evidence.md`, and `decisions.md` after requirement review, research, technical design, plan reviews, implementation-brake, and closeout.

## Evidence Reviewed

- source_type: requirement
  location_or_reference: `requirements/001-pglite-owner-broker/requirements.md`
  extracted_fact: The accepted first requirement records the user-confirmed material product boundaries: PGLite only, gbrain behavior only, queue/serve concurrency rather than unsafe direct multi-process database access, interactive priority over maintenance, unchanged CLI command surfaces, direct-open fallback when no owner exists, and at least five simultaneous MCP/CLI callers without PGLite lock timeout.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/001-pglite-owner-broker/evidence.md`
  extracted_fact: Requirement 001 closeout and implementation-brake evidence confirm the owner-broker contract was built around five mixed callers, trust/source preservation, stale socket recovery diagnostics, and no-lock-timeout behavior.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/003-pglite-priority-scheduler/closeout.md`
  extracted_fact: Requirement 003 closed with `sync`, `embed`, and `extract` classified as `deferred_safe_fallback`, while interactive calls continue to use the owner broker.
  confidence: high
- source_type: test
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/test/cli-pglite-operation-broker.test.ts`
  extracted_fact: Existing tests cover five concurrent CLI callers, mixed CLI/MCP callers, maintenance-like owner broker exposure, MCP proxy source/auth behavior, and maintenance deferral using injected live-lock/socket fixtures.
  confidence: high
- source_type: test
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/test/pglite-operation-ipc.test.ts`
  extracted_fact: Existing IPC tests cover priority ordering, stale socket recovery, startup election, dropped clients, broker timeout, and protocol errors.
  confidence: high
- source_type: doc
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/docs/ENGINES.md`
  extracted_fact: ENGINES.md already documents local owner-broker routing for `query`, `search`, and `think`, but still says maintenance forwarding/yield is tracked separately in a table row.
  confidence: high
- source_type: doc
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/docs/architecture/serve-sync-concurrency.md`
  extracted_fact: The serve/sync concurrency guide still gives stale blanket guidance to stop `gbrain serve` before a large PGLite sync and does not describe the new interactive broker plus maintenance deferral contract.
  confidence: high
- source_type: sequence
  location_or_reference: `goal-requirements/001-pglite-concurrent-access/sequence.md`
  extracted_fact: Requirement 004 outcome is end-to-end concurrency, stale-owner recovery, diagnostics, and documentation coverage.
  confidence: high

## Artifact Handoff Contract

- producer role: requirement-clarifier
- consumer role: goal-requirement-orchestrator, research, technical-design, plan reviewers, implementation-brake reviewers, closeout
- artifact path or path-producing rule: `requirements/004-pglite-concurrency-verification/requirements.md`
- artifact purpose: Source-of-truth requirements for the integrated verification and documentation slice after owner forwarding and maintenance deferral.
- failure classification: Missing, stale, reviewer-unaccepted, or contradicted requirements block downstream gates.
- verification method: Post-draft reviewer returns structured `SHIP` or material findings are revised and rerun.

## Ambiguity / Readiness Summary

- Depth used: Quick
- Final ambiguity: 0.24
- Target ambiguity: 0.30
- Unresolved readiness gaps used to score ambiguity: Exact subprocess harness design and complete docs list require research/design.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
- Closure audit passed: yes
- Residual risk: Some current tests are socket-level/injected-owner tests; this requirement explicitly requires real-subprocess E2E evidence before closeout.

## Recommended Next Step

- research
- Reason: Real subprocess harness design, stale-owner diagnostics, and docs contradiction coverage need research before design.

## Open Questions

None blocking for reviewer.
