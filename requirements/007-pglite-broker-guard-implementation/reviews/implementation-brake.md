# Implementation Brake: PGLite Broker Guard Implementation

Created: 2026-06-21 KST
Mode: recent diff review + requirement conformance self-review
Verdict: [SHIP]

## Implementation Under Review

Requirement 007 implements live-owner PGLite broker/guard behavior for the accepted 468-row inventory:

- owner-routed operation dispatch for local CLI, `gbrain call`, stdio MCP, and HTTP MCP-safe surfaces
- curated owner-side CLI command adapters with stdout/stderr/exitCode capture
- typed fail-fast guards for maintenance, lifecycle, daemon/session, schema/reset, local-only remote, corrupt lock, owner-starting, missing socket, and completion-unknown paths
- inventory/policy parity and row-id keyed representative coverage

Acceptance basis: `requirements/007-pglite-broker-guard-implementation/requirements.md`, requirement 006 inventory, implementation evidence, representative manifest, and coverage ledger closure.

## Findings

No must-fix findings.

Non-blocking follow-ups:

- Requirement 008 still owns the repeated N-attempt named matrix and must not treat requirement 007 representative evidence as final all-row proof.
- Requirement 009 should decide whether public docs/help/changelog need operator recovery guidance for `maintenance_deferred` and owner-broker typed errors.

## What Must Be Fixed Now

None.

## Open Blockers

None for requirement 007 implementation-brake.

Requirement conformance reviewer accounting:

- `conformance_result_status`: CONFORMANT via `FALLBACK_SELF_REVIEW_USED`
- Fallback reason: the available subagent tool policy says not to spawn subagents unless the user explicitly asks for subagents/delegation. This requirement is not the final production-readiness slice; requirement 009 remains the production gate.
- AC coverage summary:
  - AC1 inventory consumed: `test/pglite-owner-policy.test.ts`, inventory validator, regenerated inventory counts 217 / 223 / 28.
  - AC2 broker-success reads: `gbrain call list_pages`, direct operation CLI, stdio MCP proxy, HTTP MCP tests, representative manifest.
  - AC3 serialized owner mutation: `config set`, `auth`, cache/command-family/one-shot adapter tests and owner-engine seams.
  - AC4 typed guards: maintenance, lifecycle/heavy/session, corrupt lock, owner-starting, local-only remote, missing socket, and completion-unknown tests.
  - AC5 trust boundary: dispatch and HTTP tests reject localOnly remote paths; stdio proxy omits localOnly operation rows.
  - AC6 owner states: live, no-owner, dead/stale, corrupt/unknown, missing socket, owner-starting, completion-unknown, and stdio proxy states covered.
  - AC7 public compatibility: command syntax preserved; IPC extension is additive protocol v1; HTTP/MCP envelope tests pass.
  - AC8 expected-red replacement: former raw-timeout representatives now broker or typed-guard without raw lock/connect text.
  - AC9 class-complete targeted coverage: representative manifest validates all required dimensions; requirement 008 owns final repeated matrix.
  - AC10 handoff: evidence/progress/ledger record residual requirement 008 and 009 obligations.
- Unresolved conformance findings: none.
- Residual risk handling: representative implementation proof is intentionally bounded; repeated all-row proof and production/public docs are reserved for requirements 008 and 009.

## What Can Be Deferred

- A single packaged script for the fast feedback loop can wait for requirement 008 if the matrix runner needs it.
- Public docs/help/changelog updates can wait for requirement 009 production readiness, where operator recovery language belongs.

## Verification Result

- `bun test test/cli-pglite-operation-broker.test.ts` -> 51 pass, 420 expectations.
- `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 2498 expectations.
- `bun run typecheck` -> pass.
- `bun test test/pglite-broker-representative-coverage.test.ts test/pglite-owner-policy.test.ts` -> 2 pass, 1953 expectations.
- `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> ok.
- `python3 scripts/coverage_ledger.py validate --mode closure --requirement-dir requirements/007-pglite-broker-guard-implementation` -> pass.

## UltraQA Matrix Result

Triggered because the implementation changes stateful CLI/service IPC, owner queueing, trust boundaries, and operator-facing typed errors.

| ID | Scenario | Expected signal | Actual result | Evidence | Cleanup |
| --- | --- | --- | --- | --- | --- |
| U1 | Concurrent owner-side CLI adapters mutate global cwd/stdout capture | Requests are serialized before monkeypatching can overlap | Pass; IPC server awaits one queued handler at a time | `src/core/pglite-operation-ipc.ts`, full broker suite | temp homes removed by tests |
| U2 | Live lock with missing owner socket | No direct PGLite open; typed owner_unreachable | Pass | `second stdio MCP proxy returns owner_unreachable`; CLI owner_unreachable test | temp homes removed |
| U3 | Corrupt lock file | No lock deletion/direct open; typed lock_safety_blocked | Pass | corrupt lock CLI and stdio tests | temp homes removed |
| U4 | Remote localOnly operation | Rejected before handler/filesystem execution | Pass | dispatch and HTTP localOnly tests | no external state |
| U5 | Lifecycle/session/heavy command under live owner | Nonzero bounded maintenance_deferred, no raw lock text | Pass | 12 typed-guard representative tests | temp homes removed |
| U6 | Broker accepts but times out | completion_unknown, not misleading success | Pass | completion_unknown test | temp homes removed |
| U7 | Public compatibility | Syntax/envelopes remain stable | Pass | MCP, HTTP, IPC, direct CLI tests | no external state |

No relevant matrix row failed, skipped without justification, or left debris.

## Ship-Readiness Verdict

[SHIP]

Requirement 007 implementation is ready for closeout. The only remaining obligations are workflow gates: closeout and sequence handoff to requirement 008 for the full repeated matrix, then requirement 009 for production readiness.
