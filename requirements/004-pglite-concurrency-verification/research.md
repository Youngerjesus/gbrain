# Research: PGLite Concurrency Verification

## Status

Complete.

## Requirement

- Source: `requirements/004-pglite-concurrency-verification/requirements.md`
- Gate: research
- Date: 2026-06-20

## Decision Summary

1. Add a new real-subprocess serial test file instead of treating existing injected-socket tests as E2E proof.
2. Use a hermetic `GBRAIN_HOME` plus a shell shim to run `bun run src/cli.ts`, following `test/e2e/pglite-cli-exit.serial.test.ts`.
3. Make a first real `gbrain serve` stdio process the PGLite owner, then start a second real `gbrain serve` stdio proxy and concurrent CLI callers.
4. Keep existing `test/cli-pglite-operation-broker.test.ts`, `test/pglite-operation-ipc.test.ts`, and `test/pglite-lock.test.ts` as regression/unit coverage for the named diagnostic matrix.
5. Update stale docs, especially `docs/architecture/serve-sync-concurrency.md`, to distinguish interactive brokered reads from maintenance deferral.

## Evidence Reviewed

| Source | Evidence | Finding | Confidence |
| --- | --- | --- | --- |
| `docs/TESTING.md` | Subprocess and env-coupled tests should use `*.serial.test.ts`; PGLite cold-starting tests are expensive and should not be in the parallel pool. | The real subprocess E2E should be a serial test file. | High |
| `test/e2e/pglite-cli-exit.serial.test.ts` | Existing shim pattern creates `test/.cache/gbrain-...-shim.sh`, runs `bun run src/cli.ts`, uses hermetic `GBRAIN_HOME`, temp git source, and seeded PGLite brain. | This is the repo-native pattern for real CLI subprocess PGLite tests. | High |
| `test/cli-pglite-operation-broker.test.ts` | Existing tests cover injected live locks/sockets, five mixed CLI/MCP callers through a fake owner, second stdio proxy, source/auth preservation, `owner_unreachable`, `completion_unknown`, `lock_safety_blocked`, `owner_starting`, and maintenance deferral. | Strong regression coverage exists, but AC1 explicitly needs a real owner process. | High |
| `test/pglite-operation-ipc.test.ts` | Existing tests cover IPC queue priority, stale socket recovery, startup election, dropped clients, and timeout status. | These are suitable named diagnostic matrix rows but are unit-level evidence. | High |
| `test/pglite-lock.test.ts` | Existing tests cover live heartbeat non-steal, dead/stale recovery, corrupt lock classification, and ownership-token protection. | These cover safe stale/dead lock recovery and live-lock preservation. | High |
| `src/mcp/server.ts` | A normal stdio owner starts `startPgliteOperationIpcServer()` after connecting PGLite; a second stdio process routes through `startMcpOperationProxyServer()` when it sees a live PGLite lock. | Real owner/proxy topology can be tested with two spawned `gbrain serve` processes. | High |
| `docs/ENGINES.md` | Already documents owner-broker routing for `query`/`search`/`think`, but a table row still says maintenance forwarding/yield is tracked separately. | Needs minor alignment with requirement 003 maintenance deferral. | Medium |
| `docs/architecture/serve-sync-concurrency.md` | Still tells PGLite users to stop `gbrain serve` before a large sync and does not explain brokered interactive calls or maintenance deferral. | This is stale operator guidance and should be updated. | High |

## Decisions

### D1. Use a new serial E2E-style unit test

Add a file such as `test/pglite-concurrent-access.serial.test.ts`.

Reasons:

- Real subprocess tests cold-start Bun and PGLite and are slower than normal unit tests.
- They mutate process-level env through subprocesses and run long-lived stdio servers.
- `docs/TESTING.md` explicitly keeps this class out of the parallel fast pool.

### D2. Use real `gbrain serve` for owner and proxy

The E2E proof should:

1. Create a hermetic temp `GBRAIN_HOME`.
2. Initialize a PGLite brain with no embedding/API dependency.
3. Seed or sync minimal local data if needed.
4. Start first `gbrain serve` stdio process and complete JSON-RPC initialize. This process owns PGLite and binds the operation broker.
5. Start second `gbrain serve` stdio process. It should observe the live PGLite lock and run as operation proxy instead of direct-opening.
6. Send MCP `query`/`search`/`think` through the second process while also launching CLI `query`/`search`/`think` subprocesses.
7. Assert all five or more callers complete or return deterministic broker output and no output contains raw PGLite lock timeout strings.

This is the most direct proof of the final user topology.

### D3. Keep diagnostic named cases split across evidence types

Not every diagnostic row needs to be duplicated in the real subprocess E2E. Existing narrower tests already cover some cases better:

- `stale_socket_recovered`: `test/pglite-operation-ipc.test.ts`
- dead/stale lock recovery and live heartbeat non-steal: `test/pglite-lock.test.ts`
- `owner_unreachable`, `completion_unknown`, `lock_safety_blocked`, `owner_starting`, and `maintenance_deferred`: `test/cli-pglite-operation-broker.test.ts`

Closeout must distinguish these as `ipc_unit` or `command_level_integration`, while the five-caller owner/proxy test is `real_subprocess_e2e`.

### D4. Update docs with a new split model

Docs should say:

- PGLite still has one DB owner.
- Interactive local `query`/`search`/`think` can route through the owner broker while a CLI or stdio MCP owner is live.
- A second stdio MCP server can act as a proxy for those interactive tools.
- Maintenance `sync`/`embed`/`extract` is not broker-executed in this sequence; under a live owner, the second maintenance caller is deferred with `maintenance_deferred`.
- For large maintenance work, the operator can still choose to stop long-running owners to let maintenance run, but this is no longer a blanket requirement for interactive reads.

## Requirement Impact

None. Research confirms the accepted requirement is implementable without changing scope.

## Open Questions

None blocking.

## Verification Obligations For Design

- Specify robust subprocess cleanup for both owner and proxy processes.
- Define JSON-RPC helper functions for initialize, notifications, tool calls, and response matching.
- Bound all subprocess waits.
- Use no API keys and no network.
- Include doc update paths in the plan.
- Rerun requirement 001-003 related tests plus the new serial E2E test and typecheck.
