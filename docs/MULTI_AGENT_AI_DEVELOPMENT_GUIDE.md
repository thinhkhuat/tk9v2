# Agent Development Guide

## Agent System Overview

This system uses 8 specialized agents orchestrated by LangGraph. Each agent has a specific role in the research pipeline.

## Agent Base Class Pattern

```python
# All agents inherit from BaseAgent
from multi_agents.agents.base_agent import BaseAgent
from typing import Dict, Any, Optional

class BaseAgent:
    def __init__(self, role: str, goal: str, backstory: str, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.verbose = kwargs.get('verbose', True)
        self.max_iter = kwargs.get('max_iter', 5)
        self.llm = kwargs.get('llm')  # LLM instance
        self.tools = kwargs.get('tools', [])
        self.callbacks = kwargs.get('callbacks')
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute the agent's task"""
        raise NotImplementedError
```

## Existing Agents Reference

### 1. ChiefEditorAgent (Orchestrator)
```python
# Location: multi_agents/agents/orchestrator.py
# Role: Master coordinator managing the entire workflow
# Key Methods:
- run_research_task() - Main entry point
- _create_workflow() - Builds LangGraph workflow
- _run_parallel_research() - Manages parallel researcher agents
```

### 2. BrowserAgent
```python
# Location: multi_agents/agents/browser.py  
# Role: Initial web research and source gathering
# Key Features:
- Uses search providers (BRAVE, Tavily, etc.)
- Collects initial sources
- Creates research context
```

### 3. EditorAgent
```python
# Location: multi_agents/agents/editor.py
# Role: Plans report structure and outline
# Key Features:
- Creates detailed outline
- Defines section structure
- Sets research parameters
```

### 4. ResearcherAgent
```python
# Location: multi_agents/agents/researcher.py
# Role: Detailed research on specific sections
# Key Features:
- Parallel execution support
- Deep research per section
- Source validation
```

### 5. WriterAgent
```python
# Location: multi_agents/agents/writer.py
# Role: Compiles final report
# Key Features:
- Markdown formatting
- Introduction/conclusion writing
- Citation management
```

### 6. PublisherAgent
```python
# Location: multi_agents/agents/publisher.py
# Role: Multi-format export
# Key Features:
- PDF generation (via Pandoc)
- DOCX export
- Markdown finalization
```

### 7. TranslatorAgent
```python
# Location: multi_agents/agents/translator.py
# Role: Language translation
# Key Features:
- 50+ language support
- Formatting preservation
- Multi-endpoint failover
```

### 8. ReviewerAgent & ReviserAgent
```python
# Location: multi_agents/agents/reviewer.py, reviser.py
# Role: Quality assurance and corrections
# Key Features:
- Formatting validation
- Content quality checks
- Final corrections
```

## Creating a New Agent

### Step 1: Create Agent File
```python
# File: multi_agents/agents/new_agent.py
from typing import Dict, Any, Optional
from multi_agents.agents.base_agent import BaseAgent
from multi_agents.utils.views import print_agent_output

class NewAgent(BaseAgent):
    def __init__(self, **kwargs):
        role = kwargs.get('role', 'New Agent')
        goal = kwargs.get('goal', 'Perform new specialized task')
        backstory = kwargs.get('backstory', 'Expert in new domain with years of experience')
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute the new agent's task"""
        if context is None:
            context = {}
        
        # Get previous agent outputs if needed
        previous_output = context.get('previous_output', '')
        
        # Your agent logic here
        prompt = f"""
        As a {self.role}, your goal is to {self.goal}.
        
        Task: {task}
        
        Context: {previous_output}
        
        Please provide your output:
        """
        
        # Use LLM to generate response
        if self.llm:
            response = await self.llm.ainvoke(prompt)
            result = response.content if hasattr(response, 'content') else str(response)
        else:
            result = "No LLM configured"
        
        # Print output for debugging
        if self.verbose:
            print_agent_output(f"{self.role} Output", result)
        
        return result
```

### Step 2: Register Agent
```python
# File: multi_agents/agents/__init__.py
from .browser import BrowserAgent
from .editor import EditorAgent
from .researcher import ResearcherAgent
from .writer import WriterAgent
from .publisher import PublisherAgent
from .translator import TranslatorAgent
from .reviewer import ReviewerAgent
from .reviser import ReviserAgent
from .human import HumanAgent
from .new_agent import NewAgent  # ADD THIS LINE

__all__ = [
    "BrowserAgent",
    "EditorAgent", 
    "ResearcherAgent",
    "WriterAgent",
    "PublisherAgent",
    "TranslatorAgent",
    "ReviewerAgent",
    "ReviserAgent",
    "HumanAgent",
    "NewAgent"  # ADD THIS LINE
]
```

