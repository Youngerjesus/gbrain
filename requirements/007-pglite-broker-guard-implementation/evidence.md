# Requirement Evidence

## Evidence

### 2026-06-21 00:25 KST - Requirement draft created

- Claim: Requirement 007 draft captures the full broker/guard implementation scope from sequence item 2 and requirement 006 handoff artifacts.
- Evidence: Created `requirements/007-pglite-broker-guard-implementation/requirements.md` with ten acceptance criteria covering inventory consumption, brokered reads, serialized mutations, typed guards, trust boundaries, owner-state variants, public compatibility, expected-red replacement, class-complete targeted tests, and requirement 008 handoff.
- Command/artifact: requirement-clarifier draft
- Result: readiness blocked only on post-draft reviewer.
- Files:
  - `requirements/007-pglite-broker-guard-implementation/requirements.md`
  - `requirements/007-pglite-broker-guard-implementation/coverage-decision.yml`
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
- Gate status: requirement-clarifier draft completed
- Source artifact: requirement-clarifier
- Requirement Impact: none
- Blocking/non-blocking unresolved items: post-draft reviewer pending.

### 2026-06-21 00:25 KST - Coverage ledger readiness artifacts created

- Claim: Requirement 007 triggers the coverage ledger gate because it is broad, high-risk, and crosses multiple runtime/security/test modules.
- Evidence: Created `coverage-decision.yml` with `ledger_required: true` and `coverage-ledger.yml` with planned rows for inventory consumption, all three behavior classes, trust-boundary preservation, owner-state failures, public compatibility, expected-red replacement, class-complete regression, and requirement 008 handoff.
- Command/artifact: `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation`; `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation`
- Result: both returned pass with no errors.
- Files:
  - `requirements/007-pglite-broker-guard-implementation/coverage-decision.yml`
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
- Gate status: readiness and schema validation passed
- Source artifact: coverage-ledger
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none known before validation.

### 2026-06-21 00:25 KST - Post-draft reviewer SHIP

- Claim: Requirement 007 is accepted for downstream gates.
- Evidence: Requirement Clarifier Post-Draft Reviewer `Parfit` returned `reviewer_result_status: SHIP` with no findings. Reviewer notes confirmed the draft preserves all-PGLite scope, consumes the 468-row requirement 006 inventory, maps acceptance criteria to verification, preserves broker-success / serialized-owner / typed-guard behavior, keeps remote trust boundaries explicit, rejects raw PGLite lock/connect timeout, and separates requirement 007 implementation evidence from requirement 008 final repeated matrix proof.
- Command/artifact: post-draft reviewer result
- Result: `SHIP`
- Files:
  - `requirements/007-pglite-broker-guard-implementation/requirements.md`
  - `requirements/007-pglite-broker-guard-implementation/coverage-decision.yml`
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
- Gate status: requirement-clarifier-post-draft-review completed
- Source artifact: requirement-clarifier-post-draft-reviewer
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none.

### 2026-06-21 00:25 KST - Research gate completed

- Claim: Requirement 007 technical unknowns are resolved enough for technical-design.
- Evidence: Created `requirements/007-pglite-broker-guard-implementation/research.md` with eight decisions: use requirement 006 inventory as validation contract rather than runtime dependency, generalize existing local owner IPC beyond `query/search/think`, preflight live locks before direct PGLite opens, dispatch operation rows through existing `dispatchToolCall` semantics, use owner-owned serialization for accepted mutation rows, reuse/extend typed broker error vocabulary, enforce remote trust boundaries before and inside owner dispatch, and keep requirement 007 evidence class-complete while requirement 008 owns the full repeated matrix.
- Command/artifact: research gate
- Result: completed; no Requirement Impact.
- Files:
  - `requirements/007-pglite-broker-guard-implementation/research.md`
  - `src/core/pglite-operation-ipc.ts`
  - `src/cli.ts`
  - `src/mcp/server.ts`
  - `src/mcp/dispatch.ts`
  - `src/mcp/pglite-operation-dispatch.ts`
  - `src/core/pglite-lock.ts`
  - `src/core/operations.ts`
  - `test/cli-pglite-operation-broker.test.ts`
- Gate status: research completed
- Source artifact: research
- Requirement Impact: none
- Blocking/non-blocking unresolved items: non-blocking technical-design details remain for module names, exact typed error additions, representative row set, and command-module adapter versus wrapper placement.

