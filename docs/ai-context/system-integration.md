# TK9 System Integration - Foundational Documentation

## Purpose

This document describes the cross-component integration patterns, data flow architectures, and communication strategies that connect TK9's major subsystems into a cohesive research platform. It provides foundational knowledge for understanding how the multi-agent system, web dashboard, CLI interface, provider system, and configuration management work together.

## Integration Architecture Overview

TK9 is architected as a modular system where components communicate through well-defined interfaces while maintaining independence. The system supports three primary usage modes (CLI, Web Dashboard, MCP Server) that all leverage the same core multi-agent research engine.

### Component Interaction Map

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Server    │     │   Web Dashboard  │     │  CLI Interface  │
│  (mcp_server.py)│     │  (web_dashboard/)│     │    (cli/)       │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                         │
         └───────────────────────┴─────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Multi-Agent System    │
                    │   (multi_agents/)       │
                    │                         │
                    │  ChiefEditorAgent       │
                    │  ├─ Browser            │
                    │  ├─ Editor             │
                    │  ├─ Researcher         │
                    │  ├─ Writer             │
                    │  ├─ Publisher          │
                    │  ├─ Translator         │
                    │  ├─ Reviewer           │
                    │  └─ Reviser            │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
    ┌────▼─────┐        ┌───────▼────────┐     ┌───────▼──────┐
    │ Provider │        │  Configuration  │     │   Memory     │
    │  System  │        │   Management    │     │   System     │
    │(providers/)       │   (config/)     │     │  (memory/)   │
    └────┬─────┘        └────────────────┘     └──────────────┘
         │
    ┌────▼────────────────────────┐
    │   External Services         │
    │  ┌──────────────────────┐   │
    │  │ LLM Providers        │   │
    │  │ - Google Gemini      │   │
    │  │ - OpenAI             │   │
    │  │ - Anthropic          │   │
    │  └──────────────────────┘   │
    │  ┌──────────────────────┐   │
    │  │ Search Providers     │   │
    │  │ - BRAVE              │   │
    │  │ - Tavily             │   │
    │  └──────────────────────┘   │
    └─────────────────────────────┘
```

## Core Integration Patterns

### 1. Entry Point Abstraction

All three usage modes (CLI, Web Dashboard, MCP) provide different interfaces to the same underlying research engine.

**Pattern**: Facade pattern with unified task structure

**CLI Entry** (`main.py` + `cli/`):
```python
# Parse arguments
args = parse_arguments()

# Create task from CLI input
task = {
    "query": args.research,
    "tone": args.tone,
    "language": args.language,
    "max_sections": 5,
    "publish_formats": ["md", "pdf", "docx"]
}

# Execute via ChiefEditorAgent
orchestrator = ChiefEditorAgent(task, write_to_files=args.save_files)
result = orchestrator.run_research_task()
```

**Web Dashboard Entry** (`web_dashboard/main.py`):
```python
@app.post("/api/research")
async def submit_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())

    # Execute in background with WebSocket
    background_tasks.add_task(
        start_research_session,
        session_id,
        request.subject,
        request.language
    )

    return ResearchResponse(session_id=session_id, status="started")

async def start_research_session(session_id, subject, language):
    # Create same task structure
    task = {"query": subject, "language": language, ...}

    # Execute with WebSocket for real-time updates
    orchestrator = ChiefEditorAgent(task, websocket=websocket, write_to_files=True)
    result = orchestrator.run_research_task()
```

**MCP Server Entry** (`mcp_server.py`):
```python
@mcp.tool()
async def deep_research(query: str, tone: str = "objective", language: str = "vi"):
    """MCP tool for deep research"""

    # Create same task structure
    task = {"query": query, "tone": tone, "language": language, ...}

    # Execute without file output (return JSON)
    orchestrator = ChiefEditorAgent(task, write_to_files=False)
    result = orchestrator.run_research_task()

    return {"report": result["final_report"], "sources": result["sources"]}
```

**Key Integration Point**: All entry points construct a standardized task dictionary and delegate to `ChiefEditorAgent`.

### 2. State Management Integration

TK9 uses LangGraph for workflow orchestration with immutable state updates flowing through the agent pipeline.

**Pattern**: State machine with functional updates

**State Flow**:
```python
# Initial state (from any entry point)
initial_state = ResearchState(
    query="AI trends",
    tone="objective",
    language="vi",
    guidelines=[],
    research_plan=[],
    research_sections=[],
    draft_report="",
    final_report=""
)

# Agent updates (each agent returns partial updates)
def browser_node(state: ResearchState) -> Dict:
    sources = discover_sources(state["query"])
    return {"initial_sources": sources}

