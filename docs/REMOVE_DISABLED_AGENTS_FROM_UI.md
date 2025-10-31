# Removing Disabled Agents from Frontend UI

## Summary

Removed Reviewer and Reviser agent cards from the frontend to accurately reflect the backend workflow, which disabled these agents for performance optimization.

## Rationale

The backend workflow intentionally **disables** Reviewer and Reviser agents to:
- ⏱️ **Reduce research time**: From 6+ minutes to 3-4 minutes
- 💰 **Lower API costs**: Eliminates BRAVE search calls for fact-checking
- 📊 **Maintain quality**: Output quality remains high without these agents

Displaying them in the frontend was misleading since they never execute.

## Changes Made

### 1. Frontend Store (`sessionStore.ts`)

**AGENT_PIPELINE_ORDER**:
```typescript
// Before (8 agents)
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator', 'Reviewer', 'Reviser'  // ❌ Misleading
]

// After (6 agents)
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator'  // ✅ Accurate
]
```

**Agent Count**:
```typescript
// Before
const agentsTotal = ref(8)

// After
const agentsTotal = ref(6)  // 6 active agents (Reviewer & Reviser disabled)
```

### 2. Backend WebSocket Handler (`websocket_handler.py`)

**AGENT_PIPELINE**:
```python
# Before
AGENT_PIPELINE = ['Browser', 'Editor', 'Researcher', 'Writer', 'Publisher', 'Translator', 'Reviewer', 'Reviser']

# After
AGENT_PIPELINE = ['Browser', 'Editor', 'Researcher', 'Writer', 'Publisher', 'Translator']
```

**AGENT_NAME_MAP** - Added filtering for disabled agents:
```python
AGENT_NAME_MAP = {
    # Active pipeline agents
    'BROWSER': 'Browser',
    'EDITOR': 'Editor',
    'RESEARCHER': 'Researcher',
    'WRITER': 'Writer',
    'PUBLISHER': 'Publisher',
    'TRANSLATOR': 'Translator',
    # ... other mappings ...

    # Disabled agents - filtered out if they somehow send events
    'REVIEWER': None,  # Disabled for performance
    'REVISER': None,  # Disabled for performance
    'REVISOR': None,  # Alternative name for Reviser
}
```

**Event counts updated**:
```python
# create_research_status_event default parameter
agents_total: int = 6  # Changed from 8

# Initial connection event
agents_total=6  # Changed from 8

# Start event
agents_total=6  # Changed from 8

# Completion event
agents_completed=6,  # Changed from 8
agents_total=6  # Changed from 8
```

### 3. Backend Schemas (`schemas.py`)

**Function signature**:
```python
# Before
def create_research_status_event(
    session_id: str,
    overall_status: str,
    progress: float,
    current_stage: Optional[str] = None,
    agents_completed: int = 0,
    agents_total: int = 8,  # ❌ Incorrect count
    estimated_completion: Optional[datetime] = None
) -> ResearchStatusEvent:

# After
def create_research_status_event(
    session_id: str,
    overall_status: str,
    progress: float,
    current_stage: Optional[str] = None,
    agents_completed: int = 0,
    agents_total: int = 6,  # ✅ Correct count (Reviewer & Reviser disabled)
    estimated_completion: Optional[datetime] = None
) -> ResearchStatusEvent:
```

### 4. Documentation (`AGENT_NAME_MAPPING.md`)

Updated to reflect:
- Only 6 active pipeline agents
- Reviewer and Reviser listed as "Disabled Agents"
- Explanation of why they were disabled
- Correct frontend AGENT_PIPELINE_ORDER
- Correct backend AGENT_NAME_MAP

## Backend Evidence of Disabled Agents

### Not Instantiated
```python
# orchestrator.py:190-198
def _initialize_agents(self):
    return {
        "writer": WriterAgent(...),
        "editor": EditorAgent(...),
        "research": ResearchAgent(...),
        "translator": TranslatorAgent(...),
        "publisher": PublisherAgent(...),
        "human": HumanAgent(...)
        # ❌ No "reviewer" or "reviser" keys
    }
```

### Not Imported
```python
# orchestrator.py:51-57
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent, \
    HumanAgent, \
    TranslatorAgent
# ❌ ReviewerAgent and ReviserAgent NOT imported
```

