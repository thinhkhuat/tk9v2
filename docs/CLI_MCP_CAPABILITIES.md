# Deep Research MCP - Complete CLI & MCP Capabilities Documentation

## Table of Contents
1. [Overview](#overview)
2. [CLI Interface](#cli-interface)
3. [MCP Server](#mcp-server)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)
7. [Integration Guide](#integration-guide)

---

## Overview

The Deep Research MCP system provides two powerful interfaces for conducting AI-powered research:

1. **CLI (Command Line Interface)**: Interactive and batch research execution
2. **MCP (Model Context Protocol) Server**: Integration with Claude Desktop and other MCP clients

Both interfaces leverage the same underlying multi-agent research engine with 9 specialized AI agents.

---

## CLI Interface

### Command Structure

```bash
python main.py [OPTIONS]
```

### Available Options

| Option | Short | Description | Values | Default |
|--------|-------|-------------|---------|---------|
| `--research` | `-r` | Run a single research query and exit | Any text query | None |
| `--tone` | `-t` | Set research tone | objective, critical, optimistic, balanced, skeptical | objective |
| `--language` | `-l` | Output language | en, vi, es, fr, de, zh, ja, ko, pt, it, ru, ar, hi, th | en |
| `--interactive` | `-i` | Start interactive chat mode | Flag | True if no args |
| `--config` | `-c` | Show current configuration | Flag | False |
| `--verbose` | `-v` | Enable verbose output | Flag | False |
| `--save-files` | `-s` | Save research reports to files | Flag | True |
| `--no-save-files` | | Don't save reports to files | Flag | False |
| `--provider-info` | | Show provider configuration | Flag | False |

### CLI Modes

#### 1. Interactive Mode (Default)
Launches when no arguments are provided or with `--interactive`

```bash
python main.py
# or
python main.py --interactive
```

**Features:**
- Chat-style interface for continuous research
- Session history within the same run
- Real-time progress updates
- Command system with special commands
- Persistent configuration for the session

**Interactive Commands:**
- `/help` - Show available commands
- `/config` - Display current configuration
- `/history` - Show research history for session
- `/clear` - Clear screen
- `/quit` or `/exit` - Exit interactive mode
- Regular text - Treated as research query

#### 2. Single Query Mode
Execute one research task and exit

```bash
python main.py --research "Your research question here"
```

**Options can be combined:**
```bash
python main.py --research "Climate change impacts" --tone critical --language vi --verbose
```

#### 3. Configuration Display Mode
Show current system configuration

```bash
python main.py --config
```

**Displays:**
- Task configuration from `task.json`
- Environment variables
- Provider settings
- Language settings
- Output format settings

#### 4. Provider Information Mode
Display provider status and configuration

```bash
python main.py --provider-info
```

**Shows:**
- Available LLM providers and their status
- Available search providers and their status
- Current primary/fallback configurations
- API key presence (masked)
- Model availability

### Output Management

#### File Output Structure
When `--save-files` is enabled (default):

```
outputs/
└── run_TIMESTAMP_query_preview/
    ├── research_report.md         # Markdown report
    ├── research_report.pdf        # PDF version
    ├── research_report.docx       # Word document
    ├── research_report_[lang].md  # Translated markdown
    ├── research_report_[lang].pdf # Translated PDF
    ├── research_report_[lang].docx # Translated Word
    └── drafts/                    # Workflow history
        ├── initial_research.json
        ├── outline.json
        ├── sections/
        └── revisions/
```

#### Console Output
- **Default Mode**: Concise progress indicators
- **Verbose Mode** (`-v`): Detailed agent activity logs
- **Real-time Updates**: Live progress from each agent
- **Color-coded**: Different colors for different agent stages

### Language Support

#### Supported Languages (14)
- `en` - English
- `vi` - Vietnamese
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `pt` - Portuguese
- `it` - Italian
- `ru` - Russian
- `ar` - Arabic
- `hi` - Hindi
- `th` - Thai

#### Language Configuration
```bash
# Set language via command line
python main.py -r "AI trends" -l vi

# Set via environment variable
export RESEARCH_LANGUAGE=vi
python main.py -r "AI trends"
```

### Research Tones

| Tone | Description | Use Case |
|------|-------------|----------|
| `objective` | Neutral, fact-based | Academic research, documentation |
| `critical` | Analytical, questioning | Technology reviews, analysis |
| `optimistic` | Positive, forward-looking | Vision documents, proposals |
| `balanced` | Multiple perspectives | Comprehensive reports |
| `skeptical` | Cautious, questioning | Risk assessment, validation |

---

## MCP Server

### Overview
The MCP server (`mcp_server.py`) exposes the research capabilities via the Model Context Protocol, allowing integration with Claude Desktop and other MCP-compatible clients.

### Server Configuration

```python
# Server initialization
mcp = FastMCP("Deep Research")
```

### Available Tools

#### `deep_research` Tool

**Function Signature:**
```python
async def deep_research(
    query: str, 
    tone: str = "objective",
    ctx: Context = None
) -> Dict[Any, Any]
```

**Parameters:**
- `query` (required): The research question or topic to investigate
- `tone` (optional): Research tone (objective, critical, optimistic, balanced, skeptical)
- `ctx` (optional): MCP context for progress reporting

**Returns:**
```json
{
    "status": "success|error",
    "query": "original query",
    "tone": "selected tone",
    "report": {
        "title": "Research Title",
        "sections": [...],
        "conclusion": "...",
        "sources": [...]
    }
}
```

### MCP Integration

#### With Claude Desktop

1. **Add to Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "deep-research": {
      "command": "python",
      "args": ["/path/to/deep-research-mcp-og/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key",
        "TAVILY_API_KEY": "your-key"
      }
    }
  }
}
```

2. **Use in Claude Desktop:**
```
Use the deep_research tool to investigate "quantum computing applications in healthcare"
```

#### Progress Reporting
The MCP server reports progress through the context:
- Log messages via `ctx.info()`
- Progress percentage via `ctx.report_progress()`
- Real-time streaming of agent activities

### Starting the MCP Server

```bash
# Direct execution
python mcp_server.py

# Or via MCP client
mcp run deep-research
```

---

## Configuration

### Environment Variables

#### Essential Variables
```bash
# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Search Providers (at least one required)
TAVILY_API_KEY=tvly-...
BRAVE_API_KEY=...

# Provider Selection
PRIMARY_LLM_PROVIDER=openai
PRIMARY_SEARCH_PROVIDER=tavily

# Language Settings
RESEARCH_LANGUAGE=en
```

#### Optional Variables
```bash
# Fallback Providers
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_SEARCH_PROVIDER=brave

# Provider Strategies
LLM_STRATEGY=primary_only|fallback_on_error|round_robin
SEARCH_STRATEGY=primary_only|fallback_on_error|round_robin

# Model Selection
PRIMARY_LLM_MODEL=gpt-4o
```

### Task Configuration (task.json)

```json
{
    "query": "Default research query",
    "max_sections": 5,
    "publish_formats": ["pdf", "docx", "markdown"],
    "follow_guidelines": true,
    "guidelines": [
        "Focus on recent developments (2023-2024)",
        "Include statistical data",
        "Provide balanced perspectives"
    ],
    "model": "gpt-4o",
    "include_human_feedback": false,
    "language": "en",
    "tone": "objective",
    "verbose": false
}
```

---

## Usage Examples

### CLI Examples

#### Basic Research
```bash
# Simple research
python main.py -r "What are the latest developments in quantum computing?"

# With specific tone
python main.py -r "AI impact on employment" -t critical

# In Vietnamese with verbose output
python main.py -r "Climate change solutions" -l vi -v

# Without saving files (console only)
python main.py -r "Quick fact check on solar energy" --no-save-files
```

#### Interactive Session
```bash
$ python main.py

Welcome to Deep Research CLI!
Type '/help' for commands or enter your research query.

> What are the benefits of meditation?
[Browser Agent] Starting initial research...
[Editor Agent] Planning report structure...
[Researcher Agent] Conducting parallel research...
[Writer Agent] Compiling final report...
[Publisher Agent] Generating output formats...
Research complete! Files saved to: outputs/run_20250830_142531_meditation/

> /history
1. What are the benefits of meditation? [Completed]

> /quit
Goodbye!
```

#### Configuration Check
```bash
$ python main.py --config

Current Configuration:
----------------------
Task Settings:
  Max Sections: 5
  Output Formats: pdf, docx, markdown
  Language: en
  Tone: objective

Provider Configuration:
  Primary LLM: openai (gpt-4o)
  Primary Search: tavily
  Fallback LLM: google_gemini
  Fallback Search: brave
```

### MCP Usage Examples

#### In Claude Desktop
```
Human: Can you research the environmental impact of electric vehicles using the deep research tool?

Claude: I'll research the environmental impact of electric vehicles for you.

[Uses deep_research tool with query="environmental impact of electric vehicles"]

Based on my comprehensive research using multiple AI agents, here's what I found...
```

#### Programmatic MCP Usage
```python
# Python client example
from mcp.client import MCPClient

client = MCPClient("deep-research")
result = await client.call_tool(
    "deep_research",
    {
        "query": "blockchain applications in supply chain",
        "tone": "balanced"
    }
)
```

---

## Best Practices

### CLI Best Practices

#### 1. Query Formulation
- **Be Specific**: "Impact of AI on healthcare diagnostics in 2024" vs "AI in healthcare"
- **Include Context**: Add relevant context for better research
- **Avoid Ambiguity**: Clear, unambiguous questions get better results

#### 2. Tone Selection
- Use `objective` for factual research
- Use `critical` when you need deep analysis
- Use `balanced` for comprehensive coverage
- Use `skeptical` for risk assessment
- Use `optimistic` for vision/strategy documents

#### 3. Language Considerations
- Research is conducted in English, then translated
- For best results in non-English, be explicit about regional context
- Translation preserves formatting and structure

#### 4. Performance Optimization
- Use `--no-save-files` for quick queries
- Enable `--verbose` only when debugging
- Run multiple queries in interactive mode to save startup time

#### 5. File Management
- Research outputs are timestamped and organized
- Clean up old outputs periodically
- PDF generation requires Pandoc/LaTeX installation

### MCP Best Practices

#### 1. Configuration
- Keep API keys in environment variables, never in config files
- Set reasonable timeouts for long research tasks
- Configure both primary and fallback providers

#### 2. Integration
- Use progress callbacks for user feedback
- Handle errors gracefully
- Implement retry logic for network failures

#### 3. Resource Management
- MCP server runs one research task at a time
- Consider queuing for multiple requests
- Monitor API usage and costs

---

## Advanced Usage

### Batch Processing
```bash
# Create a research queue file
cat > research_queue.txt << EOF
What are the latest breakthroughs in cancer research?
How is AI being used in climate change mitigation?
What are the economic impacts of remote work?
EOF

# Process batch (requires custom script)
while read query; do
    python main.py -r "$query" --tone objective
    sleep 5  # Avoid rate limits
done < research_queue.txt
```

### Custom Guidelines
Edit `task.json` to set custom research guidelines:
```json
{
    "guidelines": [
        "Focus on peer-reviewed sources",
        "Include recent case studies",
        "Provide actionable recommendations",
        "Compare multiple viewpoints"
    ]
}
```

### Provider Switching
```bash
# Use specific providers
export PRIMARY_LLM_PROVIDER=google_gemini
export PRIMARY_SEARCH_PROVIDER=brave
python main.py -r "Your query"

# Test failover
export LLM_STRATEGY=fallback_on_error
export FALLBACK_LLM_PROVIDER=anthropic
```

### Output Customization
```bash
# Markdown only
edit task.json  # Set publish_formats: ["markdown"]

# Research without translation
python main.py -r "Query" -l en  # Keep in English

# Debug mode
export DEBUG=true
python main.py -r "Query" -v
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No API keys found" | Set environment variables for at least one LLM and search provider |
| "Import error: cli module not found" | Ensure you're running from project root directory |
| "PDF generation failed" | Install Pandoc: `brew install pandoc` |
| "Translation timeout" | Check translation endpoint configuration |
| "MCP server won't start" | Verify Python path and FastMCP installation |

### Debug Commands
```bash
# Check configuration
python main.py --config

# Verify providers
python main.py --provider-info

# Test with minimal query
python main.py -r "test" --no-save-files

# Enable all logging
export DEBUG=true
export VERBOSE=true
python main.py -r "test" -v
```

---

## Integration Guide

### Integrating with Your Application

#### Python Integration
```python
import asyncio
from multi_agents.main import run_research_task

async def conduct_research(query: str):
    result = await run_research_task(
        query=query,
        tone="objective",
        write_to_files=True
    )
    return result

# Run research
result = asyncio.run(conduct_research("Your research question"))
```

#### Shell Script Integration
```bash
#!/bin/bash
# research.sh - Wrapper script for research tasks

QUERY="$1"
TONE="${2:-objective}"
LANG="${3:-en}"

python /path/to/main.py \
    --research "$QUERY" \
    --tone "$TONE" \
    --language "$LANG" \
    --save-files
```

#### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run Research Report
  run: |
    python main.py --research "${{ inputs.query }}" \
      --tone objective \
      --no-save-files
```

---

## Summary

The Deep Research MCP system provides two robust interfaces:

1. **CLI**: Perfect for interactive research, batch processing, and direct command-line usage
2. **MCP Server**: Ideal for integration with Claude Desktop and programmatic access

Both interfaces offer:
- ✅ Multi-agent orchestration (9 specialized agents)
- ✅ Multi-language support (14 languages)
- ✅ Multiple output formats (PDF, DOCX, Markdown)
- ✅ Configurable research tones
- ✅ Provider failover support
- ✅ Real-time progress tracking
- ✅ Comprehensive error handling

The system is production-ready, well-documented, and provides all necessary capabilities without requiring additional web UI complexity.