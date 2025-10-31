# AI Assistant Guide for Multi-Agent Deep Research System

## Quick Context Loading

This is a **Multi-Agent Research System** using LangGraph to orchestrate 8 specialized AI agents that conduct comprehensive research and produce reports in multiple formats and languages.

### System Architecture at a Glance
```
MCP Server (mcp_server.py)
    └── Multi-Agent Pipeline (multi_agents/)
            ├── ChiefEditorAgent (orchestrator.py) - Master coordinator
            ├── Browser Agent - Initial web research
            ├── Editor Agent - Plans report structure
            ├── Researcher Agent - Detailed research (parallel)
            ├── Writer Agent - Compiles final report
            ├── Publisher Agent - Multi-format export
            ├── Translator Agent - Language translation
            ├── Reviewer Agent - Quality assurance
            └── Reviser Agent - Final corrections
```

### Critical Dependencies
- **Python 3.13+** (specified in pyproject.toml)
- **LangGraph** for agent orchestration
- **FastMCP** for Model Context Protocol server
- **BRAVE Search API** for web research (custom integration)
- **Multi-Provider System** for LLM/Search flexibility

### Primary Entry Points
1. **MCP Server**: `python mcp_server.py`
2. **CLI Interface**: `python main.py` 
3. **Direct Research**: `cd multi_agents && python main.py`

## Anti-Hallucination Checkpoints

### ✅ ALWAYS VERIFY BEFORE CODING

1. **Import Paths**
   ```python
   # CORRECT - Actual project structure
   from multi_agents.agents.orchestrator import ChiefEditorAgent
   from multi_agents.memory.research import ResearchMemory
   from multi_agents.providers.base import BaseLLMProvider
   
   # WRONG - Common hallucinations
   from agents.orchestrator import ChiefEditorAgent  # Missing multi_agents prefix
   from multi_agents.core.agents import Agent  # No 'core' module exists
   ```

2. **Configuration Files**
   - ✅ EXISTS: `multi_agents/task.json`, `.env`, `pyproject.toml`
   - ❌ DOESN'T EXIST: `config.yaml`, `settings.json`, `multi_agents/config.json`

3. **Provider System**
   - ✅ CORRECT: Providers are in `multi_agents/providers/`
   - ✅ CORRECT: Configuration in `multi_agents/config/providers.py`
   - ❌ WRONG: No `multi_agents/llm/` or `multi_agents/search/` directories

4. **State Management**
   - ✅ CORRECT: Uses `ResearchState` TypedDict for LangGraph
   - ❌ WRONG: No custom state classes or ORM models

## Code Patterns and Templates

### Agent Implementation Pattern
```python
from typing import Dict, Any
from multi_agents.agents.base_agent import BaseAgent

class NewAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            role=kwargs.get('role', 'new_agent'),
            goal=kwargs.get('goal', 'Perform new task'),
            backstory=kwargs.get('backstory', 'Expert in new domain'),
            **kwargs
        )
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute agent task with streaming support"""
        # Implementation here
        return result
```

### Provider Integration Pattern
```python
from multi_agents.providers.base import BaseLLMProvider

class NewLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "default-model"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implementation
        pass
    
    def get_available_models(self) -> list[str]:
        return ["model-1", "model-2"]
```

### BRAVE Search Integration Pattern
```python
# CRITICAL: Must patch BEFORE importing gpt_researcher
from multi_agents.simple_brave_retriever import setup_brave_retriever
setup_brave_retriever()

# Only AFTER patching can you import gpt_researcher
from gpt_researcher import GPTResearcher
```

## Decision Matrices

### When to Create New Files vs Edit Existing

| Scenario | Decision | Rationale |
|----------|----------|-----------|
| Adding new agent | Edit `multi_agents/agents/__init__.py` + Create new file | Agents are modular |
| Modifying workflow | Edit `multi_agents/agents/orchestrator.py` | Workflow logic centralized |
| Adding provider | Create in `multi_agents/providers/` | Provider abstraction pattern |
| Changing config | Edit `.env` or `multi_agents/task.json` | No new config files |
| Adding utility | Create in `multi_agents/utils/` | Utilities are separated |

### Provider Selection Logic

```python
# Primary provider selection
if env.get('PRIMARY_LLM_PROVIDER') == 'google_gemini':
    use_google_gemini()
elif env.get('PRIMARY_LLM_PROVIDER') == 'openai':
    use_openai()

# Fallback strategy
if env.get('LLM_STRATEGY') == 'fallback_on_error':
    try:
        primary_result = await primary_provider.generate()
    except Exception:
        fallback_result = await fallback_provider.generate()
```

## Validation Checklists

### Before Modifying Agents
- [ ] Agent exists in `multi_agents/agents/`
- [ ] Agent is imported in `multi_agents/agents/__init__.py`
- [ ] Agent follows BaseAgent pattern
- [ ] Agent has execute() method
- [ ] Agent is registered in orchestrator workflow

### Before Adding Providers
- [ ] Provider inherits from `BaseLLMProvider` or `BaseSearchProvider`
- [ ] Provider implements all required methods
- [ ] Provider is registered in `multi_agents/config/providers.py`
- [ ] Environment variables are documented in `.env.example`
- [ ] Provider has error handling

### Before Modifying Workflow
- [ ] Understand current LangGraph flow in `orchestrator.py`
- [ ] Check state management in `ResearchState`
- [ ] Verify agent dependencies and order
- [ ] Test parallel execution implications
- [ ] Update task.json if adding parameters

## Common Pitfalls to Avoid

1. **Don't create configuration files** - Use existing `.env` and `task.json`
2. **Don't modify BRAVE integration order** - Must patch before GPT-researcher import
3. **Don't assume file structure** - Always verify with `ls` or `find`
4. **Don't hardcode providers** - Use environment configuration
5. **Don't skip translation workflow** - It's required for non-English output

## Quick Commands Reference

```bash
# Development setup
uv sync  # or pip install -r multi_agents/requirements.txt

# Run MCP server
python mcp_server.py

# Run CLI (saves files by default)
python main.py --research "Your query"

# Run without saving files
python main.py --research "Quick query" --no-save-files

# Check configuration
python main.py --config
python main.py --provider-info

# Run tests
python -m pytest tests/unit/
python -m pytest tests/integration/
```

## Emergency Debugging

If something breaks:
1. Check `.env` for correct API keys
2. Verify BRAVE setup with `RETRIEVER=custom`
3. Check `multi_agents/task.json` for valid configuration
4. Look for import errors in agent initialization
5. Verify LangGraph state flow in orchestrator

Remember: This is a production system. Always test changes thoroughly.