# TK9 Deep Research MCP - Project Structure

This document provides the complete technology stack and file tree structure for the TK9 Deep Research MCP server. **AI agents MUST read this file to understand the project organization before making any changes.**

## Technology Stack

### Backend Technologies
- **Python 3.12/3.13** with **pip/uv** - Dependency management and packaging
- **FastAPI 0.116.0+** - Modern async web framework with type hints and auto-generated OpenAPI docs
- **FastMCP 0.9.0+** - Model Context Protocol server implementation
- **Uvicorn 0.25.0+** - ASGI server with standard extras for production deployment
- **Pydantic 2.5.0+** - Data validation and settings management with type safety

### AI & Multi-Agent Framework
- **LangGraph 0.0.20+** - Multi-agent workflow orchestration with state management
- **GPT-Researcher 0.14.1+** - Core research capabilities and document processing
- **LangChain 0.1.0+** - AI application framework for LLM integration
- **LangChain-Community 0.0.10+** - Community integrations and tools
- **LangChain-Google-GenAI 2.0.10+** - Google Gemini integration

### LLM Provider Integrations
- **OpenAI 1.12.0+** - OpenAI GPT models (GPT-4, GPT-3.5-turbo)
- **Google Generative AI 0.8.0+** - Google Gemini models (gemini-2.5-flash-preview, gemini-pro)
- **Anthropic 0.25.0+** - Claude models (Claude 3 Opus, Sonnet, Haiku)
- **Azure OpenAI** - Enterprise OpenAI deployment

### Search & Data Retrieval
- **BRAVE Search API** - Primary search provider (configured as custom retriever)
- **Tavily API** - Fallback search provider for web research
- **aiohttp 3.10.0+** - Async HTTP client for search requests
- **requests 2.31.0+** - Synchronous HTTP client for legacy integrations
- **BeautifulSoup4 4.12.0+** - HTML parsing and web scraping
- **lxml 4.9.0+** - Fast XML/HTML processing

### Document Processing & Export
- **Jinja2 3.1.0+** - Template engine for report generation
- **pypandoc 1.11+** - Universal document converter (Markdown → PDF/DOCX)
- **python-docx 1.1.0+** - Microsoft Word document generation
- **ReportLab 4.0.0+** - PDF generation library
- **WeasyPrint 60.0+** - HTML to PDF conversion with CSS support
- **Pandoc** (system dependency) - Universal document converter
- **LaTeX** (optional) - High-quality PDF rendering via BasicTeX

### Async & Performance
- **asyncio** (built-in) - Python's async I/O framework
- **nest-asyncio 1.6.0+** - Nested event loop support for complex workflows
- **asyncio-throttle 1.0.0+** - Rate limiting for API calls

### Configuration & Environment
- **python-dotenv** - Environment variable management from .env files
- **Pydantic Settings 2.5.2+** - Type-safe configuration with validation
- **json5** - Enhanced JSON parsing with comments and trailing commas

### Logging & Monitoring
- **loguru** - Structured logging with rotation and formatting
- **Custom monitoring** - Performance metrics and error tracking

### Web Dashboard (Real-time Monitoring)
- **FastAPI** - Dashboard backend API
- **WebSocket** - Real-time research progress updates
- **SSE (Server-Sent Events)** - One-way real-time notifications
- **Vanilla JavaScript** - Minimal frontend dependencies
- **Tailwind CSS** - Utility-first CSS framework

### Development & Quality Tools
- **pytest** - Testing framework for unit, integration, and e2e tests
- **black** - Code formatting with 88-character line length
- **flake8** - Code linting and style checking
- **mypy** - Static type checking for Python
- **pre-commit** - Git hooks for automated quality checks

### Deployment & Infrastructure
- **Docker** - Container packaging with multi-stage builds
- **Docker Compose** - Multi-container orchestration
- **Kubernetes** - Production-grade container orchestration
- **AWS Lambda** (optional) - Serverless deployment support
- **Caddy** - Reverse proxy with automatic HTTPS
- **Nginx** (alternative) - Traditional reverse proxy option

### Network & Security
- **SSL/TLS** - Certificate handling with special Vietnamese .gov.vn domain support
- **Network reliability patches** - Custom retry logic for unstable connections
- **Rate limiting** - API throttling and request management
- **CORS** - Cross-origin resource sharing configuration

## Complete Project Structure

