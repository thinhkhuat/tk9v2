# Phase 2: Structured JSON Output Migration

**Date**: 2025-10-31
**Status**: 🟡 IN PROGRESS - Pilot agent (Researcher) migrated
**Gemini Validation**: Session eee27430-a42a-40f3-a60b-718269c4df50

## Overview

Phase 2 replaces unreliable regex-based agent status parsing with structured JSON output, eliminating the agent status mix-up issues identified in Phase 1.

### Problem Being Solved

**Issue**: Agent status updates were unreliable and mixed up due to fragile regex parsing of colored text output:
```python
# Old format - brittle and error-prone
print(f"{color}RESEARCHER: Found 5 articles{reset}")  # Parsed with regex
```

**Solution**: Structured JSON events with envelope pattern:
```json
{
  "type": "agent_update",
  "payload": {
    "agent_id": "researcher",
    "agent_name": "RESEARCHER",
    "status": "running",
    "progress": 60,
    "message": "Found 5 articles",
    "timestamp": "2025-10-31T12:00:00.123Z"
  }
}
```

---

## Architecture

### Envelope-Based Event Pattern

Following industry best practices for event-driven systems, we use an envelope structure:

```
┌─────────────────────────────────────────────────────────┐
│ Event Envelope                                           │
├─────────────────────────────────────────────────────────┤
│ type: "agent_update"                                     │
│ payload: {                                               │
│   agent_id: string (machine-readable, lowercase)        │
│   agent_name: string (human-readable for display)       │
│   status: "pending"|"running"|"completed"|"error"       │
│   message: string (user-facing message)                 │
│   timestamp: string (ISO 8601)                          │
│   progress?: number (0-100, optional)                   │
│   data?: object (structured agent data, optional)       │
│   error?: {code, message, details} (optional)           │
│ }                                                        │
└─────────────────────────────────────────────────────────┘
```

**Why Envelope Pattern?**
- Allows introducing new event types without breaking existing consumers
- Clean separation of event metadata (type) from event data (payload)
- Industry standard for WebSocket/SSE communication

### Type Safety with TypedDict

All event structures are defined using Python's `TypedDict` for:
- Static analysis and autocomplete support
- Runtime type checking
- Self-documenting code

See: `multi_agents/agents/utils/event_types.py`

---

## Migration Strategy

### Incremental Migration (Gemini-Validated)

**Critical**: We use incremental migration, NOT "big bang" deployment.

**Why?**
- ✅ Low risk - isolated to one agent at a time
- ✅ Easy debugging - know exactly where issues occur
- ✅ Simple rollback - revert single agent if needed
- ✅ Minimal user impact - most system remains stable
- ❌ "Big bang" is unacceptably risky for production

### Migration Phases

```
Phase 2.1: Infrastructure ✅ COMPLETE
├── Create TypedDict definitions
├── Implement print_structured_output()
├── Add dual-mode parsing to WebSocket handler
└── Add feature flags for gradual rollout

Phase 2.2: Pilot Agent ✅ COMPLETE
├── Migrate Researcher agent
├── Test with feature flag: AGENT_JSON_MIGRATION=researcher
├── Validate WebSocket parsing works
└── Monitor for issues

Phase 2.3: Full Migration 🟡 IN PROGRESS
├── Migrate Writer agent
├── Migrate Translator agent
├── Migrate Publisher agent
├── Migrate Editor agent
├── Migrate Reviewer agent
├── Migrate Reviser agent
├── Migrate Browser agent
└── Test each agent individually before proceeding

Phase 2.4: Cleanup ⏳ PENDING
├── Enable ENABLE_JSON_OUTPUT=true globally
├── Remove legacy regex parsing code
├── Remove print_agent_output() function
└── Update documentation
```

---

## Feature Flags

### Environment Variables

```bash
# .env configuration

# Global flag - enables JSON for ALL agents (use only after full migration)
ENABLE_JSON_OUTPUT=false  # Default: false during migration

# Agent-specific flag - enables JSON for specific agents (comma-separated)
AGENT_JSON_MIGRATION=researcher  # Pilot: only researcher uses JSON
# AGENT_JSON_MIGRATION=researcher,writer  # After writer migration
# AGENT_JSON_MIGRATION=researcher,writer,translator  # Progressive rollout
```

### Migration Workflow

1. **Start**: All agents use legacy text output
   ```bash
   # No flags set
   ```