def editor_node(state: ResearchState) -> Dict:
    plan = generate_research_plan(state["query"])
    return {"research_plan": plan}

# LangGraph merges updates automatically
# new_state = {**old_state, **updates}
```

**Memory Integration** (`multi_agents/memory/`):
- `ResearchState` TypedDict defines state schema
- Draft manager persists intermediate results
- Session state enables resumable research
- State validation ensures integrity

**Cross-Reference**: [Memory System CONTEXT.md](/multi_agents/memory/CONTEXT.md)

### 3. Provider Abstraction Integration

The provider system decouples agents from specific LLM/search providers, enabling multi-provider support with automatic failover.

**Pattern**: Factory pattern with strategy-based failover

**Configuration Layer** (`multi_agents/config/`):
```python
# Environment-driven configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_SEARCH_PROVIDER=brave
LLM_STRATEGY=fallback_on_error
```

**Provider Factory** (`multi_agents/providers/factory.py`):
```python
class ProviderFactory:
    @classmethod
    def create_llm_provider(cls, config: LLMConfig):
        provider_class = cls.LLM_PROVIDERS.get(config.provider)
        return provider_class(config)
```

**Agent Integration**:
```python
# In ChiefEditorAgent.__init__()
self._setup_providers()
enhanced_config.apply_to_environment()

# Agents use providers transparently
llm = enhanced_config.get_llm_instance()
response = await llm.generate(prompt)
```

**Failover Flow**:
1. Agent requests LLM generation
2. Factory tries primary provider (Google Gemini)
3. On failure, switches to fallback (OpenAI)
4. Logs provider switch for monitoring
5. Updates provider health metrics

**Cross-Reference**: [Provider System CONTEXT.md](/multi_agents/providers/CONTEXT.md)

### 4. Real-Time Communication Integration

Web Dashboard uses WebSocket for bidirectional real-time communication between browser and research process.

**Pattern**: Publisher-subscriber with fan-out broadcasting

**Backend** (`web_dashboard/websocket_handler.py`):
```python
class WebSocketManager:
    connections: Dict[str, List[WebSocket]] = {}

    async def broadcast(self, session_id: str, message: str):
        """Broadcast to all clients monitoring this session"""
        for ws in self.connections.get(session_id, []):
            try:
                await ws.send_text(message)
            except:
                self.connections[session_id].remove(ws)
```

**Agent Integration** (`multi_agents/agents/utils/views.py`):
```python
def print_agent_output(message: str, agent: str, websocket=None):
    """Send progress update to console AND WebSocket"""
    formatted = f"[{agent}] {message}"

    # Console output
    print(formatted)

    # WebSocket broadcast
    if websocket:
        asyncio.create_task(websocket.send_text(formatted))
