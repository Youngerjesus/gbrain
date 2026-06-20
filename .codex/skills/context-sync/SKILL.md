---
name: context-sync
description: Keep root/project AGENTS.md, docs/AUTOPILOT_DESIGN.md, docs/META_DESIGN.md, docs, specs, and .codex guidance aligned when a requirement, policy, or assumption changes.
---

# Context Sync

Use this skill when a policy, architecture decision, requirement, or terminology change needs to be reflected across multiple documents.

## When To Use

- A spec assumption changes and related docs still mention the old one
- A workflow or policy in `AGENTS.md` or `.codex` changed
- A project-level decision must be propagated into `docs/`, `specs/`, or template assets

## Workflow

1. Identify the old context and the new context.
2. Search the active doc surface:
   - `AGENTS.md`
   - `project_manager/AGENTS.md`
   - managed repo root `AGENTS.md` when the change affects repo-local product or execution guidance
   - `docs/AUTOPILOT_DESIGN.md`
   - `docs/META_DESIGN.md`
   - `DESIGN.md` where present
   - `README.md`
   - `.codex/**`
   - `docs/**`
   - `specs/**`
   - `repo_name/docs/**`
   - `repo_name/specs/**`
3. Filter out irrelevant matches and archives.
4. Update only the files that actually encode the outdated assumption.
5. Report:
   - `changed`
   - `ignored`
   - `conflicts`
   - `follow-up`

## Constraints

- Do not blindly find-and-replace.
- Do not rewrite history or archive docs unless explicitly asked.
- If the replacement policy is ambiguous, stop and report the conflict.
