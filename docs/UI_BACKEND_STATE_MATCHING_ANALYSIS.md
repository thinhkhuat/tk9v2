# UI-Backend State Matching Analysis

**Date**: October 31, 2025
**Status**: 🔴 **CRITICAL ISSUES IDENTIFIED**

## Executive Summary

The TK9 Dashboard has **three critical architectural flaws** in how UI components match backend state:

1. **Orchestrator Agent is Invisible** - Events are sent but no card displays them
2. **Research Completion is Silent** - UI receives completion event but shows nothing to user
3. **Agent Pipeline Mismatch** - Backend workflow doesn't match frontend expectations

---

## 📊 Complete Flow: Backend → WebSocket → Frontend → UI

### 1. Backend Agent Execution Flow

#### Agent Workflow (orchestrator.py)
```python
# Line 204-210: Workflow nodes
workflow.add_node("browser", agents["research"].run_initial_research)
workflow.add_node("planner", agents["editor"].plan_research)
workflow.add_node("researcher", agents["editor"].run_parallel_research)
workflow.add_node("writer", agents["writer"].run)
workflow.add_node("translator", agents["translator"].run)
workflow.add_node("publisher", agents["publisher"].run)
workflow.add_node("human", agents["human"].review_plan)
```

#### Workflow Execution Order
```
1. browser    → ResearchAgent.run_initial_research()
2. planner    → EditorAgent.plan_research()
3. human      → HumanAgent.review_plan() [optional]
4. researcher → EditorAgent.run_parallel_research()
5. writer     → WriterAgent.run()
6. publisher  → PublisherAgent.run()
7. translator → TranslatorAgent.run() [conditional]
```

#### Agent Output Examples

**Browser Agent** (researcher.py:61-64):
```python
print_structured_output(
    message=f"Running initial research on query: {query}",
    agent="BROWSER",  # ✅ Correct as of latest fix
    status="running"
)
```

**Editor Agent** (editor.py:40-42):
```python
print_agent_output(
    "Planning an outline layout based on initial research...",
    agent="EDITOR"
)
```

