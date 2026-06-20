#!/bin/bash
# Description: Stops the main worktree dev environment using the official repo wrapper.

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
MAIN_ROOT="$WORKSPACE_ROOT/main"

cd "$MAIN_ROOT" || exit 1
exec bash scripts/stop_dev_env.sh