### Step 3: Integrate into Workflow
```python
# File: multi_agents/agents/orchestrator.py
# In ChiefEditorAgent._create_workflow() method

# Add state field if needed
class ResearchState(TypedDict):
    # ... existing fields ...
    new_agent_output: str  # ADD THIS

# Add agent initialization
self.new_agent = NewAgent(
    llm=llm,
    verbose=self.verbose,
    callbacks=self.callbacks
)

# Add workflow node
async def new_agent_node(state):
    task = "Your specific task here"
    context = {
        'previous_output': state.get('some_previous_output', '')
    }
    result = await self.new_agent.execute(task, context)
    return {"new_agent_output": result}

# Add to workflow
workflow.add_node("new_agent", new_agent_node)

# Add edge from previous node
workflow.add_edge("previous_node", "new_agent")
workflow.add_edge("new_agent", "next_node")
```

## Agent Communication Patterns

### 1. Sequential Communication
```python
# Agent A -> Agent B -> Agent C
workflow.add_edge("agent_a", "agent_b")
workflow.add_edge("agent_b", "agent_c")
```

### 2. Parallel Execution
```python
# Multiple agents run simultaneously
async def run_parallel_agents(state):
    tasks = []
    for section in state['sections']:
        task = researcher_agent.execute(section, context)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return {"research_results": results}
```

### 3. Conditional Routing
```python
# Route based on state
def should_translate(state):
    return state.get('language') != 'en'

workflow.add_conditional_edges(
    "writer",
    should_translate,
    {
        True: "translator",
        False: "publisher"
    }
)
```

## State Management

### ResearchState Structure
```python
class ResearchState(TypedDict):
    task: str                    # Initial research query
    browser_output: str          # Web research results
    editor_output: str           # Report outline
    research_data: List[str]     # Section research
    final_report: str           # Compiled report
    published_formats: Dict      # Export paths
    translated_content: str      # Translated version
    reviewer_feedback: str       # Quality review
    revised_content: str         # Final content
    language: str               # Target language
    tone: str                   # Report tone
```

### Accessing State in Agents
```python
async def agent_node(state: ResearchState) -> Dict[str, Any]:
    # Read from state
    previous_data = state.get('editor_output', '')
    
    # Process
    result = await agent.execute(task, {'context': previous_data})
    
    # Update state
    return {"agent_output": result}
```

## Testing Agents

### Unit Test Template
```python
# File: tests/unit/test_new_agent.py
import pytest
from multi_agents.agents.new_agent import NewAgent

@pytest.mark.asyncio
async def test_new_agent_execution():
    agent = NewAgent(verbose=False)
    
    task = "Test task"
    context = {"previous_output": "Test context"}
    
    result = await agent.execute(task, context)
    
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio  
async def test_new_agent_with_llm():
    from unittest.mock import AsyncMock
    
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value.content = "Test response"
    
    agent = NewAgent(llm=mock_llm, verbose=False)
    result = await agent.execute("Test task")
    
    assert result == "Test response"
    mock_llm.ainvoke.assert_called_once()
```

## Best Practices

### 1. Error Handling
```python
async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
    try:
        # Agent logic
        result = await self._process_task(task, context)
        return result
    except Exception as e:
        error_msg = f"Error in {self.role}: {str(e)}"
        if self.verbose:
            print(f"❌ {error_msg}")
        # Return graceful fallback
        return f"Unable to complete task due to: {error_msg}"
```

### 2. Streaming Support
```python
async def execute_with_stream(self, task: str, context: Dict[str, Any] = None):
    """Execute with streaming output"""
    async for chunk in self._stream_process(task, context):
        if self.callbacks:
            await self.callbacks.on_chunk(chunk)
        yield chunk
```

### 3. Tool Integration
```python
from langchain.tools import Tool

class NewAgent(BaseAgent):
    def __init__(self, **kwargs):
        # Define tools
        tools = [
            Tool(
                name="search",
                func=self._search,
                description="Search for information"
            ),
            Tool(
                name="analyze",
                func=self._analyze,
                description="Analyze data"
            )
        ]
        kwargs['tools'] = tools
        super().__init__(**kwargs)
```

## Debugging Tips

1. **Enable Verbose Mode**: Set `verbose=True` for detailed output
2. **Check State Flow**: Print state at each node to trace data flow
3. **Test in Isolation**: Test agents individually before integration
4. **Mock External Dependencies**: Use mocks for LLMs during testing
5. **Log Transitions**: Add logging between workflow nodes

## Common Patterns to Copy

### Pattern 1: Research Agent with Sections
```python
# From researcher.py
for section in sections:
    section_research = await self.execute(
        f"Research this section: {section}",
        context={'sources': sources}
    )
    results.append(section_research)
```

### Pattern 2: Format Validation
```python
# From reviewer.py
def validate_format(content: str) -> Dict[str, Any]:
    issues = []
    if not content.startswith('#'):
        issues.append("Missing main title")
    if '```' in content and '```\n' not in content:
        issues.append("Code blocks not properly formatted")
    return {"valid": len(issues) == 0, "issues": issues}
```

### Pattern 3: Multi-Provider Support
```python
# From translator.py
providers = ['primary_endpoint', 'fallback_endpoint']
for provider in providers:
    try:
        result = await self._translate_with_provider(content, provider)
        if result:
            return result
    except Exception:
        continue
```

Remember: Always follow existing patterns and test thoroughly before integration.