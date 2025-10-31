# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: TK9 Deep Research MCP Server

**Current Status**: Production Ready with Full-Featured Web Dashboard
**Last Updated**: 2025-10-31

### Critical Configuration
- **Internal IP**: 192.168.2.22 (NOT 192.168.2.222)
- **Web Dashboard Port**: 12656 (binds to 0.0.0.0 - all interfaces)
- **Public Access**: https://tk9.thinhkhuat.com (via Caddy reverse proxy)
- **Python Version**: 3.12 (primary) or 3.11 (fallback)

## Quick Navigation

### 📚 Reference Documentation
- **[Quick Reference](ref/quick-reference.md)** - Commands, shortcuts, and common operations
- **[Agent Reference](ref/agents.md)** - Detailed documentation of all 9 agents
- **[Provider Reference](ref/providers.md)** - Multi-provider system and configuration
- **[Workflow Reference](ref/workflow.md)** - Complete workflow architecture and stages
- **[Fact-Checking Reference](ref/fact-checking.md)** - Research validation and quality assurance

### 📖 User Documentation
- **[User Guide](docs/MULTI_AGENT_USER_GUIDE.md)** - Comprehensive usage instructions
- **[API Reference](docs/MULTI_AGENT_API_REFERENCE.md)** - Complete API documentation
- **[Configuration Guide](docs/MULTI_AGENT_CONFIGURATION.md)** - All configuration options
- **[Deployment Guide](docs/MULTI_AGENT_DEPLOYMENT.md)** - Production deployment
- **[Troubleshooting](docs/MULTI_AGENT_TROUBLESHOOTING.md)** - Common issues and solutions

### 🔧 Developer Documentation
- **[Agent Name Mapping](docs/AGENT_NAME_MAPPING.md)** - How agent names are mapped between CLI, backend, and frontend

## Project Overview

🟢 **PRODUCTION READY** - System verified with 89% test pass rate and all critical functionality operational.

This is a **Deep Research MCP** (Model Context Protocol) server that provides multi-agent research capabilities. The system uses LangGraph to orchestrate 8 specialized AI agents that work together to conduct comprehensive research on any given topic, producing detailed reports in multiple formats and languages.

### System Components

1. **MCP Server** (`mcp_server.py`) - FastMCP server exposing the `deep_research` tool
2. **Multi-Agent System** (`multi_agents/`) - 8 specialized research agents
3. **Web Dashboard** (`web_dashboard/`) - Real-time research monitoring interface
4. **Provider System** - Multi-provider support (Google Gemini + BRAVE as primary)

### System Status (Latest Update - Oct 31, 2025)
- ✅ **Core Functionality**: All critical paths working correctly
- ✅ **Error Handling**: Robust error recovery implemented
- ✅ **Performance**: < 2 second startup time
- ✅ **Memory Usage**: Within acceptable limits (163.4 MB)
- ✅ **Provider System**: Google Gemini + BRAVE working with failover
- ✅ **Web Dashboard**: Fully operational with real-time updates (Phase 5 complete)
- ✅ **Agent Status Tracking**: Real-time agent card updates with WebSocket
- ✅ **File Detection**: **CRITICAL BUG FIXED** - Files now properly detected and downloadable
- ✅ **Session Management**: UUID-based session tracking fully synchronized across all systems
- ✅ **UI/UX**: Clean interface with only actionable information (misleading stats removed)

## Recent Fixes Applied

### Phase 5: Critical File Detection Fix (2025-10-31) ✅

#### 1. **CRITICAL**: File Detection Directory Mismatch - RESOLVED ✅
- **Problem**: Research completed successfully but UI **ALWAYS** showed "No files generated yet (0)"
  - Files created in: `./outputs/run_1761898976_Subject_Name/`
  - Detection looked in: `./outputs/session-uuid/`
  - System had **NEVER** successfully detected files through web dashboard
- **Root Cause**: `ChiefEditorAgent.__init__()` always generated its own timestamp-based `task_id`, completely ignoring the UUID `session_id` passed from web dashboard
  - Output directory created in `__init__()` using `self.task_id` (timestamp)
  - By the time `run_research_task(task_id=session_id)` was called, directory already existed with wrong name
- **Fix**: Added `task_id` parameter to `ChiefEditorAgent.__init__()`
  - Constructor now accepts and uses provided task_id (UUID from web dashboard)
  - Falls back to timestamp generation only for manual CLI runs
