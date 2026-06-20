---
requirement_id: 007-pglite-broker-guard-implementation
feature_name: PGLite Broker Guard Implementation
created_by: requirement-clarifier
created_at: 2026-06-20T15:25:41Z
updated_at: 2026-06-20T15:25:41Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Broker Guard Implementation

## Readiness Status

Ready. The post-draft reviewer returned structured `SHIP` with no material findings. The scope is explicit and testable: implement the behavior classes accepted by requirement 006 for every row in `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.

## User Story

As a local gbrain operator or agent using a PGLite-backed brain while `gbrain serve` owns the database, I need every PGLite-touching CLI and MCP path to either route through the owner, serialize safely through the owner, or fail fast with a typed guard error so command output never exposes raw PGLite lock/connect timeout text.

## Problem / Intent / Outcome

Requirement 006 proved that the prior broker only solved a narrow `query` / `search` / `think` subset and produced a 468-row inventory of remaining PGLite-touching paths. This slice must turn that inventory into product behavior without rediscovering or narrowing the scope.

The intended outcome is a runtime implementation that consumes the accepted inventory classification:

- `broker_success_read` rows route through the live owner and preserve successful read/diagnostic behavior.
- `serialized_owner_mutation` rows execute through owner-owned serialization when allowed by the existing trust boundary.
- `typed_guard_fail_fast` rows return a bounded typed error before direct PGLite open under live-owner conditions.

No in-scope live-owner path may surface raw PGLite lock/connect timeout as the product-boundary result.

## Acceptance Criteria

- AC1. Consume the accepted requirement 006 inventory as the implementation contract.
  - Verification: implementation planning and tests validate `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` before coding; the row count, class counts, source fingerprints, and required surface ids are treated as authoritative unless a recorded requirement-impact decision updates the inventory and reruns its validator.
- AC2. Implement owner-broker routing for all `broker_success_read` rows.
  - Verification: under a live local owner, representative CLI `call`, direct CLI read/diagnostic, stdio MCP, HTTP MCP, and existing `query`/`search`/`think` rows return through the owner path with no raw lock/connect timeout; no-owner direct-open behavior remains valid where requirement 006 recorded it as the baseline.
- AC3. Implement owner-owned serialization for all `serialized_owner_mutation` rows that are allowed for the caller.
  - Verification: mutating local CLI and allowed MCP operation rows are routed to owner-owned execution or an owner-owned queue/dispatch path that prevents concurrent direct PGLite open. A row classified `serialized_owner_mutation` may not be silently downgraded to a guard-only result without updating the inventory and recording user-approved requirement impact.
- AC4. Implement typed fail-fast guards for all `typed_guard_fail_fast` rows.
  - Verification: maintenance, migration, schema/exclusive-owner, local-only remote rejection, stale owner, and unavailable-owner cases return stable typed errors with documented exit-code/error-shape behavior before direct PGLite open; stderr/stdout do not contain raw PGLite lock/connect timeout text.
- AC5. Preserve trusted-local versus remote-MCP security boundaries.
  - Verification: `OperationContext.remote`, local-only operation checks, protected operation checks, filesystem confinement, source auth, budget/auth scopes, and `file_upload` restrictions remain at least as strict as before. Remote MCP must not gain access to local-only or filesystem-sensitive capabilities merely because a local owner can serialize them.
- AC6. Handle owner-state variants deterministically.
  - Verification: tests cover healthy live owner, no owner, live PGLite lock with missing/stale owner socket, owner startup/duplicate-owner-start, broker timeout, and owner unreachable states. Each state maps to brokered success, serialized execution, or a typed guard error; none map to raw PGLite lock/connect timeout.
- AC7. Preserve public command syntax while improving product-boundary errors.
  - Verification: existing CLI command names, MCP tool names, argument shapes, and JSON envelopes remain compatible unless explicitly approved by the user. Any new error codes are typed, bounded, and documented in tests/evidence with exit code, stderr, stdout, and structured error shape.
- AC8. Replace requirement 006 expected-red rows with implementation evidence.
  - Verification: the requirement 006 gauntlet or a successor requirement-007 gauntlet proves that previously expected-red live-owner rows, including `gbrain call list_pages {}`, no longer emit raw PGLite lock/connect timeout and now satisfy their accepted behavior class.
- AC9. Add class-complete regression coverage for the implementation.
  - Verification: tests include positive and negative coverage for read broker routing, serialized mutation routing, typed guard fail-fast, remote local-only rejection, filesystem-sensitive operations, stale/missing owner states, and no-owner baseline preservation. Coverage may use representative rows plus inventory-bound manifest validation in this slice, while requirement 008 remains responsible for the full repeated named matrix.
- AC10. Produce handoff-ready evidence for requirement 008.
  - Verification: closeout records implemented behavior by class, remaining verification-only risks, updated gauntlet/test paths, exact commands run, any accepted deferrals, and the next requirement path `requirements/008-pglite-all-access-concurrency-verification/requirements.md`.

## Out Of Scope / Avoid

- Do not reduce the implementation scope to only `query`, `search`, `think`, or the five live-runnable rows from requirement 006.
- Do not accept raw PGLite lock/connect timeout text as an allowed product-boundary result for any in-scope live-owner path.
- Do not delete, force-remove, or auto-clean live PGLite locks as a concurrency fix.
- Do not introduce a network-accessible broker, raw SQL forwarding, or unauthenticated owner dispatch.
- Do not broaden remote-MCP authority, weaken `OperationContext.remote`, bypass protected operation checks, or relax filesystem confinement.
- Do not change public CLI syntax, MCP tool names, or request schemas without explicit user confirmation.
- Do not silently reclassify an inventory row to a weaker behavior class; inventory changes require recorded requirement impact and validator rerun.
- Do not rely on substring checks as authoritative proof of semantic routing, security, or completion; use structured errors, typed fields, validators, and deterministic tests.

## Success Metrics

- 100% of requirement 006 inventory rows have an implemented behavior path or an explicitly recorded, user-approved inventory update.
- 0 raw PGLite lock/connect timeout product-boundary results across requirement 007 targeted live-owner tests.
- All typed guard failures expose stable error code/error shape/exit-code behavior.
- Existing `query`, `search`, `think`, no-owner PGLite direct-open behavior, remote authorization, and filesystem confinement tests remain green.
- Requirement 008 can run final all-access verification without rediscovering implementation scope.

## Failure Condition

This requirement fails if any accepted inventory row still bypasses owner routing and can surface raw PGLite lock/connect timeout under a live owner, if mutating or filesystem-sensitive paths gain broader remote authority, if `serialized_owner_mutation` rows are converted to guard-only behavior without approved inventory impact, or if evidence covers only a representative subset while claiming all rows are implemented.

## Edge Cases

- `gbrain call list_pages {}` under a healthy live owner.
- A local mutating `gbrain call` operation under a healthy live owner.
- A remote MCP caller attempts a local-only or filesystem-sensitive operation.
- `sync`, `embed`, `extract`, `apply-migrations`, `upgrade`, and doctor remediation under live-owner conditions.
- Owner lock exists but owner socket is missing, stale, delayed, or unreachable.
- Owner broker is healthy but busy or times out.
- No owner is active and direct local PGLite access should continue to work.
- Duplicate owner startup attempts while another owner already holds the lock.
- File upload and source-management operations with path confinement and remote context.
- Empty or uninitialized temporary homes, stale schema, or migration-pending state during tests.

## Constraints

- Scope is local PGLite-backed gbrain behavior.
- The accepted inventory path is `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.
- Current accepted inventory count is 468 rows: 217 `broker_success_read`, 223 `serialized_owner_mutation`, and 28 `typed_guard_fail_fast`.
- The later sequence standard remains N=3 repeated concurrent attempts with `raw_lock_timeout_allowed: false`.
- Product runtime may add internal dispatch/serialization APIs, but requirement artifacts and test validators must not become runtime dependencies.
- Remote-MCP security boundaries are compatibility-sensitive and must be preserved by default.
- Public command syntax and MCP schemas remain stable unless the user explicitly approves a change.
- Tests must use temporary homes/backends and must not depend on or mutate the user's live brain.

