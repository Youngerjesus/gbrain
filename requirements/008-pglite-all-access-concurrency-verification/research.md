# Technical Research: PGLite All-Access Concurrency Verification

Created: 2026-06-21
Status: Complete
Requirement source: requirements/008-pglite-all-access-concurrency-verification/requirements.md

## Research Decisions

### RD-001: Treat requirement 006 inventory and requirement 007 policy/evidence as mandatory preflight inputs

- Question: What artifacts define final matrix scope and expected outcomes?
- Decision: Requirement 008 must preflight-validate the requirement 006 inventory and consume requirement 007 implementation evidence before generating a matrix. The accepted row count and class counts are 468 rows: 217 `broker_success_read`, 223 `serialized_owner_mutation`, and 28 `typed_guard_fail_fast`.
- Rationale: The sequence split scope discovery, implementation, and final proof into separate slices. The inventory validator currently passes against the main worktree, and requirement 007 added code-native policy parity against every accepted row. Re-discovering scope in 008 would risk row loss and weaker representative-only proof.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Use requirement 006 inventory and requirement 007 evidence as preflight inputs | Preserves accepted scope and class decisions | Requires strict stale-artifact handling | Accepted |
  | Re-scan source files and create an independent 008 inventory | Could catch drift | Reopens already accepted requirement 006 scope and duplicates validator ownership | Rejected |
  | Use only requirement 007 representative coverage | Fast | Would violate requirement 008 all-row matrix proof | Rejected |
- Risk: Source fingerprints or policy parity can drift after 007; 008 must block instead of silently regenerating weaker expectations.
- Evidence:
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` returned `{ "ok": true, "errors": [], "warnings": [] }`.
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` records `later_sequence_standard.attempts: 3`, `raw_lock_timeout_allowed: false`, and the 217 / 223 / 28 class counts.
  - `test/pglite-owner-policy.test.ts` asserts runtime policy coverage for all 468 accepted inventory rows.
  - `requirements/007-pglite-broker-guard-implementation/evidence.md` records requirement 007 closeout evidence and explicitly leaves the full repeated all-row matrix to requirement 008.

### RD-002: Create a requirement-local successor matrix instead of reusing the requirement 006 minimal gauntlet as final proof

- Question: Can the existing requirement 006 gauntlet be treated as the final requirement 008 matrix?
- Decision: No. Requirement 008 should create a requirement-local successor matrix and result artifact, seeded from the accepted inventory but not limited to the existing minimal gauntlet modes. The successor matrix should name every accepted row and include row id, surface, command/tool, caller context, expected behavior class, execution mode, safety rationale, data preconditions, timeout budget, and expected final outcome.
- Rationale: The existing gauntlet in `test/pglite-all-access-inventory-gauntlet.serial.test.ts` was intentionally minimal and pre-implementation. It currently has only five runnable rows and expected-red behavior for `call:list_pages:local-cli`. Requirement 008 needs all-access final proof after requirement 007 implementation.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Reuse the five-row gauntlet as final evidence | Very fast | Representative-only overclaim; still includes historical expected-red semantics | Rejected |
  | Mutate requirement 006 inventory rows into final result rows | Keeps one file | Blurs accepted inventory with verification output and risks changing source-of-truth scope | Rejected |
  | Add requirement-local matrix/results artifacts for 008 | Clean handoff to production-readiness and preserves 006 as source of truth | Requires new validator/test work | Accepted |
- Risk: A successor matrix could drift from inventory unless it has parity validation for row count, row ids, class counts, and accepted behavior class.
- Evidence:
  - `test/pglite-all-access-inventory-gauntlet.serial.test.ts` hard-codes five runnable rows: `call:list_pages:local-cli`, `cli:query:operation-cli`, `cli:search:operation-cli`, `cli:sync:maintenance`, and `cli:think:operation-cli`.
  - A local inventory count check found `gauntlet` modes: 375 `fixture_only`, 88 `safe_non_execution`, and 5 `runnable`.
  - Requirement 008 AC2, AC8, and AC9 require full named matrix representation, structured result artifacts, and fail-closed behavior for missing rows.

