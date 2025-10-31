# Agent Name Mapping Documentation

## Overview

The TK9 Deep Research system uses multiple agents during the research process. Some agents are part of the research pipeline (visible in the frontend), while others are infrastructure/configuration agents (not visible). This document describes the correct approach to map agent names between the CLI output, backend processing, and frontend display.

## Agent Categories

### 1. Pipeline Agents (Visible in Frontend)
These agents perform the core research workflow and are displayed as cards in the frontend UI:

| Frontend Name | CLI Names | Description |
|--------------|-----------|-------------|
| Browser | BROWSER | Web browsing and URL extraction |
| Editor | EDITOR, MASTER, ORCHESTRATOR | Research planning and coordination |
| Researcher | RESEARCHER, RESEARCH | Conducting research and gathering information |
| Writer | WRITER | Writing the research report |
| Publisher | PUBLISHER | Publishing and formatting the final report |
| Translator | TRANSLATOR | Translating reports to target language |

### 2. Infrastructure & Disabled Agents (Hidden from Frontend)
These agents either handle configuration/setup or are disabled for performance optimization:

| CLI Name | Purpose | Why Hidden |
|----------|---------|-----------|
| PROVIDERS | Provider configuration validation | System setup, not research work |
| LANGUAGE | Language configuration | System setup, not research work |
| REVIEWER | Report quality review | **DISABLED** - Removed for performance (saves 2-3 minutes) |
| REVISER/REVISOR | Draft revisions | **DISABLED** - Removed for performance (saves 2-3 minutes) |

**Note on Disabled Agents**: The Reviewer and Reviser agents exist in the codebase but are not instantiated or used in the workflow. They were disabled to:
- Reduce research time from 6+ minutes to 3-4 minutes
- Lower API costs (no BRAVE calls for fact-checking)
- Maintain output quality while eliminating resource waste

## Backend Mapping Configuration

### Location
`web_dashboard/websocket_handler.py`

### Code
```python
AGENT_NAME_MAP = {
    # Active pipeline agents - mapped to frontend names
    'BROWSER': 'Browser',
    'EDITOR': 'Editor',
    'RESEARCHER': 'Researcher',
    'RESEARCH': 'Researcher',  # Alternative name
    'WRITER': 'Writer',
    'PUBLISHER': 'Publisher',
    'TRANSLATOR': 'Translator',
    'MASTER': 'Editor',  # Maps to Editor
    'ORCHESTRATOR': 'Editor',  # Maps to Editor

    # Infrastructure agents - mapped to None (filtered out)
    'PROVIDERS': None,  # Don't show in pipeline
    'LANGUAGE': None,  # Don't show in pipeline

    # Disabled agents - mapped to None (filtered out if they somehow send events)
    'REVIEWER': None,  # Disabled for performance
    'REVISER': None,  # Disabled for performance
    'REVISOR': None,  # Alternative name for Reviser
}
```

### Mapping Rules

1. **Pipeline Agents**: Map to the exact frontend name (e.g., `'RESEARCHER' → 'Researcher'`)
2. **Alternative Names**: Multiple CLI names can map to the same frontend name (e.g., `MASTER` and `ORCHESTRATOR` both map to `Editor`)
3. **Infrastructure Agents**: Map to `None` to filter them from the frontend

## Frontend Configuration

### Location
`web_dashboard/frontend_poc/src/stores/sessionStore.ts`

### Code
```typescript
// Agent pipeline order (Phase 4: Agent Flow Visualization)
// NOTE: Reviewer and Reviser are DISABLED in the backend workflow for performance optimization
// Simplified workflow: Browser → Editor → Researcher → Writer → Publisher → Translator
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator'
]
```

### Display Rules

1. **Ordered Display**: Agents are displayed in the order defined in `AGENT_PIPELINE_ORDER`
2. **Status Tracking**: Each agent shows current status: `pending`, `running`, `completed`, `error`
3. **Progress Display**: Optional progress bar (only shown when agent provides explicit progress)

## How Agent Name Mapping Works

### Phase 1: CLI Output Parsing

