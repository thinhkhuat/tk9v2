# Deep Research MCP - CLI Quick Reference Card

## 🚀 Quick Start

```bash
# Interactive mode (default)
python main.py

# Single research query
python main.py -r "Your research question"

# Research with options
python main.py -r "AI impacts" -t critical -l vi -v
```

## 📋 Command Options

| Option | Short | Example | Description |
|--------|-------|---------|-------------|
| `--research` | `-r` | `-r "AI trends"` | Run single query |
| `--tone` | `-t` | `-t critical` | Set tone |
| `--language` | `-l` | `-l vi` | Output language |
| `--verbose` | `-v` | `-v` | Detailed output |
| `--config` | `-c` | `-c` | Show config |
| `--no-save-files` | | `--no-save-files` | Console only |
| `--provider-info` | | `--provider-info` | Provider status |

## 🎭 Available Tones

- `objective` - Neutral, factual (default)
- `critical` - Analytical, questioning
- `optimistic` - Positive outlook
- `balanced` - Multiple perspectives
- `skeptical` - Cautious analysis

## 🌍 Supported Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `ja` | Japanese |
| `vi` | Vietnamese | `ko` | Korean |
| `es` | Spanish | `pt` | Portuguese |
| `fr` | French | `it` | Italian |
| `de` | German | `ru` | Russian |
| `zh` | Chinese | `ar` | Arabic |
| `hi` | Hindi | `th` | Thai |

## 💬 Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/config` | Display configuration |
| `/history` | Show session history |
| `/clear` | Clear screen |
| `/quit` or `/exit` | Exit interactive mode |
| Any text | Treated as research query |

## 🔧 Essential Environment Variables

```bash
# Required (at least one of each)
export OPENAI_API_KEY=sk-...
export TAVILY_API_KEY=tvly-...

# Optional
export PRIMARY_LLM_PROVIDER=openai
export PRIMARY_SEARCH_PROVIDER=tavily
export RESEARCH_LANGUAGE=en
```

## 📁 Output Structure

```
outputs/
└── run_TIMESTAMP_query/
    ├── research_report.md
    ├── research_report.pdf
    ├── research_report.docx
    └── research_report_[lang].*  # If translated
```

## 🎯 Common Use Cases

```bash
# Academic research
python main.py -r "Latest CRISPR developments 2024" -t objective

# Critical analysis
python main.py -r "Social media impact on democracy" -t critical

# Business research
python main.py -r "Remote work productivity trends" -t balanced

# Quick lookup (no files)
python main.py -r "Python vs JavaScript 2024" --no-save-files

# Non-English output
python main.py -r "Climate change solutions" -l vi

# Debug mode
python main.py -r "Test query" -v

# Check setup
python main.py --config
python main.py --provider-info
```

## 🔌 MCP Server Usage

### Start Server
```bash
python mcp_server.py
```

### Claude Desktop Config
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "deep-research": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

## ⚡ Performance Tips

1. Use `--no-save-files` for quick queries
2. Run interactive mode for multiple queries
3. Set `PRIMARY_LLM_PROVIDER` for consistency
4. Use specific tones for better results
5. Be specific in your queries

## 🚨 Troubleshooting

```bash
# Test minimal setup
python main.py -r "test" --no-save-files

# Check configuration
python main.py --config

# Verify providers
python main.py --provider-info

# Enable debug logging
export DEBUG=true
python main.py -r "test" -v
```

## 📚 More Information

- Full documentation: `docs/CLI_MCP_CAPABILITIES.md`
- Configuration guide: `docs/MULTI_AGENT_CONFIGURATION.md`
- API reference: `docs/MULTI_AGENT_API_REFERENCE.md`