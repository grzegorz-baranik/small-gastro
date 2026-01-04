# .claude/hooks/pre-bash.ps1
# Validates bash commands before execution
# Exit codes: 0 = allow, 2 = block

param([string]$ToolInput)

try {
    $input = $ToolInput | ConvertFrom-Json
    $command = $input.command
} catch {
    exit 0  # Allow if we can't parse
}

if (-not $command) {
    exit 0
}

# =============================================================================
# BLOCKED COMMANDS (exit 2 to block)
# =============================================================================

# Block git operations that affect main/master
if ($command -match 'git\s+(merge|rebase).*\s+(main|master)') {
    Write-Host "BLOCKED: Direct merge/rebase to main/master is not allowed"
    Write-Host "   Use pull requests for integration to protected branches"
    exit 2
}

if ($command -match 'git\s+push.*\s+(origin\s+)?(main|master)') {
    Write-Host "BLOCKED: Direct push to main/master is not allowed"
    Write-Host "   Use pull requests for integration to protected branches"
    exit 2
}

if ($command -match 'git\s+checkout\s+(main|master)\s*&&\s*git\s+merge') {
    Write-Host "BLOCKED: Merge workflow to main/master detected"
    exit 2
}

# Block dangerous system commands
if ($command -match '^\s*(sudo|rm\s+-rf\s+/)') {
    Write-Host "BLOCKED: Potentially dangerous system command"
    exit 2
}

# All other commands are allowed (permission system handles approval)
exit 0
