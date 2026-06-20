# Technical Design: PGLite Concurrency Verification

## Status

Complete.

## Requirement

- Source: `requirements/004-pglite-concurrency-verification/requirements.md`
- Research: `requirements/004-pglite-concurrency-verification/research.md`
- Date: 2026-06-20

## Goals

- Prove the owner-broker behavior with real gbrain subprocesses.
- Preserve and cite existing diagnostic/unit coverage without overclaiming it as E2E.
- Update stale docs to match the implemented interactive broker plus maintenance deferral contract.

## Non-Goals

- Do not add new production broker behavior unless a test exposes a real bug.
- Do not add a network broker, mandatory daemon, raw SQL forwarding, or maintenance execution queue.
- Do not require API keys, Postgres, Docker, or real user brain data.

## Test Architecture

Add `test/pglite-concurrent-access.serial.test.ts`.

### Fixture setup

Use the same shape as `test/e2e/pglite-cli-exit.serial.test.ts`:

- `REPO_ROOT = resolve(import.meta.dir, '..')`
- create `test/.cache/gbrain-pglite-concurrent-shim.sh`
- shim body: `exec bun run "<repo>/src/cli.ts" "$@"`
- create temp `GBRAIN_HOME`
- create temp git source repo with two markdown pages
- clear inherited embedding/provider API keys from subprocess env
- clear `DATABASE_URL` and `GBRAIN_DATABASE_URL` for every subprocess
- run:

```bash
gbrain init --pglite --repo <source> --no-embedding --yes
gbrain sync --repo <source> --no-pull --no-embed --no-extract --yes --no-hard-deadline
```

Seeded pages should include deterministic keyword text so `query` and `search` produce stable local results without embeddings or API keys.
The fixture must assert the loaded config is `engine: pglite` before the
subprocess owner/proxy section starts.

### JSON-RPC helpers

Implement helpers local to the test file:

- `spawnGbrain(args, opts?)`
- `runCli(args, timeoutMs)`
- `startStdioServer(label)`
- `sendJson(child, message)`
- `waitForJsonLine(child, id, timeoutMs)`
- `listTools(child)`
- `initializeMcp(child)`
- `callTool(child, id, name, args)`
- `killChild(child)`
- `expectNoRawPgliteLockFailure(text)`

Each spawned process must have:

- bounded response wait
- captured stdout/stderr
- cleanup in `afterEach`/`afterAll`
- `SIGTERM` first, `SIGKILL` fallback if it does not exit

### Real owner/proxy flow

Test: `real stdio owner and proxy serve five mixed CLI/MCP callers without PGLite lock timeout`.

1. Start owner: `gbrain serve` stdio.
2. Complete JSON-RPC initialize and initialized notification.
3. Wait for a live PGLite lock and `.gbrain-operation.sock`; failing to observe
   the operation socket fails the E2E instead of falling back to a loose
   "no lock timeout text" assertion.
4. Start proxy: second `gbrain serve` stdio.
5. Complete JSON-RPC initialize and initialized notification.
6. Assert proxy mode via `tools/list`: the second server should expose only the
   proxy operation set `query`, `search`, and `think`.
7. Send three MCP calls through proxy:
   - `query`
   - `search`
   - `think`
8. Concurrently launch at least three CLI calls:
   - `query`
   - `search`
   - `think --json`
9. Await all six or more calls.
10. Assert:
   - every process/call resolves within bounded time
   - no stdout/stderr/result contains `Timed out waiting for PGLite lock` or `Could not acquire PGLite lock`
   - proxy `query` or `search` and CLI `query` or `search` return the seeded marker, proving served owner results
   - proxy `think` returns a preserved MCP result/error envelope from the proxy while the owner/proxy window is live
   - `owner_unreachable`, `broker_timeout`, and `completion_unknown` are failures for this AC1/AC2 E2E and belong only in separate recovery-matrix tests
   - any accepted keyless/no-result `think` output is classified as route/no-lock evidence, not answer-quality evidence
11. Terminate proxy and owner, then run a fresh direct-open CLI `query` or start
    a fresh owner and assert no raw lock timeout or stale `owner_unreachable`.

This test satisfies AC1 and AC2 as `real_subprocess_e2e`. It also supplies
post-teardown re-entry evidence, but command-level stale-lock recovery remains
covered separately.

### Additional command-level regression coverage

Extend existing tests rather than the expensive serial E2E when practical:

- Add or cite command-level no-owner direct-open coverage for `query`,
  `search`, and `think`.
- Add command-level dead/stale PGLite lock recovery evidence where a normal
  direct-open command succeeds after stale lock classification.
