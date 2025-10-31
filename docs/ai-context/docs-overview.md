# TK9 Deep Research MCP - Documentation Architecture

This project uses a **3-tier documentation system** that organizes knowledge by stability and scope, enabling efficient AI context loading and scalable development.

## How the 3-Tier System Works

**Tier 1 (Foundation)**: Stable, system-wide documentation that rarely changes - architectural principles, technology decisions, cross-component patterns, and core development protocols.

**Tier 2 (Component)**: Architectural charters for major components - high-level design principles, integration patterns, and component-wide conventions without feature-specific details.

**Tier 3 (Feature-Specific)**: Granular documentation co-located with code - specific implementation patterns, technical details, and local architectural decisions that evolve with features.

This hierarchy allows AI agents to load targeted context efficiently while maintaining a stable foundation of core knowledge.

## Documentation Principles
- **Co-location**: Documentation lives near relevant code
- **Smart Extension**: New documentation files created automatically when warranted
- **AI-First**: Optimized for efficient AI context loading and machine-readable patterns
- **Evidence-Based**: All documentation derived from actual codebase analysis, not assumptions

## Tier 1: Foundational Documentation (System-Wide)

### Core Project Documentation
- **[Master Context](/CLAUDE.md)** - *Essential for every session.* Production configuration (IP: 192.168.2.22, port: 12656), Archon MCP integration rules, coding standards, and critical development protocols
- **[Archon Integration](/ARCHON.md)** - *CRITICAL: Read first.* Archon MCP server workflow, task management rules, RAG workflow, and project organization (overrides TodoWrite)
- **[README](/README.md)** - *Quick start guide.* Project overview, features, installation, usage modes (CLI/MCP/Dashboard), and deployment instructions

### AI Context Documentation (docs/ai-context/)
- **[Project Structure](/docs/ai-context/project-structure.md)** - *REQUIRED reading for all code changes.* Complete technology stack (Python 3.12, FastAPI, LangGraph, multi-provider system), file tree with 500+ lines, architecture patterns, development workflows (467 lines)
- **[Documentation Overview](/docs/ai-context/docs-overview.md)** - *THIS FILE.* 3-tier documentation system, registry of all documentation files, tier classification, and navigation guide (237+ lines)
- **[System Integration](/docs/ai-context/system-integration.md)** - ✅ **Complete.** Cross-component communication patterns, data flow architectures, integration protocols, error propagation, WebSocket patterns, provider abstraction integration (585 lines)
- **[Deployment Infrastructure](/docs/ai-context/deployment-infrastructure.md)** - ✅ **Complete.** Deployment methods (Docker, systemd, cloud), Caddy proxy configuration, monitoring, backup/recovery procedures, security considerations, operational procedures (738 lines)
- **[Task Management & Handoff](/docs/ai-context/handoff.md)** - ✅ **Complete.** Archon MCP task workflow, session continuity patterns, knowledge handoff strategies, development workflows, debugging context (450 lines)

### Quick Reference Documentation (ref/)
- **[Quick Reference](/ref/quick-reference.md)** - Commands, shortcuts, and common operations for TK9 system
- **[Agent Reference](/ref/agents.md)** - Detailed documentation of all 8 agents (Browser, Editor, Researcher, Writer, Publisher, Translator, Reviewer, Reviser)
- **[Provider Reference](/ref/providers.md)** - Multi-provider system (OpenAI, Gemini, Anthropic, Azure), search providers (BRAVE, Tavily), failover strategies
- **[Workflow Reference](/ref/workflow.md)** - Complete workflow architecture, state transitions, LangGraph orchestration
- **[Fact-Checking Reference](/ref/fact-checking.md)** - Research validation, quality assurance, source verification

## Tier 2: Component-Level Documentation

### Backend Components
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - ✅ **Complete.** 8-agent research workflow, LangGraph orchestration, state management, agent coordination patterns, WebSocket integration, draft management (300+ lines)
- **[Web Dashboard](/web_dashboard/CONTEXT.md)** - ✅ **Complete.** FastAPI server, WebSocket real-time updates, file management, session tracking, CLI execution layer, streaming downloads (260+ lines)
- **[Provider System](/multi_agents/providers/CONTEXT.md)** - ✅ **Complete.** Multi-provider abstraction (LLM + Search), automatic failover strategies, Google Gemini + BRAVE recommended, circuit breaker pattern (190+ lines)
- **[CLI Interface](/cli/CONTEXT.md)** - ✅ **Complete.** Interactive REPL and single-query modes, command system, provider display, progress indicators, 1,400+ lines total (240+ lines doc)
- **[Configuration Management](/multi_agents/config/CONTEXT.md)** - ✅ **Complete.** Pydantic dataclasses, type-safe settings, validation system, multi-provider configuration, 1,154 lines total (230+ lines doc)

