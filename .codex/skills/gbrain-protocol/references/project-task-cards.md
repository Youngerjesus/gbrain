# Project Task Card Memory

Use a Project Task Card when the user asks to preserve work context, continue
goal-requirements work across sessions, link GBrain memory to
`requirement-clarifier`, or prevent future agents from restarting from scratch.

Task Cards are compact working memory, not official contracts. The authoritative
contracts remain the linked `goal-requirements/`, `requirements/`, `plans/`,
`progress.md`, `decisions.md`, and `evidence.md` files.

## Storage

- Global template or policy: `projects/task-card-template`
- Project-specific memory: `projects/<project-id>/task-card`

## Required Sections

- `Goal / Outcome`: the user-visible or workflow-visible state after success.
- `Inputs`: linked Sequence and Requirement paths when present.
- `Verification`: pass evidence and stop/ask conditions.
- `Constraints`: must-preserve and must-not rules.
- `Decisions`: decision, reason, impact, and revisit condition.

## Update Rules

When updating a Task Card, fold in only durable conclusions from the current
session. Do not store raw chat logs, temporary confusion, duplicated requirement
text, or implementation minutiae. Preserve user wording when it carries the
decision, but keep the page concise enough to read before a session starts.

After `requirement-clarifier` finalizes or updates a requirement, save or update
the matching Task Card when the work is expected to continue across sessions.
After `goal-requirement-orchestrator` creates or resumes a sequence, save or
update the matching Task Card with the Sequence path, current Requirement path,
current outcome, constraints, verification standard, and durable decisions.

## Template

```markdown
# Task Card

## Goal / Outcome

- When this work is done, `<user or agent>` can `<do what>` `<how or under what
  conditions>`.
- The previous `<friction, failure, or confusion>` no longer happens.

## Inputs

- Sequence: `<goal-requirements/<id>/sequence.md or not applicable>`
- Requirement: `<requirements/<requirement-id>/requirements.md or not applicable>`

## Verification

- Pass: `<observable evidence that proves the outcome>`
- Stop/ask if: `<conflict, ambiguity, unverified result, scope change, or
  capability gap>`

## Constraints

- Must preserve: `<original intent, verification standard, non-goals, accepted
  scope>`
- Must not: `<narrowing, reinterpretation, unauthorized substitution, arbitrary
  scope change>`

## Decisions

- Decision: `<what was decided>`
  - Reason: `<why this was decided>`
  - Impact: `<what changes for future work>`
  - Revisit if: `<condition that should reopen the decision>`
```

