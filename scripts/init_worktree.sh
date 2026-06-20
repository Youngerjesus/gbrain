#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: scripts/init_worktree.sh <task-worktree-path> [branch-name]" >&2
  exit 64
fi

target_path="$1"
branch_name="${2:-codex/$(basename "$target_path")}"

repo_root="$(git rev-parse --show-toplevel)"
mkdir -p "$(dirname "$target_path")"

if [[ -d "$target_path/.git" || -f "$target_path/.git" ]]; then
  existing_root="$(git -C "$target_path" rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ "$existing_root" != "$target_path" ]]; then
    echo "Existing path is not a git worktree root: $target_path" >&2
    exit 65
  fi
  echo "Worktree already exists: $target_path"
else
  if git show-ref --verify --quiet "refs/heads/$branch_name"; then
    git -C "$repo_root" worktree add "$target_path" "$branch_name"
  else
    git -C "$repo_root" worktree add -b "$branch_name" "$target_path" HEAD
  fi
fi

if [[ -f "$repo_root/bun.lockb" || -f "$repo_root/package.json" ]]; then
  if command -v bun >/dev/null 2>&1; then
    (cd "$target_path" && bun install --frozen-lockfile)
  else
    echo "bun not found; skipping dependency install" >&2
  fi
fi

echo "Initialized worktree: $target_path"
echo "Branch: $(git -C "$target_path" branch --show-current)"