2. **Pilot Agent**: Test with Researcher only
   ```bash
   AGENT_JSON_MIGRATION=researcher
   ```

3. **Progressive Rollout**: Add agents one by one
   ```bash
   AGENT_JSON_MIGRATION=researcher,writer
   AGENT_JSON_MIGRATION=researcher,writer,translator
   # ... continue adding agents
   ```

4. **Full Migration**: Enable globally
   ```bash
   ENABLE_JSON_OUTPUT=true  # All agents now use JSON
   ```

5. **Cleanup**: Remove feature flags and legacy code
   ```bash
   # Remove both flags from .env
   # Delete legacy parsing code
   # Delete print_agent_output() function
   ```

---

## Implementation Details

### 1. New Functions in `views.py`

```python
# Core function - replaces print_agent_output()
print_structured_output(
    message="Running research",
    agent="RESEARCHER",
    status="running",  # pending, running, completed, error
    progress=50,  # Optional: 0-100
    data={"urls_found": [...]},  # Optional: structured data
    error={"code": "...", "message": "..."}  # Optional: error details
)

# Convenience wrappers
print_agent_progress(agent="RESEARCHER", message="...", progress=60)
print_agent_completion(agent="RESEARCHER", message="...", data={...})
print_agent_error(agent="RESEARCHER", message="...", error_code="API_TIMEOUT")
```

### 2. Dual-Mode WebSocket Parser

The WebSocket handler (`websocket_handler.py`) now supports BOTH formats:

```python
def parse_agent_from_output(self, line: str) -> tuple[str, str, dict | None] | None:
    """
    Returns: (agent_name, message, json_payload)
    - json_payload is None for legacy text format
    - json_payload contains full event for JSON format
    """
    # Try JSON first
    try:
        event = json.loads(line)
        if event.get("type") == "agent_update":
            payload = event["payload"]
            return (payload["agent_name"], payload["message"], payload)
    except:
        pass

    # Fall back to legacy regex parsing
    # ... (existing regex code)
```

### 3. Agent Migration Pattern

**Before (Legacy)**:
```python
print_agent_output(f"Running research on: {query}", agent="RESEARCHER")
```

**After (Phase 2)**:
```python
print_structured_output(
    message=f"Running research on: {query}",
    agent="RESEARCHER",
    status="running",
    progress=10
)
```

**Migration Checklist per Agent**:
1. Import new functions: `from .utils.views import print_structured_output, print_agent_completion`
2. Replace all `print_agent_output()` calls with `print_structured_output()`
3. Add explicit `status` parameter (running, completed, error)
4. Add `progress` percentage where applicable
5. Use `print_agent_completion()` wrapper for completion events
6. Test with `AGENT_JSON_MIGRATION=agent_name`
7. Verify WebSocket events appear correctly in frontend

---

## Testing

### Local Testing

1. **Enable pilot agent**:
   ```bash
   echo "AGENT_JSON_MIGRATION=researcher" >> .env
   ```

2. **Start dashboard**:
   ```bash
   cd web_dashboard
   python3 main.py
   ```

3. **Start research**:
   ```bash
   # Via dashboard UI
   http://localhost:12656
   ```

4. **Verify logs**:
   ```
   # Should see in terminal:
   ✅ Parsed JSON agent update: Researcher - Running initial research...
   ✅ Sent JSON-based agent_update: Researcher → running (10%)
   ✅ Sent JSON-based agent_update: Researcher → completed (100%)
   ```

5. **Check frontend**:
   - Researcher agent card should show correct status
   - Other agents still work with legacy text parsing
   - No mixed-up agent states

### Production Deployment

1. Deploy Phase 2.1 + 2.2 (infrastructure + pilot)
2. Monitor for 24 hours with `AGENT_JSON_MIGRATION=researcher`
3. Verify zero agent status mix-ups for Researcher
4. If successful, proceed to migrate next agent
5. If issues occur, remove researcher from AGENT_JSON_MIGRATION

---

## Migration Progress

| Agent | Status | Flag Value | Notes |
|-------|--------|------------|-------|
| Researcher | ✅ Migrated | `researcher` | Pilot agent - tested and verified |
| Writer | ⏳ Pending | `writer` | Next to migrate |
| Translator | ⏳ Pending | `translator` | |
| Publisher | ⏳ Pending | `publisher` | |
| Editor | ⏳ Pending | `editor` | |
| Reviewer | ⏳ Pending | `reviewer` | |
| Reviser | ⏳ Pending | `reviser` | |
| Browser | ⏳ Pending | `browser` | |

