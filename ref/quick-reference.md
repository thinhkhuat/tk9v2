# Quick Reference Guide

## 🚀 Quick Start (30 seconds)

```bash
# Clone and setup
git clone <repo-url> && cd deep-research-mcp-og
pip install -r multi_agents/requirements.txt
cp .env.example .env && nano .env  # Add API keys

# Run research
python main.py --research "Your research question"
```

## 📋 Essential Commands

### Running Research
```bash
# Interactive mode
python main.py

# Single query
python main.py --research "Climate change impacts"

# With options
python main.py --research "AI developments" --language vi --tone critical --verbose

# Without file saving
python main.py --research "Quick query" --no-save-files

# Show configuration
python main.py --config
python main.py --provider-info
```

### MCP Server
```bash
# Start MCP server
python mcp_server.py

# Test MCP endpoint
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"query":"Test query"}'
```

### Testing
```bash
# Quick test
python -m pytest tests/unit/ -v

# Full test suite
python -m pytest tests/ -v

# Provider test
python tests/test_providers.py
```

## ⚙️ Minimal Configuration

### Required Environment Variables (.env)
```bash
# Option 1: Google Gemini + BRAVE (Recommended)
GOOGLE_API_KEY=your-key
BRAVE_API_KEY=your-key
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_SEARCH_PROVIDER=brave

# Option 2: OpenAI + Tavily
OPENAI_API_KEY=sk-your-key
TAVILY_API_KEY=tvly-your-key
PRIMARY_LLM_PROVIDER=openai
PRIMARY_SEARCH_PROVIDER=tavily
```

### BRAVE Search Setup (if using BRAVE)
```bash
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local
```

## 🏗️ Project Structure

```
deep-research-mcp-og/
├── mcp_server.py           # MCP server entry point
├── main.py                 # CLI interface
├── multi_agents/           # Core multi-agent system
│   ├── main.py            # Multi-agent entry point
│   ├── agents/            # 9 specialized agents
│   ├── providers/         # LLM & search providers
│   ├── config/            # Configuration files
│   ├── memory/            # State management
│   └── task.json          # Task configuration
├── cli/                   # CLI components
├── tests/                 # Test suite
├── outputs/               # Generated reports
└── ref/                   # Reference documentation
```

## 🤖 Agent Quick Reference

| Agent | Purpose | Duration | Key Output |
|-------|---------|----------|------------|
| **Browser** | Initial web research | 10-30s | Search results & URLs |
| **Editor** | Report structure planning | 5-15s | Detailed outline |
| **Researcher** | Deep section research | 30-120s | Research data & citations |
| **Writer** | Report compilation | 20-40s | Complete markdown report |
| **Publisher** | Multi-format export | 10-30s | PDF, DOCX, MD files |
| **Translator** | Language translation | 30-60s | Translated report |
| **Reviewer** | Quality assurance | 10-20s | Review feedback |
| **Reviser** | Final corrections | 10-20s | Polished report |
| **Human** | Manual feedback | Variable | User corrections |

## 🔧 Provider Quick Setup

### LLM Providers

| Provider | Env Variable | Model Examples |
|----------|-------------|----------------|
| **OpenAI** | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| **Google** | `GOOGLE_API_KEY` | gemini-2.5-flash-preview-04-17-thinking |
| **Anthropic** | `ANTHROPIC_API_KEY` | claude-3-sonnet |
| **Azure** | `AZURE_OPENAI_KEY` | gpt-4, gpt-3.5-turbo |

### Search Providers

| Provider | Env Variable | Special Config |
|----------|-------------|----------------|
| **BRAVE** | `BRAVE_API_KEY` | `RETRIEVER=custom` |
| **Tavily** | `TAVILY_API_KEY` | None |
| **Google** | `GOOGLE_SEARCH_API_KEY` | `GOOGLE_SEARCH_ENGINE_ID` |
| **DuckDuckGo** | None | No API key needed |
| **SerpAPI** | `SERPAPI_KEY` | None |

## 📁 Output Structure

```
outputs/
└── run_20240101_120000_your_research/
    ├── research_report.pdf       # Professional PDF
    ├── research_report.docx      # Editable Word doc
    ├── research_report.md        # Markdown source
    ├── research_report_vi.pdf    # Translated (if configured)
    └── drafts/                   # Workflow history
```

