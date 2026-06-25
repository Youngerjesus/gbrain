---
name: technical-design
description: Produce requirement-local HOW-level module design and optional architecture design when planning-orchestrator records design_depth as full_artifact_required.
---

# Technical Design

This skill is the `goal-requirements` HOW-level module design and architecture design specialist. It is not UI/visual design.

In the three main gate model, `technical-design` is not a top-level `goal-requirement-orchestrator` gate. Use it from `planning-orchestrator` when Plan records `design_depth: full_artifact_required` because implementation planning needs module boundaries, architecture boundaries, interactions, state, invariants, error handling, edge cases, testability, or cross-layer handoff decisions. Direct use outside goal orchestration remains valid when the user explicitly asks for technical design.

## Contract

Technical design is complete only when it turns accepted requirements into implementation-ready HOW-level design without changing the WHAT. The design must:

- Decide whether the gate is `required_pending`, `completed`, `not_required`, `blocked`, or `stale_needs_recheck` from requirement-local state rather than artifact presence alone.
- Map every acceptance criterion to module boundaries, interfaces, data flow, state, invariants, error handling, and verification.
- Create `architecture.md` only when system-level boundaries or cross-layer handoffs need a separate artifact.
- Keep `progress.md`, `decisions.md`, and `evidence.md` coherent with the artifact status.
- Stop before `plan-eng-review` when research, requirements, gate state, unresolved blockers, or Requirement Impact are contradictory or awaiting approval.

## Inputs

- Required: `requirements/<requirement-id>/requirements.md`
- Required if present or required by gate state: `requirements/<requirement-id>/research.md`
- Required state: `requirements/<requirement-id>/progress.md`, `decisions.md`, and `evidence.md`
- Optional: accepted plans, existing docs, code, or architecture notes

## Outputs

Write or update:

```text
requirements/<requirement-id>/technical-design.md
```

Write this only when a separate system-level architecture design is needed:

```text
requirements/<requirement-id>/architecture.md
```

`architecture.md` is requirement-local planning/design context. It is not the durable project architecture source of truth. If the design changes durable system boundaries, record Requirement Impact and use `context-sync` or user approval before treating durable docs as changed.

## Module Design Vs Architecture Design

- Module design belongs in `technical-design.md`: module boundaries, public interfaces, local data flow, state, invariants, edge cases, and tests for this requirement.
- Architecture design belongs in `architecture.md` only when system-level architecture boundaries, runtime handoffs, schema ownership, module dependency direction, cross-layer invariants, evidence identity, or multi-agent/control-plane boundaries need a separate artifact.
- If architecture is not required, record the explicit rationale in `technical-design.md` and `progress.md`.
- Name the owning module for each responsibility. Higher-level or more volatile modules may depend on lower-level or more stable modules, but lower-level modules must not import back upward across a declared boundary.
- Cross-boundary calls should use the owning boundary's public interface, typed schema, or artifact handoff instead of private implementation details.

## Scope Protection

- Do not add, remove, or weaken functional requirements.
- Do not introduce new business requirements.
- Do not remove a requirement because the design is difficult.
- Requirement Impact requires user approval before downstream gates continue.
- If user approval changes `requirements.md`, prior technical design becomes `stale_needs_recheck` until revalidated or rerun.

## Workflow

1. Read the requirement source first, then required research, then `progress.md`, `decisions.md`, and `evidence.md`.
2. Report a gate decision before drafting artifacts: `not_required` with a concrete rationale, `required_pending` or `in_progress` for real design work, `blocked` for missing required inputs, or `stale_needs_recheck` for contradictory state.
3. Inspect existing code, docs, tests, and accepted plans only enough to identify real module boundaries, public interfaces, data ownership, dependency direction, and verification hooks.
4. Build a requirement coverage map before drafting design details. If any acceptance criterion lacks a design mapping, keep the gate incomplete.
5. Decide whether `architecture.md` is required. Use `technical-design.md` for local module design; use `architecture.md` only for system-level boundaries, schema/runtime ownership, evidence identity, multi-agent handoffs, or cross-layer invariants.
6. Draft HOW-level design: module boundaries, public interfaces, interactions, data flow, state, invariants, error handling, edge cases, observability, and testability.
7. Classify every unresolved item as `blocking` or `non_blocking` with rationale and downstream owner.
8. Record material decisions in `decisions.md` and artifact/source evidence in `evidence.md`.
9. Update `progress.md` with the gate status, reason, artifact path, architecture artifact status, unresolved blocking count, and next owner.
10. Self-review for requirement coverage, separation of concerns, testability, security/safety, and requirement integrity before reporting completion.

