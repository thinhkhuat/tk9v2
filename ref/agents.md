# Agent Reference Documentation

## Overview

The Deep Research MCP system employs 7 active AI agents orchestrated through LangGraph to conduct comprehensive research. Each agent has specific responsibilities and capabilities within the research workflow.

**Note**: Reviewer and Reviser agents are currently disabled due to quality and technical improvements in progress.

## Agent Architecture

### Core Components
- **Base Agent Class**: Common functionality shared across all agents
- **State Management**: Uses `ResearchState` for workflow state
- **Async Execution**: All agents implement async/await patterns
- **Error Handling**: Robust error recovery and fallback mechanisms

## Agent Descriptions

### 1. ChiefEditorAgent (Orchestrator)
**File**: `multi_agents/agents/orchestrator.py`  
**Role**: Master coordinator managing the entire research workflow

**Key Responsibilities**:
- Orchestrates the flow between all other agents
- Manages state transitions and workflow decisions
- Handles error recovery and retry logic
- Coordinates parallel research tasks
- Determines when to engage specific agents

**Critical Methods**:
- `plan_research()`: Initial research planning
- `review_draft()`: Reviews and approves drafts
- `finalize_report()`: Final report validation

### 2. SearchAgent
**File**: Integrated within orchestrator
**Role**: Initial web research and source gathering

**Key Responsibilities**:
- Performs initial web searches for research topics
- Collects relevant URLs and sources
- Filters and ranks search results by relevance
- Extracts key information from web pages

**Integration**: Uses configured search providers (BRAVE, Tavily, etc.)

### 3. PlanAgent
**File**: `multi_agents/agents/editor.py`
**Role**: Plans report structure and detailed outline

**Key Responsibilities**:
- Creates comprehensive report outlines
- Defines section structure and organization
- Identifies key topics to research
- Establishes research guidelines and focus areas

**Output**: Structured outline with sections and subsections

### 4. ResearchAgent
**File**: `multi_agents/agents/researcher.py`
**Role**: Conducts detailed research on each section

**Key Responsibilities**:
- Performs deep research on assigned sections
- Gathers supporting evidence and citations
- Validates information accuracy
- Supports parallel processing for multiple sections

**Features**:
- Parallel section research capability
- Citation management
- Fact verification

### 5. WriteAgent
**File**: `multi_agents/agents/writer.py`
**Role**: Compiles final report with introduction and conclusion

**Key Responsibilities**:
- Synthesizes research into coherent narrative
- Writes introduction and conclusion
- Ensures consistent tone and style
- Formats citations and references
- Creates table of contents

**Output**: Complete markdown report with proper formatting

### 6. PublishAgent
**File**: `multi_agents/agents/publisher.py`
**Role**: Exports reports to multiple formats

**Key Responsibilities**:
- Converts markdown to PDF using LaTeX/Pandoc
- Generates DOCX files for editing
- Preserves formatting across formats
- Manages output directory structure

**Supported Formats**:
- PDF (high-quality LaTeX rendering)
- DOCX (Microsoft Word)
- Markdown (source format)

### 7. TranslateAgent
**File**: `multi_agents/agents/translator.py`
**Role**: Translates content to target languages

**Key Responsibilities**:
- Translates reports to 50+ languages
- Preserves markdown formatting
- Handles technical terminology
- Manages translation API endpoints
- Implements retry logic for reliability

**Features**:
- Multiple translation endpoint support
- Formatting preservation
- Batch translation capability
- Language detection

### 8. ReviewerAgent (DISABLED)
**File**: `multi_agents/agents/reviewer.py`
**Status**: ⚠️ Currently disabled due to quality and technical improvements

**Previous Role**: Quality assurance and formatting validation

**Note**: This agent is temporarily disabled. Quality assurance is currently handled through alternative methods.

### 9. ReviserAgent (DISABLED)
**File**: `multi_agents/agents/reviser.py`
**Status**: ⚠️ Currently disabled due to quality and technical improvements

**Previous Role**: Final revisions and corrections

**Note**: This agent is temporarily disabled. Revisions are currently handled through alternative methods.

### 10. HumanAgent
**File**: `multi_agents/agents/human.py`
**Role**: Human-in-the-loop feedback integration

