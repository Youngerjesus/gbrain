---
name: idea-review
description: Facilitates an autonomous, critical deep-dive discussion between a simulated Product Builder and Reviewer to rigorously evaluate a new feature or idea before specification.
---

# Idea Review

When this skill is activated, autonomously simulate a structured debate between:

1. **The Project Builder**: argues for user value, business impact, and alignment with the product's North Star.
2. **The Reviewer**: acts as the devil's advocate, questions necessity, highlights complexity, and pushes for simpler alternatives.

## Goal

Stress-test the user's idea through a dialectic process and produce a synthesized conclusion about whether the feature is truly necessary and what the leanest viable approach is.

## Process

### 1. Context & State Discovery

Before debating, ground the discussion in the actual repo state.

- Read root `AGENTS.md`, `policies/autonomy-policy.yml`, relevant `ssot/*.md`, `human-requests/inbox.md`, `memory/*`, `project_manager/AGENTS.md`, and `project_manager/project_profile.json`.
- Resolve the active managed repo from `project_manager/project_profile.json`; use its `source_repo_root`, `workspace_root`, and `main_worktree` instead of hardcoded repo or worktree paths.
- Read the candidate package under `project_manager/specs/<feature_slug>/`, especially `design.md` when present, plus `project_manager/tasks/tasks.json` for queue state.
- Inspect only profile-resolved managed repo files that are relevant to the candidate's APIs, schemas, UI components, or existing flows.
- If a needed input or resolved path is missing, record it as missing evidence instead of falling back to non-canonical paths.
- Summarize the current CAO candidate context in a few sentences before starting the debate.

### 2. The Debate

Run 3 to 5 rounds:

1. Builder pitches the value.
2. Reviewer attacks the premise and complexity.
3. Builder defends or narrows scope.
4. Reviewer pressures for simplification.
5. Continue if needed until the real tradeoff is clear.

### 3. Synthesis

- Define the underlying problem, not just the proposed solution.
- Present the synthesized solution.
- Suggest an MVP that captures most of the value with minimal complexity.

### 4. Verdict

Return one of:

- `[PROCEED]`
- `[PIVOT]`
- `[DISCARD]`

For CAO candidate review, always include a normalized block with:

- `feature_slug`
- `source_inputs_read`
- `missing_inputs`
- `verdict`
- `lean_mvp`
- `discard_reason`
- `handoff_impact`
- `required_followups`

When the CAO runtime provides a structured output schema, the final response must be a single plain JSON object matching that schema exactly. Put extra human-facing fields such as `feature_slug`, `source_inputs_read`, `missing_inputs`, `handoff_impact`, and `required_followups` into `project_manager/specs/<feature_slug>/idea_review.md`, not into the final structured response unless the runtime schema explicitly includes them.

When `feature_slug` is known, save the result at `project_manager/specs/<feature_slug>/idea_review.md`.

For CAO policy mapping, `verdict=[DISCARD]` means the candidate must be discarded. `verdict=[PIVOT]` means the candidate is not ready for handoff until the pivot is reflected in `design.md` or a follow-up planning artifact. `verdict=[PROCEED]` keeps the candidate eligible for the remaining review gates.

If the idea touches protected areas, security/data-loss/deploy risk, or conflicting evidence from `policies/autonomy-policy.yml`, set `handoff_impact` to `escalation-needed` or `human-input-needed` even when the product idea is otherwise strong.

Maintain a sharp, analytical, professional tone.
