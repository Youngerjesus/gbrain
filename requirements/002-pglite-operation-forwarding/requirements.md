---
requirement_id: 002-pglite-operation-forwarding
feature_name: PGLite Operation Forwarding
created_by: requirement-clarifier
created_at: 2026-06-20T07:35:00Z
updated_at: 2026-06-20T07:35:00Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Operation Forwarding

## Readiness Status

Ready. The post-draft reviewer returned structured `SHIP` with no findings. Requirement 001 established and implemented the owner-broker boundary. This slice locks the narrower operation-forwarding contract so the sequence can prove that `query`, `search`, and `think` discover a live PGLite owner, forward locally through that owner, and preserve CLI/MCP behavior without relying on direct multi-process PGLite access.

## User Story

As a gbrain user with a PGLite brain already opened by a CLI or stdio MCP owner process, I can run another local CLI or stdio MCP `query`, `search`, or `think` call and have it reach the owner safely instead of failing on the PGLite lock.

## Problem / Intent / Outcome

The sequence outcome requires user-observable concurrent access. Requirement 001 created the owner-broker contract; this requirement focuses on the forwarding path itself:

- caller-side owner discovery before direct PGLite open
- local-only IPC request forwarding for `query`, `search`, and `think`
- owner-side dispatch parity for CLI and MCP callers
- direct-open fallback when no owner exists
- deterministic error semantics when forwarding cannot safely complete

The intended outcome is that operation forwarding is no longer an implicit side effect of the broker implementation; it is an explicitly accepted, testable slice with evidence tied to each caller path.

## Acceptance Criteria

- AC1. CLI owner discovery happens before direct PGLite open for `gbrain query`, free-text `gbrain search`, and `gbrain think` when a live PGLite lock exists.
  - Verification: automated CLI test runs each command while a live owner lock/socket exists and fails if stderr/stdout contains `Timed out waiting for PGLite lock`, `Could not acquire PGLite lock`, or `Another gbrain process is using the database`.
- AC2. A second stdio MCP server process started while a PGLite owner exists does not open PGLite directly for `query`, `search`, or `think`; it exposes those tools and forwards calls to the owner.
  - Verification: JSON-RPC stdio MCP test starts a second `gbrain serve`, lists tools, calls `query`, `search`, and `think`, and asserts the owner receives the forwarded operations.
- AC3. When no live PGLite owner exists, existing local CLI direct-open behavior remains intact for `query`, `search`, and `think`.
  - Verification: no-owner CLI smoke test runs the existing command forms and asserts success or the command's existing non-lock failure mode, not a broker-only error.
- AC4. Owner-side dispatch preserves caller semantics.
  - Verification: brokered CLI calls carry caller `cwd` / source information for source resolution; brokered `mcp-stdio` calls route through the same MCP dispatch envelope as direct stdio MCP, including `remote=true`, takes-holder privacy defaults, and `invalid_params` error shape.
- AC5. Forwarding is local-only and operation-level.
  - Verification: code review or unit test confirms the forwarding transport is a filesystem socket path under the PGLite data directory, uses newline-delimited operation requests, and does not expose raw SQL or a network listener.
- AC6. Forwarding failure states are deterministic and safe.
  - Verification: tests cover absent owner socket, owner-unreachable proxy result, request-accepted timeout as `completion_unknown`, corrupt/unknown lock as `lock_safety_blocked`, and closed queued client skip behavior.
- AC7. If current implementation from requirement 001 already satisfies any AC, the downstream gates may reuse that evidence only after explicitly mapping current code/tests to the AC and confirming the evidence is not stale.
  - Verification: research/design or implementation-brake artifact records reused evidence paths, commit `d50dc701`, and any required re-run commands.

## Out of Scope / Avoid

- Do not implement or claim real `sync`, `embed`, or `extract` maintenance yielding in this slice; that remains requirement 003.
- Do not add a network-accessible operation broker or HTTP MCP owner proxy in this slice.
- Do not weaken, remove, or bypass the PGLite file lock.
- Do not require users to manually start a daemon before `query`, `search`, or `think` can work.
- Do not change public CLI command syntax for `query`, `search`, or `think`.
- Do not treat conversation memory as sufficient proof that requirement 001 implementation satisfies this slice; current files and command output must be inspected.

## Success Metrics

- `query`, `search`, and `think` have automated coverage for owner-forwarded CLI paths.
- stdio MCP proxy behavior is covered for all three forwarded tools.
- No accepted forwarding path can fall through to normal PGLite lock wait while a live owner exists.
- Forwarded MCP error/privacy behavior matches direct MCP dispatch for tested cases.

## Failure Condition

This requirement fails if any accepted `query`, `search`, or `think` caller path still attempts to open file-backed PGLite directly while a live owner lock exists, or if forwarding succeeds only by changing CLI syntax, erasing MCP remote semantics, exposing raw SQL, or weakening PGLite lock safety.

## Edge Cases

- Live lock exists but operation socket is absent, stale, permission denied, or not yet bound.
- Owner dies after discovery but before response.
- Request is accepted but the caller times out before completion.
- Caller closes while queued before owner starts handling it.
- CLI caller is launched from a repo/source path that affects source resolution.
- MCP caller sends invalid params and expects MCP-style error envelope.
- `think --save` is brokered locally and must preserve existing save failure behavior when no synthesis is produced.
- Remote MCP `think` persistence remains blocked even when forwarded.

## Constraints

- Scope is PGLite only.
- Transport must be local-only.
- The forwarding request must be operation-level, not SQL-level.
- Postgres behavior must remain unchanged except for behavior-preserving shared abstractions.
- Current requirement 001 commit `d50dc701` is relevant evidence but not automatic acceptance.

## Contract Preservation

