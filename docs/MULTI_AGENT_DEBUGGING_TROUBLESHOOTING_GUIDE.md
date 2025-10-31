# Debugging & Troubleshooting Guide

## Quick Diagnostic Commands

### System Health Check
```bash
# Check environment configuration
python main.py --config

# Check provider status
python main.py --provider-info

# Test basic functionality
python main.py --research "test query" --no-save-files

# Check dependencies
python -c "import multi_agents; print('✅ Multi-agents module loaded')"
python -c "import langgraph; print('✅ LangGraph available')"
python -c "import gpt_researcher; print('✅ GPT-researcher available')"
```

### Environment Validation
```bash
# Check Python version (requires 3.13+)
python --version

# Check virtual environment
which python
echo $VIRTUAL_ENV

# Check environment variables
env | grep -E "(API_KEY|PROVIDER|RETRIEVER)"

# Check file permissions
ls -la multi_agents/
ls -la .env
```

## Common Issues and Solutions

### 1. BRAVE Search Integration Issues

#### Problem: BRAVE API not working
```
Error: BRAVE search failed: 401
Error: No search results found
```

**Diagnosis:**
```bash
# Check BRAVE configuration
echo "BRAVE_API_KEY: $BRAVE_API_KEY"
echo "RETRIEVER: $RETRIEVER"
echo "PRIMARY_SEARCH_PROVIDER: $PRIMARY_SEARCH_PROVIDER"

# Test BRAVE API directly
curl -H "Accept: application/json" \
     -H "X-Subscription-Token: $BRAVE_API_KEY" \
     "https://api.search.brave.com/res/v1/web/search?q=test&count=1"
```

**Solutions:**
1. **Invalid API Key**: Get new key from [BRAVE Search API](https://api.search.brave.com/)
2. **Wrong Environment Setup**:
   ```bash
   # Required settings
   RETRIEVER=custom
   RETRIEVER_ENDPOINT=https://brave-local-provider.local
   PRIMARY_SEARCH_PROVIDER=brave
   BRAVE_API_KEY=your_actual_key
   ```
3. **Import Order Issue**: Ensure BRAVE setup runs before GPT-researcher import
   ```python
   # CORRECT order in orchestrator.py
   from multi_agents.simple_brave_retriever import setup_brave_retriever
   setup_brave_retriever()  # MUST be first
   
   # Only after setup
   from gpt_researcher import GPTResearcher
   ```

### 2. LLM Provider Issues

#### Problem: Google Gemini API failures
```
Error: Gemini generation failed: 403
Error: Model not found: gemini-2.5-flash-preview-04-17-thinking
```

**Diagnosis:**
```python
# Test Google API
import google.generativeai as genai
genai.configure(api_key="your_key")
models = list(genai.list_models())
print([m.name for m in models])
```

**Solutions:**
1. **API Key Issues**: 
   - Verify key at [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Check quota and billing
2. **Model Availability**:
   ```python
   # Check available models
   from multi_agents.providers.llm.google_provider import GoogleGeminiProvider
   provider = GoogleGeminiProvider("your_key")
   print(provider.get_available_models())
   ```
3. **Safety Settings**: Some content may be blocked by safety filters
   ```python
   # In google_provider.py, adjust safety settings
   self.safety_settings = [
       {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
       # ... other categories
   ]
   ```

### 3. Agent Workflow Issues

#### Problem: Agents not executing in order
```
Error: 'editor_output' key not found in state
Error: Agent X failed to receive input from Agent Y
```

**Diagnosis:**
```python
# Check workflow structure in orchestrator.py
def debug_workflow_state(state):
    print("Current state keys:", list(state.keys()))
    print("State values:", {k: v[:100] if isinstance(v, str) else v for k, v in state.items()})
    return state

# Add to workflow nodes for debugging
workflow.add_node("debug", debug_workflow_state)
```

**Solutions:**
1. **Missing State Keys**: Ensure each agent returns proper state updates
   ```python
   # In agent node functions
   async def agent_node(state):
       result = await agent.execute(task, context)
       return {"agent_output": result}  # Must return dict with state updates
   ```
2. **Wrong Edge Connections**: Check workflow edges in orchestrator
   ```python
   # Verify edge order
   workflow.add_edge("browser", "editor")
   workflow.add_edge("editor", "researcher") 
   # etc.
   ```

### 4. File Output Issues

#### Problem: Files not being saved
```
Error: Permission denied: ./outputs/
Error: No such file or directory
```

**Diagnosis:**
```bash
# Check output directory
ls -la outputs/
mkdir -p outputs/  # Create if missing

# Check permissions
ls -ld outputs/
chmod 755 outputs/  # Fix permissions

# Check disk space
df -h .
```

**Solutions:**
1. **Create Output Directory**:
   ```python
   import os
   os.makedirs("outputs", exist_ok=True)
   ```
2. **File Writing Settings**:
   ```python
   # For CLI mode (saves by default)
   result = await run_research_task(query, write_to_files=True)
   
   # For MCP mode (no save by default)
   result = await run_research_task(query, write_to_files=False)
   ```

### 5. Translation Issues

#### Problem: Translation failing or corrupting format
```
Error: Translation endpoint not responding
Warning: Markdown formatting lost in translation
```

**Diagnosis:**
```python
# Test translation endpoint
from multi_agents.agents.translator import TranslatorAgent
translator = TranslatorAgent()

# Check if endpoints are reachable
import aiohttp
async def test_endpoint():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://translation-endpoint.com/health") as resp:
            print(f"Status: {resp.status}")
```

**Solutions:**
1. **Endpoint Configuration**: Verify translation service URLs
2. **Format Preservation**: Ensure translation preserves markdown
   ```python
   # In translator.py - markdown should be preserved by endpoint
   # DO NOT apply removeMarkdown() to translation results
   translated_content = await self._translate_content(content)
   # Return as-is, don't strip formatting
   return translated_content
   ```

### 6. Memory and Performance Issues

#### Problem: High memory usage or slow performance
```
Error: Out of memory
Warning: Request timeout after 30s
```

**Diagnosis:**
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Check async task count
import asyncio
tasks = asyncio.all_tasks()
print(f"Active tasks: {len(tasks)}")
```

**Solutions:**
1. **Parallel Execution Limits**: Reduce concurrent researchers
   ```python
   # In orchestrator.py
   MAX_PARALLEL_RESEARCHERS = 3  # Reduce from default
   ```
2. **Timeout Settings**: Increase timeouts for slow operations
   ```python
   # In provider configs
   timeout = 60  # Increase from 30s default
   ```
3. **Cleanup Resources**: Ensure proper async context management
   ```python
   async with aiohttp.ClientSession() as session:
       # Use session here
       pass  # Session automatically closed
   ```

## Debug Configuration

### Enable Verbose Logging
```python
# In multi_agents/main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# For agents
agent = SomeAgent(verbose=True)

# For providers
provider = SomeProvider(debug=True)
```

### Add Debug Checkpoints
```python
# In agent execute methods
async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
    print(f"🔍 {self.role} executing: {task[:100]}...")
    print(f"📝 Context keys: {list(context.keys()) if context else 'None'}")
    
    try:
        result = await self._process_task(task, context)
        print(f"✅ {self.role} completed: {len(result)} chars")
        return result
    except Exception as e:
        print(f"❌ {self.role} failed: {str(e)}")
        raise
```

### State Monitoring
```python
# Add to workflow nodes
async def monitor_state(state):
    print("\n" + "="*50)
    print("WORKFLOW STATE MONITOR")
    print("="*50)
    for key, value in state.items():
        if isinstance(value, str):
            print(f"{key}: {len(value)} chars")
        else:
            print(f"{key}: {type(value)} - {value}")
    print("="*50 + "\n")
    return state

# Add monitoring nodes
workflow.add_node("monitor_1", monitor_state)
workflow.add_edge("browser", "monitor_1")
workflow.add_edge("monitor_1", "editor")
```

## Performance Profiling

### Timing Analysis
```python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"⏱️ {func.__name__}: {end - start:.2f}s")
        return result
    return wrapper

# Apply to agent methods
@timer
async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
    # Agent logic here
    pass
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
    pass
```

## Emergency Recovery

### Reset System State
```bash
# Stop all processes
pkill -f "python.*multi_agents"

# Clear temporary files
rm -rf /tmp/multi_agents_*
rm -rf outputs/run_*

# Reset environment
source .env
export PYTHONPATH=$PWD
```

### Minimal Test Mode
```python
# Create minimal test script
# File: debug_minimal.py
import asyncio
from multi_agents.agents.browser import BrowserAgent

async def test_minimal():
    try:
        agent = BrowserAgent(verbose=True)
        result = await agent.execute("test search", {})
        print(f"✅ Success: {len(result)} chars")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_minimal())
