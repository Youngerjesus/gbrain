---
requirement_id: 008-pglite-all-access-concurrency-verification
feature_name: PGLite All-Access Concurrency Verification
created_by: requirement-clarifier
created_at: 2026-06-20T17:39:31Z
updated_at: 2026-06-20T17:39:31Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite All-Access Concurrency Verification

## Readiness Status

Ready. The requirement-clarifier post-draft reviewer returned structured `SHIP` with no findings, and coverage-ledger readiness/schema validation passed. The scope is explicit: prove the accepted all-access PGLite behavior matrix under a live local owner; do not add or weaken runtime behavior unless verification finds a requirement-impact failure.

## User Story

As a local gbrain operator or agent using a PGLite-backed brain while `gbrain serve` owns the database, I need a repeatable all-access verification matrix that proves every accepted PGLite-touching path returns brokered success, serialized owner execution, or typed guard fail-fast behavior without exposing raw PGLite lock/connect timeout text.

## Problem / Intent / Outcome

Requirement 006 produced the authoritative PGLite access-path inventory and minimal reproduction contract. Requirement 007 implemented broker routing, owner serialization, and typed guards for the accepted behavior classes. This requirement must close the verification gap left intentionally open by requirement 007: the final repeated named command matrix.

The intended outcome is a structured, reproducible verification artifact showing that every in-scope named command/operation row has zero raw PGLite lock/connect timeout failures across repeated concurrent attempts under a live local owner, while preserving exit code, stdout, stderr, and structured error-shape evidence for each row.

## Acceptance Criteria

- AC1. Consume requirement 006 and 007 artifacts as the verification source of truth.
  - Verification: before executing the matrix, validate `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`, read requirement 007 implementation evidence, and record source fingerprints, accepted class counts, and any inventory-impact drift. Verification must not rediscover scope ad hoc or drop rows silently.
- AC2. Define a named command matrix covering every accepted PGLite-touching path.
  - Verification: the matrix is generated or validated from the accepted inventory and includes row id, surface, command/tool name, caller context, expected behavior class, execution safety mode, data preconditions, timeout budget, and expected product-boundary result.
- AC3. Run repeated concurrent attempts against each live-runnable matrix row.
  - Verification: for each row marked live-runnable by the accepted inventory, run N=3 concurrent attempts under a healthy live local owner in a temporary PGLite home/source, capturing per-attempt exit code, stdout, stderr, duration, structured error fields, owner route/status fields when available, and cleanup status.
- AC4. Prove zero raw PGLite lock/connect timeout at the product boundary.
  - Verification: the result classifier asserts `raw_lock_timeout_observed: false` for every attempt and fails on raw PGLite lock/connect timeout text, connect-timeout exceptions, second-process direct-open lock failure, or untyped timeout leakage. Acceptable final outcomes are only `broker_success_read`, `serialized_owner_mutation`, or `typed_guard_fail_fast`.
- AC5. Preserve the stronger behavior class for each row.
  - Verification: `broker_success_read` rows must not pass merely by typed guard; `serialized_owner_mutation` rows must not pass merely by guard-only downgrade; `typed_guard_fail_fast` rows must fail fast before direct PGLite open with stable typed error/exit-shape evidence. Any class mismatch is requirement-impact and blocks closeout unless the user explicitly approves an inventory update.
- AC6. Include the explicitly scoped surfaces: sync, embed, extract, doctor remediation, migrations, and file upload.
  - Verification: the matrix has named rows or explicitly safe non-execution rows for these surfaces, with row-specific evidence explaining whether the row was live-executed, dry-run/fixture-executed, or typed-guard verified. No surface may be excluded because it is destructive, heavy, or filesystem-sensitive; unsafe execution must be represented as typed guard or safe fixture evidence.
- AC7. Preserve trusted-local and remote-MCP trust boundaries during verification.
  - Verification: local CLI, local MCP, remote MCP, protected operation, local-only operation, and filesystem-sensitive `file_upload` rows keep the authority and confinement behavior implemented in requirement 007. The matrix must not use verification shortcuts that broaden remote access, bypass `OperationContext.remote`, or run against the user's live brain.
- AC8. Produce handoff-ready structured evidence.
  - Verification: write machine-readable matrix results and a human-readable evidence summary under this requirement directory. Evidence must include exit code, stdout/stderr excerpts or hashes, structured error shape, raw-timeout classifier output, pass/fail reason, retry/attempt count, owner lifecycle notes, environment hygiene, and command used to reproduce each matrix run.
- AC9. Fail closed on incomplete or ambiguous verification.
  - Verification: missing rows, stale inventory fingerprints, unclassified stderr, cleanup failure, owner startup uncertainty, partial result capture, unsupported command safety mode, or row-level result mismatch produces a row-specific failure and blocks closeout; it must not be summarized as pass.
