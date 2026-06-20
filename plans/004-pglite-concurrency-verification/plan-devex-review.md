# Plan DevEx Review: PGLite Concurrency Verification

Status: GO WITH CHANGES
Date: 2026-06-20
Reviewed plan: `plans/004-pglite-concurrency-verification/plan.md`
Requirements source: `requirements/004-pglite-concurrency-verification/requirements.md`

## Applicability

- Product type: CLI, MCP server, documentation, and local agent tool.
- Target developer persona:
  - Who: developer or AI-agent operator using default local PGLite with Codex/Claude/Cursor MCP.
  - Context: wants `gbrain serve` running while also using CLI `query`/`search`/`think`; may also run maintenance commands.
  - Tolerance: low for unexplained PGLite lock errors; moderate for explicit maintenance deferral.
  - Expects: unchanged commands, no daemon ceremony, clear recovery messages, and docs that separate interactive use from maintenance work.
- Review mode: DX TRIAGE. This slice is not a new onboarding project; it must remove a confusing lock-timeout failure mode and prevent stale operator guidance.
- TTHW target: Competitive, 2-5 minutes from reading docs to understanding whether a concurrent command should work or be deferred.
- Magical moment: user runs a second local interactive caller and it completes or returns a deterministic non-lock broker status.

## Journey Trace

- Discover: README and `docs/ENGINES.md` explain PGLite as zero-config; current README troubleshooting still says to stop `gbrain serve` before a large sync.
- Install: no change.
- Hello World: unchanged `gbrain init --pglite`, `gbrain serve`, `gbrain query`.
- Real Usage: plan must document that interactive `query`/`search`/`think` route through the owner broker while `sync`/`embed`/`extract` are deferred under a live owner.
- Debug: status vocabulary must be operator-meaningful and privacy-safe.
- Upgrade: no migration or command syntax change; docs must avoid implying old behavior remains universal.

## Findings

1. README contains directly stale broad guidance and should be included in the implementation plan.
   - Evidence: `README.md` says, "on a PGLite brain, stop `gbrain serve` before a large sync" and points to `docs/architecture/serve-sync-concurrency.md`.
   - Impact: a user may keep applying the old blanket workaround and conclude concurrent `query`/`search`/`think` is unsupported.
   - Required plan change: include README troubleshooting copy in the docs update search, with wording that preserves the maintenance caveat but calls out interactive broker support.

2. Docs need examples that separate success, deferral, and safety-blocked outcomes.
   - Evidence: Requirement AC4 names `served`, `owner_unreachable`, `completion_unknown`, `lock_safety_blocked`, `owner_starting`, `maintenance_deferred`, and `stale_socket_recovered`.
   - Impact: stable status names are useful only if an operator can decide whether to retry, stop an owner, or avoid unsafe lock deletion.
   - Required plan change: docs update should include a compact status/action table or equivalent operator hints.

3. Test evidence should not overpromise key-dependent `think` quality.
   - Evidence: The plan accepts deterministic keyless/no-result `think` behavior when no API keys exist.
   - Impact: developers could misread the E2E as proving LLM answer quality rather than concurrency routing.
   - Required plan change: closeout and test names should state the `think` proof is route/completion/no-lock evidence, not model-quality evidence.

## Eight-Pass DX Scorecard

- Getting Started Experience: 7/10 -> 8/10 with README/doc copy updated.
- API/CLI/SDK Design: 9/10; public command syntax remains unchanged.
- Error Messages And Debugging: 7/10 -> 8/10 with status/action docs.
- Documentation And Learning: 6/10 -> 8/10 with README plus architecture doc alignment.
- Upgrade And Migration Path: 9/10; no migration required.
- Developer Environment And Tooling: 8/10; hermetic serial test aligns with repo test patterns.
- Community And Ecosystem: 7/10; no broad ecosystem change.
- DX Measurement And Feedback Loops: 7/10; closeout evidence matrix and regression suite are enough for this narrow slice.

## Implementation Tasks

- [ ] **T1 (P1)** - Docs - Update README troubleshooting language where it still gives blanket PGLite serve/sync guidance.
  - Surfaced by: Finding 1.
  - Files: `README.md`, `docs/architecture/serve-sync-concurrency.md`
  - Verify: `rg -n "stop.*serve|serve.*sync|maintenance_deferred|owner broker" README.md docs -S`

- [ ] **T2 (P1)** - Docs - Add operator action guidance for stable broker/defer/safety statuses.
  - Surfaced by: Finding 2.
  - Files: `docs/architecture/serve-sync-concurrency.md`, possibly `docs/ENGINES.md`
  - Verify: docs mention the required status vocabulary without private data examples.

- [ ] **T3 (P2)** - Evidence - Label `think` test evidence as route/no-lock proof, not LLM answer-quality proof.
  - Surfaced by: Finding 3.
  - Files: `test/pglite-concurrent-access.serial.test.ts`, requirement closeout.
  - Verify: test assertions and closeout matrix distinguish concurrency route success from answer quality.
