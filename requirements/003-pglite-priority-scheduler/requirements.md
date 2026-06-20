---
requirement_id: 003-pglite-priority-scheduler
feature_name: PGLite Priority Scheduler
created_by: requirement-clarifier
created_at: 2026-06-20T10:10:00Z
updated_at: 2026-06-20T10:35:00Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Priority Scheduler

## Readiness Status

Ready. The post-draft reviewer rerun returned `SHIP`; research and design may proceed.

## User Story

As a gbrain user whose PGLite brain is busy with local maintenance work, I can still run `gbrain query`, `gbrain search`, or `gbrain think` from another CLI or stdio MCP caller and have that interactive request queue or serve ahead of maintenance work instead of timing out on the PGLite lock.

## Problem / Intent / Outcome

Requirement 002 proved local operation forwarding for `query`, `search`, and `think` when a PGLite owner exists. The remaining concurrency risk is that long-running or repeated maintenance operations can own the PGLite connection while interactive callers wait on the PGLite file lock or sit behind lower-value work.

This slice locks the priority contract:

- interactive operations are `query`, `search`, and `think`
- maintenance operations are `sync`, `embed`, and `extract`
- when maintenance owns PGLite, interactive calls must be accepted through the local owner broker and served before queued maintenance work where the implementation has a queue boundary
- maintenance work must remain bounded and safe; priority must not weaken locks, corrupt state, or claim preemption inside an already-running non-interruptible DB transaction

## Acceptance Criteria

- AC1. A PGLite maintenance owner exposes the local operation broker while running.
  - Verification: automated test starts a controlled maintenance-owner path or maintenance-like owner and proves a second CLI/MCP `query`, `search`, or `think` call does not attempt direct PGLite open or emit PGLite lock timeout text.
- AC2. Interactive `query`, `search`, and `think` requests have higher queue priority than maintenance-class requests at the broker queue boundary.
  - Verification: automated IPC or integration test enqueues lower-priority maintenance-class work and later interactive work, then asserts interactive work is served first after the currently-running item finishes.
- AC3. The priority contract is bounded and honest.
  - Verification: tests or implementation-brake evidence state that the implementation does not abort, rollback, or preempt an already-running DB transaction; priority applies at enqueue/drain or checkpoint boundaries only.
- AC4. Maintenance callers do not create PGLite lock timeout storms when another live owner exists.
  - Verification: automated test covers a second `sync`, `embed`, or `extract`-class maintenance attempt while a live owner exists and asserts deterministic queued/bounded/deferred behavior, not raw PGLite lock timeout.
- AC5. Each real maintenance command has explicit coverage or explicit safe fallback classification.
  - Verification: closeout includes a matrix for `sync`, `embed`, and `extract`. Each row must be one of:
    - `covered_real_command`: real command integration evidence proves interactive requests can queue/serve at a safe boundary or maintenance receives deterministic bounded behavior.
    - `deferred_safe_fallback`: the command is intentionally not integrated in this slice, and a real-command test proves it returns a deterministic non-lock-timeout fallback while a live owner exists.
    - `blocked_user_decision`: the user explicitly accepts dropping or moving that command's behavior to a later requirement.
  - Synthetic `maintenance` IPC queue tests alone do not satisfy this AC for any of `sync`, `embed`, or `extract`.
- AC6. Existing public command syntax remains unchanged for `sync`, `embed`, `extract`, `query`, `search`, and `think`.
  - Verification: command smoke tests or code inspection confirm no new required daemon flag or syntax is introduced.
- AC7. Forwarding remains local-only and operation-level.
  - Verification: code review confirms this slice reuses the filesystem operation IPC boundary and does not introduce raw SQL forwarding or a network listener.
- AC8. Requirement 002 behavior does not regress.
  - Verification: rerun the requirement 002 related suite, including CLI/MCP operation forwarding tests and stdio source/auth tests.

## Out Of Scope / Avoid

- Do not implement network-accessible broker behavior.
- Do not weaken, remove, bypass, or silently delete the PGLite file lock.
- Do not claim mid-transaction preemption unless the underlying operation actually supports safe checkpoints.
- Do not require users to manually start a separate daemon before normal commands work.
- Do not change public command syntax.
- Do not expand this slice to final end-to-end readiness; requirement 004 owns broad concurrency verification and diagnostics, and requirement 005 owns production readiness.

