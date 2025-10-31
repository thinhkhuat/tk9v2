# Multi-Agent Research System - Component Context

## Purpose

The multi-agent research system is the core component of TK9 that orchestrates 8 specialized AI agents to conduct comprehensive research. Using LangGraph for workflow management, it coordinates agents in a sequential pipeline with parallel research sections, producing professional reports in multiple formats and languages.

## Current Status: Production Ready

**Last Updated**: 2025-10-31
**Status**: ✅ Stable - 89% test pass rate, all critical paths operational
**Python Version**: 3.12/3.13 required

## Component-Specific Development Guidelines

### Code Organization Principles
- **Agent Independence**: Each agent is self-contained with clear responsibilities
- **Type Safety**: All agents use Pydantic models and type hints
- **Error Resilience**: Comprehensive try-catch blocks with graceful degradation
- **State Management**: Immutable state updates through LangGraph
- **Provider Abstraction**: No direct API calls - use provider interfaces

### Agent Development Pattern
```python
class NewAgent:
    """Agent responsible for [specific task]"""

    def __init__(self, task: Dict[str, Any], websocket=None, ...):
        self.task = task
        self.websocket = websocket
        self._validate_inputs()

    def _validate_inputs(self):
        """Validate all required task parameters"""
        pass

    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """Main agent execution logic"""
        try:
            # Agent logic here
            return {"agent_name": result}
        except Exception as e:
            return {"error": str(e)}
```

### State Management Pattern
- Use `ResearchState` TypedDict for all state
- Never mutate state directly - return updates
- Include error information in state for downstream agents
- Preserve intermediate results for debugging

### WebSocket Communication
- All agents support optional WebSocket for real-time updates
- Use `print_agent_output()` for consistent messaging
- Include phase information in messages
- Send progress updates for long-running operations

## Major Subsystem Organization

### 1. Agent Orchestration (`agents/orchestrator.py`)
**ChiefEditorAgent** - The master coordinator (350+ lines)

**Key Responsibilities**:
- Initializes all agents and workflow
- Manages LangGraph state machine
- Coordinates 8-agent sequential pipeline
- Handles provider configuration
- Manages output directory and file writing

**Critical Methods**:
- `_setup_providers()` - Multi-provider configuration and validation
- `_setup_language()` - Language configuration for research and translation
- `run_research_task()` - Main workflow execution
- `_build_workflow()` - LangGraph workflow construction

**Workflow Stages**:
```
browser → editor → planner → researcher (parallel) →
writer → publisher → translator → reviewer → reviser → end
```

### 2. Research Planning (`agents/editor.py`)
**EditorAgent** - Research planner and query analyzer (300+ lines)

**Responsibilities**:
- Analyzes research query intent
- Generates research plan with sections
- Determines optimal research approach
- Sets quality guidelines for downstream agents

**Key Outputs**:
- Section list with search queries
- Research methodology
- Quality criteria

### 3. Parallel Research Execution (`agents/researcher.py`)
**ResearchAgent** - Data gathering and source collection (150+ lines)

**Responsibilities**:
- Executes search queries via configured provider
- Processes web search results
- Extracts relevant information
- Runs in parallel for multiple sections

**Integration**:
- Uses `gpt_researcher` library
- Supports BRAVE, Tavily, Google, DuckDuckGo search
- Automatic retry and fallback logic

### 4. Content Synthesis (`agents/writer.py`)
**WriterAgent** - Report composition and synthesis (450+ lines)

**Responsibilities**:
- Synthesizes research from all sections
- Generates structured markdown reports
- Includes citations and references
- Applies tone guidelines (objective/critical/optimistic)

**Output Format**:
- Markdown with proper headers
- Citation footnotes
- Table of contents
- Executive summary

### 5. Multi-Format Publishing (`agents/publisher.py`)
**PublisherAgent** - Document format generation (150+ lines)

