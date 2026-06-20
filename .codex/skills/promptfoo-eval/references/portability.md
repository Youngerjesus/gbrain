# Promptfoo Eval Portability

Use this reference when applying `promptfoo-eval` in a project that may not already have promptfoo installed or configured.

## Discovery Checklist

Inspect before creating files:

- `promptfooconfig.*`, `promptfoo.yaml`, `promptfoo.yml`, `promptfoo.json`
- `package.json` scripts and lockfiles
- existing eval, prompt, test, or assertion folders
- `.gitignore` and runtime artifact conventions
- `node --version`, `npm --version`, and available package manager
- environment variables or docs for providers
- changed prompt/instruction files and baseline availability

## Mode Selection

- Use **existing-config** when the project already owns promptfoo conventions.
- Use **ephemeral-config** when no config exists or the current feedback needs temporary coverage.
- Use **deterministic-only** when an API provider is unavailable but mechanical properties can still be checked.
- Use **blocked** only when promptfoo cannot execute at all.

## Ephemeral Harness Layout

Create temporary harnesses under:

```text
.runtime/promptfoo-eval/<eval-id>/
  promptfooconfig.yaml
  providers/
    read_file_provider.js
  README.md
```

Write result artifacts under:

```text
.runtime/promptfoo/<timestamp>-<label>/
  results.json
  report.html
```

Keep generated runtime harnesses local unless the user explicitly asks to commit reusable eval coverage.

## Portability Rules

- Do not hardcode absolute paths in templates.
- Prefer relative paths from the project root.
- If using an `exec:` provider, account for promptfoo config `basePath`. Provider scripts should derive the repo root from `__dirname` or accept it through context/options.
- If `npx` fails due cache corruption or concurrent install state, retry with `NPM_CONFIG_CACHE=.runtime/npm-cache`.
- Preserve failed run artifacts and rerun into a new result directory.
