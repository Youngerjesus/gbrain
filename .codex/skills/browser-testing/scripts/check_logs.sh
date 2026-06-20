#!/bin/bash
# Description: Waits for the main dev environment to be ready and prints recent log lines on failure.

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
MAIN_ROOT="$WORKSPACE_ROOT/main"
LOG_FILE="$MAIN_ROOT/dev_env.log"
TARGET_URL=${1:-"http://localhost:3000"}
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "Waiting for environment at $TARGET_URL to be ready..."

for ((i=1; i<=MAX_RETRIES; i++)); do
    # curl -s (silent), -f (fail silently on server errors), output to dev/null
    if curl -s -f "$TARGET_URL" > /dev/null; then
        echo "Success: Environment is ready and responding at $TARGET_URL!"
        exit 0
    fi
    echo "Waiting... ($i/$MAX_RETRIES)"
    sleep "$RETRY_INTERVAL"
done

echo "Error: Environment failed to become ready within the timeout."
if [ -f "$LOG_FILE" ]; then
    echo "Recent logs from $LOG_FILE:"
    tail -n 50 "$LOG_FILE" || true
else
    echo "Log file not found at $LOG_FILE"
fi
exit 1
