# Primary Plan: PGLite Concurrency Verification

Plan id: `004-pglite-concurrency-verification`
Status: accepted
Created: 2026-06-20
Last updated: 2026-06-20
Secondary plan: [secondary_plan.md](secondary_plan.md)
Requirements source: [requirements.md](../../requirements/004-pglite-concurrency-verification/requirements.md)

## Goal Objective

- Codex goal objective: Prove and document that local PGLite gbrain can serve concurrent interactive CLI/MCP callers through the owner broker without normal-use PGLite lock timeout.
- User-visible outcome: Users can keep a PGLite owner process running and call `gbrain query`, `gbrain search`, `gbrain think`, or a second stdio MCP server without raw lock failures; maintenance commands remain explicitly deferred under a live owner.
- Why this is the right unit of work: Requirements 001-003 implemented the behavior; this slice closes the integrated E2E proof, diagnostic evidence matrix, and docs alignment.
- Goal completion standard: Requirement 004 closeout records real-subprocess E2E evidence, existing diagnostic regression coverage, docs updates, passing verification commands, and a conformance/implementation review verdict.

## Scope

- In scope:
  - Add one hermetic serial real-subprocess PGLite concurrency test.
  - Exercise one real owner stdio `gbrain serve`, one second stdio MCP proxy server, at least three concurrent CLI callers, and all three proxy MCP operations.
  - Include `query`, `search`, and `think` across CLI and MCP proxy paths.
  - Prove positive owner/proxy routing with operation socket readiness, proxy-only `tools/list`, and seeded marker results for `query`/`search`; absence of lock text alone is insufficient.
  - Update stale PGLite concurrency docs, especially `docs/architecture/serve-sync-concurrency.md`, the relevant `docs/ENGINES.md` table row, and the known stale README troubleshooting language.
  - Preserve and rerun existing tests that prove named stale/recovery/diagnostic statuses.
- Out of scope:
  - New network-facing broker behavior.
  - Raw SQL forwarding.
  - Mandatory daemon requirements.
  - True execution queueing for `sync`, `embed`, or `extract`.
  - External services, API keys, Docker, Postgres, or real user data in the new test.
- Non-goals:
  - Do not rework the broker architecture unless the E2E test exposes an implementation bug.
  - Do not weaken live-lock safety to make tests pass.
  - Do not claim maintenance work ran if it was only deferred.
- Assumptions:
  - Task implementation happens in `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker` on `codex/001-pglite-owner-broker`.
  - Baseline commit includes requirement 003 closeout commit `8a23554a`.
  - `think` may return deterministic keyless/no-result behavior as long as the route does not fail on PGLite locking.
- Dependencies or required inputs:
  - Requirement 004 requirements, research, and technical design are accepted.
  - Existing broker/lock tests remain the source of diagnostic matrix evidence.

## Execution Plan

1. Review current implementation and tests: inspect owner/proxy startup, operation socket path, subprocess test patterns, privacy/status tests, and current docs before editing.
2. Add the serial E2E test: create `test/pglite-concurrent-access.serial.test.ts` with hermetic `GBRAIN_HOME`, no inherited DB/provider env, source repo fixture, real owner stdio server, real proxy stdio server, three proxy MCP calls, and at least three concurrent CLI interactive calls.
3. Prove real proxy routing: assert config `engine: pglite`, owner lock/socket readiness, proxy `tools/list` exposes only `query`/`search`/`think`, seeded `query`/`search` marker results arrive through proxy/CLI, and `owner_unreachable`/`completion_unknown` fail the AC1/AC2 E2E.
4. Add or strengthen command-level regression evidence for no-owner direct-open, dead/stale-lock direct-open recovery, `completion_unknown` queue usability after timeout, interactive startup-election status, and privacy-safe diagnostics.
5. Verify post-teardown recovery: terminate proxy/owner from the E2E and assert a fresh direct-open CLI command or fresh owner starts without stale lock/socket behavior.
6. Update documentation: revise `docs/architecture/serve-sync-concurrency.md`, `docs/ENGINES.md`, and README troubleshooting language; search MCP docs and update only directly contradictory text.
7. Run targeted and related verification commands, then fix any real implementation bug exposed by the new E2E test.
8. Run requirement conformance and implementation-brake, reconcile findings, and perform closeout/commit for requirement 004.