```

### Provider Isolation Test
```python
# Test each provider individually
# File: debug_providers.py
import asyncio
import os
from multi_agents.providers import ProviderFactory

async def test_provider(provider_name: str, api_key_env: str):
    try:
        api_key = os.getenv(api_key_env)
        if not api_key:
            print(f"❌ {provider_name}: No API key ({api_key_env})")
            return
        
        if provider_name in ['google_gemini', 'openai', 'anthropic']:
            provider = ProviderFactory.create_llm_provider(
                provider_name, api_key, "default-model"
            )
            result = await provider.generate("Hello")
            print(f"✅ {provider_name}: {len(result)} chars")
        else:
            provider = ProviderFactory.create_search_provider(
                provider_name, api_key
            )
            results = await provider.search("test")
            print(f"✅ {provider_name}: {len(results)} results")
    except Exception as e:
        print(f"❌ {provider_name}: {e}")

async def test_all_providers():
    tests = [
        ('google_gemini', 'GOOGLE_API_KEY'),
        ('openai', 'OPENAI_API_KEY'),
        ('brave', 'BRAVE_API_KEY'),
        ('tavily', 'TAVILY_API_KEY'),
    ]
    
    for provider_name, api_key_env in tests:
        await test_provider(provider_name, api_key_env)

if __name__ == "__main__":
    asyncio.run(test_all_providers())
```

## Log Analysis

### Common Error Patterns
```bash
# Search for common errors in logs
grep -i "error\|failed\|exception" logs/debug.log

# Check API rate limits
grep -i "rate limit\|quota\|throttle" logs/debug.log

# Find memory issues
grep -i "memory\|out of\|killed" logs/debug.log

# Check timeout issues
grep -i "timeout\|timed out" logs/debug.log
```

### Log File Locations
```bash
# Application logs
./logs/multi_agents.log
./logs/debug.log

# System logs (macOS)
/var/log/system.log

# Check disk space for logs
du -h logs/
```

## Contact Points for Issues

### Configuration Issues
1. Check `.env` file against `.env.example`
2. Verify `multi_agents/task.json` structure
3. Validate `pyproject.toml` dependencies

### Agent Issues
1. Test agents individually
2. Check state flow in orchestrator
3. Verify LangGraph workflow structure

### Provider Issues
1. Test API keys with curl/direct calls
2. Check provider registration in config
3. Validate model availability

### Performance Issues
1. Monitor system resources
2. Reduce parallel execution
3. Increase timeout values

Remember: Always test with minimal examples first, then build up complexity.