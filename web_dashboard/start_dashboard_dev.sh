#!/bin/bash

################################################################################
# TK9 Deep Research MCP - V2 Dashboard Development Startup Script
#
# Development Features:
# - Development mode (ports 12656, 5173)
# - Automatic dependency detection and installation
# - Interactive environment configuration with prompts
# - Graceful shutdown handling (SIGTERM, SIGINT, SIGKILL)
# - Vite dev server with hot-reload
# - Concurrent backend (FastAPI) and frontend (Vite dev) management
# - Process isolation (only manages TK9 processes)
# - Console output (no file logging)
# - Health monitoring
# - Single Ctrl+C to shutdown everything gracefully
#
# Author: TK9 Team
# Date: 2025-11-02
# Version: 2.0-DEVELOPMENT
################################################################################

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# ============================================================================
# Global Variables & Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend_poc"
BACKEND_MAIN="$SCRIPT_DIR/main.py"

# Development ports
BACKEND_PORT=12656
FRONTEND_PORT=5173

# Development mode flag
PRODUCTION_MODE=false

# No logging for development (console output only)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Process tracking
BACKEND_PID=""
FRONTEND_PID=""
CLEANUP_DONE=false

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║    🔧 TK9 Deep Research MCP - V2 Dashboard [DEVELOPMENT]      ║"
    echo "║                                                                ║"
    echo "║    Backend Port: 12656  │  Frontend Port: 5173                ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}${BOLD}▶ $1${NC}"
    echo -e "${BLUE}$(printf '─%.0s' {1..65})${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_step() {
    echo -e "${MAGENTA}→${NC} $1"
}

# ============================================================================
# Cleanup & Signal Handling
# ============================================================================

cleanup() {
    if [ "$CLEANUP_DONE" = true ]; then
        return
    fi
    CLEANUP_DONE=true

    echo ""
    print_section "Shutting Down TK9 Dashboard"

    # Kill frontend process (Vite)
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        print_step "Stopping frontend (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true

        # Wait up to 5 seconds for graceful shutdown
        local count=0
        while kill -0 "$FRONTEND_PID" 2>/dev/null && [ $count -lt 5 ]; do
            sleep 1
            ((count++))
        done

        # Force kill if still running
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            print_warning "Force killing frontend..."
            kill -9 "$FRONTEND_PID" 2>/dev/null || true
        fi
        print_success "Frontend stopped"
    fi

    # Kill backend process (FastAPI/Uvicorn)
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        print_step "Stopping backend (PID: $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true

        # Wait up to 5 seconds for graceful shutdown
        local count=0
        while kill -0 "$BACKEND_PID" 2>/dev/null && [ $count -lt 5 ]; do
            sleep 1
            ((count++))
        done

        # Force kill if still running
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            print_warning "Force killing backend..."
            kill -9 "$BACKEND_PID" 2>/dev/null || true
        fi
        print_success "Backend stopped"
    fi

    echo ""
    print_success "TK9 Dashboard stopped gracefully"
    echo ""
}

# Trap signals for graceful shutdown
trap cleanup EXIT
trap cleanup SIGINT
trap cleanup SIGTERM
trap cleanup SIGKILL

# ============================================================================
# Validation Functions
# ============================================================================

check_directory_structure() {
    print_section "Validating Directory Structure"

    if [[ ! -f "$BACKEND_MAIN" ]]; then
        print_error "Backend main.py not found at: $BACKEND_MAIN"
        return 1
    fi
    print_success "Backend main.py found"

    if [[ ! -d "$FRONTEND_DIR" ]]; then
        print_error "Frontend directory not found at: $FRONTEND_DIR"
        return 1
    fi
    print_success "Frontend directory found"

    if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
        print_error "Frontend package.json not found"
        return 1
    fi
    print_success "Frontend package.json found"

    if [[ ! -f "$BACKEND_MAIN" ]]; then
        print_error "Backend main.py not found at: $BACKEND_MAIN"
        return 1
    fi
    print_success "Backend main.py validated"

    return 0
}

