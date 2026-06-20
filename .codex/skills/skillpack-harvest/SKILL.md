---
name: skillpack-harvest
description: Copy a mature host Codex skill into this repo's skillpack through dry-run preview, privacy lint, genericization review, safe path handling, and verification.
---

# Skillpack Harvest

Use this skill when the user wants to bring a proven skill from another repo into this Codex skillpack, publish a local skill upstream, or promote a custom skill into the shared bundle.

## Contract

A harvest is complete only when:

- The source skill is mature enough to share.
- Dry-run preview lists the exact file set.
- Privacy lint finds no private names, emails, machine paths, or internal channels.
- Files are copied, not moved.
- Symlinks and path escapes are rejected.
- The destination skill passes `skillpack-check` and `scripts/verify`.

## Workflow

1. Confirm source repo root, skill slug, and destination repo.
2. Run dry-run harvest first with `.codex/skills/skillpack-harvest/scripts/skillpack_harvest.py <slug> --from <source> --to <dest> --dry-run`.
3. Read the source skill and genericize host-specific language before the real copy.
4. Run the real harvest without `--dry-run`.
5. Run `python3 .codex/skills/skillpack-check/scripts/skillpack_check.py`.
6. Run `scripts/verify`.
7. Report files written and any lint bypass rationale.

## Output Format

Report `status`, copied or planned files, lint findings, and follow-up verification commands.

## Anti-Patterns

- Skipping dry-run.
- Trusting the privacy linter instead of doing editorial genericization.
- Harvesting a skill still in flux.
- Moving or deleting source files.
- Batch harvesting multiple skills without reviewing each one.
