# Sequence Progress Template

Use this template for:

```text
goal-requirements/<id>/progress.md
```

Keep this file focused on sequence-level recovery state: which requirement is active, which gate is active, whether the sequence is blocked, and what the next action is.

```markdown
# Sequence Progress

## Current State

- Current requirement:
- Current gate:
- Status:
- Next action:

## Outcome Contract

- Sequence outcome:
- First requirement path:
- First requirement acceptance status:
- Later requirement files deferred until reached: yes | no

## Production Readiness

- Required: yes | no | not_evaluated
- Readiness requirement:
- Verdict: not_started | ready | ready_with_external_handoff | blocked_internal | blocked_external | deferred_non_goal
- External handoff:
- Internal blocker:

## Log

### YYYY-MM-DD HH:MM KST

- Requirement:
- Gate:
- Result:
- Next:
```