- AC10. Hand off a bounded readiness verdict to production-readiness.
  - Verification: closeout records the exact commands run, matrix artifact paths, coverage-ledger closure, unresolved risks, any approved deferrals, and the next requirement path `requirements/009-pglite-all-access-concurrency-production-readiness/requirements.md`.

## Out of Scope / Avoid

- Do not implement new broker/guard behavior unless matrix execution reveals a concrete requirement-impact bug that must be routed through the active goal workflow.
- Do not narrow the matrix to representative rows, prior `query`/`search`/`think` coverage, or only fast read paths.
- Do not accept raw PGLite lock/connect timeout text as an allowed product-boundary result for any in-scope row.
- Do not delete, force-remove, or auto-clean live PGLite locks as a verification shortcut.
- Do not run destructive migrations, resets, remediation, or filesystem-sensitive operations against the user's real brain.
- Do not broaden remote-MCP authority, weaken filesystem confinement, bypass protected operation checks, or change public CLI/MCP syntax.
- Do not treat prose summaries, substring-only scans, or reviewer praise as authoritative pass/fail evidence.
- Do not claim production readiness; requirement 009 owns the sequence-level readiness verdict.

## Success Metrics

- 100% of accepted inventory rows are represented in the named command matrix or have a row-specific, validator-approved non-execution reason.
- N=3 repeated concurrent attempts complete for every live-runnable row.
- 0 attempts expose raw PGLite lock/connect timeout or untyped connect-timeout failure.
- 100% of rows preserve their accepted behavior class or record an explicit user-approved inventory impact.
- Structured matrix results, evidence summary, and coverage-ledger closure validation pass.

## Failure Condition

This requirement fails if any accepted row is missing, if any live-runnable attempt emits raw PGLite lock/connect timeout text, if a row passes by weakening its accepted behavior class, if trust-boundary behavior is broadened for verification convenience, if evidence omits exit code/stderr/error-shape capture, or if the final report claims all-access proof from representative-only coverage.

## Edge Cases

- `gbrain call list_pages {}` under a healthy live owner.
- Local read/diagnostic direct CLI commands and stdio/HTTP MCP tool calls under a healthy live owner.
- Local mutating operations that must serialize through the owner.
- `sync`, `embed`, `extract`, doctor remediation, `apply-migrations`, upgrade/post-upgrade paths, and schema/repair/reset commands under live-owner conditions.
- `file_upload` for trusted local CLI/MCP callers and rejected remote callers.
- Protected and local-only operations under remote MCP.
- Owner startup, duplicate owner startup, owner busy/broker timeout, owner unreachable, stale/dead recoverable lock, corrupt/unknown lock, missing socket, wrong owner identity, and cleanup after matrix failure.
- Empty temporary brain/source, initialized but empty source, migration-pending temp home, and data-precondition rows that need fixtures.

## Constraints

