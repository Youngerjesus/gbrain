# DevEx Live Audit: PGLite Broker Guard Implementation

Created: 2026-06-21 KST
Gate: devex-review
Verdict: PASS WITH NON-BLOCKING FOLLOW-UPS

## Target And Persona

- Surface under test: GBrain local CLI, stdio MCP proxy behavior, HTTP MCP localOnly filtering, owner IPC command adapters, and requirement-local verification artifacts for PGLite live-owner concurrency.
- Primary persona: GBrain maintainer or contributor implementing runtime changes without touching a real user brain.
- Canonical live proof path: run targeted Bun tests with temp homes and synthetic PGLite owner locks, then validate inventory/policy parity.

## Top Findings

1. P3 polish - Typed guard errors are stable and actionable enough for this slice, but they do not yet point to a docs page.
   - Evidence: `bun test test/cli-pglite-operation-broker.test.ts -t "typed-guard caller defers"` asserts `maintenance_deferred`, command name, nonzero exit, and no raw PGLite lock text.
   - Developer impact: contributors can assert the product boundary, but operators may still need prior context to know when to stop the owner versus retry later.
   - Recommended fix: during requirement 009 production readiness, decide whether public docs/help should mention live-owner guard behavior and recovery guidance.
   - Verification: docs/help/changelog check recorded in requirement 009 or closeout evidence.

2. P3 polish - The fast feedback loop is good, but not packaged as a single script.
   - Evidence: focused loop uses `bun test test/pglite-owner-policy.test.ts test/pglite-broker-representative-coverage.test.ts` plus inventory validation; full broker suite is still a separate command.
   - Developer impact: maintainers have exact commands, but a future contributor may need to copy several commands from evidence.
   - Recommended fix: leave as-is for requirement 007; consider a named script only if requirement 008 repeats the matrix often.
   - Verification: requirement 008 matrix runner covers the full repeated command set.

## TTHW Trace

GETTING STARTED AUDIT

Step 1: Run policy and representative coverage tests. Time: under 1 minute. Friction: low. Evidence: `bun test test/pglite-broker-representative-coverage.test.ts test/pglite-owner-policy.test.ts` -> 2 pass, 1953 expectations.
Step 2: Validate inventory schema/classes. Time: under 1 minute. Friction: low. Evidence: `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> ok.
Step 3: Run full broker behavior suite. Time: about 38 seconds. Friction: medium due migration noise but deterministic. Evidence: `bun test test/cli-pglite-operation-broker.test.ts` -> 51 pass, 420 expectations.

TOTAL: 3 steps, under 3 minutes, final state green targeted implementation proof.

## DX Scorecard

DX LIVE AUDIT - SCORECARD

Dimension              Score   Evidence                                  Method
Getting Started        8/10    focused tests + validator under 3 min      TESTED
API/CLI/SDK            8/10    public command syntax unchanged            TESTED
Error Messages         7/10    typed status assertions, no raw lock text   TESTED
Documentation          6/10    docs impact recorded for later readiness    INFERRED
Upgrade Path           8/10    additive IPC + policy parity                TESTED
Dev Environment        9/10    temp-home fixtures, no live brain access    TESTED
Community              6/10    internal contributor evidence only          INFERRED
DX Measurement         8/10    TTHW commands recorded in evidence          TESTED
TTHW measured          <3 min  3 steps                                     TESTED
Overall DX             8/10

## Boomerang Comparison

- Plan-devex-review requested a named fast verification loop: satisfied by focused policy/manifest/inventory commands and full broker suite evidence.
- Plan-devex-review requested typed error examples: satisfied in tests for `maintenance_deferred`, `local_only_remote_rejected`, `owner_unreachable`, `completion_unknown`, and `lock_safety_blocked`.
- Plan-devex-review requested docs/help/changelog impact check: partially satisfied for requirement 007; no public syntax changed, but operator-facing recovery docs remain better suited for requirement 009 production readiness.

## Evidence Inventory

- `bun test test/cli-pglite-operation-broker.test.ts` -> 51 pass, 420 expectations.
- `bun test test/http-transport.test.ts test/pglite-owner-policy.test.ts test/pglite-operation-ipc.test.ts test/e2e/mcp.test.ts test/pglite-broker-representative-coverage.test.ts` -> 43 pass, 2498 expectations.
- `bun run typecheck` -> pass.
- `bun test test/pglite-broker-representative-coverage.test.ts test/pglite-owner-policy.test.ts` -> 2 pass, 1953 expectations.
- `bun run scripts/validate-pglite-access-inventory.ts requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml --json` -> ok.

## Verification Gaps

- Requirement 008 still owns the repeated N-attempt named command matrix and must not be substituted by this representative implementation proof.
- Requirement 009 should decide final public docs/help/changelog recovery guidance for live-owner typed guards.