**Current Flag**: `AGENT_JSON_MIGRATION=researcher`

---

## Rollback Plan

If issues occur with JSON output:

### Per-Agent Rollback
```bash
# Remove agent from AGENT_JSON_MIGRATION
AGENT_JSON_MIGRATION=writer,translator  # Removed 'researcher'
```

### Full Rollback
```bash
# Remove both flags
unset ENABLE_JSON_OUTPUT
unset AGENT_JSON_MIGRATION
# System reverts to 100% legacy text output
```

### Code Rollback
```bash
# Revert agent file changes
git checkout main -- multi_agents/agents/researcher.py
```

---

## Success Criteria

Phase 2 is successful when:

- [x] TypedDict schema defined and documented
- [x] `print_structured_output()` implemented with feature flags
- [x] WebSocket handler supports dual-mode parsing
- [x] Pilot agent (Researcher) migrated and tested
- [ ] All 8 agents migrated to JSON output
- [ ] 48 hours of production stability with `ENABLE_JSON_OUTPUT=true`
- [ ] Zero agent status mix-ups in logs
- [ ] Agent cards show correct real-time status
- [ ] Legacy code removed and tests passing

---

## Files Modified

### New Files
```
multi_agents/agents/utils/event_types.py     - TypedDict definitions (169 lines)
docs/PHASE_2_STRUCTURED_JSON_MIGRATION.md    - This file
```

### Modified Files
```
multi_agents/agents/utils/views.py           - Added print_structured_output() (198 lines total)
web_dashboard/websocket_handler.py           - Dual-mode parser (lines 114-192, 194-282)
multi_agents/agents/researcher.py            - Migrated to JSON output ✅
```

### Files to Modify (Remaining)
```
multi_agents/agents/writer.py               - Pending migration
multi_agents/agents/translator.py           - Pending migration
multi_agents/agents/publisher.py            - Pending migration
multi_agents/agents/editor.py               - Pending migration
multi_agents/agents/reviewer.py             - Pending migration
multi_agents/agents/reviser.py              - Pending migration
multi_agents/agents/browser.py              - Pending migration (if exists)
```

---

## Gemini AI Validation

**Session**: eee27430-a42a-40f3-a60b-718269c4df50
**Consultation Date**: 2025-10-31

### Key Validation Points

1. ✅ **Migrating ALL agents to JSON is correct**
   > "This isn't just a minor improvement; it's a foundational architectural enhancement that will pay dividends in stability and future development speed."

2. ✅ **Incremental migration is mandatory**
   > "Incremental migration is the only safe and professional approach for a live production system. A 'big bang' migration is unacceptably risky."

3. ✅ **Envelope pattern is best practice**
   > "A best practice for event-driven systems is to use an 'envelope' structure... allows you to introduce completely different types of events in the future."

4. ✅ **Backward compatibility critical**
   > "Update the consumer (WebSocket handler) to be backward-compatible first, then migrate agents one by one using a feature flag."

5. ✅ **TypedDict for type safety**
   > "You can define this schema using TypedDict. This gives you static analysis and autocomplete support."

---

## Next Steps

1. **Immediate** (This Sprint):
   - [ ] Test Researcher agent in production with `AGENT_JSON_MIGRATION=researcher`
   - [ ] Monitor for 24-48 hours
   - [ ] Verify zero status mix-ups

2. **Short-term** (Next Sprint):
   - [ ] Migrate Writer agent (next in pipeline)
   - [ ] Migrate Translator agent
   - [ ] Continue progressive rollout

3. **Long-term** (Following Sprint):
   - [ ] Complete all 8 agents migration
   - [ ] Enable `ENABLE_JSON_OUTPUT=true` globally
   - [ ] Remove legacy regex parsing code
   - [ ] Update all documentation

---

**Status**: ✅ **PHASE 2.1 + 2.2 COMPLETE** - Infrastructure and pilot agent ready for production testing
**Next**: Deploy to production and monitor Researcher agent with JSON output
**Confidence Level**: HIGH (Gemini-validated, type-safe, backward-compatible)

---

*Generated: 2025-10-31*
*Gemini Session: eee27430-a42a-40f3-a60b-718269c4df50*