```

**Frontend** (`web_dashboard/static/js/dashboard.js`):
```javascript
const ws = new WebSocket(`ws://${location.host}/ws/${sessionId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendLogMessage(data.message);
    updateProgressIndicator(data.progress);
};
```

**Message Flow**:
1. Agent emits progress message
2. `print_agent_output()` forwards to WebSocket manager
3. WebSocket manager broadcasts to all connected clients
4. Browser receives and displays real-time update

**Cross-Reference**: [Web Dashboard CONTEXT.md](/web_dashboard/CONTEXT.md)

### 5. File System Integration

Research outputs are persisted to filesystem with structured draft history for debugging and transparency.

**Pattern**: Hierarchical output directory with versioned drafts

**Output Structure**:
```
outputs/
└── run_[timestamp]_[query]/
    ├── [uuid].md                    # Final report
    ├── [uuid]_vi.md                 # Translated report
    ├── [uuid].pdf                   # PDF version
    ├── [uuid].docx                  # DOCX version
    └── drafts/
        ├── WORKFLOW_SUMMARY.md      # Complete workflow log
        ├── 1_browsing/
        │   └── [timestamp]_sources.md
        ├── 2_planning/
        │   └── [timestamp]_plan.md
        ├── 3_research/
        │   ├── [timestamp]_section_1.md
        │   └── [timestamp]_section_2.md
        ├── 4_writing/
        │   └── [timestamp]_draft.md
        ├── 5_reviewing/
        │   └── [timestamp]_review.md
        └── 7_publishing/
            └── [timestamp]_final.md
```

**Draft Manager Integration** (`multi_agents/utils/draft_manager.py`):
```python
class DraftManager:
    def save_draft(self, phase: str, content: str, metadata: Dict):
        """Save draft at specific workflow phase"""
        path = self._get_draft_path(phase)
        self._write_with_metadata(path, content, metadata)
```

**Web Dashboard Integration**:
- File manager scans `outputs/` directory
- Session discovery via directory naming pattern
- File serving with proper MIME types
- Download functionality for all formats

**Cross-Reference**: [Memory System CONTEXT.md](/multi_agents/memory/CONTEXT.md)

### 6. Configuration Propagation

Configuration flows from environment variables through validation to runtime provider instances.

**Pattern**: Hierarchical configuration with validation gates

**Configuration Flow**:
```
.env file
    ↓
Environment Variables (os.getenv)
    ↓
ProviderConfigManager.load_config()
    ↓
Configuration Validation (validation.py)
    ↓ (if valid)
ProviderFactory.create_provider()
    ↓
Runtime Provider Instance
    ↓
Agent Usage
```

**Validation Gates**:
1. **Startup Validation**: Full validation before any operations
2. **Provider Validation**: API key format and availability
3. **Strategy Validation**: Ensure fallback providers exist if strategy requires
4. **Runtime Validation**: Check before each provider switch

**Cross-Reference**: [Configuration Management CONTEXT.md](/multi_agents/config/CONTEXT.md)

## Data Flow Patterns

### Research Execution Data Flow

Complete data flow through a typical research execution:

```
1. User Input (CLI/Web/MCP)
       ↓
2. Task Creation (standardized dict)
       ↓
3. ChiefEditorAgent Initialization
       ↓
4. Provider Setup (config → factory → instances)
       ↓
5. LangGraph Workflow Construction
       ↓
6. Sequential Agent Execution:
   Browser → discover sources
   Editor → generate plan
   Researcher → parallel data gathering (asyncio.gather)
   Writer → synthesize report
   Publisher → generate formats
   Translator → translate (if language != English)
   Reviewer → quality check
   Reviser → final polish
       ↓
7. Output Generation:
   - Final report (markdown/PDF/DOCX)
   - Translated version (if requested)
   - Draft history (all intermediate stages)
   - Workflow summary
       ↓
8. Response Delivery:
   - CLI: Print to console, optionally save files
   - Web: WebSocket completion message + file listing
   - MCP: Return JSON with report and sources
```

### Error Propagation Flow

How errors are handled across component boundaries:

```
Provider Failure (e.g., API timeout)
       ↓
Provider catches error, logs, raises
       ↓
ProviderFactory catches, attempts failover
       ↓ (if failover successful)
Continue with fallback provider
       ↓ (if all providers fail)
Agent catches, adds to state["errors"]
       ↓
Orchestrator checks state["errors"]
       ↓ (if critical)
Graceful degradation or abort
       ↓
User notification via respective interface
```

**Error Resilience Patterns**:
- **Try-catch at agent level**: Each agent wraps logic in error handling
- **State error propagation**: Errors added to state for downstream agents
- **Provider failover**: Automatic switch to backup providers
- **Graceful degradation**: Continue with partial results when possible
- **User-friendly messages**: Technical errors translated to actionable feedback

## Communication Protocols

### Agent-to-Agent Communication

**Protocol**: State-based message passing via LangGraph

Agents communicate by reading from and writing to shared `ResearchState`:

```python
# Agent 1 (Editor) produces research plan
def editor_node(state: ResearchState) -> Dict:
    plan = generate_plan(state["query"])
    return {"research_plan": plan}

# Agent 2 (Researcher) consumes research plan
def researcher_node(state: ResearchState) -> Dict:
    plan = state["research_plan"]  # Read from previous agent
    results = execute_research(plan)
    return {"research_sections": results}
```

**No direct agent-to-agent calls**. All communication flows through state.

### Dashboard-to-Backend Communication

**Protocol**: REST API + WebSocket

**REST Endpoints** (request-response):
- `POST /api/research` - Submit new research query
- `GET /api/session/{id}` - Get session status
- `GET /api/sessions` - List all sessions
- `GET /download/{session}/{file}` - Download research output

**WebSocket** (bidirectional streaming):
- `WS /ws/{session_id}` - Real-time progress updates
- Client → Server: Subscribe to session
- Server → Client: Stream log messages, progress updates, completion notifications

### MCP-to-Multi-Agent Communication

**Protocol**: Direct Python function calls

MCP server runs in same process as multi-agent system:

```python
# MCP tool directly instantiates and calls multi-agent system
@mcp.tool()
async def deep_research(query: str, ...):
    task = {...}
    orchestrator = ChiefEditorAgent(task)
    result = orchestrator.run_research_task()
    return result
```

**No network boundary** between MCP server and multi-agent system.

## Integration Testing Patterns

### Cross-Component Test Strategy

**Unit Tests**: Test components in isolation
- Mock external dependencies (providers, filesystem)
- Test component logic independently

**Integration Tests**: Test component boundaries
- Test CLI → Multi-Agent integration
- Test Web Dashboard → Multi-Agent integration
- Test Provider System → External API integration

**End-to-End Tests**: Test complete workflows
- Full research execution through CLI
- Full research execution through Web Dashboard
- Verify file outputs, state consistency, error handling

**Example Integration Test**:
```python
async def test_cli_to_multiagent_integration():
    """Test CLI successfully invokes multi-agent system"""
    # Arrange: Create task via CLI-like structure
    task = create_task_from_cli_args(query="test", tone="objective")

    # Act: Execute via orchestrator
    orchestrator = ChiefEditorAgent(task, write_to_files=False)
    result = orchestrator.run_research_task()

    # Assert: Verify expected outputs
    assert result["final_report"] is not None
    assert len(result["research_sections"]) > 0
    assert "errors" not in result or len(result["errors"]) == 0
```

**Cross-Reference**: [Testing Framework CONTEXT.md](/tests/CONTEXT.md)

## Performance Considerations

### Integration Bottlenecks

**Identified Bottlenecks**:
1. **Provider API latency**: 500ms-2000ms per LLM call
2. **Sequential agent execution**: No parallelism between agents
3. **File I/O**: Draft saves can accumulate
4. **WebSocket broadcasting**: Overhead for many concurrent clients

**Optimization Strategies**:
1. **Parallel research sections**: Researcher agent uses `asyncio.gather()`
2. **Async provider calls**: All provider methods are async
3. **Buffered WebSocket messages**: Batch updates to reduce overhead
4. **Selective draft saving**: Only save at key workflow stages

### Scalability Patterns

**Horizontal Scaling** (future consideration):
- Web Dashboard: Scale via load balancer
- Multi-Agent System: Queue-based distribution
- Provider System: Connection pooling

**Vertical Scaling** (current approach):
- Increase resources for single-instance deployment
- Optimize memory usage (streaming, cleanup)
- Cache provider responses where appropriate

## Common Integration Issues

### Issue: WebSocket Connection Failures
**Symptom**: Dashboard shows "connection failed" errors
**Root Cause**: Often proxy configuration (Caddy not forwarding WebSocket upgrade)
**Solution**: Direct connection to dashboard port or fix proxy WebSocket config

### Issue: Provider Failover Not Triggering
**Symptom**: Research fails instead of switching to fallback provider
**Root Cause**: Failover strategy set to `primary_only` or fallback provider not configured
**Solution**: Set `LLM_STRATEGY=fallback_on_error` and configure `FALLBACK_LLM_PROVIDER`

### Issue: State Inconsistency Between Agents
**Symptom**: Agent receives unexpected state structure
**Root Cause**: Previous agent didn't return expected fields
**Solution**: Use type-safe state accessors from `agents/utils/type_safety.py`

### Issue: File Output Not Generated
**Symptom**: Research completes but no files in `outputs/`
**Root Cause**: `write_to_files=False` in orchestrator initialization
**Solution**: CLI requires `--save-files` flag, Web Dashboard always saves, MCP never saves

## Cross-References

### Related Tier 2 Component Documentation
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Core research orchestration
- **[Web Dashboard](/web_dashboard/CONTEXT.md)** - Web interface and WebSocket integration
- **[Provider System](/multi_agents/providers/CONTEXT.md)** - Provider abstraction and failover
- **[CLI Interface](/cli/CONTEXT.md)** - Command-line interface patterns
- **[Configuration Management](/multi_agents/config/CONTEXT.md)** - Configuration propagation

### Related Tier 3 Feature Documentation
- **[Agent Implementations](/multi_agents/agents/CONTEXT.md)** - Individual agent integration points
- **[Memory System](/multi_agents/memory/CONTEXT.md)** - State management and persistence
- **[Custom Retrievers](/multi_agents/retrievers/CONTEXT.md)** - Search provider integration

### Related Tier 1 Documentation
- **[Project Structure](/docs/ai-context/project-structure.md)** - Complete file organization
- **[Documentation Overview](/docs/ai-context/docs-overview.md)** - Documentation system navigation

### Key Integration Files
- `main.py:1-150` - CLI entry point
- `mcp_server.py:1-200` - MCP server entry point
- `web_dashboard/main.py:1-290` - Web Dashboard entry point
- `multi_agents/agents/orchestrator.py:60-350` - Core integration orchestrator
- `multi_agents/providers/factory.py:1-420` - Provider abstraction layer
- `multi_agents/memory/research.py` - Shared state schema

---

*This foundational document provides system-wide integration knowledge for TK9. For component-specific integration details, see individual Tier 2 CONTEXT.md files. Last updated: 2025-10-31*