## Contract Preservation

- Requested behavior / artifact: runtime broker/serialization/typed-guard implementation for every accepted PGLite-touching inventory row.
- Execution boundary: local owner process, local CLI, local stdio/HTTP MCP surfaces, and temporary test homes only; no network broker expansion.
- Required evidence level: targeted implementation tests, updated gauntlet or successor manifest, inventory validator pass, exit code/stderr/stdout/error-shape evidence, and implementation-brake `[SHIP]`.
- Known capability gaps: final repeated all-row named matrix proof is reserved for requirement 008; requirement 007 must still implement all row classes and provide representative class-complete evidence.
- Allowed substitutions: an inventory row may be updated only through a recorded requirement-impact decision, validator rerun, and user confirmation when the change reduces behavior strength or scope.
- Disallowed substitutions: representative-only implementation, guard-only downgrade for serialized mutation rows, raw timeout acceptance, remote authority broadening, or prose-only evidence.
- Downgrade approval rule: any reduction in row coverage, behavior class, evidence level, security posture, or public compatibility requires explicit user approval recorded in `decisions.md`.

## Iteration Policy

### Continue when

- Implementation discovers a missing or stale inventory row and can update the inventory with validator evidence.
- A test exposes raw lock/connect timeout under a live owner.
- A row needs a stronger typed error, serialization route, or trust-boundary guard to satisfy its accepted class.
- A reviewer finds evidence overclaiming, route bypass, or security-boundary drift.

