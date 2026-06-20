# Secondary Plan: PGLite Concurrency Verification

Primary plan: [plan.md](plan.md)
Plan id: `004-pglite-concurrency-verification`
Created: 2026-06-20
Last updated: 2026-06-20

## Why This Approach

- Chosen direction: add a focused real-subprocess serial E2E plus targeted command-level regression tests and docs updates.
- Why it fits the stated goal: requirements 001-003 already built the behavior; requirement 004 needs trustworthy evidence and operator-facing documentation, not a new broker architecture.
- Rejected alternatives:
  - Reusing injected socket/fake-owner tests as final proof: insufficient for AC1/AC2.
  - Building a new mandatory daemon: outside user-confirmed constraints.
  - Queuing maintenance commands through the broker: outside requirement 004 and contradicted by requirement 003.
- Assumptions that must hold:
  - The task worktree baseline includes requirement 003 commit `8a23554a`.
  - Real subprocess tests can run hermetically with local PGLite, no DB env, and no provider keys.
  - `think` without keys can still be used as route/no-lock evidence if the test separately proves proxy/owner routing.
- Evidence still needed before implementation:
  - None blocking after plan/design reconciliation; code/test/docs inspection remains part of implementation.

## RALPLAN-DR Summary

- Principles:
  - Prove real owner/proxy routing positively; do not treat absence of lock text as success.
  - Keep PGLite lock safety stronger than convenience; never force-delete live/unknown locks.
  - Separate evidence levels: real subprocess E2E, command-level integration, IPC/unit, and docs.
  - Preserve public CLI/MCP surfaces and command syntax.
  - Keep maintenance behavior described as deferred, not queued/executed.
- Decision drivers:
  - User-confirmed minimum: at least five simultaneous MCP/CLI callers without PGLite lock timeout.
  - AC2 requires multiple stdio MCP processes, not only CLI callers.
  - AC3/AC4 require bounded, observable, privacy-safe recovery statuses.
  - Tests must run without external services or API keys.
- Viable options:
  - One comprehensive serial E2E plus existing targeted tests: best fit; proves integrated topology while containing flake/cost.
  - Many real-subprocess recovery E2Es: stronger realism but too slow and duplicates lower-level deterministic tests.
  - Injected-socket-only proof: fast but invalid for requirement 004.
- Alternatives rejected or invalidated:
  - Accepting deterministic proxy error envelopes as AC1/AC2 success: invalid because `owner_unreachable` can mean the owner socket never existed.
  - Omitting README updates: invalid because a direct stale contradiction is known.
  - Treating `owner_starting`/`maintenance_deferred` as broker statuses: invalid because code owns them as CLI preflight statuses.
- Premortem for high-risk plans:
  - E2E passes against Postgres or thin-client due to ambient env: clear DB env and assert config `engine: pglite`.
  - E2E passes while second server is not a proxy: assert owner socket readiness and proxy-only `tools/list`.
  - E2E passes on empty/keyless failures: require seeded marker result for `query`/`search` and classify `think` narrowly.
- Expanded test plan for high-risk plans:
  - Unit: existing PGLite lock and IPC status tests.
  - Integration: strengthen CLI broker tests for stale-lock direct-open, post-timeout queue health, startup status, and privacy diagnostics.
  - E2E or browser/manual: add `test/pglite-concurrent-access.serial.test.ts`.
  - Observability/operator evidence: docs status/action table and closeout evidence matrix.

## ADR

- Decision: Requirement 004 will close by adding one real-subprocess owner/proxy E2E, strengthening command-level diagnostics/recovery tests where needed, and aligning docs.
- Drivers: real subprocess proof is explicitly required; existing injected tests are valuable but insufficient; docs currently contain stale guidance.
- Alternatives considered: fake-owner proof, broader architecture change, full maintenance queue, many E2E recovery tests.
- Why chosen: this keeps the slice narrow while proving the user-visible concurrency contract.
- Consequences: the serial test may be slower, but it buys confidence in the exact local PGLite/MCP/CLI topology users hit.
- Follow-ups: requirement 005 owns production readiness; any future maintenance queue requires a new requirement.

## Implementation Guardrails

- Required implementation constraints:
  - Use task worktree `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`.
  - Add/modify tests before production code unless a doc-only/test-only change already satisfies the requirement.
  - Clear `DATABASE_URL`, `GBRAIN_DATABASE_URL`, provider keys, and unrelated source/auth env in subprocess fixtures unless deliberately testing those fields.
  - Assert PGLite config before real owner/proxy E2E.
  - Assert proxy mode via `tools/list` and live owner operation socket.
  - Treat `owner_unreachable`, `broker_timeout`, and `completion_unknown` as AC1/AC2 E2E failures.
  - Label `think` evidence as broker/proxy route evidence, not synthesis quality evidence.
  - Keep local socket paths allowed only as explicit local operator diagnostics; do not leak user content/auth/request params.
- Allowed implementation freedom:
  - Exact helper function names and timeout budgets.
  - Whether stale-lock command-level recovery is added to an existing test or a new focused test in the same file.
  - Exact wording of docs, provided behavior and status ownership are accurate.
