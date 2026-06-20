# Requirement Decisions

## Decisions

### 2026-06-21 02:39 KST - Requirement 008 is verification-only by default

- Decision: Requirement 008 must prove the final repeated named command matrix and must not implement new broker/guard behavior unless matrix evidence exposes a concrete requirement-impact failure.
- Rationale: Requirement 007 owns implementation; requirement 008 owns all-row repeated proof. Mixing those scopes would let verification bugs or product bugs hide behind broad implementation churn.
- Applies to: requirement, planning, implementation, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Requirement 006 and 007 artifacts are authoritative inputs

- Decision: Use `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` and requirement 007 closeout artifacts as the source of truth for matrix scope and expected behavior classes.
- Rationale: The sequence intentionally separated inventory, implementation, and final verification. Rediscovery would risk row loss or weaker representative-only evidence.
- Applies to: requirement, technical-design, matrix generation, implementation-brake
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - N=3 concurrent attempts is the accepted standard

- Decision: The named command matrix must run N=3 concurrent attempts for live-runnable rows and record row-level exit code, stdout, stderr, structured error shape, and raw-timeout classification.
- Rationale: The user selected the named matrix standard and requirement 006 recorded `attempts: 3` with `raw_lock_timeout_allowed: false`.
- Applies to: requirement, technical-design, verification, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Heavy/destructive surfaces stay in scope through safe evidence modes

- Decision: Sync, embed, extract, doctor remediation, migrations, file upload, and heavy/lifecycle maintenance surfaces remain in scope, but destructive or owner-blocking rows may be verified through safe fixtures, dry-run/non-execution evidence, or typed-guard proof when that matches the accepted inventory class.
- Rationale: The user explicitly chose all PGLite-touching paths; safety concerns change execution mode, not scope.
- Applies to: requirement, technical-design, scenario-brake, verification
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Coverage ledger required

- Decision: Requirement 008 requires `coverage-decision.yml` and `coverage-ledger.yml`.
- Rationale: The slice covers hundreds of rows, many acceptance criteria, multiple CLI/MCP surfaces, trust-boundary variants, destructive/heavy command safety, and machine-readable evidence artifacts.
- Applies to: requirement acceptance, planning, implementation, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Requirement 008 uses a successor matrix, not the requirement 006 minimal gauntlet

- Decision: Create a requirement-local successor matrix and result artifact for requirement 008, seeded from the accepted inventory but not limited to the existing five-row minimal gauntlet.
- Rationale: Requirement 006 intentionally created a minimal pre-implementation gauntlet; requirement 008 owns final all-access verification across all accepted rows.
- Applies to: research, technical-design, implementation, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Execution safety changes row mode, not row scope

- Decision: Every accepted row remains represented in the final matrix. Destructive, heavy, externally dependent, or filesystem-sensitive rows may use explicit safe execution modes with row-specific rationale and validator-visible evidence.
- Rationale: The user selected all PGLite-touching paths, including sync/embed/extract/doctor remediation/migrations/file upload; safety concerns cannot erase scope.
- Applies to: research, technical-design, scenario-brake, implementation
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Final pass requires behavior-class preservation

- Decision: Requirement 008 validation must check zero raw timeout and accepted behavior-class preservation; raw-timeout absence alone is insufficient.
- Rationale: A broad typed guard could remove lock text while downgrading `broker_success_read` or `serialized_owner_mutation` rows, violating requirement 007 and requirement 008 AC5.
- Applies to: research, technical-design, matrix validator, implementation-brake
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Requirement 008 architecture artifact not required

- Decision: Do not create `architecture.md` for requirement 008.
- Rationale: Requirement 008 adds requirement-local scripts, tests, matrix/result artifacts, and coverage evidence. It does not change the runtime broker/guard architecture already owned by requirement 007.
- Applies to: technical-design, planning
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Matrix/result artifacts are requirement-local

- Decision: Store the successor matrix, raw results, validation summary, and evidence summary under `requirements/008-pglite-all-access-concurrency-verification/`.
- Rationale: Requirement 009 production-readiness needs durable evidence paths, and product runtime must not import requirement artifacts.
- Applies to: technical-design, implementation, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Full-loop artifact writer is a single requirement-local script

- Decision: Use `scripts/run-pglite-all-access-matrix.ts` as the single owner for writing `pglite-all-access-results.jsonl`, `pglite-all-access-validation.json`, `pglite-all-access-summary.md`, and `pglite-all-access-run-manifest.json`.
- Rationale: Plan Eng Review required one full-loop artifact writer so tests and closeout cannot drift into competing evidence pipelines.
- Applies to: implementation, verification, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 02:39 KST - Requirement 008 did not change runtime broker/guard behavior

- Decision: Keep implementation scoped to matrix generation, result validation, full-loop evidence writing, tests, and requirement-local artifacts. No runtime CLI/MCP broker or guard source was changed in requirement 008.
- Rationale: Requirement 007 owns product behavior. Requirement 008 found no product-behavior failure requiring requirement-impact repair.
- Applies to: implementation, implementation-brake, closeout, production-readiness handoff
- Status: accepted
- Requirement Impact: none
