# Technical Design: PGLite Access Path Inventory

Created: 2026-06-20
Status: Complete
Requirement source: requirements/006-pglite-access-path-inventory/requirements.md
Research source: requirements/006-pglite-access-path-inventory/research.md
Architecture artifact: Not required - this slice adds requirement-local inventory/test artifacts and does not change runtime broker architecture or durable product boundaries.

## Requirement Coverage

| Requirement / Acceptance Criterion | Design mapping |
| --- | --- |
| AC1. Inventory every PGLite-touching CLI and MCP entry path | Produce `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` with one row per entry path and transport/caller variant. Populate from `operations.ts` AST extraction, `src/cli.ts` CLI-only command dispatch, MCP transport filters, and PGLite open-site evidence. |
| AC2. Classify every inventoried path | Inventory schema requires `accepted_behavior_class` with enum `broker_success_read`, `serialized_owner_mutation`, `typed_guard_fail_fast`, `existing_direct_when_no_owner`, or `out_of_scope_with_user_approval`; validator fails on missing/unknown values. |
| AC3. Include known problematic surfaces | Seed required matrix groups for `query`, `search`, `think`, `call:list_pages`, `sources`, `stats`, `config`, `doctor`, `sync`, `embed`, `extract`, migrations/apply-migrations/upgrade, file upload/files, and MCP operations. Validator checks required surface ids are present. |
| AC4. Preserve trust boundary classification | Each row records `caller_surface`, `transport`, `remote_context`, `operation_context_remote`, `mcp_exposed`, `local_only`, `filesystem_confinement`, and `side_effects`. |
| AC5. Add minimal reproducing concurrency gauntlet | Add subprocess test coverage that creates a temporary PGLite home, starts a live `gbrain serve` owner, runs a named command matrix with N=3 concurrent attempts for safe runnable rows, and records exit code/stdout/stderr/parsed error shape/raw timeout detection. |
| AC6. Define later pass/fail standard | Inventory and gauntlet fixture metadata include the later sequence standard: zero raw PGLite lock/connect timeout across the named matrix; typed guard failures remain allowed only for rows classified `typed_guard_fail_fast`. |
| AC7. Do not implement broad broker/guard behavior | Product behavior changes are out of scope. Edits are limited to requirement artifact, validator/test harness, and expected-red reproducing tests. No new operation is added to `BROKERED_OPERATIONS` in this slice. |
| AC8. Handoff-ready artifacts | Closeout records inventory path, validator command, gauntlet test path(s), red/pass status, and unresolved risks in `evidence.md` and coverage ledger rows for requirement 007. |

## Module Design

