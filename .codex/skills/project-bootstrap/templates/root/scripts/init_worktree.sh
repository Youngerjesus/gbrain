#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'init_worktree.sh: %s\n' "$*" >&2
  exit 1
}

if [ "$#" -ne 1 ]; then
  fail "usage: scripts/init_worktree.sh <task-worktree-path>"
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source_root="$(cd "$script_dir/.." && pwd -P)"
target_arg="$1"

[ -d "$target_arg" ] || fail "task worktree path does not exist: $target_arg"

target_root_raw="$(git -C "$target_arg" rev-parse --show-toplevel 2>/dev/null)" \
  || fail "task worktree path is not inside a git worktree: $target_arg"
target_root="$(cd "$target_root_raw" && pwd -P)"
target_path="$(cd "$target_arg" && pwd -P)"

[ "$target_path" = "$target_root" ] \
  || fail "task worktree path must be the git worktree root: $target_arg"

source_common="$(git -C "$source_root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
  || fail "source root is not a git repository: $source_root"
target_common="$(git -C "$target_root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
  || fail "target root is not a git repository: $target_root"

[ "$source_common" = "$target_common" ] \
  || fail "task worktree must belong to the same git repository as $source_root"

primary_worktree=""
while IFS= read -r line; do
  case "$line" in
    worktree\ *)
      primary_worktree="${line#worktree }"
      break
      ;;
  esac
done < <(git -C "$target_root" worktree list --porcelain)

[ -n "$primary_worktree" ] || fail "cannot identify primary git worktree"
primary_worktree="$(cd "$primary_worktree" && pwd -P)"

[ "$target_root" != "$primary_worktree" ] \
  || fail "target is the primary/main worktree; goal-requirements implementation requires an isolated task worktree"

branch="$(git -C "$target_root" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
[ -n "$branch" ] || fail "task worktree must be on a named non-main branch"
[ "$branch" != "main" ] || fail "task worktree branch is main; use a non-main task branch"

[ -x "$target_root/scripts/verify" ] \
  || fail "target worktree is missing executable scripts/verify"

printf 'worktree setup ok: %s (%s)\n' "$target_root" "$branch"