### 2026-06-21 00:25 KST - Technical design completed

- Claim: Requirement 007 has an implementation-ready HOW-level design and a requirement-local architecture boundary artifact.
- Evidence: Created `technical-design.md` mapping all ten acceptance criteria to module boundaries, public interfaces, data flow, owner-state interactions, invariants, error handling, and tests. Created `architecture.md` because the slice changes cross-layer local owner runtime handoffs among CLI, MCP, IPC, lock inspection, owner dispatch, and evidence validators.
- Command/artifact: technical-design gate
- Result: completed; no Requirement Impact.
- Files:
  - `requirements/007-pglite-broker-guard-implementation/technical-design.md`
  - `requirements/007-pglite-broker-guard-implementation/architecture.md`
- Gate status: technical-design completed
- Source artifact: technical-design
- Requirement Impact: none
- Blocking/non-blocking unresolved items: non-blocking plan choices remain for protocol extension shape, exact command adapter ordering, exact new typed status names, and HTTP-vs-stdio proxy rollout order.

### 2026-06-21 00:25 KST - Plan DevEx review completed

- Claim: Draft implementation plan is developer-facing enough to proceed to engineering review after bounded DX changes.
- Evidence: Created `plans/007-pglite-broker-guard-implementation/reviews/plan-devex-review.md`; verdict `GO WITH CHANGES`. The review identified three bounded obligations: name a fast implementation feedback loop, specify typed CLI/MCP error examples, and check docs/help/changelog impact. These were reconciled into `plans/007-pglite-broker-guard-implementation/plan.md`.
- Command/artifact: plan-devex-review
- Result: `GO WITH CHANGES`, reconciled
- Files:
  - `plans/007-pglite-broker-guard-implementation/plan.md`
  - `plans/007-pglite-broker-guard-implementation/reviews/plan-devex-review.md`
- Gate status: plan-devex-review completed
- Source artifact: plan-devex-review
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none.

### 2026-06-21 00:25 KST - Plan Eng review completed

- Claim: Draft implementation plan is engineering-ready for scenario-brake after required plan, technical-design, architecture, and coverage-ledger changes.
- Evidence: Created `plans/007-pglite-broker-guard-implementation/reviews/plan-eng-review.md`; verdict `GO WITH CHANGES`. Scope/reuse, architecture/contract, and verification/failure companion reviewers identified required changes for scenario-brake, HTTP MCP ownership, additive IPC compatibility, surface-id keyed command adapters, inventory fingerprint refresh, row-id keyed representative coverage, owner-route proof, owner-side trust-boundary proof, and observability. The draft plan, technical design, architecture artifact, and coverage ledger were reconciled with those obligations.
- Command/artifact: plan-eng-review
- Result: `GO WITH CHANGES`, reconciled
- Files:
  - `plans/007-pglite-broker-guard-implementation/plan.md`
  - `plans/007-pglite-broker-guard-implementation/reviews/plan-eng-review.md`
  - `requirements/007-pglite-broker-guard-implementation/technical-design.md`
  - `requirements/007-pglite-broker-guard-implementation/architecture.md`
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
- Gate status: plan-eng-review completed
- Source artifact: plan-eng-review
- Requirement Impact: none
- Blocking/non-blocking unresolved items: scenario-brake is required before secondary-plan and implementation.

### 2026-06-21 00:25 KST - Scenario Brake completed

- Claim: Requirement 007 scenario coverage is sufficient to proceed to secondary-plan after required missing scenarios were reconciled into planning and evidence obligations.
- Evidence: Created `plans/007-pglite-broker-guard-implementation/reviews/scenario-brake.md`; verdict `[SCENARIOS MISSING]`. The review accepted companion findings for duplicate owner startup, separated owner-state fixtures, serialized mutation `completion_unknown` re-entry, owner crash/restart after accept, command adapter partial/misleading success, filesystem payload drift, caller/owner IPC version skew, wrong-owner home/profile/source identity, mandatory request/status correlation, and inventory fingerprint coverage. The draft plan, technical design, and coverage ledger were updated with these obligations.
- Command/artifact: scenario-brake
- Result: `[SCENARIOS MISSING]`, reconciled
- Files:
  - `plans/007-pglite-broker-guard-implementation/reviews/scenario-brake.md`
  - `plans/007-pglite-broker-guard-implementation/plan.md`
  - `requirements/007-pglite-broker-guard-implementation/technical-design.md`
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
- Gate status: scenario-brake completed
- Source artifact: scenario-brake
- Requirement Impact: none
- Blocking/non-blocking unresolved items: secondary-plan must preserve the scenario additions before implementation starts.

