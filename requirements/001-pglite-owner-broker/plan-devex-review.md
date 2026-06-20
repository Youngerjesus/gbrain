# Plan DevEx Review: PGLite Owner Broker

Created: 2026-06-20
Status: GO WITH CHANGES
Plan under review: plans/001-pglite-owner-broker/plan.md

## Plan Under Review

The plan changes CLI, MCP, local IPC, diagnostics, tests, and operator-facing PGLite behavior. Product type: CLI + MCP server + agent tool.

## Persona And TTHW Target

TARGET DEVELOPER PERSONA
Who: Open-source contributor or operator debugging gbrain on a local PGLite install.
Context: They can run Bun tests and inspect local gbrain config, but may not know PGLite lock internals.
Tolerance: Low tolerance for flaky concurrency tests or hidden daemon requirements.
Expects: Existing command syntax to keep working; errors to say whether the broker, owner, or lock is the problem.

TTHW target: Competitive, 2-5 minutes for a contributor to run a focused broker test and understand pass/fail output.
Magical moment: A synthetic concurrency test shows five callers served/queued without PGLite lock timeout strings.

Competitive DX benchmark: Reference only from local `dx-hall-of-fame.md`; no live competitor claim affects this implementation plan. Target is Stripe/Rust-like actionable errors: what happened, why, how to fix, and actual local path/process values when safe.

## DX Scorecard

DX PLAN REVIEW - SCORECARD
Dimension              Score   Prior/Target   Trend/Gap
Getting Started        7/10    Competitive    Need exact focused test command and fixture path.
API/CLI/SDK            8/10    Existing CLI   Strong unchanged syntax; ensure `search` wrapper mapping is explicit.
Error Messages         7/10    Actionable     Needs concrete broker error/status examples.
Documentation          6/10    Feature docs   Plan should include docs/ENGINES or operator note update.
Upgrade Path           8/10    Compatible     No syntax break; include fallback/kill-switch note if added.
Dev Environment        7/10    Fast loop      Missing `scripts/init_worktree.sh` blocks isolated implementation setup.
Community              7/10    OSS credible   Fine if docs/tests are public and synthetic.
DX Measurement         7/10    Test evidence  Need focused verification recipe plus live devex-review boomerang.
TTHW                   3-5 min Competitive    Achievable with focused tests and docs.
Competitive Rank       Competitive
Magical Moment         designed via synthetic five-caller concurrency test
Product Type           CLI + MCP server + agent tool
Mode                   DX POLISH
Overall DX             7/10
Verdict                GO WITH CHANGES

## Implementation Checklist

[x] product type and developer persona are explicit
[x] public CLI syntax remains unchanged
[ ] broker error/status examples are concrete and tested
[ ] docs mention PGLite owner broker behavior and troubleshooting
[ ] focused verification command is documented in evidence
[ ] isolated worktree bootstrap exists and is reproducible
[x] synthetic tests avoid private brain data
[ ] live devex-review after implementation compares against this review

## Implementation Tasks

- [ ] DX1 (P1) - Worktree setup - Add idempotent `scripts/init_worktree.sh` before product implementation if it is still missing.
  - Surfaced by: Dev Environment.
  - Files: `scripts/init_worktree.sh`.
  - Verify: running the script with a task path creates or refreshes a usable worktree without external runtime state.
- [ ] DX2 (P1) - Error contract - Implement and test broker error envelopes with actionable local diagnostics.
  - Surfaced by: Error Messages And Debugging.
  - Files: `src/core/pglite-operation-ipc.ts`, CLI/MCP tests.
  - Verify: tests assert status codes/messages for owner unreachable, stale socket recovery, lock safety block, queued, and served.
- [ ] DX3 (P2) - Docs and verification recipe - Update operator docs with PGLite owner broker behavior, no-daemon fallback, and focused verification command.
  - Surfaced by: Documentation And Learning; DX Measurement.
  - Files: `docs/ENGINES.md` or a more specific existing doc.
  - Verify: docs mention no command syntax change and privacy-safe diagnostics.
- [ ] DX4 (P1) - Search/think CLI parity - Explicitly test `query`, `search`, and `think` command forms through direct-open and owner-forwarded paths.
  - Surfaced by: API/CLI/SDK Design.
  - Files: `src/cli.ts`, `src/commands/search.ts`, `src/commands/think.ts`, tests.
  - Verify: unchanged command forms pass smoke/concurrency tests.

## Unresolved Decisions

None blocking. If a kill-switch environment variable is added, document it and test that it restores direct behavior only when safe.

## Recommended Next Step

Update the draft plan with DX1-DX4 before plan-eng-review.
