# Web Dashboard Best Practices

**Project**: TK9 Deep Research MCP - Web Dashboard
**Last Updated**: 2025-10-31
**Purpose**: Capture lessons learned and best practices from Phase 4 implementation

## Critical Patterns

### 1. Session ID as Single Source of Truth

**Problem Solved**: File detection failure due to mismatched directory naming

**Pattern**:
```python
# ❌ WRONG: Multiple identifiers
web_session_id = str(uuid.uuid4())  # UUID in web dashboard
cli_directory = f"run_{timestamp}_{query}"  # Different in CLI

# ✅ RIGHT: Single identifier throughout
session_id = str(uuid.uuid4())  # Generate once in web dashboard
# Pass to CLI: --session-id {session_id}
# Use in orchestrator: output_dir = f"./outputs/{session_id}"
```

**Implementation**:
1. Web dashboard generates UUID
2. Passes as `--session-id` argument to CLI
3. CLI accepts and forwards to orchestrator
4. Orchestrator detects UUID format and uses directly

**Benefits**:
- No directory name translation needed
- Files appear in expected location
- Clear ownership of session

---

### 2. Dual Message Format Parser

**Problem Solved**: Agent cards not updating due to format mismatch

**Pattern**:
```python
def parse_agent_from_output(self, line: str) -> tuple[str, str] | None:
    """Parse agent messages supporting multiple formats for backward compatibility"""

    # Pattern 1: "AGENT_NAME: message" (uppercase, colon)
    match = re.search(r'([A-Z_]+):\s*(.+)', clean_line)
    if match:
        agent_name = match.group(1)
        message = match.group(2)
        # Map to frontend name
        return (AGENT_NAME_MAP.get(agent_name), message)

    # Pattern 2: "Agent Name - message" (mixed case, hyphen)
    match = re.search(r'(Browser|Editor|Researcher|Writer|...)\s*-\s*(.+)', clean_line)
    if match:
        agent_name = match.group(1)
        message = match.group(2)
        return (agent_name, message)

    return None  # No match found
```

**Benefits**:
- Backward compatibility with existing output
- Graceful handling of multiple formats
- Clear fallback logic

**When to Use**:
- Integrating with existing systems
- Transitioning between formats
- Supporting multiple output sources

---

### 3. Explicit Module Paths

**Problem Solved**: Python loading wrong module due to naming conflict

**Pattern**:
```python
# ❌ WRONG: Ambiguous module path
cmd = ["python", "-m", "main"]  # Which main.py?

# ✅ RIGHT: Explicit module path
cmd = ["python", "-m", "multi_agents.main"]  # Clear and unambiguous
```

**Additional Safety**:
```python
# Archive conflicting files
ARCHIVE/cli-deprecated-20251031/
  ├── main.py (old conflicting file)
  └── README.md (documentation of why archived)
```

**Benefits**:
- No module resolution conflicts
- Clear intent in code
- Prevents future issues

**When to Use**:
- Always in production code
- When using subprocess to run Python
- In projects with multiple entry points

---

### 4. WebSocket Event-Driven Architecture

**Pattern**:
```typescript
// Centralized state management (Pinia store)
export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    sessionId: null,
    status: 'idle',
    agents: {},
    logs: [],
    files: [],
    websocket: null
  }),

  actions: {
    connectWebSocket(sessionId: string) {
      this.websocket = new WebSocket(`ws://localhost:12656/ws/${sessionId}`)

      this.websocket.onmessage = (event) => {
        const message = JSON.parse(event.data)

        switch (message.type) {
          case 'agent_status':
            this.updateAgentStatus(message.data)
            break
          case 'log':
            this.logs.push(message.data)
            break
          case 'files_ready':
            this.files = message.data.files
            break
        }
      }

      this.websocket.onerror = () => {
        this.reconnect()  // Auto-reconnect on error
      }
    },

    updateAgentStatus(data: AgentStatusUpdate) {
      this.agents[data.agent] = {
        status: data.status,
        message: data.message
      }
    }
  }
})
```

**Benefits**:
- Reactive state updates
- Clear event handling
- Automatic UI updates
- Centralized logic

---

### 5. Graceful Error Handling

**Pattern**:
```python
# Backend: Comprehensive error handling
async def execute_research(...):
    try:
        # Start process
        process = await asyncio.create_subprocess_exec(...)

        # Stream output
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            try:
                yield line.decode('utf-8')
            except UnicodeDecodeError:
                yield line.decode('utf-8', errors='replace')  # Graceful degradation

    except Exception as e:
        logger.error(f"Session {session_id} error: {e}")
        yield f"\n[SYSTEM ERROR] {str(e)}\n"  # User-friendly message