### 2026-06-21 00:25 KST - Secondary Plan completed

- Claim: Requirement 007 has an accepted implementation-ready primary plan and a secondary guardrail handoff preserving review decisions.
- Evidence: Updated `plans/007-pglite-broker-guard-implementation/plan.md` to `Status: accepted` and created `plans/007-pglite-broker-guard-implementation/secondary_plan.md`. The secondary plan preserves RALPLAN-DR principles, ADR decision, implementation guardrails, files to inspect, tests to add/run, plan-devex-review findings, plan-eng-review findings, and scenario-brake additions.
- Command/artifact: secondary-plan
- Result: completed
- Files:
  - `plans/007-pglite-broker-guard-implementation/plan.md`
  - `plans/007-pglite-broker-guard-implementation/secondary_plan.md`
  - `plans/007-pglite-broker-guard-implementation/reviews/plan-devex-review.md`
  - `plans/007-pglite-broker-guard-implementation/reviews/plan-eng-review.md`
  - `plans/007-pglite-broker-guard-implementation/reviews/scenario-brake.md`
- Gate status: secondary-plan completed
- Source artifact: secondary-plan
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none; worktree preflight and context-loading remain before implementation.

### 2026-06-21 00:25 KST - Worktree preflight completed

- Claim: Requirement 007 implementation has an isolated managed-repo task worktree.
- Evidence: Ran `scripts/init_worktree.sh /Users/jeongmin/Documents/garrytan-gbrain-007-pglite-broker-guard codex/007-pglite-broker-guard-implementation` from the main worktree. The script created branch `codex/007-pglite-broker-guard-implementation` at `01692b60678d4dac6d941c3a59211565a355ad8b`, installed dependencies, and initialized the worktree path. Local planning files were copied into ignored `plans/007-pglite-broker-guard-implementation/` in the task worktree.
- Command/artifact: worktree preflight
- Result: initialized; `bun install --frozen-lockfile` completed. Postinstall `gbrain apply-migrations --yes --non-interactive` reported `GBrain: Timed out waiting for PGLite lock`, reinforcing the requirement to use temporary test homes rather than the user's live brain during verification.
- Files:
  - `/Users/jeongmin/Documents/garrytan-gbrain-007-pglite-broker-guard`
  - `requirements/007-pglite-broker-guard-implementation/progress.md`
- Gate status: implementation-preflight completed
- Source artifact: worktree-preflight
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none; context-loading remains before implementation.

### 2026-06-21 00:25 KST - Context Loading completed

- Claim: Requirement 007 has a usable context-loader report before TDD implementation.
- Evidence: Context Loader `Lagrange` returned all required fields: inspected files/directories, core findings, change candidate files, test strategy, and residual context risk. The report identified the current narrow broker (`query/search/think`), representative current red `gbrain call list_pages {}`, reusable IPC/dispatch/status primitives, trust-boundary constraints in `operations.ts`, and HTTP MCP coverage gap.
- Command/artifact: context-loading subagent report
- Result: completed; report usable
- Files:
  - `src/core/pglite-operation-ipc.ts`
  - `src/mcp/pglite-operation-dispatch.ts`
  - `src/cli.ts`
  - `src/mcp/server.ts`
  - `src/commands/serve-http.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `test/pglite-operation-ipc.test.ts`
  - `test/pglite-all-access-inventory-gauntlet.serial.test.ts`
- Gate status: context-loading completed
- Source artifact: context-loading
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none; TDD implementation starts with the `call:list_pages` representative red.

### 2026-06-21 00:25 KST - Operation broker routing and policy parity implementation slice

- Claim: The first implementation slice generalizes operation-target owner routing beyond `query`/`search`/`think`, preserves MCP/local-only trust boundaries, and pins a code-native owner policy against the full accepted 468-row inventory.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "gbrain call list_pages proxies"` failed by timing out after the second process tried the direct PGLite path under a live owner lock.
  - `bun test test/pglite-owner-policy.test.ts` initially failed because `src/core/pglite-owner-policy.ts` did not exist.
  - `bun test test/cli-pglite-operation-broker.test.ts -t "second stdio MCP serve proxies broker-success read tools"` initially failed because the live-owner proxy listed only `query`, `search`, and `think`.
  - `bun test test/cli-pglite-operation-broker.test.ts -t "rejects localOnly MCP requests"` initially failed because remote `file_upload` reached handler execution under `dry_run`.