```
tk9_source_deploy/
├── README.md                           # Project overview, features, and quick start
├── CLAUDE.md                           # Master AI context file with critical configuration
├── ARCHON.md                           # Archon MCP integration rules and workflow
├── .env                                # Environment variables and API keys (not committed)
├── .env.production                     # Production environment configuration
├── .gitignore                          # Git ignore patterns
├── requirements-prod.txt               # Production dependencies (minimal)
├── Dockerfile                          # Docker container configuration
├── docker-compose.yml                  # Multi-container orchestration
├── deploy.sh                           # Automated deployment script
├── test-deployment.sh                  # Deployment verification script
│
├── mcp_server.py                       # FastMCP server entry point (MCP mode)
├── main.py                             # CLI entry point (interactive/single-query mode)
├── serverless_handler.py               # AWS Lambda handler for serverless deployment
│
├── multi_agents/                       # Multi-agent research system core
│   ├── README.md                       # Multi-agent system overview
│   ├── requirements.txt                # Multi-agent dependencies
│   ├── task.json                       # Research task configuration
│   ├── main.py                         # Multi-agent workflow orchestration
│   ├── __init__.py                     # Package initialization
│   │
│   ├── agents/                         # 8 specialized AI agents
│   │   ├── __init__.py                 # Agent package initialization
│   │   ├── orchestrator.py             # ChiefEditorAgent - master coordinator
│   │   ├── editor.py                   # EditorAgent - research planning
│   │   ├── researcher.py               # ResearchAgent - data gathering (parallel)
│   │   ├── writer.py                   # WriterAgent - content synthesis
│   │   ├── publisher.py                # PublisherAgent - format generation (PDF/DOCX/MD)
│   │   ├── translator.py               # TranslatorAgent - multi-language translation
│   │   ├── reviewer.py                 # ReviewerAgent - quality assurance
│   │   ├── reviser.py                  # ReviserAgent - content refinement
│   │   ├── human.py                    # HumanAgent - human-in-the-loop feedback
│   │   │
│   │   └── utils/                      # Agent utilities and helpers
│   │       ├── __init__.py             # Utils package initialization
│   │       ├── utils.py                # General agent utilities
│   │       ├── llms.py                 # LLM interface and wrappers
│   │       ├── views.py                # Output formatting and display
│   │       ├── file_formats.py         # Document format handlers (PDF/DOCX/MD)
│   │       ├── fact_checker.py         # Research validation and fact-checking
│   │       ├── date_context.py         # Temporal context for research queries
│   │       └── type_safety.py          # Type checking and validation utilities
│   │
│   ├── config/                         # Configuration management
│   │   ├── __init__.py                 # Config package initialization
│   │   ├── providers.py                # Multi-provider configuration (LLM + Search)
│   │   └── settings.py                 # Application settings with Pydantic
│   │
│   ├── providers/                      # Provider abstraction layer
│   │   ├── __init__.py                 # Provider package initialization
│   │   ├── base.py                     # Base provider interfaces
│   │   │
│   │   ├── llm/                        # LLM provider implementations
│   │   │   ├── __init__.py             # LLM providers initialization
│   │   │   ├── openai.py               # OpenAI GPT provider
│   │   │   ├── enhanced_gemini.py      # Google Gemini provider with enhancements
│   │   │   ├── anthropic.py            # Anthropic Claude provider
│   │   │   └── azure_openai.py         # Azure OpenAI provider
│   │   │
│   │   └── search/                     # Search provider implementations
│   │       ├── __init__.py             # Search providers initialization
│   │       ├── brave.py                # BRAVE Search provider (primary)
│   │       ├── tavily.py               # Tavily Search provider (fallback)
│   │       ├── google.py               # Google Search provider
│   │       └── duckduckgo.py           # DuckDuckGo Search provider
│   │
│   ├── memory/                         # State and memory management
│   │   ├── __init__.py                 # Memory package initialization
│   │   ├── research.py                 # Research state tracking
│   │   ├── draft.py                    # Draft versioning and history
│   │   └── session.py                  # Session state management
│   │
│   ├── retrievers/                     # Custom search retrievers
│   │   ├── __init__.py                 # Retrievers initialization
│   │   ├── brave_retriever.py          # BRAVE Search custom retriever
│   │   └── base_retriever.py           # Base retriever interface
│   │
│   ├── utils/                          # System-wide utilities
│   │   ├── __init__.py                 # Utils initialization
│   │   ├── logging.py                  # Structured logging configuration
│   │   ├── validation.py               # Input validation utilities
│   │   └── helpers.py                  # General helper functions
│   │
│   ├── outputs/                        # Research output storage
│   │   └── run_[timestamp]_[query]/    # Individual research run outputs
│   │       ├── [id].md                 # Final report (Markdown)
│   │       ├── [id]_vi.md              # Translated report (if configured)
│   │       └── drafts/                 # Complete workflow history
│   │           ├── WORKFLOW_SUMMARY.md # Workflow execution summary
│   │           ├── 1_browsing/         # Browser agent outputs
│   │           ├── 2_planning/         # Editor agent outputs
│   │           ├── 3_research/         # Researcher agent outputs
│   │           ├── 4_writing/          # Writer agent outputs
│   │           ├── 5_reviewing/        # Reviewer agent outputs
│   │           ├── 6_revision/         # Reviser agent outputs
│   │           └── 7_publishing/       # Publisher agent outputs
│   │
│   ├── suppress_alts_warnings.py       # Suppress Google gRPC ALTS warnings
│   ├── direct_timeout_patch.py         # Direct timeout handling for APIs
│   ├── network_reliability_patch.py    # Enhanced SSL and retry logic
│   └── text_processing_fix.py          # Text chunking and processing fixes
│
├── web_dashboard/                      # Real-time web dashboard
│   ├── README.md                       # Dashboard overview and usage
│   ├── main.py                         # FastAPI dashboard server
│   ├── cli_executor.py                 # Research execution handler
│   ├── models.py                       # Pydantic models for dashboard
│   ├── file_manager.py                 # File management and serving
│   ├── file_manager_enhanced.py        # Enhanced file operations with streaming
│   ├── websocket_handler.py            # WebSocket connection management
│   ├── start_dashboard.sh              # Dashboard startup script
│   ├── requirements.txt                # Dashboard dependencies
│   │
│   ├── static/                         # Static assets
│   │   ├── css/                        # Stylesheets
│   │   │   ├── dashboard.css           # Main dashboard styles
│   │   │   └── enhanced-downloads.css  # Download manager styles
│   │   └── js/                         # JavaScript
│   │       ├── dashboard.js            # Main dashboard logic
│   │       └── enhanced-downloads.js   # Download manager logic
│   │
│   └── templates/                      # HTML templates
│       └── index.html                  # Dashboard main page
│
├── cli/                                # Command-line interface
│   ├── __init__.py                     # CLI package initialization
│   ├── commands.py                     # CLI command implementations
│   ├── prompts.py                      # Interactive prompts and UI
│   └── utils.py                        # CLI utilities
│
├── patches/                            # System-level patches
│   ├── README.md                       # Patches documentation
│   └── gpt_researcher_dimension_fix.py # CSS dimension parsing fix
│
├── tests/                              # Comprehensive test suite
│   ├── __init__.py                     # Test package initialization
│   ├── conftest.py                     # Pytest configuration and fixtures
│   │
│   ├── unit/                           # Unit tests (fast, isolated)
│   │   ├── __init__.py
│   │   ├── test_agents.py              # Agent logic tests
│   │   ├── test_providers.py           # Provider implementation tests
│   │   ├── test_memory.py              # Memory system tests
│   │   └── test_utils.py               # Utility function tests
│   │
│   ├── integration/                    # Integration tests (component interaction)
│   │   ├── __init__.py
│   │   ├── test_workflow.py            # Multi-agent workflow tests
│   │   ├── test_translation.py         # Translation pipeline tests
│   │   └── test_providers_failover.py  # Provider failover tests
│   │
│   ├── e2e/                            # End-to-end tests (full system)
│   │   ├── __init__.py
│   │   ├── test_cli.py                 # CLI interface tests
│   │   ├── test_mcp_server.py          # MCP server tests
│   │   └── test_research_flow.py       # Complete research flow tests
│   │
│   ├── fixtures/                       # Test data and fixtures
│   │   ├── __init__.py
│   │   ├── sample_queries.py           # Sample research queries
│   │   ├── mock_responses.py           # Mock API responses
│   │   └── test_data.json              # Static test data
│   │
│   └── mocks/                          # Mock objects for testing
│       ├── __init__.py
│       ├── mock_providers.py           # Mock LLM/Search providers
│       └── mock_agents.py              # Mock agent implementations
│
├── deploy/                             # Deployment configurations
│   ├── aws/                            # AWS deployment
│   │   ├── lambda/                     # Lambda configurations
│   │   ├── ecs/                        # ECS task definitions
│   │   └── cloudformation/             # CloudFormation templates
│   │
│   └── monitoring/                     # Monitoring and observability
│       ├── prometheus/                 # Prometheus configuration
│       ├── grafana/                    # Grafana dashboards
│       └── alerts/                     # Alert rules
│
├── docs/                               # Comprehensive documentation
│   ├── ai-context/                     # AI-specific documentation (Tier 1)
│   │   ├── project-structure.md        # THIS FILE - Complete tech stack and structure
│   │   ├── docs-overview.md            # Documentation architecture overview
│   │   ├── system-integration.md       # Cross-component integration patterns
│   │   ├── deployment-infrastructure.md # Deployment and infrastructure docs
│   │   └── handoff.md                  # Task management and session continuity
│   │
│   ├── MULTI_AGENT_USER_GUIDE.md       # Comprehensive user guide
│   ├── MULTI_AGENT_API_REFERENCE.md    # Complete API documentation
│   ├── MULTI_AGENT_CONFIGURATION.md    # Configuration options
│   ├── MULTI_AGENT_DEPLOYMENT.md       # Deployment guide
│   ├── MULTI_AGENT_TROUBLESHOOTING.md  # Common issues and solutions
│   ├── MULTI_PROVIDER_GUIDE.md         # Multi-provider setup guide
│   ├── MULTI_AGENT_BRAVE_SEARCH_INTEGRATION.md # BRAVE Search integration
│   ├── MULTI_AGENT_SYSTEM_DESIGN_ARCHITECTURE.md # System architecture
│   ├── MULTI_AGENT_SYSTEM_METHODOLOGY.md # Research methodology
│   ├── MULTI_AGENT_FRAMEWORK_BLUEPRINT.md # Framework design
│   ├── MULTI_AGENT_AI_ASSISTANT_GUIDE.md # AI assistant integration
│   ├── MULTI_AGENT_AI_DEVELOPMENT_GUIDE.md # Development guide
│   ├── MULTI_AGENT_PROVIDER_INTEGRATION_GUIDE.md # Provider integration
│   ├── MULTI_AGENT_DEBUGGING_TROUBLESHOOTING_GUIDE.md # Debug guide
│   ├── MULTI_AGENT_CODE_PATTERNS_SNIPPETS.md # Code patterns
│   ├── MULTI_AGENT_VALIDATION_CHECKLISTS.md # Validation checklists
│   ├── CLI_MCP_CAPABILITIES.md         # CLI and MCP capabilities
│   ├── CLI_QUICK_REFERENCE.md          # CLI command reference
│   ├── TRANSLATION_OPTIMIZATION.md     # Translation system optimization
│   ├── FACT_CHECKING_PROTOCOL.md       # Fact-checking methodology
│   └── CRITICAL_DIRECTIVES.md          # Critical development rules
│
├── ref/                                # Quick reference documentation
│   ├── quick-reference.md              # Commands, shortcuts, common operations
│   ├── agents.md                       # Detailed agent documentation
│   ├── providers.md                    # Provider system reference
│   ├── workflow.md                     # Complete workflow architecture
│   └── fact-checking.md                # Research validation reference
│
├── outputs/                            # Research output directory (CLI mode)
│   └── run_[timestamp]_[query]/        # Individual research runs
│
├── logs/                               # Application logs
│   ├── app.log                         # Main application log
│   ├── error.log                       # Error log
│   └── dashboard.log                   # Web dashboard log
│
├── ARCHIVE/                            # Deprecated code and backups
│   ├── webui-deprecated-20250905/      # Old web UI (replaced by dashboard)
│   └── backups/                        # Configuration backups
│
└── .serena/                            # Serena MCP server integration
    ├── cache/                          # Serena cache
    └── memories/                       # Serena memory storage
```

