#!/bin/bash
# Installation script for Pydantic BaseSettings migration
# Run this after pulling the Pydantic BaseSettings changes

set -e

echo "================================================"
echo "Installing Pydantic BaseSettings Dependencies"
echo "================================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  WARNING: Not in a virtual environment"
    echo "It's recommended to use a virtual environment."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo "Installing pydantic-settings..."
pip install pydantic-settings==2.1.0

echo ""
echo "================================================"
echo "Running Configuration Tests"
echo "================================================"
echo ""

# Run tests to verify installation
if command -v pytest &> /dev/null; then
    pytest tests/test_config_pydantic.py -v --tb=short
    TEST_EXIT=$?

    if [ $TEST_EXIT -eq 0 ]; then
        echo ""
        echo "✅ All tests passed!"
    else
        echo ""
        echo "❌ Some tests failed. Please review the output above."
        exit 1
    fi
else
    echo "⚠️  pytest not found. Skipping tests."
    echo "Install pytest with: pip install pytest"
fi

echo ""
echo "================================================"
echo "Verifying Application Startup"
echo "================================================"
echo ""

echo "Testing configuration loading..."
python -c "from config import settings; print(f'✅ Configuration loaded: PORT={settings.PORT}')"

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review configuration: cat config.py"
echo "2. Update .env file if needed"
echo "3. Start the application: python main.py"
echo "4. Check logs for configuration output"
echo ""
echo "Documentation:"
echo "- PYDANTIC_BASESETTINGS_MIGRATION.md - Full migration guide"
echo "- tests/test_config_pydantic.py - Test examples"
echo ""