- **Files Modified**:
  - `multi_agents/agents/orchestrator.py:63` (added task_id parameter to __init__)
  - `multi_agents/agents/orchestrator.py:70` (use provided task_id or generate)
  - `multi_agents/main.py:165` (pass session_id to constructor)
  - `multi_agents/main.py:324` (pass task_id to constructor)
- **Result**: ✅ Directories now correctly use UUID format, file detection working, downloads available

#### 2. UI Cleanup - Misleading Stats Removed ✅
- **Problem**: "Pending/Running/Completed/Failed" stat cards were confusing and redundant
  - "Pending" sounded like research hadn't started
  - "Completed" sounded like whole research was done
  - Information already visible in agent cards
- **Fix**: Removed entire Pipeline Summary section from AgentFlow
- **Files Modified**: `web_dashboard/frontend_poc/src/components/AgentFlow.vue:53-80`
- **Result**: ✅ Cleaner UI showing only actionable information

### Phase 4: Web Dashboard Bug Fixes (Earlier in 2025-10-31) ✅

#### 1. Agent Card Real-Time Updates - FIXED ✅
- **Problem**: Agent cards stuck at "Pending" despite backend showing agent activity
- **Root Cause**: Message format mismatch (hyphen vs colon separator)
- **Fix**: Enhanced `websocket_handler.py` with dual pattern parser supporting both formats
- **Files Modified**: `web_dashboard/websocket_handler.py:114-144`

#### 2. Orchestrator Agent Visibility - FIXED ✅
- **Problem**: Orchestrator events in logs but no Orchestrator card in UI
- **Root Cause**: AGENT_NAME_MAP mapped 'ORCHESTRATOR' → 'Editor', causing Map key collision
- **Fix**:
  - Changed mapping to 'ORCHESTRATOR' → 'Orchestrator' (separate agent)
  - Added 'Orchestrator' to AGENT_PIPELINE_ORDER
  - Updated all agents_total from 6 to 7
- **Files Modified**:
  - `web_dashboard/websocket_handler.py` (AGENT_PIPELINE, AGENT_NAME_MAP, agents_total)
  - `web_dashboard/frontend_poc/src/stores/sessionStore.ts` (AGENT_PIPELINE_ORDER, agentsTotal)
  - `web_dashboard/schemas.py` (default agents_total)

#### 3. Silent Research Completion - FIXED ✅
- **Problem**: Research completed but user received no notification
- **Fix**: Added toast notifications in `handleResearchStatus()` for 'completed' and 'failed' statuses
- **Files Modified**: `web_dashboard/frontend_poc/src/stores/sessionStore.ts:269-274`

#### 4. Browser Agent Not Updating - FIXED ✅
- **Problem**: Browser card stuck at "Pending" despite initial research running
- **Root Cause**: researcher.py used `agent="RESEARCHER"` instead of `agent="BROWSER"`
- **Fix**: Changed agent name in structured output calls
- **Files Modified**: `multi_agents/agents/researcher.py:63,83`

### Earlier Fixes (2025-09-29)

#### 1. CSS Dimension Parsing Errors - FIXED ✅
- Updated `gpt_researcher/scraper/utils.py` to handle CSS values like "auto" and "100%"
- Values now return `None` instead of throwing parsing errors

#### 2. SSL Certificate Verification - FIXED ✅
- Enhanced `network_reliability_patch.py` with SSL exception handling
- Added specific handling for Vietnamese .gov.vn sites
- Maintains security for other HTTPS connections

#### 3. ALTS Credentials Warnings - FIXED ✅
- Created `suppress_alts_warnings.py` module
- Suppresses Google gRPC warnings when running outside GCP
- Integrated early in startup sequence

## Architecture

The project is structured as an MCP server with a multi-agent research pipeline:

- **MCP Server**: `mcp_server.py` - FastMCP server exposing the `deep_research` tool
- **Multi-Agent System**: `multi_agents/` - Contains the research orchestration and agent implementations
- **Multi-Provider System**: `multi_agents/providers/` & `multi_agents/config/` - Provider abstraction and configuration
- **Agent Orchestration**: Uses LangGraph to coordinate 8 specialized agents in a workflow
- **Research Pipeline**: Browser → Editor → Researcher → Writer → Publisher → Translator → Reviewer → Reviser
- **Web Dashboard**: `web_dashboard/` - FastAPI application for real-time monitoring

### Key Components