## Key Architecture Patterns

### 1. Multi-Agent Orchestration
- **ChiefEditorAgent** coordinates 8 specialized agents in a sequential workflow
- **LangGraph** manages state transitions and agent communication
- **Parallel Processing** for research sections (ResearchAgent runs multiple instances)
- **Human-in-the-Loop** optional feedback integration at review stage

### 2. Provider Abstraction
- **Multi-Provider System** supports OpenAI, Google Gemini, Anthropic, Azure OpenAI
- **Automatic Failover** switches providers on errors or rate limits
- **Strategy Pattern** for primary-only, fallback-on-error, or round-robin
- **Cost Optimization** route requests based on performance and budget

### 3. Memory & State Management
- **Research State** tracks current stage, completed sections, errors
- **Draft History** preserves complete workflow for debugging and auditing
- **Session Persistence** enables resumable long-running research tasks
- **Incremental Saves** protect against data loss during execution

### 4. Document Processing Pipeline
- **Multi-Format Output** generates PDF, DOCX, and Markdown simultaneously
- **Template-Based** uses Jinja2 for consistent formatting
- **LaTeX Rendering** for high-quality PDF generation
- **Citation Management** automatic reference formatting and tracking

### 5. Translation System
- **Quality Assurance** post-translation review and revision workflow
- **Format Preservation** maintains markdown structure, citations, formatting
- **Failover Translation** multiple translation endpoints for reliability
- **Language Detection** automatic source language identification

