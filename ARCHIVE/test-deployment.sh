#!/bin/bash
# ============================================================================
# Deep Research MCP - Deployment Testing Script
# ============================================================================
# This script tests various aspects of the deployment to ensure everything
# is working correctly after deployment.
#
# Usage:
#   ./test-deployment.sh [options]
#
# Options:
#   --endpoint URL    Test specific endpoint (default: http://localhost:8000)
#   --timeout SEC     Request timeout in seconds (default: 30)
#   --verbose         Enable verbose output
#   --skip-api        Skip API key tests (for environments without keys)
#   --quick           Run only basic tests
#   --full            Run comprehensive test suite
#
# Examples:
#   ./test-deployment.sh                    # Basic deployment test
#   ./test-deployment.sh --verbose --full   # Comprehensive test with verbose output
#   ./test-deployment.sh --endpoint https://your-domain.com/api
# ============================================================================

set -euo pipefail

# Configuration
ENDPOINT="${ENDPOINT:-http://localhost:8000}"
TIMEOUT=30
VERBOSE=false
SKIP_API_TESTS=false
TEST_MODE="basic"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# ============================================================================
# Utility Functions
# ============================================================================

log() {
    echo -e "${GREEN}[TEST] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}[DEBUG] $1${NC}"
    fi
}

test_passed() {
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
    log "✓ $1"
}

test_failed() {
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
    log_error "✗ $1"
}

test_skipped() {
    log_warn "⊘ $1 (skipped)"
}

show_summary() {
    echo
    echo "============================================================================"
    echo "Test Summary"
    echo "============================================================================"
    echo "Total tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 All tests passed! Deployment is ready.${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Some tests failed. Please check the deployment.${NC}"
        exit 1
    fi
}

# ============================================================================
# HTTP Test Functions
# ============================================================================

http_get() {
    local url="$1"
    local expected_status="${2:-200}"
    
    log_verbose "GET $url"
    
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "HTTPSTATUS:000")
    status_code=$(echo "$response" | sed -E 's/.*HTTPSTATUS:([0-9]{3}).*/\1/')
    
    if [[ "$status_code" == "000" ]]; then
        log_verbose "Request failed - connection error"
        return 1
    fi
    
    if [[ "$status_code" != "$expected_status" ]]; then
        log_verbose "Expected status $expected_status, got $status_code"
        return 1
    fi
    
    # Return response body without status code
    echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//'
    return 0
}

http_post() {
    local url="$1"
    local data="$2"
    local expected_status="${3:-200}"
    
    log_verbose "POST $url with data: $data"
    
    local response
    local status_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
                   --max-time "$TIMEOUT" \
                   -H "Content-Type: application/json" \
                   -d "$data" \
                   "$url" 2>/dev/null || echo "HTTPSTATUS:000")
    
    status_code=$(echo "$response" | sed -E 's/.*HTTPSTATUS:([0-9]{3}).*/\1/')
    
    if [[ "$status_code" == "000" ]]; then
        log_verbose "Request failed - connection error"
        return 1
    fi
    
    if [[ "$status_code" != "$expected_status" ]]; then
        log_verbose "Expected status $expected_status, got $status_code"
        return 1
    fi
    
    # Return response body without status code
    echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//'
    return 0
}

# ============================================================================
# Test Functions
# ============================================================================

test_basic_connectivity() {
    log_info "Testing basic connectivity..."
    
    if http_get "$ENDPOINT" >/dev/null 2>&1; then
        test_passed "Server is responding"
    else
        test_failed "Server is not responding at $ENDPOINT"
        return 1
    fi
    
    # Test with timeout
    local start_time
    start_time=$(date +%s)
    
    if http_get "$ENDPOINT" >/dev/null 2>&1; then
        local end_time
        end_time=$(date +%s)
        local response_time=$((end_time - start_time))
        
        if [[ $response_time -le 10 ]]; then
            test_passed "Response time acceptable ($response_time seconds)"
        else
            log_warn "Response time slow ($response_time seconds)"
        fi
    fi
}

test_health_endpoint() {
    log_info "Testing health endpoint..."
    
    local health_response
    if health_response=$(http_get "$ENDPOINT/health" 2>/dev/null); then
        test_passed "Health endpoint responding"
        
        # Parse JSON response
        if echo "$health_response" | grep -q '"status"'; then
            local status
            status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            
            if [[ "$status" == "healthy" ]]; then
                test_passed "System reports healthy status"
            elif [[ "$status" == "degraded" ]]; then
                log_warn "System reports degraded status"
                test_passed "Health endpoint working (degraded status)"
            else
                test_failed "System reports unhealthy status: $status"
            fi
        else
            test_failed "Health endpoint returned invalid JSON"
        fi
        
        log_verbose "Health response: $health_response"
    else
        test_failed "Health endpoint not responding"
    fi
}