## Gate State Contract

Use the requirement progress vocabulary:

- `not_evaluated`
- `required_pending`
- `in_progress`
- `completed`
- `not_required`
- `blocked`
- `awaiting_user_approval`
- `stale_needs_recheck`

Artifact existence alone is insufficient. A completed technical-design gate requires a coherent tuple:

- `progress.md` records `Gate: technical-design`, `Gate status: completed`, reason, artifact path, and architecture artifact status.
- `technical-design.md` exists under the owning requirement folder.
- `architecture.md` exists when architecture design is required, or the non-required rationale is recorded.
- `evidence.md` records artifact paths and source evidence.
- `decisions.md` records or references material design and architecture decisions.
- Every unresolved item is classified as `blocking` or `non_blocking` with rationale and downstream owner.
- No Requirement Impact is awaiting user approval.

If these surfaces disagree, record `stale_needs_recheck` or `blocked` and do not continue to `plan-eng-review`.

## Artifact Shape

Use this structure for `technical-design.md`:

```markdown
# Technical Design: <Requirement Title>

Created: <YYYY-MM-DD>
Status: Complete | Partial | Blocked | Awaiting User Approval
Requirement source: requirements/<requirement-id>/requirements.md
Research source: requirements/<requirement-id>/research.md | Not required
Architecture artifact: requirements/<requirement-id>/architecture.md | Not required - <reason>

## Requirement Coverage

| Requirement / Acceptance Criterion | Design mapping |
| --- | --- |

## Module Design

- Module boundaries:
- Public interfaces:
- Dependency direction:
- Data flow:

## Interactions

- Main flow:
- Alternate flows:
- Handoffs:

## State And Invariants

- States:
- Invariants:
- Consistency rules:

## Error Handling And Edge Cases

- Errors:
- Edge cases:
- Recovery:
- Observability:

## Testability

- Unit:
- Integration:
- E2E/manual if relevant:
- Mockable boundaries:

## Requirement Impact

- None, or:
- Impact:
- Affected requirement:
- Alternatives:
- Approval status: requires user approval

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |

## Self-Review

- Requirement coverage:
- Separation of concerns:
- Testability:
- Security / safety:
- Requirement integrity:
```

Use this structure for `architecture.md` when needed:

```markdown
# Architecture Design: <Requirement Title>

Requirement source:
Technical design source:

## Architecture Boundary

## Components And Ownership

## Dependency Direction

## Runtime / Agent / Schema / Evidence Handoffs

## Cross-Layer Invariants

## Risks And Rollback
```

## Output Format

Report:

- Gate-State Summary: status, reason, source paths, artifact paths, architecture status, unresolved blocking count, and next owner.
- `technical-design.md` path
- `architecture.md` path or not-required rationale
- requirement coverage status
- unresolved blocking count
- Requirement Impact status
- progress/decisions/evidence updates

Return blocked instead of completed when blocking unresolved items, missing required architecture design, stale research, contradictory state, or Requirement Impact approval remain open.

## Anti-Patterns

- Treating `technical-design.md` existence as completion while `progress.md`, `decisions.md`, or `evidence.md` disagree.
- Recording `not_required` without a concrete requirement-local rationale.
- Writing `architecture.md` for ordinary local module design or skipping it when system-level boundaries actually change.
- Changing, weakening, or adding requirements inside the design artifact.
- Jumping into implementation planning, task breakdown, or code edits instead of HOW-level design.
- Leaving unresolved blockers hidden as non-blocking notes.
- Duplicating durable architecture guidance without recording Requirement Impact and using `context-sync` or user approval.
- Continuing to `plan-eng-review` with stale research, contradictory state, missing evidence, or pending Requirement Impact approval.