- Green evidence:
  - Added `src/core/pglite-owner-policy.ts` and `test/pglite-owner-policy.test.ts`; the policy parity test covers all 468 accepted inventory rows across operation, CLI command, and owner-startup row kinds with matching behavior class and local-only flags.
  - Generalized `OperationIpcOperation` to a non-empty string and kept IPC protocol validation/queue semantics compatible.
  - Added `gbrain call <operation> <json>` live-owner forwarding for all registered operations, including `list_pages`, while preserving local CLI `remote=false` context and `--source` forwarding.
  - Expanded live-owner stdio MCP proxy tools to all non-localOnly operation rows; `file_upload` is not advertised.
  - Added shared remote localOnly fail-fast guard in MCP dispatch and owner-side broker dispatch with typed `local_only_remote_rejected` status.
  - Updated standalone HTTP MCP transport tools/list to omit localOnly operations and added direct-call guard coverage for `file_upload`.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 31 pass, 0 fail, 253 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts` -> 42 pass, 0 fail, 2434 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/core/pglite-owner-policy.ts`
  - `src/core/pglite-operation-ipc.ts`
  - `src/mcp/pglite-operation-dispatch.ts`
  - `src/mcp/dispatch.ts`
  - `src/mcp/server.ts`
  - `src/mcp/http-transport.ts`
  - `src/cli.ts`
  - `test/pglite-owner-policy.test.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `test/http-transport.test.ts`
  - `test/e2e/mcp.test.ts`
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- Gate status: implementation in progress; first TDD slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none. Inventory content stayed row/class-stable; only source fingerprints changed for `src/cli.ts` and `src/mcp/server.ts`.
- Blocking/non-blocking unresolved items: full command-adapter execution coverage, row-id keyed representative manifest closure, implementation-brake, devex-review, coverage-ledger closure, and closeout remain.

### 2026-06-21 00:25 KST - Expanded typed guard for live-owner maintenance/exclusive commands

- Claim: Live-owner typed guard coverage now includes additional requirement-006 `typed_guard_fail_fast` CLI command rows beyond the original `sync`/`embed`/`extract` set.
- Red evidence: `bun test test/cli-pglite-operation-broker.test.ts -t "typed-guard caller defers"` failed for `apply-migrations` and `extract-conversation-facts`; both bounded runs timed out instead of returning a typed guard before the direct PGLite-touching path.
- Green evidence:
  - Expanded the typed-guard command set to include `apply-migrations`, `embed`, `extract`, `extract-conversation-facts`, `sync`, and `upgrade`.
  - Moved the guard before early CLI-only branches so `apply-migrations` and `upgrade` cannot bypass it under a live owner.
  - Added startup-handle release around early `upgrade` and `apply-migrations` execution when no owner is present.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "typed-guard caller defers|no-owner sync maintenance"` -> 3 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 31 pass, 0 fail, 253 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
- Files:
  - `src/cli.ts`
  - `test/cli-pglite-operation-broker.test.ts`
- Gate status: implementation in progress; typed guard representative slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none.
- Blocking/non-blocking unresolved items: `upgrade` is policy/guard-hook covered but not directly executed in tests because it is a self-update/network-facing command; full repeated command matrix remains requirement 008.

### 2026-06-21 00:25 KST - Representative coverage manifest added

- Claim: Requirement 007 now has a row-id keyed representative coverage manifest tied to the accepted requirement 006 inventory.
- Evidence: Added `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml` with targeted representatives for all three behavior classes, `gbrain-call`, local CLI, stdio MCP, HTTP MCP, and key owner-state variants. Added `test/pglite-broker-representative-coverage.test.ts` to validate every referenced row exists in the accepted inventory, behavior classes match inventory values, required surfaces are present, and owner-state representatives include healthy live owner, missing socket, corrupt lock, owner starting, and completion unknown.
- Commands:
  - `bun test test/pglite-broker-representative-coverage.test.ts` -> 1 pass, 0 fail, 40 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2474 expectations.
  - `bun run typecheck` -> pass.
