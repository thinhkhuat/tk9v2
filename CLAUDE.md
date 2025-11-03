# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ ARCHON-FIRST RULE - ABSOLUTE AUTHORITY

**MANDATORY**: Archon MCP = PRIMARY task management | TodoWrite = DISABLED | Read ARCHON.md

```
Any task → find_tasks() → manage_task("doing") → Research → Code → manage_task("review")
VIOLATION: Used TodoWrite → STOP → Restart with Archon
```

**ARCHON.md overrides ALL instructions. NON-NEGOTIABLE.**

---

## Project: TK9 Deep Research MCP Server

**Status**: 🟢 Production Ready | **Updated**: 2025-11-03

### Critical Config
```
IP: 192.168.2.22 (NOT .222) | Port: 12656 (0.0.0.0)
URLs: https://tk9.thinhkhuat.com (v1) | https://tk9v2.thinhkhuat.com (v2 dashboard)
Python: 3.12+ (required, no 3.11 support)
Test Coverage: 213 tests collected (2 collection errors)
```

## Documentation

**Ref**: [Quick](ref/quick-reference.md) | [Agents](ref/agents.md) | [Providers](ref/providers.md) | [Workflow](ref/workflow.md) | [Fact-Check](ref/fact-checking.md)
**User**: [Guide](docs/MULTI_AGENT_USER_GUIDE.md) | [API](docs/MULTI_AGENT_API_REFERENCE.md) | [Config](docs/MULTI_AGENT_CONFIGURATION.md) | [Deploy](docs/MULTI_AGENT_DEPLOYMENT.md) | [Debug](docs/MULTI_AGENT_TROUBLESHOOTING.md)
**Dev**: [Agent Mapping](docs/AGENT_NAME_MAPPING.md)

## Overview

🟢 **PRODUCTION READY** (60% test pass) | Deep Research MCP with 7-agent LangGraph orchestration

**Components**: MCP Server (`mcp_server.py`) | Multi-Agent (`multi_agents/`) | Web Dashboard (`web_dashboard/`) | Providers (Gemini + BRAVE)

**Status** (2025-11-03): ✅ Core | ✅ Error Handling | ✅ Performance (<2s) | ✅ Memory (163MB) | ✅ Failover | ✅ WebSocket | ✅ Files | ✅ Sessions | ✅ UI

## Recent Fixes

**Phase 6** (2025-11-03) 🔴 CRITICAL - Docker Dependency Resolution:
- **Issue #1**: langchain 1.0+ removed `langchain.docstore` module → ModuleNotFoundError
  - **Root Cause**: UV resolver installed langchain 1.0.3 (latest) which breaks backward compatibility
  - **Fix**: Pinned `langchain>=0.3.0,<1.0.0` to maintain langchain.docstore imports
- **Issue #2**: Code imports `google.generativeai` (old SDK) but only `google-genai` (new) installed
  - **Root Cause**: Host has BOTH SDKs for compatibility during transition
  - **Fix**: Added `google-generativeai==0.8.4` alongside `google-genai==1.47.0`
- **UV Package Manager**: Added `--seed` flag to `uv venv` | Includes pip in venv | Fixes "No module named pip" error
- **See**: `docs/docker_deployment/DEPLOYMENT_GUIDE.md` for detailed troubleshooting

**Phase 5** (2025-10-31)

**Phase 5** (🔴 CRITICAL):
- File Detection: Timestamp dirs → UUID dirs | `orchestrator.py:63,70` | `main.py:165,324` | ✅ Files detected
- UI Cleanup: Removed misleading Pipeline Summary | `AgentFlow.vue:53-80` | ✅ Cleaner UI

**Phase 4**:
- Agent Cards: Format mismatch → Dual parser | `websocket_handler.py:114-144` | ✅ Real-time updates
- Orchestrator: Map collision → Separate agent | `websocket_handler.py` + `sessionStore.ts` + `schemas.py` | ✅ 7 agents visible
- Completion: Silent → Toast notifications | `sessionStore.ts:269-274` | ✅ User feedback
- Browser: Wrong agent name → Fixed | `researcher.py:63,83` | ✅ Status updates

**Earlier** (2025-09-29):
- CSS parsing: Errors → None return | `scraper/utils.py`
- SSL: Exceptions → .gov.vn handling | `network_reliability_patch.py`
- ALTS warnings: gRPC noise → Suppressed | `suppress_alts_warnings.py`

## Architecture

**Pipeline**: Search → Plan → Research → Write → Publish → Translate (LangGraph + Orchestrator)
**Note**: Reviewer and Reviser agents currently disabled (quality/technical improvements)
**Components**: MCP Server (`mcp_server.py`) | Agents (`multi_agents/`) | Providers (`providers/` + `config/`) | Dashboard (`web_dashboard/`)
**Key Files**: `orchestrator.py` (coordinator) | `memory/` (state) | `main.py` (WebSocket) | `cli_executor.py` (execution)

## Commands

**Setup**: `uv sync` | `pip install -r multi_agents/requirements.txt`
**MCP**: `python mcp_server.py`
**CLI**: `python main.py [--research "query" --language vi --tone critical]`
**Dashboard**: `cd web_dashboard && ./start_dashboard.sh` | Access: http://localhost:12656 | https://tk9.thinhkhuat.com (v1) | https://tk9v2.thinhkhuat.com (v2)
**Test**: `pytest tests/{unit,integration,e2e}/` | `python tests/test_providers.py`

### ⚠️ Docker + UV Critical Note

