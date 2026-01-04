#!/bin/bash
# .claude/hooks/post-file-write.sh
# Auto-format files after writes

set -euo pipefail

FILE_PATHS="$1"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Process each file path (newline separated)
echo "$FILE_PATHS" | while IFS= read -r FILE_PATH; do
    [[ -z "$FILE_PATH" ]] && continue
    [[ ! -f "$FILE_PATH" ]] && continue

    EXTENSION="${FILE_PATH##*.}"

    case "$EXTENSION" in
        py)
            # Python formatting
            if command -v ruff &> /dev/null; then
                ruff format "$FILE_PATH" 2>/dev/null || true
                ruff check --fix "$FILE_PATH" 2>/dev/null || true
            elif command -v black &> /dev/null; then
                black --quiet "$FILE_PATH" 2>/dev/null || true
            fi
            ;;
        js|jsx|ts|tsx|json|css|scss|md)
            # JavaScript/TypeScript/JSON/CSS/Markdown formatting
            if command -v prettier &> /dev/null; then
                prettier --write "$FILE_PATH" 2>/dev/null || true
            fi
            ;;
        sql)
            # SQL formatting (if you have a formatter)
            if command -v pg_format &> /dev/null; then
                pg_format -i "$FILE_PATH" 2>/dev/null || true
            fi
            ;;
    esac
done

exit 0
