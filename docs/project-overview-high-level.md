# TK9 Deep Research System - High-Level Project Overview

**Generated**: 2025-10-31
**Purpose**: Comprehensive overview of Web Dashboard Backend, Frontend, Components, State Management, and Multi-Agent System
**Scope**: 500+ files analyzed across 5 major areas

---

## Table of Contents

1. [Web Dashboard Backend Architecture](#1-web-dashboard-backend-architecture)
2. [Web Dashboard Frontend Architecture](#2-web-dashboard-frontend-architecture)
3. [Frontend Component Library](#3-frontend-component-library)
4. [Frontend State Management (Pinia)](#4-frontend-state-management-pinia)
5. [Complete Multi-Agent System](#5-complete-multi-agent-system)
6. [System Integration](#6-system-integration)
7. [Key Technical Decisions](#7-key-technical-decisions)
8. [Development Guidelines](#8-development-guidelines)

---

## 1. Web Dashboard Backend Architecture

**Location**: `web_dashboard/`
**Technology Stack**: Python 3.12, FastAPI, WebSocket, asyncio
**Files**: 8 core Python files + utilities

### 1.1 Core Components

#### main.py (379 lines)
**Purpose**: FastAPI application entry point for the web dashboard

**Key Features**:
- FastAPI app with async/await architecture
- Lifespan management with periodic cleanup (every hour)
- CORS middleware for cross-origin requests
- Static file serving for frontend
- RESTful API endpoints + WebSocket

**API Endpoints**:
```python
POST   /api/research              # Submit new research request
GET    /api/session/{session_id}  # Get session state
GET    /download/{session_id}/{filename}  # Download generated files
WS     /ws/{session_id}            # WebSocket for real-time updates
```

**CORS Configuration**:
- localhost:5173 (Vite dev server)
- localhost:12656 (production build)
- tk9.thinhkhuat.com (public domain)
- tk9v2.thinhkhuat.com (backup domain)

**Lifespan Management**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown: cancel cleanup task
    cleanup_task.cancel()
```

---

#### cli_executor.py (201 lines)
**Purpose**: Execute CLI research command and stream output to WebSocket

**Critical Fix - Chunk-Based Reading**:
The module implements fixed-size chunk reading (4096 bytes) instead of `readline()` to prevent `LimitOverrunError` when CLI outputs extremely long lines (common during research with large context).

```python
# PHASE 1 FIX: Chunk-based reading prevents buffer overflow
buffer = ""
while True:
    chunk = await process.stdout.read(4096)  # Read fixed-size chunks
    if not chunk:
        break

    buffer += chunk.decode("utf-8", errors="replace")

    # Process complete lines from buffer
    while "\n" in buffer:
        line, _, buffer = buffer.partition("\n")
        cleaned_line = ANSI_ESCAPE_PATTERN.sub("", line).strip()
        if cleaned_line:
            yield cleaned_line + "\n"
```

**Command Structure**:
```bash
uv run python -m multi_agents.main \
  --research "query" \
  --language "vi" \
  --session-id "uuid" \
  --verbose
```

**Input Sanitization**: Removes dangerous characters: `` ` $ & | ; > < ( ) { } ``

---

#### websocket_handler.py (439 lines)
**Purpose**: Manage WebSocket connections and parse agent updates

**Agent Pipeline**:
```python
AGENT_PIPELINE = [
    "Browser",      # Initial research (GPT Researcher)
    "Editor",       # Planning and outline
    "Researcher",   # Parallel deep research
    "Writer",       # Report writing
    "Publisher",    # Final publishing
    "Translator",   # Multi-language translation
    "Orchestrator"  # Master coordinator
]
```

**Dual-Mode Parser** (Phase 2 Migration Strategy):
Supports both JSON format (new) and legacy text format for backward compatibility:

```python
def parse_agent_from_output(self, line: str) -> tuple[str, str, dict | None] | None:
    """
    1. JSON Format (Phase 2 - NEW):
       {"type": "agent_update", "payload": {...}}

    2. Text Format (Legacy):
       "AGENT_NAME: message"
    """
    # Try JSON parsing first
    try:
        event = json.loads(line.strip())
        if event.get("type") == "agent_update":
            # Process JSON event...
    except (json.JSONDecodeError, KeyError, TypeError):
        pass  # Fall through to legacy parsing

    # Legacy text format parsing...
```

**Agent Name Mapping**:
```python
AGENT_NAME_MAP = {
    "BROWSER": "Browser",
    "EDITOR": "Editor",
    "RESEARCHER": "Researcher",
    "RESEARCH": "Researcher",  # Alternative name
    "WRITER": "Writer",
    "PUBLISHER": "Publisher",
    "TRANSLATOR": "Translator",
    "ORCHESTRATOR": "Orchestrator",
    "MASTER": "Editor",  # ChiefEditor/Master maps to Editor
    # Disabled agents (mapped to None)
    "REVIEWER": None,
    "REVISER": None,
    "REVISOR": None,
    # Infrastructure agents (don't show in pipeline)
    "PROVIDERS": None,
    "LANGUAGE": None,
}
```

---

#### schemas.py (340 lines)
**Purpose**: Pydantic event schemas for type-safe WebSocket communication

**Event Types**:
```python
class AgentUpdatePayload(BaseModel):
    agent_id: str
    agent_name: str
    status: Literal["pending", "running", "completed", "error"]
    progress: Optional[float] = Field(None, ge=0, le=100)
    message: str
    stats: Optional[Dict[str, Any]] = None

class FileGeneratedPayload(BaseModel):
    file_id: str
    filename: str
    file_type: str  # 'pdf', 'docx', 'md'
    language: str
    size_bytes: int
    path: Optional[str] = None

class ResearchStatusPayload(BaseModel):
    overall_status: Literal["initializing", "running", "completed", "failed"]
    progress: float  # 0-100
    current_stage: Optional[str] = None
    agents_completed: int
    agents_total: int

# Union type for all events
WebSocketEvent = Union[
    AgentUpdateEvent,
    FileGeneratedEvent,
    ResearchStatusEvent,
    LogEvent,
    ErrorEvent,
    ConnectionStatusEvent,
    FilesReadyEvent,
]
```

**Helper Functions**:
```python
def create_agent_update_event(session_id, agent_id, agent_name, status,
                               progress, message, stats=None)
def create_file_generated_event(session_id, file_id, filename, file_type,
                                 language, size_bytes, path=None)
def create_research_status_event(session_id, overall_status, progress,
                                  current_stage=None, ...)
```

---

#### file_manager.py (280 lines)
**Purpose**: Manage research output files and serve for download

**Supported Extensions**: `.pdf`, `.docx`, `.md`

**UUID to Friendly Name Conversion**:
```python
def create_friendly_filename_from_uuid(self, uuid_filename: str) -> str:
    """
    Converts UUID-based filenames to user-friendly names:

    f84a84cb-dc65-4321-abe1-169c502ad2fe.pdf → research_report.pdf
    f84a84cb-dc65-4321-abe1-169c502ad2fe_vi.pdf → research_report_vi.pdf
    """
    name_part, extension = uuid_filename.rsplit(".", 1)

    # Check if translated file (ends with language code)
    if "_" in name_part and len(name_part.split("_")[-1]) <= 3:
        language_code = name_part.split("_")[-1]
        base_name = f"research_report_{language_code}"
    else:
        base_name = "research_report"

    return f"{base_name}.{extension}"
```

**Dynamic File Discovery**:
Instead of hard-coded expected files, the system dynamically discovers files in the session directory:

```python
async def discover_session_files(self, session_id: str) -> List[FileInfo]:
    """Discover actual files in session directory"""
    session_dir = self.outputs_path / session_id
    for file_path in session_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
            friendly_name = self.create_friendly_filename_from_uuid(file_path.name)
            file_info = FileInfo(
                filename=friendly_name,
                url=f"/download/{session_id}/{file_path.name}",
                size=file_path.stat().st_size,
                created=datetime.fromtimestamp(file_path.stat().st_ctime)
            )
            files.append(file_info)
    return files
```

**Automatic Cleanup**: Files older than 24 hours are automatically deleted via periodic cleanup task.

---

### 1.2 Backend Architecture Patterns

1. **Async/Await Throughout**: All I/O operations use async/await for maximum concurrency
2. **Background Tasks**: Long-running research executes in background via `BackgroundTasks`
3. **Process Management**: Subprocess handling with proper cleanup and error recovery
4. **Error Handling**: Try/except blocks with structured error events via WebSocket
5. **Session Isolation**: Each research session gets unique UUID and isolated output directory

---

## 2. Web Dashboard Frontend Architecture

**Location**: `web_dashboard/frontend_poc/`
**Technology Stack**: Vue 3.5.22, TypeScript, Vite, Tailwind CSS, Pinia
**Files**: 12 Vue components + store + services

### 2.1 Technology Stack

**Core Framework**:
```json
{
  "vue": "^3.5.22",           // Composition API, TypeScript support
  "pinia": "^3.0.3",          // State management
  "vue-toastification": "^2.0.0-rc.5",  // Toast notifications
  "axios": "^1.13.1"          // HTTP client
}
```

**Build Tools**:
```json
{
  "vite": "^7.1.7",           // Fast build tool
  "vue-tsc": "^3.1.0",        // TypeScript compiler
  "typescript": "~5.9.3"      // Type checking
}
```

**Styling**:
```json
{
  "tailwindcss": "^3.4.18",   // Utility-first CSS
  "autoprefixer": "^10.4.21", // CSS vendor prefixes
  "postcss": "^8.5.6"         // CSS transformations
}
```

---

### 2.2 Application Structure (App.vue)

**Component Hierarchy**:
```
App.vue (185 lines)
├── AppSkeletonLoader (initial loading)
├── ErrorMessage (error state)
└── Main Application UI
    ├── Research Form (when no active session)
    │   ├── Subject input
    │   ├── Language selector
    │   └── Submit button
    └── Active Session Dashboard
        ├── Session Header
        ├── AgentFlow (Phase 4: Agent visualization)
        └── Dashboard Grid
            ├── Left Column (Progress + Files)
            │   ├── ProgressTracker
            │   └── FileExplorer
            └── Right Column (Logs)
                └── LogViewer
```

**State Management Integration**:
```typescript
import { useSessionStore } from './stores/sessionStore'

const store = useSessionStore()

// Session lifecycle
onMounted(() => {
  const savedSessionId = localStorage.getItem('tk9_session_id')
  if (savedSessionId) {
    store.rehydrate(savedSessionId)  // Resume existing session
  } else {
    store.initializeNew()  // Fresh state
  }
})

async function submitResearch() {
  await store.startNewSession(researchSubject.value, researchLanguage.value)
}
```

**Conditional Rendering** (Phase 3):
```vue
<!-- 1. Show skeleton during initial load -->
<div v-if="store.isLoading">
  <AppSkeletonLoader />
</div>

<!-- 2. Show error message if something went wrong -->
<div v-else-if="store.appError">
  <ErrorMessage :message="store.appError" @retry="handleRetry" />
</div>

<!-- 3. Show main application UI -->
<div v-else>
  <!-- Research form or active session dashboard -->
</div>
```

---

### 2.3 Frontend Architecture Patterns

1. **Composition API**: All components use `<script setup lang="ts">` for better TypeScript support
2. **Reactive State**: Uses `ref()` and `computed()` for reactive data
3. **Centralized Store**: Single Pinia store manages all session state
4. **Type Safety**: Full TypeScript with strict type checking
5. **Progressive Enhancement**: Skeleton loaders → Error states → Full UI
6. **Persistent Sessions**: LocalStorage integration for session resumption after refresh

---

## 3. Frontend Component Library

**Location**: `web_dashboard/frontend_poc/src/components/`
**Total Components**: 12 Vue single-file components (SFC)

### 3.1 Component Inventory

#### Core Components
1. **AgentFlow.vue** - Phase 4: Real-time agent pipeline visualization
2. **AgentCard.vue** (108 lines) - Individual agent status card with click-to-expand
3. **ProgressTracker.vue** - Overall research progress display
4. **LogViewer.vue** - Real-time log streaming display
5. **FileExplorer.vue** - Generated files browser with download links

#### UI/UX Components
6. **ErrorMessage.vue** - Error state display with retry capability
7. **HelloWorld.vue** - Welcome component (legacy)

#### Skeleton Loaders (Phase 3)
8. **AppSkeletonLoader.vue** - Application-wide loading state
9. **ProgressTrackerSkeleton.vue** - Progress tracker loading placeholder
10. **FileExplorerSkeleton.vue** - File explorer loading placeholder
11. **LogViewerSkeleton.vue** - Log viewer loading placeholder
12. **AgentFlowSkeleton.vue** - Agent flow loading placeholder

---

### 3.2 AgentCard Component Deep Dive

**Purpose**: Visual representation of a single agent in the pipeline
**File**: `AgentCard.vue` (108 lines)

**Features**:
- **Color-coded status indicators**:
  - Pending: Gray (`bg-gray-50 border-gray-300`)
  - Running: Yellow with glow effect (`bg-yellow-50 border-yellow-500`)
  - Completed: Green (`bg-green-50 border-green-500`)
  - Error: Red (`bg-red-50 border-red-500`)
- **Click-to-expand** for detailed agent messages
- **Human-friendly workflow step names**:
  ```typescript
  const WORKFLOW_STEP_NAMES: Record<string, string> = {
    'Browser': 'Initial Research',
    'Editor': 'Planning',
    'Researcher': 'Parallel Research',
    'Writer': 'Writing',
    'Translator': 'Translation',
    'Publisher': 'Publishing',
    'Orchestrator': 'Orchestrator'
  }
  ```
- **Status icons**: ⏳ (pending), 🔄 (running), ✅ (completed), ❌ (error)
- **Smooth transitions** and hover effects

**Component Structure**:
```vue
<template>
  <div
    class="p-3 rounded-lg border-2 w-40 text-center cursor-pointer"
    :class="statusStyles.bgColor"
    @click="toggleDetails"
  >
    <h3>{{ displayName }}</h3>
    <div>{{ statusStyles.icon }} {{ agent.status }}</div>

    <!-- Expandable details -->
    <div v-if="isExpanded">
      <p>{{ agent.message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  agent: AgentUpdatePayload
}>()

const isExpanded = ref(false)
const statusStyles = computed(() => { /* ... */ })
</script>
```

---

### 3.3 Component Communication Patterns

1. **Props Down**: Parent components pass data via props
2. **Events Up**: Child components emit events to parents
3. **Store Access**: Components directly access Pinia store for global state
4. **Computed Properties**: Reactive derived state based on store data

**Example - AgentFlow using store**:
```typescript
import { useSessionStore } from '@/stores/sessionStore'

const store = useSessionStore()

// Reactive agent list from store
const agents = computed(() => store.orderedAgents)
```

---

## 4. Frontend State Management (Pinia)

**Location**: `web_dashboard/frontend_poc/src/stores/sessionStore.ts`
**Lines of Code**: 468 lines
**Purpose**: Centralized state management for research session

### 4.1 Store Architecture

**State Structure**:
```typescript
export const useSessionStore = defineStore('session', () => {
  // Session identity
  const sessionId = ref<string | null>(null)

  // WebSocket connection
  const wsStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')

  // Agent states (Map for O(1) lookups)
  const agents = ref<Map<string, AgentUpdatePayload>>(new Map())

  // Event log (circular buffer, max 1000 events)
  const events = ref<WebSocketEvent[]>([])

  // Files generated during research
  const files = ref<FileGeneratedPayload[]>([])

  // Overall research progress
  const overallProgress = ref(0)
  const overallStatus = ref<ResearchStatus>('initializing')
  const currentStage = ref<string>('Idle')
  const agentsCompleted = ref(0)
  const agentsTotal = ref(7)  // 7 active agents

  // Error state
  const lastError = ref<ErrorPayload | null>(null)

  // UI state (Phase 3)
  const isLoading = ref(true)
  const isSubmitting = ref(false)
  const appError = ref<string | null>(null)

  // WebSocket instance
  let ws: WebSocket | null = null
})
```

---

### 4.2 Agent Pipeline Order

**Critical Configuration** (Phase 4):
```typescript
const AGENT_PIPELINE_ORDER = [
  'Browser',      // Initial research
  'Editor',       // Planning
  'Researcher',   // Parallel research
  'Writer',       // Writing
  'Publisher',    // Publishing
  'Translator',   // Translation
  'Orchestrator'  // Master coordinator
]
```

**Note**: Reviewer and Reviser are **DISABLED** in backend workflow for performance optimization.

---

### 4.3 Computed Properties

**Ordered Agents** (Phase 4 Fix):
```typescript
const orderedAgents = computed(() => {
  return AGENT_PIPELINE_ORDER.map(agentName => {
    // KEY FIX: Direct O(1) lookup using agent_name as key
    const agentData = agents.value.get(agentName)

    // Return actual data or default pending state
    return agentData || {
      agent_id: agentName.toLowerCase(),
      agent_name: agentName,
      status: 'pending' as const,
      progress: null,
      message: 'Waiting to start...'
    }
  })
})
```

**Summary Statistics**:
```typescript
const activeAgent = computed(() =>
  orderedAgents.value.find(a => a.status === 'running')
)

const completedAgents = computed(() =>
  orderedAgents.value.filter(a => a.status === 'completed')
)

const pendingAgents = computed(() =>
  orderedAgents.value.filter(a => a.status === 'pending')
)

const failedAgents = computed(() =>
  orderedAgents.value.filter(a => a.status === 'error')
)
```

---

### 4.4 WebSocket Management

**Connection Lifecycle**:
```typescript
function connect(sessionIdParam: string) {
  sessionId.value = sessionIdParam
  wsStatus.value = 'connecting'

  // Construct WebSocket URL
  const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL ||
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
    window.location.host

  ws = new WebSocket(`${wsBaseUrl}/ws/${sessionIdParam}`)

  ws.onopen = () => {
    wsStatus.value = 'connected'
    console.log('✅ WebSocket connected')
  }

  ws.onmessage = (event) => {
    const data: WebSocketEvent = JSON.parse(event.data)
    handleEvent(data)
  }

  ws.onerror = (error) => {
    wsStatus.value = 'error'
    console.error('❌ WebSocket error:', error)
  }

  ws.onclose = (event) => {
    wsStatus.value = 'disconnected'
    // Auto-reconnect if not clean closure
    if (!event.wasClean && sessionId.value) {
      setTimeout(() => connect(sessionId.value!), 3000)
    }
  }
}
```

---

### 4.5 Event Handling

**Event Router**:
```typescript
function handleEvent(event: WebSocketEvent) {
  // Add to circular buffer
  events.value.push(event)
  if (events.value.length > maxEvents) {
    events.value = events.value.slice(-maxEvents)
  }

  // Type-safe event handling (TypeScript discriminated unions)
  switch (event.event_type) {
    case 'agent_update':
      handleAgentUpdate(event.payload)  // payload is AgentUpdatePayload
      break
    case 'file_generated':
      handleFileGenerated(event.payload)  // payload is FileGeneratedPayload
      break
    case 'research_status':
      handleResearchStatus(event.payload)  // payload is ResearchStatusPayload
      break
    case 'error':
      handleError(event.payload)  // payload is ErrorPayload
      break
    case 'log':
      handleLog(event.payload)  // payload is LogPayload
      break
  }
}
```

**Agent Update Handler** (Phase 4 Fix):
```typescript
function handleAgentUpdate(payload: AgentUpdatePayload) {
  // KEY FIX: Use agent_name as key (not agent_id)
  // This aligns with orderedAgents computed property lookups
  agents.value.set(payload.agent_name, payload)

  // Update overall progress (average of agents with explicit progress)
  const allAgents = Array.from(agents.value.values())
  const agentsWithProgress = allAgents.filter(a => a.progress !== null)

  if (agentsWithProgress.length > 0) {
    const avgProgress = agentsWithProgress.reduce((sum, a) =>
      sum + (a.progress || 0), 0) / agentsWithProgress.length
    overallProgress.value = Math.round(avgProgress)
  }
}
```

---

### 4.6 Session Lifecycle Actions

**Start New Session**:
```typescript
async function startNewSession(subject: string, language: string) {
  isSubmitting.value = true
  appError.value = null

  try {
    reset()  // Clear previous session

    const { api } = await import('@/services/api')
    const response = await api.submitResearch(subject, language)

    // Save session ID to localStorage
    localStorage.setItem('tk9_session_id', response.session_id)
    sessionId.value = response.session_id

    // Connect WebSocket
    connect(response.session_id)

    toast.success('Research started successfully!')
  } catch (error) {
    appError.value = 'Failed to start research. Please try again.'
    toast.error(appError.value)
  } finally {
    isSubmitting.value = false
  }
}
```

**Rehydrate Session** (Phase 3):
```typescript
async function rehydrate(sessionIdParam: string) {
  isLoading.value = true
  appError.value = null

  try {
    // Fetch current session state from server
    const { api } = await import('@/services/api')
    const state = await api.getSessionState(sessionIdParam)

    sessionId.value = sessionIdParam

    // Re-populate files
    if (state.files && state.files.length > 0) {
      files.value = state.files.map((f: any) => ({
        file_id: f.file_id || f.filename,
        filename: f.filename,
        file_type: f.file_type,
        language: f.language,
        size_bytes: f.size_bytes,
        path: f.download_url
      }))
    }

    // Set overall status
    if (state.status === 'completed') {
      overallStatus.value = 'completed'
      overallProgress.value = 100
      currentStage.value = 'Research completed'
    }

    // Connect WebSocket for real-time updates
    connect(sessionIdParam)
  } catch (error) {
    appError.value = 'Failed to restore session. Please start new research.'
    toast.error(appError.value)
    localStorage.removeItem('tk9_session_id')
  } finally {
    isLoading.value = false
  }
}
```

---

## 5. Complete Multi-Agent System

**Location**: `multi_agents/`
**Technology Stack**: Python 3.12, LangGraph, gpt-researcher, Google Gemini, BRAVE Search
**Files**: 60+ Python files

### 5.1 Agent Architecture

**ChiefEditorAgent** (Orchestrator):
- **File**: `multi_agents/agents/orchestrator.py`
- **Role**: Master coordinator managing the entire research workflow
- **Responsibilities**:
  - Initialize and configure all specialized agents
  - Build LangGraph state machine
  - Coordinate agent execution order
  - Manage research state and memory
  - Handle output directory creation and file management

**Constructor** (Phase 5 Fix):
```python
def __init__(
    self,
    task: Dict[str, Any],
    websocket=None,
    stream_output=None,
    tone=None,
    headers=None,
    write_to_files: bool = False,
    task_id=None,  # NEW: Accept task_id from web dashboard
):
    self.task = task
    self.websocket = websocket
    self.stream_output = stream_output
    self.headers = headers or {}
    self.tone = tone

    # Use provided task_id (UUID from web dashboard) or generate timestamp-based ID
    self.task_id = task_id if task_id is not None else self._generate_task_id()
    self.output_dir = self._create_output_directory() if write_to_files else None
```

**Critical Fix** (Phase 5):
The orchestrator now accepts `task_id` parameter to ensure output directories use UUID format for proper file detection:
```python
is_uuid = isinstance(self.task_id, str) and "-" in str(self.task_id)

if is_uuid:
    # Use UUID directly for web dashboard sessions
    directory_name = f"{self.task_id}"
else:
    # Traditional timestamp-based for CLI
    directory_name = f"run_{self.task_id}_{sanitized_query}"
```

---

### 5.2 Specialized Agents

#### 1. Browser Agent (ResearchAgent.run_initial_research)
**File**: `multi_agents/agents/researcher.py`
**Purpose**: Conduct initial web research using GPT Researcher
**Output**: Initial research findings and context

```python
async def run_initial_research(self, research_state: dict):
    task = research_state.get("task")
    query = task.get("query")

    # Phase 2: Use structured JSON output
    print_structured_output(
        message=f"Running initial research on: {query}",
        agent="BROWSER",
        status="running",
    )

    # Conduct research
    research_summary = await self.research(
        query=query,
        research_report="research_report",
        verbose=True,
    )

    return {"research_data": [research_summary]}
```

#### 2. Editor Agent
**File**: `multi_agents/agents/editor.py`
**Purpose**: Plan research outline and structure
**Output**: Detailed outline with sections and subsections

#### 3. Researcher Agent
**File**: `multi_agents/agents/researcher.py`
**Purpose**: Parallel deep research on subtopics
**Output**: Comprehensive research on each subtopic

#### 4. Writer Agent
**File**: `multi_agents/agents/writer.py`
**Purpose**: Write complete research report
**Output**: Full report in markdown format

#### 5. Publisher Agent
**File**: `multi_agents/agents/publisher.py`
**Purpose**: Publish final report to PDF/DOCX
**Output**: Generated PDF and DOCX files

#### 6. Translator Agent
**File**: `multi_agents/agents/translator.py`
**Purpose**: Translate report to target language
**Output**: Translated PDF/DOCX files

#### 7. Orchestrator Agent
**Role**: Master coordinator (ChiefEditorAgent itself)

**Disabled Agents** (Performance Optimization):
- **Reviewer Agent**: Quality review (disabled)
- **Reviser Agent**: Content revision (disabled)

---

### 5.3 LangGraph Workflow

**State Machine**:
```
START → browser (initial research)
      ↓
      editor (planning)
      ↓
      researcher (deep research)
      ↓
      writer (report writing)
      ↓
      publisher (file generation)
      ↓
      translator (translation)
      ↓
      END
```

**Conditional Routing**:
```python
graph = StateGraph(ResearchState)

# Add nodes
graph.add_node("browser", run_initial_research)
graph.add_node("editor", run_editor_review)
graph.add_node("researcher", run_parallel_research)
graph.add_node("writer", run_writer)
graph.add_node("publisher", run_publisher)
graph.add_node("translator", run_translator)

# Add edges
graph.set_entry_point("browser")
graph.add_edge("browser", "editor")
graph.add_edge("editor", "researcher")
graph.add_edge("researcher", "writer")
graph.add_edge("writer", "publisher")
graph.add_conditional_edges(
    "publisher",
    should_translate,
    {True: "translator", False: END}
)
graph.add_edge("translator", END)
```

---

### 5.4 Multi-Provider System

**Provider Strategy**:
```python
# Primary providers
PRIMARY_LLM_PROVIDER = "google_gemini"
PRIMARY_LLM_MODEL = "gemini-2.5-flash-preview-04-17-thinking"
PRIMARY_SEARCH_PROVIDER = "brave"

# Failover strategy
LLM_STRATEGY = "primary_only"  # or "failover", "round_robin"
SEARCH_STRATEGY = "primary_only"
```

**Provider Factory**:
```python
from multi_agents.providers.factory import enhanced_config

# LLM provider
llm = enhanced_config.get_llm_provider()

# Search provider
search = enhanced_config.get_search_provider()
```

**BRAVE Search Integration**:
```python
RETRIEVER = "custom"
RETRIEVER_ENDPOINT = "https://brave-local-provider.local"
BRAVE_API_KEY = "your_brave_api_key"
```

---

### 5.5 Memory System

**Research State**:
```python
class ResearchState(TypedDict):
    task: Dict[str, Any]
    initial_research: str
    research_data: List[str]
    sections: List[str]
    research_summary: str
    draft: Dict[str, Any]
    translated_draft: Dict[str, Any]
```

**Draft Manager**:
```python
class DraftManager:
    def __init__(self, output_dir, task_id):
        self.output_dir = output_dir
        self.task_id = task_id

    def write_draft(self, content: str, language: str = "en"):
        """Write draft content to file"""

    def read_draft(self) -> Optional[str]:
        """Read existing draft"""

    def get_draft_path(self, language: str = "en") -> Path:
        """Get path to draft file"""
```

---

## 6. System Integration

### 6.1 Web Dashboard ↔ Multi-Agent System

**Integration Flow**:
```
1. User submits research via Web Dashboard Frontend
   ↓
2. Frontend calls POST /api/research
   ↓
3. Backend (FastAPI) generates UUID session_id
   ↓
4. Backend starts CLI executor as background task
   ↓
5. CLI executor runs: uv run python -m multi_agents.main --session-id {uuid}
   ↓
6. Multi-agent system creates output directory: ./outputs/{uuid}/
   ↓
7. CLI stdout streams to WebSocket via websocket_handler
   ↓
8. Frontend receives WebSocket events and updates UI
   ↓
9. Research completes, files generated in ./outputs/{uuid}/
   ↓
10. file_manager discovers files and makes them available for download
```

---

### 6.2 Key Integration Points

**Session ID Propagation**:
```
Web Dashboard → FastAPI → CLI Executor → multi_agents.main → ChiefEditorAgent
(UUID)           (UUID)    (--session-id)   (task_id param)   (self.task_id)
```

**Output Directory Naming** (Phase 5 Fix):
```python
# Before fix: Always used timestamp
directory_name = f"run_{int(time.time())}_{sanitized_query}"
# Result: ./outputs/run_1761898976_Subject_Name/

# After fix: Uses UUID from web dashboard
directory_name = f"{self.task_id}"  # task_id = "f84a84cb-dc65-4321-abe1-169c502ad2fe"
# Result: ./outputs/f84a84cb-dc65-4321-abe1-169c502ad2fe/
```

**WebSocket Event Flow**:
```
CLI stdout → websocket_handler.parse_agent_from_output()
          → websocket_handler.broadcast_agent_update()
          → WebSocket.send(JSON event)
          → Frontend receives event
          → sessionStore.handleAgentUpdate()
          → agents.value.set(agent_name, payload)
          → orderedAgents computed property updates
          → AgentCard components re-render
```

---

### 6.3 File Detection Flow (Phase 5 Fix)

**Before Fix**:
```
Multi-agent creates: ./outputs/run_1761898976_Subject_Name/report.pdf
Web dashboard looks in: ./outputs/f84a84cb-dc65-4321-abe1-169c502ad2fe/
Result: ❌ "No files generated yet (0)"
```

**After Fix**:
```
Multi-agent creates: ./outputs/f84a84cb-dc65-4321-abe1-169c502ad2fe/report.pdf
Web dashboard looks in: ./outputs/f84a84cb-dc65-4321-abe1-169c502ad2fe/
Result: ✅ Files detected and downloadable
```

---

## 7. Key Technical Decisions

### 7.1 Phase 1: Core Fixes

**Problem**: CLI output with extremely long lines caused `LimitOverrunError`
**Solution**: Chunk-based reading (4096 bytes) instead of `readline()`
**Impact**: Stable log streaming regardless of line length

---

### 7.2 Phase 2: Structured Output Migration

**Problem**: Legacy text parsing fragile and hard to extend
**Solution**: Dual-mode parser supporting both JSON and text formats
**Impact**: Backward compatibility while migrating to structured events

---

### 7.3 Phase 3: UI State Management

**Problem**: No loading states, errors not handled gracefully
**Solution**: Added `isLoading`, `isSubmitting`, `appError` state + skeleton loaders
**Impact**: Professional UX with proper loading/error feedback

---

### 7.4 Phase 4: Real-Time Agent Visualization

**Problem**: Users couldn't see which agents were running
**Solution**: Agent flow cards with real-time WebSocket updates
**Impact**: Full visibility into research progress

---

### 7.5 Phase 5: File Detection Fix (CRITICAL)

**Problem**: Files always created but never detected by web dashboard
**Root Cause**: Directory mismatch (timestamp vs UUID)
**Solution**: Pass `task_id` parameter to ChiefEditorAgent constructor
**Impact**: Files now properly detected and downloadable

---

## 8. Development Guidelines

### 8.1 Adding New Agent to Pipeline

**Backend Changes**:
```python
# 1. websocket_handler.py - Add to pipeline
AGENT_PIPELINE = [
    "Browser", "Editor", "Researcher", "Writer",
    "Publisher", "Translator", "Orchestrator",
    "YourNewAgent"  # Add here
]

# 2. websocket_handler.py - Add name mapping
AGENT_NAME_MAP = {
    "YOUR_NEW_AGENT": "YourNewAgent",
}

# 3. schemas.py - Update default total
agentsTotal.value = ref(8)  # Increment
```

**Frontend Changes**:
```typescript
// 1. sessionStore.ts - Add to pipeline order
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator', 'Orchestrator',
  'YourNewAgent'  // Add here
]

// 2. sessionStore.ts - Update total
const agentsTotal = ref(8)  // Increment

// 3. AgentCard.vue - Add human-friendly name
const WORKFLOW_STEP_NAMES: Record<string, string> = {
  // ...existing mappings...
  'YourNewAgent': 'Your Feature Name'
}
```

---

### 8.2 Code Style

**Backend (Python)**:
- Use type hints for all function parameters and return values
- Async/await for all I/O operations
- Structured logging with print_structured_output()
- Error handling with try/except and structured error events

**Frontend (TypeScript/Vue)**:
- `<script setup lang="ts">` for all components
- Type all props, emits, and reactive state
- Use computed properties for derived state
- Access store via `useSessionStore()` hook

---

### 8.3 Testing Checklist

**Backend**:
- [ ] API endpoints respond correctly
- [ ] WebSocket connections established
- [ ] CLI executor handles long output lines
- [ ] File detection works with UUID directories
- [ ] Cleanup task removes old files

**Frontend**:
- [ ] Research form validation works
- [ ] WebSocket receives and processes events
- [ ] Agent cards update in real-time
- [ ] Files appear after generation
- [ ] Session rehydration works after refresh
- [ ] Toast notifications appear for status changes

---

## Summary Statistics

**Total Files Analyzed**: 500+ files
**Backend Files**: 8 core + utilities
**Frontend Components**: 12 Vue SFCs
**Multi-Agent Files**: 60+ Python files
**State Management**: 1 Pinia store (468 lines)
**Agent Pipeline**: 7 active agents
**WebSocket Events**: 7 event types

**Key Achievements**:
- ✅ Stable WebSocket communication
- ✅ Real-time agent visualization
- ✅ File detection working correctly
- ✅ Session persistence across refreshes
- ✅ Professional error handling and loading states
- ✅ Multi-provider LLM/search support
- ✅ 50+ language translation support

---

**Last Updated**: 2025-10-31
**Status**: Production Ready
**Next Steps**: Consider sequential deep-dives for detailed area documentation
