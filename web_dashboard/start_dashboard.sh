#!/bin/bash

# Deep Research MCP Web Dashboard Startup Script

echo "🚀 Starting Deep Research MCP Web Dashboard..."
echo "================================================"

# Check if we're in the correct directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found. Please run from web_dashboard directory."
    exit 1
fi

# Check if parent directory has the main project
if [[ ! -f "../main.py" ]]; then
    echo "❌ Error: Main project not found. Please ensure web_dashboard is inside the project."
    exit 1
fi

# Try to find a working Python version
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3 python; do
    if command -v $cmd &> /dev/null; then
        if $cmd -c "import fastapi, uvicorn" 2>/dev/null; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "❌ Error: No suitable Python with FastAPI found."
    echo "   Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Using Python: $PYTHON_CMD"

# Check main project CLI
echo "🔧 Testing main project CLI..."
cd ..
if $PYTHON_CMD main.py --help &>/dev/null; then
    echo "✅ Main CLI is working"
else
    echo "⚠️  Warning: Main CLI may have issues, but continuing..."
fi

# Return to web_dashboard
cd web_dashboard

# Check dependencies
echo "📦 Checking dependencies..."
if $PYTHON_CMD -c "import fastapi, uvicorn, websockets, jinja2, aiofiles, pydantic" 2>/dev/null; then
    echo "✅ All dependencies available"
else
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

echo ""
echo "🌐 Starting web dashboard on http://0.0.0.0:12656 (all interfaces)"
echo "📊 Public access: https://tk9.thinhkhuat.com (via Caddy reverse proxy)"
echo "📊 Local access: http://localhost:12656"
echo "📊 Internal access: http://192.168.2.22:12656"
echo "🔄 Press Ctrl+C to stop the server"
echo ""

# Start the server with correct IP for reverse proxy
$PYTHON_CMD main.py