- Requested behavior / artifact: local owner forwarding for PGLite `query`, `search`, and `think`.
- Execution boundary: callers discover an owner before PGLite connect and forward operation requests to the owner process over local IPC.
- Required evidence level: CLI owner-forwarding tests, stdio MCP proxy tests, context/error parity tests, failure-state tests, and code evidence for local-only operation transport.
- Known capability gaps: maintenance priority/yield behavior for `sync`, `embed`, and `extract` remains outside this slice.
- Allowed substitutions: existing requirement 001 implementation evidence may satisfy this slice when explicitly revalidated.
- Disallowed substitutions: direct multi-process PGLite open, network broker, raw SQL forwarding, changed command syntax, or unreviewed reuse of stale evidence.

## Iteration Policy

### Continue when

- Work maps current code/tests to one of AC1-AC7 or repairs a real forwarding gap.
- Reused evidence is checked against current files and current test output.

### Stop when

- A fix would require weakening PGLite lock safety or changing public CLI syntax.
- A design conflates operation forwarding with requirement 003 maintenance scheduling.

### Ask user when

- Expanding forwarding to operations beyond `query`, `search`, and `think`.
- Adding network-facing broker access.
- Treating HTTP MCP serve forwarding as in-scope for this slice.

### Checkpoint cadence

After each gate, record whether this slice is satisfied by current implementation evidence, needs additional code, or should be reconciled with a later requirement.

## Decision Boundaries

### Agent may decide

- Whether this slice needs additional code or can close through revalidation of current implementation.
- Exact test names and fixture setup for forwarding evidence.
- Whether owner-forwarding evidence belongs in unit, CLI integration, or stdio MCP integration tests.

### User must confirm

- Any change to public command syntax.
- Any expansion to remote/network operation forwarding.
- Any decision to merge requirement 002 with requirement 003 or drop it from the sequence.

## Verification Method

- Inspect current implementation files: `src/cli.ts`, `src/mcp/server.ts`, `src/core/pglite-operation-ipc.ts`, `src/core/pglite-operation-dispatch.ts`, `src/core/pglite-lock.ts`.
- Re-run forwarding-relevant tests: `test/cli-pglite-operation-broker.test.ts`, `test/pglite-operation-ipc.test.ts`, and `test/pglite-lock.test.ts`.
- For broader regression, re-run the related suite used in requirement 001 closeout when code changes are made.
- Record AC-to-evidence mapping before implementation-brake.

## Evidence Reviewed

- source_type: sequence
  location_or_reference: `goal-requirements/001-pglite-concurrent-access/sequence.md`
  extracted_fact: Requirement 002 outcome is owner discovery and local-only operation forwarding for `query`, `search`, and `think`.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/001-pglite-owner-broker/closeout.md`
  extracted_fact: Requirement 001 closed with owner-broker implementation and noted that requirement 002 should continue the sequence.
  confidence: high
- source_type: code
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/core/pglite-operation-ipc.ts`
  extracted_fact: The current implementation defines local operation IPC request/response types, socket path, forwarding client, owner server, queueing, startup election, and forwarding failure statuses.
  confidence: high
- source_type: code
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/cli.ts`
  extracted_fact: The current implementation has pre-connect broker routing for eligible CLI operations and direct-open fallback when no live owner exists.
  confidence: high
- source_type: code
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/mcp/server.ts`
  extracted_fact: The current implementation has a stdio MCP operation proxy server for `query`, `search`, and `think`.
  confidence: high
- source_type: tests
  location_or_reference: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/test/cli-pglite-operation-broker.test.ts`
  extracted_fact: Current tests cover CLI-owned MCP invalid params parity, five concurrent query callers, mixed query/search/think callers, no-owner query/think direct-open behavior, five mixed CLI+MCP callers, caller cwd source handoff, corrupt lock safety, and second stdio MCP proxy behavior.
  confidence: high
- source_type: tests
  location_or_reference: requirement 001 closeout command output
  extracted_fact: The related suite passed with 79 tests and `tsc --noEmit`.
  confidence: high

## Artifact Handoff Contract

- producer role: requirement-clarifier
- consumer role: goal-requirement-orchestrator, research, technical-design, plan reviewers, implementation-brake reviewers
- artifact path or path-producing rule: `requirements/002-pglite-operation-forwarding/requirements.md`
- artifact purpose: Source-of-truth requirements for the operation-forwarding slice after the owner-broker contract.
- failure classification: Missing, stale, reviewer-unaccepted, or contradicted requirements block downstream gates.
- verification method: Post-draft reviewer returns structured `SHIP` or material findings are revised and rerun.

## Ambiguity / Readiness Summary

- Depth used: Quick
- Final ambiguity: 0.05
- Target ambiguity: 0.30
- Unresolved readiness gaps used to score ambiguity: Whether additional code is needed versus evidence revalidation is intentionally left to downstream gates.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
  - Pressure pass completed: yes; this requirement explicitly avoids silently treating requirement 001's implementation as complete without current evidence mapping.
  - Closure audit passed: yes
- Residual risk: Current evidence appears strong, but this slice must still perform AC-to-evidence mapping and reviewer gates before closeout.

## Assumptions

- Requirement 001's task branch commit `d50dc701` remains available for revalidation.
- The user still wants the sequence executed as written, even if requirement 001 implementation already covers some later-slice behavior.

## Recommended Next Step

- research
- Reason: Downstream work must decide whether this slice requires new implementation or can be closed by evidence-backed revalidation of the current owner-forwarding implementation.

## Planning Handoff

Do not implement directly from this requirement. Start by mapping AC1-AC7 to current code and tests, then determine which required gates can be satisfied by existing evidence and which require new work.

## Open Questions

None blocking.