## Success Metrics

- Interactive work has automated priority evidence over queued maintenance-class work.
- A live maintenance owner does not cause `query`, `search`, or `think` to fail with normal PGLite lock timeout.
- Maintenance contention returns a deterministic bounded result rather than raw PGLite lock timeout.
- Requirement 002 forwarding and MCP source/auth parity tests continue to pass.

## Failure Condition

This requirement fails if an accepted interactive caller path still waits on or times out on the PGLite file lock while a maintenance owner is live, if maintenance priority claims rely on unimplemented preemption, or if the fix changes public command syntax, exposes raw SQL/network forwarding, or weakens lock safety.

## Edge Cases

- Maintenance owner is starting but the operation socket is not yet bound.
- Maintenance owner dies while an interactive request is queued.
- A maintenance request is already running and cannot safely yield mid-transaction.
- Multiple interactive callers arrive while maintenance work is queued.
- A second maintenance caller arrives while another maintenance owner is live.
- One of `sync`, `embed`, or `extract` proves too large for real integration in this slice and must be classified as `deferred_safe_fallback` with actual command evidence.
- Corrupt/unknown lock state exists before maintenance or interactive routing.
- `think --save` remains remote read-only under MCP and local save semantics remain unchanged.

## Constraints

- Scope is PGLite only.
- Priority applies to local owner-broker scheduling or safe operation checkpoints, not arbitrary process preemption.
- Postgres behavior must remain unchanged except for shared abstractions that preserve behavior.
- Requirement 002 commit `3acdc5e60d94fded5b9c1a567bb839c896db02c0` is relevant baseline evidence but not automatic acceptance.

## Decision Boundaries

### Agent may decide

- Whether priority evidence is best implemented at IPC unit level, CLI integration level, or both.
- Whether `sync`, `embed`, and `extract` can all use the same maintenance-owner pattern or need separate adapters.
- Whether a maintenance operation should be deferred with deterministic fallback if safe integration is too large for this slice.
- Exact test harness shape for the required per-command coverage matrix.

### User must confirm

- Any change to public command syntax.
- Any mandatory daemon requirement.
- Any expansion to remote/network forwarding.
- Any decision to drop `sync`, `embed`, or `extract` from the final sequence outcome.
- Any `blocked_user_decision` classification for a maintenance command.

## Verification Method

- Inspect current owner-broker modules: `src/core/pglite-operation-ipc.ts`, `src/mcp/pglite-operation-dispatch.ts`, `src/cli.ts`, `src/mcp/server.ts`.
- Inspect maintenance command entry points for `sync`, `embed`, and `extract`.
- Add or update automated tests for priority ordering and maintenance-owner contention.
- Produce a per-command maintenance coverage matrix for `sync`, `embed`, and `extract`; synthetic IPC queue tests may supplement but not replace this evidence.
- Rerun requirement 002 related suite plus any new maintenance-focused tests.
- Record an AC-to-evidence map before implementation-brake.

## Per-Command Coverage Matrix Contract

Closeout must include the following matrix and must not mark this requirement complete until every row has a non-blocking classification:

| Command | Required classification | Minimum acceptable evidence |
| --- | --- | --- |
| `sync` | `covered_real_command`, `deferred_safe_fallback`, or `blocked_user_decision` | real CLI or command-level test while a live PGLite owner exists |
| `embed` | `covered_real_command`, `deferred_safe_fallback`, or `blocked_user_decision` | real CLI or command-level test while a live PGLite owner exists |
| `extract` | `covered_real_command`, `deferred_safe_fallback`, or `blocked_user_decision` | real CLI or command-level test while a live PGLite owner exists |

Rules:

- `covered_real_command` may use a fixture or stubbed maintenance workload, but it must enter through that command's real dispatch path or a narrowly factored command core used by that path.
- `deferred_safe_fallback` must prove the real command does not emit raw PGLite lock timeout and does not direct-open past a live owner; the fallback copy must be deterministic enough for an operator or agent to understand.
- `blocked_user_decision` requires explicit user approval and must be recorded in `decisions.md`.
- Generic IPC priority tests are still required for scheduler correctness, but they do not count as real command coverage for this matrix.

