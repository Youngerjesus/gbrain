# Plan UX Review

## Plan Under Review

- Requirement: `requirements/002-pglite-operation-forwarding/requirements.md`
- Draft plan: `plans/002-pglite-operation-forwarding/plan.md`
- Review mode: UX TRIAGE
- Surface: local CLI and stdio MCP operational behavior for PGLite forwarding

## Persona And First Value

Target user: a gbrain operator using the default PGLite setup while multiple local tools are open.

Job: run `query`, `search`, or `think` without needing to understand or manually resolve PGLite lock contention.

First value target: within the command's normal response time, the user either gets the expected result or a deterministic broker-specific failure message that does not blame them with a raw lock timeout.

## Top UX Findings

### UX1 - No-owner search evidence is too indirect for user-confidence closure

- Risk: AC3 says no-owner `query`, `search`, and `think` remain direct-open compatible, but the current plan only calls out direct no-owner `query` and `think` plus separate search dispatch evidence.
- User impact: a user who primarily uses `gbrain search "x"` could still hit a forwarding-only or lock-related regression without this slice proving that exact flow.
- Required plan change: add an exact no-owner PGLite `search` smoke assertion or explicitly record why the existing search dispatch test plus shared direct-open path is sufficient.
- Verdict impact: GO WITH CHANGES.

### UX2 - Failure-state wording must remain cause/action oriented

- Risk: the plan lists deterministic statuses but does not require the user-visible text to explain whether completion is unknown, the owner is unreachable, or lock safety blocked direct open.
- User impact: users may retry unsafe operations or assume data loss.
- Required plan change: implementation-brake must inspect broker failure copy for cause and safe next action, not only enum presence.
- Verdict impact: GO WITH CHANGES.

## UX Scorecard

| Dimension | Score | Target/Gap |
| --- | ---: | --- |
| First Value | 8/10 | Strong if lock errors disappear; no-owner search proof should be exact |
| Core Task Flow | 8/10 | Existing command syntax preserved |
| Information Architecture | 8/10 | Status classes are clear, but user-visible copy must be checked |
| Interaction States | 8/10 | Main forwarding states covered |
| Recovery And Re-entry | 7/10 | Completion-unknown and owner-unreachable recovery copy needs explicit review |
| Trust And Clarity | 8/10 | Local-only and no raw SQL constraints support trust |
| Accessibility And Responsive Use | 9/10 | Terminal/MCP text surface; no visual responsive concern |
| Measurement And Feedback | 7/10 | Test evidence strong; post-ship support/error signal deferred to readiness |

## Journey Map

1. Arrive: user runs existing `gbrain query/search/think`.
2. Orient: no new daemon or flag is required.
3. Act: command detects live owner or direct-open fallback.
4. Wait/interpret: response is served, queued, or fails with broker-specific diagnostic.
5. Recover: user sees owner-unreachable/completion-unknown/lock-safety-blocked distinction.
6. Complete: command result or deterministic failure without raw PGLite lock timeout.

## Implementation Checklist

- Verify exact no-owner `search` behavior or document direct-path sufficiency.
- Confirm broker failure copy includes cause and safe next action.
- Preserve existing CLI command syntax.
- Preserve deterministic statuses without exposing private query content.

## Implementation Tasks

- [ ] **UX-T1 (P1)** - No-owner search - Prove exact direct-open compatibility for `gbrain search "x"` or record why existing evidence is sufficient.
  - Surfaced by: UX1
  - Files: `test/cli-pglite-operation-broker.test.ts` or requirement 002 evidence
  - Verify: focused forwarding test suite

- [ ] **UX-T2 (P2)** - Broker failure copy - Inspect implementation-brake evidence for cause/action wording on forwarding failures.
  - Surfaced by: UX2
  - Files: `src/cli.ts`, `src/mcp/server.ts`, `requirements/002-pglite-operation-forwarding/implementation-brake.md`
  - Verify: static evidence plus existing failure tests

## Unresolved Decisions

None requiring user input.

## Recommended Next Step

GO WITH CHANGES. Reconcile UX-T1 and UX-T2 into the plan before plan-eng-review.
