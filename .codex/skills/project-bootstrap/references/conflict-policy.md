# Conflict Policy

Default rule: preserve existing files and report conflicts instead of overwriting.

## Allowed Automatic Template Updates

- `.codex/agents/*.toml`
- `.codex/skills/project-bootstrap/**`
- `.codex/docs/template_customization.md`

## Never Overwrite Automatically

- `AGENTS.md`
- `DESIGN.md`
- `README.md`
- `main/docs/project_overview.md`
- `main/specs/_template/spec.md`
- `main/specs/_template/contracts.md`

## Report Labels

- `created`: file did not exist and was created
- `skipped`: file already existed and was intentionally preserved
- `needs-merge`: template and existing file conflict; manual merge needed
- `template-updated`: template-managed file was safely updated
