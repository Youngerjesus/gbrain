# Artifact Contract

All outputs from this skill are repository-local reference artifacts.

## Storage Path

Save generated files under:

```text
project_manager/contexts/design-html/<screen-name>-<YYYYMMDD>/
```

Required files:

- `finalized.html`
- `finalized.json`

When this skill is used inside `project_manager/design_loop.py`, the orchestrator-provided round directory under `project_manager/contexts/design-loop/...` takes precedence.

## `finalized.json` Shape

```json
{
  "mode": "approved-mockup | plan-driven | freeform | evolve",
  "source_design_context": "path or null",
  "html_file": "absolute path to finalized.html",
  "pretext_pattern": "basic-layout | segmented-tight-fit | obstacle-flow | full-lines",
  "screen": "screen name",
  "branch": "git branch",
  "date": "ISO-8601"
}
```

## HTML Requirements

- standalone file
- inline or local CSS only
- semantic HTML5 structure
- tokenized CSS custom properties
- real product copy
- responsive layout behavior
- uses the vendored Pretext runtime
  If the artifact lives outside the skill folder, either copy `pretext.js` into a sibling `vendor/` directory or reference the vendored runtime with a valid repo-local relative path.

## Relationship to the Codebase

- This artifact is a design and review deliverable.
- It is allowed to be more page-specific than the shared frontend component system.
- It should still feel directly translatable into the existing frontend stack.
- Do not claim it is already production-integrated unless the user separately asks for that implementation step.