When the CLI outputs agent messages, they come in two formats:

#### Format 1: JSON (Phase 2 - Structured Output)
```json
{
  "type": "agent_update",
  "payload": {
    "agent_id": "researcher",
    "agent_name": "RESEARCHER",
    "status": "running",
    "message": "Running initial research...",
    "progress": null
  }
}
```

#### Format 2: Legacy Text (Being Deprecated)
```
RESEARCHER: Running initial research...
EDITOR: Planning outline...
PROVIDERS: Configuration validated successfully...
```

### Phase 2: Backend Name Normalization

The WebSocket handler (`websocket_handler.py`) parses both formats:

```python
def parse_agent_from_output(self, line: str) -> tuple[str, str, dict | None] | None:
    # Try JSON first
    try:
        event = json.loads(line.strip())
        if event.get("type") == "agent_update":
            payload = event["payload"]
            agent_id = payload.get("agent_id", "").upper()

            # Check if infrastructure agent (skip it)
            if agent_id in AGENT_NAME_MAP and AGENT_NAME_MAP[agent_id] is None:
                logger.debug(f"⏭️ Skipping infrastructure agent: {agent_id}")
                return None

            # Map to frontend name
            agent_name = AGENT_NAME_MAP.get(agent_id, agent_id.capitalize())
            message = payload.get("message", "")
            return (agent_name, message, payload)
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Fall back to legacy text parsing
    match = re.search(r'([A-Z_]+):\s*(.+)', clean_line)
    if match:
        cli_agent_name = match.group(1)
        if cli_agent_name in AGENT_NAME_MAP:
            frontend_name = AGENT_NAME_MAP[cli_agent_name]
            if frontend_name is None:
                # Skip infrastructure agent
                return None
            return (frontend_name, message, None)

    return None
```

### Phase 3: Frontend Display

The frontend (`sessionStore.ts`) receives WebSocket events:

```typescript
function handleAgentUpdate(payload: AgentUpdatePayload) {
  // Update agent state in reactive Map
  agents.value.set(payload.agent_id, payload)

  // Frontend only displays agents in AGENT_PIPELINE_ORDER
  // Infrastructure agents are never stored or displayed
}

const orderedAgents = computed(() => {
  return AGENT_PIPELINE_ORDER.map(agentName => {
    // Find agent data from reactive map
    const agentData = Array.from(agents.value.values()).find(
      a => a.agent_name === agentName
    )

    // Return actual data or default pending state
    return agentData || {
      agent_id: agentName.toLowerCase(),
      agent_name: agentName,
      status: 'pending',
      progress: null,
      message: 'Waiting to start...'
    }
  })
})
```

## Adding New Agents

### Step 1: Determine Agent Category

**Question**: Is this agent part of the research workflow that users should see?

- **YES** → Pipeline Agent (add to frontend)
- **NO** → Infrastructure Agent (map to None)

### Step 2: Update Backend Mapping

Edit `web_dashboard/websocket_handler.py`:

```python
AGENT_NAME_MAP = {
    # ... existing mappings ...

    # For pipeline agent:
    'NEW_AGENT_CLI_NAME': 'FrontendName',

    # For infrastructure agent:
    'NEW_INFRA_AGENT': None,
}
```

### Step 3: Update Frontend (Pipeline Agents Only)

Edit `web_dashboard/frontend_poc/src/stores/sessionStore.ts`:

```typescript
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator', 'Reviewer', 'Reviser',
  'FrontendName'  // Add new agent to pipeline
]
```

### Step 4: Update CLI Output

Ensure the agent outputs the correct name:

```python
# For pipeline agents
from agents.utils.views import print_structured_output

print_structured_output(
    message="Doing work...",
    agent="NEW_AGENT_CLI_NAME",  # Must match AGENT_NAME_MAP key
    status="running",
    progress=50  # Optional, use None if no progress tracking
)

# For infrastructure agents
print_structured_output(
    message="Configuration complete",
    agent="NEW_INFRA_AGENT",  # Will be filtered out
    status="completed"
)
```

