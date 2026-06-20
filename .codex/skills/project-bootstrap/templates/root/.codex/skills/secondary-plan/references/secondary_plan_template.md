# Secondary Plan: <Plan Title>

Primary plan: [plan.md](plan.md)
Codex proposed plan link: <link to planning message if available>
Plan id: `<plan-id>`
Created: <YYYY-MM-DD>
Last updated: <YYYY-MM-DD>

## Why This Approach

- Chosen direction:
- Why it fits the stated goal:
- Rejected alternatives:
- Assumptions that must hold:
- Evidence still needed before implementation:

## RALPLAN-DR Summary

Use this section only when the plan involved meaningful implementation choices, consensus planning, Plan Engineer Review, or an explicit ralplan handoff. Otherwise write `Not triggered: <reason>` and delete the placeholder bullets.

- Principles:
  - <principle 1>
  - <principle 2>
  - <principle 3>
- Decision drivers:
  - <driver 1>
  - <driver 2>
  - <driver 3>
- Viable options:
  - <option A>: <bounded pros, cons, and fit>
  - <option B>: <bounded pros, cons, and fit>
- Alternatives rejected or invalidated:
  - <alternative>: <why it should not be reopened during implementation>
- Premortem for high-risk plans:
  - <failure scenario 1 and mitigation>
  - <failure scenario 2 and mitigation>
  - <failure scenario 3 and mitigation>
- Expanded test plan for high-risk plans:
  - Unit:
  - Integration:
  - E2E or browser/manual:
  - Observability/operator evidence:

## ADR

Use this section only when the chosen path has architectural, operational, UX, data, or workflow consequences worth preserving. Otherwise write `Not triggered: <reason>` and delete the placeholder bullets.

- Decision:
- Drivers:
- Alternatives considered:
- Why chosen:
- Consequences:
- Follow-ups:

## Implementation Guardrails

- Required implementation constraints:
- Allowed implementation freedom:
- Likely mistake points:
- Boundaries not to cross:
- Existing behavior that must not regress:
- Decisions the implementer must not reopen:
- Details that belong in `spec.md` or `contracts.md` instead:
- Executable contract compatibility findings:
- Required legal executable contract evidence:
- Drift checks against `plan.md` and the compressed Codex plan:

## Files To Inspect

- `<path>`: <why this matters before editing>
- `<path>`: <why this matters before editing>

## Tests To Run Or Add

- Run `<command>`: <what this proves>
- Add `<test target>`: <behavior or invariant it proves>
- Likely failure interpretation:
- Minimum verification before handoff:

## Review Notes

- Decision brake:
- Plan design review:
- Plan UX review:
- Plan DevEx review:
- Plan engineering review:
- Scenario review:
- Open review risks:

## Optional Detailed Review Sections

Use these sections only when the review output contains handoff-changing details that would be too compressed inside `Review Notes`. Delete unused sections. Keep `Review Notes` as the short index, and put the detailed reasoning here.

### Decision Brake Details

- Core decision under review:
- Strongest reason to proceed:
- Strongest reason to stop or change direction:
- Hidden assumptions:
- Better alternatives considered:
- Failure modes or second-order effects:
- Final judgment:

### Plan Engineering Review Details

- Implementation approach reviewed:
- Reuse or architecture constraints:
- File, module, or ownership boundaries:
- Interface, data, or migration risks:
- Testing gaps:
- Sequencing or dependency risks:
- Required changes before implementation:

### Plan Design Review Details

- UI scope reviewed:
- Information architecture gaps:
- Interaction state coverage:
- User journey or trust risks:
- Design-system alignment:
- Responsive or accessibility concerns:
- Locked design decisions:
- Deferred design items:
- Required changes before implementation:

### Plan UX Review Details

- User-facing scope reviewed:
- First value or onboarding gaps:
- Core task flow gaps:
- Interaction state coverage:
- Recovery or re-entry risks:
- Trust, clarity, or accessibility concerns:
- Locked UX decisions:
- Deferred UX items:
- Required changes before implementation:

### Plan DevEx Review Details

- Developer-facing scope reviewed:
- Target developer persona:
- TTHW target or getting-started gaps:
- API/CLI/SDK ergonomics:
- Error quality or debugging gaps:
- Documentation, upgrade, or tooling risks:
- Locked DX decisions:
- Deferred DX items:
- Required changes before implementation:

### Scenario Brake Details

- Scenarios covered:
- Missing or weak scenarios:
- Edge cases:
- Recovery or rollback paths:
- State, timing, or concurrency risks:
- Acceptance evidence needed:
- Required scenario additions before implementation:

## Conversation Details To Preserve

- User preferences:
- User constraints:
- Examples or references:
- Rejected ideas:
- Context likely to disappear during compression:

## Handoff Checklist

- [ ] Primary plan, secondary plan, and compressed Codex plan agree.
- [ ] Any conflict between this document, `plan.md`, and the compressed Codex plan has been reconciled before editing.
- [ ] Required files have been inspected before editing.
- [ ] Implementation stays inside the listed guardrails.
- [ ] Implementation details in this document are required constraints, not incidental coding choices.
- [ ] Required tests have been added or run.
- [ ] Review notes have been addressed or explicitly deferred.
- [ ] No new decisions were introduced without updating this document.
