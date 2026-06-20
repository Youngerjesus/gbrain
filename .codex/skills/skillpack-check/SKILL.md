---
name: skillpack-check
description: Check the local Codex skillpack for structural health, missing sections, unsafe host-specific leaks, and verification alignment before a user or automation relies on it.
---

# Skillpack Check

Use this skill when the user asks whether the Codex skillpack is healthy, whether new skills conform, or whether a skill bundle needs maintenance.

## Contract

`skillpack-check` produces a structured health report with:

- `healthy`: true only when no required remediation remains.
- `summary`: one line safe to quote.
- `actions`: concrete remediation steps.
- `skills_checked`: count of inspected skills.
- `issues`: structured issue objects with skill, severity, code, and message.

## Workflow

1. Run `.codex/skills/skillpack-check/scripts/skillpack_check.py` from the repo root.
2. Inspect every `.codex/skills/*/SKILL.md`.
3. Validate frontmatter and required body sections.
4. Check for host-specific leaks such as machine paths or non-Codex tool conventions.
5. Confirm `scripts/verify` runs lifecycle verification when lifecycle skills are present.
6. Report actions before raw details.

## Output Format

Return the one-line summary, action list, and JSON report path or inline JSON when requested.

## Anti-Patterns

- Treating warnings as successful health when they require action.
- Running this on every chat turn instead of on demand or as a bounded preflight.
- Using string matches as final semantic proof; use them only for leak detection and structural hints.
- Ignoring a missing verification hook.
