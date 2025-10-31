#!/bin/bash
# ============================================================================
# Deep Research MCP - One-Click Deployment Script
# ============================================================================
# This script provides automated deployment for the Deep Research MCP server
# with support for multiple deployment strategies and environments.
#
# Usage:
#   ./deploy.sh [command] [options]
#
# Commands:
#   setup     - Initial setup and dependency check
#   docker    - Deploy using Docker Compose
#   local     - Deploy locally with Python virtual environment
#   cloud     - Deploy to cloud platform (AWS/GCP/Azure)
#   dev       - Start development environment
#   stop      - Stop all services
#   clean     - Clean up deployment artifacts
#   health    - Check system health
#   logs      - View deployment logs
#   backup    - Backup configuration and data
#   restore   - Restore from backup
#   help      - Show detailed help
#
# Options:
#   --env ENV         Environment (dev, staging, prod) [default: prod]
#   --config FILE     Custom configuration file
#   --no-deps         Skip dependency installation
#   --force           Force deployment without confirmation
#   --verbose         Enable verbose logging
#   --dry-run         Show what would be done without executing
#
# Examples:
#   ./deploy.sh setup                    # Initial setup
#   ./deploy.sh docker --env prod        # Production Docker deployment
#   ./deploy.sh local --env dev          # Local development setup
#   ./deploy.sh cloud --config aws.yaml # Cloud deployment with custom config
# ============================================================================

set -euo pipefail

# ============================================================================
# Configuration and Constants
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="deep-research-mcp"
VERSION="1.0.0"
PYTHON_MIN_VERSION="3.13"
UV_MIN_VERSION="0.1.0"

# Default values
ENVIRONMENT="prod"
CONFIG_FILE=""
SKIP_DEPS=false
FORCE_DEPLOYMENT=false
VERBOSE=false
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Utility Functions
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $1${NC}"
    fi
}

show_banner() {
    echo -e "${CYAN}"
    echo "============================================================================"
    echo "  Deep Research MCP - Multi-Agent Research System"
    echo "  Version: $VERSION"
    echo "  Environment: $ENVIRONMENT"
    echo "============================================================================"
    echo -e "${NC}"
}

check_command() {
    local cmd=$1
    local install_msg=${2:-"Please install $cmd"}
    
    if ! command -v "$cmd" &> /dev/null; then
        log_error "$cmd is not installed. $install_msg"
        return 1
    fi
    return 0
}

