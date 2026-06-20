# Plan UX Review: PGLite Owner Broker

Created: 2026-06-20
Status: GO WITH CHANGES
Plan under review: plans/001-pglite-owner-broker/plan.md

## Plan Under Review

The plan changes user-facing operational behavior for local gbrain users who run multiple MCP servers and CLI commands against a PGLite brain.

## Persona And First Value

TARGET USER PERSONA
Who: Local gbrain operator using default PGLite from Codex/Claude/CLI.
Context: Multiple agent/MCP processes may start simultaneously.
Goal: Run `query`, `search`, or `think` without PGLite lock failures.
Tolerance: Low tolerance for opaque lock errors; moderate tolerance for brief queueing if the reason is clear.
Constraints: Personal brain data must not leak into diagnostics.
Success looks like: The command completes or explains owner/broker state with a next action, without asking the user to understand PGLite internals.

First-value target: under 30 seconds for owner discovery and first visible progress/diagnostic; successful forwarded operations may take operation-specific time.

## Journey Map

1. Arrive: user runs `gbrain query "x"` while a PGLite owner is alive.
2. Orient: command should avoid 30s lock waiting and either serve, queue, or show broker-specific state.
3. Act: caller forwards to owner automatically; no new flags.
4. Wait or interpret: queued operations should be bounded by existing command timeout semantics and emit privacy-safe diagnostics when useful.
5. Recover: owner-unreachable and lock-safety-blocked cases must tell the user whether to restart `gbrain serve`, wait, or inspect stale processes.
6. Complete: output remains the existing command result format.
7. Continue: user can rerun commands; direct-open fallback still works when no owner exists.

## UX Scorecard

UX PLAN REVIEW - SCORECARD
Dimension                 Score   Target/Gap
First Value               8/10    Good automatic routing; add explicit first visible queued/served diagnostic target.
Core Task Flow            8/10    Unchanged commands; ensure `search` and `think` wrappers do not diverge.
Information Architecture  7/10    Status taxonomy exists; needs exact user-facing state matrix.
Interaction States        7/10    Main states named; add copy/actions for owner-unreachable and lock-safety-blocked.
Recovery And Re-entry     8/10    Conservative recovery is strong; make retry/direct-open behavior explicit.
Trust And Clarity         8/10    Single-owner safety is clear; diagnostics must avoid private query payloads.
Accessibility             9/10    Terminal/MCP text surface; no visual accessibility risk beyond clear text.
Measurement               7/10    Tests are strong; add operator/debug evidence for queue/serve statuses.
Overall UX                8/10
Mode                      UX POLISH
Verdict                   GO WITH CHANGES

## Implementation Checklist

[x] target user and job are explicit
[x] first-value moment is reachable in under 30 seconds for broker discovery
[x] primary task has a clear start, middle, and finish
[ ] empty, loading, partial, error, and success states are defined with exact copy/status
[x] user can recover, retry, go back, refresh, or resume
[x] trust cues explain lock safety and owner state
[x] accessibility and keyboard behavior are covered by terminal text semantics
[ ] privacy-safe diagnostics and post-ship friction measurement are named

## Implementation Tasks

- [ ] UX1 (P1) - Broker diagnostics - Define exact status matrix and actionable messages for `queued`, `served`, `owner_unreachable`, `stale_socket_recovered`, and `lock_safety_blocked`.
  - Surfaced by: Interaction States; Recovery And Re-entry.
  - Files: `src/core/pglite-operation-ipc.ts`, `src/cli.ts`, tests.
  - Verify: tests assert deterministic status/message text without private query payloads.
- [ ] UX2 (P1) - CLI wait semantics - Preserve existing command timeout behavior while avoiding PGLite lock wait; queued operations must fail with a broker/operation timeout, not a PGLite lock timeout.
  - Surfaced by: First Value; Core Task Flow.
  - Files: `src/cli.ts`, broker tests.
  - Verify: concurrency test checks no lock timeout strings and timeout messages remain actionable.
- [ ] UX3 (P2) - Operator evidence - Add privacy-safe debug or docs evidence explaining how to recognize owner-forwarded vs direct-open behavior.
  - Surfaced by: Trust And Clarity; Measurement.
  - Files: `docs/ENGINES.md` or equivalent docs, tests/evidence.
  - Verify: docs mention owner broker states without exposing private query content.

## Unresolved Decisions

None blocking. Exact diagnostic phrasing can be chosen during implementation if it satisfies UX1.

## Recommended Next Step

Update the draft plan to include the status matrix, timeout requirement, and operator evidence before plan-eng-review.
