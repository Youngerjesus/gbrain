---
name: planning-orchestrator
description: Own the goal-requirements Plan main gate by resolving research, design-depth, plan reviews, scenario coverage, secondary-plan reconciliation, and a durable implementation handoff before Impl starts.
---

# Planning Orchestrator

Use this skill as the `Plan` main gate for goal-requirements slices after requirement acceptance and any source/coverage readiness checks are satisfied.

This skill does not implement code. It turns an accepted requirement into a durable Plan handoff that `Impl` can consume without conversation memory.

## Contract

Plan is complete only when it emits an accepted handoff at:

```text
plans/<plan-id>/plan_handoff.toml
```

The handoff must include:

- `accepted_plan_path`
- `design_depth`
- `invoked_subreviews`
- `deferred_items`
- `blockers`
- `verification_strategy`
- `stale_recheck_routing`

Allowed `design_depth` values:

- `none`: no design artifact is required; record the reason.
- `inline`: local design notes in the handoff are enough; record the notes.
- `full_artifact_required`: run `technical-design` and reference `requirements/<requirement-id>/technical-design.md`.

The existing `technical-design` skill remains available. It is no longer a top-level goal-requirement gate when this Plan model is active; it is a Plan-internal full-artifact option.

## Owned Sub-Decisions

Plan owns these planning-side decisions and may invoke the named specialist skills when their triggers apply:

- `research`
- `design_depth`
- `plan-design-review`
- `plan-ux-review`
- `plan-devex-review`
- `plan-eng-review`
- `scenario-brake`
- `secondary-plan`

Triggered sub-decisions block Plan completion when missing, stale, contradictory, unresolved-blocking, cleanup-only, or awaiting requirement-impact approval.

## Workflow

1. Read the accepted requirement, progress, decisions, evidence, coverage/source-obligation state, and any existing planning artifacts.
2. Confirm requirement acceptance and readiness are satisfied before planning.
3. Decide whether research is required; record a structured not-required reason when skipped.
4. Record `design_depth`. Use `full_artifact_required` when module boundaries, state, invariants, architecture, testability, or cross-layer handoff risk requires a full technical design artifact.
5. Create or update the draft plan and run any triggered plan design, UX, DevEx, engineering, and scenario reviews.
6. Run `secondary-plan` to reconcile accepted planning evidence.
7. Emit `plans/<plan-id>/plan_handoff.toml`.
8. Update requirement `progress.md`, `decisions.md`, and `evidence.md` with Plan status, invoked subreviews, blockers, deferred items, and the handoff path.

## Handoff Shape

```toml
requirement_id = "<requirement-id>"
plan_status = "accepted"
accepted_plan_path = "plans/<plan-id>/plan.md"
secondary_plan_path = "plans/<plan-id>/secondary_plan.md"
design_depth = "none | inline | full_artifact_required"
technical_design_path = "requirements/<requirement-id>/technical-design.md | not_required"
verification_strategy = "<targeted and baseline checks>"
stale_recheck_routing = "plan | requirement-clarifier | review | none"
blockers = []
deferred_items = []

[[invoked_subreviews]]
name = "plan-eng-review"
status = "passed | not_required | blocked"
artifact_path = "plans/<plan-id>/reviews/plan-eng-review.md"
```

## Output Format

Report:

- Plan status
- Plan handoff path
- Design-depth decision
- Invoked subreviews and artifact paths
- Blockers and deferred items
- Verification strategy
- Next gate: `Impl`

## Anti-Patterns

- Treating a ready requirement as implementation permission.
- Skipping design-depth because the top-level Technical Design Gate was removed.
- Replacing Plan handoff with conversation memory.
- Flattening plan design, UX, DevEx, engineering, scenario, and secondary-plan evidence into vague prose.
- Treating cleanup-only or timed-out subagent state as approval.
