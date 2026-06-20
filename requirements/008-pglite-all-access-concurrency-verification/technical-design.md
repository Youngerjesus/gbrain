# Technical Design: PGLite All-Access Concurrency Verification

Created: 2026-06-21
Status: Complete
Requirement source: requirements/008-pglite-all-access-concurrency-verification/requirements.md
Research source: requirements/008-pglite-all-access-concurrency-verification/research.md
Architecture artifact: Not required - requirement 008 adds requirement-local verification harnesses, validators, and evidence artifacts; requirement 007 already owns the runtime broker/guard architecture.

## Requirement Coverage

| Requirement / Acceptance Criterion | Design mapping |
| --- | --- |
| AC1. Consume requirement 006 and 007 artifacts | Add preflight checks that run the requirement 006 inventory validator, read the accepted inventory, read requirement 007 representative/evidence artifacts, and compare matrix rows against runtime policy parity. |
| AC2. Define named command matrix | Create `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-command-matrix.yml` generated or validated from the accepted 468-row inventory. Each row records row id, surface, command/tool, caller, expected behavior class, execution mode, data preconditions, safety rationale, timeout budget, and expected outcome. |
| AC3. Run N=3 concurrent attempts | Add a serial live matrix test or script that runs N=3 concurrent attempts for rows with executable modes (`live_concurrent`, `typed_guard_concurrent`, `dry_run_concurrent`, `fixture_concurrent`) against temporary PGLite homes or controlled fixtures. |
| AC4. Prove zero raw timeout | Add a final outcome classifier and result validator that fails on raw PGLite lock/connect timeout text, harness timeouts masquerading as product outcomes, direct-open lock failures, and untyped connect timeouts. |
| AC5. Preserve behavior class | Result validator compares observed final outcome against the accepted `broker_success_read`, `serialized_owner_mutation`, or `typed_guard_fail_fast` class and fails on guard-only downgrade or class mismatch. |
| AC6. Include heavy/filesystem/maintenance surfaces | Matrix generation has required surface group checks for sync, embed, extract, doctor remediation, migrations/apply-migrations/upgrade, and file upload/files. Unsafe rows remain represented through explicit safe execution modes and row-specific rationale. |
| AC7. Preserve trust boundaries | Matrix rows include caller context and remote/local flags. Tests include remote MCP local-only rejection and filesystem-sensitive local/remote cases, always using temp homes and confined paths. |
| AC8. Produce structured evidence | Write raw result JSONL, validation summary JSON, and evidence summary Markdown under the requirement directory; coverage ledger refs point to these artifacts at closure. |
| AC9. Fail closed | Validator rejects missing rows, stale fingerprints, invalid execution mode, missing attempt count, missing stderr/error-shape fields, unclassified output, cleanup failures, and incomplete safe-non-execution rationale. |
| AC10. Handoff to production-readiness | Closeout updates evidence, coverage ledger, and sequence progress with exact commands, artifact paths, unresolved risks, and requirement 009 handoff. |

## Module Design

