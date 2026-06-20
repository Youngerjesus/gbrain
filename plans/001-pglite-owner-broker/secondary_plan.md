# Secondary Plan: PGLite Owner Broker

Primary plan: [plan.md](plan.md)
Codex proposed plan link: current goal-requirements sequence
Plan id: `001-pglite-owner-broker`
Created: 2026-06-20
Last updated: 2026-06-20

## Why This Approach

- Chosen direction: implement user-observable PGLite concurrency with a single local owner broker, not direct multi-process PGLite access.
- Why it fits the stated goal: PGLite remains single-owner safe while CLI/MCP callers queue or are served without normal lock timeout failures.
- Rejected alternatives: weakening the file lock, waiting for `acquireLock()` timeout then falling back, generic SQL-over-IPC, mandatory user-started daemon, and first-slice HTTP MCP support.
- Assumptions that must hold: local Unix sockets are available; actual SQL serialization is acceptable; existing dispatch/CLI seams can be extracted without changing public command syntax.
- Evidence still needed before implementation: isolated worktree preflight, tests proving broker routing, second MCP stdio proxy, lock classifier behavior, race/recovery paths, privacy-safe diagnostics, and focused verification output.

## RALPLAN-DR Summary

- Principles:
  - Preserve one PGLite opener per file-backed data directory.
  - Route before `connectEngine()` whenever a live owner may exist.
  - Keep MCP remote/source semantics and CLI local trust semantics explicit.
  - Prefer typed local IPC with injected handlers over upward imports or raw SQL.
  - Prove broker routing positively; absence of lock timeout strings is insufficient.
- Decision drivers:
  - User asked for queue/serve concurrency, not unsafe PGLite parallel access.
  - Current lock timeout happens before normal operation dispatch.
  - MCP stdio startup differs from CLI operation startup.
  - Recovery and diagnostics must be privacy-safe and actionable.
- Viable options:
  - Local operation broker with pre-connect routing: more work, but satisfies lock safety and caller compatibility.
  - Post-lock fallback: smaller diff, but preserves user-visible lock waits and fails AC1/AC3.
  - Require Postgres or manual daemon: operationally simpler, but outside accepted PGLite-only/no syntax-change requirement.
- Alternatives rejected or invalidated:
  - Direct multi-process PGLite: violates storage safety.
  - Reusing retrieval-reflex IPC as a generic op channel: wrong ownership; that protocol is intentionally narrow.
  - First-slice `serve --http`: scope creep without accepted HTTP owner binding/tests.
- Premortem for high-risk plans:
  - Five-caller test passes without broker routing: require request id/owner pid/status evidence.
  - Broker timeout later mutates state: require completion phase status and no auto-retry for mutating `think`.
  - Cold-start race recreates lock timeout: require no-owner thundering-herd test.
  - Owner proxy preserves source incorrectly: require `GBRAIN_SOURCE` and federated-read tests.
- Expanded test plan for high-risk plans:
  - Unit: IPC protocol, queue ordering, lock classifier, status matrix, privacy sentinel, injected handler boundary.
  - Integration: live-owner CLI, second MCP stdio proxy, trust/source, owner failure phases, cold-start race.
  - E2E or manual: synthetic PGLite brain only; five mixed callers; no private content.
  - Observability/operator evidence: docs and deterministic diagnostics for queued, served, timeout, unknown completion, lock-safety block.

## ADR

- Decision: Add a local PGLite operation owner broker with CLI/MCP stdio pre-connect forwarding and a non-acquiring lock classifier.
- Drivers: PGLite single-owner safety, existing user-visible lock timeouts, unchanged CLI syntax, MCP trust boundary, and at least five concurrent callers.
- Alternatives considered: weaken lock, post-timeout fallback, generic SQL IPC, manual daemon requirement, Postgres-only recommendation.
- Why chosen: It is the only path that moves normal concurrent use away from lock timeouts while preserving accepted safety and compatibility constraints.
- Consequences: More moving parts in CLI/MCP startup; stronger tests required; later scheduler slice must complete real maintenance command priority.
- Follow-ups: requirements/003-pglite-priority-scheduler for `sync`/`embed`/`extract`; production-readiness gate for launch verdict.

## Implementation Guardrails

- Required implementation constraints:
  - `pglite-operation-ipc` owns transport/queue/protocol only and receives an injected owner handler.
  - Lock classifier is non-acquiring, non-stealing, and does not wait through `acquireLock()`.
  - Second MCP stdio process must choose proxy mode before direct PGLite open when a live owner is detected.
  - CLI-only `think` must have a concrete pre-connect forwarding seam.
  - Completion-unknown and broker-timeout behavior must be phase-aware.
  - Mutating local CLI `think --save/--take` must not auto-retry after ambiguous completion.
  - Diagnostics must not include raw query text, page content, file content, or sensitive params.
- Allowed implementation freedom:
  - Exact TypeScript type names and helper placement, if dependency direction and tests hold.
  - Exact deterministic diagnostic wording, if tests assert status/category/next action and privacy.
  - Whether the owner handler adapter lives in `mcp/server.ts` or an adjacent MCP module.
