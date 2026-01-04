# Claude Code Hooks Specification

## Overview

This document specifies the hooks configuration for Claude Code agents working on this project. The goal is to enable autonomous, long-running agent sessions while maintaining appropriate guardrails.

**Tech Stack:** React (Frontend) + Python FastAPI (Backend) + PostgreSQL (Database)

---

## Design Principles

1. **Autonomous operation** — Minimize permission prompts for routine development tasks
2. **Project isolation** — All file operations must stay within the project directory
3. **Git safety** — Allow commits and branch pushes, but protect `main`/`master` from direct integration
4. **Development velocity** — Auto-approve tests, linting, Docker, and package management

---

## Hook Types Reference

| Hook Type | Trigger | Use Case |
|-----------|---------|----------|
| `PreToolUse` | Before a tool executes | Validate, block, or auto-approve commands |
| `PostToolUse` | After a tool executes | Log, format, or validate results |
| `Stop` | When agent completes a task | Cleanup, summarize, or notify |

---

## Hooks Configuration

Place this in `.claude/settings.json` (for team-shared) or `.claude/settings.local.json` (for personal use):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-bash.sh \"$CLAUDE_TOOL_INPUT\""
          }
        ]
      },
      {
        "matcher": "WriteFile|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-file-write.sh \"$CLAUDE_TOOL_INPUT\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "WriteFile|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-file-write.sh \"$CLAUDE_FILE_PATHS\""
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-bash.sh \"$CLAUDE_TOOL_INPUT\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/on-stop.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Hook Scripts Implementation

### Directory Structure

```
.claude/
├── settings.json
├── settings.local.json (gitignored)
└── hooks/
    ├── pre-bash.sh
    ├── pre-file-write.sh
    ├── post-file-write.sh
    ├── post-bash.sh
    ├── on-stop.sh
    └── lib/
        └── common.sh
```

---

### 1. Pre-Bash Hook (`pre-bash.sh`)

This hook validates bash commands before execution. It auto-approves safe operations and blocks dangerous ones.

```bash
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
    echo "❌ BLOCKED: Direct merge/rebase to main/master is not allowed"
    echo "   Use pull requests for integration to protected branches"
    exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+push.*\s+(origin\s+)?(main|master)'; then
    echo "❌ BLOCKED: Direct push to main/master is not allowed"
    echo "   Use pull requests for integration to protected branches"
    exit 2
fi

if echo "$COMMAND" | grep -qE 'git\s+checkout\s+(main|master)\s*&&\s*git\s+merge'; then
    echo "❌ BLOCKED: Merge workflow to main/master detected"
    exit 2
fi

# Block operations outside project directory
if echo "$COMMAND" | grep -qE '(rm|mv|cp|cat|nano|vim|code)\s+[^|]*(/etc/|/usr/|/var/|/home/(?!.*'"$PROJECT_ROOT"')|~/)'; then
    echo "❌ BLOCKED: File operations outside project directory"
    exit 2
fi

# Block dangerous system commands
if echo "$COMMAND" | grep -qE '^\s*(sudo|su\s|chmod\s+777|rm\s+-rf\s+/|mkfs|dd\s+if=)'; then
    echo "❌ BLOCKED: Potentially dangerous system command"
    exit 2
fi

# =============================================================================
# AUTO-APPROVED COMMANDS (exit 0 with empty stdout to skip prompt)
# =============================================================================

# Git operations (except protected branch operations blocked above)
if echo "$COMMAND" | grep -qE '^git\s+(status|log|diff|branch|add|commit|push|pull|fetch|stash|checkout|switch|restore)'; then
    exit 0
fi

# npm/yarn/pnpm commands
if echo "$COMMAND" | grep -qE '^(npm|yarn|pnpm|npx)\s+(install|ci|run|test|build|lint|format|start|dev|exec)'; then
    exit 0
fi

# Python/pip commands
if echo "$COMMAND" | grep -qE '^(pip|pip3|python|python3|poetry|pdm|uv)\s+(install|run|test|-m\s+pytest|-m\s+pip)'; then
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
if echo "$COMMAND" | grep -qE '^alembic\s+(upgrade|downgrade|revision|history|current)'; then
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

# If not explicitly approved or blocked, let it pass to normal permission flow
exit 0
```

---

### 2. Pre-File-Write Hook (`pre-file-write.sh`)

Validates that file writes stay within the project directory.

```bash
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
    echo "❌ BLOCKED: Cannot write files outside project directory"
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
        echo "⚠️  WARNING: Writing to potentially sensitive file: $FILENAME"
        # Not blocking, just warning - remove 'exit 2' if you want to block
    fi
done

exit 0
```

---

### 3. Post-File-Write Hook (`post-file-write.sh`)

Runs formatters after file modifications.

```bash
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
```

---

### 4. Post-Bash Hook (`post-bash.sh`)

Logs executed commands for audit trail.

```bash
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
```

---

### 5. Stop Hook (`on-stop.sh`)

Runs when the agent completes a task.

```bash
#!/bin/bash
# .claude/hooks/on-stop.sh
# Cleanup and summary when agent stops

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "🏁 Agent session completed"
echo ""

# Show git status summary
if git rev-parse --is-inside-work-tree &>/dev/null; then
    BRANCH=$(git branch --show-current)
    CHANGES=$(git status --porcelain | wc -l | tr -d ' ')
    STAGED=$(git diff --cached --numstat | wc -l | tr -d ' ')
    
    echo "📊 Git Status:"
    echo "   Branch: $BRANCH"
    echo "   Uncommitted changes: $CHANGES files"
    echo "   Staged for commit: $STAGED files"
    
    if [[ "$CHANGES" -gt 0 ]]; then
        echo ""
        echo "📝 Modified files:"
        git status --porcelain | head -10
        [[ "$CHANGES" -gt 10 ]] && echo "   ... and $((CHANGES - 10)) more"
    fi
fi

echo ""

# Run quick validation
echo "🔍 Quick validation:"

# Check for TypeScript/JavaScript errors
if [[ -f "package.json" ]]; then
    if grep -q '"typecheck"' package.json 2>/dev/null; then
        npm run typecheck 2>/dev/null && echo "   ✅ TypeScript: OK" || echo "   ❌ TypeScript: Errors found"
    fi
fi

# Check for Python syntax errors
if [[ -f "pyproject.toml" ]] || [[ -f "requirements.txt" ]]; then
    PYTHON_ERRORS=$(find . -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" -exec python3 -m py_compile {} \; 2>&1 | wc -l)
    if [[ "$PYTHON_ERRORS" -eq 0 ]]; then
        echo "   ✅ Python syntax: OK"
    else
        echo "   ❌ Python syntax: $PYTHON_ERRORS errors"
    fi
fi

echo ""
echo "💡 Remember: Create a PR to merge changes into main/master"

exit 0
```

---

## Permissions Configuration

In addition to hooks, configure these permissions in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(yarn *)",
      "Bash(pnpm *)",
      "Bash(npx *)",
      "Bash(pip install *)",
      "Bash(pip3 install *)",
      "Bash(poetry *)",
      "Bash(python -m pytest*)",
      "Bash(pytest*)",
      "Bash(docker *)",
      "Bash(docker-compose *)",
      "Bash(docker compose *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git push origin *)",
      "Bash(git checkout *)",
      "Bash(git switch *)",
      "Bash(git branch *)",
      "Bash(git stash *)",
      "Bash(git fetch *)",
      "Bash(git pull *)",
      "Bash(git status*)",
      "Bash(git log*)",
      "Bash(git diff*)",
      "Bash(alembic *)",
      "Bash(make *)",
      "Bash(ruff *)",
      "Bash(black *)",
      "Bash(eslint *)",
      "Bash(prettier *)",
      "Bash(psql *)",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(head *)",
      "Bash(tail *)",
      "Bash(grep *)",
      "Bash(find *)",
      "Bash(mkdir *)",
      "Bash(touch *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Read(*)",
      "Write(./**)",
      "Edit(./**)"
    ],
    "deny": [
      "Bash(git push * main*)",
      "Bash(git push * master*)",
      "Bash(git merge * main*)",
      "Bash(git merge * master*)",
      "Bash(sudo *)",
      "Bash(rm -rf /*)",
      "Write(../**)",
      "Write(/etc/**)",
      "Write(/usr/**)",
      "Write(~/**)"
    ]
  }
}
```

---

## Setup Instructions

1. **Create the hooks directory:**
   ```bash
   mkdir -p .claude/hooks/lib
   ```

2. **Copy the hook scripts** from this document to their respective files

3. **Make scripts executable:**
   ```bash
   chmod +x .claude/hooks/*.sh
   ```

4. **Ensure `jq` is installed** (required for JSON parsing in hooks):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # macOS
   brew install jq
   ```

5. **Add to `.gitignore`:**
   ```
   .claude/settings.local.json
   .claude/hooks/command-history.log
   ```

6. **Commit the shared configuration:**
   ```bash
   git add .claude/settings.json .claude/hooks/
   git commit -m "feat: add Claude Code hooks for autonomous operation"
   ```

---

## Security Considerations

| Risk | Mitigation |
|------|------------|
| Path traversal | Pre-write hook validates paths stay within `$PROJECT_ROOT` |
| Protected branch corruption | Block patterns for main/master in push/merge commands |
| Credential exposure | Warning on sensitive file patterns |
| Audit trail | Post-bash hook logs all executed commands |
| Runaway processes | Stop hook provides session summary |

---

## Customization Notes

### To add more auto-approved commands:
Add patterns to the "AUTO-APPROVED COMMANDS" section in `pre-bash.sh`

### To protect additional branches:
Modify the regex patterns in the "BLOCKED COMMANDS" section:
```bash
# Example: also protect 'develop' and 'staging'
if echo "$COMMAND" | grep -qE 'git\s+push.*\s+(origin\s+)?(main|master|develop|staging)'; then
```

### To enable stricter mode:
Change the final `exit 0` in `pre-bash.sh` to `exit 1` — this will require explicit approval for any command not in the allow list.

---

## Troubleshooting

**Hook not executing:**
- Verify script is executable: `chmod +x .claude/hooks/*.sh`
- Check JSON syntax in settings file
- Ensure `jq` is installed

**Commands still prompting:**
- Hooks with empty stdout auto-approve; ensure your approval cases don't echo anything
- Check that the matcher regex matches the tool name exactly

**Path validation failing:**
- Ensure `realpath` is available (coreutils)
- Check that `git rev-parse --show-toplevel` works in your repo

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-04 | Initial specification |