- Module boundaries:
  - Requirement artifact: `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.
  - Validator/test helper: a focused repo-local validator, preferably `scripts/validate-pglite-access-inventory.ts`, using TypeScript AST and existing `js-yaml` dependency.
  - Gauntlet test: a serial subprocess test near the existing PGLite owner test, preferably `test/pglite-all-access-inventory-gauntlet.serial.test.ts`, sharing patterns from `test/pglite-concurrent-access.serial.test.ts`.
  - Requirement state: `progress.md`, `evidence.md`, `decisions.md`, and `coverage-ledger.yml` remain the gate bookkeeping source.
- Public interfaces:
  - Inventory YAML top-level fields:
    - `requirement_id`
    - `schema_version`
    - `generated_from`
    - `later_sequence_standard`
    - `required_surface_ids`
    - `rows`
  - Row fields:
    - `id`
    - `command_or_operation`
    - `subcommand_or_mode`
    - `argument_profile`
    - `entry_kind`
    - `caller_surface`
    - `transport`
    - `implementation_entrypoint`
    - `database_open_site`
    - `current_owner_behavior`
    - `no_owner_baseline`
    - `accepted_behavior_class`
    - `scope`
    - `local_only`
    - `mcp_exposed`
    - `operation_context_remote`
    - `filesystem_confinement`
    - `side_effects`
    - `data_preconditions`
    - `gauntlet`
    - `evidence_refs`
  - Validator interface:
    - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
    - Exit 0 only when schema, pinned enums, required surfaces, source-derived candidate sets, and source evidence references are coherent.
    - Exit nonzero with structured JSON/text diagnostics when rows are missing, unclassified, duplicate, enum-invalid, trust-boundary-incomplete, or present in code-derived PGLite candidate sets but absent from YAML.
    - Candidate extraction must compare YAML rows against code-derived operation/command sets, not only a hand-curated `required_surface_ids` list.
    - Source extraction fails closed when registry or dispatcher syntax is unsupported, partially parsed, dynamically computed, or stale relative to the recorded source fingerprint.
    - Validator rejects coarse command-group rows when subcommand, flag/mode, transport, trust boundary, side effect, DB-open timing, or gauntlet safety differs.
- Dependency direction:
  - Tests and scripts may parse source files and requirement artifacts.
  - Product source must not import requirement artifacts or test validators.
  - Validator may depend on `typescript` and `js-yaml`; product runtime must not gain new dependencies.
- Data flow:
  - AST/source inspection identifies operation, command, subcommand/mode, MCP transport, owner-startup, and PGLite open-site candidates.
  - Inventory YAML records classification and handoff fields.
  - Validator reads YAML plus source files and checks required structural coverage and code-derived candidate coverage.
  - Gauntlet uses inventory row ids as the canonical named matrix input and captures actual CLI subprocess results.

## Interactions

- Main flow:
  - Build/update inventory rows from source evidence.
  - Run inventory validator and fix missing schema/coverage rows.
  - Add strict expected-red gauntlet cases under a temporary `GBRAIN_HOME` with row-specific seeded PGLite data preconditions.
  - Scrub inherited environment, prove the harness is using a temporary local PGLite backend, and fail setup separately from row outcomes when backend/home/permission preconditions are wrong.
  - Start owner `gbrain serve`, wait for operation socket/lock/readiness, run safe matrix rows concurrently, and classify results.
  - Run a dedicated split-brain/stale-proxy fixture for lock-held but broker-socket-missing/stale states where safe to construct in a temporary home.
  - Record a gauntlet result manifest that proves every runnable row produced exactly N attempt records and every safe-non-execution row has a concrete reason plus replacement expectation.
  - Record teardown status and cleanup requirements after success, timeout, or interruption; a failed cleanup is a harness failure, not row evidence.
  - Record actual evidence and ledger row status.
- Alternate flows:
  - If a command is destructive, irreversible, external-service-dependent, or file-deleting, the gauntlet row uses `safe_non_execution`, `--dry-run`, or fixture-only invocation and records why; safe non-execution requires a concrete mutation risk and a requirement-007 replacement expectation.
  - If a command already passes through the owner broker, it is an `existing_pass` control row.
  - If a command has no live owner path because it is pure filesystem/config, it remains in discovery notes but is not represented as PGLite-touching unless evidence proves DB access.
  - If `gbrain serve` or `serve --http` startup paths touch PGLite, represent them as owner-startup rows or record explicit exclusion evidence; duplicate-owner-start under a live lock must be classified separately.
  - If no-owner direct-open behavior is valid, record it as `no_owner_baseline`; it cannot by itself close live-owner product-boundary evidence.
  - If a safe runnable MCP path differs by stdio/HTTP transport or trusted local `gbrain call`, invoke representative transport rows or record row-specific non-runnable rationale.
- Handoffs:
  - Requirement 007 consumes the accepted inventory and uses `accepted_behavior_class` to choose broker-success, serialized owner mutation, or typed guard-fail-fast behavior.
  - Requirement 008 consumes the gauntlet and broadens repeated zero-timeout verification after fixes.

## State And Invariants

- States:
  - `inventory_candidate`: discovered from registry/dispatcher but not yet confirmed PGLite-touching.
  - `inventory_row_verified`: row has entrypoint, open-site, current behavior, trust boundary, side effects, and accepted behavior class.
  - `gauntlet_runnable`: safe to execute concurrently in temp PGLite home.
  - `gauntlet_safe_non_execution`: represented without concurrent live execution because execution would be destructive or require external state.
  - `expected_red`: current behavior exposes raw lock/connect timeout or owner bypass risk and must include both `current_expected_outcome` and `future_required_outcome`.
  - `existing_pass`: current behavior is already brokered or typed-guarded.
  - `harness_setup_failure`: owner/backend/environment precondition was not proven, so no row outcome may be trusted.
  - `owner_split_brain`: PGLite lock exists but broker socket/readiness is missing, stale, delayed, or unusable.
- Invariants:
  - Every row has exactly one accepted behavior class.
  - No discovered PGLite-touching row may be silently omitted.
  - `out_of_scope_with_user_approval` requires an explicit decision entry; absent approval is validator failure.
  - Remote MCP classifications must preserve `OperationContext.remote` fail-closed semantics.
  - File upload and filesystem-touching rows must record confinement behavior and may not broaden remote authority.
  - Requirement 006 must not add operations to owner broker routing.
- Consistency rules:
  - Inventory required surface ids must match validator expectations.
  - Inventory rows must cover every code-derived PGLite candidate unless a validator-approved exclusion is backed by a decision entry.
  - Live-owner rows must have live-owner behavior evidence; no-owner behavior is a separate baseline field.
  - Mode-sensitive command groups must split into separate rows when behavior, side effects, trust boundary, or accepted behavior class differs.
  - Gauntlet raw-timeout detection distinguishes raw PGLite lock/connect timeout from typed broker/guard errors and is backed by positive and negative fixture examples.
  - Gauntlet manifests must prove row completeness, attempt cardinality, setup readiness, environment isolation, and cleanup status before coverage ledger closure.
  - Coverage ledger rows remain `planned` until artifact/test evidence closes them.

## Error Handling And Edge Cases

- Errors:
  - Validator missing required surface: nonzero exit, row id listed.
  - Validator unclassified row: nonzero exit, row id listed.
  - Validator invalid enum: nonzero exit, allowed values listed.
  - Gauntlet subprocess timeout: captured as harness timeout, not conflated with raw PGLite lock/connect timeout.
  - Raw owner lock/connect timeout: captured via stderr/stdout classifier and strict expected-red assertion.
- Edge cases:
  - `gbrain call list_pages` read path under live owner.
  - `gbrain call file_upload` trusted local but filesystem-sensitive path.
  - Remote MCP op with `localOnly` false but admin/write scope.
  - Stdio MCP, HTTP MCP, and trusted-local `gbrain call` actor differences.
  - `doctor --remediate` and migration/apply-migrations paths needing safe non-execution or dry-run.
  - `sync`, `embed`, `extract` maintenance-deferred current behavior.
  - No owner active, where direct open can remain valid.
  - Owner broker socket missing/stale while PGLite lock is live.
  - Owner startup and duplicate-owner-start paths under an existing lock.
  - Empty or under-seeded fixture data that exits before the intended PGLite access path.
  - Inherited `DATABASE_URL`, stale `GBRAIN_HOME`, alternate backend config, read-only temp dirs, or permission errors.
- Recovery:
  - Tests use temporary homes and source repos only.
  - No live user lock deletion, migration, or destructive remediation runs in this slice.
  - Failed gauntlet leaves captured stdout/stderr/error-shape for requirement evidence.
  - Harness precondition failures are recorded separately from product row outcomes.
  - Owner process, socket, and temp lock cleanup are asserted or reported as `cleanup_required`.
- Observability:
  - Gauntlet result objects include `row_id`, `attempt`, `command`, `exit_code`, `timed_out`, `stdout_tail`, `stderr_tail`, `raw_timeout_detected`, and `typed_error_code`.
  - Harness result manifests include `owner_pid`, `lock_observed`, `broker_ready`, `readiness_error`, `backend_confirmed`, `harness_phase`, `attempt_count_expected`, `attempt_count_observed`, `omitted_rows`, `teardown_status`, and `cleanup_required`.

## Testability

- Unit:
  - Validator accepts a complete fixture and rejects missing required surfaces, invalid enum values, duplicate ids, and unapproved `out_of_scope_with_user_approval`.
  - Validator rejects partial/unparseable source extraction, coarse command-group rows for mode-sensitive branches, live-owner rows without live-owner evidence, and runnable rows without data preconditions.
  - Raw-timeout classifier distinguishes raw PGLite lock/connect timeout text from typed broker errors such as `maintenance_deferred`, `owner_unreachable`, or `broker_timeout`.
  - Result manifest validation rejects omitted runnable rows, wrong attempt counts, missing safe-non-execution reasons, and missing cleanup/readiness fields.
- Integration:
  - Inventory validator runs against the real `pglite-access-inventory.yml`.
  - Gauntlet starts real local PGLite owner process and runs safe named matrix rows with N=3 concurrent attempts.
  - Harness setup asserts temp local PGLite backend/environment hygiene and fails closed when contaminated.
  - Stale/missing broker socket or lock/proxy split-brain fixture is classified separately from healthy live-owner row outcomes.
  - Owner cleanup/restart is verified after timeout or simulated harness failure.
  - Safe runnable MCP transport representatives are exercised for stdio/HTTP/trusted-local actor differences, or each skipped transport row records non-runnable rationale.
- E2E/manual if relevant:
  - Existing `test/pglite-concurrent-access.serial.test.ts` remains the baseline for brokered `query/search/think`.
  - New gauntlet must be explicit serial/PGLite test coverage and should reuse or extract the owner/subprocess harness from `test/pglite-concurrent-access.serial.test.ts` unless implementation evidence justifies a narrower duplicate.
- Mockable boundaries:
  - Validator source-file reads can be tested with fixture strings.
  - Raw-timeout classifier can be pure and unit-tested.
  - Subprocess command runner can expose a small result shape for fixture tests.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact task worktree path for managed repo implementation | non_blocking | Worktree preflight is required before implementation; planning can proceed in base worktree. | secondary-plan / implementation |
| Final inventory row count | non_blocking | Implementation must fill rows from structured discovery and validator evidence. | implementation |
| Whether gauntlet joins normal `bun test` or serial-only command | non_blocking | Plan-eng-review should choose runtime placement after reviewing test cost. | plan-eng-review |

## Self-Review

- Requirement coverage: All eight acceptance criteria map to artifacts, validators, tests, and handoff evidence.
- Separation of concerns: Requirement artifacts/tests/scripts depend on product source; product runtime does not depend on requirement artifacts.
- Testability: Schema validation, negative fixtures, raw-timeout classifier, and real subprocess gauntlet are independently testable.
- Security / safety: Remote authority and filesystem confinement remain explicit; destructive paths use dry-run or safe non-execution evidence.
- Requirement integrity: No scope reduction and no broad broker/guard behavior is introduced in this slice.