test_system_info_endpoint() {
    log_info "Testing system info endpoint..."
    
    local info_response
    if info_response=$(http_get "$ENDPOINT/system-info" 2>/dev/null); then
        test_passed "System info endpoint responding"
        
        # Check for key fields
        if echo "$info_response" | grep -q '"version"'; then
            test_passed "System info contains version"
        else
            log_warn "System info missing version field"
        fi
        
        if echo "$info_response" | grep -q '"python_version"'; then
            test_passed "System info contains Python version"
        else
            log_warn "System info missing Python version"
        fi
        
        log_verbose "System info response: $info_response"
    else
        test_failed "System info endpoint not responding"
    fi
}

test_cors_headers() {
    log_info "Testing CORS headers..."
    
    local cors_test
    if cors_test=$(curl -s -I --max-time "$TIMEOUT" \
                       -H "Origin: https://example.com" \
                       -H "Access-Control-Request-Method: POST" \
                       -H "Access-Control-Request-Headers: Content-Type" \
                       -X OPTIONS \
                       "$ENDPOINT" 2>/dev/null); then
        
        if echo "$cors_test" | grep -q "Access-Control-Allow-Origin"; then
            test_passed "CORS headers present"
        else
            log_warn "CORS headers missing (might be intentional)"
        fi
    else
        log_warn "CORS preflight test failed"
    fi
}