- Scope is local PGLite-backed gbrain behavior across CLI and MCP surfaces.
- The accepted inventory path is `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.
- The current accepted inventory count is 468 rows: 217 `broker_success_read`, 223 `serialized_owner_mutation`, and 28 `typed_guard_fail_fast`.
- The repeated matrix standard is N=3 concurrent attempts with `raw_lock_timeout_allowed: false`.
- Tests and matrix runs must use temporary homes/backends and must not depend on or mutate the user's live brain.
- Public CLI command names, MCP tool names, request schemas, JSON envelopes, and security posture remain stable unless the user explicitly approves a change.
- Requirement artifacts and validators may guide tests, but product runtime must not depend on requirement YAML.

## Contract Preservation

- Requested behavior / artifact: final all-access repeated concurrency verification matrix and evidence package for every accepted PGLite-touching row.
- Execution boundary: local owner process, local CLI, local stdio/HTTP MCP surfaces, temporary PGLite homes/sources, and requirement-local artifacts only.
- Required evidence level: structured matrix artifact, row-level exit code/stdout/stderr/error-shape evidence, raw-timeout classifier output, inventory validation, coverage-ledger closure, and closeout summary.
- Known capability gaps: production-readiness, documentation/release verdict, and launch handoff remain reserved for requirement 009.
- Allowed substitutions: unsafe destructive/heavy rows may use safe fixture, dry-run, or typed-guard verification only when the accepted row classification and evidence explicitly justify the execution mode.
- Disallowed substitutions: representative-only matrix, guard-only downgrade for serialized mutations, raw timeout acceptance, remote authority broadening, real-brain execution, or prose-only evidence.
- Downgrade approval rule: any reduction in row coverage, behavior class, evidence level, security posture, public compatibility, or matrix repeat count requires explicit user approval recorded in `decisions.md`.

## Iteration Policy

### Continue when

- Matrix generation finds stale inventory fingerprints or missing rows that can be reconciled through a recorded requirement-impact decision.
- A live-runnable row emits raw lock/connect timeout and needs bug routing.
- Evidence capture is incomplete but can be repaired without changing accepted behavior.
- A reviewer finds overclaiming, row loss, or trust-boundary drift.

### Stop when

- Verification would require mutating the user's live brain or running destructive maintenance outside a temp fixture.
- A row cannot be safely verified under its accepted behavior class without changing public behavior, trust boundaries, or sequence scope.
- Matrix results contradict requirement 007 implementation claims in a way that requires product behavior changes.

### Ask user when

- Excluding any accepted PGLite-touching row from the matrix.
- Lowering N below 3 or accepting partial attempts.
- Reclassifying a row to a weaker behavior class.
- Running destructive/heavy maintenance against non-temporary data.
- Changing public CLI/MCP syntax, security posture, or accepted sequence scope.

### Checkpoint cadence

Update `progress.md`, `evidence.md`, `decisions.md`, coverage artifacts, and sequence progress after requirement review, research/technical-design decisions, plan reviews, matrix generation, first matrix execution, failed row triage, final matrix validation, implementation-brake, and closeout.

## Decision Boundaries

### Agent may decide

- Exact matrix artifact schema and file names under this requirement directory.
- Exact representative temp fixtures and safe command arguments, as long as every accepted row is represented and live-runnable rows are executed N=3.
- Timeout budgets and cleanup mechanics that keep the matrix bounded and deterministic.
- Whether a row needs safe fixture, dry-run, or typed-guard verification based on accepted inventory safety metadata.
- Internal validator/test helper design for matrix generation, result classification, and evidence summarization.

### User must confirm

- Any row exclusion, weaker behavior class, lower repeat count, or evidence downgrade.
- Any public CLI/MCP syntax, request/response schema, or documented behavior change.
- Any remote-MCP authority expansion, filesystem confinement relaxation, protected-operation bypass, or network-facing owner broker change.
- Any irreversible migration/data deletion/lock deletion behavior used as part of verification.
- Any production-readiness verdict before requirement 009.

## Verification Method

- Validate the accepted inventory with `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json`.
- Read requirement 007 evidence and representative coverage to identify implemented behavior classes, owner-state expectations, trust-boundary expectations, and known verification-only residual risk.
- Generate or validate the named command matrix from the accepted inventory.
- Start a healthy local `gbrain serve` owner in a temporary home/source and run the matrix with N=3 concurrent attempts for live-runnable rows.
- Capture row-level exit code, stdout, stderr, structured error shape, owner/broker status when available, duration, cleanup result, and raw-timeout classification.
- Run negative/fixture rows for destructive, heavy, remote-only, protected, and filesystem-sensitive surfaces without touching the user's live brain.
- Validate the machine-readable result artifact and fail on missing rows, class mismatches, raw timeout, or unclassified outcomes.
- Run coverage-ledger closure before closeout.

## Evidence Reviewed

- source_type: sequence
  location_or_reference: `goal-requirements/002-pglite-all-access-concurrency/sequence.md`
  extracted_fact: Requirement 008 must prove the named command matrix has zero raw PGLite lock/connect timeout failures across repeated concurrent attempts, with exit code, stderr, and error-shape evidence.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/006-pglite-access-path-inventory/requirements.md`
  extracted_fact: Requirement 006 owns the access-path inventory and later-sequence standard of N=3 attempts with raw lock timeout disallowed.
  confidence: high