**Key Responsibilities**:
- Collects human feedback when enabled
- Integrates manual corrections
- Allows interactive review process
- Supports iterative refinement

**Usage**: Optional, enabled via `include_human_feedback` configuration

## Agent Communication

### State Management
All agents communicate through the `ResearchState` object which maintains:
- Current research query
- Report sections and outline
- Draft versions
- Research findings
- Translation status
- Review feedback
- Final outputs

### Workflow Coordination
```python
# Active workflow sequence (7 agents)
Search → Plan → Research → Write → Publish → Translate
                              ↓
                      Orchestrator (coordinates all)
```

**Note**: Reviewer and Reviser agents are currently disabled.

### Parallel Processing
- **Research Agent**: Can process multiple sections simultaneously
- **Translate Agent**: Supports batch translation
- **Publish Agent**: Generates multiple formats concurrently

## Agent Configuration

### Task Configuration (`multi_agents/task.json`)
```json
{
  "query": "Research question",
  "max_sections": 5,
  "include_human_feedback": false,
  "follow_guidelines": true,
  "guidelines": ["Focus on recent data", "Include citations"],
  "language": "en",
  "tone": "objective"
}
```

### Agent-Specific Settings
- **Researcher**: `max_sections` controls parallel research depth
- **Translator**: `language` determines target translation
- **Publisher**: `publish_formats` specifies output formats
- **Human**: `include_human_feedback` enables/disables

## Error Handling

### Agent-Level Error Recovery
Each agent implements:
1. **Try-Catch Blocks**: Graceful error handling
2. **Retry Logic**: Automatic retry with exponential backoff
3. **Fallback Strategies**: Alternative approaches on failure
4. **Error Propagation**: Informative error messages to orchestrator

### Orchestrator Error Management
The ChiefEditorAgent handles:
- Agent failure recovery
- Workflow rerouting
- State rollback when needed
- User notification of issues

## Performance Considerations

### Optimization Strategies
1. **Parallel Processing**: Multiple sections researched simultaneously
2. **Caching**: Results cached to avoid redundant operations
3. **Lazy Loading**: Agents loaded only when needed
4. **Stream Processing**: Real-time progress updates

### Resource Management
- **Memory**: State pruning for long research sessions
- **API Calls**: Rate limiting and quota management
- **Token Usage**: Efficient prompt engineering
- **Timeouts**: Configurable timeouts per agent

## Integration Points

### Provider Integration
Agents integrate with providers through:
- **LLM Providers**: For content generation and analysis
- **Search Providers**: For web research and source gathering
- **Translation Services**: For multi-language support

### Output Integration
- **File System**: Saves reports to `./outputs/` directory
- **MCP Protocol**: Returns structured responses
- **Streaming**: Real-time progress updates

## Best Practices

### Agent Development
1. **Single Responsibility**: Each agent focuses on one task
2. **Async First**: Use async/await for all operations
3. **Error Resilience**: Implement comprehensive error handling
4. **State Immutability**: Don't modify state directly
5. **Logging**: Detailed logging for debugging

### Agent Usage
1. **Configure Appropriately**: Set task.json for specific needs
2. **Monitor Progress**: Use verbose mode for debugging
3. **Handle Failures**: Implement retry logic in orchestration
4. **Validate Output**: Check agent outputs before proceeding

## Debugging Agents

### Debug Commands
```bash
# Run with verbose output
python main.py --research "query" --verbose

# Test specific agent
python -m pytest tests/unit/test_[agent_name].py

# Check agent logs
tail -f logs/agents.log
```

### Common Issues
1. **Translation Failures**: Check API endpoints and keys
2. **Publisher Errors**: Verify Pandoc/LaTeX installation
3. **Research Timeouts**: Adjust timeout configurations
4. **Memory Issues**: Reduce max_sections or batch size

## Agent Enhancement Opportunities

### Current Limitations
- Sequential workflow (some parallelization)
- Fixed agent roles
- Limited customization per agent

### Future Enhancements
- Dynamic agent spawning
- Custom agent plugins
- Advanced caching strategies
- Multi-modal capabilities
- Real-time collaboration