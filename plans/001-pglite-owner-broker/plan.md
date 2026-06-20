# Primary Plan: PGLite Owner Broker

Plan id: `001-pglite-owner-broker`
Status: accepted
Created: 2026-06-20
Last updated: 2026-06-20
Secondary plan: [secondary_plan.md](secondary_plan.md)
Requirements source: [requirements.md](../../requirements/001-pglite-owner-broker/requirements.md)

## Goal Objective

- Codex goal objective: Implement the first PGLite owner-broker slice so gbrain can route eligible concurrent PGLite `query`, `search`, and `think` calls through one owner process without normal PGLite lock timeout failures.
- User-visible outcome: Multiple local MCP/CLI callers can request interactive brain operations while a PGLite owner is alive; calls queue/serve through the owner instead of trying to open the database a second time.
- Why this is the right unit of work: It establishes the safe owner-forwarding contract required before the later operation-forwarding, scheduler, verification, and production-readiness slices can close the full sequence.
- Goal completion standard: The requirement can be marked complete only after implementation, required verification, implementation-brake `[SHIP]`, closeout, and sequence state updates prove AC1-AC8 for this slice without weakening PGLite locking.

## Scope

- In scope:
  - Local-only operation IPC for file-backed PGLite owner forwarding.
  - `gbrain serve` owner binding for the operation broker.
  - Pre-connect broker probing for eligible CLI/MCP caller paths.
  - Broker request/response diagnostics and priority-aware queue shape.
  - Exact privacy-safe user/operator status matrix for queued, served, owner-unreachable, stale-socket-recovered, and lock-safety-blocked states.
  - Operator/developer documentation for PGLite owner broker behavior and focused verification.
  - Tests for no-lock-timeout forwarding, direct-open fallback, trust/source preservation, stale recovery, and at least five concurrent callers.
  - MCP stdio owner-proxy startup path for a second `gbrain serve` process that cannot open PGLite directly while an owner is alive.
  - Non-acquiring PGLite lock classifier used before direct-open fallback.
  - `scripts/init_worktree.sh` if still missing before isolated managed repo implementation.
- Out of scope:
  - Unsafe direct multi-process PGLite access.
  - Network-accessible broker surfaces.
  - Changing public CLI command syntax.
  - Postgres behavior changes beyond behavior-preserving shared code.
  - `serve --http` owner broker behavior in this slice.
  - Public forwarding of `sync`, `embed`, or `extract`; only the queue priority seam is proven now, with real maintenance command integration reserved for `requirements/003-pglite-priority-scheduler`.
  - Full production readiness for the entire sequence before later slices complete.
- Non-goals:
  - Replacing PGLite with Postgres.
  - Rewriting all command dispatch.
  - Making PGLite SQL execution parallel.
- Assumptions:
  - Serializing actual PGLite SQL through one owner is acceptable if callers queue or are served without lock failures.
  - The existing resolve IPC pattern is valid precedent for local-only operation IPC.
  - Later scheduler and verification requirements may extend this broker without changing the public command contract.
- Dependencies or required inputs:
  - Accepted requirement: `requirements/001-pglite-owner-broker/requirements.md`.
  - Completed research/design artifacts in the same requirement folder.
  - Isolated managed repo worktree before product source implementation.

## Execution Plan

1. Complete pre-implementation review gates: run plan-UX, plan-DevEx, plan-engineering, and scenario review against this draft and reconcile findings into an accepted primary/secondary plan.
2. Prepare isolated implementation worktree: create `scripts/init_worktree.sh` if missing, run it to create a task worktree, and record cwd/root/branch/HEAD/dirty state before product edits.
3. Lock user/operator state matrix: define deterministic privacy-safe statuses/messages for queued, served, owner-unreachable, stale-socket-recovered, lock-safety-blocked, protocol-error, completion-unknown, and broker/operation timeout paths.
4. Add lock classifier: implement a non-acquiring, non-stealing `pglite-lock` classifier so broker-unavailable + live lock returns `lock_safety_blocked` before any `connectEngine()`/`acquireLock()` wait.
5. Add broker IPC module: implement typed local operation IPC with bounded messages, short probe timeout, stale socket cleanup, injected owner handler, queue/priority ordering, and deterministic diagnostics. The broker module must not import CLI or MCP dispatch directly.
6. Bind owner server: start/stop operation IPC from `startMcpServer()` for PGLite data dirs, alongside existing resolve IPC cleanup.
7. Add caller pre-connect routing: route eligible `query`, `search`, and `think` CLI paths through the broker before `connectEngine()` when owner is reachable; add an explicit pre-connect path for CLI-only `think`; preserve no-owner direct-open fallback.
8. Add MCP stdio proxy path: when a second `gbrain serve` sees a live PGLite owner and cannot directly connect, serve a stdio proxy for broker-eligible tools and forward `query`, `search`, and `think` to the owner.
9. Preserve trust/source behavior: ensure forwarded MCP calls execute with original `DispatchOpts`; ensure forwarded CLI calls remain local trusted, carry caller source-resolution inputs, and render existing output shapes.
10. Add phase-aware retry rules: distinguish before-send, queued-not-started, handler-started, and response-lost-after-handler cases; forbid automatic retry for mutating local `think --save/--take` when completion is ambiguous.
11. Add operator docs: update the most relevant existing docs with owner broker behavior, no-daemon fallback, diagnostics, and focused verification command.
12. Add regression coverage: unit tests for IPC/scheduler/diagnostics, integration tests for forwarded MCP trust/source, CLI smoke tests, stale recovery, second MCP stdio proxy, no-owner cold-start race, partial broker responses, permission/not-yet-bound sockets, long `think` queue behavior, positive broker-routing evidence, and at least five concurrent mixed callers without lock timeout strings.
13. Verify and review: run focused tests, relevant lint/typecheck checks, implementation-brake, required UX/DevEx live review evidence, closeout, and update sequence/requirement state.