**Responsibilities**:
- Converts markdown to PDF/DOCX
- Applies professional formatting
- Manages file output
- Draft version tracking

**Supported Formats**:
- PDF (via Pandoc + LaTeX)
- DOCX (via python-docx)
- Markdown (native)

### 6. Translation Pipeline (`agents/translator.py`)
**TranslatorAgent** - Multi-language translation (850+ lines)

**Responsibilities**:
- Translates final report to target language
- Preserves markdown formatting
- Maintains citations and structure
- Supports 50+ languages

**Translation Approach**:
- Section-by-section translation
- Format preservation logic
- Automatic language detection
- Failover translation endpoints

### 7. Quality Assurance (`agents/reviewer.py`)
**ReviewerAgent** - Content review and validation (600+ lines)

**Responsibilities**:
- Reviews report for quality issues
- Validates citations and sources
- Checks factual accuracy
- Identifies improvement areas

**Review Criteria**:
- Factual accuracy
- Citation completeness
- Logical flow
- Tone consistency

### 8. Content Refinement (`agents/reviser.py`)
**ReviserAgent** - Report improvement (700+ lines)

**Responsibilities**:
- Implements reviewer suggestions
- Refines content and structure
- Improves clarity and flow
- Final quality polish

### 9. Human Feedback Integration (`agents/human.py`)
**HumanAgent** - Human-in-the-loop feedback (100+ lines)

**Responsibilities**:
- Accepts human feedback at review stage
- Optional manual intervention point
- Feedback incorporation into revision

**Usage**: Optional - can be bypassed for automated workflows

## Architectural Patterns

### 1. LangGraph State Machine
**Pattern**: Sequential workflow with conditional branching

```python
workflow = StateGraph(ResearchState)
workflow.add_node("browser", browser_agent)
workflow.add_node("editor", editor_agent)
workflow.add_node("researcher", researcher_agent)
# ... more nodes

workflow.add_conditional_edges(
    "reviewer",
    lambda state: "human" if human_feedback else "reviser",
    {"human": "human", "reviser": "reviser"}
)
```

**State Transitions**: Each agent returns dict updates merged into state

### 2. Provider Abstraction
**Pattern**: Factory pattern with automatic failover

```python
from multi_agents.providers.factory import enhanced_config

# Configuration setup
enhanced_config.apply_to_environment()
current_providers = enhanced_config.get_current_providers()

# Usage in agents
llm = enhanced_config.get_llm_instance()  # Auto-selects provider
```

**Providers**: OpenAI, Google Gemini, Anthropic, Azure OpenAI
**Search**: BRAVE (primary), Tavily (fallback), Google, DuckDuckGo

### 3. Draft Management
**Pattern**: Versioned draft system with incremental saves

```python
draft_manager = DraftManager(output_dir, task_id)

# Save draft at each stage
draft_manager.save_draft(
    phase="3_research",
    content=research_content,
    metadata={"agent": "researcher"}
)
```

**Structure**: `drafts/[phase]_[agent]/[timestamp]_[type].md`

### 4. Error Handling
**Pattern**: Try-catch with state error propagation

```python
async def run(self, state: ResearchState) -> Dict[str, Any]:
    try:
        result = await self._process()
        return {"agent_output": result}
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return {"error": str(e), "agent_output": None}
```

**Recovery**: Downstream agents check for errors in state

### 5. WebSocket Progress Updates
**Pattern**: Real-time status broadcasting

```python
from multi_agents.agents.utils.views import print_agent_output

print_agent_output(
    f"Processing section {i+1}/{total}",
    agent="RESEARCHER",
    websocket=self.websocket
)
```

**Message Format**: `[AGENT] message` → WebSocket → Dashboard

### 6. Type Safety
**Pattern**: Pydantic models and utility functions

