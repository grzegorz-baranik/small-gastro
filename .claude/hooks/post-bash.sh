#!/bin/bash
# .claude/hooks/post-bash.sh
# Logs executed commands for audit trail

set -euo pipefail

TOOL_INPUT="$1"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOG_FILE="$PROJECT_ROOT/.claude/hooks/command-history.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Extract command
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // "unknown"')

# Log with timestamp
echo "[$(date -Iseconds)] $COMMAND" >> "$LOG_FILE"

# Keep log file manageable (last 1000 entries)
if [[ -f "$LOG_FILE" ]]; then
    tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi

exit 0