### Stop when

- A proposed implementation would delete locks, mutate real user data, run irreversible migrations outside a temp fixture, or weaken remote/file confinement.
- The accepted inventory and repo reality conflict in a way that changes scope or behavior class.
- A row cannot be safely implemented without changing public command syntax, security posture, or accepted sequence scope.

### Ask user when

- Reclassifying an accepted row to a weaker or narrower behavior.
- Excluding any PGLite-touching path from this requirement.
- Changing public CLI/MCP syntax or response schemas.
- Adding network-facing owner dispatch or broadening remote authority.
- Accepting lower evidence than the requirement 007 targeted implementation proof plus requirement 008 final matrix.

### Checkpoint cadence

Update `progress.md`, `evidence.md`, and `decisions.md` after requirement review, research, technical design, plan reviews, implementation milestones, devex-review, implementation-brake, and closeout.

## Decision Boundaries

### Agent may decide

- Internal module boundaries for owner dispatch, serialization, guards, and test helpers.
- Exact typed error code names when they are stable, documented in tests, and compatibility-preserving.
- Which representative rows prove each class in requirement 007, as long as all rows are implementation-covered and requirement 008 remains responsible for the full repeated matrix.
- Whether to add validator/test helper APIs to keep inventory-to-implementation mapping deterministic.

### User must confirm

- Any row exclusion, weaker class, or behavior downgrade from the accepted inventory.
- Any public CLI syntax, MCP schema, or documented command behavior change.
- Any remote-MCP authorization expansion, filesystem confinement relaxation, or protected-operation bypass.
- Any network-facing owner broker or raw SQL forwarding design.
- Any irreversible migration/data deletion/lock deletion behavior used as a fix.

## Verification Method

- Validate the requirement 006 inventory before planning and after any inventory-impact edit.
- Inspect existing owner broker, operation IPC, CLI dispatch, MCP dispatch, PGLite lock, engine creation, file upload, doctor, migration, sync/embed/extract, and source-management paths.
- Add failing tests first for current raw timeout or bypass behavior on representative rows, including `gbrain call list_pages {}`.
- Add implementation tests for brokered read routing, serialized owner mutation, typed guard fail-fast, no-owner baseline, stale/missing owner, and remote local-only rejection.
- Run the updated requirement 006 gauntlet or a requirement 007 successor gauntlet against temporary PGLite homes and capture exit code, stdout, stderr, typed error shape, and raw-timeout classification.
- Run existing PGLite broker and relevant CLI/MCP trust-boundary tests.
- Run the requirement 007 coverage ledger in closure mode before closeout.

## Evidence Reviewed