- Module boundaries:
  - `scripts/generate-pglite-all-access-matrix.ts`
    - Reads `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.
    - Reads code-native policy through `src/core/pglite-owner-policy.ts`.
    - Emits or refreshes the requirement-local command matrix.
    - Does not mutate requirement 006 inventory.
  - `scripts/validate-pglite-all-access-matrix.ts`
    - Validates matrix schema, inventory parity, behavior-class parity, execution-mode completeness, required surface groups, result artifacts, raw-timeout classifier output, and fail-closed closure criteria.
    - Reuses or imports pure helpers from `scripts/validate-pglite-access-inventory.ts` when suitable, but owns final 008 semantics.
  - `test/pglite-all-access-matrix-validator.test.ts`
    - Unit/fixture tests for matrix schema, result classification, behavior-class mismatch rejection, raw-timeout positive/negative fixtures, missing-row rejection, and safe-non-execution counterexamples.
  - `test/pglite-all-access-concurrency-matrix.serial.test.ts`
    - Serial subprocess/integration test that starts a temp owner or controlled owner fixture and runs the executable matrix rows with N=3 attempts.
  - Requirement artifacts:
    - `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-command-matrix.yml`
    - `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-results.jsonl`
    - `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-validation.json`
    - `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-summary.md`
    - `requirements/008-pglite-all-access-concurrency-verification/pglite-all-access-run-manifest.json`
- Public interfaces:
  - Matrix top-level fields:
    - `requirement_id`
    - `schema_version`
    - `inventory_ref`
    - `inventory_sha256`
    - `source_fingerprints`
    - `attempts_expected: 3`
    - `raw_lock_timeout_allowed: false`
    - `rows`
  - Matrix row fields:
    - `row_id`
    - `command_or_operation`
    - `surface`
    - `caller`
    - `transport`
    - `local_only`
    - `mcp_exposed`
    - `operation_context_remote`
    - `filesystem_confinement`
    - `caller_surface`
    - `accepted_behavior_class`
    - `expected_final_outcome`
    - `execution_mode`
    - `attempts`
    - `timeout_ms`
    - `fixture_profile`
    - `owner_sequence`
    - `args_or_params_profile`
    - `data_preconditions`
    - `safety_rationale`
    - `evidence_source_refs`
  - Execution modes:
    - `live_concurrent`: real subprocess or MCP call against a temporary live owner.
    - `typed_guard_concurrent`: real subprocess expected to fail fast before direct PGLite open.
    - `dry_run_concurrent`: real command with safe dry-run flags and temporary home.
    - `fixture_concurrent`: controlled owner/dispatch fixture that exercises policy/dispatch/output/error shape without destructive side effects.
    - `safe_non_execution`: no live attempt; requires bounded row-specific rationale plus replacement evidence.
  - Result entry fields:
    - `row_id`
    - `attempt`
    - `execution_mode`
    - `command`
    - `exit_code`
    - `timed_out`
    - `duration_ms`
    - `stdout_tail`
    - `stderr_tail`
    - `stdout_sha256`
    - `stderr_sha256`
    - `full_stream_classification_sha256`
    - `structured_error`
    - `owner_status`
    - `final_outcome`
    - `raw_lock_timeout_observed`
    - `cleanup_status`
    - `run_id`
    - `pass`
    - `failure_reason`
    - `failure_category`
- Dependency direction:
  - Scripts/tests may read requirement artifacts and product source.
  - Product runtime must not import requirement 008 artifacts or validators.
  - The matrix generator may import `resolvePgliteOwnerPolicy`; lower-level runtime modules must not depend on scripts/tests.
  - Result validator consumes matrix/results only; it does not execute commands.
- Data flow:
  - Preflight validates requirement 006 inventory.
  - Matrix generator loads inventory rows and runtime owner policy, assigns execution mode, and writes matrix artifact.
  - Matrix generator copies canonical inventory trust fields into each row and the validator compares them back to inventory.
  - Matrix validator checks matrix parity and schema before any subprocess execution.
  - Serial runner executes executable rows in temp homes/fixtures and writes raw JSONL results.
  - Result validator reads matrix plus JSONL and writes validation summary.
  - Run manifest ties matrix, results, validation, summary, inventory hash, source fingerprints, temp root, owner session, command invocation, timestamps, artifact hashes, and final run status into one coherent proof bundle.
  - Closeout updates coverage ledger evidence refs from validation artifacts.

## Interactions

- Main flow:
  - Validate requirement 006 inventory.
  - Generate or validate requirement 008 matrix.
  - Assert matrix row count equals 468 and class counts match accepted inventory.
  - Start a healthy temp local owner for `live_concurrent`, `typed_guard_concurrent`, and `dry_run_concurrent` rows.
  - Run exactly three concurrent attempts per executable row.
  - For `fixture_concurrent` rows, run three controlled dispatch attempts that still capture final outcome, error shape, and raw-timeout classification.
  - For `safe_non_execution` rows, emit no attempts but require safety rationale, accepted final outcome, and evidence refs.
  - For HTTP MCP rows, use explicit `http_owner_server` topology evidence: the HTTP server is the owner process and remote=true JSON-RPC/envelope behavior is exercised. A second HTTP process under an already-live owner that would need new proxying is requirement-impact and blocks this verification-only slice.
  - For owner-startup and duplicate-owner rows, use an explicit actor/state sequence with actor A/B, initial state, next state, expected outcome, and attempt semantics.
  - For rerun after partial failure, reject stale or mixed artifacts unless a deliberate clean replace/resume mode creates a new coherent run manifest.
  - Validate raw results and write summary.
  - Replace coverage-ledger `planned_evidence` entries with concrete evidence refs during implementation/closeout.
- Alternate flows:
  - If inventory fingerprints are stale, stop before matrix execution and record requirement impact or stale recheck.
  - If runtime policy does not cover an accepted row, stop before matrix execution.
  - If owner setup fails, mark harness failure and do not trust row outcomes.
  - If a row command needs external credentials or network, use `fixture_concurrent` or `safe_non_execution` only with row-specific rationale.
  - If a typed guard row exits nonzero with the expected typed error, treat it as pass only when raw timeout is false and structured error shape matches.
  - If a mutation row exits nonzero for invalid fixture data, fail unless the row's expected final outcome explicitly allows a typed validation error unrelated to PGLite locking.
- Handoffs:
  - Technical-design hands matrix schema and module ownership to plan-devex-review and plan-eng-review.
  - Implementation hands raw matrix artifacts to implementation-brake and closeout.
  - Closeout hands artifacts to requirement 009 production-readiness.

## State And Invariants

- States:
  - `inventory_preflight_passed`: requirement 006 inventory validated and row/class counts recorded.
  - `matrix_generated`: requirement 008 matrix exists and is linked to the inventory hash.
  - `matrix_validated`: matrix parity/schema validation passed.
  - `owner_ready`: temp live owner and broker are ready for executable rows.
  - `row_attempts_recorded`: each executable row has exactly three attempt records.
  - `row_safe_non_execution_recorded`: non-executed row has bounded rationale and evidence refs.
  - `validation_passed`: result validator found no missing rows, raw timeout, class mismatch, or incomplete capture.
  - `validation_failed`: row-specific failure blocks closeout.
  - `partial_run_present`: prior artifacts exist but do not form a completed coherent run package.
  - `owner_lost`: owner was healthy at setup but died or became unreachable during row execution.
  - `stale_artifact_rejected`: result, validation, or summary artifact does not match current matrix/run identity.
- Invariants:
  - Every accepted inventory row appears exactly once in the requirement 008 matrix.
  - Matrix behavior class equals inventory behavior class.
  - Matrix trust-boundary fields equal inventory `local_only`, `mcp_exposed`, `operation_context_remote`, `filesystem_confinement`, `caller_surface`, and `transport`.
  - Matrix fixture profiles are explicit and validator-owned; migration/doctor/schema rows require a profile that can expose migration-pending behavior or a row-specific safe rationale.
  - One successful full proof has one `run_id` across matrix execution outputs, manifest, validation, summary, and coverage-ledger refs.
  - `attempts` is 3 for executable modes.
  - No raw PGLite lock/connect timeout is allowed in full captured stdout, stderr, structured errors, timeout exceptions, or process-failure text. Tails and hashes are evidence storage only, not the source of truth for classification.
  - Raw timeout absence is not enough; final outcome must preserve the accepted behavior class.
  - Execution-mode eligibility is validator-owned. Live-runnable or product-boundary-runnable rows cannot be downgraded to fixture/non-execution without row-specific disqualifying metadata and approved requirement-impact evidence when behavior strength is reduced.
  - Safe non-execution cannot be generic and must have row-specific rationale and evidence refs.
  - Verification never uses the user's live `GBRAIN_HOME`, PGLite path, source, or lock.
  - Failed setup or cleanup is a harness failure and blocks closeout.
- Consistency rules:
  - Matrix `inventory_sha256` must match the accepted inventory file used for generation.
  - Required surface groups must include sync, embed, extract, doctor remediation/fix/remediate, migrations/apply-migrations/upgrade, file upload/files, local CLI, gbrain call, stdio MCP, HTTP MCP, and owner-startup/duplicate-owner-start rows where present in inventory.
  - Result entries must match matrix row command/profile and execution mode.
  - Result validator rejects unknown typed errors unless technical-design or implementation explicitly adds them to the typed outcome enum with tests.
  - Coverage ledger closure cannot pass while rows have only `planned_evidence`.

## Error Handling And Edge Cases

- Errors:
  - `inventory_stale`: inventory validator or hash check fails.
  - `matrix_row_missing`: accepted inventory row absent from matrix.
  - `matrix_class_mismatch`: matrix class differs from accepted inventory.
  - `invalid_execution_mode`: row mode is unknown or lacks required safety fields.
  - `wrong_attempt_count`: executable row has fewer or more than three attempts.
  - `raw_timeout_observed`: stdout/stderr/error text contains raw PGLite lock/connect timeout.
  - `behavior_class_mismatch`: final outcome is weaker or different than accepted behavior class.
  - `execution_mode_downgrade`: matrix assigns fixture/non-execution to a live-runnable or product-boundary-runnable row without approved row-specific rationale.
  - `trust_boundary_drift`: matrix or result fields differ from inventory trust-boundary fields.
  - `http_topology_mismatch`: HTTP MCP row uses stdio evidence, invented proxy evidence, or ambiguous owner topology.
  - `unclassified_output`: result cannot be classified as success, serialized mutation, typed guard, or explicit safe non-execution.
  - `harness_setup_failure`: temp owner/backend readiness was not proven.
  - `cleanup_failed`: temp owner/socket/home cleanup failed or needs manual cleanup.
  - `env_isolation_failed`: inherited or resolved DB/home/source path escapes the temp fixture.
  - `stale_or_mixed_artifact`: result or validation artifact belongs to another run id, matrix hash, inventory hash, owner session, temp root, or incomplete run.
  - `owner_lost`: owner dies or becomes unreachable after setup and before run completion.
  - `invalid_fixture_profile`: row has missing, generic, or incompatible fixture profile.
  - `filesystem_timing_escape`: file path is symlink-swapped, deleted, or changed between validation and owner dispatch.
- Edge cases:
  - `call:list_pages:local-cli` must no longer be historical expected-red.
  - `sync`, `embed`, and `extract` typed guard behavior under live owner.
  - `doctor --remediate`, `doctor --fix`, and migration/apply-migrations rows with destructive potential.
  - `file_upload` local allowed path versus remote local-only rejection.
  - stdio MCP and HTTP MCP tool visibility/envelope preservation.
  - duplicate owner startup and owner-startup rows.
  - missing owner socket, corrupt/unknown lock, owner starting, broker timeout, and completion unknown.
  - commands that print partial success before nonzero/typed failure.
  - rows that require seeded data, empty brain, or migration-pending fixture state.
  - stale JSONL from a previous successful run with current row ids.
  - owner process termination after some rows have passed.
  - file upload path swapped to symlink or deleted before dispatch.
- Recovery:
  - Validator failures report row ids and exact fields.
  - Runner writes partial JSONL with `pass: false` and `failure_reason` when possible.
  - Partial artifacts are not reusable for closeout unless a fresh coherent run manifest supersedes them.
  - Cleanup always attempts to close owner processes and remove temp homes; cleanup uncertainty blocks closeout.
  - Requirement Impact is recorded if verification exposes implementation or inventory mismatch.
- Observability:
  - Matrix summary reports total rows, class counts, execution-mode counts, attempt counts, pass/fail counts, raw timeout count, class mismatch count, setup/cleanup status, and failed row ids.
  - Validation summary reports normalized `failure_category` and remediation details for product behavior failures, harness failures, owner lost, cleanup failures, evidence capture failures, inventory/policy drift, and user-decision-required cases.
  - Run manifest reports artifact bundle identity and hashes.
  - Evidence summary records commands run, artifact paths, environment isolation notes, and reproduction instructions.

## Testability

- Unit:
  - Matrix validator accepts a complete fixture and rejects missing rows, duplicate rows, class drift, invalid execution modes, missing required surface groups, and generic safe-non-execution rationale.
  - Matrix validator rejects execution-mode downgrades, trust-boundary drift, and HTTP topology ambiguity.
  - Matrix validator rejects missing/incompatible fixture profiles and owner-startup rows without actor/state sequence.
  - Result validator rejects raw timeout fixtures, including timeout text outside retained tails, wrong attempt counts, missing stderr/error-shape fields, behavior-class downgrades, and unclassified output.
  - Harness validator rejects poisoned env, outside-temp resolved paths, orphan owner/socket/lock residue, forced cleanup failure, stale/mixed artifact bundles, and owner-lost mid-run.
  - Filesystem fixtures cover symlink escape and deleted-before-dispatch for file upload/files rows.
  - Classifier distinguishes broker success, serialized owner mutation success, typed guard fail-fast, raw timeout, harness timeout, and unknown output.
  - Coverage-ledger closure rejects `planned_evidence` and accepts only concrete evidence refs with compatible types.
- Integration:
  - Inventory validator still passes against the accepted requirement 006 inventory.
  - Runtime policy parity still covers all 468 accepted rows.
  - Requirement 008 matrix generator emits 468 rows with the accepted 217 / 223 / 28 class counts.
  - Serial matrix runner exercises executable rows N=3 under temp owner/fixtures and writes JSONL results.
  - Result validator passes only when every executable row has three attempts and every row has accepted final evidence.
- E2E/manual if relevant:
  - Full serial matrix command may be kept out of the fast unit suite if runtime is high, but closeout must run the contracted final command and record artifacts.
  - A faster diff command may validate schema, fixtures, and a small executable smoke subset during iteration.
- Mockable boundaries:
  - Inventory and policy rows can be fixture-loaded.
  - Subprocess runner can be injected with canned stdout/stderr/exit codes.
  - Owner fixture can simulate `owner_unreachable`, `broker_timeout`, `completion_unknown`, and typed guard errors.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact split between `live_concurrent`, `fixture_concurrent`, and `safe_non_execution` rows | non_blocking | The design now makes mode eligibility validator-owned; implementation can assign modes deterministically only within those rules, and scenario-brake must pressure-test scope loss. | implementation / scenario-brake |
| Exact long-running command placement | non_blocking | Plan-devex and plan-eng should choose fast and full commands while preserving the full closeout evidence contract. | plan-devex-review / plan-eng-review |
| Exact stdout/stderr storage policy | non_blocking | Design allows bounded tails plus hashes; implementation can tune retention to avoid noisy or sensitive artifacts while preserving evidence. | implementation |

## Self-Review

- Requirement coverage: All ten acceptance criteria map to concrete artifacts, validators, runner behavior, and closeout evidence.
- Separation of concerns: Product runtime does not depend on requirement artifacts; scripts/tests own matrix and result validation.
- Testability: Schema fixtures, result classifier fixtures, policy parity, and live serial runner are independently testable.
- Security / safety: Real user brain access is disallowed; destructive/heavy rows require safe modes and row-specific rationale; remote/file trust boundaries remain explicit.
- Requirement integrity: No accepted row, behavior class, repeat count, or evidence level is weakened.
