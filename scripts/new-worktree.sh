#!/bin/bash
#
# new-worktree.sh - Creates a Git worktree for feature development or bug fixing
#
# Usage:
#   new-worktree <name> [type] [base]
#
# Arguments:
#   name  - The name of the feature/fix (without prefix)
#   type  - Branch type: 'feature', 'fix', or 'refactor' (default: 'feature')
#   base  - Base branch to create from (default: 'main')
#
# Examples:
#   new-worktree my-feature
#   new-worktree login-bug fix
#   new-worktree code-cleanup refactor develop
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Parse arguments
NAME="$1"
TYPE="${2:-feature}"
BASE="${3:-master}"

# Validate arguments
if [ -z "$NAME" ]; then
    echo -e "${RED}Error: Name is required!${NC}"
    echo ""
    echo "Usage: new-worktree <name> [type] [base]"
    echo ""
    echo "Arguments:"
    echo "  name  - The name of the feature/fix (without prefix)"
    echo "  type  - Branch type: 'feature', 'fix', or 'refactor' (default: 'feature')"
    echo "  base  - Base branch to create from (default: 'main')"
    echo ""
    echo "Examples:"
    echo "  new-worktree my-feature"
    echo "  new-worktree login-bug fix"
    echo "  new-worktree code-cleanup refactor develop"
    exit 1
fi

# Validate type
if [[ ! "$TYPE" =~ ^(feature|fix|refactor)$ ]]; then
    echo -e "${RED}Error: Type must be 'feature', 'fix', or 'refactor'!${NC}"
    exit 1
fi

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    echo -e "${RED}Error: Not in a Git repository!${NC}"
    exit 1
fi

REPO_NAME=$(basename "$REPO_ROOT")
WORKTREES_DIR="$(dirname "$REPO_ROOT")/${REPO_NAME}-worktrees"
BRANCH_NAME="${TYPE}-${NAME}"
WORKTREE_PATH="${WORKTREES_DIR}/${BRANCH_NAME}"

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
    echo -e "${YELLOW}Worktree already exists at: $WORKTREE_PATH${NC}"
    read -p "Open existing worktree in VS Code? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Opening VS Code...${NC}"
        code "$WORKTREE_PATH"
    fi
    exit 0
fi

# Ensure worktrees directory exists
if [ ! -d "$WORKTREES_DIR" ]; then
    mkdir -p "$WORKTREES_DIR"
    echo -e "${CYAN}Created worktrees directory: $WORKTREES_DIR${NC}"
fi

# Fetch latest from origin
echo -e "${CYAN}Fetching latest from origin...${NC}"
git fetch origin

# Check if base branch exists
BASE_REF=""
if git show-ref --verify --quiet "refs/heads/$BASE" 2>/dev/null; then
    BASE_REF="$BASE"
elif git show-ref --verify --quiet "refs/remotes/origin/$BASE" 2>/dev/null; then
    BASE_REF="origin/$BASE"
else
    echo -e "${RED}Error: Base branch '$BASE' does not exist locally or on origin!${NC}"
    exit 1
fi

# Check if branch already exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Branch '$BRANCH_NAME' already exists. Creating worktree from existing branch...${NC}"
    git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
else
    # Create worktree with new branch
    echo -e "${CYAN}Creating worktree with new branch '$BRANCH_NAME' from '$BASE_REF'...${NC}"
    git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "$BASE_REF"
fi

echo ""
echo -e "${GREEN}Worktree created successfully!${NC}"
echo -e "  ${WHITE}Path:${NC}   $WORKTREE_PATH"
echo -e "  ${WHITE}Branch:${NC} $BRANCH_NAME"
echo ""

# Open VS Code
echo -e "${CYAN}Opening VS Code...${NC}"
code "$WORKTREE_PATH"

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Work on your changes in the new VS Code window"
echo "  2. Commit your changes"
echo "  3. When ready, create a PR"
echo "  4. After merge, clean up with: git worktree remove $WORKTREE_PATH"
echo ""