### 6. Web Dashboard Architecture
- **FastAPI Backend** serves dashboard API and WebSocket connections
- **Real-time Updates** via WebSocket for live progress tracking
- **File Management** browse, download, and manage research outputs
- **Session Management** track multiple concurrent research sessions

### 7. Error Handling & Reliability
- **Network Reliability Patches** custom SSL handling for Vietnamese domains
- **Retry Logic** exponential backoff for transient failures
- **Timeout Management** configurable timeouts per operation
- **Warning Suppression** clean logs by suppressing known benign warnings

### 8. Configuration Management
- **Environment Variables** via .env files for secrets and configuration
- **Pydantic Settings** type-safe configuration with validation
- **Multi-Environment** separate configs for development, staging, production
- **Feature Flags** enable/disable features without code changes

## Critical Configuration Notes

### Production Environment
- **Internal IP**: 192.168.2.22 (NOT 192.168.2.222)
- **Web Dashboard Port**: 12656 (binds to 0.0.0.0 - all interfaces)
- **Public Access**: https://tk9.thinhkhuat.com (via Caddy reverse proxy)
- **Python Version**: 3.12 (primary) or 3.11 (fallback)

### Recommended Provider Configuration
```bash
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave
LLM_STRATEGY=primary_only
SEARCH_STRATEGY=primary_only
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local
```