- Files:
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
  - `test/pglite-broker-representative-coverage.test.ts`
- Gate status: implementation in progress; representative manifest validation green.
- Source artifact: targeted coverage manifest.
- Requirement Impact: none.
- Blocking/non-blocking unresolved items: manifest status remains `in_progress`; closure still requires remaining command-adapter evidence, coverage-ledger closure, devex-review, implementation-brake, and closeout.

### 2026-06-21 00:25 KST - First true CLI command adapter execution slice

- Claim: Requirement 007 now has executable owner-side CLI command adapter coverage for a true CLI command row, not only operation-backed rows.
- Target behavior: under a live local PGLite owner, `gbrain config show` forwards a typed `cli_command` target to the owner and renders the owner-returned stdout, stderr, and exit code without opening PGLite in the second process.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "config show"` failed because caller-side `gbrain config show` timed out under a live owner lock instead of forwarding, and owner-side dispatch returned `ok: false` for `operation: "__cli_command__"`.
- Green evidence:
  - Added optional IPC `target` support for `cli_command` requests while preserving legacy operation requests.
  - Added `src/mcp/pglite-cli-command-dispatch.ts`, with a `config show` adapter that captures `console.log`, `console.error`, and `process.exit(code)` into `{ stdout, stderr, exitCode }` so the owner process is not terminated by adapter execution.
  - Added caller-side broker routing for `cli:config:show` and renderer support for brokered CLI command output.
  - Added `cli:config:show` to `representative-coverage.yml`.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "config show|no-owner sync maintenance"` -> 3 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 33 pass, 0 fail, 267 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2477 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/core/pglite-operation-ipc.ts`
  - `src/mcp/pglite-cli-command-dispatch.ts`
  - `src/mcp/pglite-operation-dispatch.ts`
  - `src/cli.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
- Gate status: implementation in progress; first true CLI command adapter slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none. Inventory content stayed row/class-stable; only source fingerprints changed.
- Blocking/non-blocking unresolved items: adapter registry still covers only `cli:config:show`; additional true CLI command rows and closure/review gates remain before requirement 007 can close.

### 2026-06-21 00:25 KST - Serialized CLI command adapter execution slice

- Claim: Requirement 007 now has owner-side CLI command adapter execution evidence for a serialized mutation CLI command row.
- Target behavior: under a live local PGLite owner, `gbrain config set spend.posture gated` forwards a typed `cli_command` target to the owner and the owner executes the mutation through the owner engine, returning captured stdout, stderr, and exit code.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "config set"` failed because caller-side `gbrain config set` timed out under a live owner lock, and owner-side adapter execution did not call `engine.setConfig`.
- Green evidence:
  - Added caller-side broker target mapping for `cli:config:set`.
  - Extended `src/mcp/pglite-cli-command-dispatch.ts` to run `runConfig(engine, ['set', ...])` through the same owner-side output/exit capture used by `config show`.
  - Added `cli:config:set` to `representative-coverage.yml` as a `serialized_owner_mutation` local CLI representative.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "config set"` -> 2 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 35 pass, 0 fail, 279 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2480 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/cli.ts`
  - `src/mcp/pglite-cli-command-dispatch.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
- Gate status: implementation in progress; serialized CLI command adapter representative green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none.
- Blocking/non-blocking unresolved items: remaining true CLI command rows still need either implementation coverage, explicit coverage rationale, or additional adapter representatives before closure.

### 2026-06-21 00:25 KST - Filesystem-sensitive read CLI command adapter and direct operation CLI routing slice