find_python_command() {
    local python_cmd=""

    # Try Python versions in order of preference
    for cmd in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            python_cmd="$cmd"
            break
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        return 1
    fi

    echo "$python_cmd"
    return 0
}

setup_python_venv() {
    local python_cmd="$1"
    local venv_dir="$SCRIPT_DIR/venv"

    print_section "Python Virtual Environment Setup"

    # Check if venv exists
    if [[ -d "$venv_dir" ]] && [[ -f "$venv_dir/bin/python" ]]; then
        print_success "Virtual environment found at: $venv_dir"
    else
        print_step "Creating virtual environment (required for Python 3.12+ PEP 668)..."
        if $python_cmd -m venv "$venv_dir"; then
            print_success "Virtual environment created"
        else
            print_error "Failed to create virtual environment"
            return 1
        fi
    fi

    # Return path to venv python
    echo "$venv_dir/bin/python"
}

check_python_dependencies() {
    local python_cmd="$1"
    print_section "Checking Python Dependencies"

    print_step "Using Python: $python_cmd ($($python_cmd --version 2>&1))"

    # Check for required packages
    local required_packages=(
        "fastapi"
        "uvicorn"
        "websockets"
        "pydantic"
        "aiofiles"
        "python-dotenv"
    )

    local missing_packages=()

    for package in "${required_packages[@]}"; do
        if ! $python_cmd -c "import ${package//-/_}" 2>/dev/null; then
            missing_packages+=("$package")
            print_warning "Missing: $package"
        else
            print_success "Found: $package"
        fi
    done

    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_error "Missing ${#missing_packages[@]} Python package(s) - REQUIRED for production"

        if [[ "$PRODUCTION_MODE" == "true" ]]; then
            # Production mode: auto-install without prompting
            print_step "Auto-installing Python dependencies (production mode)..."
            if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
                $python_cmd -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
                print_success "Python dependencies installed"
            else
                print_error "requirements.txt not found"
                return 1
            fi
        else
            # Development mode: ask for permission
            echo ""
            read -p "$(echo -e ${YELLOW}Install missing Python packages? [Y/n]: ${NC})" -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                print_step "Installing Python dependencies..."
                if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
                    $python_cmd -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
                    print_success "Python dependencies installed"
                else
                    print_error "requirements.txt not found"
                    return 1
                fi
            else
                print_error "Cannot proceed without required dependencies"
                return 1
            fi
        fi
    else
        print_success "All Python dependencies satisfied"
    fi

    return 0
}

check_node_dependencies() {
    print_section "Checking Node.js Dependencies"

    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org"
        return 1
    fi

    local node_version=$(node --version)
    print_success "Node.js found: $node_version"

    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm not found. Please install npm"
        return 1
    fi

    print_success "npm found: $(npm --version)"

    # Check if node_modules exists
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        print_error "Frontend dependencies not installed - REQUIRED for production"

        if [[ "$PRODUCTION_MODE" == "true" ]]; then
            # Production mode: auto-install without prompting
            print_step "Auto-installing frontend dependencies (production mode)..."
            print_info "This may take a few minutes on first run..."
            cd "$FRONTEND_DIR"
            npm install --silent
            cd "$SCRIPT_DIR"
            print_success "Frontend dependencies installed"
        else
            # Development mode: ask for permission
            echo ""
            read -p "$(echo -e ${YELLOW}Install frontend dependencies? [Y/n]: ${NC})" -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                print_step "Installing frontend dependencies (this may take a few minutes)..."
                cd "$FRONTEND_DIR"
                npm install --silent
                cd "$SCRIPT_DIR"
                print_success "Frontend dependencies installed"
            else
                print_error "Cannot proceed without frontend dependencies"
                return 1
            fi
        fi
    else
        print_success "Frontend dependencies found"
    fi

    return 0
}

# ============================================================================
# Environment Configuration
# ============================================================================