```python
from multi_agents.agents.utils.type_safety import (
    ensure_dict, safe_dict_get, safe_list_operation
)

# Safe dictionary access
query = safe_dict_get(state, 'query', 'default_query', str)

# Safe type conversion
data = ensure_dict(possibly_none_data)
```

**Utilities**: Type guards, safe operations, validation helpers

### 7. Network Reliability
**Pattern**: Early patching and retry logic

```python
# Applied in main.py before agent imports
from direct_timeout_patch import apply_direct_timeout_patches
from network_reliability_patch import setup_global_session_defaults

apply_direct_timeout_patches()  # 4s → 30s timeout
setup_global_session_defaults()  # Retry with exponential backoff
```

**SSL Handling**: Special logic for Vietnamese .gov.vn domains

### 8. Fact-Checking Integration
**Pattern**: Optional validation layer in research

```python
from multi_agents.agents.utils.fact_checker import validate_research_results

if fact_checking_enabled:
    validated_results = await validate_research_results(
        research_content,
        sources
    )
```

**Capabilities**: Source verification, claim validation, confidence scoring

## Integration Points

### Upstream Dependencies
- **MCP Server** (`/mcp_server.py`) - Exposes `deep_research` tool via FastMCP
- **CLI** (`/cli/`) - Interactive and single-query research execution
- **Web Dashboard** (`/web_dashboard/`) - Real-time monitoring and file management
- **Main Entry** (`/main.py`) - Direct Python API and CLI entry point

### Downstream Dependencies
- **Provider System** (`multi_agents/providers/`) - LLM and search provider abstraction
- **Memory System** (`multi_agents/memory/`) - Research state and draft management
- **Configuration** (`multi_agents/config/`) - Multi-provider and language settings
- **Utilities** (`multi_agents/utils/`) - Logging, validation, draft management

### External Services
- **LLM Providers**: OpenAI, Google Gemini, Anthropic, Azure OpenAI
- **Search Providers**: BRAVE, Tavily, Google, DuckDuckGo, SerpAPI
- **Translation Endpoints**: Configurable translation service APIs
- **Document Converters**: Pandoc (PDF/DOCX), LaTeX (high-quality PDFs)

### File System
- **Output Directory**: `./outputs/run_[timestamp]_[query]/`
  - Final reports: `[uuid].md`, `[uuid]_vi.md`
  - Draft history: `drafts/[phase]_[agent]/`
  - Workflow summary: `drafts/WORKFLOW_SUMMARY.md`

- **Task Configuration**: `multi_agents/task.json`
  - Query, guidelines, tone, language
  - Max sections, publish formats

### Environment Variables
```bash
# LLM Configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
LLM_STRATEGY=primary_only

# Search Configuration
PRIMARY_SEARCH_PROVIDER=brave
SEARCH_STRATEGY=primary_only
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# Language Configuration
RESEARCH_LANGUAGE=vi  # Target translation language

# API Keys
GOOGLE_API_KEY=your_key
BRAVE_API_KEY=your_key
OPENAI_API_KEY=your_key (optional)
TAVILY_API_KEY=your_key (optional)
```

## Development Patterns

### Adding a New Agent
1. **Create Agent File**: `multi_agents/agents/new_agent.py`
2. **Implement Agent Class**:
   ```python
   class NewAgent:
       def __init__(self, task, websocket=None):
           self.task = task
           self.websocket = websocket

       async def run(self, state: ResearchState) -> Dict[str, Any]:
           # Implementation
           return {"new_agent_output": result}
   ```

3. **Update Orchestrator**: Add to workflow in `orchestrator.py`
   ```python
   from . import NewAgent

   # In _build_workflow()
   workflow.add_node("new_agent", new_agent_node)
   workflow.add_edge("previous_agent", "new_agent")
   ```

4. **Update State**: Add to `ResearchState` if new state fields needed
5. **Add Tests**: Unit tests in `tests/unit/test_agents.py`
6. **Update Docs**: Document in `ref/agents.md`