### Integration & Infrastructure
- **[Testing Framework](/tests/CONTEXT.md)** - ✅ **Complete.** 89% test pass rate, unit/integration/e2e tests, fixtures, mocking patterns (110 lines doc)
- **[Deployment System](/deploy/CONTEXT.md)** - ✅ **Complete.** Docker, Kubernetes, AWS Lambda, systemd, Caddy proxy, production monitoring (120 lines doc)

## Tier 3: Feature-Specific Documentation

### Multi-Agent System Features
- **[Agent Implementations](/multi_agents/agents/CONTEXT.md)** - ✅ **Complete.** 8 agent pipeline (Browser→Editor→Researcher→Writer→Publisher→Translator→Reviewer→Reviser), agent utilities (LLM, views, file formats, fact-checking, type safety), unified interface pattern (180+ lines doc)
- **[Memory System](/multi_agents/memory/CONTEXT.md)** - ✅ **Complete.** ResearchState TypedDict, LangGraph state management, draft versioning system, session persistence, incremental saves, state validation patterns (150+ lines doc)
- **[Custom Retrievers](/multi_agents/retrievers/CONTEXT.md)** - ✅ **Complete.** BRAVE Search integration, base retriever interface, result filtering/ranking, content extraction, caching strategies, gpt-researcher integration (140+ lines doc)

### Web Dashboard Features (TODO: Create CONTEXT.md files)
- **[Dashboard UI](/web_dashboard/static/CONTEXT.md)** - *TODO: Create.* Vanilla JavaScript frontend, Tailwind CSS styling, WebSocket client, real-time updates
- **[File Management](/web_dashboard/file_manager_enhanced.py)** - *File exists.* Enhanced file operations, streaming downloads, directory browsing

### System Patches & Fixes (TODO: Create CONTEXT.md files)
- **[Network Reliability](/multi_agents/network_reliability_patch.py)** - *File exists.* Custom SSL handling for Vietnamese .gov.vn domains, retry logic, timeout management
- **[Dimension Parsing](/patches/gpt_researcher_dimension_fix.py)** - *File exists.* CSS dimension parsing fix for "auto" and percentage values
- **[Warning Suppression](/multi_agents/suppress_alts_warnings.py)** - *File exists.* Google gRPC ALTS warning suppression for clean logs

## Existing User Documentation (Legacy Structure)

The project currently has extensive user-facing documentation following an older pattern. These files provide comprehensive information but are not part of the 3-tier AI-optimized system:

### Core User Guides (docs/)
- **[Multi-Agent User Guide](/docs/MULTI_AGENT_USER_GUIDE.md)** - Comprehensive usage instructions
- **[Multi-Agent API Reference](/docs/MULTI_AGENT_API_REFERENCE.md)** - Complete API documentation
- **[Multi-Agent Configuration](/docs/MULTI_AGENT_CONFIGURATION.md)** - All configuration options
- **[Multi-Agent Deployment](/docs/MULTI_AGENT_DEPLOYMENT.md)** - Production deployment guide
- **[Multi-Agent Troubleshooting](/docs/MULTI_AGENT_TROUBLESHOOTING.md)** - Common issues and solutions

### System Design Documentation (docs/)
- **[System Design Architecture](/docs/MULTI_AGENT_SYSTEM_DESIGN_ARCHITECTURE.md)** - Overall system architecture
- **[System Methodology](/docs/MULTI_AGENT_SYSTEM_METHODOLOGY.md)** - Research methodology
- **[Framework Blueprint](/docs/MULTI_AGENT_FRAMEWORK_BLUEPRINT.md)** - Framework design principles
- **[Multi-Provider Guide](/docs/MULTI_PROVIDER_GUIDE.md)** - Multi-provider setup and configuration
- **[BRAVE Search Integration](/docs/MULTI_AGENT_BRAVE_SEARCH_INTEGRATION.md)** - BRAVE Search provider integration

