# Agent Implementations - Feature Documentation

## Purpose

Detailed implementation documentation for TK9's 8 specialized AI agents that form the research pipeline. Each agent has specific responsibilities in the workflow from initial browsing through final revision, orchestrated by LangGraph state machine.

## Agent Architecture

### Agent Workflow Pipeline
```
Browser → Editor → Researcher (parallel) → Writer →
Publisher → Translator → Reviewer → Reviser → END
```

### Agent Communication Pattern
All agents follow unified interface:
```python
class Agent:
    async def run(self, state: ResearchState) -> Dict[str, Any]:
        """
        Execute agent logic and return state updates

        Args:
            state: Current research state (immutable)

        Returns:
            Dictionary of state updates to merge
        """
        pass
```

## Individual Agent Documentation

### 1. Browser Agent (`agents/browser.py`)
**Status**: Implemented via gpt-researcher integration
**Purpose**: Initial web research and source discovery

**Responsibilities**:
- Analyze research query
- Discover relevant web sources
- Extract initial context
- Generate search queries

**Output**: List of relevant URLs and initial context

### 2. Editor Agent (`agents/editor.py` - 300+ lines)
**Purpose**: Research planning and section generation

**Key Methods**:
```python
async def run(self, state: ResearchState):
    """
    Generate research plan with sections

    Returns:
        {
            "research_plan": [
                {"title": "Section 1", "query": "...", "priority": 1},
                {"title": "Section 2", "query": "...", "priority": 2}
            ],
            "methodology": "Research approach description"
        }
    """
```

**Implementation Pattern**:
- Analyzes query intent and scope
- Generates 3-7 research sections
- Creates specific search queries for each section
- Sets quality guidelines

**Files**: `agents/editor.py:1-300`

### 3. Researcher Agent (`agents/researcher.py` - 150+ lines)
**Purpose**: Parallel data gathering across sections

**Key Methods**:
```python
async def conduct_research(section_query: str) -> Dict:
    """
    Execute search and extract information

    Uses gpt-researcher for:
    - Web search via configured provider
    - Content extraction
    - Source validation
    - Summary generation
    """
```

**Parallel Execution**:
```python
# Multiple instances run simultaneously
async def research_all_sections(sections):
    tasks = [
        researcher.conduct_research(section['query'])
        for section in sections
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Files**: `agents/researcher.py:1-150`

### 4. Writer Agent (`agents/writer.py` - 450+ lines)
**Purpose**: Synthesize research into structured report

**Key Methods**:
```python
async def write_report(research_data: List[Dict]) -> str:
    """
    Create comprehensive markdown report

    Includes:
    - Executive summary
    - Structured sections
    - Citations and references
    - Table of contents
    """
```

**Report Structure**:
```markdown
# Research Report Title

## Executive Summary
[High-level overview]

## Section 1: [Title]
[Detailed content with citations[1][2]]

## Section 2: [Title]
[Content continues...]

## References
[1] Source title - URL
[2] Source title - URL
```

**Files**: `agents/writer.py:1-450`

### 5. Publisher Agent (`agents/publisher.py` - 150+ lines)
**Purpose**: Generate multiple output formats

**Supported Formats**:
- **Markdown**: Native format (fastest)
- **PDF**: Via Pandoc + LaTeX (high quality)
- **DOCX**: Via python-docx (editable)

**Implementation**:
```python
async def publish(markdown_content: str) -> Dict[str, str]:
    """
    Generate all requested formats

    Returns:
        {
            "markdown_path": "path/to/report.md",
            "pdf_path": "path/to/report.pdf",
            "docx_path": "path/to/report.docx"
        }
    """
```

**Files**: `agents/publisher.py:1-150`

### 6. Translator Agent (`agents/translator.py` - 850+ lines)
**Purpose**: Multi-language translation with quality assurance

**Key Features**:
- Section-by-section translation
- Format preservation (markdown structure)
- Citation maintenance
- 50+ language support

**Translation Pipeline**:
```python
async def translate(content: str, target_lang: str) -> str:
    """
    Translate while preserving format

    Steps:
    1. Split into translatable sections
    2. Translate each section
    3. Preserve markdown formatting
    4. Maintain citations
    5. Reconstruct document
    """
