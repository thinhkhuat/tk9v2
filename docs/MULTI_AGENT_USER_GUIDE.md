# Deep Research MCP - User Guide

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [CLI Interface](#cli-interface)
- [MCP Integration](#mcp-integration)
- [Multi-Provider Configuration](#multi-provider-configuration)
- [Translation Features](#translation-features)
- [Output Formats](#output-formats)
- [Customization](#customization)

## Quick Start

The Deep Research MCP is a powerful multi-agent research system that can conduct comprehensive research on any topic and produce detailed reports in multiple formats and languages.

### 30-Second Demo

```bash
# Clone and setup
git clone <repository-url>
cd deep-research-mcp-og
pip install -r multi_agents/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run a quick research
python main.py --research "What are the latest AI developments?"
```

## Installation

### Prerequisites

- **Python 3.12+** (required)
- **API Keys** for LLM and search providers
- **Pandoc** (optional, for PDF generation)
- **LaTeX** (optional, for high-quality PDFs)

### Step 1: Environment Setup

```bash
# Install dependencies
pip install -r multi_agents/requirements.txt

# Or use uv (recommended)
uv sync
```

### Step 2: API Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Required: At least one search provider  
TAVILY_API_KEY=your_tavily_key_here
BRAVE_API_KEY=your_brave_key_here

# Optional: Provider preferences
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily
```

### Step 3: Optional Tools

For enhanced PDF generation:

```bash
# Install Pandoc
brew install pandoc

# Install LaTeX (for high-quality PDFs)
brew install --cask basictex
```

## Basic Usage

### Method 1: CLI Interface (Recommended)

#### Interactive Mode

```bash
python main.py
```

This opens an interactive chat interface where you can:
- Conduct multiple research sessions
- View real-time progress
- Access configuration and history
- Use commands like `/help`, `/config`, `/clear`

#### Single Query Mode

```bash
python main.py --research "Your research question"
```

#### With Options

```bash
python main.py --research "Climate change impacts" \
  --tone critical \
  --verbose \
  --save-files
```

### Method 2: MCP Server

#### Start the Server

```bash
python mcp_server.py
```

#### Use via MCP Client

```python
import mcp_client

result = await mcp_client.deep_research(
    query="What are the latest AI developments?",
    tone="objective"
)
```

### Method 3: Direct Python Integration

```python
from multi_agents.main import run_research_task
from gpt_researcher.utils.enum import Tone

result = await run_research_task(
    query="Your research question",
    tone=Tone.Critical,
    write_to_files=True,
    language="vi"  # For Vietnamese translation
)
```

## Advanced Features

### Multi-Agent Workflow

The system uses 8 specialized agents working in sequence:

1. **Browser Agent**: Initial web research and topic exploration
2. **Editor Agent**: Structure planning and section organization  
3. **Researcher Agent**: Detailed research on each section (parallel execution)
4. **Writer Agent**: Report compilation with introduction/conclusion
5. **Publisher Agent**: Multi-format export (PDF, DOCX, Markdown)
6. **Translator Agent**: Professional translation with formatting preservation
7. **Reviewer Agent**: Quality assurance and feedback generation
8. **Reviser Agent**: Content improvement based on feedback

### Human-in-the-Loop

Enable human feedback during research planning:

```json
{
  "include_human_feedback": true,
  "follow_guidelines": true,
  "guidelines": [
    "Focus on recent developments (2023-2024)",
    "Include statistical data and citations",
    "Maintain objective tone throughout"
  ]
}
```

### Real-time Progress Tracking

Monitor research progress with live updates:

```bash
python main.py --research "Your topic" --verbose
```

Shows:
- Current agent activity
- Research section progress
- File generation status
- Translation progress
- Error handling and recovery

## CLI Interface

### Interactive Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | `/help` |
| `/config` | Display current configuration | `/config` |
| `/history` | Show research history | `/history` |
| `/clear` | Clear terminal | `/clear` |
| `/quit` | Exit application | `/quit` |

### Command Line Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--research` | Single research query | None | `--research "AI trends"` |
| `--tone` | Research tone | `objective` | `--tone critical` |
| `--verbose` | Detailed output | `False` | `--verbose` |
| `--save-files` | Save to files | `True` | `--save-files` |
| `--no-save-files` | Console only | `False` | `--no-save-files` |
| `--config` | Show configuration | `False` | `--config` |
| `--provider-info` | Provider status | `False` | `--provider-info` |

### Research Tones

- **objective**: Balanced, factual reporting
- **critical**: Analytical, questioning approach  
- **optimistic**: Positive perspective emphasis
- **balanced**: Multiple viewpoint consideration
- **skeptical**: Cautious, evidence-focused approach

## MCP Integration

### Server Configuration

The MCP server runs on default MCP port and provides:

- **Tool**: `deep_research`
- **Progress reporting**: Real-time updates via MCP context
- **Error handling**: Structured error responses
- **Streaming**: Live progress updates

### Client Integration

```python
# Via MCP client
async def research_with_mcp():
    result = await mcp_client.call_tool(
        "deep_research",
        {
            "query": "Latest developments in quantum computing",
            "tone": "critical"
        }
    )
    return result["report"]
```

### Claude Desktop Integration

Add to Claude Desktop MCP configuration:

```json
{
  "servers": {
    "deep-research": {
      "command": "python",
      "args": ["path/to/mcp_server.py"]
    }
  }
}
```

## Multi-Provider Configuration

### Supported Providers

#### LLM Providers
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- **Google Gemini**: `gemini-1.5-pro`, `gemini-1.5-flash`
- **Anthropic**: `claude-3-sonnet`, `claude-3-haiku`
- **Azure OpenAI**: `gpt-4`, `gpt-3.5-turbo`

#### Search Providers
- **Tavily**: AI-optimized research (recommended)
- **Brave Search**: Independent, privacy-focused
- **Google Custom Search**: Comprehensive results
- **DuckDuckGo**: No API key required
- **SerpAPI**: Google scraping service

### Provider Configuration

```bash
# Primary configuration
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily

# Fallback configuration
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_SEARCH_PROVIDER=brave

# Cost optimization
MAX_CONCURRENT_SEARCHES=5
REQUEST_TIMEOUT=30
```

### Provider Switching

Automatic fallback on failures:

```python
# Providers switch automatically on errors
# Manual switching available:
chief_editor.switch_providers(
    llm_fallback=True,    # Switch to fallback LLM
    search_fallback=True  # Switch to fallback search
)
```

### Provider Status

Check provider availability:

```bash
python main.py --provider-info
```

Output shows:
- Active providers and models
- API key status
- Connection testing results
- Cost estimates
- Performance metrics

## Translation Features

### Supported Languages

The system supports translation to any language supported by your translation endpoints:

- **Vietnamese** (`vi`): Primary target language
- **Spanish** (`es`): Fully supported
- **French** (`fr`): Fully supported
- **German** (`de`): Fully supported
- **Chinese** (`zh`): Fully supported
- **Japanese** (`ja`): Fully supported

### Translation Configuration

Set target language in `task.json`:

```json
{
  "language": "vi",
  "query": "Your research question"
}
```

Or via CLI:

```bash
python main.py --research "Your question" --language vi
```

### Translation Endpoints

Multiple endpoints with failover:

1. **Primary**: `https://n8n.thinhkhuat.com/webhook/agent/translate`
2. **Backup**: `https://srv.saola-great.ts.net/webhook/agent/translate`  
3. **Tertiary**: `https://n8n.thinhkhuat.work/webhook/agent/translate`

### Translation Quality

Post-translation quality assurance:

1. **Automatic Review**: Translation accuracy and formatting check
2. **Revision Loop**: Improvement based on review feedback
3. **Formatting Preservation**: Markdown structure maintained
4. **Multi-format Support**: Translated PDF, DOCX, and Markdown files

### Translation Workflow

```
Original Report (EN) → Translation → Review → Revision (if needed) → Final Output
```

## Output Formats

### File Structure

```
./outputs/run_{timestamp}_{query_preview}/
├── research_report.md         # Markdown format
├── research_report.pdf        # PDF format
├── research_report.docx       # Word format
├── research_report_vi.md      # Translated Markdown
├── research_report_vi.pdf     # Translated PDF
├── research_report_vi.docx    # Translated Word
├── drafts/                    # Intermediate outputs
│   ├── 1_initial_research/
│   ├── 2_planning/
│   ├── 3_parallel_research/
│   ├── 4_writing/
│   ├── 5_editing/
│   ├── 6_publishing/
│   ├── translation/
│   ├── human_feedback/
│   ├── revisions/
│   └── metadata.json
└── WORKFLOW_SUMMARY.md        # Process summary
```

### Format Features

#### PDF Output
- Professional formatting with margins
- Table of contents (when applicable)
- Proper heading hierarchy
- High-quality graphics (with LaTeX)

#### DOCX Output
- Microsoft Word compatibility
- Editable format for further revision
- Preserved formatting and structure
- Table and list support

#### Markdown Output
- GitHub-flavored Markdown
- Code syntax highlighting
- Table support
- Link preservation

### Output Control

```bash
# Save all formats (default)
python main.py --research "Question" --save-files

# Console output only
python main.py --research "Question" --no-save-files

# Custom output directory
export OUTPUT_DIR="./custom_output"
python main.py --research "Question"
```

## Customization

### Task Configuration

Edit `multi_agents/task.json`:

```json
{
  "query": "Default research question",
  "max_sections": 5,
  "publish_formats": ["pdf", "docx", "md"],
  "include_human_feedback": false,
  "follow_guidelines": true,
  "model": "gpt-4o",
  "language": "en",
  "guidelines": [
    "Focus on recent developments",
    "Include statistical data",
    "Provide citations and sources",
    "Maintain objective tone"
  ],
  "tone": "objective",
  "max_sources_per_section": 3,
  "max_research_depth": 3
}
```

### Agent Customization

Modify agent behavior by editing agent files:

```python
# multi_agents/agents/researcher.py
class ResearchAgent:
    def __init__(self, websocket=None, stream_output=None, tone=None):
        self.custom_search_depth = 5  # Increase search depth
        self.max_sources = 10         # More sources per section
```

### Custom Guidelines

Add research-specific guidelines:

```json
{
  "guidelines": [
    "Focus on peer-reviewed sources",
    "Include quantitative data where possible",
    "Cite sources in APA format",
    "Highlight controversies and debates",
    "Include recent developments (last 2 years)"
  ]
}
```

### WebSocket Integration

For real-time updates in web applications:

```python
import websockets

async def research_with_websocket():
    async def stream_handler(type, key, value, websocket):
        await websocket.send(json.dumps({
            "type": type,
            "key": key, 
            "value": value
        }))
    
    async with websockets.serve(handle_client, "localhost", 8765):
        result = await run_research_task(
            query="Your question",
            stream_output=stream_handler,
            websocket=websocket
        )
```

### Performance Tuning

Optimize for your use case:

```bash
# Environment variables for performance
export MAX_CONCURRENT_SECTIONS=3    # Parallel research sections
export REQUEST_TIMEOUT=60           # API timeout
export RETRY_ATTEMPTS=3             # Failed request retries
export CHUNK_SIZE=1000             # Translation chunk size
export CACHE_DURATION=3600         # Search result caching
```

## Best Practices

### Research Quality

1. **Use specific queries**: "Latest developments in quantum computing 2024" vs "quantum computing"
2. **Set appropriate tone**: Use "critical" for analysis, "objective" for reports
3. **Enable guidelines**: Provide specific research requirements
4. **Review outputs**: Use human feedback for important research

### Performance

1. **Choose appropriate providers**: Tavily for research, GPT-4o for quality
2. **Monitor costs**: Check provider usage and set limits
3. **Use fallbacks**: Configure backup providers for reliability
4. **Optimize sections**: Adjust max_sections based on topic complexity

### Security

1. **Protect API keys**: Use environment variables, not hardcoded keys
2. **Validate inputs**: Sanitize research queries
3. **Monitor usage**: Track API consumption and costs
4. **Regular updates**: Keep dependencies updated

### Troubleshooting

1. **Check logs**: Use `--verbose` for detailed output
2. **Verify providers**: Run `--provider-info` to check status
3. **Test translation**: Ensure translation endpoints are accessible
4. **Monitor resources**: Check disk space for output files

## Examples

### Academic Research

```bash
python main.py --research "Impact of artificial intelligence on higher education: systematic review of recent literature" --tone critical --save-files
```

### Business Analysis

```bash
python main.py --research "Market analysis of electric vehicle adoption in Southeast Asia 2024" --tone balanced
```

### Technical Documentation

```bash
python main.py --research "Comparison of modern web frameworks: React, Vue, and Angular performance benchmarks" --tone objective
```

### Multilingual Research

```bash
# Research in English, output in Vietnamese
python main.py --research "Latest developments in renewable energy" --language vi --tone optimistic
```

This comprehensive user guide covers all aspects of using the Deep Research MCP system. For additional help, use the `--help` flag or check the troubleshooting documentation.