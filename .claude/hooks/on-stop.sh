#!/bin/bash
# .claude/hooks/on-stop.sh
# Cleanup and summary when agent stops

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "Agent session completed"
echo ""

# Show git status summary
if git rev-parse --is-inside-work-tree &>/dev/null; then
    BRANCH=$(git branch --show-current)
    CHANGES=$(git status --porcelain | wc -l | tr -d ' ')
    STAGED=$(git diff --cached --numstat | wc -l | tr -d ' ')

    echo "Git Status:"
    echo "   Branch: $BRANCH"
    echo "   Uncommitted changes: $CHANGES files"
    echo "   Staged for commit: $STAGED files"

    if [[ "$CHANGES" -gt 0 ]]; then
        echo ""
        echo "Modified files:"
        git status --porcelain | head -10
        [[ "$CHANGES" -gt 10 ]] && echo "   ... and $((CHANGES - 10)) more"
    fi
fi

echo ""

# Run quick validation
echo "Quick validation:"

# Check for TypeScript/JavaScript errors
if [[ -f "$PROJECT_ROOT/frontend/package.json" ]]; then
    cd "$PROJECT_ROOT/frontend"
    if grep -q '"typecheck"' package.json 2>/dev/null; then
        npm run typecheck 2>/dev/null && echo "   TypeScript: OK" || echo "   TypeScript: Errors found"
    elif grep -q '"build"' package.json 2>/dev/null; then
        npm run build 2>/dev/null && echo "   Frontend build: OK" || echo "   Frontend build: Errors found"
    fi
    cd "$PROJECT_ROOT"
fi

# Check for Python syntax errors
if [[ -d "$PROJECT_ROOT/backend" ]]; then
    PYTHON_ERRORS=$(find "$PROJECT_ROOT/backend" -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" -not -path "*/__pycache__/*" -exec python -m py_compile {} \; 2>&1 | wc -l)
    if [[ "$PYTHON_ERRORS" -eq 0 ]]; then
        echo "   Python syntax: OK"
    else
        echo "   Python syntax: $PYTHON_ERRORS errors"
    fi
fi

echo ""
echo "Remember: Create a PR to merge changes into main/master"

exit 0