### RD-003: Use explicit execution modes, with safety changing execution mode rather than scope

- Question: How should destructive, heavy, remote-sensitive, or data-precondition-heavy rows participate in the final matrix?
- Decision: The successor matrix should use explicit execution modes such as `live_concurrent`, `typed_guard_concurrent`, `fixture_concurrent`, `dry_run_concurrent`, and `safe_non_execution`. Every accepted row remains in the matrix; unsafe or externally dependent rows need row-specific safety rationale and replacement evidence rather than omission.
- Rationale: The user explicitly selected all PGLite-touching paths, including sync/embed/extract/doctor remediation/migrations/file upload. Requirement 007 accepted typed guards for lifecycle/heavy commands that cannot safely run inside the owner broker. Verification should preserve that decision: safety affects how a row is proven, not whether it is in scope.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Run every row as a real subprocess command | Strong boundary evidence | Can trigger destructive maintenance, external dependencies, self-update/network paths, or misleading fixture failures | Rejected |
  | Exclude destructive/heavy rows | Simple | Violates user scope and sequence outcome | Rejected |
  | Include every row with explicit safe execution mode and row-specific rationale | Preserves scope and safety | Requires stricter matrix schema and validator | Accepted |
- Risk: Overusing `safe_non_execution` can become representative-only proof. Technical design must require a concrete reason, accepted behavior class, and closure evidence for every non-live row.
- Evidence:
  - `requirements/007-pglite-broker-guard-implementation/decisions.md` records the accepted lifecycle/heavy/session typed-guard decision for commands such as `apply-migrations`, `autopilot`, `init`, `integrity`, `mounts`, `reinit-pglite`, `repair-jsonb`, `schema`, `watch`, `embed`, `extract`, and `sync`.
  - `src/core/pglite-owner-policy.ts` exposes behavior classes for CLI command, operation, and owner-startup targets.
  - `test/cli-pglite-operation-broker.test.ts` includes typed-guard coverage for maintenance and exclusive commands, plus local-only remote rejection coverage.

### RD-004: Validate final outcomes against accepted behavior class, not just absence of raw timeout

- Question: Is `raw_lock_timeout_observed: false` sufficient for requirement 008 pass/fail?
- Decision: No. The matrix validator must assert both zero raw PGLite lock/connect timeout and accepted behavior-class preservation. `broker_success_read` rows must not pass via typed guard; `serialized_owner_mutation` rows must not pass via guard-only downgrade; `typed_guard_fail_fast` rows must return stable typed guard evidence before direct PGLite open.
- Rationale: Requirement 007 explicitly forbids silently downgrading serialized mutation rows to guard-only behavior, and requirement 008 AC5 preserves the stronger behavior class. A raw-timeout-only pass would allow a broad typed guard to mask a behavior regression.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Assert only raw timeout is absent | Easy to implement | Allows behavior downgrades and false positives | Rejected |
  | Assert exact stdout for every row | Strong but brittle | Overfits command output and may make evidence noisy | Rejected |
  | Assert typed final outcome class plus required shape fields | Stable and requirement-aligned | Requires result schema and outcome classifier | Accepted |
- Risk: Some legitimate command failures may produce nonzero exits while still satisfying typed guard semantics; the validator must distinguish typed expected failure from raw or unclassified failure.
- Evidence:
  - Requirement 008 AC4 and AC5 separately require zero raw timeout and behavior-class preservation.
  - `scripts/validate-pglite-access-inventory.ts` already includes `classifyPgliteAccessOutput`, but it only recognizes a narrow typed-error list and historical current outcomes; requirement 008 needs a successor classifier for final outcomes.
  - `requirements/007-pglite-broker-guard-implementation/requirements.md` AC3 forbids downgrading `serialized_owner_mutation` rows to guard-only behavior without approved inventory impact.

### RD-005: Store machine-readable raw results and a summarized evidence report under requirement 008