- Likely mistake points:
  - Letting the serial test pass on no-result/no-error alone.
  - Forgetting MCP proxy `search`.
  - Updating architecture docs but leaving README stale.
  - Presenting maintenance deferral as queued broker work.
  - Treating a lock primitive test as command-level direct-open proof.
- Boundaries not to cross:
  - No network broker.
  - No mandatory daemon.
  - No public command syntax change.
  - No live/unknown lock deletion shortcut.
  - No external API/service dependency in tests.
- Existing behavior that must not regress:
  - No-owner direct-open for `query`, `search`, and `think`.
  - Source/auth preservation for MCP proxy requests.
  - Maintenance commands defer under live owner.
  - Corrupt/unknown lock returns safety status.
- Decisions the implementer must not reopen:
  - Requirement 004 is verification/docs, not maintenance execution.
  - PGLite only.
  - Existing public command syntax remains unchanged.
- Details that belong in `requirements.md` or `contracts.md` instead:
  - Product acceptance criteria remain in requirement 004.
  - This secondary plan only preserves implementation guardrails and review reconciliation.
- Executable contract compatibility findings:
  - Operation broker vocabulary is `query | search | think`; tests/docs must not imply other operations are broker-executed.
  - Second stdio MCP proxy exposes the filtered operation set only.
- Required legal executable contract evidence:
  - Code/tests should rely on actual `tools/list`, CLI command execution, and IPC response statuses, not manually assumed operation names.
- Drift checks against `plan.md` and the compressed Codex plan:
  - `plan.md`, this secondary plan, technical design, and requirement 004 all agree after review reconciliation.

## Files To Inspect

- `src/cli.ts`: CLI broker forwarding, maintenance deferral, startup-election behavior, and status emission.
- `src/mcp/server.ts`: owner/proxy server behavior and proxy tool surface.
- `src/core/pglite-operation-ipc.ts`: operation vocabulary, queueing, timeout, stale socket diagnostics.
- `src/core/pglite-lock.ts`: live/stale/corrupt lock classification.
- `test/e2e/pglite-cli-exit.serial.test.ts`: hermetic subprocess fixture pattern.
- `test/cli-pglite-operation-broker.test.ts`: command-level broker/status tests to extend.
- `test/pglite-operation-ipc.test.ts`: IPC status/recovery tests.
- `test/pglite-lock.test.ts`: lock safety tests.
- `docs/architecture/serve-sync-concurrency.md`: main stale doc.
- `docs/ENGINES.md`: engine concurrency table and broker narrative.
- `README.md`: known stale troubleshooting note.

## Tests To Run Or Add

- Add `test/pglite-concurrent-access.serial.test.ts`: proves real subprocess owner/proxy mixed concurrency, proxy mode, seeded marker results, no raw lock timeout, and post-teardown re-entry.
- Run `bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000`: proves new E2E.
- Run `bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000`: proves regression matrix.
- Run `bun run typecheck`: proves TS compile health.
- Likely failure interpretation:
  - E2E `owner_unreachable`: owner socket/proxy readiness bug or test startup race.
  - Empty marker result: seed/sync failed or result assertion too loose.
  - Stale lock after teardown: cleanup or process lock release bug.
  - Privacy sentinel leak: sanitize status/error messages before closeout.
- Minimum verification before handoff:
  - Targeted serial test pass, related suite pass, typecheck pass, conformance/implementation-brake pass.

## Review Notes

- Decision brake: not used; direction was already fixed by accepted sequence requirements.
- Plan design review: not required; no UI.
- Plan UX review: not required separately; operator-facing clarity handled by DevEx and scenario review.
- Plan DevEx review: `GO WITH CHANGES`; README update, status/action docs, and `think` evidence classification accepted.
- Plan engineering review: `GO WITH CHANGES`; proxy `search`, positive proxy proof, stale-lock direct-open evidence, privacy diagnostics, and status ownership accepted.
- Scenario review: `[SCENARIOS MISSING]`; all implementation-changing missing scenarios reconciled.
- Open review risks: E2E flake from subprocess startup; mitigate with bounded waits for actual socket/readiness evidence rather than sleeps alone.

## Conversation Details To Preserve

- User constraints:
  - PGLite only.
  - Important target is gbrain behavior.
  - Multiple callers must queue/serve without lock errors.
  - `query`/`search`/`think` are prioritized over `sync`/`embed`/`extract`.
  - Public commands remain unchanged.
  - No owner daemon means CLI may directly open DB.
  - At least five simultaneous MCP/CLI callers without PGLite lock timeout.
- Rejected ideas:
  - Mandatory daemon.
  - Network-facing broker.
  - Maintenance queued/executed through broker in this slice.
- Context likely to disappear during compression:
  - Requirement 004 exists to prove and document requirements 001-003, not to redesign them.
  - Requirement 005 still owns final production readiness after this requirement closes.

## Handoff Checklist

- [x] Primary plan, secondary plan, and compressed Codex plan agree.
- [x] Any conflict between this document, `plan.md`, and the compressed Codex plan has been reconciled before editing.
- [ ] Required files have been inspected before editing in task worktree.
- [ ] Implementation stays inside the listed guardrails.
- [x] Implementation details in this document are required constraints, not incidental coding choices.
- [ ] Required tests have been added or run.
- [x] Review notes have been addressed or explicitly deferred.
- [x] No new decisions were introduced without updating this document.