- Likely mistake points:
  - Letting a second `gbrain serve` call `connectEngine()` before proxy decision.
  - Treating socket unavailable as safe direct-open without lock classification.
  - Reconstructing source scope from owner env instead of caller context.
  - Treating no timeout string as enough evidence.
  - Auto-retrying ambiguous mutating `think`.
- Boundaries not to cross:
  - Do not weaken live heartbeat lock protection.
  - Do not add network broker surfaces.
  - Do not add `serve --http` support in this slice unless requirements/design are updated first.
  - Do not publicly claim real `sync`/`embed`/`extract` forwarding in requirement 001.
- Existing behavior that must not regress:
  - No-owner direct-open CLI behavior.
  - `gbrain query/search/think` command syntax.
  - MCP `remote=true`, takes allow-list, source/federated-read scope, and remote persistence blocking.
- Decisions the implementer must not reopen:
  - Single-owner broker instead of direct PGLite concurrency.
  - Local-only typed IPC, not raw SQL.
  - Positive broker-routing evidence is required.
- Details that belong in `spec.md` or `contracts.md` instead:
  - Durable public docs for future HTTP or maintenance command broker extensions.
- Executable contract compatibility findings:
  - Broker request fields must match actual handler inputs; free-form schema prose is not sufficient.
  - Status enums used by tests/docs must match code-owned constants.
- Required legal executable contract evidence:
  - Type-level request/response schema or runtime validator.
  - Tests for every status and caller context field used in dispatch.
- Drift checks against `plan.md` and the compressed Codex plan:
  - If `plan.md` omits a scenario from `scenario-brake.md`, update `plan.md` before coding.

## Files To Inspect

- `src/core/pglite-lock.ts`: lock heartbeat, steal-grace, and classifier placement.
- `src/core/context/resolve-ipc.ts`: local IPC framing precedent.
- `src/mcp/server.ts`: stdio server startup, source scope, remote dispatch, resolve IPC binding.
- `src/mcp/dispatch.ts`: MCP context contract and result envelope.
- `src/cli.ts`: pre-connect command flow, CLI_ONLY handling, query/image transform, formatting.
- `src/commands/think.ts`: parse/render extraction target and local save/take behavior.
- `src/commands/search.ts`: free-text vs dashboard subcommand behavior.
- `src/core/operations.ts`: query/search/think operation contracts and `operationsByName`.
- `test/context/resolve-ipc.test.ts`, `test/pglite-lock.test.ts`, `test/e2e/pglite-cli-exit.serial.test.ts`: test patterns to reuse.

## Tests To Run Or Add

- Add broker unit tests: IPC framing, statuses, queue ordering, injected handler, privacy sentinel.
- Add lock classifier tests: absent/live/dead/corrupt/unknown, no acquire/no wait/no live steal.
- Add CLI tests: direct-open fallback, live-owner forwarding, CLI-only `think`, `query --image`, free-text `search`.
- Add MCP tests: second stdio proxy startup, brokered tool calls, trust/source/federated read, remote `think` persistence blocking.
- Add concurrency tests: live-owner five mixed callers and no-owner five-caller cold-start race.
- Add recovery tests: owner dies by phase, partial response, permission/not-yet-bound socket, race-safe stale socket cleanup.
- Add queue tests: synthetic maintenance-class request behind/ahead of interactive and long `think` boundedness.
- Minimum verification before handoff: focused `bun test` set covering all new/changed tests plus any repo guard touched by docs/scripts.

## Review Notes

- Decision brake: not separately run; research/design rejected unsafe direct-PGLite alternatives.
- Plan design review: not required; no UI.
- Plan UX review: GO WITH CHANGES; exact status matrix, timeout semantics, and operator evidence required.
- Plan DevEx review: GO WITH CHANGES; worktree setup, error contract, docs, and CLI parity required.
- Plan engineering review: GO WITH CHANGES; all companion findings accepted and reflected.
- Scenario review: [SCENARIOS MISSING] before reconciliation; missing scenarios are now guardrails.
- Open review risks: implementation may still discover that `think` CLI extraction is larger than expected; keep command syntax unchanged and preserve local trust.

## Conversation Details To Preserve

- User constraints:
  - PGLite only.
  - gbrain behavior is the target.
  - Multiple callers queue/serve without lock error.
  - `query/search/think` priority over `sync/embed/extract`.
  - `gbrain query "x"` unchanged, including search and think forms.
  - Direct-open fallback allowed when no owner daemon exists.
  - At least five simultaneous MCP/CLI calls without PGLite lock timeout.
- Rejected ideas:
  - Unsafe PGLite direct multi-process access.
  - Manual daemon requirement.
  - Weakening/removing PGLite file lock.

## Handoff Checklist

- [x] Primary plan, secondary plan, and compressed Codex plan agree.
- [x] Any conflict between this document, `plan.md`, and the compressed Codex plan has been reconciled before editing.
- [ ] Required files have been inspected before editing.
- [ ] Implementation stays inside the listed guardrails.
- [x] Implementation details in this document are required constraints, not incidental coding choices.
- [ ] Required tests have been added or run.
- [x] Review notes have been addressed or explicitly deferred.
- [ ] No new decisions were introduced without updating this document.
