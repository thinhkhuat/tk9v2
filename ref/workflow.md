# Workflow Reference Documentation

## Overview

The Deep Research MCP system implements a sophisticated multi-stage workflow using LangGraph for orchestration. The workflow coordinates 8 specialized agents through a state-driven pipeline to produce comprehensive research reports.

## Workflow Architecture

### Core Technologies
- **LangGraph**: State machine and workflow orchestration
- **AsyncIO**: Concurrent task execution
- **State Management**: Typed state dictionaries
- **Stream Processing**: Real-time progress updates

### Workflow Components
```
┌─────────────┐
│   Trigger   │ (User Query)
└──────┬──────┘
       ↓
┌─────────────┐
│   Browser   │ (Initial Research)
└──────┬──────┘
       ↓
┌─────────────┐
│   Editor    │ (Structure Planning)
└──────┬──────┘
       ↓
┌─────────────┐
│ Researcher  │ (Parallel Deep Research)
└──────┬──────┘
       ↓
┌─────────────┐
│   Writer    │ (Report Compilation)
└──────┬──────┘
       ↓
┌─────────────┐
│  Publisher  │ (Multi-format Export)
└──────┬──────┘
       ↓
┌─────────────┐
│ Translator  │ (Language Translation)
└──────┬──────┘
       ↓
┌─────────────┐
│  Reviewer   │ (Quality Assurance)
└──────┬──────┘
       ↓
┌─────────────┐
│   Reviser   │ (Final Corrections)
└──────┬──────┘
       ↓
┌─────────────┐
│   Output    │ (Final Report)
└─────────────┘
```

## State Management

### ResearchState Structure
```python
class ResearchState(TypedDict):
    # Core Fields
    query: str                    # Research question
    tone: str                     # Research tone (objective, critical, etc.)
    language: str                 # Target language for translation
    
    # Research Data
    browser_results: List[Dict]   # Initial search results
    outline: Dict                 # Report structure from Editor
    research_data: List[Dict]     # Detailed research per section
    
    # Draft Management
    draft: str                    # Current draft version
    revision_history: List[str]   # Previous draft versions
    
    # Review & Feedback
    review_feedback: Dict         # Reviewer agent feedback
    human_feedback: Optional[str] # Human-in-the-loop input
    
    # Output
    final_report: str            # Final markdown report
    published_formats: Dict      # PDF, DOCX, MD file paths
    translated_report: str       # Translated version
    
    # Workflow Control
    current_stage: str           # Current workflow stage
    error_state: Optional[Dict]  # Error information if any
    metadata: Dict              # Additional metadata
```

## Workflow Stages

### Stage 1: Initialization
**Trigger**: User submits research query

**Process**:
1. Parse user input and configuration
2. Initialize ResearchState
3. Validate provider availability
4. Set workflow parameters

**Output**: Initialized state with query and configuration

### Stage 2: Browser Research
**Agent**: BrowserAgent  
**Duration**: 10-30 seconds

**Process**:
1. Perform web searches using configured provider
2. Collect relevant URLs and snippets
3. Filter and rank results by relevance
4. Extract key information

**State Updates**:
```python
state.browser_results = [
    {
        "url": "https://example.com",
        "title": "Article Title",
        "snippet": "Brief description...",
        "relevance_score": 0.95
    }
]
```

### Stage 3: Structure Planning
**Agent**: EditorAgent  
**Duration**: 5-15 seconds

**Process**:
1. Analyze research question and browser results
2. Create comprehensive outline
3. Define sections and subsections
4. Establish research guidelines

**State Updates**:
```python
state.outline = {
    "title": "Research Report Title",
    "sections": [
        {
            "heading": "Introduction",
            "subsections": [],
            "research_focus": "Overview and context"
        },
        {
            "heading": "Main Topic 1",
            "subsections": ["Subtopic 1.1", "Subtopic 1.2"],
            "research_focus": "Detailed analysis"
        }
    ]
}
```

### Stage 4: Deep Research
**Agent**: ResearcherAgent  
**Duration**: 30-120 seconds (parallel processing)

**Process**:
1. Assign sections to parallel research tasks
2. Conduct deep research per section
3. Gather citations and evidence
4. Validate information accuracy

**Parallel Execution**:
```python
async def parallel_research(sections):
    tasks = []
    for section in sections:
        task = asyncio.create_task(
            research_section(section)
        )
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results
```

**State Updates**:
```python
state.research_data = [
    {
        "section": "Main Topic 1",
        "content": "Detailed research content...",
        "citations": ["source1", "source2"],
        "confidence": 0.92
    }
]
```

### Stage 5: Report Writing
**Agent**: WriterAgent  
**Duration**: 20-40 seconds

**Process**:
1. Synthesize research into coherent narrative
2. Write introduction and conclusion
3. Format citations and references
4. Create table of contents
5. Ensure consistent tone and style

**State Updates**:
```python
state.draft = """
# Research Report Title

## Table of Contents
...

## Introduction
...

## Main Content
...

## Conclusion
...

## References
...
"""
```

