# Requirement Decisions Template

Use this template for:

```text
requirements/<requirement-id>/decisions.md
```

Record only material design, scope, ordering, constraint, or tradeoff decisions. Do not turn this into a full implementation diary.

For `research.md`, `technical-design.md`, optional `architecture.md`, and UI-bearing `plan-design-review`, record material decisions here or link to the exact artifact or chat-only review outcome. Requirement Impact entries must say whether approval is pending, approved, denied, or superseded. Unresolved research/design items must be classified as blocking/non-blocking with rationale and downstream owner.

```markdown
# Requirement Decisions

## Decisions

### YYYY-MM-DD HH:MM KST - <short title>

- Decision:
- Rationale:
- Alternatives considered:
- Impact:
- Source artifact: research.md | technical-design.md | architecture.md | plan-design-review outcome | progress.md | other
- Requirement Impact:
- Blocking/non-blocking unresolved items:
```