- source_type: sequence
  location_or_reference: `goal-requirements/002-pglite-all-access-concurrency/sequence.md`
  extracted_fact: Requirement 007 must implement per-operation broker-success, serialized owner execution, or typed guard-fail-fast behavior according to the accepted inventory classification.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/006-pglite-access-path-inventory/requirements.md`
  extracted_fact: Requirement 006 defined zero raw PGLite lock/connect timeout as the later sequence standard and required handoff-ready inventory plus gauntlet artifacts for requirement 007.
  confidence: high
- source_type: artifact
  location_or_reference: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
  extracted_fact: The accepted inventory contains 468 rows with 217 `broker_success_read`, 223 `serialized_owner_mutation`, 28 `typed_guard_fail_fast`, and N=3 later sequence attempts with raw lock timeout disallowed.
  confidence: high
- source_type: evidence
  location_or_reference: `requirements/006-pglite-access-path-inventory/evidence.md`
  extracted_fact: The minimal gauntlet currently includes expected-red raw timeout evidence for `gbrain call list_pages {}` under a live owner and records broad verify's unrelated baseline isolation failure.
  confidence: high
- source_type: code
  location_or_reference: `src/core/pglite-operation-ipc.ts`, `src/cli.ts`, `src/mcp/server.ts`, `src/mcp/dispatch.ts`, `src/core/pglite-lock.ts`
  extracted_fact: Existing owner IPC, CLI/MCP dispatch, and lock behavior are the likely implementation boundaries for broker/guard behavior.
  confidence: medium
- source_type: user_decision
  location_or_reference: current sequence decisions from 2026-06-20
  extracted_fact: The user selected all PGLite-touching paths, including sync/embed/extract/doctor remediation/migrations/file upload, with verification of exit code/error shape/stderr and zero lock/connect timeout across the named matrix.
  confidence: high

## Artifact Handoff Contract

### Inventory Contract

- producer role: requirement 006 closeout
- consumer role: requirement 007 research, technical-design, implementation, implementation-brake
- artifact path or path-producing rule: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- artifact purpose: authoritative row-by-row behavior-class source for implementation.
- failure classification: missing, validator-failing, stale fingerprint, row-count drift, class-count drift, or unapproved class change blocks implementation planning.
- verification method: `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json`

### Implementation Evidence Contract

- producer role: requirement 007 implementation
- consumer role: devex-review, implementation-brake, closeout, requirement 008
- artifact path or path-producing rule: tests, gauntlet manifests, and evidence paths recorded in `requirements/007-pglite-broker-guard-implementation/evidence.md`
- artifact purpose: prove that each behavior class has runtime implementation evidence and that previously expected-red paths no longer surface raw lock/connect timeout.
- failure classification: missing class evidence, missing raw-timeout classifier evidence, missing exit-code/error-shape evidence, or representative-only evidence presented as all-row proof blocks closeout.
- verification method: targeted Bun tests, inventory validator, coverage-ledger closure, and implementation-brake `[SHIP]`.

## Ambiguity / Readiness Summary

- Depth used: Standard; no new user questions asked because sequence and requirement 006 artifacts answer the decision-bearing scope questions.
- Final ambiguity: 0.10
- Target ambiguity: 0.20
- Unresolved readiness gaps used to score ambiguity: exact module design, exact typed error names, and representative row selection belong to technical-design and plan-eng-review.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
  - Pressure pass completed: yes, via contract pressure against requirement 006 inventory and avoid conditions.
  - Closure audit passed: yes, no additional user question would change scope, safety, verification, or handoff route.
- Residual risk: high implementation breadth; coverage ledger required and downstream gates must prevent representative-only implementation from being mistaken for all-row completion.

## Assumptions

- Requirement 006 inventory remains authoritative until a validator-backed requirement-impact decision updates it.
- Requirement 008 owns the final full repeated named command matrix; requirement 007 owns implementation plus class-complete targeted proof.
- Existing no-owner direct-open behavior remains compatible unless a test proves it conflicts with the accepted live-owner contract.

## Recommended Next Step

- technical-design
- Reason: The requirement is architecture- and state-sensitive; module boundaries, owner dispatch contracts, typed errors, serialization policy, trust-boundary invariants, and test harness design must be specified before plan reviews and implementation.

## Planning Handoff

Before writing the final Codex plan or starting implementation, read this requirements document and treat it as the product requirements source of truth only when this document was created or updated in the current planning session, or when the user explicitly selected this exact document for reuse. If the implementation plan conflicts with these requirements, pause and reconcile the conflict before editing code.

Preserve the handoff bridge:

- Do not repeat already-satisfied requirement discovery by default.
- Do preserve intent, non-goals, decision boundaries, acceptance criteria, verification method, and residual risk.
- Do not let the next planning or implementation agent silently turn an assumption into a product decision.
- If residual risk is non-trivial, the next skill must either reduce it or carry it explicitly into its own plan/review artifact.

## Open Questions

None blocking for reviewer.
