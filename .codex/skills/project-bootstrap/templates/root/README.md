# Project Name

Short description of the project.

## Bootstrap Checklist

1. Update `AGENTS.md` with the project's actual product direction, operating rules, and constraints.
2. Fill `docs/project_overview.md`.
3. Fill `docs/tech_stack.md`.
4. Decide whether this project needs a root `DESIGN.md`.
5. Copy `specs/_template/` to create the first feature spec.

## Task Worktree Initialization

If new task worktrees need repo-specific setup, add an optional `scripts/init_worktree.sh`.

The script must be idempotent, local-safe, and accept the task worktree path as its first argument. Use it only for setup that must happen when a fresh task worktree is created and is not covered by normal install or verification commands. Keep secrets and machine-specific values untracked; do not embed them in the script.

## Repository Layout

- `/`: primary workspace for implementation-facing docs, specs, code, and tests
- `.codex/`: agent and skill definitions
- root docs: project-level operating contracts