### Development & AI Assistant Guides (docs/)
- **[AI Assistant Guide](/docs/MULTI_AGENT_AI_ASSISTANT_GUIDE.md)** - AI assistant integration patterns
- **[AI Development Guide](/docs/MULTI_AGENT_AI_DEVELOPMENT_GUIDE.md)** - AI-first development practices
- **[Provider Integration Guide](/docs/MULTI_AGENT_PROVIDER_INTEGRATION_GUIDE.md)** - Adding new providers
- **[Debugging & Troubleshooting](/docs/MULTI_AGENT_DEBUGGING_TROUBLESHOOTING_GUIDE.md)** - Debug techniques
- **[Code Patterns & Snippets](/docs/MULTI_AGENT_CODE_PATTERNS_SNIPPETS.md)** - Reusable code patterns
- **[Validation Checklists](/docs/MULTI_AGENT_VALIDATION_CHECKLISTS.md)** - Quality validation checklists

### CLI & Feature Documentation (docs/)
- **[CLI MCP Capabilities](/docs/CLI_MCP_CAPABILITIES.md)** - CLI and MCP mode capabilities
- **[CLI Quick Reference](/docs/CLI_QUICK_REFERENCE.md)** - CLI command quick reference
- **[Translation Optimization](/docs/TRANSLATION_OPTIMIZATION.md)** - Translation system optimization
- **[Fact-Checking Protocol](/docs/FACT_CHECKING_PROTOCOL.md)** - Fact-checking methodology

### Critical Development Documentation (docs/)
- **[Critical Directives](/docs/CRITICAL_DIRECTIVES.md)** - Critical development rules and requirements
- **[AI Coding Assistant README](/docs/AI_CODING_ASSISTANT_README.md)** - AI assistant integration
- **[AI Assistant Documentation Index](/docs/AI_ASSISTANT_DOCUMENTATION_INDEX.md)** - Documentation navigation for AI

### Implementation & Fix Summaries (docs/)
- **[TK9 Implementation Summary](/docs/TK9_IMPLEMENTATION_SUMMARY.md)** - Complete implementation summary
- **[Fact-Checking Implementation](/docs/FACT_CHECKING_IMPLEMENTATION_SUMMARY.md)** - Fact-checking feature implementation
- **[Fact-Checker Implementation](/docs/FACT_CHECKER_IMPLEMENTATION_SUMMARY.md)** - Fact-checker agent implementation
- **[Type Safety Audit](/docs/TYPE_SAFETY_AUDIT_REPORT.md)** - Type safety audit results
- **[Type Safety Fixes](/docs/TYPE_SAFETY_FIXES_SUMMARY.md)** - Type safety improvements
- **[Translation Workflow Validation](/docs/TRANSLATION_WORKFLOW_VALIDATION_REPORT.md)** - Translation validation
- **[Translator Final Fix](/docs/FIX_TRANSLATOR_FINAL.md)** - Final translator fixes
- **[Temporal Fix Solution](/docs/TEMPORAL_FIX_SOLUTION.md)** - Temporal context fixes
- **[Workflow Fix Script](/docs/WORKFLOW_FIX_SCRIPT_DOCUMENTATION.md)** - Workflow automation fixes
- **[Fix Report (2025-08-30)](/docs/fix_report_20250830_193103.md)** - Historical fix report
- **[Fix Summary](/docs/FIX_SUMMARY.md)** - General fixes summary

### Root-Level Operational Documentation (Active)
- **[README](/README.md)** - Project overview and quick start
- **[CLAUDE.md](/CLAUDE.md)** - Master AI context with production configuration
- **[ARCHON.md](/ARCHON.md)** - Archon MCP integration and task management
- **[DEPLOYMENT.md](/DEPLOYMENT.md)** - Deployment documentation and procedures
- **[PRODUCTION-CHECKLIST.md](/PRODUCTION-CHECKLIST.md)** - Production deployment checklist

### Archived Historical Documentation (2025-10-31)
**Location**: `/ARCHIVE/docs-deprecated-20251031/`

**16 files archived to reduce root directory clutter:**
- Production fix summaries (2025-09-29, BRAVE API, SSL, WebSocket, Dashboard, Chunking, Failover)
- Implementation reports (Achievements, Verification Report, File Reorganization)
- Historical documentation (CLAUDE.md Cleanup, MCP Assistant Rules, logs)

**See**: `/ARCHIVE/docs-deprecated-20251031/ARCHIVE_INDEX.md` for complete archive manifest and migration notes

**Rationale**: These documents provided valuable historical context but cluttered the root directory. All information is preserved in the archive and accessible for reference.

## Documentation Status & Roadmap

