# Extending Codex With Skills

## Skill Location

Project skills live under:

```text
.codex/skills/<skill-name>/SKILL.md
```

## Recommended Structure

```text
<skill-name>/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

## SKILL.md Format

Each skill should include YAML frontmatter followed by Markdown instructions.

```markdown
---
name: my-skill
description: One sentence describing what the skill does and when it should be used.
---

# My Skill
...
```

## What to Put in SKILL.md

- The role the skill plays
- When to trigger it
- The workflow to follow
- Any constraints or anti-patterns
- References to supporting files when needed

## When to Split Content

Move content out of `SKILL.md` when:

- the file gets long enough to create context bloat
- the skill supports multiple variants or frameworks
- a script or template can do the work more reliably than prose

## Best Practices

- Keep `SKILL.md` under roughly 500 lines.
- Avoid deep reference chains.
- Prefer one level of indirection from `SKILL.md`.
- Keep descriptions trigger-oriented, not marketing-oriented.
- Do not add extra docs unless they help the agent do the task.