- Extend `completion_unknown` coverage with a later same-broker request after
  the original handler releases, proving the queue continues serving.
- Add interactive startup-election coverage: a `query`/`search`/`think` caller
  arriving while operation startup is held must return a deterministic
  operator-facing status, currently `owner_unreachable`, without raw PGLite lock
  timeout. `owner_starting` remains a maintenance preflight status unless
  production code changes it explicitly.
- Broaden privacy-safe diagnostic assertions beyond private query text to cover
  request params, source/federated env sentinels, MCP auth material, and the
  maintenance/status paths. Local filesystem socket paths in explicit
  `stale_socket_recovered` diagnostics are allowed as local operator debugging
  context; user brain content and auth material are not.

## Existing Diagnostic Evidence

Keep and rerun these existing tests:

- `test/pglite-operation-ipc.test.ts`
  - stale operation socket recovery -> `stale_socket_recovered`
  - queue priority and timeout semantics
- `test/pglite-lock.test.ts`
  - live heartbeat non-steal
  - dead/stale lock recovery
  - corrupt lock classification
- `test/cli-pglite-operation-broker.test.ts`
  - `owner_unreachable`
  - `completion_unknown`
  - post-timeout queue usability
  - `lock_safety_blocked`
  - `owner_starting`
  - `maintenance_deferred`
  - no-owner direct-open command behavior
  - dead/stale lock direct-open recovery
  - MCP source/auth preservation
  - broker/status diagnostics avoid private request/auth/source echo

Do not move these into the new serial E2E file unless needed.

## Documentation Updates

### `docs/architecture/serve-sync-concurrency.md`

Replace the stale blanket "stop serve before a large sync" framing with:

- PGLite remains single-owner.
- Interactive `query`/`search`/`think` can route through a live CLI or stdio MCP owner.
- Multiple stdio MCP servers can coexist because secondary servers proxy interactive operations.
- `sync`/`embed`/`extract` are not broker-executed in this sequence; they return `maintenance_deferred` under a live owner.
- Operators may still stop long-running owners before large maintenance work if they want the maintenance command to run immediately.
- Include status vocabulary and recovery hints.
- Preserve status ownership:
  - broker/IPC statuses: `served`, `owner_unreachable`,
    `completion_unknown`, `lock_safety_blocked`, `stale_socket_recovered`
  - CLI preflight maintenance statuses: `owner_starting`,
    `maintenance_deferred`

### `docs/ENGINES.md`

Update the concurrency table row that says maintenance forwarding/yield is tracked separately. It should instead say maintenance commands are deferred under a live owner in the current contract.

### `README.md`

Update the troubleshooting section that still gives blanket "stop
`gbrain serve` before a large sync" guidance. The new copy should preserve the
large-maintenance advice while making clear that interactive
`query`/`search`/`think` callers route through the local owner broker.

Search MCP docs for directly contradictory language and update only when directly stale.

## Evidence Matrix For Closeout

Closeout must include:

| Behavior | Evidence type | Required path |
| --- | --- | --- |
| five mixed CLI/MCP callers with real owner/proxy | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` |
| second stdio MCP proxy against live owner | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` |
| post-teardown re-entry after real owner/proxy | `real_subprocess_e2e` | `test/pglite-concurrent-access.serial.test.ts` |
| stale operation socket recovery | `ipc_unit` | `test/pglite-operation-ipc.test.ts` |
| dead/stale lock recovery and live non-steal | `ipc_unit` | `test/pglite-lock.test.ts` |
| no-owner and stale-lock direct-open command behavior | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` |
| owner unreachable / completion unknown / safety statuses | `command_level_integration` | `test/cli-pglite-operation-broker.test.ts` |
| docs aligned | `doc_update` | `docs/architecture/serve-sync-concurrency.md`, `docs/ENGINES.md`, `README.md` |

## Verification Commands

```bash
bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000
bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000
bun run typecheck
```

## Risks And Mitigations

- Risk: spawned stdio servers linger after failure.
  - Mitigation: central child registry, `afterEach` cleanup, SIGTERM then SIGKILL fallback.
- Risk: `think` depends on API keys.
  - Mitigation: use keyless behavior already covered by current CLI tests; accept deterministic no-key/no-result behavior only if no lock timeout occurs.
- Risk: E2E is slow.
  - Mitigation: serial file with one shared initialized PGLite brain.
- Risk: docs overclaim maintenance queuing.
  - Mitigation: explicitly say maintenance is deferred, not queued/executed.

## Open Questions

None blocking.