```

**Quality Assurance**:
- Post-translation validation
- Format consistency check
- Citation integrity verification

**Files**: `agents/translator.py:1-850`

### 7. Reviewer Agent (`agents/reviewer.py` - 600+ lines)
**Purpose**: Quality assurance and validation

**Review Criteria**:
```python
review_aspects = [
    "factual_accuracy",      # Check facts against sources
    "citation_completeness", # Verify all claims cited
    "logical_flow",          # Content organization
    "tone_consistency",      # Matches requested tone
    "section_balance"        # Even coverage
]
```

**Review Output**:
```python
{
    "overall_quality": "good",
    "issues": [
        {"type": "citation", "location": "Section 2", "suggestion": "..."},
        {"type": "clarity", "location": "Intro", "suggestion": "..."}
    ],
    "recommendations": ["Expand section 3", "Add more data"]
}
```

**Files**: `agents/reviewer.py:1-600`

### 8. Reviser Agent (`agents/reviser.py` - 700+ lines)
**Purpose**: Implement reviewer suggestions

**Revision Process**:
```python
async def revise(content: str, review: Dict) -> str:
    """
    Apply improvements based on review

    Actions:
    - Fix citation issues
    - Improve clarity
    - Expand thin sections
    - Refine tone
    - Final polish
    """
```

**Revision Strategies**:
- **Critical Issues**: Must fix (missing citations, factual errors)
- **Improvements**: Should fix (clarity, flow)
- **Enhancements**: Optional (additional data, examples)

**Files**: `agents/reviser.py:1-700`

### 9. Human Agent (`agents/human.py` - 100+ lines)
**Purpose**: Optional human-in-the-loop feedback

**Usage Pattern**:
```python
if human_feedback_enabled:
    # Pause workflow for human input
    feedback = await human_agent.get_feedback(review)
    # Incorporate feedback into revision
    revised_content = await reviser.revise(content, feedback)
```

**Files**: `agents/human.py:1-100`

## Agent Utilities (`agents/utils/`)

### Core Utilities (`utils/utils.py`)
- Filename sanitization
- State management helpers
- Error handling utilities

### LLM Interface (`utils/llms.py`)
- Provider abstraction for agents
- Common LLM operations
- Response parsing

### Output Views (`utils/views.py`)
- Terminal output formatting
- WebSocket message formatting
- Progress indicators

### File Formats (`utils/file_formats.py`)
- PDF generation logic
- DOCX conversion
- Format validation

### Fact Checker (`utils/fact_checker.py`)
- Source verification
- Claim validation
- Confidence scoring

### Type Safety (`utils/type_safety.py`)
- Type guards
- Safe operations
- Validation helpers

### Date Context (`utils/date_context.py`)
- Temporal context injection
- Date-aware research
- Recency handling

## Development Patterns

### Adding New Agent
1. **Create Agent File**: `agents/new_agent.py`
2. **Implement Interface**:
   ```python
   class NewAgent:
       async def run(self, state: ResearchState) -> Dict[str, Any]:
           # Implementation
           return {"new_agent_output": result}
   ```
3. **Add to Workflow**: Update `orchestrator.py`
4. **Add Tests**: Unit tests in `tests/unit/test_agents.py`

### Modifying Agent Behavior
1. Read current implementation
2. Update `run()` method
3. Test in isolation
4. Integration test with full workflow

## Common Patterns

### Error Handling
```python
async def run(self, state: ResearchState):
    try:
        result = await self._process(state)
        return {"output": result}
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return {"error": str(e), "output": None}
```

### WebSocket Updates
```python
from agents.utils.views import print_agent_output

print_agent_output(
    "Processing section 1 of 5",
    agent="RESEARCHER",
    websocket=self.websocket
)
```

### State Access
```python
from agents.utils.type_safety import safe_dict_get

query = safe_dict_get(state, 'query', 'default', str)
sections = safe_dict_get(state, 'sections', [], list)
```

## Cross-References

- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Overall orchestration
- **[Agent Reference](/ref/agents.md)** - Detailed agent documentation
- **[Workflow Reference](/ref/workflow.md)** - Complete workflow diagrams

---

*For implementation details, see individual agent files. For usage examples, see integration tests.*
