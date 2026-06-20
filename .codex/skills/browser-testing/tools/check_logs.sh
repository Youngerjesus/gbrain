#!/bin/bash
# Description: Outputs the last 50 lines of the dev environment log.

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
MAIN_ROOT="$WORKSPACE_ROOT/main"
LOG_FILE="$MAIN_ROOT/dev_env.log"

if [ -f "$LOG_FILE" ]; then
    tail -n 50 "$LOG_FILE"
else
    echo "Log file not found. Did you run start_env.sh?"
fi
