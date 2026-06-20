# Secondary Plan: PGLite Priority Scheduler

## Status

accepted

## Execution Worktree

`/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`

## Change Set

- `src/cli.ts`
  - add `PGLITE_MAINTENANCE_COMMANDS`
  - add `maybeDeferPgliteMaintenanceCommand()`
  - call it before `connectEngine()` for DB-bound CLI-only commands
- `test/cli-pglite-operation-broker.test.ts`
  - add real command fallback tests for `sync`, `embed`, `extract`
  - add startup-election-held fallback test
  - add corrupt-lock maintenance fallback test
  - add no-owner direct-open smoke evidence or cite existing evidence

## Required Behavior

- Live PGLite owner + second `sync`/`embed`/`extract`: return `maintenance_deferred`, non-zero, no raw lock timeout, no queued/completed wording.
- Startup election held + second maintenance command: return `owner_starting`, non-zero, no raw lock timeout.
- Corrupt/unknown lock + maintenance command: return `lock_safety_blocked`, non-zero, no raw lock timeout.
- No owner: command reaches its existing direct path.
- Interactive `query`/`search`/`think`: existing owner broker behavior remains green.

## Verification

1. Red test for maintenance fallback before implementation.
2. Green targeted tests after implementation.
3. Full related requirement 002/003 suite:

```bash
bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000
bun run typecheck
```