- Question: What evidence shape lets implementation-brake, closeout, and requirement 009 verify the final matrix without rerunning discovery?
- Decision: Requirement 008 should produce at least three requirement-local artifacts: a matrix definition, raw per-attempt results, and a summarized validation report. Raw results should preserve per-attempt exit code, stdout/stderr evidence or hashes, structured error shape, owner/broker status when available, duration, timeout flag, cleanup state, and raw-timeout classification. The summary should include row counts, execution-mode counts, failure rows, commands run, and reproduction instructions.
- Rationale: Requirement 009 production-readiness needs durable evidence, not only test output. Row-level artifacts also prevent substring-only or prose-only acceptance.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Keep only Bun test output | Fast | Hard to audit row-level pass/fail or production-readiness handoff | Rejected |
  | Store only human-readable Markdown | Easy to read | Not machine-verifiable enough for fail-closed closure | Rejected |
  | Store matrix, raw results, and validation summary | Auditable and validator-friendly | More artifact work | Accepted |
- Risk: Capturing full stdout/stderr can expose paths or noisy data; technical design should prefer bounded tails plus hashes where full output is not needed.
- Evidence:
  - Requirement 008 AC8 requires machine-readable and human-readable evidence.
  - `scripts/coverage_ledger.py` supports closure only when structured evidence refs match obligation types; prose-only evidence is insufficient.
  - `test/pglite-all-access-inventory-gauntlet.serial.test.ts` already records per-attempt stdout, stderr, exit code, timeout, classification, and typed error code in a manifest-like shape.

### RD-006: Keep all verification isolated to temporary homes and fail closed on harness uncertainty

- Question: What environment and cleanup guarantees are required before final matrix results can be trusted?
- Decision: The final matrix runner must create temporary `GBRAIN_HOME` / PGLite database state, scrub inherited database-related environment, start or simulate the owner only in that temp context, and record owner lifecycle plus cleanup. Harness setup failures, cleanup failures, stale owner readiness, partial capture, or unclassified stderr must block closeout.
- Rationale: Prior evidence already saw real local PGLite lock timeout during dependency/postinstall flows, and both AGENTS.md and the requirement forbid touching the user's live brain. Harness uncertainty can otherwise look like row failure or false success.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Run matrix against the developer's current brain | Realistic | Unsafe and explicitly disallowed | Rejected |
  | Use only mocked owner/server fixtures | Safe and fast | Loses product-boundary CLI/MCP evidence for live-runnable rows | Rejected |
  | Use temporary real homes plus fixture/dry-run modes as needed | Safe with meaningful product-boundary evidence | Requires lifecycle and cleanup validation | Accepted |
- Risk: Full live subprocess coverage may be slow. Plan review should separate fast schema/unit feedback from a serial/live matrix command, but closeout cannot claim all-access proof without the required live evidence.
- Evidence:
  - Requirement 008 constraints forbid using or mutating the user's live brain.
  - Requirement 007 evidence records postinstall `gbrain apply-migrations --yes --non-interactive` hitting `GBrain: Timed out waiting for PGLite lock`, reinforcing temp-home-only verification.
  - Existing tests scrub `DATABASE_URL`, `GBRAIN_DATABASE_URL`, `GBRAIN_SOURCE`, and related env vars in subprocess helpers.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact successor matrix schema and artifact filenames | non_blocking | Research establishes required fields and artifact classes; technical-design owns final schema and validator interface. | technical-design |
| Exact row-level execution mode assignment for all 468 rows | non_blocking | The assignment must be generated/validated from accepted inventory and runtime policy; technical-design and implementation own the deterministic algorithm. | technical-design / implementation |
| Exact live matrix command cost/runtime placement | non_blocking | Plan-devex and plan-eng should choose fast versus serial/live commands without lowering evidence requirements. | plan-devex-review / plan-eng-review |

## Gate Self-Review

- All technical unknowns from the requirement were addressed or classified.
- Every decision has rationale and alternatives.
- Requirement Impact is absent.
- Every unresolved item is classified as non_blocking with a downstream owner.
- Evidence paths and source commands are recorded in `evidence.md`.