load_env_file() {
    # ONLY load web_dashboard/.env (never .env.production or project root .env)
    local env_file="$SCRIPT_DIR/.env"

    print_info "Loading environment from: $env_file"

    if [[ -f "$env_file" ]]; then
        set -a  # Automatically export all variables
        source "$env_file"
        set +a
        print_success "Environment loaded from web_dashboard/.env"
        return 0
    fi

    return 1
}

prompt_for_env_var() {
    local var_name="$1"
    local var_description="$2"
    local var_default="$3"
    local is_secret="${4:-false}"

    echo ""
    echo -e "${CYAN}${BOLD}Configure: $var_description${NC}"

    if [[ -n "$var_default" ]]; then
        read -p "$(echo -e ${WHITE}Enter $var_name [default: $var_default]: ${NC})" var_value
        var_value="${var_value:-$var_default}"
    else
        if [[ "$is_secret" == "true" ]]; then
            read -s -p "$(echo -e ${WHITE}Enter $var_name: ${NC})" var_value
            echo ""
        else
            read -p "$(echo -e ${WHITE}Enter $var_name: ${NC})" var_value
        fi
    fi

    echo "$var_value"
}

configure_environment() {
    print_section "Environment Configuration [DEVELOPMENT MODE]"

    # Try to load existing .env file
    if load_env_file; then
        print_success "Loaded existing .env file"
    else
        print_warning "No .env file found"
        print_info "Some features may not work without proper configuration"
    fi

    # Define required environment variables
    local required_vars=(
        "SUPABASE_URL:Supabase Project URL"
        "SUPABASE_SERVICE_KEY:Supabase Service Role Key"
        "SUPABASE_ANON_KEY:Supabase Anonymous Key"
        "JWT_SECRET:JWT Secret for token validation"
    )

    local missing_vars=()

    # Check for missing required variables (development mode - show values)
    for var_spec in "${required_vars[@]}"; do
        IFS=':' read -r var_name var_desc <<< "$var_spec"

        if [[ -z "${!var_name}" ]] || [[ "${!var_name}" == "your-project.supabase.co" ]] || [[ "${!var_name}" == *"your_"* ]] || [[ "${!var_name}" == *"example"* ]]; then
            missing_vars+=("$var_name")
            print_warning "$var_name: MISSING or PLACEHOLDER"
        else
            # Show first 20 chars in development for debugging
            local value="${!var_name}"
            local preview="${value:0:20}..."
            print_success "$var_name: $preview"
        fi
    done

    # In development mode, warn but continue
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_warning "${#missing_vars[@]} required environment variable(s) missing"
        echo ""
        echo -e "${YELLOW}${BOLD}Missing/Invalid variables:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "  ${YELLOW}⚠${NC} $var"
        done
        echo ""
        print_info "Dashboard will start but some features may not work"
        print_info "Configure these in web_dashboard/.env file"
    else
        print_success "All required environment variables configured"
    fi

    # Set development defaults
    export HOST="${HOST:-0.0.0.0}"
    export PORT="${PORT:-$BACKEND_PORT}"

    # Development CORS - comprehensive list for HTTP, HTTPS, WebSocket (WS, WSS)
    # Includes original domain (tk9.thinhkhuat.com) and v2 domain (tk9v2.thinhkhuat.com)
    # Format: frontend URLs (http/https/ws/wss) + backend URLs (http)
    local default_cors="http://localhost:5173,http://127.0.0.1:5173,http://192.168.2.22:5173"
    default_cors+=",https://tk9.thinhkhuat.com,https://tk9v2.thinhkhuat.com"
    default_cors+=",ws://localhost:5173,ws://127.0.0.1:5173,ws://192.168.2.22:5173"
    default_cors+=",wss://tk9.thinhkhuat.com,wss://tk9v2.thinhkhuat.com"
    default_cors+=",http://localhost:12656,http://127.0.0.1:12656,http://192.168.2.22:12656"

    export CORS_ORIGINS="${CORS_ORIGINS:-$default_cors}"

    print_info "CORS configured for development (HTTP/HTTPS/WS/WSS)"
    print_info "Backend will listen on: $HOST:$PORT"

    return 0
}