- source_type: artifact
  location_or_reference: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
  extracted_fact: The accepted inventory contains 468 rows with 217 `broker_success_read`, 223 `serialized_owner_mutation`, 28 `typed_guard_fail_fast`, and `raw_lock_timeout_allowed: false`.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/007-pglite-broker-guard-implementation/requirements.md`
  extracted_fact: Requirement 007 intentionally provides class-complete targeted implementation proof while reserving full repeated all-row matrix proof for requirement 008.
  confidence: high
- source_type: decision
  location_or_reference: `requirements/007-pglite-broker-guard-implementation/decisions.md`
  extracted_fact: Lifecycle, daemon, reset, and heavy local commands that cannot safely run inside the owner broker are accepted as `typed_guard_fail_fast`, and requirement 008 owns the final N=3 all-row named matrix.
  confidence: high
- source_type: evidence
  location_or_reference: `requirements/007-pglite-broker-guard-implementation/evidence.md`
  extracted_fact: Requirement 007 closeout completed class-complete targeted evidence, inventory validator pass, targeted broker/guard tests, and implementation-brake `[SHIP]`, leaving only final all-row repeated matrix proof.
  confidence: high
- source_type: user_decision
  location_or_reference: current sequence discussion
  extracted_fact: The user selected coverage of all PGLite-touching paths, including sync/embed/extract/doctor remediation/migrations/file upload, and requested named command matrix evidence across concurrent attempts with exit code/error shape/stderr.
  confidence: high

## Artifact Handoff Contract

### Inventory Input Contract

- producer role: requirement 006 closeout
- consumer role: requirement 008 matrix generator, validator, implementation-brake, closeout
- artifact path or path-producing rule: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- artifact purpose: authoritative row-level list of PGLite-touching surfaces, behavior classes, safety modes, and later-sequence verification standard.
- failure classification: missing artifact, validator failure, stale source fingerprint, row-count drift, unapproved class drift, or missing required surface blocks matrix generation.
- verification method: inventory validator plus matrix row-count/class-count parity check.

### Implementation Evidence Input Contract

- producer role: requirement 007 closeout
- consumer role: requirement 008 matrix generator, validator, implementation-brake, closeout
- artifact path or path-producing rule: `requirements/007-pglite-broker-guard-implementation/evidence.md`, `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`, and requirement 007 coverage ledger.
- artifact purpose: identify implemented behavior classes, typed errors, trust-boundary expectations, owner-state expectations, and residual verification-only risks.
- failure classification: missing closeout evidence, open implementation-brake finding, missing representative coverage, or unresolved implementation risk blocks matrix execution.
- verification method: preflight read and structured evidence checklist recorded in this requirement's evidence.

### Matrix Result Contract

- producer role: requirement 008 implementation/verification runner
- consumer role: implementation-brake, closeout, requirement 009 production-readiness
- artifact path or path-producing rule: requirement-local matrix definition, raw result artifact, and summarized evidence artifact under `requirements/008-pglite-all-access-concurrency-verification/`.
- artifact purpose: prove final all-access repeated concurrency behavior and hand off production-readiness evidence.
- failure classification: missing row, failed attempt, raw timeout observed, class mismatch, trust-boundary drift, incomplete evidence capture, or invalid artifact schema blocks closeout.
- verification method: structured validator, targeted tests/scripts, coverage-ledger closure, and implementation-brake `[SHIP]`.

## Ambiguity / Readiness Summary

- Not applicable: deep-interview gate not used.
- Depth used: Standard; no new user questions asked because sequence, requirement 006, requirement 007, and current user decisions answer the decision-bearing scope questions.
- Final ambiguity: 0.10
- Target ambiguity: 0.20
- Unresolved readiness gaps used to score ambiguity:
  - Exact matrix artifact schema and runner command are intentionally deferred to technical-design.
  - Exact destructive/heavy-row fixture mode is intentionally deferred to technical-design and plan review, constrained by no real-brain execution.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
  - Pressure pass completed: yes; the draft preserves all rows and forbids representative-only proof, lower repeat count, behavior downgrade, real-brain destructive execution, and remote authority broadening.
  - Closure audit passed: yes; another user question would not materially change requirement scope after the user's accepted choices.
- Residual risk: Some rows may require safe non-execution or fixture verification to avoid destructive side effects; those choices must be row-specific and validator-visible before closeout.

## Assumptions

- Requirement 007 fast-forward merge represents the current implementation baseline for requirement 008.
- The accepted behavior-class counts remain 217 / 223 / 28 unless a validator-backed requirement-impact decision updates the inventory.
- The runtime can run enough temporary-home fixture evidence locally to avoid the user's live brain.

## Recommended Next Step

- technical-design
- Reason: the requirement is a verification harness and evidence-contract slice; the next hard decision is HOW to generate, execute, classify, and validate the all-row named matrix without unsafe real-brain side effects.

## Planning Handoff

Before writing the final Codex plan or starting implementation, read this requirements document and treat it as the product requirements source of truth only when this document was created or updated in the current planning session, or when the user explicitly selected this exact document for reuse. If the implementation plan conflicts with these requirements, pause and reconcile the conflict before editing code.

Preserve the handoff bridge:

- Do not repeat already-satisfied requirement discovery by default.
- Do preserve intent, non-goals, decision boundaries, acceptance criteria, verification method, artifact handoff contracts, and residual risk.
- Do not let the next planning or implementation agent silently turn an assumption into a product decision.
- If residual risk is non-trivial, the next skill must either reduce it or carry it explicitly into its own plan/review artifact.

## Open Questions

- None blocking for requirement acceptance after post-draft reviewer `SHIP`; technical-design owns the exact matrix schema, runner command, and per-row safety execution mode.