### ✅ Completed (Tier 1) - 100%
- **Project Structure** (467 lines) - Complete technology stack and file tree
- **Documentation Overview** (237+ lines) - This file - documentation registry
- **System Integration** (585 lines) - Cross-component communication, data flow, integration protocols
- **Deployment Infrastructure** (738 lines) - Deployment methods, monitoring, operations
- **Task Management & Handoff** (450 lines) - Archon workflow, session continuity, handoff strategies
- **Master Context** (CLAUDE.md) - Production configuration and development guidelines
- **Archon Integration** (ARCHON.md) - Task management workflow
- **Quick Reference** documentation (5 files in ref/)

**Total Tier 1**: 8/8 complete (2,477+ lines of foundational documentation)

### ✅ Completed (Tier 2) - 100%
- **Multi-Agent System CONTEXT.md** (300+ lines) - Complete architecture, 8 agents, LangGraph workflow
- **Web Dashboard CONTEXT.md** (260+ lines) - FastAPI server, WebSocket, file management
- **Provider System CONTEXT.md** (190+ lines) - Multi-provider abstraction with failover
- **CLI Interface CONTEXT.md** (240+ lines) - Interactive and single-query modes, command system
- **Configuration Management CONTEXT.md** (230+ lines) - Type-safe settings with validation
- **Testing Framework CONTEXT.md** (110 lines) - 89% test coverage, all test types
- **Deployment System CONTEXT.md** (120 lines) - Production deployment patterns

**Total Tier 2**: 7/7 complete (1,350+ lines of component documentation)

### ✅ Completed (Tier 3) - Critical Features
- **Agent Implementations CONTEXT.md** (180+ lines) - 8-agent pipeline with utilities
- **Memory System CONTEXT.md** (150+ lines) - State management and draft versioning
- **Custom Retrievers CONTEXT.md** (140+ lines) - BRAVE Search integration

**Total Tier 3**: 3/3 critical features (470+ lines of feature documentation)

### ✅ Completed - Root Cleanup
- Root-level documentation cleanup (✅ Complete - 16 files archived to `/ARCHIVE/docs-deprecated-20251031/`)
- Archive index created with migration notes
- Root directory: 5 essential files remain (76% reduction)

### 📋 Optional Future Enhancements
- Advanced monitoring dashboards (Prometheus/Grafana setup)
- CI/CD pipeline automation (GitHub Actions workflows)
- Multi-instance deployment patterns (load balancing, shared storage)

### 📋 Optional: Additional Tier 3 Documentation
- Dashboard UI (CONTEXT.md) - Frontend JavaScript patterns
- Additional feature-specific CONTEXT.md files as needed

## Adding New Documentation

### New Component (Tier 2)
1. Create `/component-name/CONTEXT.md` at component root
2. Add entry to this file under "Tier 2: Component-Level Documentation"
3. Create feature-specific Tier 3 docs as features develop
4. Use template from `/docs/CONTEXT-tier2-component.md` (TODO: Create)

### New Feature (Tier 3)
1. Create `/component/src/feature/CONTEXT.md` co-located with code
2. Reference parent component patterns
3. Add entry to this file under appropriate component's features
4. Use template from `/docs/CONTEXT-tier3-feature.md` (TODO: Create)

### Updating Existing Documentation
1. Update the relevant CONTEXT.md file
2. If tier changes, update this registry
3. Check for broken cross-references in other docs
4. Update "Last updated" timestamp

### Deprecating Documentation
1. Move obsolete files to `/ARCHIVE/docs-deprecated-[date]/`
2. Remove entries from this registry
3. Check for and fix broken references in other docs
4. Update migration notes if content moved to new location

## Documentation Migration Strategy

The project currently has 50+ documentation files in various formats. The migration strategy:

### Phase 1: Foundation (Completed)
- ✅ Create Tier 1 foundational docs (project-structure.md, docs-overview.md)
- ✅ Establish 3-tier system and principles
- ✅ Update CLAUDE.md and ARCHON.md with current production config

### Phase 2: Component Architecture (TODO)
- Create Tier 2 CONTEXT.md files for all major components
- Extract architectural patterns from existing docs
- Preserve high-level design decisions
- Add cross-references to existing detailed docs

### Phase 3: Feature Documentation (TODO)
- Create Tier 3 CONTEXT.md files co-located with code
- Extract implementation patterns from existing docs
- Document feature-specific decisions
- Link to parent component architecture

### Phase 4: Consolidation & Cleanup (TODO)
- Identify redundant content in legacy docs
- Migrate valuable content to appropriate tiers
- Archive obsolete documentation
- Create clear navigation paths between old and new docs

---

*This documentation architecture is being actively developed. The 3-tier system provides AI-optimized navigation while preserving the extensive existing documentation. Last updated: 2025-10-31*