## 🎯 Common Use Cases

### Academic Research
```bash
python main.py --research "Machine learning in healthcare 2024" --tone critical
```

### Business Analysis
```bash
python main.py --research "EV market Southeast Asia" --tone balanced
```

### Technical Documentation
```bash
python main.py --research "React vs Vue performance" --tone objective
```

### Multi-language Report
```bash
python main.py --research "Renewable energy" --language vi --tone optimistic
```

## 🔍 CLI Commands

### Interactive Mode Commands
- `/help` - Show available commands
- `/config` - Display current configuration
- `/history` - Show research history
- `/clear` - Clear screen
- `/quit` - Exit application

## 🚨 Troubleshooting

### Provider Issues
```bash
# Check API keys
grep "API_KEY" .env

# Test provider
python main.py --provider-info

# Use fallback
export LLM_STRATEGY=fallback_on_error
```

### BRAVE Search Issues
```bash
# Verify configuration
echo $RETRIEVER  # Should be "custom"
echo $RETRIEVER_ENDPOINT  # Should be "https://brave-local-provider.local"

# Test API
curl -H "X-Subscription-Token: $BRAVE_API_KEY" \
  "https://api.search.brave.com/res/v1/web/search?q=test"
```

### File Output Issues
```bash
# Check permissions
ls -la outputs/

# Install PDF dependencies
brew install pandoc
brew install --cask basictex
```

## 📊 Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| **Startup Time** | < 3s | < 2s ✅ |
| **Memory Usage** | < 200MB | 163.4MB ✅ |
| **Total Research Time** | < 5min | 2-4min ✅ |
| **Test Pass Rate** | > 85% | 89% ✅ |

## 🔑 Environment Variables

### Essential
- `PRIMARY_LLM_PROVIDER` - Main LLM provider
- `PRIMARY_SEARCH_PROVIDER` - Main search provider
- `[PROVIDER]_API_KEY` - API keys for providers

### Optional
- `LLM_STRATEGY` - Failover strategy (primary_only, fallback_on_error)
- `RESEARCH_LANGUAGE` - Default translation language
- `ENABLE_STREAMING` - Real-time progress updates
- `WORKFLOW_DEBUG` - Debug mode

## 📚 Documentation Links

### Reference Docs
- [Agent Reference](agents.md) - Detailed agent documentation
- [Provider Reference](providers.md) - Provider configuration
- [Workflow Reference](workflow.md) - Workflow architecture

### User Docs
- [User Guide](../docs/MULTI_AGENT_USER_GUIDE.md)
- [API Reference](../docs/MULTI_AGENT_API_REFERENCE.md)
- [Configuration Guide](../docs/MULTI_AGENT_CONFIGURATION.md)
- [Deployment Guide](../docs/MULTI_AGENT_DEPLOYMENT.md)
- [Troubleshooting](../docs/MULTI_AGENT_TROUBLESHOOTING.md)

## 💡 Tips & Tricks

### Performance
- Use `--no-save-files` for quick queries
- Enable parallel research for faster results
- Cache responses with same queries
- Use lighter models for drafts

### Quality
- Set specific guidelines in task.json
- Enable review stage for critical research
- Use multiple search providers for comprehensive results
- Configure appropriate tone for audience

### Development
- Use `--verbose` for debugging
- Check logs in `workflow.log`
- Test with `primary_only` strategy first
- Monitor provider costs regularly

## 🆘 Getting Help

```bash
# Show help
python main.py --help

# Interactive help
python main.py
> /help

# Check configuration
python main.py --config

# Provider status
python main.py --provider-info
```

## 🎉 Success Indicators

✅ **Working Setup**:
- API keys configured correctly
- Providers connecting successfully
- Research completes without errors
- Output files generated in `outputs/`
- PDF/DOCX files open correctly

❌ **Common Issues**:
- Missing API keys → Check .env file
- Provider errors → Try fallback provider
- No output files → Check write permissions
- Translation fails → Verify language code
- PDF generation fails → Install pandoc/latex

## 🚦 Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 🟢 | Working | Continue |
| 🟡 | Warning | Check logs |
| 🔴 | Error | Check configuration |
| ⚪ | Pending | Wait |
| 🔵 | Info | Note for reference |

---

**Quick Help**: `python main.py --help` | **Docs**: `/ref/` | **Support**: GitHub Issues