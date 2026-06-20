---
name: skill-creator
description: Create or update Codex skills as conformant, tested, non-overlapping capability packages with lean SKILL.md files, one-hop references, optional helper scripts, and verification evidence.
---

# Skill Creator

Use this skill when creating a new Codex skill or materially updating an existing one. It ports the gbrain skill-creator idea into Codex conventions: a skill is a routed capability package, not just a markdown note.

reference @./extend_codex_with_skills.md

## Contract

This skill guarantees:

- The skill has Codex-native frontmatter with `name` and `description`.
- The body declares when to use it, the workflow, output expectations, and anti-patterns.
- Supporting references, scripts, templates, or assets are one hop from `SKILL.md`.
- Existing skills are checked for overlap before a new skill is added.
- Verification evidence is collected with repo-native checks before calling the skill complete.

## Core Principles

### Concise is Key

Assume the model is already strong. Add only context that the model would not reliably infer on its own.

### Match Degrees of Freedom to Risk

- Use freeform instructions when multiple approaches are valid.
- Use templates or pseudocode when a preferred pattern exists.
- Use scripts or assets when consistency and reliability matter.

### Keep the Skill Modular

Every skill should have:

- a focused trigger description
- a lean `SKILL.md`
- optional references, assets, or scripts only when they materially help

## Workflow

1. Define the skill's exact job and trigger conditions.
2. Check nearby skills for overlap. Extend an existing skill when the new capability is not MECE.
3. Choose the minimum files needed: `SKILL.md` first, then `references/`, `scripts/`, `templates/`, or `assets/` only when they materially improve reliability.
4. Create `SKILL.md` with explicit routing guidance, a contract, workflow, output format, and anti-patterns.
5. Put deterministic behavior in scripts instead of prose when consistency matters.
6. Verify all relative references are one hop away from `SKILL.md`.
7. Add or update a repo-native verification test when the skill changes durable behavior.
8. Run the narrow verification first, then `scripts/verify`.

## Output Format

Return the files created or changed, the verification commands run, and any overlap or follow-up risks. For new skills, include the canonical path `.codex/skills/<name>/SKILL.md`.

## Anti-Patterns

- Creating a skill for one-off work that will not be reused.
- Copying gbrain, Claude, or host-specific frontmatter directly into Codex skills.
- Hiding complex deterministic behavior in prose when a script would be safer.
- Adding deep reference chains that the agent will not reliably load.
- Treating a new skill as complete without verification evidence.
