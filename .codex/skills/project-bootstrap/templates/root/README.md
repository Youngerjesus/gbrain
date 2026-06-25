# Project Name

Short description of the project.

## Bootstrap Checklist

1. Update `AGENTS.md` with the project's actual product direction, operating rules, and constraints.
2. Fill `docs/project_overview.md`.
3. Fill `docs/tech_stack.md`.
4. Decide whether this project needs a root `DESIGN.md`.
5. Create a single requirement under `requirements/` or a complete upfront goal sequence under `goal-requirements/`.

## Task Worktree Initialization

Goal-requirements implementation uses isolated task worktrees. Run `scripts/init_worktree.sh <task-worktree-path>` before coding in a task worktree.

The script is idempotent and local-safe. It rejects the primary/main worktree, requires a non-main task branch, checks that the target worktree has `scripts/verify`, and keeps secrets and machine-specific values untracked.

## Repository Layout

- `/`: primary workspace for implementation-facing docs, specs, code, and tests
- `.codex/`: agent and skill definitions
- root docs: project-level operating contracts
