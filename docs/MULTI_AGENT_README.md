# Deep Research MCP - Documentation

## Overview

Welcome to the comprehensive documentation for the Deep Research MCP (Message Control Protocol) system. This multi-agent research platform uses LangGraph to orchestrate 8 specialized AI agents that work together to conduct thorough research on any topic and produce detailed reports in multiple formats and languages.

## Documentation Structure

### Core Documentation

1. **[API Reference](API_REFERENCE.md)** - Complete API documentation
   - MCP server endpoints
   - Agent classes and methods
   - Utility functions
   - Configuration options
   - Provider system details

2. **[User Guide](USER_GUIDE.md)** - Comprehensive usage instructions
   - Quick start guide
   - Installation procedures
   - Basic and advanced usage
   - CLI interface documentation
   - Multi-provider configuration
   - Translation features
   - Output formats and customization

3. **[Configuration Guide](CONFIGURATION.md)** - Complete configuration reference
   - Environment setup
   - Provider configuration (LLM and search)
   - Language settings
   - Task customization
   - Performance tuning
   - Security configuration

4. **[Deployment Guide](DEPLOYMENT.md)** - Production deployment strategies
   - Infrastructure requirements
   - Deployment methods (Docker, Kubernetes, Cloud)
   - Monitoring and logging
   - Backup and recovery
   - Maintenance procedures
   - Scaling strategies

5. **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Problem resolution
   - Common issues and solutions
   - Installation problems
   - API and provider issues
   - Performance optimization
   - Diagnostic tools
   - FAQ section

## Quick Navigation