```

```typescript
// Frontend: Error boundaries
const startResearch = async (query: string) => {
  try {
    sessionStore.status = 'running'
    const response = await api.post('/research/start', { query })
    sessionStore.sessionId = response.data.session_id
    sessionStore.connectWebSocket(response.data.session_id)
  } catch (error) {
    sessionStore.status = 'failed'
    sessionStore.error = error.message
    // Show user-friendly error message
  }
}
```

**Benefits**:
- User sees helpful error messages
- System doesn't crash on errors
- Logs capture full context
- Graceful degradation

---

## Component Design Patterns

### 1. Skeleton Loaders

**Purpose**: Improve perceived performance during loading

**Pattern**:
```vue
<template>
  <div v-if="loading">
    <SkeletonLoader />
  </div>
  <div v-else>
    <ActualContent />
  </div>
</template>
```

**Components Created**:
- `AppSkeletonLoader.vue` - Full app loading
- `FileExplorerSkeleton.vue` - File list loading
- `LogViewerSkeleton.vue` - Log area loading
- `ProgressTrackerSkeleton.vue` - Progress indicators

**Benefits**:
- Better user experience
- Reduces perceived wait time
- Professional appearance

---

### 2. Agent Status Cards

**Pattern**: Color-coded status with real-time updates

```vue
<script setup lang="ts">
interface Props {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  message?: string
}

const statusColors = {
  pending: 'bg-gray-300',
  running: 'bg-blue-500 animate-pulse',
  completed: 'bg-green-500',
  failed: 'bg-red-500'
}
</script>

<template>
  <div class="agent-card" :class="statusColors[status]">
    <h3>{{ name }}</h3>
    <p>{{ message }}</p>
  </div>
</template>
```

**Benefits**:
- Visual feedback
- Clear agent state
- Professional UI

---

## State Management Patterns

### 1. Centralized Store (Pinia)

**Structure**:
```typescript
// stores/sessionStore.ts
export const useSessionStore = defineStore('session', {
  state: () => ({
    // Session data
    sessionId: null,
    status: 'idle',

    // Agent states
    agents: {},

    // Research output
    logs: [],
    files: [],

    // WebSocket connection
    websocket: null
  }),

  actions: {
    // WebSocket management
    connectWebSocket() { },
    disconnectWebSocket() { },

    // State updates
    updateAgentStatus() { },
    addLog() { },
    setFiles() { }
  },

  getters: {
    // Computed properties
    isRunning: (state) => state.status === 'running',
    hasFiles: (state) => state.files.length > 0
  }
})
```

**Benefits**:
- Single source of truth
- Reactive updates
- TypeScript support
- Clear API

---

### 2. WebSocket Lifecycle Management

**Pattern**:
```typescript
export const useSessionStore = defineStore('session', {
  actions: {
    connectWebSocket(sessionId: string) {
      // Close existing connection
      if (this.websocket) {
        this.websocket.close()
      }

      // Create new connection
      this.websocket = new WebSocket(`ws://.../${sessionId}`)

      // Setup event handlers
      this.websocket.onopen = () => console.log('Connected')
      this.websocket.onmessage = (event) => this.handleMessage(event)
      this.websocket.onerror = () => this.reconnect()
      this.websocket.onclose = () => console.log('Disconnected')
    },

    reconnect() {
      if (this.sessionId) {
        setTimeout(() => {
          this.connectWebSocket(this.sessionId)
        }, 3000)  // Exponential backoff
      }
    },

    disconnectWebSocket() {
      if (this.websocket) {
        this.websocket.close()
        this.websocket = null
      }
    }
  }
})
```

**Benefits**:
- Automatic reconnection
- Clean connection handling
- Prevents memory leaks

---

## Testing Patterns

### 1. Manual Testing Checklist

**Before Each Release**:
- [ ] Agent cards update in real-time
- [ ] Logs stream correctly
- [ ] Files appear within 5 seconds
- [ ] Error messages display properly
- [ ] WebSocket reconnects on disconnect
- [ ] Multiple browsers tested
- [ ] Network interruption handled

### 2. Integration Point Verification

**Test Each Integration**:
```bash
# 1. Web Dashboard → CLI Executor
curl -X POST http://localhost:12656/api/research/start \
  -H "Content-Type: application/json" \
  -d '{"query":"test", "language":"en"}'

# 2. CLI Executor → Multi-Agent System
uv run python -m multi_agents.main \
  --research "test" \
  --session-id "test-uuid" \
  --verbose

# 3. File Detection
ls -la ./outputs/test-uuid/

# 4. WebSocket Events
# Open browser DevTools → Network → WS → Watch messages
```

---

## Performance Optimization

### 1. Backend Optimization

**Patterns**:
```python
# Async subprocess for non-blocking execution
process = await asyncio.create_subprocess_exec(...)

# Stream output instead of buffering
async for line in stream_output():
    yield line