# ============================================================================
# Server Management
# ============================================================================

check_port_available() {
    local port="$1"
    local process_name="$2"

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        print_error "Port $port is already in use by PID $pid"

        # Check if it's a TK9 process
        local process_cmd=$(ps -p $pid -o command= 2>/dev/null)
        if [[ "$process_cmd" == *"main.py"* ]] || [[ "$process_cmd" == *"vite"* ]]; then
            print_warning "This appears to be a TK9 process"
            echo ""
            read -p "$(echo -e ${YELLOW}Kill existing $process_name process? [Y/n]: ${NC})" -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                kill -TERM $pid 2>/dev/null || kill -9 $pid 2>/dev/null
                sleep 2
                print_success "Killed existing process"
                return 0
            else
                return 1
            fi
        else
            print_error "Port is used by non-TK9 process. Please free the port manually."
            return 1
        fi
    fi

    return 0
}

start_backend() {
    local python_cmd="$1"

    print_section "Starting Backend Server [DEVELOPMENT]"

    # Check if port is available
    if ! check_port_available "$BACKEND_PORT" "backend"; then
        return 1
    fi

    print_step "Starting FastAPI/Uvicorn on port $BACKEND_PORT (development mode)..."
    print_info "Output: Console (no log file)"

    # Start backend in background (console output)
    cd "$SCRIPT_DIR"
    $python_cmd "$BACKEND_MAIN" > /dev/null 2>&1 &
    BACKEND_PID=$!

    # Wait for backend to start
    print_step "Waiting for backend to be ready (health check)..."
    local count=0
    local max_wait=30

    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
            print_success "Backend server started successfully"
            print_success "  PID: $BACKEND_PID"
            print_success "  Port: $BACKEND_PORT"
            print_success "  Mode: DEVELOPMENT"
            return 0
        fi

        # Check if process is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            print_error "Try running manually: python3 main.py"
            return 1
        fi

        sleep 1
        ((count++))
    done

    print_error "Backend failed to start within ${max_wait}s"
    return 1
}

start_frontend() {
    print_section "Starting Frontend Server [DEVELOPMENT]"

    # Check if port is available
    if ! check_port_available "$FRONTEND_PORT" "frontend"; then
        return 1
    fi

    print_step "Starting Vite dev server on port $FRONTEND_PORT..."
    print_info "Mode: Development (hot-reload enabled)"
    print_info "Output: Console (no log file)"

    # Start frontend dev server
    cd "$FRONTEND_DIR"
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!

    # Wait for frontend to start
    print_step "Waiting for frontend to be ready..."
    local count=0
    local max_wait=30

    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            print_success "Frontend server started successfully"
            print_success "  PID: $FRONTEND_PID"
            print_success "  Port: $FRONTEND_PORT"
            print_success "  Mode: DEVELOPMENT (hot-reload)"
            cd "$SCRIPT_DIR"
            return 0
        fi

        # Check if process is still running
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            print_error "Try running manually: cd frontend_poc && npm run dev"
            cd "$SCRIPT_DIR"
            return 1
        fi

        sleep 1
        ((count++))
    done

    print_error "Frontend failed to start within ${max_wait}s"
    print_error "Try running manually: cd frontend_poc && npm run dev"
    cd "$SCRIPT_DIR"
    return 1
}