## Contract Preservation

- Requested behavior / artifact: interactive `query`, `search`, and `think` priority over PGLite maintenance contention involving `sync`, `embed`, and `extract`.
- Execution boundary: local PGLite owner-broker scheduling and safe command checkpoints/fallbacks.
- Required evidence level: generic queue priority tests plus per-command maintenance matrix evidence for `sync`, `embed`, and `extract`; requirement 002 regression suite must remain green.
- Known capability gaps: safe mid-transaction preemption may not exist for some maintenance paths; those paths must be classified honestly rather than overclaimed.
- Allowed substitutions: command-core tests may substitute for full CLI tests only when the core is the same path used by the CLI and the test still runs against a live-owner PGLite contention shape.
- Disallowed substitutions: synthetic maintenance IPC tests as the only proof for real `sync`/`embed`/`extract`; public syntax changes; raw SQL forwarding; network listener; lock weakening; silent downgrade from priority to ordinary lock wait.
- Downgrade approval rule: any downgrade from real command coverage to `deferred_safe_fallback` is allowed only when implementation-brake accepts the evidence as non-blocking; any downgrade to `blocked_user_decision` requires explicit user confirmation.

## Iteration Policy

### Continue when

- Work maps to AC1-AC8, the per-command coverage matrix, or requirement 002 regression preservation.
- A command integration proves a safe queue/checkpoint boundary or a deterministic non-lock-timeout fallback.

### Stop when

- A fix would require weakening PGLite lock safety, raw SQL forwarding, network broker behavior, or public command syntax changes.
- A plan claims preemption inside already-running DB transactions without code support and tests.
- A maintenance command cannot be covered or safely deferred without user approval.

### Ask user when

- Classifying any of `sync`, `embed`, or `extract` as `blocked_user_decision`.
- Expanding priority behavior to commands beyond `sync`, `embed`, and `extract`.
- Introducing a mandatory daemon, public syntax change, or network-facing broker.

### Checkpoint cadence

After research, technical-design, plan review, implementation-brake, and closeout, update `progress.md`, `evidence.md`, and when relevant `decisions.md` with the current per-command coverage matrix state.

## Evidence Reviewed

- source_type: requirement
  location_or_reference: `requirements/002-pglite-operation-forwarding/closeout.md`
  extracted_fact: Requirement 002 closed local forwarding for `query`, `search`, and `think` and explicitly left maintenance priority/yield for requirement 003.
  confidence: high
- source_type: code
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/core/pglite-operation-ipc.ts`
  extracted_fact: Current IPC queue already has operation classes and priority ordering at the queue boundary.
  confidence: high
- source_type: sequence
  location_or_reference: `goal-requirements/001-pglite-concurrent-access/sequence.md`
  extracted_fact: Requirement 003 outcome is interactive priority and bounded maintenance behavior for `sync`, `embed`, and `extract`.
  confidence: high

## Artifact Handoff Contract

- producer role: requirement-clarifier
- consumer role: goal-requirement-orchestrator, research, technical-design, plan reviewers, implementation-brake reviewers
- artifact path or path-producing rule: `requirements/003-pglite-priority-scheduler/requirements.md`
- artifact purpose: Source-of-truth requirements for the priority scheduling slice after operation forwarding.
- failure classification: Missing, stale, reviewer-unaccepted, or contradicted requirements block downstream gates.
- verification method: Post-draft reviewer returns structured `SHIP` or material findings are revised and rerun.

## Ambiguity / Readiness Summary

- Depth used: Quick
- Final ambiguity: 0.22
- Target ambiguity: 0.30
- Unresolved readiness gaps used to score ambiguity: Exact integration approach for real `sync`, `embed`, and `extract` requires research/design.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
- Closure audit passed: yes
- Residual risk: Some maintenance operations may not have safe mid-operation yield points; this requirement deliberately permits bounded checkpoint/queue priority or deterministic non-lock-timeout fallback rather than pretending arbitrary preemption exists.

## Recommended Next Step

- research
- Reason: Maintenance operation integration and priority/yield boundaries must be researched before design or implementation.

## Open Questions

None blocking for reviewer.
