# .claude/hooks/pre-file-write.ps1
# Validates file write operations
# Exit codes: 0 = allow, 2 = block

param([string]$ToolInput)

try {
    $input = $ToolInput | ConvertFrom-Json
    $filePath = $input.file_path
} catch {
    exit 0  # Allow if we can't parse
}

if (-not $filePath) {
    exit 0
}

# Block writes to sensitive locations
$blockedPatterns = @(
    '^C:\\Windows\\',
    '^C:\\Program Files',
    '^C:\\Users\\[^\\]+\\AppData\\',
    '\\\.env$',
    '\\\.env\.local$',
    '\\credentials',
    '\\secrets'
)

foreach ($pattern in $blockedPatterns) {
    if ($filePath -match $pattern) {
        # Allow .env files within the project (check if it's a template or example)
        if ($filePath -match '\.env\.(example|template|sample)$') {
            continue
        }

        # Check if it's within the project directory
        $projectRoot = git rev-parse --show-toplevel 2>$null
        if ($projectRoot -and $filePath.StartsWith($projectRoot)) {
            # Allow .env files in project if they exist (updating existing)
            if (Test-Path $filePath) {
                continue
            }
        }

        Write-Host "BLOCKED: Write to sensitive location: $filePath"
        exit 2
    }
}

exit 0
