# API Reference

## Overview

The Deep Research MCP provides a comprehensive multi-agent research system that orchestrates 8 specialized AI agents to conduct thorough research on any given topic. This document provides detailed API documentation for all modules, classes, and functions.

## Table of Contents

- [MCP Server API](#mcp-server-api)
- [Core Agents](#core-agents)
- [Utility Modules](#utility-modules)
- [Configuration System](#configuration-system)
- [Memory Management](#memory-management)
- [Provider System](#provider-system)

## MCP Server API

### `mcp_server.py`

Main MCP server implementation using FastMCP.

#### Functions

##### `deep_research(query: str, tone: str = "objective", ctx: Context = None) -> Dict[Any, Any]`

Perform deep research on a given query using multiple AI agents.

**Parameters:**
- `query` (str): The research question or topic to investigate
- `tone` (str, optional): Research tone. Options: `objective`, `critical`, `optimistic`, `balanced`, `skeptical`. Default: `objective`
- `ctx` (Context, optional): MCP context for progress reporting

**Returns:**
- `Dict[Any, Any]`: Dictionary containing:
  - `status` (str): "success" or "error"
  - `query` (str): Original query
  - `tone` (str): Used research tone
  - `report` (dict): Complete research results
  - `error` (str): Error message if status is "error"

**Example:**
```python
result = await deep_research("What are the latest AI developments?", tone="critical")
```

## Core Agents

### ChiefEditorAgent (`multi_agents/agents/orchestrator.py`)

The master coordinator that manages the research workflow and orchestrates all other agents.

#### Constructor

```python
ChiefEditorAgent(task: dict, websocket=None, stream_output=None, tone=None, headers=None, write_to_files: bool = False)
```

**Parameters:**
- `task` (dict): Task configuration containing research parameters
- `websocket` (optional): WebSocket connection for real-time communication
- `stream_output` (optional): Stream output handler function
- `tone` (optional): Research tone preference
- `headers` (dict, optional): HTTP headers for API requests
- `write_to_files` (bool): Whether to save intermediate and final outputs to files

#### Methods

##### `async run_research_task(task_id=None) -> dict`

Execute the complete research workflow.

**Parameters:**
- `task_id` (optional): Unique identifier for the task

**Returns:**
- `dict`: Final research results including all agent outputs

**Workflow:**
1. Browser Agent: Initial web research
2. Editor Agent: Plan report structure
3. Researcher Agent: Conduct detailed research (parallel)
4. Writer Agent: Compile final report
5. Publisher Agent: Export to multiple formats
6. Translator Agent: Translate if target language != English
7. Reviewer Agent: Quality review of translation
8. Reviser Agent: Improve translation if needed

##### `switch_providers(llm_fallback: bool = False, search_fallback: bool = False) -> dict`

Switch to fallback providers if needed.

**Parameters:**
- `llm_fallback` (bool): Switch to fallback LLM provider
- `search_fallback` (bool): Switch to fallback search provider

### WriterAgent (`multi_agents/agents/writer.py`)

Responsible for compiling final research reports with introduction and conclusion.

#### Methods

##### `async run(research_state: dict) -> dict`

Main execution method that compiles the final research report.

### EditorAgent (`multi_agents/agents/editor.py`) 

Plans research structure and manages parallel research execution.

#### Methods

##### `async plan_research(research_state: dict) -> dict`

Create research plan and outline.

##### `async run_parallel_research(research_state: dict) -> dict`

Execute research on multiple sections in parallel.

### ResearchAgent (`multi_agents/agents/researcher.py`)

Conducts detailed research on specific sections using web search and AI analysis.

#### Methods

##### `async run_initial_research(research_state: dict) -> dict`

Perform initial broad research on the topic.

### PublisherAgent (`multi_agents/agents/publisher.py`)

Exports research reports to multiple formats (PDF, DOCX, Markdown).

#### Methods

##### `async run(research_state: dict) -> dict`

Generate and save research report in all configured formats.

### TranslatorAgent (`multi_agents/agents/translator.py`)

Professional translation of final research reports with formatting preservation.

#### Methods

##### `async translate_report_file(research_state: dict) -> dict`

Translate final research report files maintaining markdown formatting.

**Features:**
- Multiple translation endpoints with failover
- Markdown formatting preservation
- Support for .md, .pdf, .docx formats
- Comprehensive error handling

##### `async run(research_state: dict) -> dict`

Main execution method for translation workflow.

### ReviewerAgent (`multi_agents/agents/reviewer.py`)

Reviews research drafts and translations for quality assurance.

#### Methods

##### `async review_draft(draft_state: dict) -> str`

Review draft content and provide feedback.

**Special Features:**
- Translation-specific review criteria
- Accuracy, formatting, fluency evaluation
- Guidelines compliance checking

##### `async run(draft_state: dict) -> dict`

Main execution with optional guideline enforcement.

### ReviserAgent (`multi_agents/agents/reviser.py`)

Improves content based on reviewer feedback.

#### Methods

##### `async revise_draft(draft_state: dict) -> dict`

Revise content based on review feedback.

##### `async run(draft_state: dict) -> dict`

Main execution method for revision workflow.

### HumanAgent (`multi_agents/agents/human.py`)

Enables human-in-the-loop feedback during research planning.

#### Methods

##### `async review_plan(research_state: dict) -> dict`

Present research plan to human for feedback and approval.

## Utility Modules

### File Formats (`multi_agents/agents/utils/file_formats.py`)

Handles file I/O and format conversion operations.

#### Functions

##### `async write_text_to_md(text: str, path: str) -> str`

Write text to a Markdown file.

##### `async write_md_to_pdf(text: str, path: str) -> str`

Convert Markdown to PDF using Pandoc with multiple fallback engines.

**PDF Engines (in order of preference):**
1. XeLaTeX (best quality)
2. pdflatex (good quality) 
3. Basic pandoc (default engine)

##### `async write_md_to_word(text: str, path: str) -> str`

Convert Markdown to DOCX format.

### LLM Interface (`multi_agents/agents/utils/llms.py`)

Provides unified interface for different LLM providers.

#### Functions

##### `async call_model(prompt: list, model: str = None) -> str`

Call configured LLM with prompt and return response.

### Views (`multi_agents/agents/utils/views.py`)

Utility functions for formatted output and logging.

#### Functions

##### `print_agent_output(message: str, agent: str = "AGENT") -> None`

Print formatted agent output with color coding and timestamps.

## Configuration System

### Provider Factory (`multi_agents/providers/factory.py`)

Manages multi-provider configuration and switching.

#### Functions

##### `get_current_providers() -> dict`

Get currently active provider configuration.

##### `switch_llm_provider(use_fallback: bool = False) -> None`

Switch LLM provider to primary or fallback.

##### `switch_search_provider(use_fallback: bool = False) -> None`

Switch search provider to primary or fallback.

### Language Configuration (`multi_agents/utils/language_config.py`)

Manages language settings for research and translation.

#### Class: `LanguageConfig`

##### `get_language_name(code: str) -> str`

Convert language code to full language name.

##### `apply_to_environment() -> None`

Apply language configuration to environment variables.

## Memory Management

### Research State (`multi_agents/memory/research.py`)

Typed dictionary for maintaining workflow state across agents.

#### Fields

- `task` (dict): Task configuration
- `initial_research` (str): Initial research findings
- `sections` (list): Research sections
- `research_data` (list): Detailed research results
- `draft` (str): Current draft content
- `revision_notes` (str): Feedback for revisions
- `human_feedback` (str): Human reviewer feedback

### Draft Manager (`multi_agents/utils/draft_manager.py`)

Manages intermediate outputs and workflow history.

#### Methods

##### `save_agent_output(agent_name: str, phase: str, output: Any, step: str, metadata: dict = None) -> None`

Save agent output to structured draft files.

##### `save_research_state(phase: str, state: dict) -> None`

Save complete research state at workflow checkpoints.

##### `get_phase_history(phase: str) -> list`

Retrieve all outputs for a specific workflow phase.

## Provider System

### Supported LLM Providers

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Google Gemini**: Gemini-1.5-pro, Gemini-1.5-flash, Gemini-1.0-pro
- **Anthropic**: Claude-3-sonnet, Claude-3-haiku
- **Azure OpenAI**: GPT-4, GPT-3.5-turbo

### Supported Search Providers

- **Tavily**: AI-optimized search with deep research capabilities
- **Brave Search**: Independent search engine with news search
- **Google**: Custom search engine integration
- **DuckDuckGo**: Privacy-focused search (no API key required)
- **SerpAPI**: Google search scraping service

### Provider Configuration

Configure providers via environment variables:

```bash
# Primary providers
PRIMARY_LLM_PROVIDER=openai|google_gemini|anthropic|azure_openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily|brave|google|duckduckgo|serpapi

# Fallback providers
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_SEARCH_PROVIDER=brave

# API Keys
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here
```

## Error Handling

All agents implement comprehensive error handling with:

- **Graceful degradation**: Fallback to alternative providers
- **Retry mechanisms**: Automatic retry with exponential backoff
- **Error logging**: Detailed error messages and stack traces
- **State preservation**: Research state maintained during failures
- **Recovery workflows**: Ability to resume from last successful checkpoint

## Performance Considerations

- **Parallel execution**: Multiple research sections processed concurrently
- **Async/await patterns**: Non-blocking I/O operations
- **Provider optimization**: Automatic selection of fastest providers
- **Memory management**: Efficient state handling for large research tasks
- **File streaming**: Large file operations use streaming for memory efficiency

## Security

- **API key management**: Secure storage and rotation
- **Input validation**: Sanitization of user inputs
- **Output filtering**: Content safety checks
- **Provider isolation**: Sandboxed provider interactions
- **Audit logging**: Complete audit trail of all operations