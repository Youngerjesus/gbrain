# Requirement Decisions Template

Use this template for:

```text
requirements/<requirement-id>/decisions.md
```

Record only material design, scope, ordering, constraint, or tradeoff decisions. Do not turn this into a full implementation diary.

For `research.md`, `technical-design.md`, optional `architecture.md`, conditional plan-stage reviews, and conditional live reviews, record material decisions here or link to the exact artifact. Plan-stage review artifacts live under the plan directory:

- `plans/<plan-id>/reviews/plan-design-review.md`
- `plans/<plan-id>/reviews/plan-ux-review.md`
- `plans/<plan-id>/reviews/plan-devex-review.md`
- `plans/<plan-id>/reviews/plan-eng-review.md`

Requirement Impact entries must say whether approval is pending, approved, denied, or superseded. Unresolved research/design/review items must be classified as blocking/non-blocking with rationale and downstream owner.

For each source-obligation decision, record whether `source_obligation_inventory_required` is true or false, whether a structured source-obligation not-required decision was accepted, and how `source-inventory.yml`, `scope-reconciliation.yml`, reviewer status, and validator evidence preserve accepted scope. Do not use prose-only scope narrowing as a decision substitute.

```markdown
# Requirement Decisions

## Decisions

### YYYY-MM-DD HH:MM KST - <short title>

- Decision:
- Rationale:
- Alternatives considered:
- Impact:
- Source artifact: research.md | technical-design.md | architecture.md | plans/<plan-id>/reviews/<gate>.md | progress.md | other
- Requirement Impact:
- Blocking/non-blocking unresolved items:
```
