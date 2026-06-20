# Loop Contract

`design-hardening-loop` is a code-driven orchestration skill.

## Inputs

- `--worktree-root`: target worktree that owns the website code and server helpers
- `--app-url`: live URL inspected during review rounds
- `--consultation-path`: prior `design-consultation` result markdown
- `--target-brief-path`: run-specific route list and success criteria markdown
- `--max-rounds`: optional, default `10`
- `--run-name`: optional name for a new run directory
- `--run-dir`: existing run directory to resume; this is the canonical resume entrypoint

## Storage

All outputs live under:

```text
project_manager/contexts/design-loop/<run-name>-<YYYYMMDD-HHMMSS>/
```

Required outputs:

- `policy-summary.md`
- `consultation.base.md`
- `consultation.current.md`
- `consultation.md`
- `target-brief.md`
- `state.json`
- `round-01-generator/finalized.html`
- `round-01-generator/finalized.json`
- `round-01-review.md`
- `best-round.json`
- `final.md`

## Loop Roles

- Generator: `design-html` standard, artifact-only, no product code changes, same session reused across rounds, optimize for visual polish and system consistency
- Evaluator: `design-review` standard, live browser evidence required, fresh session per round, judge first-screen impact, polish, rhythm, typography, consistency, and mobile intentionality
- Consultation: external prerequisite input for project-level visual direction, with run-local amendments allowed when direction conflict is proven
- Target brief: external prerequisite input for run-specific routes, exclusions, approval criteria, and browser-reviewable route contract

## Completion

- Early success: evaluator returns no `high` severity findings
- Consultation revision: when the evaluator explicitly flags a visual direction conflict or the same `high` visual finding repeats twice, resume the current evaluator session to create a consultation amendment before the next generator round
- Route precondition failure: if a target-brief route is not browser-reviewable in the live app, stop the run with `route_precondition_failed`; do not treat it as a consultation amendment
- Round limit: select the best-scoring round and record the remaining debt
- Canonical final: the artifact referenced from `final.md`
