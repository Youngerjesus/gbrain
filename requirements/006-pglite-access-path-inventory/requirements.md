---
requirement_id: 006-pglite-access-path-inventory
feature_name: PGLite Access Path Inventory
created_by: requirement-clarifier
created_at: 2026-06-20T09:16:00Z
updated_at: 2026-06-20T09:16:00Z
session_provenance: current-session
readiness_status: Ready
reviewer_status: SHIP
reviewer_fallback_status: none
---

# PGLite Access Path Inventory

## Readiness Status

Ready. The post-draft reviewer returned `SHIP`; research and technical-design may proceed. The user accepted the requirement shape: first slice creates an inventory plus minimal failing/reproducing concurrency gauntlet; later slices implement broker/guard behavior for every PGLite-touching path.

## User Story

As a gbrain operator or agent running a local PGLite-backed brain while `gbrain serve` is active, I need every CLI and MCP path that touches PGLite to have an explicit concurrency contract so I can inspect, repair, ingest, and diagnose without ambiguous raw lock/connect timeouts.

## Problem / Intent / Outcome

The previous PGLite concurrent-access sequence solved a deliberately limited contract for `query`, `search`, and `think`, while maintenance and many CLI-only diagnostic/admin paths stayed outside the owner broker. The observed lock problem therefore still exists for commands such as raw `call list_pages`, `sources`, `stats`, `config`, `doctor`, and potentially mutating or heavy maintenance paths.

This first slice must not jump straight into a partial patch. It must produce a complete inventory of every PGLite-touching command/tool/code path, classify each operation by safe concurrency behavior, and add the smallest honest regression gauntlet that reproduces the current lock/connect timeout or direct-open risk under a live owner.

## Acceptance Criteria

- AC1. Inventory every PGLite-touching CLI and MCP entry path.
  - Verification: a durable artifact in this requirement or its research/design output lists every discovered path, including command/tool name, caller type, implementation entry point, database-open site, operation kind, and whether it currently bypasses owner routing.
- AC2. Classify every inventoried path into one of the accepted behavior classes.
  - Verification: each inventory row is classified as `broker_success_read`, `serialized_owner_mutation`, `typed_guard_fail_fast`, `existing_direct_when_no_owner`, or `out_of_scope_with_user_approval`; no row may be left unclassified.
- AC3. Include all known problematic surfaces in the inventory.
  - Verification: the inventory explicitly covers `query`, `search`, `think`, `call` including `list_pages`/read operations, `sources`, `stats`, `config`, `doctor`, `sync`, `embed`, `extract`, migrations/upgrade/apply-migrations, file upload or filesystem-touching operations, and any MCP operation that opens PGLite.
- AC4. Preserve the trust boundary classification for each path.
  - Verification: every row records trusted local CLI versus remote-MCP exposure, whether `OperationContext.remote` applies, whether filesystem confinement is relevant, and whether the operation can mutate files, schema, settings, facts, sources, embeddings, or external state.
- AC5. Add a minimal reproducing concurrency gauntlet before implementation fixes.
  - Verification: tests or executable fixtures start or simulate a live local PGLite owner, invoke the named command matrix concurrently where feasible, and capture current failures as expected red evidence or explicit existing-pass evidence. The gauntlet must inspect exit code, structured error shape when available, stderr, and raw PGLite lock/connect timeout text.
- AC6. Define the sequence-level pass/fail standard for later slices.
  - Verification: the resulting artifact states that accepted implementation must produce zero raw PGLite lock/connect timeout failures across N repeated concurrent attempts for the named matrix, while preserving exit-code and typed-error expectations for operations classified as guard-fail-fast.
- AC7. Do not implement broad broker/guard behavior in this slice.
  - Verification: code changes, if any, are limited to inventory tooling, failing/reproducing tests, fixtures, or documentation of the accepted matrix. Product behavior changes belong to the next requirement unless a tiny instrumentation hook is required for the gauntlet and documented.
- AC8. Produce handoff-ready artifacts for the next requirement.
  - Verification: closeout identifies the accepted inventory artifact path, gauntlet test paths, red/green status by operation class, unresolved classification risks, and the recommended next requirement path `requirements/007-pglite-broker-guard-implementation/requirements.md`.

## Out Of Scope / Avoid

- Do not claim all PGLite paths are fixed in this slice.
- Do not silently reduce scope back to `query`, `search`, and `think`.
- Do not treat a command as safe merely because it is CLI-only.
- Do not route remote-MCP callers to local-only or filesystem-sensitive capabilities.
- Do not weaken, bypass, delete, or auto-force-remove live PGLite locks.
- Do not introduce a network-accessible broker, raw SQL forwarding, or public command syntax changes.
- Do not rely on substring scans as authoritative inventory proof when structured command registries, operation schemas, typed handlers, or import graphs can provide better evidence.
- Do not mark a path `out_of_scope_with_user_approval` without explicit user approval recorded in `decisions.md`.

## Success Metrics

