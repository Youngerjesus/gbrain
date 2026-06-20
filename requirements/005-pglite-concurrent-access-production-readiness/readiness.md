# Production Readiness: PGLite Concurrent Access

Date: 2026-06-20
Verdict: `[PRODUCTION READY]`
Launch boundary: local gbrain PGLite CLI and stdio MCP behavior in the task branch/worktree.
Task worktree: `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker`
Branch: `codex/001-pglite-owner-broker`

## Launch Boundary Reviewed

This readiness gate covers local PGLite behavior for:

- `gbrain serve` as the local owner process and second stdio MCP proxy process.
- `gbrain query`, `gbrain search`, and `gbrain think` as interactive callers.
- `gbrain sync`, `gbrain embed`, and `gbrain extract` only as bounded maintenance callers that defer under a live owner.
- Operator-facing docs and diagnostics for local PGLite contention.

This gate does not cover hosted deployment, remote MCP HTTP deployment, DNS,
OAuth application setup, payment/email/storage accounts, push, PR creation,
merge, publish, or release.

## Evidence Checked

- Requirement 001 closeout exists and records `[CLOSED_COMMITTED]` for the
  owner-broker contract, lock safety, trust/source preservation, and verification.
- Requirement 002 closeout exists and records `[CLOSED_COMMITTED]` for
  `query`, `search`, and `think` operation forwarding.
- Requirement 003 closeout exists and records `[CLOSED_COMMITTED]` for
  interactive priority and maintenance deferral behavior.
- Requirement 004 closeout exists and records `[CLOSED_COMMITTED]` with an AC8
  evidence matrix for real-subprocess E2E, recovery diagnostics, source/auth
  forwarding, stale-lock recovery, privacy diagnostics, and docs.
- Task worktree log contains the implementation commits:
  - `d50dc701 Add PGLite owner operation broker`
  - `3acdc5e6 Close PGLite operation forwarding`
  - `8a23554a Defer PGLite maintenance under live owner`
  - `89e3a094 Verify PGLite concurrent access`
- Requirement 005 post-draft reviewer returned `SHIP` with no findings.

## Verification Evidence

- `bun test test/pglite-concurrent-access.serial.test.ts --timeout 120000`
  - Result: 1 pass, 0 fail.
- `bun test test/cli-pglite-operation-broker.test.ts --timeout 60000`
  - Result: 27 pass, 0 fail.
- `bun test test/pglite-concurrent-access.serial.test.ts test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts test/mcp-stdio-source-scope.test.ts --timeout 60000`
  - Result: 103 pass, 0 fail.
- `bun run typecheck`
  - Result: `tsc --noEmit` passed.
- `bun run verify`
  - First result: failed 1/30 checks because `src/mcp/pglite-operation-dispatch.ts`
    imported `operations` without being listed in
    `scripts/check-operations-filter-bypass.sh`.
  - Root cause: the new local stdio owner-broker dispatch adapter was a safe
    direct importer, but the structural trust-boundary guard required an
    explicit allowlist rationale.
  - Fix: added `src/mcp/pglite-operation-dispatch.ts` to the guard allowlist
    with the rationale that IPC validates `query`/`search`/`think` only.
  - Final result: pass 30/30 checks, 0 failures.

## Readiness Findings

| Area | Classification | Evidence / rationale |
| --- | --- | --- |
| Deployment boundary | ready | Local CLI/stdio MCP branch readiness only; no hosted deploy required. |
| Build and verification | ready | Related suites, typecheck, and `bun run verify` passed after fixing the guard allowlist omission. |
| Migrations | ready | No new migration or schema bump is introduced by requirement 004/005. Existing owner-broker work uses local PGLite files and IPC state. |
| Data safety | ready | Live PGLite locks are not stolen; corrupt/unknown locks produce `lock_safety_blocked`; stale sockets are probed before cleanup. |
| Observability / diagnostics | ready | Status vocabulary is documented for `served`, `owner_unreachable`, `completion_unknown`, `lock_safety_blocked`, `owner_starting`, `maintenance_deferred`, and `stale_socket_recovered`. |
| Stability / recovery | ready | Owner unreachable, completion unknown, stale socket, stale lock, startup election, post-timeout queue reuse, and post-teardown direct-open paths are covered. |
| Performance / queue behavior | ready | IPC priority ordering keeps interactive requests ahead of lower-priority work; real-subprocess mixed caller smoke proves at least five interactive callers complete without raw PGLite lock timeout. |
| Security / privacy | ready | Stdio MCP source/auth context is preserved; diagnostic tests assert private sentinels are not echoed in failure surfaces. |
| Operator docs | ready | README, `docs/ENGINES.md`, and `docs/architecture/serve-sync-concurrency.md` describe interactive broker routing, maintenance deferral, and troubleshooting status vocabulary. |
| External dependencies | ready | No DNS, OAuth app, email, payment, storage, hosted service, or external account setup is required for this local PGLite behavior. |

## Required Internal Follow-Up Slices

None.

## External Handoff Items

None.

## Deferred Non-Goals

- True broker execution for `sync`, `embed`, and `extract`; current contract is
  deterministic maintenance deferral under a live owner.
- Multi-machine or networked PGLite ownership.
- Hosted remote MCP HTTP deployment readiness.
- Release publication, push, PR, merge, or changelog packaging.

## Residual Risk

The remaining risk is release-process risk, not local behavior readiness: full
project release still needs the repository's normal PR/release workflow and any
maintainer-selected broader CI gates. That is outside this sequence's accepted
launch boundary.

## Final Verdict

`[PRODUCTION READY]`

The PGLite concurrent-access sequence is ready for local gbrain CLI and stdio
MCP exposure. Sequence item 5 may be marked complete.