### Getting Started
- [Installation Instructions](USER_GUIDE.md#installation)
- [Quick Start Demo](USER_GUIDE.md#quick-start)
- [Basic Usage Examples](USER_GUIDE.md#basic-usage)

### Configuration
- [Environment Setup](CONFIGURATION.md#environment-configuration)
- [Provider Configuration](CONFIGURATION.md#provider-configuration)
- [Language Settings](CONFIGURATION.md#language-configuration)

### Development
- [API Reference](API_REFERENCE.md)
- [Agent Architecture](API_REFERENCE.md#core-agents)
- [Custom Integration](USER_GUIDE.md#customization)

### Deployment
- [Production Setup](DEPLOYMENT.md#production-configuration)
- [Docker Deployment](DEPLOYMENT.md#method-2-docker-deployment)
- [Monitoring Setup](DEPLOYMENT.md#monitoring-and-logging)

### Support
- [Common Issues](TROUBLESHOOTING.md#common-issues)
- [Performance Problems](TROUBLESHOOTING.md#performance-problems)
- [FAQ](TROUBLESHOOTING.md#frequently-asked-questions)

## Architecture Overview

### Multi-Agent System
The system employs 8 specialized agents working in a coordinated workflow:

1. **Browser Agent**: Initial web research and topic exploration
2. **Editor Agent**: Research planning and structure organization
3. **Researcher Agent**: Detailed research on specific sections (parallel)
4. **Writer Agent**: Report compilation with introduction and conclusion
5. **Publisher Agent**: Multi-format export (PDF, DOCX, Markdown)
6. **Translator Agent**: Professional translation with formatting preservation
7. **Reviewer Agent**: Quality assurance and feedback generation
8. **Reviser Agent**: Content improvement based on review feedback

### Key Features

#### Multi-Provider Support
- **LLM Providers**: OpenAI, Google Gemini, Anthropic, Azure OpenAI
- **Search Providers**: Tavily, Brave Search, Google, DuckDuckGo, SerpAPI
- **Automatic Failover**: Seamless switching between providers
- **Cost Optimization**: Choose providers based on performance and cost

#### Advanced Translation
- **Multiple Languages**: Support for 50+ languages
- **Quality Assurance**: Post-translation review and revision workflow
- **Formatting Preservation**: Maintains markdown structure and formatting
- **Multiple Endpoints**: Failover translation services
- **Multi-format Output**: Translated PDF, DOCX, and Markdown files

#### Professional Output
- **Multiple Formats**: PDF, DOCX, Markdown generation
- **High-Quality PDFs**: LaTeX-based rendering with proper formatting
- **Structured Reports**: Table of contents, citations, proper headings
- **Draft Management**: Complete workflow history and intermediate outputs

#### Enterprise Features
- **Scalable Architecture**: Horizontal and vertical scaling support
- **Monitoring Integration**: Prometheus metrics and health checks
- **Security Features**: API key management, rate limiting, content filtering
- **Backup Systems**: Automated backup and disaster recovery

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM (8GB recommended)
- **Storage**: 20GB free space
- **Network**: Stable internet connection

### Recommended Production Setup
- **CPU**: 8+ cores
- **Memory**: 16-32GB RAM
- **Storage**: 500GB+ SSD
- **Load Balancer**: For multi-instance deployments
- **Monitoring**: Prometheus + Grafana

## Quick Start

### 1. Installation
```bash
git clone <repository-url>
cd deep-research-mcp-og
pip install -r multi_agents/requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Research
```bash
python main.py --research "Your research question"
```

### 4. Access Results
```bash
ls outputs/  # Check generated files
```

## Integration Options

### MCP Integration
```python
# Via MCP client
result = await mcp_client.deep_research(
    query="Research question",
    tone="objective"
)
```

### Direct Python Integration
```python
from multi_agents.main import run_research_task

result = await run_research_task(
    query="Research question",
    language="vi",  # Vietnamese translation
    write_to_files=True
)
```

### CLI Interface
```bash
# Interactive mode
python main.py

# Single query
python main.py --research "Question" --tone critical
```

### REST API
```bash
curl -X POST http://localhost:8080/research \
  -H "Content-Type: application/json" \
  -d '{"query":"Research question","tone":"objective"}'
```

## Use Cases

### Academic Research
- Literature reviews and systematic analyses
- Research proposal development
- Comparative studies and meta-analyses
- Multi-language research documentation

### Business Intelligence
- Market research and competitive analysis
- Industry trend analysis
- Regulatory compliance research
- Investment due diligence

### Content Creation
- In-depth articles and whitepapers
- Technical documentation
- Educational materials
- Multi-language content production

### Consulting and Advisory
- Client research reports
- Policy analysis and recommendations
- Technology assessments
- Strategic planning research

## Support and Community

### Getting Help
1. **Documentation**: Start with the relevant guide above
2. **Troubleshooting**: Check the [troubleshooting guide](TROUBLESHOOTING.md)
3. **Issues**: Create an issue in the repository
4. **Discussions**: Join community discussions

### Contributing
- **Bug Reports**: Use the issue tracker
- **Feature Requests**: Propose new features via issues
- **Code Contributions**: Fork, develop, and submit pull requests
- **Documentation**: Help improve documentation

### License and Usage
- Review the license file for usage terms
- Commercial licensing available for enterprise use
- Community support via GitHub discussions
- Professional support options available

## Version Information

**Current Version**: See repository tags for latest version

### Release Notes
- **Latest**: Enhanced translation quality assurance workflow
- **Previous**: Multi-provider support and configuration improvements
- **Historical**: Check repository releases for complete changelog

### Roadmap
- Advanced citation management
- Custom template support
- Enhanced visualization capabilities
- Multi-modal research (images, videos)
- Real-time collaboration features

## Additional Resources

### External Dependencies
- **LangGraph**: Multi-agent workflow orchestration
- **GPT-Researcher**: Core research capabilities
- **Pandoc**: Document conversion
- **LaTeX**: High-quality PDF generation

### Related Projects
- **FastMCP**: MCP server framework
- **GPT-Researcher**: Research automation library
- **LangChain**: LLM application framework

### Learning Resources
- **LangGraph Documentation**: Understanding agent workflows
- **MCP Specification**: Message Control Protocol details
- **Provider APIs**: Documentation for LLM and search providers

---

This documentation is actively maintained and updated. For the most current information, always refer to the latest version in the repository.