- 100% of discovered PGLite-touching paths have an inventory row and behavior classification.
- The known observed failing surfaces are represented in the gauntlet.
- The gauntlet can distinguish raw PGLite lock/connect timeout from typed guard errors, brokered success, and expected direct-open behavior with no owner.
- The next implementation requirement can consume the inventory without re-discovering basic scope.

## Failure Condition

This requirement fails if any PGLite-opening command/tool path remains unclassified, if the gauntlet only covers already-solved `query`/`search`/`think`, if mutating/heavy maintenance paths are omitted because they are risky, or if the requirement allows raw PGLite lock/connect timeout to remain an accepted product-boundary result for an in-scope path.

## Edge Cases

- `gbrain serve` is active and a local CLI diagnostic command opens the same PGLite store directly.
- A raw `gbrain call` operation invokes a read-only handler such as `list_pages`.
- A raw `gbrain call` operation invokes a mutating or filesystem-sensitive handler.
- A remote MCP caller attempts an operation that local CLI may perform but remote callers must not.
- `sync`, `embed`, or `extract` encounter a live owner and must be classified separately from read/diagnostic operations.
- Migration or upgrade commands need exclusive schema ownership.
- `doctor --fix` or remediation plans may mutate settings, sources, files, or data.
- File upload and filesystem-touching operations must preserve remote confinement.
- No owner is active; existing direct-open behavior should remain possible where already valid.
- Owner is active but broker is busy, missing, stale, or unreachable.

## Constraints

- Scope is local PGLite-backed gbrain behavior.
- The sequence includes all PGLite-touching paths, including read, diagnostic, mutating, maintenance, migration, remediation, and file-touching paths.
- The accepted product boundary is zero raw PGLite lock/connect timeout for in-scope paths under a live owner; typed fail-fast is allowed only when recorded as the intended behavior class.
- Read/diagnostic paths should bias toward `broker_success_read` unless trust-boundary or correctness evidence proves otherwise.
- Mutating, schema-changing, file-touching, and heavy maintenance paths must be classified as `serialized_owner_mutation` or `typed_guard_fail_fast`; concurrency success is not assumed.
- Existing trusted-local versus remote-MCP security boundaries must be preserved exactly unless the user explicitly accepts a security design change.
- Public command syntax must remain unchanged unless the user explicitly approves otherwise.

## Decision Boundaries

### Agent may decide

- Exact inventory artifact format, as long as it is durable, reviewable, and structured enough to drive later implementation.
- Exact gauntlet implementation strategy and N value for repeated attempts, as long as N is justified and captures concurrent behavior rather than a single happy path.
- Whether a path is initially classified as `typed_guard_fail_fast` versus `serialized_owner_mutation`, if the rationale is evidence-backed and security-preserving.
- Whether research and technical-design artifacts are separate or combined by gate, as long as required gates record their status correctly.

### User must confirm

- Any path excluded from the sequence after being discovered as PGLite-touching.
- Any public command syntax change.
- Any network-facing broker behavior.
- Any weakening of `OperationContext.remote`, remote-MCP authorization, filesystem confinement, protected operation checks, or local-only restrictions.
- Any decision to make raw lock/connect timeout an accepted outcome for an in-scope path.
- Any irreversible migration, schema, data deletion, or lock deletion behavior.

## Verification Method

- Inspect CLI command registration, MCP operation registration, database-open helpers, PGLite adapter code, migration/upgrade paths, doctor/remediation flows, file upload paths, source management, and existing broker tests.
- Produce a structured inventory with path, caller, database access, trust boundary, side effects, existing owner behavior, and accepted behavior class.
- Add or update a minimal concurrency gauntlet that can run locally against temporary PGLite stores and identify raw PGLite lock/connect timeout text, exit code, stderr, and typed error envelopes.
- Run the new gauntlet in its expected pre-fix state and record which operations fail, pass, or require safe non-execution because they are destructive or irreversible.
- Run relevant existing PGLite broker tests to ensure the inventory work does not regress already-solved paths.

## Contract Preservation

- Requested behavior / artifact: inventory and executable concurrency reproduction for all PGLite-touching paths.
- Execution boundary: local PGLite owner process and local CLI/MCP callers; no network broker or external service.
- Required evidence level: structured inventory plus command/path gauntlet evidence, not prose-only analysis.
- Known capability gaps: broad broker/guard implementation is intentionally deferred to requirement 007.
- Allowed substitutions: destructive or irreversible operations may be represented by safe fixtures or dry-run paths if the classification and skipped live behavior are explicit.
- Disallowed substitutions: omitting risky paths, accepting raw lock timeout, or treating existing documentation as proof.
- Downgrade approval rule: any scope reduction requires explicit user confirmation recorded in `decisions.md`.

## Iteration Policy

### Continue when

- Work discovers additional PGLite access paths.
- The gauntlet exposes another raw lock/connect timeout or direct-open bypass.
- A classification needs stronger evidence before the next implementation slice.

### Stop when

- A proposed action would mutate real user data, delete locks, run irreversible migrations, or weaken security boundaries during inventory.
- The work requires changing product behavior beyond instrumentation or test scaffolding.
- A discovered path cannot be safely classified without user confirmation.

### Ask user when

