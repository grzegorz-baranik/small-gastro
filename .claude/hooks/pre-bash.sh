#!/bin/bash
# .claude/hooks/pre-bash.sh
# Validates bash commands before execution
# Exit codes: 0 = allow, 2 = block

set -euo pipefail

TOOL_INPUT="$1"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Extract the command from JSON input
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')

if [[ -z "$COMMAND" ]]; then
    exit 0  # Allow if we can't parse
fi

# =============================================================================
# BLOCKED COMMANDS (exit 2 to block)
# =============================================================================

# Block git operations that affect main/master
if echo "$COMMAND" | grep -qE 'git\s+(merge|rebase).*\s+(main|master)'; then
    echo "BLOCKED: Direct merge/rebase to main/master is not allowed"
    echo "   Use pull requests for integration to protected branches"
    exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+push.*\s+(origin\s+)?(main|master)'; then
    echo "BLOCKED: Direct push to main/master is not allowed"
    echo "   Use pull requests for integration to protected branches"
    exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+checkout\s+(main|master)\s*&&\s*git\s+merge'; then
    echo "BLOCKED: Merge workflow to main/master detected"
    exit 2
fi

# Block operations outside project directory
if echo "$COMMAND" | grep -qE '(rm|mv|cp|cat|nano|vim|code)\s+[^|]*(/etc/|/usr/|/var/|/home/(?!.*'"$PROJECT_ROOT"')|~/)'; then
    echo "BLOCKED: File operations outside project directory"
    exit 2
fi

# Block dangerous system commands
if echo "$COMMAND" | grep -qE '^\s*(sudo|su\s|chmod\s+777|rm\s+-rf\s+/|mkfs|dd\s+if=)'; then
    echo "BLOCKED: Potentially dangerous system command"
    exit 2
fi

# =============================================================================
# AUTO-APPROVED COMMANDS (exit 0 with empty stdout to skip prompt)
# =============================================================================

# Git operations (except protected branch operations blocked above)
if echo "$COMMAND" | grep -qE '^git\s+(status|log|diff|branch|add|commit|push|pull|fetch|stash|checkout|switch|restore|worktree|rebase|reset)'; then
    exit 0
fi

# npm/yarn/pnpm commands
if echo "$COMMAND" | grep -qE '^(npm|yarn|pnpm|npx)\s+(install|ci|run|test|build|lint|format|start|dev|exec)'; then
    exit 0
fi

# Python/pip commands
if echo "$COMMAND" | grep -qE '^(pip|pip3|python|python3|poetry|pdm|uv)\s+(install|run|test|-m\s+pytest|-m\s+pip|-m\s+py_compile|-c)'; then
    exit 0
fi

# pytest directly
if echo "$COMMAND" | grep -qE '^pytest'; then
    exit 0
fi

# Docker commands
if echo "$COMMAND" | grep -qE '^docker(\s+compose)?\s+(build|up|down|start|stop|restart|logs|ps|exec|run|pull)'; then
    exit 0
fi

# Linting and formatting tools
if echo "$COMMAND" | grep -qE '^(eslint|prettier|black|ruff|isort|mypy|flake8|pylint)'; then
    exit 0
fi

# Safe read-only commands
if echo "$COMMAND" | grep -qE '^(ls|cat|head|tail|grep|find|wc|pwd|echo|which|type|file|stat)\s'; then
    exit 0
fi

# Database CLI tools (read operations)
if echo "$COMMAND" | grep -qE '^psql.*(-c\s+.*(SELECT|\\d|\\l|\\dt))'; then
    exit 0
fi

# Alembic migrations
if echo "$COMMAND" | grep -qE '^(alembic|python\s+-m\s+alembic)\s+(upgrade|downgrade|revision|history|current)'; then
    exit 0
fi

# Make commands
if echo "$COMMAND" | grep -qE '^make\s+(test|lint|format|build|dev|run|install|clean)'; then
    exit 0
fi

# curl/wget for downloading (often needed for setup)
if echo "$COMMAND" | grep -qE '^(curl|wget)\s'; then
    exit 0
fi

# Directory navigation and creation within project
if echo "$COMMAND" | grep -qE '^(cd|mkdir|touch)\s'; then
    exit 0
fi

# jq for JSON processing
if echo "$COMMAND" | grep -qE '^jq\s'; then
    exit 0
fi

# timeout command (used for testing)
if echo "$COMMAND" | grep -qE '^timeout\s'; then
    exit 0
fi

# If not explicitly approved or blocked, let it pass to normal permission flow
exit 0
