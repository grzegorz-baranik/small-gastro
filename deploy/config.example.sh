#!/bin/bash
#
# Small Gastro - Deployment Configuration Template
#
# Copy this file to create environment-specific configs:
#   cp deploy/config.example.sh deploy/config.production.sh
#   cp deploy/config.example.sh deploy/config.staging.sh
#
# Then fill in the values for each environment.
#

# === SSH Connection ===
SSH_HOST="your-vps-ip-or-hostname"
SSH_USER="your-ssh-user"
SSH_KEY_PATH="$HOME/.ssh/id_rsa"
SSH_PORT=22

# === Project Location on VPS ===
REMOTE_PROJECT_DIR="/home/your-user/small-gastro"

# === Git ===
GIT_BRANCH="master"

# === Health Check (optional) ===
# External URL to verify deployment is working
# HEALTH_CHECK_URL="https://your-domain.com/api/v1/health"

# === Logging ===
# Number of log lines to show with 'logs' command
LOG_LINES=100