### Stage 6: Multi-format Publishing
**Agent**: PublisherAgent  
**Duration**: 10-30 seconds

**Process**:
1. Convert markdown to PDF via LaTeX/Pandoc
2. Generate DOCX file
3. Preserve formatting across formats
4. Create output directory structure

**Output Files**:
```
outputs/
└── run_20240101_120000_research_query/
    ├── research_report.pdf
    ├── research_report.docx
    └── research_report.md
```

**State Updates**:
```python
state.published_formats = {
    "pdf": "/path/to/report.pdf",
    "docx": "/path/to/report.docx",
    "markdown": "/path/to/report.md"
}
```

### Stage 7: Translation (Optional)
**Agent**: TranslatorAgent  
**Duration**: 30-60 seconds

**Process**:
1. Detect source language
2. Translate to target language
3. Preserve markdown formatting
4. Handle technical terminology

**State Updates**:
```python
state.translated_report = """
# Tiêu đề Báo cáo Nghiên cứu
... (Vietnamese translation)
"""
```

### Stage 8: Quality Review
**Agent**: ReviewerAgent  
**Duration**: 10-20 seconds

**Process**:
1. Validate report structure
2. Check citation accuracy
3. Ensure guideline compliance
4. Review translation quality
5. Identify improvement areas

**State Updates**:
```python
state.review_feedback = {
    "structure": "pass",
    "citations": "pass",
    "formatting": "needs_improvement",
    "suggestions": ["Fix heading levels", "Add missing citation"]
}
```

### Stage 9: Final Revision
**Agent**: ReviserAgent  
**Duration**: 10-20 seconds

**Process**:
1. Implement reviewer feedback
2. Correct formatting issues
3. Enhance content clarity
4. Perform final polish

**State Updates**:
```python
state.final_report = """
# [Revised] Research Report Title
... (Final polished version)
"""
```

## Workflow Control Flow

### Decision Points

#### 1. Human Feedback Integration
```python
if state.include_human_feedback:
    human_input = await get_human_feedback()
    state.human_feedback = human_input
    # Return to appropriate stage based on feedback
```

#### 2. Translation Decision
```python
if state.language != "en":
    # Proceed to translation stage
    state = await translator_agent.translate(state)
```

#### 3. Error Recovery
```python
try:
    state = await agent.process(state)
except Exception as e:
    state.error_state = {"agent": agent_name, "error": str(e)}
    # Attempt recovery or fallback
    state = await recover_workflow(state)
```

### Conditional Branches

#### Quality Gates
```python
if state.review_feedback["structure"] == "fail":
    # Return to Writer agent for restructuring
    return "writer"
```

#### Retry Logic
```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    try:
        result = await agent.process(state)
        break
    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            raise WorkflowError(f"Agent failed after {MAX_RETRIES} attempts")
        await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Parallel Processing

### Concurrent Research Sections
```python
class ResearcherAgent:
    async def research_sections_parallel(self, sections):
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(5)
        
        async def research_with_limit(section):
            async with semaphore:
                return await self.research_section(section)
        
        tasks = [research_with_limit(s) for s in sections]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
```

### Batch Translation
```python
class TranslatorAgent:
    async def batch_translate(self, segments):
        # Process in batches to avoid API limits
        BATCH_SIZE = 10
        translated = []
        
        for i in range(0, len(segments), BATCH_SIZE):
            batch = segments[i:i+BATCH_SIZE]
            batch_results = await self.translate_batch(batch)
            translated.extend(batch_results)
        
        return translated
```

## Stream Processing

### Real-time Progress Updates
```python
async def stream_workflow_progress(state, callback):
    async for update in workflow.stream(state):
        # Send progress update to client
        await callback({
            "stage": update.current_stage,
            "progress": update.progress_percentage,
            "message": update.status_message
        })
```

### WebSocket Integration
```python
@websocket_endpoint("/ws/research")
async def research_websocket(websocket: WebSocket):
    await websocket.accept()
    
    async def send_update(update):
        await websocket.send_json(update)
    
    state = initialize_state(query)
    await stream_workflow_progress(state, send_update)
```

## Error Handling

### Agent-Level Errors
```python
class AgentError(Exception):
    def __init__(self, agent_name, original_error):
        self.agent_name = agent_name
        self.original_error = original_error
        super().__init__(f"Agent {agent_name} failed: {original_error}")
```

### Workflow-Level Recovery
```python
async def recover_workflow(state, error):
    recovery_strategies = {
        "BrowserAgent": lambda: use_fallback_search_provider(),
        "TranslatorAgent": lambda: skip_translation(),
        "PublisherAgent": lambda: save_markdown_only()
    }
    
    if error.agent_name in recovery_strategies:
        return await recovery_strategies[error.agent_name]()
    else:
        # Generic recovery: skip to next stage
        return advance_to_next_stage(state)