### API Keys Required
- **GOOGLE_API_KEY** - Primary LLM provider (Gemini)
- **BRAVE_API_KEY** - Primary search provider
- **OPENAI_API_KEY** - Fallback LLM (optional)
- **TAVILY_API_KEY** - Fallback search (optional)

### System Dependencies
- **Pandoc** - Universal document converter (required for PDF/DOCX)
- **LaTeX** - High-quality PDF rendering (optional, recommended for production)
- **Caddy** - Reverse proxy with automatic HTTPS (production deployment)

## Development Workflows

### Adding a New Agent
1. Create agent file in `multi_agents/agents/[agent_name].py`
2. Implement agent logic extending base agent class
3. Add agent to workflow in `multi_agents/agents/orchestrator.py`
4. Update state transitions in LangGraph configuration
5. Add unit tests in `tests/unit/test_agents.py`
6. Update documentation in `ref/agents.md`

### Adding a New Provider
1. Create provider file in `multi_agents/providers/[llm|search]/[provider_name].py`
2. Implement provider interface (base.py)
3. Add provider configuration in `multi_agents/config/providers.py`
4. Add API key handling in `.env.example`
5. Add provider tests in `tests/integration/test_providers_failover.py`
6. Update documentation in `ref/providers.md`

### Modifying the Workflow
1. Update workflow stages in `multi_agents/agents/orchestrator.py`
2. Modify state transitions in LangGraph configuration
3. Update memory/state structures in `multi_agents/memory/`
4. Add workflow tests in `tests/integration/test_workflow.py`
5. Update workflow diagram in `ref/workflow.md`

### Adding Output Formats
1. Create format handler in `multi_agents/agents/utils/file_formats.py`
2. Add format option in `multi_agents/task.json`
3. Update PublisherAgent in `multi_agents/agents/publisher.py`
4. Add format tests in `tests/unit/test_file_formats.py`
5. Update user guide in `docs/MULTI_AGENT_USER_GUIDE.md`

## Important Notes

### Version Requirements
- **Python 3.12+** required (some features use 3.13 improvements)
- **Always use `python3.12` or `python3.13`**, never just `python`
- Use `pyenv` to manage Python versions

### Output Locations
- **CLI Mode**: `./outputs/run_[timestamp]_[query]/`
- **MCP Mode**: In-memory only (no file output)
- **Dashboard**: Can browse and download from both

### Translation Behavior
- **Automatic**: Translates if `RESEARCH_LANGUAGE` is set and not English
- **Quality Assured**: Includes review and revision stages
- **Format Preserved**: Maintains markdown structure, citations, formatting

### Known Issues (Sep 29, 2025)
- **WebSocket via Proxy**: 404 errors when accessing through Caddy proxy
- **Workaround**: Direct access to http://192.168.2.22:12656 works correctly

### Performance Characteristics
- **Startup Time**: < 2 seconds
- **Memory Usage**: ~163 MB baseline, scales with research complexity
- **Concurrent Sessions**: Dashboard supports multiple simultaneous research tasks
- **Provider Latency**: Google Gemini typically fastest, OpenAI GPT-4 slowest

---

*This project structure document is maintained to reflect the current state of the TK9 Deep Research MCP codebase. Last updated: 2025-10-31*