display_access_info() {
    print_section "TK9 Dashboard V2 - Development Access Information"

    echo ""
    echo -e "${GREEN}${BOLD}✓ Dashboard is now running in DEVELOPMENT mode!${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}Frontend Access (Port $FRONTEND_PORT):${NC}"
    echo -e "  ${CYAN}Local:${NC}        http://localhost:$FRONTEND_PORT"
    echo -e "  ${CYAN}Internal:${NC}     http://192.168.2.22:$FRONTEND_PORT"
    echo -e "  ${CYAN}Public (v2):${NC}  https://tk9v2.thinhkhuat.com ${YELLOW}(via proxy)${NC}"
    echo -e "  ${CYAN}Public (v1):${NC}  https://tk9.thinhkhuat.com ${YELLOW}(via proxy)${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}Backend Access (Port $BACKEND_PORT):${NC}"
    echo -e "  ${CYAN}Local:${NC}     http://localhost:$BACKEND_PORT"
    echo -e "  ${CYAN}Internal:${NC}  http://192.168.2.22:$BACKEND_PORT"
    echo -e "  ${CYAN}API Docs:${NC}  http://localhost:$BACKEND_PORT/docs"
    echo -e "  ${CYAN}Health:${NC}    http://localhost:$BACKEND_PORT/health"
    echo ""

    echo -e "${WHITE}${BOLD}Development Configuration:${NC}"
    echo -e "  ${CYAN}Mode:${NC}         DEVELOPMENT (hot-reload enabled)"
    echo -e "  ${CYAN}Backend PID:${NC}  $BACKEND_PID"
    echo -e "  ${CYAN}Frontend PID:${NC} $FRONTEND_PID"
    echo -e "  ${CYAN}Output:${NC}       Console (no log files)"
    echo ""

    echo -e "${WHITE}${BOLD}Development Features:${NC}"
    echo -e "  ${GREEN}✓${NC} Hot Module Replacement (HMR)"
    echo -e "  ${GREEN}✓${NC} Auto-restart on file changes"
    echo -e "  ${GREEN}✓${NC} Source maps enabled"
    echo -e "  ${GREEN}✓${NC} Detailed error messages"
    echo ""

    echo -e "${YELLOW}${BOLD}⚠  Press Ctrl+C to stop all services gracefully${NC}"
    echo ""
}

# ============================================================================
# Main Execution Flow
# ============================================================================

main() {
    print_header

    # Step 1: Validate directory structure
    if ! check_directory_structure; then
        print_error "Directory structure validation failed"
        exit 1
    fi

    # Step 2: Find Python command
    print_section "Detecting Python Installation"
    PYTHON_CMD=$(find_python_command)
    if [[ -z "$PYTHON_CMD" ]]; then
        print_error "No suitable Python installation found"
        print_info "Please install Python 3.10+ from https://python.org"
        exit 1
    fi
    print_success "Found System Python: $PYTHON_CMD"

    # Step 3: Setup virtual environment (required for Python 3.12+ PEP 668)
    VENV_PYTHON=$(setup_python_venv "$PYTHON_CMD")
    if [[ -z "$VENV_PYTHON" ]]; then
        print_error "Virtual environment setup failed"
        exit 1
    fi
    # Use venv python for all subsequent operations
    PYTHON_CMD="$VENV_PYTHON"
    print_success "Using Virtual Environment Python: $PYTHON_CMD"

    # Step 4: Check Python dependencies
    if ! check_python_dependencies "$PYTHON_CMD"; then
        print_error "Python dependency check failed"
        exit 1
    fi

    # Step 4: Check Node.js dependencies
    if ! check_node_dependencies; then
        print_error "Node.js dependency check failed"
        exit 1
    fi

    # Step 5: Configure environment
    if ! configure_environment; then
        print_error "Environment configuration failed"
        exit 1
    fi

    # Step 6: Start backend server
    if ! start_backend "$PYTHON_CMD"; then
        print_error "Failed to start backend server"
        exit 1
    fi

    # Step 7: Start frontend server
    if ! start_frontend; then
        print_error "Failed to start frontend server"
        cleanup
        exit 1
    fi

    # Step 8: Display access information
    display_access_info

    # Step 9: Keep script running and monitor processes
    while true; do
        # Check if backend is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            cleanup
            exit 1
        fi

        # Check if frontend is still running
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            cleanup
            exit 1
        fi

        sleep 5
    done
}

# ============================================================================
# Script Entry Point
# ============================================================================

main "$@"