## Acceptance Evidence

- Required artifact changes:
  - `src/core/pglite-operation-ipc.ts` or equivalent broker module.
  - Non-acquiring lock classifier in `src/core/pglite-lock.ts` or an adjacent lower-level helper.
  - `src/mcp/server.ts` owner binding and cleanup updates.
  - `src/mcp/server.ts` or adjacent MCP module owner-proxy path for second stdio MCP server startup.
  - `src/cli.ts` pre-connect broker routing seam, including CLI-only `think`.
  - CLI command helper updates for `think` and any needed `search` mapping.
  - Operator docs update for PGLite owner broker behavior and troubleshooting.
  - Tests under `test/` or `test/e2e/` covering AC1-AC8.
  - Requirement/sequence progress, decisions, and evidence updates.
- Required behavior or state changes:
  - A live PGLite owner prevents second direct-open attempts for brokered interactive calls.
  - A live PGLite lock with no reachable broker produces a fast `lock_safety_blocked` diagnostic rather than the 30s lock wait.
  - Unknown/corrupt lock classification with broker unreachable never falls into the normal 30s `acquireLock()` wait.
  - No owner keeps existing direct-open CLI behavior.
  - Concurrent no-owner cold starts converge without PGLite lock timeout.
  - At least five simultaneous mixed callers do not fail solely due to PGLite lock contention.
  - Five-caller evidence positively proves broker routing with request IDs, owner PID, or broker statuses; absence of timeout strings alone is insufficient.
  - MCP remote/source/takes visibility semantics survive broker forwarding.
  - Diagnostics distinguish queued, served, owner-unreachable, stale recovered, and lock-safety-blocked paths.
  - Ambiguous completion is distinct from ordinary timeout/unreachable states and blocks automatic retry of mutating `think`.
  - Diagnostics avoid raw private query text and include next action where a human can recover.
- Required tests or verification commands:
  - `bun test test/context/resolve-ipc.test.ts test/pglite-lock.test.ts` or updated broker-focused equivalents.
  - New focused broker unit/integration tests.
  - New or updated PGLite CLI/E2E concurrency test proving five callers without lock timeout strings.
  - Typecheck/verify command selected by implementation scope, at minimum a focused `bun test` set and any repo guard relevant to touched files.
- Evidence that is insufficient by itself:
  - A passing unit test that does not spawn or simulate competing callers.
  - Artifact existence without progress/evidence/decision state coherence.
  - Successful direct-open commands without a live owner.
  - Absence of visible failures without checking lock-timeout strings.
- Manual checks, if any:
  - Optional local CLI smoke with synthetic PGLite brain if automated subprocess test is too slow, but automation remains required for acceptance.

## Goal Completion Audit

- Requirements evidence map:
  - `AC1` -> second-process query/search/think test with live owner and no PGLite lock timeout/direct-open contention strings.
  - `AC2` -> no-owner direct-open smoke for query/search/think, allowing existing non-lock failures.
  - `AC3` -> at least five simultaneous mixed CLI/MCP-shaped callers complete or queue without lock failure and include positive broker-routing evidence; no-owner five-caller cold-start race also avoids PGLite lock timeout.
  - `AC4` -> priority queue unit/integration evidence using the same queue's maintenance-class seam now; real `sync`/`embed`/`extract` command forwarding/yield behavior remains required in `requirements/003-pglite-priority-scheduler` before the overall sequence can complete.
  - `AC5` -> forwarded MCP trust/source assertion for `remote=true`, takes allow-list, and allowed source scope.
  - `AC6` -> CLI command syntax smoke using unchanged command forms.
  - `AC7` -> stale socket/dead owner/live heartbeat lock tests.
  - `AC8` -> deterministic diagnostic status/message tests plus docs/evidence for operator interpretation.