test_research_endpoint() {
    log_info "Testing research endpoint..."
    
    if [[ "$SKIP_API_TESTS" == true ]]; then
        test_skipped "Research endpoint test (API keys not configured)"
        return 0
    fi
    
    # Test with minimal query
    local test_query='{"query": "What is artificial intelligence?", "tone": "objective"}'
    
    local research_response
    if research_response=$(http_post "$ENDPOINT/research" "$test_query" 200 2>/dev/null); then
        test_passed "Research endpoint accepting requests"
        
        # Check response structure
        if echo "$research_response" | grep -q '"status"'; then
            local status
            status=$(echo "$research_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            
            if [[ "$status" == "success" ]]; then
                test_passed "Research request processed successfully"
            elif [[ "$status" == "error" ]]; then
                local error
                error=$(echo "$research_response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
                test_failed "Research request failed: $error"
            else
                test_failed "Research request returned unknown status: $status"
            fi
        else
            test_failed "Research endpoint returned invalid response format"
        fi
        
        log_verbose "Research response: ${research_response:0:200}..."
    else
        test_failed "Research endpoint not responding or returning error"
    fi
}

test_error_handling() {
    log_info "Testing error handling..."
    
    # Test invalid endpoint
    if ! http_get "$ENDPOINT/invalid-endpoint" 404 >/dev/null 2>&1; then
        log_warn "Invalid endpoint should return 404"
    else
        test_passed "404 handling working correctly"
    fi
    
    # Test invalid JSON
    local invalid_json='{"invalid": json}'
    if ! http_post "$ENDPOINT/research" "$invalid_json" 400 >/dev/null 2>&1; then
        log_warn "Invalid JSON should return 400"
    else
        test_passed "Invalid JSON handling working"
    fi
    
    # Test missing required field
    local missing_query='{"tone": "objective"}'
    if ! http_post "$ENDPOINT/research" "$missing_query" 400 >/dev/null 2>&1; then
        log_warn "Missing required fields should return 400"
    else
        test_passed "Required field validation working"
    fi
}

test_docker_services() {
    log_info "Testing Docker services (if applicable)..."
    
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        # Check if Docker Compose is running
        if docker-compose ps >/dev/null 2>&1; then
            local running_services
            running_services=$(docker-compose ps --services --filter "status=running")
            
            if echo "$running_services" | grep -q "deep-research-mcp"; then
                test_passed "MCP server container running"
            else
                test_failed "MCP server container not running"
            fi
            
            if echo "$running_services" | grep -q "redis"; then
                test_passed "Redis container running"
            else
                log_warn "Redis container not running (optional)"
            fi
            
            if echo "$running_services" | grep -q "nginx"; then
                test_passed "Nginx container running"
            else
                log_warn "Nginx container not running (optional)"
            fi
        else
            test_skipped "Docker Compose services check (not running via Docker Compose)"
        fi
    else
        test_skipped "Docker services check (Docker not available)"
    fi
}

test_environment_configuration() {
    log_info "Testing environment configuration..."
    
    # Check if .env file exists
    if [[ -f ".env" ]]; then
        test_passed "Environment file (.env) exists"
        
        # Check for required variables
        local required_vars=("PRIMARY_LLM_PROVIDER" "PRIMARY_SEARCH_PROVIDER")
        
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" .env; then
                test_passed "Required variable $var configured"
            else
                test_failed "Required variable $var missing from .env"
            fi
        done
        
        # Check for API keys (without showing values)
        local api_keys=("GOOGLE_API_KEY" "OPENAI_API_KEY" "BRAVE_API_KEY" "TAVILY_API_KEY")
        local configured_keys=0
        
        for key in "${api_keys[@]}"; do
            if grep -q "^$key=" .env && ! grep -q "$key=your_.*_here" .env; then
                ((configured_keys++))
            fi
        done
        
        if [[ $configured_keys -gt 0 ]]; then
            test_passed "At least one API key configured"
        else
            log_warn "No API keys appear to be configured"
        fi
        
    else
        test_failed "Environment file (.env) missing"
    fi
}

test_file_permissions() {
    log_info "Testing file permissions..."
    
    local directories=("outputs" "logs" "data")
    
    for dir in "${directories[@]}"; do
        if [[ -d "$dir" ]]; then
            if [[ -w "$dir" ]]; then
                test_passed "Directory $dir is writable"
            else
                test_failed "Directory $dir is not writable"
            fi
        else
            log_warn "Directory $dir does not exist"
        fi
    done
    
    # Check script permissions
    if [[ -x "deploy.sh" ]]; then
        test_passed "Deploy script is executable"
    else
        test_failed "Deploy script is not executable"
    fi
}

test_dependencies() {
    log_info "Testing Python dependencies..."
    
    # Test if we can import key modules
    local modules=("fastapi" "gpt_researcher" "google.generativeai" "aiohttp")
    
    for module in "${modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            test_passed "Python module $module available"
        else
            test_failed "Python module $module not available"
        fi
    done
}

# ============================================================================
# Main Test Execution
# ============================================================================

run_basic_tests() {
    log_info "Running basic deployment tests..."
    
    test_basic_connectivity
    test_health_endpoint
    test_environment_configuration
    test_file_permissions
}

run_comprehensive_tests() {
    log_info "Running comprehensive deployment tests..."
    
    test_basic_connectivity
    test_health_endpoint
    test_system_info_endpoint
    test_cors_headers
    test_research_endpoint
    test_error_handling
    test_docker_services
    test_environment_configuration
    test_file_permissions
    test_dependencies
}

# ============================================================================
# Command Line Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --endpoint)
                ENDPOINT="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skip-api)
                SKIP_API_TESTS=true
                shift
                ;;
            --quick)
                TEST_MODE="basic"
                shift
                ;;
            --full)
                TEST_MODE="comprehensive"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    echo "Deep Research MCP - Deployment Testing Script"
    echo
    echo "Usage: ./test-deployment.sh [options]"
    echo
    echo "Options:"
    echo "  --endpoint URL    Test specific endpoint (default: http://localhost:8000)"
    echo "  --timeout SEC     Request timeout in seconds (default: 30)"
    echo "  --verbose         Enable verbose output"
    echo "  --skip-api        Skip API key tests"
    echo "  --quick           Run only basic tests"
    echo "  --full            Run comprehensive test suite"
    echo "  --help            Show this help message"
    echo
    echo "Examples:"
    echo "  ./test-deployment.sh                    # Basic tests"
    echo "  ./test-deployment.sh --verbose --full   # Comprehensive tests"
    echo "  ./test-deployment.sh --endpoint https://your-domain.com/api"
}

show_banner() {
    echo "============================================================================"
    echo "Deep Research MCP - Deployment Testing"
    echo "============================================================================"
    echo "Endpoint: $ENDPOINT"
    echo "Timeout: ${TIMEOUT}s"
    echo "Test Mode: $TEST_MODE"
    echo "============================================================================"
    echo
}

main() {
    parse_args "$@"
    
    show_banner
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl is required for testing but not installed"
        exit 1
    fi
    
    # Run tests based on mode
    case "$TEST_MODE" in
        basic)
            run_basic_tests
            ;;
        comprehensive)
            run_comprehensive_tests
            ;;
        *)
            log_error "Unknown test mode: $TEST_MODE"
            exit 1
            ;;
    esac
    
    show_summary
}

# ============================================================================
# Script Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi