#!/bin/bash
# .claude/hooks/pre-file-write.sh
# Validates file write operations stay within project
# Exit codes: 0 = allow, 2 = block

set -euo pipefail

TOOL_INPUT="$1"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Extract file path from JSON input
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // .path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0  # Allow if we can't determine path
fi

# Resolve to absolute path
if [[ "$FILE_PATH" != /* ]]; then
    FILE_PATH="$PROJECT_ROOT/$FILE_PATH"
fi
RESOLVED_PATH=$(realpath -m "$FILE_PATH")

# Check if path is within project
if [[ "$RESOLVED_PATH" != "$PROJECT_ROOT"* ]]; then
    echo "BLOCKED: Cannot write files outside project directory"
    echo "   Attempted path: $FILE_PATH"
    echo "   Project root: $PROJECT_ROOT"
    exit 2
fi

# Block writes to sensitive files
SENSITIVE_PATTERNS=(
    ".env.production"
    "*.pem"
    "*.key"
    "*credentials*"
    "*secret*"
)

FILENAME=$(basename "$FILE_PATH")
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if [[ "$FILENAME" == $pattern ]]; then
        echo "WARNING: Writing to potentially sensitive file: $FILENAME"
        # Not blocking, just warning - remove 'exit 2' if you want to block
    fi
done

exit 0