**Orchestrator** (from user's logs):
```json
{
  "type": "agent_update",
  "payload": {
    "agent_id": "orchestrator",
    "agent_name": "ORCHESTRATOR",
    "status": "running",
    "message": "Translation needed for language: vi"
  }
}
```

---

### 2. Backend Name Mapping (websocket_handler.py)

#### AGENT_NAME_MAP Configuration
```python
# Line 22-39
AGENT_NAME_MAP = {
    # Active pipeline agents
    'BROWSER': 'Browser',
    'EDITOR': 'Editor',
    'RESEARCHER': 'Researcher',
    'RESEARCH': 'Researcher',
    'WRITER': 'Writer',
    'PUBLISHER': 'Publisher',
    'TRANSLATOR': 'Translator',
    'MASTER': 'Editor',         # ⚠️ MAPS TO EDITOR
    'ORCHESTRATOR': 'Editor',   # ⚠️ MAPS TO EDITOR

    # Infrastructure agents - filtered out
    'PROVIDERS': None,
    'LANGUAGE': None,

    # Disabled agents
    'REVIEWER': None,
    'REVISER': None,
    'REVISOR': None,
}
```

#### Name Mapping Logic (lines 152-188)
```python
def parse_agent_from_output(self, line: str):
    # Try JSON first
    event = json.loads(line.strip())
    if event.get("type") == "agent_update":
        payload = event["payload"]

        # Get agent name from payload
        raw_agent_name = payload.get("agent_name", "")
        agent_id = payload.get("agent_id", "")

        # Try mapping by agent_name (uppercase)
        agent_name_upper = raw_agent_name.upper()
        if agent_name_upper in AGENT_NAME_MAP:
            mapped_name = AGENT_NAME_MAP[agent_name_upper]
            if mapped_name is None:
                return None  # Skip infrastructure agent
            agent_name = mapped_name  # "ORCHESTRATOR" → "Editor"

        return (agent_name, message, payload)
```

**🔴 CRITICAL PROBLEM 1**: Orchestrator Events Merged Into Editor

When backend sends:
```json
{"agent_name": "ORCHESTRATOR", "message": "Translation needed..."}
```

Mapping transforms it to:
```json
{"agent_name": "Editor", "message": "Translation needed..."}
```

Result: **Editor card displays Orchestrator's work**, making Orchestrator invisible!

---

### 3. Frontend State Management (sessionStore.ts)

#### Agent Pipeline Order (line 25-28)
```typescript
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator'
]
// Total: 6 agents
// Missing: Orchestrator (merged into Editor due to mapping)
```

#### Agent State Storage (line 39)
```typescript
// Map<agent_name, AgentUpdatePayload>
const agents = ref<Map<string, AgentUpdatePayload>>(new Map())
```

#### Event Handling (lines 195-233)
```typescript
function handleEvent(event: WebSocketEvent) {
  // Add to event log
  events.value.push(event)

  // Route by event type
  switch (event.event_type) {
    case 'agent_update':
      handleAgentUpdate(event.payload)  // Update agent card
      break
    case 'research_status':
      handleResearchStatus(event.payload)  // Update overall status
      break
    case 'file_generated':
      handleFileGenerated(event.payload)  // Add file
      break
    case 'error':
      handleError(event.payload)  // Show error
      break
    case 'log':
      handleLog(event.payload)  // Add to log stream
      break
  }
}
```

#### Agent Update Handler (lines 235-251)
```typescript
function handleAgentUpdate(payload: AgentUpdatePayload) {
  // KEY FIX: Use agent_name as Map key
  agents.value.set(payload.agent_name, payload)

  // Example:
  // agents.value.set("Browser", {...})
  // agents.value.set("Editor", {...})  ← Both EDITOR and ORCHESTRATOR update this!
  // agents.value.set("Researcher", {...})

  console.log(`🤖 Agent ${payload.agent_name}: ${payload.status}`)
}
```

**🔴 CRITICAL PROBLEM 2**: Map Key Collision

When Orchestrator sends event:
1. Backend maps `"ORCHESTRATOR"` → `"Editor"`
2. Frontend stores: `agents.value.set("Editor", {...})`
3. **Overwrites** any previous Editor state!
4. Result: Editor and Orchestrator compete for same Map slot

---

### 4. UI Component Rendering

#### AgentFlow.vue (lines 14-50)
```vue
<template>
  <div class="flex items-center justify-start overflow-x-auto pb-4 gap-2">
    <!-- Loop through AGENT_PIPELINE_ORDER -->
    <template v-for="(agent, index) in store.orderedAgents" :key="agent.agent_id">
      <!-- Render AgentCard for each agent -->
      <AgentCard :agent="agent" />

      <!-- Connecting arrow between cards -->
      <div v-if="index < store.orderedAgents.length - 1">
        <svg><!-- Arrow icon --></svg>
      </div>
    </template>
  </div>
</template>
```

#### Ordered Agents Computed (sessionStore.ts:71-86)
```typescript
const orderedAgents = computed(() => {
  return AGENT_PIPELINE_ORDER.map(agentName => {
    // O(1) lookup in agents Map
    const agentData = agents.value.get(agentName)

    // Return actual data or default "pending" state
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

**How it Works**:
1. For each name in `AGENT_PIPELINE_ORDER` (`['Browser', 'Editor', ...]`)
2. Look up in `agents` Map: `agents.value.get("Browser")`
3. If found: Return agent data
4. If not found: Return default "pending" state
5. Render AgentCard with this data

**Result**:
- ✅ Shows 6 cards (correct)
- ❌ Editor card shows **last update** (either Editor OR Orchestrator, whichever was last)
- ❌ No Orchestrator card (not in pipeline order)

---

### 5. Research Completion Flow

#### Backend Sends Completion (websocket_handler.py:350-359)
```python
# After CLI process finishes
completion_event = create_research_status_event(
    session_id=session_id,
    overall_status="completed",  # ← KEY STATUS
    progress=100.0,
    current_stage="Research completed",
    agents_completed=6,
    agents_total=6
)
await self.send_event(session_id, completion_event)
```

#### Frontend Receives Completion (sessionStore.ts:258-268)
```typescript
function handleResearchStatus(payload: ResearchStatusPayload) {
  overallStatus.value = payload.overall_status  // "completed"
  overallProgress.value = Math.round(payload.progress)  // 100
  currentStage.value = payload.current_stage  // "Research completed"
  agentsCompleted.value = payload.agents_completed  // 6
  agentsTotal.value = payload.agents_total  // 6

  console.log(`📊 Research status: ${payload.overall_status} (${payload.progress}%)`)

  // ⚠️ NO TOAST NOTIFICATION
  // ⚠️ NO UI CALLBACK
  // ⚠️ NO VISUAL FEEDBACK
}
```

#### Completion Detection (sessionStore.ts:114-116)
```typescript
const isResearchCompleted = computed(() => {
  return overallStatus.value === 'completed'
})
```

**🔴 CRITICAL PROBLEM 3**: Silent Completion

When research completes:
1. ✅ Backend sends `research_status` event with `overall_status: "completed"`
2. ✅ Frontend updates `overallStatus.value = "completed"`
3. ✅ Computed `isResearchCompleted` becomes `true`
4. ❌ **NO UI FEEDBACK** - User doesn't know it's done!
5. ❌ **NO TOAST** - Unlike `startNewSession()` which shows toast
6. ❌ **NO CALLBACK** - No component listens to `isResearchCompleted`

---

## 🔍 State Matching Summary

### What Works ✅

1. **WebSocket Connection**: Reliable, auto-reconnects
2. **Event Parsing**: JSON events parsed correctly
3. **Agent State Updates**: Map updates work (when keys don't collide)
4. **Reactive Rendering**: Vue 3 reactivity works perfectly
5. **Log Streaming**: All events logged correctly
6. **File Tracking**: Files array populates correctly

### What's Broken 🔴

1. **Orchestrator Visibility**:
   - Backend sends: `ORCHESTRATOR` events
   - Mapping converts to: `Editor`
   - Result: **Orchestrator work is invisible**

2. **Research Completion Feedback**:
   - Backend sends: `research_status: "completed"`
   - Frontend updates: `overallStatus = "completed"`
   - Result: **User sees nothing happen**

3. **Agent Pipeline Mismatch**:
   - Backend executes: 7 steps (browser → planner → human → researcher → writer → publisher → translator)
   - Frontend shows: 6 cards (Browser, Editor, Researcher, Writer, Publisher, Translator)
   - Result: **Planner and Human steps are invisible**

---

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Workflow Nodes:                                                │
│  1. browser    → ResearchAgent.run_initial_research()           │
│     └─ Outputs: agent="BROWSER" ✅                              │
│                                                                  │
│  2. planner    → EditorAgent.plan_research()                    │
│     └─ Outputs: agent="EDITOR" ⚠️                               │
│                                                                  │
│  3. human      → HumanAgent.review_plan() [optional]            │
│     └─ Outputs: (none - no structured output)                   │
│                                                                  │
│  4. researcher → EditorAgent.run_parallel_research()            │
│     └─ Outputs: agent="RESEARCHER" ✅                           │
│                                                                  │
│  5. writer     → WriterAgent.run()                              │
│     └─ Outputs: agent="WRITER" ✅                               │
│                                                                  │
│  6. publisher  → PublisherAgent.run()                           │
│     └─ Outputs: agent="PUBLISHER" ✅                            │
│                                                                  │
│  7. translator → TranslatorAgent.run() [conditional]            │
│     └─ Outputs: agent="TRANSLATOR" ✅                           │
│                                                                  │
│  Orchestrator (ChiefEditorAgent):                               │
│     └─ Outputs: agent="ORCHESTRATOR" ⚠️                         │
│                                                                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ JSON Events via print_structured_output()
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              WEBSOCKET HANDLER (websocket_handler.py)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AGENT_NAME_MAP:                                                │
│    "BROWSER"      → "Browser" ✅                                │
│    "EDITOR"       → "Editor" ✅                                 │
│    "ORCHESTRATOR" → "Editor" ⚠️  ← COLLISION!                  │
│    "RESEARCHER"   → "Researcher" ✅                             │
│    "WRITER"       → "Writer" ✅                                 │
│    "PUBLISHER"    → "Publisher" ✅                              │
│    "TRANSLATOR"   → "Translator" ✅                             │
│                                                                  │
│  parse_agent_from_output():                                     │
│    1. Parse JSON event                                          │
│    2. Map agent_name to frontend name                           │
│    3. Send via WebSocket                                        │
│                                                                  │
│  stream_cli_output():                                           │
│    - Sends: research_status "completed" when CLI finishes       │
│                                                                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ WebSocket Events
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                FRONTEND STATE (sessionStore.ts)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  agents = Map<agent_name, AgentUpdatePayload>                   │
│    "Browser"    → {status: "completed", ...} ✅                 │
│    "Editor"     → {status: "running", ...} ⚠️                   │
│                   ↑                                              │
│                   └─ Contains EITHER Editor OR Orchestrator     │
│                      (whichever sent event last)                │
│    "Researcher" → {status: "completed", ...} ✅                 │
│    "Writer"     → {status: "completed", ...} ✅                 │
│    "Publisher"  → {status: "completed", ...} ✅                 │
│    "Translator" → {status: "running", ...} ✅                   │
│                                                                  │
│  AGENT_PIPELINE_ORDER = [                                       │
│    'Browser', 'Editor', 'Researcher',                           │
│    'Writer', 'Publisher', 'Translator'                          │
│  ]                                                               │
│                                                                  │
│  orderedAgents = computed(() => {                               │
│    return AGENT_PIPELINE_ORDER.map(name =>                      │
│      agents.value.get(name) || defaultPending                   │
│    )                                                             │
│  })                                                              │
│                                                                  │
│  handleResearchStatus(payload):                                 │
│    overallStatus.value = payload.overall_status                 │
│    // ⚠️ NO TOAST, NO CALLBACK when "completed"                │
│                                                                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ Reactive Computed Properties
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   UI COMPONENTS (Vue)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AgentFlow.vue:                                                 │
│    <AgentCard v-for="agent in store.orderedAgents">            │
│      - Browser    [✅ Completed]                                │
│      - Editor     [🔄 Running] ← SHOWS ORCHESTRATOR WORK       │
│      - Researcher [✅ Completed]                                │
│      - Writer     [✅ Completed]                                │
│      - Publisher  [✅ Completed]                                │
│      - Translator [🔄 Running]                                  │
│    </AgentCard>                                                 │
│                                                                  │
│  ProgressTracker.vue:                                           │
│    Current Stage: {{ store.currentStage }}                      │
│    Status: {{ store.overallStatus }}                            │
│    Agents: {{ store.agentsCompleted }} / {{ store.agentsTotal }}│
│                                                                  │
│  ⚠️ NO COMPLETION DIALOG                                        │
│  ⚠️ NO SUCCESS TOAST                                            │
│  ⚠️ NO "DOWNLOAD FILES" BUTTON                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Root Causes

### Root Cause 1: Name Mapping Collision
**Problem**: Multiple backend agents map to same frontend agent name

**Example**:
- `EDITOR` → `"Editor"`
- `ORCHESTRATOR` → `"Editor"`
- `MASTER` → `"Editor"`

**Result**: All three update the same Map entry, losing individual agent visibility

**Why It Exists**: Original design assumed Editor/Master/Orchestrator were aliases for same agent

**Reality**: They are **different workflow steps**

---

### Root Cause 2: Missing Completion UX
**Problem**: No user-facing feedback when research completes

**Current Flow**:
```
Backend finishes → Sends "completed" event → Frontend updates state → NOTHING VISIBLE
```

**Expected Flow**:
```
Backend finishes → Sends "completed" event → Frontend updates state → Shows toast → Enables download button
```

**Why It Exists**: Phase 2 migration focused on agent updates, not completion UX

---

### Root Cause 3: Workflow vs Pipeline Mismatch
**Problem**: Backend executes 7+ steps, frontend shows 6 cards

**Backend Workflow**:
1. browser
2. planner
3. human (optional)
4. researcher
5. writer
6. publisher
7. translator (conditional)

**Frontend Pipeline**:
1. Browser
2. Editor
3. Researcher
4. Writer
5. Publisher
6. Translator

**Missing**:
- Planner step (merged into Editor)
- Human step (no card)
- Orchestrator step (merged into Editor)

---

## 📝 Recommendations

### Immediate Fixes (High Priority)

1. **Add Completion Toast**
   ```typescript
   // sessionStore.ts:258
   function handleResearchStatus(payload: ResearchStatusPayload) {
     overallStatus.value = payload.overall_status

     // NEW: Show toast on completion
     if (payload.overall_status === 'completed') {
       toast.success('🎉 Research completed successfully!')
     }
   }
   ```

2. **Add Orchestrator Card**
   ```typescript
   // sessionStore.ts:25
   const AGENT_PIPELINE_ORDER = [
     'Browser', 'Editor', 'Researcher', 'Writer',
     'Publisher', 'Translator', 'Orchestrator'  // NEW
   ]
   ```

3. **Fix Name Mapping**
   ```python
   # websocket_handler.py:22
   AGENT_NAME_MAP = {
     'ORCHESTRATOR': 'Orchestrator',  # NEW: Separate card
     'MASTER': 'Editor',  # Keep as Editor alias
     'EDITOR': 'Editor',
     # ...
   }
   ```

### Long-term Fixes (Architectural)

1. **Separate Workflow Steps from UI Cards**: Not all workflow nodes need cards
2. **Add Workflow State Machine**: Track research phase (browsing → planning → researching → writing → publishing)
3. **Implement Completion Callbacks**: Trigger UI actions when research completes
4. **Add Progress Estimation**: Calculate real progress based on completed workflow nodes

---

## 🧪 Testing Verification

After implementing fixes, verify:

- [ ] Orchestrator card appears in pipeline
- [ ] Orchestrator events update Orchestrator card (not Editor)
- [ ] Toast notification shows when research completes
- [ ] Download button enables when research completes
- [ ] All 7 cards show in pipeline (if adding all workflow steps)
- [ ] No Map key collisions (check browser console)
- [ ] Completion status persists after page refresh

---

**Document Version**: 1.0
**Author**: AI Analysis
**Last Updated**: 2025-10-31
