# .claude/hooks/post-file-write.ps1
# Post-processing after file writes
# Exit codes: 0 = success

param([string]$FilePaths)

# Currently no post-processing needed
# This hook can be extended for:
# - Auto-formatting
# - Linting
# - Notifications

exit 0