- Excluding a PGLite-touching path.
- Changing public command syntax or security posture.
- Treating a dangerous operation as safe to execute concurrently instead of guard-fail-fast.
- Accepting lower verification than the named command matrix with zero raw lock/connect timeout.

### Checkpoint cadence

Update `progress.md`, `evidence.md`, and `decisions.md` after requirement review, research, technical design, plan reviews, gauntlet creation, implementation-brake, and closeout.

## Evidence Reviewed

- source_type: sequence
  location_or_reference: `goal-requirements/001-pglite-concurrent-access/sequence.md`
  extracted_fact: The prior sequence completed local PGLite concurrent access for the selected interactive operations and reserved production readiness for that limited contract.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/002-pglite-operation-forwarding/requirements.md`
  extracted_fact: Operation forwarding was scoped to `query`, free-text `search`, and `think`; real `sync`, `embed`, and `extract` execution was out of scope for that slice.
  confidence: high
- source_type: requirement
  location_or_reference: `requirements/003-pglite-priority-scheduler/requirements.md`
  extracted_fact: Maintenance behavior was intentionally treated as deferred fallback rather than true broker execution.
  confidence: high
- source_type: code
  location_or_reference: `src/core/pglite-operation-ipc.ts`
  extracted_fact: The current operation IPC type and valid operation set are limited to `query`, `search`, and `think`.
  confidence: high
- source_type: code
  location_or_reference: `src/cli.ts`
  extracted_fact: CLI brokered operations are limited to `query`, `search`, and `think`; many CLI-only commands bypass operation forwarding and can still encounter owner-lock behavior.
  confidence: high
- source_type: live_check
  location_or_reference: user-requested local check on 2026-06-20
  extracted_fact: `gbrain search` succeeded through the broker while `gbrain call list_pages` under an active owner returned a connect timeout, proving the remaining limitation is observable.
  confidence: high
- source_type: user_decision
  location_or_reference: current conversation, 2026-06-20
  extracted_fact: User selected a sequence where the first slice does both inventory and minimal failure reproduction, the total scope includes every PGLite-touching path including mutating/heavy maintenance, and the success standard is zero lock/connect timeout across a named command matrix with exit code, error shape, and stderr evidence.
  confidence: high

## Artifact Handoff Contract

- producer role: requirement-clarifier
- consumer role: goal-requirement-orchestrator, research, technical-design, plan reviewers, implementation, implementation-brake, closeout
- artifact path or path-producing rule: `requirements/006-pglite-access-path-inventory/requirements.md`
- artifact purpose: Source-of-truth requirements for the first slice of the all-access PGLite concurrency sequence.
- failure classification: Missing, stale, reviewer-unaccepted, or contradicted requirements block downstream gates.
- verification method: Post-draft reviewer returns structured `SHIP` or material findings are revised and rerun.

### Inventory Artifact

- producer role: research and technical-design gates for requirement 006
- consumer role: implementation planner and requirement 007 requirement-clarifier
- artifact path or path-producing rule: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` unless technical-design records a better structured path
- artifact purpose: Authoritative operation-by-operation inventory of PGLite access paths, trust boundary, side effects, current owner behavior, and accepted behavior class.
- failure classification: Missing, unstructured, stale, or containing unclassified rows blocks requirement 007 and implementation planning.
- verification method: coverage-ledger rows `inventory.cli_entrypoints`, `inventory.mcp_operations`, `inventory.maintenance_mutation_paths`, and `inventory.behavior_classification` must close with schema validation and evidence that all known registries/open sites were inspected and classified.

### Concurrency Gauntlet Artifacts

- producer role: implementation for requirement 006
- consumer role: implementation-brake, closeout, and requirement 007 planning
- artifact path or path-producing rule: test files and any fixture outputs recorded in `requirements/006-pglite-access-path-inventory/evidence.md` and `coverage-ledger.yml`
- artifact purpose: Minimal executable proof of current raw lock/connect timeout or direct-open risk, plus existing-pass evidence for already-safe paths.
- failure classification: Missing named-matrix coverage, missing stderr/exit-code/error-shape capture, or missing raw-timeout distinction blocks closeout.
- verification method: coverage-ledger rows `gauntlet.named_matrix`, `gauntlet.timeout_detection`, and `handoff.requirement_007` must close before `[SHIP]`.

## Ambiguity / Readiness Summary

- Depth used: Standard with Grill Me batch pressure pass
- Final ambiguity: 0.14
- Target ambiguity: 0.20
- Unresolved readiness gaps used to score ambiguity: Exact inventory artifact schema, exact N value for repeated attempts, and final classification of each operation require research/design evidence.
- Mandatory gates:
  - Non-goals explicit: yes
  - Decision boundaries explicit: yes
  - Pressure pass performed: yes, via Grill Me batch subagents
- Closure audit passed: yes
- Residual risk: The full list of PGLite-touching paths is not known until this requirement executes; the requirement handles that by making inventory completeness the primary acceptance criterion.

## Recommended Next Step

- research
- Reason: The first slice must discover code paths, command registries, operation handlers, and existing tests before technical design and planning.

## Open Questions

None blocking for reviewer.
