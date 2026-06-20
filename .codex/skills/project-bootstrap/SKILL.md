---
name: project-bootstrap
description: Initialize or adopt a generic software project with Codex operating structure, template docs, and minimal spec/contracts support.
---

# Project Bootstrap

Use this skill when starting a new project or when adding Codex operating structure to an existing repository.

This skill is intentionally script-free. It operates from static templates and explicit mode rules so repeated runs stay predictable.

reference @./references/mode-rules.md
reference @./references/manifest.md
reference @./references/conflict-policy.md
reference @./references/mode-examples.md
reference @./references/curated-bundle.md
reference @./references/customization-checklist.md

## Goal

Install a reusable development operating system for a generic software project:

- `.codex` with shared agents
- root `AGENTS.md`
- optional root `DESIGN.md`
- `main/` workspace templates
- minimal spec mode with `spec.md` and `contracts.md`

The default `.codex` install is curated, not exhaustive. Reuse the strongest existing agents and skills, but only after removing domain-specific or stack-specific assumptions.

Generated templates receive the curated runtime skill bundle. The source bootstrap skill `project-bootstrap` remains in the source repository because its nested template payload should not recurse into generated templates by default.

## Bootstrap Modes

Choose one mode before writing files:

- `fresh-init`
- `adopt-existing`
- `upgrade-sync`

Follow the mode rules exactly. If the correct mode is unclear, inspect the repository first and prefer the least destructive interpretation.

## Required Behavior

1. Inspect the repository and determine the bootstrap mode.
2. Use `references/mode-rules.md` as the authoritative mode selection rule.
3. Use `references/manifest.md` as the file-level source of truth.
4. Apply `references/conflict-policy.md` before creating or replacing any file.
5. Use `references/mode-examples.md` as the expected behavior reference when the repo state is ambiguous.
6. Generate `DESIGN.md` only when the repo or user intent indicates a UI-bearing project.
7. Add the bootstrap version marker to `.codex/docs/template_customization.md`.
8. Report the result using:
   - `created`
   - `skipped`
   - `needs-merge`
   - `template-updated`

## Design Signals

Recommend generating `DESIGN.md` when any of these signals exist:

- the user says the project has UI, web, app, brand, or design-system work
- the repo already contains `frontend/`, `app/`, `ui/`, `components/`, or `design-system/`

If these signals are absent, default to not generating `DESIGN.md`.

## Minimal Spec Mode

Bootstrap only these spec templates by default:

- `main/specs/_template/spec.md`
- `main/specs/_template/contracts.md`

Do not force `plan.md`, `tasks.md`, or `design.md` during bootstrap. Those can be added later when the project needs them.
