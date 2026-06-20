# Curated Bundle

`project-bootstrap` installs a curated default bundle. It is intentionally selective.

## Default Agents

- `document-writer`
- `product-builder`
- `architect`
- `project-reviewer`
- `decision-brake-thinker`
- `decision-brake-reviewer`
- `decision-brake-explorer`
- `decision-brake-scope-targeter`
- `decision-brake-causal-coverage-reviewer`
- `decision-brake-readiness-reviewer`
- `implementation-brake-reviewer`
- `plan-eng-scope-reuse-reviewer`
- `plan-eng-architecture-contract-reviewer`
- `plan-eng-verification-failure-reviewer`
- `grill-me-risk-finder`
- `grill-me-alternative-finder`
- `grill-me-verification-finder`
- `grill-me-handoff-reviewer`
- `grill-me-requirement-shape-finder`
- `requirement-clarifier-post-draft-reviewer`
- `requirement-conformance-reviewer`
- `scenario-path-separation-reviewer`
- `scenario-parameter-mutation-reviewer`
- `scenario-recovery-observability-reviewer`
- `task-master`
- `task-reviewer`
- `code-reviewer`
- `performance-reviewer`
- `testing-reviewer`
- `security-reviewer`
- `verifier`
- `context-synchronizer`
- `context-loader`
- `visual-qa-reviewer`
- `reference-fidelity-reviewer`
- `staff-engineer`
- `qa-engineer`

## Source-Only Bootstrap Skill

- `project-bootstrap`

`project-bootstrap` is the bootstrap source skill that builds the template. It is not copied into generated templates by default because its own nested template payload would recurse.

## Default Installed Skills

- `context-sync`
- `context-loading`
- `closeout`
- `goal-requirement-orchestrator`
- `production-readiness`
- `decision-brake`
- `implementation-brake`
- `grill-me`
- `requirement-clarifier`
- `secondary-plan`
- `research`
- `technical-design`
- `scenario-brake`
- `plan-design-review`
- `plan-ux-review`
- `plan-devex-review`
- `plan-eng-review`
- `ux-review`
- `devex-review`
- `spec-creator`
- `spec-reviewer`
- `task-master-planning`
- `tdd-workflow`
- `visual-qa-hardening`
- `systematic-debugging`

## Selection Rules

- Prefer existing proven assets over inventing new ones.
- Remove domain-specific language, proprietary workflows, and hard stack assumptions.
- Exclude optional specialist assets from the default bundle when they only apply to narrow UI, infra, or domain situations.
- Include `performance-reviewer` as an available conditional specialist, but do not revive broad always-on reviewer routing such as `maintainability-reviewer`, `red-team-reviewer`, `api-reviewer`, `database-reviewer`, or `ui-ux-reviewer`.