- Plan step evidence map:
  - Review gates -> progress/evidence entries and accepted secondary plan.
  - Worktree setup -> recorded task worktree path/root/branch/HEAD/dirty state.
  - State matrix -> source/tests/docs showing exact status names, messages, timeout path, completion-unknown path, protocol-error path, and privacy guard.
  - Lock classifier -> tests showing no acquisition, no live lock steal, and no 30s wait.
  - Broker module -> source diff and unit tests proving injected handler boundary.
  - Owner binding -> source diff and server lifecycle tests.
  - Caller routing -> CLI/MCP tests proving pre-connect forwarding.
  - MCP stdio proxy -> startup/tool-call test for a second MCP process against a live owner.
  - Cold-start race -> no-owner concurrent caller test with deterministic safe outcomes.
  - Ambiguous completion -> owner death/timeout phase tests and no auto-retry for mutating `think`.
  - Socket and protocol mutations -> permission/not-yet-bound socket plus partial/truncated response tests.
  - Long interactive work -> long `think` ahead of quick interactive requests bounded by timeout/non-monopoly evidence.
  - Trust/source -> tests against dispatch context behavior, including `GBRAIN_SOURCE`, federated read, and remote `think` persistence blocking.
  - Verification -> command outputs summarized in evidence.md.
- Secondary guardrail evidence map:
  - Single-owner PGLite invariant -> no code path weakens `pglite-lock.ts` live heartbeat protection; tests prove no second direct-open in owner case.
  - Local-only transport -> socket path and permissions tests; no network listener.
  - No raw SQL over IPC -> protocol schema review/test.
  - Command compatibility -> unchanged CLI smoke.
  - Operator DX -> docs update and focused verification recipe.
  - Scope boundary -> tests/docs make clear `serve --http` and real maintenance command forwarding are not claimed by this slice.
- Review gate evidence map for gates used or requested:
  - plan-design-review -> Not applicable: no UI/visual surface.
  - plan-ux-review -> required because CLI/MCP diagnostics are user-facing operational experience.
  - plan-devex-review -> required because CLI/MCP commands and errors are developer/operator-facing.
  - plan-eng-review -> required before implementation.
  - scenario-brake -> required after plan-eng-review.
  - implementation-brake -> required after implementation and verification.
  - closeout -> required before checking this requirement complete.
- Deliverables evidence map:
  - Broker IPC -> source file and tests.
  - Owner binding -> `src/mcp/server.ts` diff and lifecycle evidence.
  - Caller routing -> `src/cli.ts` and command helper diffs plus subprocess tests.
  - State updates -> requirement and sequence progress/evidence/decisions.
- Verification evidence map:
  - Focused `bun test ...` -> all listed tests pass and directly cover broker behavior.
  - Concurrency subprocess test -> no lock timeout/direct-open contention strings across at least five callers.
  - Trust/source test -> forwarded MCP context fields match direct MCP dispatch semantics.
- Insufficient completion signals:
  - Code compiles but no concurrency proof.
  - Broker works for CLI but not MCP, or vice versa.
  - Forwarding changes command syntax.
  - Lock timeout string merely hidden while second direct-open still happens.
- Residual risk accepted for this goal:
  - Later sequence slices may expand maintenance operation coverage and final production readiness; this requirement must leave compatible priority hooks and evidence.

## Context Sources

- Files or docs to read first:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/architecture/KEY_FILES.md`
  - `docs/architecture/brains-and-sources.md`
  - `skills/conventions/brain-routing.md`
  - `src/core/pglite-lock.ts`
  - `src/core/pglite-engine.ts`
  - `src/core/context/resolve-ipc.ts`
  - `src/mcp/server.ts`
  - `src/mcp/dispatch.ts`
  - `src/cli.ts`
  - `src/commands/think.ts`
  - `src/commands/search.ts`
  - `src/core/operations.ts`
- Related requirements/spec/contracts:
  - `requirements/001-pglite-owner-broker/requirements.md`
  - `requirements/001-pglite-owner-broker/research.md`
  - `requirements/001-pglite-owner-broker/technical-design.md`
  - `requirements/001-pglite-owner-broker/architecture.md`
  - `goal-requirements/001-pglite-concurrent-access/sequence.md`
- Related local planning or review artifacts:
  - This draft plan; secondary plan pending.
- External references, if any:
  - None required; repo code/docs are authoritative for this slice.

## Continuation And Stop Rules

- Continue while:
  - Edits preserve single-owner PGLite safety and move brokered interactive operations closer to no-lock-failure concurrent use.
  - Verification gaps can be closed with focused tests or local synthetic fixtures.
- Ask the user when:
  - A public command syntax change appears necessary.
  - Support below five concurrent mixed callers is proposed.
  - Any live lock stealing or network broker surface is proposed.
  - A latency tradeoff would make interactive calls materially slower.
- Stop without changing files when:
  - Requirements/design/review artifacts disagree on accepted behavior.
  - Managed repo implementation would occur in the base worktree without an isolated task worktree.
  - A plan requires weakening PGLite locking or erasing MCP remote semantics.
- Mark the goal blocked only when:
  - The same blocking condition repeats for the required goal-turn threshold and meaningful progress is impossible without user input or external state.
- Mark the goal complete only when:
  - Every sequence requirement and final production-readiness gate are complete; for this slice, do not mark the requirement complete until implementation-brake `[SHIP]`, closeout, and direct AC evidence are recorded.

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
