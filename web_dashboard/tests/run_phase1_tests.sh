#!/bin/bash
# Test runner for Phase 1 configuration tests
# Usage: ./run_phase1_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Phase 1 Configuration Test Suite${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

# Backup current environment
export BACKUP_CORS_ORIGINS="$CORS_ORIGINS"
export BACKUP_PORT="$PORT"
export BACKUP_FILE_WAIT_TIMEOUT="$FILE_WAIT_TIMEOUT"

# Clear environment variables for clean test run
unset CORS_ORIGINS
unset PORT
unset FILE_WAIT_TIMEOUT
unset SESSION_CLEANUP_INTERVAL
unset RESEARCH_LANGUAGE

echo -e "${YELLOW}Running Backend Configuration Tests...${NC}"
echo ""

# Run backend tests with coverage
pytest tests/test_config.py \
    -v \
    --tb=short \
    --cov=web_dashboard \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/phase1_backend

BACKEND_EXIT=$?

echo ""
echo -e "${YELLOW}Running Backend Integration Tests...${NC}"
echo ""

pytest tests/test_config_integration.py \
    -v \
    --tb=short \
    --cov=web_dashboard \
    --cov-append \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/phase1_integration

INTEGRATION_EXIT=$?

# Restore environment
export CORS_ORIGINS="$BACKUP_CORS_ORIGINS"
export PORT="$BACKUP_PORT"
export FILE_WAIT_TIMEOUT="$BACKUP_FILE_WAIT_TIMEOUT"

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}================================================${NC}"

if [ $BACKEND_EXIT -eq 0 ] && [ $INTEGRATION_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo -e "${YELLOW}Coverage reports:${NC}"
    echo "  - Backend: htmlcov/phase1_backend/index.html"
    echo "  - Integration: htmlcov/phase1_integration/index.html"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    if [ $BACKEND_EXIT -ne 0 ]; then
        echo -e "${RED}  - Backend tests failed${NC}"
    fi
    if [ $INTEGRATION_EXIT -ne 0 ]; then
        echo -e "${RED}  - Integration tests failed${NC}"
    fi
    echo ""
    exit 1
fi