- Claim: Requirement 007 now covers both filesystem-sensitive read CLI adapter execution and direct shared-operation CLI routing through the live owner.
- Target behavior:
  - Under a live local PGLite owner, `gbrain files list` forwards a typed `cli_command` target to the owner and the owner executes `runFiles(engine, ['list'])`, returning captured stdout/stderr/exitCode without opening PGLite in the second process.
  - Under a live local PGLite owner, direct operation CLI commands are no longer limited to `query`/`search`/`think`; the CLI routes any registered operation through owner IPC. The representative `gbrain list` route sends `operation: "list_pages"` and renders the owner result.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "files list"` initially timed out for caller-side `gbrain files list` and owner-side dispatch returned unsupported adapter output.
- Green evidence:
  - Added caller-side broker target mapping and owner-side adapter execution for `cli:files:list`.
  - Expanded `BROKERED_OPERATIONS` from the narrow `query`/`search`/`think` set to all registered operations from `src/core/operations.ts`, covering direct `operation-cli` rows through the existing operation owner dispatch path.
  - Added row-id keyed representatives for `cli:files:list` and `cli:list:operation-cli` in `representative-coverage.yml`.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "files list"` -> 2 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts -t "direct operation CLI"` -> 1 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 38 pass, 0 fail, 303 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2486 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/cli.ts`
  - `src/mcp/pglite-cli-command-dispatch.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- Gate status: implementation in progress; filesystem-sensitive read CLI command and direct operation CLI representative slices green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none. Inventory content stayed row/class-stable; source fingerprints refreshed.
- Blocking/non-blocking unresolved items: broad CLI-only command module adapter coverage is still incomplete; closure/review gates remain before requirement 007 can close.

### 2026-06-21 00:25 KST - Multiplexed CLI command adapter family expansion

- Claim: Requirement 007 now routes and owner-executes broad multiplexed CLI command families and many one-shot DB-bound CLI commands rather than only single hard-coded CLI command rows.
- Target behavior: under a live local PGLite owner, supported multiplexed CLI command rows resolve to stable `cli_command` surface ids and execute on the owner engine through the matching command module adapter.
- Green evidence:
  - Replaced the hard-coded caller-side `config show` / `config set` / `files list` target resolver with surface-id resolution for supported command families: `config`, `files`, `jobs`, `sources`, `repos`, `takes`, `search`, `eval`, `doctor`, `storage`, `status`, and `cache`.
  - Extended owner-side CLI command adapter dispatch for the same module families where repo command modules expose owner-engine-compatible entrypoints.
  - Refactored `runCache` to accept an optional owner engine so `cache stats/clear/prune` do not create a separate PGLite engine inside the owner adapter.
  - Added owner-engine adapters for one-shot DB-bound command rows including advisor, agent, anomalies, book-mirror, brainstorm/LSD, capture, code navigation, dream, edges-backfill, enrich, import/export, features, founder, graph-query, migrate, models, onboard, orphans, quarantine, recall/forget, reindex, reindex-code, reindex-frontmatter, salience, skillopt, transcripts, and ze-switch.
  - Added `cli:sources:list` and `cli:cache:stats` as row-id representatives for multiplexed local CLI command family routing.
  - At this point in the implementation, lifecycle/module-open-site/daemon/reset rows still needed a follow-up treatment decision; later slices resolved this with `auth`/`lint` adapters and approved typed guards for lifecycle/heavy/session commands.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "multiplexed CLI command families"` -> 1 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 39 pass, 0 fail, 319 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2492 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/cli.ts`
  - `src/mcp/pglite-cli-command-dispatch.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- Gate status: implementation in progress; multiplexed CLI command family routing slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none.
- Blocking/non-blocking unresolved items at this point: lifecycle/module-open-site/daemon rows still needed either direct adapter support, typed guard treatment, or a recorded implementation rationale before closeout; later slices below resolved this implementation gap.

### 2026-06-21 00:25 KST - Caller cwd/output capture and auth owner-engine adapter slice