```

### State Rollback
```python
class StateManager:
    def __init__(self):
        self.checkpoints = []
    
    def checkpoint(self, state):
        self.checkpoints.append(deepcopy(state))
    
    def rollback(self, steps=1):
        if len(self.checkpoints) >= steps:
            return self.checkpoints[-steps]
        return self.checkpoints[0] if self.checkpoints else None
```

## Configuration

### Workflow Configuration (`multi_agents/task.json`)
```json
{
    "workflow": {
        "enable_parallel_research": true,
        "max_parallel_sections": 5,
        "enable_human_feedback": false,
        "enable_translation": true,
        "enable_review": true,
        "timeout_seconds": 300,
        "retry_failed_agents": true,
        "save_intermediate_drafts": true
    },
    "agents": {
        "researcher": {
            "max_search_depth": 3,
            "min_sources_per_section": 2
        },
        "writer": {
            "min_words_per_section": 200,
            "include_citations": true
        },
        "translator": {
            "preserve_formatting": true,
            "batch_size": 10
        }
    }
}
```

### Environment Configuration
```bash
# Workflow Control
ENABLE_PARALLEL_PROCESSING=true
MAX_WORKFLOW_TIMEOUT=300
ENABLE_STREAMING=true
SAVE_WORKFLOW_HISTORY=true

# Agent Timeouts
BROWSER_TIMEOUT=30
RESEARCHER_TIMEOUT=120
WRITER_TIMEOUT=60
TRANSLATOR_TIMEOUT=60

# Quality Gates
MIN_QUALITY_SCORE=0.7
REQUIRE_REVIEW_PASS=true
MAX_REVISION_ITERATIONS=3
```

## Performance Optimization

### Caching Strategy
```python
class WorkflowCache:
    def __init__(self):
        self.cache = {}
    
    def cache_key(self, query, tone, language):
        return hashlib.md5(f"{query}:{tone}:{language}".encode()).hexdigest()
    
    async def get_or_compute(self, key, compute_func):
        if key in self.cache:
            return self.cache[key]
        result = await compute_func()
        self.cache[key] = result
        return result
```

### Resource Management
```python
class ResourceManager:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(10)
        self.active_tasks = []
    
    async def manage_resources(self, task):
        async with self.semaphore:
            self.active_tasks.append(task)
            try:
                result = await task
                return result
            finally:
                self.active_tasks.remove(task)
```

## Monitoring & Logging

### Workflow Metrics
```python
class WorkflowMetrics:
    def __init__(self):
        self.stage_durations = {}
        self.error_counts = defaultdict(int)
        self.success_rate = 0
    
    def record_stage_duration(self, stage, duration):
        self.stage_durations[stage] = duration
    
    def record_error(self, agent, error_type):
        self.error_counts[f"{agent}:{error_type}"] += 1
    
    def calculate_success_rate(self):
        total = sum(self.error_counts.values()) + self.successful_runs
        self.success_rate = self.successful_runs / total if total > 0 else 0
```

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow.log'),
        logging.StreamHandler()
    ]
)

workflow_logger = logging.getLogger('workflow')
```

## Testing Workflows

### Unit Testing
```bash
# Test individual workflow stages
python -m pytest tests/unit/test_workflow_stages.py

# Test state management
python -m pytest tests/unit/test_state_management.py
```

### Integration Testing
```bash
# Test complete workflow
python -m pytest tests/integration/test_workflow_integration.py

# Test parallel processing
python -m pytest tests/integration/test_parallel_workflow.py
```

### End-to-End Testing
```bash
# Test full research pipeline
python -m pytest tests/e2e/test_end_to_end_workflow.py
```

## Debugging Workflows

### Debug Mode
```python
# Enable debug mode
export WORKFLOW_DEBUG=true

# Verbose logging
python main.py --research "query" --verbose
```

### Workflow Visualization
```python
# Generate workflow graph
from langgraph.graph import Graph

graph = workflow.get_graph()
graph.visualize(output_file="workflow.png")
```

### State Inspection
```python
# Print state at each stage
async def debug_workflow(state):
    async for update in workflow.stream(state):
        print(f"Stage: {update.current_stage}")
        print(f"State: {json.dumps(update.state, indent=2)}")
```

## Best Practices

### Workflow Design
1. Keep agents focused on single responsibilities
2. Use parallel processing where possible
3. Implement proper error boundaries
4. Add quality gates between critical stages
5. Enable streaming for better UX

### State Management
1. Minimize state size
2. Use immutable state updates
3. Implement state validation
4. Add checkpointing for recovery
5. Clean up temporary data

### Performance
1. Cache expensive operations
2. Use connection pooling
3. Implement request batching
4. Set appropriate timeouts
5. Monitor resource usage

## Future Enhancements

### Planned Features
- Dynamic workflow composition
- Conditional agent selection
- Advanced caching strategies
- Workflow templates
- Custom workflow hooks
- Distributed workflow execution
- Workflow versioning
- A/B testing for workflows