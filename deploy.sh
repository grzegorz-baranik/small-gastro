#!/bin/bash
#
# Small Gastro Deployment Script
# Usage: ./deploy.sh [environment] [command]
#
# Environments: staging, production
# Commands: deploy (default), rollback, status, logs, ssh
#
# Examples:
#   ./deploy.sh production deploy
#   ./deploy.sh staging rollback
#   ./deploy.sh production status
#   ./deploy.sh production logs backend
#   ./deploy.sh production ssh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Logging functions
#######################################
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#######################################
# Load environment configuration
#######################################
load_config() {
    local env="$1"
    local config_file="${SCRIPT_DIR}/deploy/config.${env}.sh"

    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        log_info "Create it from the template: cp deploy/config.example.sh $config_file"
        exit 1
    fi

    # shellcheck source=/dev/null
    source "$config_file"

    # Validate required variables
    local required_vars=(
        "SSH_HOST"
        "SSH_USER"
        "SSH_KEY_PATH"
        "REMOTE_PROJECT_DIR"
        "GIT_BRANCH"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required variable $var is not set in $config_file"
            exit 1
        fi
    done

    log_info "Loaded configuration for environment: $env"
}

#######################################
# Setup SSH agent and add key
#######################################
ssh_agent_setup() {
    log_info "Adding SSH key to agent (you may be prompted for passphrase once)..."

    # Start ssh-agent if not running
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        eval "$(ssh-agent -s)" > /dev/null
    fi

    # Add key to agent (will prompt for passphrase if needed)
    if ! ssh-add -l 2>/dev/null | grep -q "$(ssh-keygen -lf "$SSH_KEY_PATH" 2>/dev/null | awk '{print $2}')"; then
        ssh-add "$SSH_KEY_PATH"
    else
        log_info "SSH key already loaded in agent"
    fi
}

#######################################
# SSH command wrapper
#######################################
ssh_cmd() {
    ssh -A \
        -p "${SSH_PORT:-22}" \
        -o ConnectTimeout=10 \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o LogLevel=ERROR \
        "${SSH_USER}@${SSH_HOST}" "$@"
}

#######################################
# Interactive SSH session
#######################################
cmd_ssh() {
    log_info "Connecting to ${SSH_USER}@${SSH_HOST}:${SSH_PORT:-22}..."
    ssh -A -p "${SSH_PORT:-22}" "${SSH_USER}@${SSH_HOST}"
}

#######################################
# Check server status
#######################################
cmd_status() {
    log_info "Checking deployment status on ${SSH_HOST}..."

    ssh_cmd << EOF
        cd ${REMOTE_PROJECT_DIR}

        echo ""
        echo "=== Git Status ==="
        git log -1 --format="Commit: %h%nAuthor: %an%nDate: %ad%nMessage: %s"
        git status --short

        echo ""
        echo "=== Docker Containers ==="
        docker compose ps

        echo ""
        echo "=== Container Health ==="
        docker compose ps --format "table {{.Name}}\t{{.Status}}"

        echo ""
        echo "=== Disk Usage ==="
        df -h ${REMOTE_PROJECT_DIR} | tail -1

        echo ""
        echo "=== Docker Images ==="
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "(small-gastro|REPOSITORY)" || true
EOF
}

#######################################
# View logs
#######################################
cmd_logs() {
    local service="${1:-}"
    local lines="${LOG_LINES:-100}"

    if [[ -n "$service" ]]; then
        log_info "Fetching logs for service: $service"
        ssh_cmd "cd ${REMOTE_PROJECT_DIR} && docker compose logs --tail=$lines -f $service"
    else
        log_info "Fetching logs for all services"
        ssh_cmd "cd ${REMOTE_PROJECT_DIR} && docker compose logs --tail=$lines -f"
    fi
}

#######################################
# Pre-deployment checks
#######################################
pre_deploy_checks() {
    log_info "Running pre-deployment checks..."

    # Check SSH connectivity
    if ! ssh_cmd "echo 'SSH connection successful'" &>/dev/null; then
        log_error "Cannot connect to server via SSH"
        exit 1
    fi
    log_success "SSH connection OK"

    # Check if project directory exists
    if ! ssh_cmd "test -d ${REMOTE_PROJECT_DIR}"; then
        log_error "Project directory does not exist: ${REMOTE_PROJECT_DIR}"
        log_info "Please clone the repository first:"
        log_info "  git clone <repo-url> ${REMOTE_PROJECT_DIR}"
        exit 1
    fi
    log_success "Project directory exists"

    # Check Docker
    if ! ssh_cmd "docker compose version" &>/dev/null; then
        log_error "Docker Compose is not installed on the server"
        exit 1
    fi
    log_success "Docker Compose available"
}

#######################################
# Create backup before deployment
#######################################
create_backup() {
    log_info "Creating pre-deployment backup..."

    ssh_cmd << EOF
        cd ${REMOTE_PROJECT_DIR}

        # Store current commit hash for rollback
        git rev-parse HEAD > .deploy_backup_commit

        # Tag current images for rollback
        for service in backend frontend; do
            image=\$(docker compose images \$service -q 2>/dev/null || true)
            if [[ -n "\$image" ]]; then
                docker tag \$image small-gastro-\${service}:rollback 2>/dev/null || true
            fi
        done

        echo "Backup created at commit: \$(cat .deploy_backup_commit)"
EOF

    log_success "Backup created"
}

#######################################
# Main deployment
#######################################
cmd_deploy() {
    local start_time
    start_time=$(date +%s)

    log_info "Starting deployment to ${ENVIRONMENT}..."
    log_info "Target: ${SSH_USER}@${SSH_HOST}:${REMOTE_PROJECT_DIR}"
    log_info "Branch: ${GIT_BRANCH}"

    # Pre-deployment checks
    pre_deploy_checks

    # Create backup for rollback
    create_backup

    # Pull latest changes and deploy
    log_info "Pulling latest changes and deploying..."

    ssh_cmd << EOF
        set -e
        cd ${REMOTE_PROJECT_DIR}

        echo ""
        echo "=== Pulling latest changes ==="
        git fetch origin
        git checkout ${GIT_BRANCH}
        git pull origin ${GIT_BRANCH}

        echo ""
        echo "=== Current commit ==="
        git log -1 --oneline

        echo ""
        echo "=== Building Docker images ==="
        docker compose build --no-cache

        echo ""
        echo "=== Stopping old containers ==="
        docker compose down

        echo ""
        echo "=== Starting new containers ==="
        docker compose up -d

        echo ""
        echo "=== Waiting for services to be healthy ==="
        sleep 10

        # Wait for backend to be healthy
        echo "Waiting for backend health check..."
        for i in {1..30}; do
            if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1; then
                echo "Backend is healthy!"
                break
            fi
            if [[ \$i -eq 30 ]]; then
                echo "Backend health check failed after 30 attempts"
                echo "Checking backend logs..."
                docker compose logs --tail=50 backend
                exit 1
            fi
            echo "Attempt \$i/30 - waiting..."
            sleep 2
        done

        echo ""
        echo "=== Running database migrations ==="
        docker compose exec -T backend alembic upgrade head

        echo ""
        echo "=== Deployment complete ==="
        docker compose ps
EOF

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Deployment completed in ${duration} seconds!"

    # Run post-deployment health check
    post_deploy_health_check
}

#######################################
# Post-deployment health check
#######################################
post_deploy_health_check() {
    log_info "Running post-deployment health checks..."

    local health_url="${HEALTH_CHECK_URL:-}"

    if [[ -n "$health_url" ]]; then
        log_info "Checking: $health_url"

        for i in {1..5}; do
            if curl -sf "$health_url" > /dev/null 2>&1; then
                log_success "Health check passed!"
                return 0
            fi
            log_warning "Attempt $i/5 failed, retrying..."
            sleep 3
        done

        log_error "Health check failed after 5 attempts"
        log_warning "Consider running: ./deploy.sh ${ENVIRONMENT} rollback"
        return 1
    else
        log_warning "No HEALTH_CHECK_URL configured, skipping external health check"
    fi
}

#######################################
# Rollback deployment
#######################################
cmd_rollback() {
    log_warning "Starting rollback on ${ENVIRONMENT}..."

    ssh_cmd << EOF
        set -e
        cd ${REMOTE_PROJECT_DIR}

        if [[ ! -f .deploy_backup_commit ]]; then
            echo "No backup commit found. Cannot rollback."
            exit 1
        fi

        BACKUP_COMMIT=\$(cat .deploy_backup_commit)
        echo "Rolling back to commit: \$BACKUP_COMMIT"

        echo ""
        echo "=== Checking out previous commit ==="
        git checkout \$BACKUP_COMMIT

        echo ""
        echo "=== Restoring previous Docker images ==="
        docker compose down

        # Try to use tagged rollback images first
        for service in backend frontend; do
            if docker images small-gastro-\${service}:rollback -q | grep -q .; then
                echo "Restoring \$service from rollback image"
            fi
        done

        echo ""
        echo "=== Rebuilding and starting containers ==="
        docker compose build
        docker compose up -d

        echo ""
        echo "=== Running database migrations ==="
        docker compose exec -T backend alembic upgrade head

        echo ""
        echo "=== Rollback complete ==="
        docker compose ps
EOF

    log_success "Rollback completed!"
}

#######################################
# Show help
#######################################
show_help() {
    cat << EOF
Small Gastro Deployment Script

Usage: ./deploy.sh [environment] [command] [options]

Environments:
    staging         Deploy to staging environment
    production      Deploy to production environment

Commands:
    deploy          Full deployment (default)
    rollback        Rollback to previous deployment
    status          Show deployment status
    logs [service]  View container logs (optionally for specific service)
    ssh             Open SSH session to server

Examples:
    ./deploy.sh production deploy       # Deploy to production
    ./deploy.sh staging rollback        # Rollback staging
    ./deploy.sh production status       # Check production status
    ./deploy.sh production logs backend # View backend logs
    ./deploy.sh staging ssh             # SSH to staging server

Configuration:
    Create environment configs in deploy/ directory:
    - deploy/config.staging.sh
    - deploy/config.production.sh

    Use deploy/config.example.sh as a template.

EOF
}

#######################################
# Main entry point
#######################################
main() {
    local environment="${1:-}"
    local command="${2:-deploy}"
    local extra_args="${3:-}"

    if [[ -z "$environment" ]] || [[ "$environment" == "help" ]] || [[ "$environment" == "--help" ]]; then
        show_help
        exit 0
    fi

    # Validate environment
    if [[ ! "$environment" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment: $environment"
        log_info "Valid environments: staging, production"
        exit 1
    fi

    ENVIRONMENT="$environment"
    load_config "$environment"
    ssh_agent_setup

    case "$command" in
        deploy)
            cmd_deploy
            ;;
        rollback)
            cmd_rollback
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$extra_args"
            ;;
        ssh)
            cmd_ssh
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