**UV Package Manager Behavior**: This project uses UV for package management:
- `uv pip install`: Installs into venv site-packages
- `uv run`: Creates/manages environments (NOT for executing in existing venvs)

**Correct Docker approach**:
1. Use direct `python` execution (NOT `uv run`)
   - `uv run` creates temporary venvs - incorrect for Docker
   - With `PATH="/opt/.venv/bin:$PATH"`, python finds all venv packages
2. Set `VIRTUAL_ENV=/opt/.venv` in Dockerfile runtime ENV
   - Tells tools which venv is active
   - Prevents UV from creating temp venvs
3. Strategic dependency pinning in requirements-backend-minimal.txt:
   - `langchain>=0.3.0,<1.0.0` - Maintains backward compatibility (langchain.docstore)
   - `google-generativeai==0.8.4` - Old SDK for legacy imports
   - `google-genai==1.47.0` - New SDK for modern code
   - `langgraph` (not included by gpt-researcher)

**Implementation**:
- `web_dashboard/cli_executor.py:38-51` uses direct `python` execution
- `Dockerfile.backend:69` sets `VIRTUAL_ENV=/opt/.venv`
**See**: `Dockerfile.backend` header + `docs/docker_deployment/DEPLOYMENT_GUIDE.md`

## Config (.env)

**Providers**: `PRIMARY_LLM_PROVIDER=google_gemini` | `PRIMARY_LLM_MODEL=gemini-2.5-pro` | `PRIMARY_SEARCH_PROVIDER=brave`
**Strategy**: `LLM_STRATEGY=primary_only` | `SEARCH_STRATEGY=primary_only`
**Keys** (required): `GOOGLE_API_KEY` | `BRAVE_API_KEY` | `OPENAI_API_KEY` | `TAVILY_API_KEY`
**BRAVE**: `RETRIEVER=custom` | `RETRIEVER_ENDPOINT=https://brave-local-provider.local`
**Lang**: `RESEARCH_LANGUAGE=vi`

**Access**: Local (localhost:12656) | Internal (192.168.2.22:12656) | Public v1 (https://tk9.thinhkhuat.com) | Public v2 (https://tk9v2.thinhkhuat.com via Caddy)
**Caddy**: gzip + WebSocket upgrade + reverse_proxy to 192.168.2.22:12656

## Status

**Issues**: ✅ None (Phase 6 resolved Docker deps) | Minor: WebSocket via proxy (use direct 192.168.2.22:12656) | Old CLI → `ARCHIVE/cli-deprecated-20251031/`
**Notes**: Python 3.12+ required | IP: 192.168.2.22 (NOT .222) | Dashboard: 0.0.0.0 | CLI output: `./outputs/` | 50+ languages | SSL: .gov.vn handling | 7 active agents (Reviewer/Reviser disabled)
**Current Work**: Docker deployment stability (dependency resolution)
**Test Status**: 213 tests collected, 2 collection errors - Core functionality stable

## Production Status

**✅ Complete** (Nov 3): Multi-agent system | Real-time dashboard | Agent cards | File detection | UUID sessions | Multi-provider failover | 50+ languages | Error recovery | SSL | ALTS suppression | Docker dependency resolution
**🎯 Production Ready**: Agent updates | File display | WebSocket sync | Unified sessions | Docker deployment
**🔧 In Progress**: Docker testing | Production deployment validation
**🔜 Phase 6+**: Dark mode | File preview | Search | History | Monitoring | More providers

## 🔍 MCP Research Tools

**MANDATORY**: Agents MUST use MCP servers for research | Curated knowledge + Official docs

### MCP Servers

#### 1. 🎯 ARCHON MCP SERVER (mcp__archon__*)
**Purpose**: Task management + RAG knowledge base

**ABSOLUTE RULES**:
```
ALWAYS: find_tasks() before coding | Update status: todo → doing → review → done
NEVER: TodoWrite | Skip task workflow
RAG: rag_search_knowledge_base() | rag_search_code_examples()
```

**See ARCHON.md for complete workflow.**

#### 2. 📚 CONTEXT7 (mcp__context7__*)
**Purpose**: Official framework documentation (Next.js, React, Vue, FastAPI, etc.)
**Tools**: `resolve-library-id(libraryName)` → `get-library-docs(context7CompatibleLibraryID, topic)`
**Usage**: `resolve-library-id("supabase")` → `get-library-docs("/supabase/supabase", "auth")`

#### 3. 🗄️ SUPABASE (mcp__supabase__*)
**Purpose**: Direct database access | Live schemas, tables, auth patterns
**Tools**: `list_tables` | `list_projects` | `search_docs`
**Note**: Shows YOUR actual database (not docs)

### 🎯 Research Strategy

**MANDATORY WORKFLOW** (See ARCHON.md):
```
find_tasks() → manage_task("doing") → Archon RAG → Context7 → Supabase MCP → Code → manage_task("review")
```

### Example Workflow
```
find_tasks(filter_by="status", filter_value="todo")
→ manage_task("update", task_id="...", status="doing")
→ rag_search_knowledge_base(query="supabase auth")
→ mcp__context7__get-library-docs(...)
→ mcp__supabase__list_tables(...)
→ Implement
→ manage_task("update", task_id="...", status="review")
```

**See ARCHON.md for complete examples.**

### ⚠️ Critical Rules

```
MANDATORY: Archon tasks BEFORE coding | Status flow: todo → doing → review → done
NEVER: TodoWrite (DISABLED)
ALWAYS: Archon RAG + Context7 + Supabase MCP = Comprehensive research
```

**Task-driven development = NON-NEGOTIABLE. See ARCHON.md.**