version_compare() {
    local version1=$1
    local version2=$2
    
    if [[ "$version1" == "$version2" ]]; then
        return 0
    fi
    
    local IFS=.
    local i version1_arr=($1) version2_arr=($2)
    
    # Fill empty fields in version1_arr with zeros
    for ((i=${#version1_arr[@]}; i<${#version2_arr[@]}; i++)); do
        version1_arr[i]=0
    done
    
    for ((i=0; i<${#version1_arr[@]}; i++)); do
        if [[ -z ${version2_arr[i]} ]]; then
            version2_arr[i]=0
        fi
        if ((10#${version1_arr[i]} > 10#${version2_arr[i]})); then
            return 1  # version1 > version2
        fi
        if ((10#${version1_arr[i]} < 10#${version2_arr[i]})); then
            return 2  # version1 < version2
        fi
    done
    return 0  # versions are equal
}

confirm_action() {
    local message=$1
    if [[ "$FORCE_DEPLOYMENT" == true ]]; then
        return 0
    fi
    
    echo -e "${YELLOW}$message${NC}"
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled by user"
        exit 0
    fi
}

# ============================================================================
# Environment Setup Functions
# ============================================================================

setup_environment() {
    log "Setting up environment variables for $ENVIRONMENT"
    
    # Create environment-specific .env file
    local env_file=".env"
    if [[ -n "$CONFIG_FILE" ]]; then
        env_file="$CONFIG_FILE"
    elif [[ -f ".env.$ENVIRONMENT" ]]; then
        env_file=".env.$ENVIRONMENT"
    fi
    
    if [[ ! -f "$env_file" ]]; then
        if [[ -f ".env.example" ]]; then
            log_info "Creating $env_file from .env.example"
            cp ".env.example" "$env_file"
        else
            log_error "No environment file found. Please create $env_file or run with --config option"
            exit 1
        fi
    fi
    
    # Load environment variables
    set -a
    source "$env_file"
    set +a
    
    log_debug "Environment file loaded: $env_file"
}

create_directories() {
    log "Creating required directories"
    
    local dirs=("outputs" "logs" "data" "backups" "deploy/configs" "deploy/monitoring" "deploy/nginx")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_debug "Created directory: $dir"
        fi
    done
}

# ============================================================================
# Dependency Check Functions
# ============================================================================

check_python_version() {
    log_debug "Checking Python version"
    
    if ! check_command python3; then
        return 1
    fi
    
    local python_version
    python_version=$(python3 --version | cut -d' ' -f2)
    
    version_compare "$python_version" "$PYTHON_MIN_VERSION"
    local result=$?
    
    if [[ $result -eq 2 ]]; then
        log_error "Python version $python_version is too old. Minimum required: $PYTHON_MIN_VERSION"
        return 1
    fi
    
    log_debug "Python version: $python_version ✓"
    return 0
}

check_uv() {
    log_debug "Checking uv package manager"
    
    if ! check_command uv "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; then
        return 1
    fi
    
    local uv_version
    uv_version=$(uv --version | cut -d' ' -f2)
    log_debug "uv version: $uv_version ✓"
    return 0
}

check_docker() {
    log_debug "Checking Docker"
    
    if ! check_command docker "Install from https://docs.docker.com/get-docker/"; then
        return 1
    fi
    
    if ! check_command docker-compose "Install Docker Compose"; then
        # Try docker compose (newer syntax)
        if ! docker compose version &> /dev/null; then
            log_error "Neither docker-compose nor docker compose found"
            return 1
        fi
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker"
        return 1
    fi
    
    log_debug "Docker is available and running ✓"
    return 0
}

check_system_deps() {
    log "Checking system dependencies"
    
    local deps=("curl" "git")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing system dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        return 1
    fi
    
    log_debug "System dependencies check passed ✓"
    return 0
}

# ============================================================================
# Deployment Strategy Functions
# ============================================================================

deploy_docker() {
    log "Starting Docker deployment"
    
    if ! check_docker; then
        exit 1
    fi
    
    # Set build variables
    export BUILD_VERSION="${VERSION}"
    export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export TAG="${ENVIRONMENT}-${BUILD_VERSION}"
    
    # Build and start services
    log_info "Building Docker images..."
    if [[ "$DRY_RUN" == false ]]; then
        docker-compose build --build-arg BUILD_VERSION="$BUILD_VERSION" \
                            --build-arg BUILD_DATE="$BUILD_DATE" \
                            --build-arg VCS_REF="$VCS_REF"
    else
        log_info "[DRY-RUN] Would build Docker images with version $BUILD_VERSION"
    fi
    
    log_info "Starting services..."
    if [[ "$DRY_RUN" == false ]]; then
        if [[ "$ENVIRONMENT" == "prod" ]]; then
            docker-compose --profile production up -d
        else
            docker-compose up -d
        fi
    else
        log_info "[DRY-RUN] Would start Docker services for $ENVIRONMENT environment"
    fi
    
    # Wait for services to be healthy
    if [[ "$DRY_RUN" == false ]]; then
        log_info "Waiting for services to be healthy..."
        sleep 10
        check_health_docker
    fi
    
    log "Docker deployment completed successfully!"
    show_deployment_info_docker
}

deploy_local() {
    log "Starting local deployment"
    
    if ! check_python_version; then
        exit 1
    fi
    
    if ! check_uv; then
        log_warn "uv not found, falling back to pip"
        deploy_local_pip
        return
    fi
    
    # Create virtual environment with uv
    log_info "Creating virtual environment with uv"
    if [[ "$DRY_RUN" == false ]]; then
        uv sync
    else
        log_info "[DRY-RUN] Would create virtual environment with uv"
    fi
    
    # Install production dependencies
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        log_info "Installing development dependencies"
        if [[ "$DRY_RUN" == false ]]; then
            uv sync --all-extras
        fi
    else
        log_info "Installing production dependencies"
        if [[ "$DRY_RUN" == false ]]; then
            uv sync --no-dev
        fi
    fi
    
    # Create systemd service file for production
    if [[ "$ENVIRONMENT" == "prod" && "$DRY_RUN" == false ]]; then
        create_systemd_service
    fi
    
    log "Local deployment completed successfully!"
    show_deployment_info_local
}

deploy_local_pip() {
    log_info "Using pip for local deployment"
    
    # Create virtual environment
    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment"
        if [[ "$DRY_RUN" == false ]]; then
            python3 -m venv .venv
        fi
    fi
    
    # Activate virtual environment and install dependencies
    if [[ "$DRY_RUN" == false ]]; then
        source .venv/bin/activate
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install dependencies
        if [[ "$ENVIRONMENT" == "dev" ]]; then
            pip install -e ".[test]"
        else
            pip install -e .
        fi
    else
        log_info "[DRY-RUN] Would install Python dependencies with pip"
    fi
}

deploy_cloud() {
    log "Starting cloud deployment"
    
    # Detect cloud platform
    local cloud_platform=""
    if [[ -f "deploy/aws/serverless.yml" || -f "app.yaml" ]]; then
        if command -v aws &> /dev/null; then
            cloud_platform="aws"
        elif command -v gcloud &> /dev/null; then
            cloud_platform="gcp"
        fi
    fi
    
    case "$cloud_platform" in
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        *)
            log_error "Cloud platform not detected or not supported"
            log_info "Supported platforms: AWS (with AWS CLI), GCP (with gcloud)"
            exit 1
            ;;
    esac
}

deploy_aws() {
    log_info "Deploying to AWS"
    
    # Check AWS CLI
    if ! check_command aws "Install AWS CLI from https://aws.amazon.com/cli/"; then
        exit 1
    fi
    
    # Create AWS deployment configuration
    create_aws_config
    
    # Deploy using AWS CLI or serverless framework
    if [[ "$DRY_RUN" == false ]]; then
        # Implementation would go here for AWS deployment
        log_info "AWS deployment would be implemented here"
    else
        log_info "[DRY-RUN] Would deploy to AWS"
    fi
}

deploy_gcp() {
    log_info "Deploying to Google Cloud Platform"
    
    # Check gcloud CLI
    if ! check_command gcloud "Install gcloud CLI"; then
        exit 1
    fi
    
    # Create GCP deployment configuration
    create_gcp_config
    
    # Deploy using gcloud
    if [[ "$DRY_RUN" == false ]]; then
        # Implementation would go here for GCP deployment
        log_info "GCP deployment would be implemented here"
    else
        log_info "[DRY-RUN] Would deploy to GCP"
    fi
}

# ============================================================================
# Configuration Functions
# ============================================================================

create_systemd_service() {
    log_info "Creating systemd service for production"
    
    local service_file="/etc/systemd/system/${PROJECT_NAME}.service"
    local user=$(whoami)
    
    cat > "${PROJECT_NAME}.service" << EOF
[Unit]
Description=Deep Research MCP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$user
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/.venv/bin:\$PATH
ExecStart=$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/mcp_server.py
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$SCRIPT_DIR/outputs $SCRIPT_DIR/logs $SCRIPT_DIR/data

# Resource limits
LimitNOFILE=65536
MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

    log_info "Systemd service file created: ${PROJECT_NAME}.service"
    log_info "To install: sudo cp ${PROJECT_NAME}.service $service_file && sudo systemctl enable ${PROJECT_NAME}"
}

create_aws_config() {
    log_info "Creating AWS deployment configuration"
    
    mkdir -p deploy/aws
    
    cat > deploy/aws/serverless.yml << 'EOF'
service: deep-research-mcp

provider:
  name: aws
  runtime: python3.13
  stage: ${env:ENVIRONMENT, 'prod'}
  region: ${env:AWS_REGION, 'us-east-1'}
  memorySize: 2048
  timeout: 300
  environment:
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
    GOOGLE_API_KEY: ${env:GOOGLE_API_KEY}
    TAVILY_API_KEY: ${env:TAVILY_API_KEY}
    PRIMARY_LLM_PROVIDER: ${env:PRIMARY_LLM_PROVIDER}
    PRIMARY_SEARCH_PROVIDER: ${env:PRIMARY_SEARCH_PROVIDER}

functions:
  mcp-server:
    handler: mcp_server.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
      - http:
          path: /
          method: ANY

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    slim: true
EOF
}

create_gcp_config() {
    log_info "Creating GCP deployment configuration"
    
    cat > app.yaml << 'EOF'
runtime: python313

env_variables:
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  GOOGLE_API_KEY: ${GOOGLE_API_KEY}
  TAVILY_API_KEY: ${TAVILY_API_KEY}
  PRIMARY_LLM_PROVIDER: ${PRIMARY_LLM_PROVIDER}
  PRIMARY_SEARCH_PROVIDER: ${PRIMARY_SEARCH_PROVIDER}

resources:
  cpu: 2
  memory_gb: 4
  disk_size_gb: 10

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6
EOF
}

create_nginx_config() {
    log_info "Creating Nginx configuration"
    
    mkdir -p deploy/nginx
    
    cat > deploy/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream deep_research_mcp {
        server deep-research-mcp:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://deep_research_mcp;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            access_log off;
            proxy_pass http://deep_research_mcp/health;
        }
    }
}
EOF
}

# ============================================================================
# Health Check Functions
# ============================================================================

check_health() {
    log "Performing health check"
    
    case "$1" in
        docker)
            check_health_docker
            ;;
        local)
            check_health_local
            ;;
        *)
            log_error "Unknown deployment type for health check"
            exit 1
            ;;
    esac
}

check_health_docker() {
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            log "Services are healthy ✓"
            return 0
        fi
        
        log_debug "Health check attempt $attempt/$max_attempts"
        sleep 5
        ((attempt++))
    done
    
    log_error "Services failed to become healthy within timeout"
    docker-compose logs
    return 1
}

check_health_local() {
    # Check if MCP server is running
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "MCP server is healthy ✓"
        return 0
    else
        log_error "MCP server health check failed"
        return 1
    fi
}

# ============================================================================
# Information Display Functions
# ============================================================================

show_deployment_info_docker() {
    log_info "=== Docker Deployment Information ==="
    echo
    echo "Service URLs:"
    echo "  MCP Server: http://localhost:${MCP_PORT:-8000}"
    echo "  Health Check: http://localhost:${MCP_PORT:-8000}/health"
    
    if docker-compose ps | grep -q redis; then
        echo "  Redis: localhost:${REDIS_PORT:-6379}"
    fi
    
    if docker-compose ps | grep -q nginx; then
        echo "  Load Balancer: http://localhost:${HTTP_PORT:-80}"
    fi
    
    echo
    echo "Management Commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart: docker-compose restart"
    echo "  Update: docker-compose pull && docker-compose up -d"
    echo
}

show_deployment_info_local() {
    log_info "=== Local Deployment Information ==="
    echo
    echo "Service Information:"
    echo "  MCP Server: http://localhost:8000"
    echo "  Health Check: http://localhost:8000/health"
    echo "  Virtual Environment: .venv/"
    echo
    echo "Management Commands:"
    echo "  Start server: python mcp_server.py"
    echo "  Start CLI: python main.py"
    echo "  Run tests: python -m pytest"
    echo "  Activate env: source .venv/bin/activate"
    echo
    
    if [[ -f "${PROJECT_NAME}.service" ]]; then
        echo "Systemd Service:"
        echo "  Install: sudo cp ${PROJECT_NAME}.service /etc/systemd/system/"
        echo "  Enable: sudo systemctl enable ${PROJECT_NAME}"
        echo "  Start: sudo systemctl start ${PROJECT_NAME}"
        echo
    fi
}

show_help() {
    show_banner
    cat << 'EOF'
USAGE:
    ./deploy.sh [COMMAND] [OPTIONS]

COMMANDS:
    setup       Initial setup and dependency verification
    docker      Deploy using Docker Compose (recommended for production)
    local       Deploy locally with Python virtual environment
    cloud       Deploy to cloud platform (AWS/GCP/Azure)
    dev         Start development environment with hot reloading
    stop        Stop all running services
    clean       Clean up deployment artifacts and containers
    health      Check system health and service status
    logs        View deployment and service logs
    backup      Backup configuration and data
    restore     Restore from backup
    update      Update to latest version
    help        Show this help message

OPTIONS:
    --env ENV           Environment: dev, staging, prod (default: prod)
    --config FILE       Use custom configuration file
    --no-deps           Skip dependency installation and checks
    --force             Force deployment without confirmation prompts
    --verbose           Enable verbose logging and debug output
    --dry-run           Show what would be done without executing

EXAMPLES:
    # Initial setup
    ./deploy.sh setup

    # Production deployment with Docker
    ./deploy.sh docker --env prod

    # Development environment
    ./deploy.sh local --env dev --verbose

    # Cloud deployment with custom config
    ./deploy.sh cloud --config deploy/production.env

    # Health check
    ./deploy.sh health

    # View logs
    ./deploy.sh logs --verbose

ENVIRONMENT FILES:
    .env                Default environment file
    .env.dev            Development environment
    .env.staging        Staging environment  
    .env.prod           Production environment
    .env.example        Example configuration template

For more information, visit: https://github.com/your-org/deep-research-mcp
EOF
}

# ============================================================================
# Command Handlers
# ============================================================================

cmd_setup() {
    log "Running initial setup"
    
    show_banner
    create_directories
    setup_environment
    
    log_info "Checking system dependencies..."
    check_system_deps
    
    if [[ "$SKIP_DEPS" == false ]]; then
        log_info "Checking Python environment..."
        check_python_version
        
        log_info "Checking package managers..."
        check_uv || log_warn "uv not available, will use pip"
        
        log_info "Checking Docker (optional)..."
        check_docker || log_warn "Docker not available"
    fi
    
    # Create configuration files
    create_nginx_config
    
    log "Setup completed successfully!"
    log_info "Next steps:"
    log_info "  1. Edit .env file with your API keys"
    log_info "  2. Run: ./deploy.sh docker    # For Docker deployment"
    log_info "  3. Run: ./deploy.sh local     # For local deployment"
}

cmd_stop() {
    log "Stopping services"
    
    # Stop Docker services if running
    if docker-compose ps &> /dev/null; then
        log_info "Stopping Docker services..."
        docker-compose down
    fi
    
    # Stop systemd service if running
    if systemctl is-active --quiet "${PROJECT_NAME}" 2>/dev/null; then
        log_info "Stopping systemd service..."
        sudo systemctl stop "${PROJECT_NAME}"
    fi
    
    # Kill any remaining processes
    pkill -f "mcp_server.py" || true
    pkill -f "main.py" || true
    
    log "All services stopped"
}

cmd_clean() {
    log "Cleaning up deployment artifacts"
    
    confirm_action "This will remove containers, images, and volumes. Continue?"
    
    # Stop services first
    cmd_stop
    
    # Clean Docker artifacts
    if command -v docker &> /dev/null; then
        log_info "Cleaning Docker artifacts..."
        docker-compose down --volumes --remove-orphans || true
        docker system prune -f || true
    fi
    
    # Clean Python artifacts
    log_info "Cleaning Python artifacts..."
    rm -rf .venv/ __pycache__/ *.egg-info/ build/ dist/
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean logs
    rm -rf logs/*.log
    
    log "Cleanup completed"
}

cmd_logs() {
    log "Viewing deployment logs"
    
    if docker-compose ps &> /dev/null; then
        docker-compose logs -f
    elif [[ -f "logs/mcp_server.log" ]]; then
        tail -f logs/mcp_server.log
    else
        log_error "No logs found"
    fi
}

cmd_backup() {
    log "Creating backup"
    
    local backup_dir="backups/backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup configuration
    cp .env* "$backup_dir/" 2>/dev/null || true
    cp -r deploy/ "$backup_dir/" 2>/dev/null || true
    
    # Backup data
    cp -r data/ "$backup_dir/" 2>/dev/null || true
    cp -r outputs/ "$backup_dir/" 2>/dev/null || true
    
    log "Backup created: $backup_dir"
}

# ============================================================================
# Main Command Processing
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --no-deps)
                SKIP_DEPS=true
                shift
                ;;
            --force)
                FORCE_DEPLOYMENT=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            setup|docker|local|cloud|dev|stop|clean|health|logs|backup|restore|update|help)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set default command
    COMMAND=${COMMAND:-help}
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Execute command
    case "$COMMAND" in
        setup)
            cmd_setup
            ;;
        docker)
            cmd_setup
            setup_environment
            deploy_docker
            ;;
        local)
            cmd_setup
            setup_environment
            deploy_local
            ;;
        cloud)
            cmd_setup
            setup_environment
            deploy_cloud
            ;;
        dev)
            ENVIRONMENT="dev"
            cmd_setup
            setup_environment
            deploy_local
            ;;
        stop)
            cmd_stop
            ;;
        clean)
            cmd_clean
            ;;
        health)
            if docker-compose ps &> /dev/null; then
                check_health docker
            else
                check_health local
            fi
            ;;
        logs)
            cmd_logs
            ;;
        backup)
            cmd_backup
            ;;
        help)
            show_help
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# ============================================================================
# Script Entry Point
# ============================================================================

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi