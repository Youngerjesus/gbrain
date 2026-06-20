# Bootstrap Manifest

This manifest is the file-level source of truth for `project-bootstrap`.

Every template-managed file under `templates/root/` that bootstrap may create, preserve, or update must be declared here.

| Path | Required | Condition | Overwrite | Upgrade Sync | Notes |
| --- | --- | --- | --- | --- | --- |
| `.codex/config.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | installs shared agents |
| `.codex/agents/document-writer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/product-builder.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/architect.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/project-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-thinker.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-explorer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-scope-targeter.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-causal-coverage-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/decision-brake-readiness-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/implementation-brake-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/plan-eng-scope-reuse-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | plan-eng companion reviewer |
| `.codex/agents/plan-eng-architecture-contract-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | plan-eng companion reviewer |
| `.codex/agents/plan-eng-verification-failure-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | plan-eng companion reviewer |
| `.codex/agents/grill-me-risk-finder.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | grill-me candidate specialist |
| `.codex/agents/grill-me-alternative-finder.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | grill-me candidate specialist |
| `.codex/agents/grill-me-verification-finder.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | grill-me candidate specialist |
| `.codex/agents/grill-me-handoff-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | grill-me candidate specialist |
| `.codex/agents/grill-me-requirement-shape-finder.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | grill-me candidate specialist |
| `.codex/agents/requirement-clarifier-post-draft-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | requirement-clarifier review gate |
| `.codex/agents/requirement-conformance-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | implementation-brake requirement conformance gate |
| `.codex/agents/scenario-path-separation-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | scenario-brake companion reviewer |
| `.codex/agents/scenario-parameter-mutation-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | scenario-brake companion reviewer |
| `.codex/agents/scenario-recovery-observability-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | scenario-brake companion reviewer |
| `.codex/agents/task-master.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/task-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/code-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/performance-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | concrete performance-risk specialist |
| `.codex/agents/testing-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/security-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/verifier.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | minimal spec mode aware |
| `.codex/agents/context-synchronizer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/context-loader.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | read-only pre-implementation codebase exploration |
| `.codex/agents/visual-qa-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | visual QA companion reviewer |
| `.codex/agents/reference-fidelity-reviewer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | reference fidelity companion reviewer |
| `.codex/agents/staff-engineer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/agents/qa-engineer.toml` | Yes | all modes | safe in `upgrade-sync` | Yes | template-managed |
| `.codex/docs/template_customization.md` | Yes | all modes | safe in `upgrade-sync` | Yes | includes bootstrap marker |
| `.codex/skills/context-sync/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/context-loading/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/closeout/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/goal-requirement-orchestrator/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/goal-requirement-orchestrator/references/decisions_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/goal-requirement-orchestrator/references/evidence_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/goal-requirement-orchestrator/references/requirement_progress_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/goal-requirement-orchestrator/references/sequence_progress_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/goal-requirement-orchestrator/references/sequence_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/goal-requirement-orchestrator/scripts/subagent_lifecycle.py` | Yes | all modes | preserve | No | executable fallback policy source |
| `.codex/skills/production-readiness/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/decision-brake/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/decision-brake/references/review-lenses.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/implementation-brake/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/implementation-brake/references/fix-handoff.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/implementation-brake/references/review-lenses.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/grill-me/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/grill-me/agents/openai.yaml` | Yes | all modes | preserve | No | companion prompt registry |
| `.codex/skills/requirement-clarifier/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/secondary-plan/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/secondary-plan/references/primary_plan_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/secondary-plan/references/secondary_plan_template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/research/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/technical-design/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/scenario-brake/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/scenario-brake/references/review-lenses.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/plan-design-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/plan-ux-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/plan-ux-review/references/review-sections.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/plan-devex-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/plan-devex-review/references/review-sections.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/plan-devex-review/references/dx-hall-of-fame.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/plan-eng-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/ux-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/ux-review/references/review-sections.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/devex-review/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/devex-review/references/review-sections.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/devex-review/references/dx-hall-of-fame.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/spec-creator/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/spec-creator/SPEC_TEMPLATE.md` | Yes | all modes | preserve | No | direct skill asset |
| `.codex/skills/spec-creator/CONTRACT_TEMPLATE.md` | Yes | all modes | preserve | No | direct skill asset |
| `.codex/skills/spec-reviewer/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/task-master-planning/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/tdd-workflow/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/tdd-workflow/references/tdd-rules.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/tdd-workflow/references/verification-checklist.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/visual-qa-hardening/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/_shared/frontend-verification-artifact-schema.md` | Yes | all modes | preserve | No | shared frontend verification artifact schema |
| `.codex/skills/systematic-debugging/SKILL.md` | Yes | all modes | preserve | No | installed runtime skill |
| `.codex/skills/systematic-debugging/references/phase-gates.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/systematic-debugging/references/test-layer-selection.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/systematic-debugging/references/debug-report-template.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/systematic-debugging/root-cause-tracing.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/systematic-debugging/defense-in-depth.md` | Yes | all modes | preserve | No | direct skill reference |
| `.codex/skills/systematic-debugging/condition-based-waiting.md` | Yes | all modes | preserve | No | direct skill reference |
| `AGENTS.md` | Yes | all modes | never | No | strategic project doc |
| `README.md` | Yes | all modes | never | No | strategic project doc |
| `DESIGN.md` | Optional | UI-bearing projects only | never | No | root design SSOT |
| `main/README.md` | Yes | all modes | preserve | No | workspace intro |
| `main/.gitignore` | Yes | all modes | preserve | No | generic ignores |
| `main/.env.example` | Yes | all modes | preserve | No | placeholder only |
| `main/docs/project_overview.md` | Yes | all modes | never | No | project SSOT seed |
| `main/docs/tech_stack.md` | Yes | all modes | preserve | No | stack decisions |
| `main/docs/history_archives/history.md` | Yes | all modes | preserve | No | history seed |
| `main/specs/_template/spec.md` | Yes | all modes | never | No | minimal spec mode |
| `main/specs/_template/contracts.md` | Yes | all modes | never | No | minimal completion contract |
| `main/work_queue/progress.md` | Yes | all modes | preserve | No | project progress seed |
| `main/src/.gitkeep` | Yes | all modes | preserve | No | workspace seed |
| `main/tests/.gitkeep` | Yes | all modes | preserve | No | workspace seed |
| `main/contexts/.gitkeep` | Yes | all modes | preserve | No | context artifacts |
| `main/temp/todo.md` | Yes | all modes | preserve | No | scratchpad |
| `main/temp/temp.md` | Yes | all modes | preserve | No | scratchpad |
