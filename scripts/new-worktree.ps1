<#
.SYNOPSIS
    Creates a Git worktree for feature development or bug fixing.

.DESCRIPTION
    This script creates a new Git worktree with a feature/fix/refactor branch
    and opens VS Code in the new worktree directory.

.PARAMETER Name
    The name of the feature/fix (without prefix).

.PARAMETER Type
    The type of branch: 'feature', 'fix', or 'refactor'. Default is 'feature'.

.PARAMETER Base
    The base branch to create from. Default is 'main'.

.EXAMPLE
    new-worktree my-feature
    Creates: ../small-gastro-worktrees/feature-my-feature

.EXAMPLE
    new-worktree login-bug -Type fix
    Creates: ../small-gastro-worktrees/fix-login-bug

.EXAMPLE
    new-worktree code-cleanup -Type refactor -Base develop
    Creates worktree from 'develop' branch
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Name,

    [Parameter(Position=1)]
    [ValidateSet('feature', 'fix', 'refactor')]
    [string]$Type = 'feature',

    [Parameter()]
    [string]$Base = 'master'
)

# Get the repository root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Error "Not in a Git repository!"
    exit 1
}

$repoName = Split-Path $repoRoot -Leaf
$worktreesDir = Join-Path (Split-Path $repoRoot -Parent) "$repoName-worktrees"
$branchName = "$Type-$Name"
$worktreePath = Join-Path $worktreesDir $branchName

# Check if worktree already exists
if (Test-Path $worktreePath) {
    Write-Host "Worktree already exists at: $worktreePath" -ForegroundColor Yellow
    $response = Read-Host "Open existing worktree in VS Code? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Opening VS Code..." -ForegroundColor Green
        code $worktreePath
    }
    exit 0
}

# Ensure worktrees directory exists
if (-not (Test-Path $worktreesDir)) {
    New-Item -ItemType Directory -Path $worktreesDir -Force | Out-Null
    Write-Host "Created worktrees directory: $worktreesDir" -ForegroundColor Cyan
}

# Fetch latest from origin
Write-Host "Fetching latest from origin..." -ForegroundColor Cyan
git fetch origin

# Check if base branch exists
$baseBranchExists = git show-ref --verify --quiet "refs/heads/$Base" 2>$null
$remoteBaseBranchExists = git show-ref --verify --quiet "refs/remotes/origin/$Base" 2>$null

if (-not $baseBranchExists -and -not $remoteBaseBranchExists) {
    Write-Error "Base branch '$Base' does not exist locally or on origin!"
    exit 1
}

# Use origin/base if local doesn't exist
$baseRef = if ($baseBranchExists) { $Base } else { "origin/$Base" }

# Check if branch already exists
$branchExists = git show-ref --verify --quiet "refs/heads/$branchName" 2>$null
if ($branchExists) {
    Write-Host "Branch '$branchName' already exists. Creating worktree from existing branch..." -ForegroundColor Yellow
    git worktree add $worktreePath $branchName
} else {
    # Create worktree with new branch
    Write-Host "Creating worktree with new branch '$branchName' from '$baseRef'..." -ForegroundColor Cyan
    git worktree add -b $branchName $worktreePath $baseRef
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create worktree!"
    exit 1
}

Write-Host ""
Write-Host "Worktree created successfully!" -ForegroundColor Green
Write-Host "  Path:   $worktreePath" -ForegroundColor White
Write-Host "  Branch: $branchName" -ForegroundColor White
Write-Host ""

# Open VS Code
Write-Host "Opening VS Code..." -ForegroundColor Cyan
code $worktreePath

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Work on your changes in the new VS Code window"
Write-Host "  2. Commit your changes"
Write-Host "  3. When ready, create a PR"
Write-Host "  4. After merge, clean up with: git worktree remove $worktreePath"
Write-Host ""