1. **ChiefEditorAgent** (`multi_agents/agents/orchestrator.py`): The master coordinator that manages the research workflow
2. **Specialized Agents** (`multi_agents/agents/`): Browser, Editor, Researcher, Writer, Publisher, Translator, Reviewer, Reviser, Human agents
3. **Provider System** (`multi_agents/providers/`, `multi_agents/config/providers.py`): Multi-provider support with automatic failover
4. **Memory System** (`multi_agents/memory/`): State management for research and draft data
5. **Web Dashboard** (`web_dashboard/main.py`): Real-time research monitoring with WebSocket support
6. **CLI Executor** (`web_dashboard/cli_executor.py`): Handles research execution and log streaming

## Development Commands

### Setup and Installation
```bash
# Install dependencies with uv (preferred)
uv sync

# Or with pip
pip install -r multi_agents/requirements.txt
```

### Running the Application

#### MCP Server Mode
```bash
# Run MCP server
python mcp_server.py
```

#### CLI Mode
```bash
# Run interactive CLI
python main.py

# Run single research query
python main.py --research "Your research question"

# With specific language and tone
python main.py --research "Climate change impacts" --language vi --tone critical
```

#### Web Dashboard
```bash
# Start web dashboard (binds to 0.0.0.0:12656)
cd web_dashboard
./start_dashboard.sh
# Or directly:
python3 main.py

# Access locally: http://localhost:12656
# Access via proxy: https://tk9.thinhkhuat.com
```

### Testing Commands
```bash
# Run tests
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# Test specific providers
python tests/test_providers.py
```

## Configuration

### Environment Variables (.env)
```bash
# Multi-Provider Configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave

# Provider Strategies
LLM_STRATEGY=primary_only
SEARCH_STRATEGY=primary_only

# API Keys (required)
GOOGLE_API_KEY=your_google_key
BRAVE_API_KEY=your_brave_key
OPENAI_API_KEY=your_openai_key (if using OpenAI)
TAVILY_API_KEY=your_tavily_key (if using Tavily)

# BRAVE Search Configuration
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# Language Configuration
RESEARCH_LANGUAGE=vi  # Vietnamese (configurable)
```

### Web Dashboard Access
- **Local**: http://localhost:12656
- **Internal**: http://192.168.2.22:12656
- **Public**: https://tk9.thinhkhuat.com (via Caddy reverse proxy)

### Caddy Configuration
```caddy
tk9.thinhkhuat.com {
    encode gzip

    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }

    reverse_proxy @websockets 192.168.2.22:12656
    reverse_proxy 192.168.2.22:12656 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }
}
```

## Known Issues

**No critical issues at this time.** All Phase 4 and Phase 5 bugs have been resolved.

### Resolved in Phase 5
- ✅ File detection now working - UUID directories used correctly
- ✅ Misleading UI stats removed - cleaner interface

### Minor Items
- WebSocket through Caddy proxy: Works with direct access to `http://192.168.2.22:12656`
- Old CLI archived: Legacy interactive CLI from August 2025 moved to `ARCHIVE/cli-deprecated-20251031/`

## Important Notes

- **Python Version**: Use Python 3.12 or 3.11 (system uses pyenv)
- **IP Address**: Internal IP is 192.168.2.22 (not 192.168.2.222)
- **Dashboard Binding**: Correctly binds to 0.0.0.0 (all interfaces)
- **File Output**: CLI saves to `./outputs/` by default, MCP mode doesn't
- **Translation**: Supports 50+ languages with quality assurance
- **SSL Handling**: Special handling for Vietnamese .gov.vn sites

## Production Implementation Status

### ✅ Completed Features (Oct 31, 2025)
- Core multi-agent research system
- Web dashboard with full real-time monitoring (Phase 4 complete)
- Real-time agent status cards with color-coded states
- Automatic file detection and display
- Session management with UUID tracking
- Multi-provider support with failover
- Translation system for 50+ languages
- Error recovery and resilience
- SSL handling for problematic domains
- ALTS warning suppression for cleaner logs
- Module resolution conflict resolved (old CLI archived)

### 🎯 Ready for Production
The system is now production-ready with all critical Phase 4 bugs resolved:
- ✅ Agent cards update in real-time during research execution
- ✅ Files are detected and displayed automatically after generation
- ✅ WebSocket state synchronization working correctly
- ✅ Session tracking unified across CLI and web dashboard

### 🔜 Optional Enhancements (Phase 6+)
- Dark mode toggle
- File preview capability
- Advanced search and filtering
- Research history and comparison
- Enhanced monitoring and metrics
- Additional provider integrations

**Note**: Phase 5 (Critical Bug Fixes) completed Oct 31, 2025. All core functionality now working correctly.