### Modifying Agent Behavior
1. **Read Agent Code**: Understand current implementation
2. **Check State Dependencies**: Review what state agent reads/writes
3. **Update Logic**: Modify agent's `run()` method
4. **Test Isolation**: Test agent in isolation first
5. **Integration Test**: Test full workflow with change
6. **Update Draft Manager**: If output format changes

### Testing Approach
```python
# Unit test individual agent
async def test_editor_agent():
    agent = EditorAgent(task={"query": "test"})
    state = {"query": "test query"}
    result = await agent.run(state)
    assert "research_plan" in result

# Integration test workflow
def test_research_workflow():
    orchestrator = ChiefEditorAgent(task=test_task)
    result = orchestrator.run_research_task()
    assert result["final_report"] is not None
```

### Debugging Workflow Issues
1. **Check Draft Files**: Review `drafts/` for each agent's output
2. **Enable Verbose Logging**: Set `LOG_LEVEL=DEBUG`
3. **WebSocket Messages**: Watch real-time agent progress
4. **State Inspection**: Add logging in `orchestrator.py` between nodes
5. **Provider Logs**: Check provider failover messages

## Performance Considerations

### Parallel Research Optimization
- **ResearchAgent** runs multiple instances for sections
- Use `asyncio.gather()` for concurrent execution
- Balance parallelism with API rate limits

### Memory Management
- Large reports held in memory during processing
- Draft manager writes incrementally to disk
- State kept minimal - only essential data

### Provider Selection
- **Google Gemini**: Fastest, lowest latency (recommended primary)
- **OpenAI GPT-4**: Highest quality, slower
- **Anthropic Claude**: Balanced quality/speed
- **BRAVE Search**: Fast, comprehensive web search (recommended)

### Caching Strategy
- No built-in caching (each research is fresh)
- Provider-level caching may apply
- Draft files serve as execution history

## Common Issues and Solutions

### Issue: Network Timeouts
**Solution**: Applied automatically via `network_reliability_patch.py`
- Increased timeout from 4s to 30s
- Exponential backoff retry logic
- Special SSL handling for problematic domains

### Issue: Provider Failures
**Solution**: Automatic failover via provider system
- Primary provider fails → fallback provider activated
- Strategy configurable: `primary_only`, `fallback_on_error`
- Logs provider switches for monitoring

### Issue: Translation Errors
**Solution**: Multiple failover endpoints
- Primary translation endpoint fails → secondary/tertiary
- Format preservation logic repairs common issues
- Manual review step catches quality problems

### Issue: WebSocket Disconnections
**Solution**: Graceful degradation
- Research continues without WebSocket
- Progress logged to console/files
- Dashboard reconnects automatically

### Issue: Missing API Keys
**Solution**: Configuration validation
- Startup validation checks all required keys
- Detailed error messages with fix suggestions
- Graceful degradation where possible

## Cross-References

### Related Documentation
- **[Agent Details](/ref/agents.md)** - Comprehensive agent documentation
- **[Workflow Architecture](/ref/workflow.md)** - Complete workflow diagrams and state transitions
- **[Provider System](/multi_agents/providers/CONTEXT.md)** - Provider abstraction and configuration
- **[Memory System](/multi_agents/memory/CONTEXT.md)** - State management and draft tracking
- **[Configuration](/multi_agents/config/CONTEXT.md)** - Multi-provider and language configuration

### Key Files
- `multi_agents/main.py:1-100` - Initialization and patch application
- `multi_agents/agents/orchestrator.py:60-150` - ChiefEditorAgent setup and workflow
- `multi_agents/agents/orchestrator.py:200-350` - Workflow construction and execution
- `multi_agents/memory/research.py` - ResearchState TypedDict definition
- `multi_agents/utils/draft_manager.py` - Draft versioning system

---

*This component context provides architectural guidance for the multi-agent research system. For implementation details, see individual agent files and Tier 3 feature documentation.*
