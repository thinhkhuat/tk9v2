# Troubleshooting and FAQ

## Overview

This document provides comprehensive troubleshooting guidance for common issues encountered with the Deep Research MCP system, along with frequently asked questions and their solutions.

## Table of Contents

- [Common Issues](#common-issues)
- [Installation Problems](#installation-problems)
- [Configuration Issues](#configuration-issues)
- [API and Provider Problems](#api-and-provider-problems)
- [Translation Issues](#translation-issues)
- [Performance Problems](#performance-problems)
- [File Generation Issues](#file-generation-issues)
- [Memory and Resource Issues](#memory-and-resource-issues)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Diagnostic Tools](#diagnostic-tools)

## Common Issues

### Issue: "No module named 'multi_agents'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'multi_agents'
```

**Cause:** Python path not set correctly or running from wrong directory.

**Solution:**
```bash
# Ensure you're in the project root directory
cd /path/to/deep-research-mcp-og

# Add current directory to Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Or run with explicit path
python -m multi_agents.main
```

### Issue: "OpenAI API key not found"

**Symptoms:**
```
Error: OpenAI API key not provided. Please set OPENAI_API_KEY environment variable.
```

**Cause:** Missing or incorrectly set API key.

**Solution:**
```bash
# Check if .env file exists
ls -la .env

# Verify API key is set
grep OPENAI_API_KEY .env

# If missing, add to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Reload environment
source .env
```

### Issue: Research gets stuck on initial research phase

**Symptoms:**
- Process hangs during "Starting initial research"
- No progress updates for extended periods
- Memory usage continues to increase

**Cause:** Network connectivity issues, API rate limits, or infinite loops.

**Solution:**
```bash
# Check network connectivity
curl -I https://api.openai.com/v1/models

# Run with verbose logging
python main.py --research "Your query" --verbose

# Check API rate limits
python scripts/check_api_limits.py

# Use fallback providers
export FALLBACK_LLM_PROVIDER=google_gemini
python main.py --research "Your query"
```

### Issue: Translation fails with timeout errors

**Symptoms:**
```
Translation attempt 1 failed with error: ServerTimeoutError
All 3 translation attempts failed
```

**Cause:** Translation endpoint unreachable or overloaded.

**Solution:**
```bash
# Test translation endpoints manually
curl -X POST https://n8n.thinhkhuat.com/webhook/agent/translate \
  -H "Content-Type: application/json" \
  -d '{"transcript":"test","sessionId":"test123"}'

# Increase timeout in configuration
export TRANSLATION_TIMEOUT=180

# Skip translation for testing
export RESEARCH_LANGUAGE=en
```

## Installation Problems

### Issue: "pip install fails with compilation errors"

**Symptoms:**
```
Building wheel for package failed
ERROR: Failed building wheel for package
```

**Solution:**
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev build-essential

# Install system dependencies (macOS)
xcode-select --install

# Use conda instead of pip
conda install package-name

# Install from pre-compiled wheels
pip install --only-binary=all package-name
```

### Issue: "pandoc command not found"

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'pandoc'
```

**Solution:**
```bash
# Install pandoc (Ubuntu/Debian)
sudo apt-get install pandoc

# Install pandoc (macOS)
brew install pandoc

# Install pandoc (Windows)
choco install pandoc

# Verify installation
pandoc --version
```

### Issue: "LaTeX not found for PDF generation"

**Symptoms:**
```
PDF generation failed. Error: xelatex not found
```

**Solution:**
```bash
# Install LaTeX (Ubuntu/Debian)
sudo apt-get install texlive-latex-base texlive-fonts-recommended

# Install LaTeX (macOS)
brew install --cask basictex
sudo /usr/local/texlive/2023/bin/universal-darwin/tlmgr update --self

# Install LaTeX (Windows)
choco install miktex

# Verify installation
xelatex --version
```

## Configuration Issues

### Issue: "Provider configuration not found"

**Symptoms:**
```
Provider setup error: Configuration file not found
```

**Solution:**
```bash
# Check if config directory exists
ls -la multi_agents/config/

# Create missing configuration
mkdir -p multi_agents/config
cp config/templates/providers.json multi_agents/config/

# Verify configuration syntax
python -c "import json; json.load(open('multi_agents/config/providers.json'))"
```

### Issue: "Invalid language configuration"

**Symptoms:**
```
Language setup error: Language 'xyz' not supported
```

**Solution:**
```bash
# Check supported languages
python -c "from multi_agents.utils.language_config import LanguageConfig; print(LanguageConfig.supported_languages)"

# Use correct language codes
export RESEARCH_LANGUAGE=vi  # for Vietnamese
export RESEARCH_LANGUAGE=es  # for Spanish

# Update task.json with correct language
nano multi_agents/task.json
```

### Issue: "Environment variables not loading"

**Symptoms:**
Variables set in `.env` file are not being recognized.

**Solution:**
```bash
# Check .env file format
cat -A .env  # Look for hidden characters

# Ensure no spaces around = sign
# Correct: API_KEY=value
# Incorrect: API_KEY = value

# Load environment manually
export $(cat .env | xargs)

# Use python-dotenv explicitly
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

## API and Provider Problems

### Issue: "OpenAI rate limit exceeded"

**Symptoms:**
```
openai.RateLimitError: You exceeded your current quota
```

**Solution:**
```bash
# Check API usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Switch to fallback provider
export FALLBACK_LLM_PROVIDER=google_gemini
export PRIMARY_LLM_PROVIDER=google_gemini

# Reduce concurrent requests
export MAX_CONCURRENT_SECTIONS=1
export MAX_CONCURRENT_SEARCHES=2

# Use different model with lower costs
export PRIMARY_LLM_MODEL=gpt-4o-mini
```

### Issue: "Google Gemini authentication failed"

**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
```bash
# Set API key directly
export GOOGLE_API_KEY=your-api-key-here

# Or use service account (for production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Verify key works
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Issue: "Search provider returning empty results"

**Symptoms:**
- Research sections are very short
- "No relevant sources found" messages
- Empty search results

**Solution:**
```bash
# Test search provider directly
python scripts/test_search_provider.py

# Check API key for search provider
curl -X GET "https://api.tavily.com/search" \
  -H "Authorization: Bearer $TAVILY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"test query","max_results":5}'

# Switch to alternative search provider
export PRIMARY_SEARCH_PROVIDER=brave
export FALLBACK_SEARCH_PROVIDER=duckduckgo

# Adjust search parameters
export MAX_SEARCH_RESULTS=10
export SEARCH_TIMEOUT=30
```

## Translation Issues

### Issue: "Translation endpoint unreachable"

**Symptoms:**
```
Endpoint https://n8n.thinhkhuat.com/webhook/agent/translate connection error: Cannot connect to host
```

**Solution:**
```bash
# Test endpoint connectivity
curl -v https://n8n.thinhkhuat.com/webhook/agent/translate

# Check DNS resolution
nslookup n8n.thinhkhuat.com

# Test alternative endpoints
curl -v https://srv.saola-great.ts.net/webhook/agent/translate

# Bypass translation for testing
export RESEARCH_LANGUAGE=en
```

### Issue: "Translation formatting lost"

**Symptoms:**
- Translated files missing headings
- Lists and tables not formatted properly
- No markdown structure in output

**Solution:**
```bash
# Check if markdown restoration is enabled
grep "_restore_markdown_formatting" multi_agents/agents/translator.py

# Update translator to latest version
git pull origin main

# Manually test formatting restoration
python scripts/test_markdown_formatting.py

# Enable debug mode for translation
export DEBUG_TRANSLATION=true
```

### Issue: "Translation files not created"

**Symptoms:**
- Only English files generated
- Translation completes but no output files
- "Failed to create translated files" error

**Solution:**
```bash
# Check file permissions
ls -la outputs/
chmod 755 outputs/

# Check disk space
df -h

# Test file creation manually
python -c "
from multi_agents.agents.utils.file_formats import write_text_to_md
import asyncio
result = asyncio.run(write_text_to_md('test', './outputs'))
print(result)
"

# Check for file path issues
python scripts/debug_file_creation.py
```

## Performance Problems

### Issue: "Research takes too long to complete"

**Symptoms:**
- Research runs for hours without completion
- Individual sections take >30 minutes
- High CPU usage sustained

**Solution:**
```bash
# Reduce research depth
export MAX_RESEARCH_DEPTH=2
export MAX_SECTIONS=3

# Increase timeouts
export REQUEST_TIMEOUT=120
export LLM_REQUEST_TIMEOUT=90

# Use faster models
export PRIMARY_LLM_MODEL=gpt-4o-mini
export PRIMARY_LLM_MODEL=gemini-1.5-flash

# Enable parallelization
export MAX_CONCURRENT_SECTIONS=3
```

### Issue: "High memory usage"

**Symptoms:**
- System becomes unresponsive
- Out of memory errors
- Swap usage increases dramatically

**Solution:**
```bash
# Monitor memory usage
htop
ps aux --sort=-%mem | head

# Reduce batch sizes
export ASYNC_BATCH_SIZE=2
export MAX_CONCURRENT_SEARCHES=3

# Enable garbage collection
export AUTO_GARBAGE_COLLECTION=true

# Clear cache periodically
rm -rf .cache/*

# Restart service periodically
systemctl restart deep-research-mcp
```

### Issue: "Slow API responses"

**Symptoms:**
- Individual API calls take >60 seconds
- Timeout errors
- Intermittent connectivity issues

**Solution:**
```bash
# Test network speed
speedtest-cli

# Check DNS resolution speed
dig @8.8.8.8 api.openai.com

# Use different API endpoints
export OPENAI_BASE_URL=https://api.openai.com/v1

# Increase timeouts
export REQUEST_TIMEOUT=180
export CONNECTION_TIMEOUT=60

# Enable request retries
export MAX_RETRY_ATTEMPTS=5
export RETRY_BACKOFF_FACTOR=2
```

## File Generation Issues

### Issue: "PDF generation fails"

**Symptoms:**
```
PDF generation failed. Error: xelatex failed with return code 1
```

**Solution:**
```bash
# Check LaTeX installation
xelatex --version
pdflatex --version

# Install missing packages
sudo tlmgr install collection-fontsrecommended

# Use alternative PDF engine
export PDF_ENGINE=pdflatex

# Test PDF generation manually
echo "# Test\nHello world" | pandoc -o test.pdf

# Check pandoc version
pandoc --version
```

### Issue: "DOCX files corrupted"

**Symptoms:**
- Word cannot open generated files
- "File is corrupted" errors
- Empty DOCX files

**Solution:**
```bash
# Check python-docx version
pip show python-docx htmldocx

# Update dependencies
pip install --upgrade python-docx htmldocx

# Test DOCX generation manually
python -c "
from docx import Document
doc = Document()
doc.add_paragraph('Test')
doc.save('test.docx')
print('DOCX test successful')
"

# Check file permissions
ls -la *.docx
```

### Issue: "Output files not found"

**Symptoms:**
- Research completes successfully
- No output files in expected directory
- "File not found" errors

**Solution:**
```bash
# Check output directory
ls -la outputs/
ls -la outputs/run_*/

# Check permissions
chmod -R 755 outputs/

# Verify output path configuration
python -c "
import os
print('Output dir:', os.getenv('OUTPUT_DIR', './outputs'))
print('Current dir:', os.getcwd())
print('Directory exists:', os.path.exists('./outputs'))
"

# Enable file saving
export SAVE_TO_FILES=true
python main.py --save-files --research "test"
```

## Memory and Resource Issues

### Issue: "Out of memory during research"

**Symptoms:**
```
MemoryError: Unable to allocate array
Process killed (signal 9)
```

**Solution:**
```bash
# Check available memory
free -h

# Reduce memory usage
export MAX_CONCURRENT_SECTIONS=1
export CHUNK_SIZE=500
export DISABLE_CACHING=true

# Use streaming for large files
export STREAM_LARGE_FILES=true

# Clear memory periodically
python -c "import gc; gc.collect()"

# Restart with memory limits
systemd-run --scope -p MemoryMax=4G python main.py
```

### Issue: "Disk space full"

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check disk usage
df -h
du -sh outputs/

# Clean old outputs
find outputs/ -type d -mtime +7 -exec rm -rf {} +

# Clean cache
rm -rf .cache/*
rm -rf __pycache__/

# Clean temp files
find /tmp -name "*.tmp" -mtime +1 -delete

# Compress old outputs
tar -czf outputs_archive.tar.gz outputs/
rm -rf outputs/
```

## Frequently Asked Questions

### Q: Can I run multiple research tasks simultaneously?

**A:** Yes, but with limitations:
```bash
# Run multiple instances with different ports
python mcp_server.py --port 8080 &
python mcp_server.py --port 8081 &

# Use separate output directories
export OUTPUT_DIR=./outputs1
python main.py --research "Query 1" &

export OUTPUT_DIR=./outputs2  
python main.py --research "Query 2" &
```

### Q: How do I reduce API costs?

**A:** Several strategies:
```bash
# Use cheaper models
export PRIMARY_LLM_MODEL=gpt-4o-mini
export FALLBACK_LLM_MODEL=gemini-1.5-flash

# Reduce research scope
export MAX_SECTIONS=3
export MAX_SOURCES_PER_SECTION=2

# Enable caching
export ENABLE_CACHING=true
export CACHE_TTL=7200

# Use free search providers
export PRIMARY_SEARCH_PROVIDER=duckduckgo
```

### Q: Can I customize the research output format?

**A:** Yes, edit the task configuration:
```json
{
  "max_sections": 5,
  "citation_style": "apa",
  "include_executive_summary": true,
  "include_methodology": true,
  "include_limitations": true,
  "custom_guidelines": [
    "Focus on peer-reviewed sources",
    "Include statistical data",
    "Provide multiple perspectives"
  ]
}
```

### Q: How do I backup my research data?

**A:** Set up automated backups:
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz outputs/ multi_agents/config/
aws s3 cp backup_$DATE.tar.gz s3://your-backup-bucket/

# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

### Q: Can I use custom translation services?

**A:** Yes, modify the translator agent:
```python
# In multi_agents/agents/translator.py
async def _translate_chunk(self, content: str, language: str):
    # Add your custom translation service
    custom_endpoint = "https://your-translation-service.com/translate"
    payload = {
        "text": content,
        "target_language": language
    }
    # ... implementation
```

### Q: How do I monitor system performance?

**A:** Use built-in monitoring:
```bash
# Enable metrics
export ENABLE_METRICS=true
export METRICS_ENDPOINT=http://localhost:8090

# Start metrics server
python monitoring/metrics_server.py &

# View metrics
curl http://localhost:8090/metrics
```

### Q: Can I integrate with existing systems?

**A:** Yes, multiple integration options:
```python
# Direct Python integration
from multi_agents.main import run_research_task

result = await run_research_task(
    query="Your question",
    write_to_files=False  # Return data only
)

# REST API integration
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question","tone":"objective"}'

# MCP integration
# Add to Claude Desktop or other MCP clients
```

## Diagnostic Tools

### System Health Check

```bash
#!/bin/bash
# health_check.sh

echo "=== Deep Research MCP Health Check ==="

# Check Python version
python3 --version

# Check dependencies
pip check

# Check API connectivity
python -c "
import openai
import requests

# Test OpenAI
try:
    client = openai.OpenAI()
    models = client.models.list()
    print('✓ OpenAI API: Connected')
except Exception as e:
    print(f'✗ OpenAI API: {e}')

# Test Tavily
try:
    response = requests.get('https://api.tavily.com/search', timeout=10)
    print('✓ Tavily API: Reachable')
except Exception as e:
    print(f'✗ Tavily API: {e}')
"

# Check file system
echo "Disk usage:"
df -h .

echo "Output directory:"
ls -la outputs/ 2>/dev/null || echo "Output directory not found"

# Check memory
echo "Memory usage:"
free -h

echo "=== Health Check Complete ==="
```

### Performance Profiler

```python
# profiler.py
import cProfile
import pstats
import asyncio
from multi_agents.main import run_research_task

def profile_research():
    pr = cProfile.Profile()
    pr.enable()
    
    # Run research task
    result = asyncio.run(run_research_task(
        query="Test query for profiling",
        write_to_files=False
    ))
    
    pr.disable()
    
    # Save results
    pr.dump_stats('research_profile.prof')
    
    # Print top functions
    stats = pstats.Stats('research_profile.prof')
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == "__main__":
    profile_research()
```

### Configuration Validator

```python
# validate_config.py
import os
import json
import requests

def validate_environment():
    """Validate environment configuration"""
    errors = []
    
    # Check required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'TAVILY_API_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing environment variable: {var}")
    
    # Check file paths
    required_files = [
        'multi_agents/task.json',
        'multi_agents/config/'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            errors.append(f"Missing file/directory: {file_path}")
    
    # Test API connectivity
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {openai_key}'},
                timeout=10
            )
            if response.status_code != 200:
                errors.append(f"OpenAI API error: {response.status_code}")
    except Exception as e:
        errors.append(f"OpenAI API test failed: {e}")
    
    return errors

if __name__ == "__main__":
    errors = validate_environment()
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"- {error}")
    else:
        print("✓ Configuration validation passed")
```

This troubleshooting guide covers the most common issues and provides practical solutions. For additional support, check the project documentation or create an issue in the repository.