- Claim: Requirement 007 now covers owner-side execution details that were not proven by earlier command-family adapters: caller cwd fidelity, direct `process.stdout.write`/`process.stderr.write` capture, and a DB-backed lifecycle command (`auth`) reusing the live owner engine instead of opening a second PGLite engine.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "owner-side CLI command adapters execute relative paths"` initially failed because `lint` was not routed as a brokered CLI command and owner-side execution did not use the caller cwd.
  - After adding cwd-aware `lint` routing, the test was tightened to assert stderr capture; it failed because `[lint.pages]` leaked through `process.stderr.write` rather than being returned in the brokered output envelope.
  - `bun test test/cli-pglite-operation-broker.test.ts -t "owner-side auth"` failed with brokered command `exitCode: 1` because `cli:auth:module-open-site` had policy coverage but no owner-side adapter.
- Green evidence:
  - `captureCliCommandOutput` now temporarily switches to the caller cwd for owner-side CLI adapters and restores the owner cwd afterward.
  - The same capture seam now intercepts `process.stdout.write` and `process.stderr.write`, not only `console.log`/`console.error`, so brokered CLI output returns in `{ stdout, stderr, exitCode }` instead of leaking from the owner process.
  - Added caller-side target mapping and owner-side adapter execution for `cli:lint:module-open-site`.
  - Refactored `runAuth(args, ownerEngine?)` and its DB-backed subcommands to use the supplied owner engine when present; direct standalone `auth` behavior still creates/connects/disconnects its own configured engine.
  - Added caller-side target mapping and owner-side adapter execution for `cli:auth:module-open-site`.
  - Added `cli:lint:module-open-site` and `cli:auth:module-open-site` representatives to `representative-coverage.yml`.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "owner-side CLI command adapters execute relative paths"` -> 1 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts -t "owner-side auth"` -> 1 pass, 0 fail.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 41 pass, 0 fail, 330 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2492 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `bun test test/pglite-broker-representative-coverage.test.ts` -> 1 pass, 0 fail, 64 expectations.
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/cli.ts`
  - `src/commands/auth.ts`
  - `src/mcp/pglite-cli-command-dispatch.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
- Gate status: implementation in progress; cwd/output/auth adapter slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: none. Inventory validation still passes after fingerprint regeneration.
- Blocking/non-blocking unresolved items at this point: lifecycle/module-open-site/daemon/reset rows still needed explicit typed-guard/rationale handling before requirement 007 could close; the lifecycle/heavy/session typed-guard slice below resolved this for the approved command set while leaving `serve` on its existing owner-startup/proxy path.

### 2026-06-21 00:25 KST - Lifecycle, daemon, reset, and heavy command typed-guard slice

- Claim: Local lifecycle/session/heavy commands that should not execute inside the owner broker now return bounded typed guard errors under a live PGLite owner, instead of bypassing the guard via help/status paths or blocking on direct PGLite access.
- User-approved requirement impact: The user approved the proposed treatment for mutating/heavy maintenance commands. The inventory and runtime policy were updated together, moving `autopilot`, `claw-test`, `frontmatter`, `init`, `integrity`, `mounts`, `reinit-pglite`, `repair-jsonb`, `schema`, and `watch` variants from `serialized_owner_mutation` to `typed_guard_fail_fast`. `serve` remains on the existing owner-startup/proxy path.
- Red evidence:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "typed-guard caller defers"` failed for the newly added lifecycle/session command representatives. `autopilot` and `watch` timed out; `claw-test`, `frontmatter`, `init`, `integrity`, `mounts`, `reinit-pglite`, `repair-jsonb`, and `schema` initially exited 0 through command help/status paths instead of returning `maintenance_deferred`.
  - After replacing `--help` profiles with safe real subcommands/flags, the remaining failures proved which commands still bypassed the live-owner guard.
- Green evidence:
  - Expanded the live-owner typed guard command set in `src/cli.ts`.
  - Updated `scripts/generate-pglite-access-inventory.ts` so accepted behavior classes match the approved live-owner treatment.
  - Updated `src/core/pglite-owner-policy.ts` so runtime policy parity matches the regenerated inventory.
  - Added typed-guard representatives for `cli:autopilot:pglite-surface`, `cli:reinit-pglite:no-sync`, and `cli:watch:pglite-surface`.
  - Regenerated `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`; accepted counts are now 217 `broker_success_read`, 223 `serialized_owner_mutation`, and 28 `typed_guard_fail_fast`.
- Commands:
  - `bun test test/cli-pglite-operation-broker.test.ts -t "typed-guard caller defers"` -> 12 pass, 0 fail, 108 expectations.
  - `bun test test/cli-pglite-operation-broker.test.ts` -> 51 pass, 0 fail, 420 expectations.
  - `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 0 fail, 2498 expectations.
  - `bun run typecheck` -> pass.
  - `bun run scripts/generate-pglite-access-inventory.ts`
  - `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> `{ "ok": true, "errors": [], "warnings": [] }`
  - `bun test test/pglite-broker-representative-coverage.test.ts` -> 1 pass, 0 fail, 73 expectations.
  - `python3 scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
  - `python3 scripts/coverage_ledger.py validate --mode schema --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `src/cli.ts`
  - `src/core/pglite-owner-policy.ts`
  - `scripts/generate-pglite-access-inventory.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `test/pglite-owner-policy.test.ts`
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`
  - `requirements/007-pglite-broker-guard-implementation/representative-coverage.yml`