## Acceptance Evidence

- Required artifact changes:
  - `test/pglite-concurrent-access.serial.test.ts`
  - `docs/architecture/serve-sync-concurrency.md`
  - `docs/ENGINES.md`
  - `README.md`
  - Requirement-local evidence, implementation-brake, and closeout artifacts.
- Required behavior or state changes:
  - Real subprocess E2E proves six or more mixed interactive calls with real owner/proxy topology, positive proxy-mode evidence, seeded served results, post-teardown re-entry, and no raw PGLite lock timeout.
  - Docs describe interactive broker routing separately from maintenance deferral.
  - Existing/new command-level tests prove stale/recovery/privacy status rows without overclaiming E2E scope.
- Required tests or verification commands:
  - `bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000`
  - `bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000`
  - `bun run typecheck`
- Evidence that is insufficient by itself:
  - Fake-owner or injected-socket tests without the new real-subprocess E2E.
  - "No lock timeout text" without positive owner/proxy evidence.
  - Passing docs-only checks.
  - A successful single CLI call when no live owner exists.
- Manual checks, if any:
  - Inspect docs for overclaiming maintenance queue execution or presenting CLI maintenance preflight statuses as broker/IPC statuses.

## Goal Completion Audit

- Requirements evidence map:
  - `AC1/AC2 real mixed CLI/MCP concurrency` -> `test/pglite-concurrent-access.serial.test.ts` plus targeted serial test pass with owner socket, proxy `tools/list`, seeded marker, all proxy operations, and post-teardown re-entry evidence.
  - `AC3 stale owner/socket recovery` -> existing and strengthened `test/pglite-operation-ipc.test.ts`, `test/pglite-lock.test.ts`, and `test/cli-pglite-operation-broker.test.ts` passes.
  - `AC4 diagnostics privacy` -> broker/status tests covering query text, params, source/federated env sentinels, MCP auth material, and maintenance/status paths; docs keep status ownership split.
  - `AC5 docs` -> updated docs paths and closeout inspection, including README.
  - `AC6 no external services` -> test fixture env clears provider keys and uses local PGLite/source data.
  - `AC7 regressions` -> related suite plus typecheck.
  - `AC8 evidence matrix` -> requirement 004 closeout table with evidence type and path.
- Plan step evidence map:
  - `Review current implementation` -> notes in evidence or closeout.
  - `Add serial E2E` -> new test file and targeted command result.
  - `Prove real proxy routing` -> assertions in test and passing command.
  - `Strengthen command-level regressions` -> targeted related suite pass.
  - `Verify post-teardown recovery` -> serial test re-entry assertion.
  - `Update documentation` -> doc diffs and closeout doc_update evidence.
  - `Run verification` -> captured command results in evidence/closeout.
  - `Review/closeout` -> conformance, implementation-brake, and closeout artifacts.
- Secondary guardrail evidence map:
  - `Do not weaken live-lock safety` -> stale/live lock tests remain green.
  - `Do not overclaim maintenance queueing` -> docs explicitly say maintenance is deferred under live owner.
  - `Do not accept deterministic broker failures as AC1/AC2 success` -> serial E2E treats `owner_unreachable`, `broker_timeout`, and `completion_unknown` as failures.
  - `Preserve status ownership` -> docs/closeout separate broker/IPC statuses from CLI maintenance preflight statuses.
  - `Keep public command syntax unchanged` -> tests invoke existing `query`, `search`, `think`, and `serve`.
- Review gate evidence map for gates used or requested:
  - `plan-devex-review` -> `plans/004-pglite-concurrency-verification/plan-devex-review.md` `GO WITH CHANGES` findings reconciled.
  - `plan-eng-review` -> `plans/004-pglite-concurrency-verification/plan-eng-review.md` `GO WITH CHANGES` findings reconciled.
  - `scenario-brake` -> `plans/004-pglite-concurrency-verification/scenario-brake.md` `[SCENARIOS MISSING]` findings reconciled.
  - `implementation-brake` -> `[SHIP]` before closeout.
  - Unused gates: `plan-design-review` not applicable because no UI is changed.