### Workflow Bypasses Them
```python
# orchestrator.py:223-225
# SIMPLIFIED WORKFLOW: Direct path from writer to publisher (no review/revision)
# Writer → Publisher (bypass reviewer/reviser agents)
workflow.add_edge('writer', 'publisher')
```

## Frontend UI Impact

### Before (Misleading)
```
┌─────────┐  ┌────────┐  ┌────────────┐  ┌────────┐
│ Browser │→ │ Editor │→ │ Researcher │→ │ Writer │→
└─────────┘  └────────┘  └────────────┘  └────────┘

┌───────────┐  ┌────────────┐  ┌──────────┐  ┌─────────┐
│ Publisher │→ │ Translator │→ │ Reviewer │→ │ Reviser │
└───────────┘  └────────────┘  └──────────┘  └─────────┘
                                    ↑              ↑
                              (Never runs)  (Never runs)
```

### After (Accurate)
```
┌─────────┐  ┌────────┐  ┌────────────┐  ┌────────┐
│ Browser │→ │ Editor │→ │ Researcher │→ │ Writer │→
└─────────┘  └────────┘  └────────────┘  └────────┘

┌───────────┐  ┌────────────┐
│ Publisher │→ │ Translator │
└───────────┘  └────────────┘
```

## Actual Workflow

```
Browser (Initial Research)
   ↓
Planner (Structure Outline) [EditorAgent.plan_research]
   ↓
Human (Optional Review)
   ↓
Researcher (Deep Research) [EditorAgent.run_parallel_research]
   ↓
Writer (Create Draft)
   ↓
Publisher (Save Files) ← DIRECT PATH (no review/revision)
   ↓
Translator (Optional Translation)
   ↓
END
```

## Benefits of This Change

1. **Accurate UI**: Frontend now shows exactly what runs
2. **No Confusion**: Users won't wonder why Reviewer/Reviser stay "Pending"
3. **Correct Metrics**:
   - Progress calculation based on 6 agents (not 8)
   - "Agents: 0/6" instead of "0/8"
   - "Completed: 6" instead of "8" at the end
4. **Performance Transparency**: Users understand the streamlined workflow
5. **Code Consistency**: Frontend matches backend workflow architecture

## Testing Verification

After these changes, verify:

- [ ] Frontend displays exactly 6 agent cards
- [ ] No Reviewer or Reviser cards visible
- [ ] Agent count shows "0 / 6" (not "0 / 8")
- [ ] When complete, shows "6 / 6" (not "6 / 8")
- [ ] Progress bar calculates correctly (100% when 6 agents done)
- [ ] Backend logs don't show reviewer/reviser events
- [ ] If reviewer/reviser somehow send events, they're filtered (mapped to None)

## Files Modified

| File | Changes |
|------|---------|
| `frontend_poc/src/stores/sessionStore.ts` | AGENT_PIPELINE_ORDER: 8→6 agents, agentsTotal: 8→6 |
| `web_dashboard/websocket_handler.py` | AGENT_PIPELINE: 8→6 agents, AGENT_NAME_MAP: added REVIEWER/REVISER/REVISOR→None, 3 occurrences of agents_total: 8→6 |
| `web_dashboard/schemas.py` | create_research_status_event default: agents_total: 8→6 |
| `docs/AGENT_NAME_MAPPING.md` | Updated to reflect 6 active agents, added disabled agents section |

## Related Documentation

- **Why agents were disabled**: `docs/FIX_TRANSLATOR_FINAL.md`
- **Workflow architecture**: `multi_agents/agents/orchestrator.py:283-297`
- **Agent name mapping**: `docs/AGENT_NAME_MAPPING.md`

## Conclusion

The frontend now accurately represents the backend workflow:
- ✅ 6 active agents displayed
- ✅ Reviewer and Reviser removed from UI
- ✅ Agent counts correct (6 total, not 8)
- ✅ No misleading "Pending" agents that never run
- ✅ Performance benefits clearly communicated

This change eliminates confusion and accurately reflects the optimized research pipeline.

---

**Date**: October 31, 2025
**Issue Reported By**: User observation
**Implemented By**: TK9 Development Team