- Gate status: implementation in progress; lifecycle/heavy/session typed-guard slice green.
- Source artifact: tdd-workflow implementation evidence.
- Requirement Impact: recorded in `decisions.md`; accepted inventory class counts changed to 217 / 223 / 28.
- Blocking/non-blocking unresolved items: devex-review, implementation-brake, coverage-ledger closure, and closeout remain before requirement 007 can be marked complete.

### 2026-06-21 00:25 KST - DevEx live audit completed

- Claim: Requirement 007 developer-facing CLI/MCP implementation is usable enough for post-implementation review, with no blocking DX findings.
- Evidence: Created `requirements/007-pglite-broker-guard-implementation/reviews/devex-review.md`. The audit dogfooded the contributor feedback loop, measured targeted TTHW under 3 minutes, scored overall DX 8/10, and recorded only non-blocking follow-ups for requirement 008 matrix packaging and requirement 009 public recovery docs/help guidance.
- Command/artifact: devex-review
- Result: PASS WITH NON-BLOCKING FOLLOW-UPS
- Files:
  - `requirements/007-pglite-broker-guard-implementation/reviews/devex-review.md`
  - `test/cli-pglite-operation-broker.test.ts`
  - `test/pglite-owner-policy.test.ts`
  - `test/pglite-broker-representative-coverage.test.ts`
- Gate status: devex-review completed.
- Source artifact: devex-review
- Requirement Impact: none.
- Blocking/non-blocking unresolved items: implementation-brake, coverage-ledger closure, and closeout remain before requirement 007 can be marked complete.

### 2026-06-21 00:25 KST - Coverage ledger closure and implementation-brake completed

- Claim: Requirement 007 implementation is ready for closeout.
- Evidence: Coverage ledger closure validator passed after all required rows were marked verified with typed evidence refs. Created `requirements/007-pglite-broker-guard-implementation/reviews/implementation-brake.md`; verdict `[SHIP]`, with no must-fix findings and conformance fallback self-review recorded as `CONFORMANT`.
- Commands:
  - `python3 scripts/coverage_ledger.py validate --mode closure --requirement-dir requirements/007-pglite-broker-guard-implementation` -> `{ "status": "pass" }`
- Files:
  - `requirements/007-pglite-broker-guard-implementation/coverage-ledger.yml`
  - `requirements/007-pglite-broker-guard-implementation/reviews/implementation-brake.md`
- Gate status: coverage-ledger closure passed; implementation-brake completed.
- Source artifact: implementation-brake
- Requirement Impact: none beyond already recorded lifecycle/heavy/session class reclassification.
- Blocking/non-blocking unresolved items: closeout remains before requirement 007 can be marked complete.

### 2026-06-21 00:25 KST - Closeout completed

- Claim: Requirement 007 is operationally closed and ready to hand off to requirement 008.
- Evidence: Confirmed implementation-brake `[SHIP]`, coverage-ledger closure pass, targeted final verification pass, no required context-sync update for repo-level operating guidance, and no safe/useful closeout refactor candidate within the touched area. Marked sequence item 2 complete.
- Final verification:
  - `bun test test/pglite-broker-representative-coverage.test.ts test/pglite-owner-policy.test.ts` -> 2 pass, 1953 expectations.
  - `python3 scripts/coverage_ledger.py validate --mode closure --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.
- Files:
  - `goal-requirements/002-pglite-all-access-concurrency/sequence.md`
  - `requirements/007-pglite-broker-guard-implementation/progress.md`
  - `requirements/007-pglite-broker-guard-implementation/evidence.md`
- Gate status: closeout completed.
- Source artifact: closeout
- Requirement Impact: none.
- Blocking/non-blocking unresolved items: none for requirement 007. Requirement 008 owns the repeated named command matrix; requirement 009 owns production-readiness and public recovery docs/help decisions.