# Timeout on file detection
await asyncio.wait_for(wait_for_files(), timeout=30)
```

### 2. Frontend Optimization

**Patterns**:
```typescript
// Debounce log updates
const addLog = debounce((log: LogEntry) => {
  state.logs.push(log)
}, 100)

// Virtual scrolling for large log lists
// (Future enhancement)

// Lazy load components
const FileExplorer = defineAsyncComponent(() =>
  import('./components/FileExplorer.vue')
)
```

---

## Security Best Practices

### 1. Input Sanitization

**Pattern**:
```python
def _sanitize_input(self, subject: str) -> str:
    """Sanitize user input to prevent command injection"""
    dangerous_chars = ['`', '$', '&', '|', ';', '>', '<', '(', ')', '{', '}']
    sanitized = subject

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # Limit length
    sanitized = sanitized[:500]

    # Ensure not empty
    if not sanitized.strip():
        sanitized = "general research topic"

    return sanitized.strip()
```

### 2. CORS Configuration

**Pattern**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Documentation Standards

### 1. Code Documentation

**Pattern**:
```python
def execute_research(self, subject: str, language: str, session_id: str):
    """
    Execute the CLI research command and stream logs.

    Args:
        subject: The research query to investigate
        language: Target language code (e.g., 'en', 'vi')
        session_id: UUID for session tracking across systems

    Yields:
        str: Log lines from the research process

    Raises:
        Exception: If subprocess fails or times out

    Example:
        async for log_line in executor.execute_research("AI ethics", "en", "uuid"):
            print(log_line)
    """
```

### 2. README Standards

**Include**:
- Quick start guide
- Architecture overview
- API documentation
- Configuration options
- Troubleshooting section
- Deployment instructions

---

## Common Pitfalls to Avoid

### 1. ❌ Don't: Assume User Actions
```python
# Assuming user restarted server
# Better: Provide clear error messages and instructions
```

### 2. ❌ Don't: Use Ambiguous Paths
```python
# Bad
cmd = ["python", "-m", "main"]

# Good
cmd = ["python", "-m", "multi_agents.main"]
```

### 3. ❌ Don't: Ignore Error Cases
```python
# Bad
agent_status = parse_agent_output(line)

# Good
agent_status = parse_agent_output(line)
if agent_status is None:
    logger.warning(f"Could not parse agent status from: {line}")
    continue
```

### 4. ❌ Don't: Hard-code Configuration
```python
# Bad
DASHBOARD_PORT = 12656

# Good
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 12656))
```

### 5. ❌ Don't: Mix Concerns
```python
# Bad: CLI executor doing WebSocket handling
class CLIExecutor:
    def execute(self):
        # ... execute CLI
        # ... also handle WebSocket

# Good: Separate responsibilities
class CLIExecutor:
    def execute(self): pass

class WebSocketHandler:
    def handle_messages(self): pass
```

---

## Development Workflow

### 1. Feature Development

**Process**:
1. Update documentation first (specs, requirements)
2. Implement backend changes
3. Add frontend components
4. Test integration points
5. Update README and CLAUDE.md
6. Git commit with clear message

### 2. Bug Fixing

**Process**:
1. Reproduce the bug
2. Identify root cause (don't assume)
3. Implement fix
4. Test fix thoroughly
5. Document in handoff.md
6. Update best practices if needed

### 3. Code Review

**Checklist**:
- [ ] Type safety (TypeScript/Python types)
- [ ] Error handling present
- [ ] Logging adequate
- [ ] No hardcoded values
- [ ] Clear variable names
- [ ] Comments for complex logic
- [ ] No security vulnerabilities

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Build successful
- [ ] CORS configured correctly

### Deployment

- [ ] Backend running on correct port
- [ ] Frontend built and served
- [ ] WebSocket connections working
- [ ] File system permissions correct
- [ ] Reverse proxy configured (if needed)

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Verify agent updates working
- [ ] Check file detection
- [ ] Test error handling
- [ ] Verify WebSocket reconnection

---

## Maintenance Guidelines

### Regular Updates

**Weekly**:
- Review logs for errors
- Check disk usage (outputs directory)
- Monitor WebSocket connections
- Update dependencies (security patches)

**Monthly**:
- Review documentation accuracy
- Update best practices
- Archive old sessions
- Performance profiling

**Quarterly**:
- Major dependency updates
- Architecture review
- Security audit
- User feedback review

---

## Conclusion

These best practices emerged from real-world implementation challenges in Phase 4. Following them will help avoid common pitfalls and maintain a high-quality, production-ready system.

**Key Takeaways**:
1. Use single source of truth for identifiers
2. Support multiple formats for backward compatibility
3. Always use explicit module paths
4. Implement proper error handling everywhere
5. Document lessons learned immediately
6. Test integration points thoroughly
7. Never assume user actions

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
**Next Review**: After Phase 5 or major changes