- Deliverables evidence map:
  - `E2E test` -> `test/pglite-concurrent-access.serial.test.ts`
  - `Docs` -> `docs/architecture/serve-sync-concurrency.md`, `docs/ENGINES.md`, `README.md`
  - `Closeout matrix` -> `requirements/004-pglite-concurrency-verification/closeout.md`
- Verification evidence map:
  - `serial test` -> pass proves real subprocess mixed concurrency.
  - `related suite` -> pass proves requirements 001-003 did not regress.
  - `typecheck` -> pass proves TS compile health.
- Insufficient completion signals:
  - New E2E test added but skipped/flaky without passing evidence.
  - Docs changed without running the related broker/lock suite.
  - Tests pass but closeout lacks evidence type separation.
- Residual risk accepted for this goal:
  - The E2E test proves local subprocess behavior, not multi-machine or networked concurrency.

## Context Sources

- Files or docs to read first:
  - `requirements/004-pglite-concurrency-verification/requirements.md`
  - `requirements/004-pglite-concurrency-verification/research.md`
  - `requirements/004-pglite-concurrency-verification/technical-design.md`
  - `src/cli.ts`
  - `src/mcp/server.ts`
  - `test/e2e/pglite-cli-exit.serial.test.ts`
  - `test/cli-pglite-operation-broker.test.ts`
  - `test/pglite-operation-ipc.test.ts`
  - `test/pglite-lock.test.ts`
  - `README.md`
  - `docs/architecture/serve-sync-concurrency.md`
  - `docs/ENGINES.md`
- Related requirements/spec/contracts:
  - `requirements/001-pglite-owner-broker/requirements.md`
  - `requirements/002-pglite-operation-forwarding/requirements.md`
  - `requirements/003-pglite-priority-scheduler/requirements.md`
- Related local planning or review artifacts:
  - Requirement 004 progress/evidence/decisions artifacts.
  - `plans/004-pglite-concurrency-verification/plan-devex-review.md`
  - `plans/004-pglite-concurrency-verification/plan-eng-review.md`
  - `plans/004-pglite-concurrency-verification/scenario-brake.md`
- External references, if any:
  - None required.

## Continuation And Stop Rules

- Continue while:
  - Work adds or tightens real subprocess proof, docs alignment, or regression evidence within requirement 004.
- Ask the user when:
  - The five-caller mixed CLI/MCP proof must be reduced.
  - A fix would require a mandatory daemon, public command syntax change, or network broker behavior.
  - Maintenance behavior would change from deferred to queued/executed.
- Stop without changing files when:
  - A proposed path weakens live PGLite lock safety or relies on real user data/external services.
- Mark the goal blocked only when:
  - The same requirement-blocking condition repeats for the required goal turns and no local implementation or test adaptation can make progress.
- Mark the goal complete only when:
  - The whole sequence, including requirement 005 production readiness, has passed and the sequence outcome is genuinely achieved.

## Drift Checks

- The final Codex proposed plan agrees with this primary plan.
- The secondary plan's guardrails do not contradict this primary plan.
- Requirements/spec/contracts, when present, remain the product behavior source of truth.
- Any implementation-changing Plan Engineer Review or Scenario Brake decision has been reflected here.

## Goal Handoff Checklist

- [x] Objective is concrete enough for `create_goal`.
- [x] Execution steps are ordered and independently checkable.
- [x] Acceptance evidence is explicit.
- [x] Verification commands are listed.
- [x] Goal completion audit maps requirements, plan steps, guardrails, review gates, deliverables, and verification to evidence.
- [x] Stop, escalation, blocked, and completion rules are clear.
- [x] Secondary plan has been read and reconciled.
- [x] No hidden chat-only requirement is needed to execute this goal.