## Validation Checklist

When adding or modifying agent names, verify:

- [ ] CLI name is in `AGENT_NAME_MAP` in `websocket_handler.py`
- [ ] Pipeline agents map to a frontend name (not None)
- [ ] Infrastructure agents map to None
- [ ] Frontend name is in `AGENT_PIPELINE_ORDER` (pipeline agents only)
- [ ] Agent uses `print_structured_output()` with correct agent name
- [ ] Backend logs show `✅ Sent JSON-based agent_update` (not errors)
- [ ] Frontend displays agent card with correct status (pipeline agents only)
- [ ] Infrastructure agents are logged but not displayed

## Troubleshooting

### Issue: Agent card not updating in frontend

**Symptoms**: Agent stays at "Pending" status despite backend logs showing activity

**Diagnosis**:
1. Check backend logs for agent name being sent
2. Verify agent name is in `AGENT_NAME_MAP`
3. Check if mapped name is in `AGENT_PIPELINE_ORDER`

**Fix**:
```python
# websocket_handler.py
AGENT_NAME_MAP = {
    'CLI_NAME': 'FrontendName',  # Ensure mapping exists
}
```

```typescript
// sessionStore.ts
const AGENT_PIPELINE_ORDER = [
  'FrontendName',  // Ensure name is in order
]
```

### Issue: Backend error "Unknown agent name"

**Symptoms**: Logs show errors about unmapped agent names

**Fix**: Add agent to `AGENT_NAME_MAP`:
```python
AGENT_NAME_MAP = {
    'MISSING_AGENT': 'MappedName',  # Add missing mapping
}
```

### Issue: Too many agents showing in frontend

**Symptoms**: Infrastructure agents appearing as cards

**Fix**: Map infrastructure agents to `None`:
```python
AGENT_NAME_MAP = {
    'INFRA_AGENT': None,  # Change from name to None
}
```

## Examples

### Example 1: Adding a "Fact-Checker" Agent

1. **Update backend mapping**:
```python
AGENT_NAME_MAP = {
    # ... existing ...
    'FACTCHECKER': 'FactChecker',
    'FACT_CHECKER': 'FactChecker',  # Alternative name
}
```

2. **Update frontend pipeline**:
```typescript
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'FactChecker',
  'Writer', 'Publisher', 'Translator', 'Reviewer', 'Reviser'
]
```

3. **Use in agent code**:
```python
print_structured_output(
    message="Checking facts against sources...",
    agent="FACTCHECKER",
    status="running",
    progress=75
)
```

### Example 2: Adding a "Database-Init" Infrastructure Agent

1. **Update backend mapping only**:
```python
AGENT_NAME_MAP = {
    # ... existing ...
    'DATABASE_INIT': None,  # Infrastructure agent
}
```

2. **No frontend changes needed** (agent won't be displayed)

3. **Use in agent code**:
```python
print_structured_output(
    message="Database initialized successfully",
    agent="DATABASE_INIT",
    status="completed"
)
```

## Best Practices

1. **Use Uppercase for CLI Names**: `RESEARCHER`, `EDITOR`, `BROWSER`
2. **Use PascalCase for Frontend Names**: `Researcher`, `Editor`, `Browser`
3. **Map Infrastructure Agents to None**: Don't display system agents
4. **Document Alternative Names**: Explain why multiple names map to same agent
5. **Keep Pipeline Order Logical**: Follow the actual research workflow sequence
6. **Test Both Paths**: Verify both JSON and legacy text parsing work

## Related Files

- **Backend Mapping**: `web_dashboard/websocket_handler.py`
- **Frontend Pipeline**: `web_dashboard/frontend_poc/src/stores/sessionStore.ts`
- **Agent Output**: `multi_agents/agents/utils/views.py`
- **Type Definitions**: `web_dashboard/frontend_poc/src/types/events.ts`
- **Pydantic Schemas**: `web_dashboard/schemas.py`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-31 | Initial documentation with Phase 2 JSON support |

---

**Last Updated**: October 31, 2025
**Maintainer**: TK9 Development Team
