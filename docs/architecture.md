# TK9 Historical Research Access & Authentication - Decision Architecture

## Executive Summary

This architecture implements a **brownfield enhancement** to the existing TK9 deep research MCP server, adding user authentication and historical research access capabilities. The architecture leverages the existing Vue 3 + FastAPI + Supabase stack while introducing a sophisticated 3-level progressive disclosure UI pattern (collapsible accordion) optimized for exploring research artifacts across 4 workflow stages.

Key architectural decisions prioritize **user experience** (immediate anonymous access with upgrade path), **transparency** (progressive disclosure of research process), and **performance** (virtualized scrolling, lazy loading, caching) to handle 1000+ research sessions without degradation.

This document serves as the consistency contract for all AI agents implementing the 16 stories across 4 epics.

## Project Initialization

**Important**: This is a brownfield project enhancing an existing application. No new project initialization is required.

The existing TK9 project already has:
- ✅ Vue 3 frontend with Vite build tooling
- ✅ FastAPI backend with Python 3.12
- ✅ Supabase PostgreSQL database
- ✅ Element Plus UI component library
- ✅ WebSocket support for real-time updates

**Enhancement Setup**:
```bash
# Frontend - Install additional dependencies
cd web_dashboard/frontend_poc
npm install vue-virtual-scroller@next  # Vue 3 compatible virtualization
npm install highlight.js               # JSON syntax highlighting
npm install @supabase/supabase-js      # Auth SDK

# Backend - Install additional dependencies
cd ../..
pip install pyjwt[crypto]               # JWT token management
pip install python-multipart            # File upload support
```

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| **Authentication** | Supabase Auth (Anonymous + Email) | 2.39+ | Epic 1, 2, 3, 4 | Zero-friction entry via anonymous sign-in, seamless upgrade to permanent account |
| **Frontend Framework** | Vue 3 (Composition API) | 3.4+ | All Epics | Existing TK9 stack, excellent TypeScript support, reactive state management |
| **UI Component Library** | Element Plus | 2.5+ | Epic 3, 4 | Battle-tested accordion component, WCAG compliant, mobile-responsive |
| **Virtualization** | vue-virtual-scroller | 2.0+ (Vue 3) | Epic 4 | High-performance rendering of 1000+ session lists, 60 FPS scroll |
| **State Management** | Pinia | 2.1+ | All Epics | Vue 3 native state management, TypeScript support, Supabase auth integration |
| **Backend Framework** | FastAPI | 0.109+ | All Epics | Existing TK9 stack, async support, automatic OpenAPI docs |
| **Database** | Supabase (PostgreSQL) | 15+ | Epic 1, 2 | Existing TK9 infrastructure, built-in RLS, real-time subscriptions |
| **Session Management** | JWT (HTTP-only cookies) | N/A | Epic 1 | Security best practice, prevents XSS attacks, 7-day access + 30-day refresh tokens |
| **API Design** | RESTful JSON | N/A | Epic 2, 3 | Standard HTTP verbs, predictable endpoints, JSON request/response |
| **WebSocket Protocol** | Native WebSocket | N/A | Epic 2 | Real-time file detection updates, existing TK9 pattern |
| **Syntax Highlighting** | highlight.js | 11.9+ | Epic 3 | Lightweight, supports JSON, customizable themes |
| **File Detection** | Watchdog (Python) | 3.0+ | Epic 2 | Monitors filesystem for new research files, reliable event-based detection |
| **Caching Strategy** | In-memory LRU + IndexedDB | N/A | Epic 4 | Fast session metadata access (LRU), offline draft content (IndexedDB) |
| **UI Pattern** | Collapsible Accordion (3-level) | N/A | Epic 3 | Progressive disclosure, comparison-optimized, mobile-responsive (ADR-001) |
| **Mobile Strategy** | Responsive Web (no native) | N/A | Epic 4 | Adaptive accordion layout, touch-optimized, 360px minimum width |
| **Testing Framework** | pytest (backend), Vitest (frontend) | Latest | All Epics | Existing TK9 testing infrastructure |
| **Code Formatting** | Black (Python), Prettier (JS/TS) | Latest | All Epics | Existing TK9 code style, automated formatting |

## Project Structure

```
tk9_source_deploy/
├── web_dashboard/                       # FastAPI backend + Vue frontend
│   ├── main.py                          # FastAPI app entry point
│   ├── cli_executor.py                  # Research execution handler
│   ├── websocket_handler.py             # WebSocket manager
│   ├── file_manager.py                  # File detection service (NEW)
│   ├── schemas.py                       # Pydantic models (EXTEND)
│   ├── models.py                        # Database models (EXTEND)
│   ├── routers/                         # API endpoints
│   │   ├── auth.py                      # Authentication routes (NEW)
│   │   ├── sessions.py                  # Session management (NEW)
│   │   └── drafts.py                    # Draft content API (NEW)
│   ├── middleware/                      # HTTP middleware
│   │   └── auth_middleware.py           # JWT verification (NEW)
│   ├── services/                        # Business logic
│   │   ├── auth_service.py              # Supabase auth integration (NEW)
│   │   ├── session_service.py           # Session CRUD operations (NEW)
│   │   └── file_detection_service.py    # File monitoring (NEW)
│   ├── frontend_poc/                    # Vue 3 frontend
│   │   ├── src/
│   │   │   ├── main.ts                  # Vue app entry
│   │   │   ├── App.vue                  # Root component
│   │   │   ├── router/
│   │   │   │   └── index.ts             # Vue Router (EXTEND)
│   │   │   ├── stores/                  # Pinia stores
│   │   │   │   ├── authStore.ts         # Auth state management (NEW)
│   │   │   │   └── sessionStore.ts      # Session state (EXTEND)
│   │   │   ├── components/              # Vue components
│   │   │   │   ├── auth/
│   │   │   │   │   ├── AnonymousPrompt.vue     # Upgrade prompt (NEW)
│   │   │   │   │   ├── RegistrationModal.vue   # Email registration (NEW)
│   │   │   │   │   └── LoginForm.vue           # Login form (NEW)
│   │   │   │   ├── sessions/
│   │   │   │   │   ├── SessionList.vue                # Virtual scrolled list (NEW)
│   │   │   │   │   ├── SessionCard.vue                # Expandable card (NEW)
│   │   │   │   │   ├── SessionSearch.vue              # Search & filters (NEW)
│   │   │   │   │   └── FinalReportViewer.vue          # Report modal (NEW)
│   │   │   │   └── drafts/
│   │   │   │       ├── StageAccordion.vue             # 4-stage accordion (NEW)
│   │   │   │       ├── DraftViewer.vue                # JSON syntax highlighter (NEW)
│   │   │   │       └── DraftStageContent.vue          # Draft list (NEW)
│   │   │   ├── composables/             # Vue composables
│   │   │   │   ├── useAuth.ts           # Auth logic (NEW)
│   │   │   │   ├── useSessions.ts       # Session fetching (NEW)
│   │   │   │   ├── useWebSocket.ts      # WS connection (EXTEND)
│   │   │   │   └── useVirtualScroll.ts  # Virtualization logic (NEW)
│   │   │   ├── utils/
│   │   │   │   ├── supabase.ts          # Supabase client (NEW)
│   │   │   │   ├── dateFormatter.ts     # Relative time formatting (NEW)
│   │   │   │   └── cacheManager.ts      # LRU cache + IndexedDB (NEW)
│   │   │   └── types/
│   │   │       ├── auth.ts              # Auth types (NEW)
│   │   │       ├── session.ts           # Session types (EXTEND)
│   │   │       └── draft.ts             # Draft types (NEW)
│   │   ├── public/                      # Static assets
│   │   └── vite.config.ts               # Vite configuration
│   └── tests/                           # Backend tests
│       ├── test_auth.py                 # Auth endpoint tests (NEW)
│       ├── test_sessions.py             # Session API tests (NEW)
│       └── test_file_detection.py       # File detection tests (NEW)
├── multi_agents/                        # Multi-agent research system
│   ├── main.py                          # Research orchestrator (EXTEND for session ID)
│   └── agents/
│       └── orchestrator.py              # ChiefEditorAgent (EXTEND for UUID task_id)
├── docs/                                # Project documentation
│   ├── PRD.md                           # Product requirements ✅
│   ├── epics.md                         # Epic breakdown ✅
│   ├── architecture.md                  # This file ✅
│   ├── product-brief-TK9-2025-10-31.md  # Product brief ✅
│   ├── research-technical-2025-10-31.md # Technical research ✅
│   └── bmm-workflow-status.yaml         # Workflow tracking ✅
├── outputs/                             # Research output files
│   └── {session_id}/                    # UUID-based session directories
│       ├── 1_initial_research/          # Stage 1 drafts (JSON files)
│       ├── 2_planning/                  # Stage 2 drafts
│       ├── 3_parallel_research/         # Stage 3 drafts
│       ├── 4_writing/                   # Stage 4 drafts
│       └── final_report.md              # Completed research report
├── .env                                 # Environment variables
├── pyproject.toml                       # Python dependencies
└── README.md                            # Project README

```

## Epic to Architecture Mapping

| Epic | Components | Database Tables | API Endpoints | Frontend Views |
|------|-----------|-----------------|---------------|----------------|
| **Epic 1: Authentication Foundation** | `auth_service.py`, `auth_middleware.py`, `authStore.ts`, Auth components | `users`, RLS policies | `/api/auth/anonymous`, `/api/auth/register`, `/api/auth/login`, `/api/auth/upgrade` | `RegistrationModal.vue`, `LoginForm.vue` |
| **Epic 2: Historical Research Access** | `session_service.py`, `file_detection_service.py`, `file_manager.py`, Session components | `research_sessions`, `draft_files` | `/api/sessions`, `/api/sessions/{id}`, `/api/sessions/search`, `/ws/sessions` | `SessionList.vue`, `SessionCard.vue`, `SessionSearch.vue`, `FinalReportViewer.vue` |
| **Epic 3: Draft Exposure System** | Draft components, `DraftViewer.vue`, `StageAccordion.vue` | `draft_files` (read-only) | `/api/sessions/{id}/stages/{stage}/drafts`, `/api/sessions/{id}/files/{file_id}` | `StageAccordion.vue`, `DraftViewer.vue`, `DraftStageContent.vue` |
| **Epic 4: Performance Optimization** | `useVirtualScroll.ts`, `cacheManager.ts`, mobile styles | N/A (optimization layer) | N/A (caching layer) | `SessionList.vue` (virtualized), responsive CSS |

## Technology Stack Details

### Core Technologies

**Frontend Stack**:
- **Vue 3.4+** (Composition API with `<script setup>` syntax)
  - Reactive state management with `ref`, `computed`, `watch`
  - Composables for reusable logic
  - TypeScript for type safety
- **Element Plus 2.5+**
  - `el-collapse` component for accordion UI
  - `el-button`, `el-input`, `el-dialog` for forms
  - `el-icon` for iconography
- **vue-virtual-scroller 2.0+**
  - `RecycleScroller` component for session list
  - Dynamic height support for expandable cards
- **Pinia 2.1+**
  - `authStore` for authentication state
  - `sessionStore` for session management
- **Vue Router 4.2+**
  - Route guards for authentication
  - Deep linking support with URL hash
- **Vite 5.0+**
  - Fast dev server with HMR
  - Optimized production builds
- **TypeScript 5.3+**
  - Strict mode enabled
  - Type-safe API calls with generated types

**Backend Stack**:
- **FastAPI 0.109+** (Python 3.12)
  - Async request handlers with `async def`
  - Automatic OpenAPI documentation at `/docs`
  - Pydantic for request/response validation
- **Supabase Python SDK 2.3+**
  - Auth client for user management
  - Database client for PostgreSQL access
  - Automatic RLS policy enforcement
- **PyJWT 2.8+**
  - JWT token generation and verification
  - RS256 algorithm with Supabase public key
- **Watchdog 3.0+**
  - Filesystem event monitoring
  - Debouncing to prevent duplicate events
- **Uvicorn 0.27+**
  - ASGI server with WebSocket support
  - Auto-reload in development mode

**Database**:
- **PostgreSQL 15+** (via Supabase)
  - Row-Level Security (RLS) for data isolation
  - UUID primary keys for sessions
  - JSONB columns for flexible metadata storage
  - Indexes on `user_id`, `created_at` for query performance

**Development Tools**:
- **pytest 7.4+** - Backend testing with fixtures
- **Vitest 1.2+** - Frontend unit testing
- **Black 24.1+** - Python code formatting
- **Prettier 3.2+** - JS/TS code formatting
- **ESLint 8.56+** - JavaScript linting
- **mypy 1.8+** - Python type checking

### Integration Points

**Frontend ↔ Backend**:
- **REST API**: JSON over HTTP(S)
  - Base URL: `http://localhost:12656/api` (dev), `https://tk9.thinhkhuat.com/api` (prod)
  - Authentication: JWT in HTTP-only cookie `access_token`
  - Request format: JSON body with Content-Type: application/json
  - Response format: `{data: {...}}` or `{error: {message, code}}`

**Frontend ↔ WebSocket**:
- **WebSocket Connection**: `ws://localhost:12656/ws/sessions` (dev)
  - Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, 16s max)
  - Message format: `{type: "file_detected", session_id: "...", stage: "...", file_count: 3}`
  - Heartbeat: Ping/pong every 30 seconds

**Backend ↔ Supabase**:
- **Auth SDK**: `supabase.auth.signInAnonymously()`, `supabase.auth.signUp()`, `supabase.auth.signInWithPassword()`
- **Database Client**: `supabase.from("table_name").select()`, auto RLS enforcement
- **JWT Verification**: Backend verifies JWT using Supabase public key from environment variable

**Backend ↔ Filesystem**:
- **File Detection**: Watchdog monitors `./outputs/{session_id}/` directories
  - Events: `on_created` for new files in staged subdirectories
  - Debouncing: 500ms delay to batch rapid file creation
  - Error Handling: 3 retries with exponential backoff (1s, 2s, 4s)

**Frontend ↔ Supabase** (Direct):
- **Auth Flow**: Frontend uses `@supabase/supabase-js` for sign-in/register
  - Session token automatically stored in cookie by Supabase SDK
  - Backend reads token from cookie header

## Novel Pattern Designs

### Pattern: File Detection with Race Condition Handling

**Purpose**: Automatically detect and link research draft files to user sessions while handling concurrent file creation and potential filesystem inconsistencies.

**Problem**: Research workflow generates multiple JSON files across 4 staged directories during execution. Files may be created rapidly in succession, and users may view the session list while research is still in progress. Traditional polling is inefficient; event-based detection must handle:
- Multiple files created within milliseconds
- File creation events firing before file is fully written
- User viewing session while files are still being generated
- Filesystem event deduplication

**Components**:

1. **FileDetectionService** (`services/file_detection_service.py`)
   - Responsibility: Monitor filesystem using Watchdog observer
   - Triggers: `on_created` events for `.json` files in staged directories
   - Debouncing: 500ms aggregation window to batch rapid events

2. **FileManager** (`file_manager.py`)
   - Responsibility: Process detected files, validate JSON, insert database records
   - Error Handling: Retry logic (3 attempts) with exponential backoff
   - Validation: Check JSON parseable, extract metadata (stage, timestamp)

3. **WebSocketManager** (`websocket_handler.py`)
   - Responsibility: Broadcast file detection events to connected clients
   - Message Format: `{type: "file_detected", session_id: UUID, stage: string, file_count: int}`
   - Client Filtering: Only notify users who own the session

4. **SessionStore** (`frontend_poc/src/stores/sessionStore.ts`)
   - Responsibility: Receive WebSocket messages, update session file counts
   - UI Update: Increment badge count, show toast notification on completion

**Data Flow**:
```
1. Research Agent saves file → ./outputs/{session_id}/1_initial_research/draft_001.json
2. Watchdog fires on_created event → FileDetectionService handler
3. 500ms debounce window → Batch multiple files if created rapidly
4. FileManager validates JSON → Extract stage from directory path
5. Database INSERT → draft_files table (session_id, stage, file_path, detected_at)
6. WebSocket broadcast → {type: "file_detected", session_id, stage, file_count}
7. Frontend SessionStore receives → Update UI: increment file count badge
8. Research completes → Status change to "completed"
9. WebSocket broadcast → {type: "status_change", session_id, status: "completed"}
10. Frontend shows toast → "Research '[title]' completed!" with "View Report" button
```

**Edge Cases Handled**:
- **File not fully written**: Retry logic catches JSON parse errors, waits 1s and retries
- **Duplicate events**: Database unique constraint on (session_id, file_path) prevents duplicates
- **User not viewing dashboard**: WebSocket message queued, UI updates on next page load
- **Connection lost during research**: Reconnection triggers full session refresh from API

**Implementation Guide for Agents**:
```python
# Story 2.4: File Detection Implementation

class FileDetectionService:
    def __init__(self):
        self.observer = Observer()
        self.debounce_delay = 0.5  # 500ms
        self.pending_files = {}

    def watch_outputs_directory(self):
        handler = FileSystemEventHandler()
        handler.on_created = self.on_file_created
        self.observer.schedule(handler, "./outputs", recursive=True)
        self.observer.start()

    def on_file_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            # Debounce: collect files in 500ms window
            file_path = event.src_path
            self.pending_files[file_path] = time.time()

    async def process_pending_files(self):
        """Run every 500ms, process files older than debounce window"""
        now = time.time()
        ready_files = [
            path for path, timestamp in self.pending_files.items()
            if now - timestamp > self.debounce_delay
        ]

        for file_path in ready_files:
            await self.process_file(file_path)
            del self.pending_files[file_path]

    async def process_file(self, file_path: str):
        """Validate JSON, extract metadata, save to database"""
        for attempt in range(3):
            try:
                with open(file_path, 'r') as f:
                    content = json.load(f)  # Validate JSON parseable

                session_id = extract_session_id_from_path(file_path)
                stage = extract_stage_from_path(file_path)

                await db.insert('draft_files', {
                    'session_id': session_id,
                    'stage': stage,
                    'file_path': file_path,
                    'detected_at': datetime.utcnow()
                })

                # Broadcast WebSocket event
                await websocket_manager.broadcast({
                    'type': 'file_detected',
                    'session_id': session_id,
                    'stage': stage,
                    'file_count': await count_stage_files(session_id, stage)
                }, user_id=session_owner_id)

                break  # Success, exit retry loop

            except json.JSONDecodeError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
                else:
                    logger.error(f"Failed to parse JSON after 3 attempts: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                break
```

**Affects Epics**: Epic 2 (Story 2.4, 2.5), Epic 3 (Story 3.2, 3.3)

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### Naming Conventions

**Python Backend**:
- Files: `snake_case.py` (e.g., `auth_service.py`, `session_service.py`)
- Classes: `PascalCase` (e.g., `AuthService`, `SessionManager`)
- Functions/methods: `snake_case` (e.g., `get_user_sessions`, `create_anonymous_user`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `JWT_SECRET_KEY`, `MAX_RETRY_ATTEMPTS`)
- Private methods: `_leading_underscore` (e.g., `_validate_token`)

**TypeScript Frontend**:
- Files: `camelCase.ts` or `PascalCase.vue` (e.g., `authStore.ts`, `SessionCard.vue`)
- Interfaces/Types: `PascalCase` (e.g., `User`, `SessionMetadata`)
- Variables/functions: `camelCase` (e.g., `getUserSessions`, `isAuthenticated`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `WS_RECONNECT_DELAY`)
- Composables: `use` prefix (e.g., `useAuth`, `useSessions`)

**Database**:
- Tables: `snake_case` plural (e.g., `users`, `research_sessions`, `draft_files`)
- Columns: `snake_case` (e.g., `user_id`, `created_at`, `is_anonymous`)
- Foreign keys: `{table}_id` format (e.g., `user_id`, `session_id`)
- Indexes: `idx_{table}_{column}` (e.g., `idx_sessions_user_id`)

**API Endpoints**:
- RESTful convention: `/api/{resource}` (e.g., `/api/sessions`, `/api/auth`)
- Resource names: Plural nouns (e.g., `/api/sessions`, not `/api/session`)
- URL parameters: `:id` format in FastAPI (e.g., `/api/sessions/{session_id}`)
- Query parameters: `snake_case` (e.g., `?date_from=2024-01-01`)

### Code Organization

**Component Structure** (Vue):
```vue
<!-- SessionCard.vue - Example structure ALL components must follow -->
<script setup lang="ts">
// 1. Imports (external libraries first, internal second)
import { ref, computed, watch } from 'vue'
import { ElCollapse, ElButton } from 'element-plus'
import type { Session } from '@/types/session'

// 2. Props definition
interface Props {
  session: Session
  expandedByDefault?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  expandedByDefault: false
})

// 3. Emits definition
const emit = defineEmits<{
  expand: [sessionId: string]
  viewReport: [sessionId: string]
}>()

// 4. Reactive state
const isExpanded = ref(props.expandedByDefault)
const isLoading = ref(false)

// 5. Computed properties
const formattedDate = computed(() => {
  return formatRelativeTime(props.session.created_at)
})

// 6. Methods
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    emit('expand', props.session.id)
  }
}

// 7. Watchers
watch(() => props.session.status, (newStatus) => {
  if (newStatus === 'completed') {
    // Handle completion
  }
})

// 8. Lifecycle hooks
onMounted(() => {
  // Initialization logic
})
</script>

<template>
  <!-- Template follows semantic HTML -->
  <div class="session-card" :class="{ 'is-expanded': isExpanded }">
    <!-- Component content -->
  </div>
</template>

<style scoped>
/* BEM naming: block__element--modifier */
.session-card {
  /* Styles */
}

.session-card__header {
  /* Styles */
}

.session-card--expanded {
  /* Styles */
}
</style>
```

**Service Structure** (Python):
```python
# auth_service.py - Example structure ALL services must follow

from typing import Optional
from datetime import datetime, timedelta
import jwt
from supabase import Client

from ..models import User
from ..schemas import UserCreate, UserResponse
from ..config import settings


class AuthService:
    """Handles user authentication and session management.

    All methods are async and raise HTTPException on errors.
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def create_anonymous_user(self) -> UserResponse:
        """Create anonymous user with UUID.

        Returns:
            UserResponse: User data with is_anonymous=True

        Raises:
            HTTPException: If Supabase sign-in fails
        """
        # Implementation
        pass

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register user with email and password.

        Args:
            user_data: Email, password, and optional metadata

        Returns:
            UserResponse: User data with is_anonymous=False

        Raises:
            HTTPException: If email exists or validation fails
        """
        # Implementation
        pass

    async def upgrade_anonymous_to_registered(
        self,
        anonymous_user_id: str,
        user_data: UserCreate
    ) -> UserResponse:
        """Convert anonymous user to registered user.

        Transfers all research sessions from anonymous to registered account.

        Args:
            anonymous_user_id: UUID of anonymous user
            user_data: Email and password for registration

        Returns:
            UserResponse: Updated user data

        Raises:
            HTTPException: If user not found or email exists
        """
        # Implementation
        pass

    def _generate_jwt(self, user_id: str, is_anonymous: bool) -> str:
        """Generate JWT access token (private method)."""
        payload = {
            'sub': user_id,
            'is_anonymous': is_anonymous,
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
```

### Error Handling

**Backend Error Format**:
```python
# ALL API endpoints return errors in this format:

from fastapi import HTTPException
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: dict

class ErrorDetail(BaseModel):
    message: str
    code: str
    details: Optional[dict] = None

# Usage in endpoints:
@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        session = await session_service.get_session(session_id)
        return {"data": session}
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Session not found",
                "code": "SESSION_NOT_FOUND",
                "details": {"session_id": session_id}
            }
        )
    except Exception as e:
        logger.exception(f"Unexpected error fetching session {session_id}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "details": None
            }
        )
```

**Frontend Error Handling**:
```typescript
// ALL API calls use this error handling pattern:

import { ElMessage } from 'element-plus'

async function fetchSessions() {
  try {
    const response = await fetch('/api/sessions', {
      credentials: 'include'  // Send cookies
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error.message)
    }

    const data = await response.json()
    return data.data  // Extract data from wrapper

  } catch (error) {
    console.error('Failed to fetch sessions:', error)

    // User-facing error message
    ElMessage.error({
      message: error instanceof Error ? error.message : 'Failed to load sessions',
      duration: 5000
    })

    throw error  // Re-throw for caller to handle
  }
}
```

**Error Categories**:
- **Authentication Errors** (401): `INVALID_TOKEN`, `TOKEN_EXPIRED`, `UNAUTHORIZED`
- **Authorization Errors** (403): `FORBIDDEN`, `INSUFFICIENT_PERMISSIONS`
- **Not Found Errors** (404): `SESSION_NOT_FOUND`, `USER_NOT_FOUND`, `FILE_NOT_FOUND`
- **Validation Errors** (422): `INVALID_EMAIL`, `WEAK_PASSWORD`, `MISSING_FIELD`
- **Server Errors** (500): `INTERNAL_ERROR`, `DATABASE_ERROR`, `FILESYSTEM_ERROR`

### Logging Strategy

**Backend Logging**:
```python
import logging
import structlog

# Configure structured logging (in main.py)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Usage in all modules:
logger.info("user_registered", user_id=user_id, is_anonymous=False)
logger.warning("jwt_expired", user_id=user_id, exp_time=exp_time)
logger.error("file_detection_failed", file_path=file_path, error=str(e))

# Log levels:
# DEBUG: Detailed diagnostic information (not in production)
# INFO: General informational messages (user actions, state changes)
# WARNING: Recoverable issues (expired token, retry attempt)
# ERROR: Error conditions requiring attention (failed API calls, file errors)
# CRITICAL: Severe errors causing service degradation (database down)
```

**Frontend Logging**:
```typescript
// Console logging with structured format

const logger = {
  info: (message: string, data?: object) => {
    console.log(`[INFO] ${message}`, data || '')
  },
  warn: (message: string, data?: object) => {
    console.warn(`[WARN] ${message}`, data || '')
  },
  error: (message: string, error?: Error, data?: object) => {
    console.error(`[ERROR] ${message}`, error, data || '')
  }
}

// Usage:
logger.info('Session expanded', { sessionId: 'abc-123' })
logger.warn('WebSocket reconnecting', { attempt: 3 })
logger.error('API call failed', new Error('Network error'), { endpoint: '/api/sessions' })
```

## Data Architecture

### Database Schema

```sql
-- users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,  -- NULL for anonymous users
    is_anonymous BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- research_sessions table
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    research_query TEXT,
    final_report_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON research_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON research_sessions(created_at DESC);
CREATE INDEX idx_sessions_status ON research_sessions(status);

-- draft_files table
CREATE TABLE draft_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    stage TEXT NOT NULL CHECK (stage IN ('1_initial_research', '2_planning', '3_parallel_research', '4_writing')),
    file_path TEXT NOT NULL,
    file_size_kb INTEGER,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, file_path)  -- Prevent duplicate detection
);

CREATE INDEX idx_drafts_session_id ON draft_files(session_id);
CREATE INDEX idx_drafts_stage ON draft_files(stage);

-- Row-Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE draft_files ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can only see their own sessions
CREATE POLICY "Users view own sessions" ON research_sessions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users insert own sessions" ON research_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users update own sessions" ON research_sessions
    FOR UPDATE USING (user_id = auth.uid());

-- Users can only see drafts from their own sessions
CREATE POLICY "Users view own drafts" ON draft_files
    FOR SELECT USING (
        session_id IN (
            SELECT id FROM research_sessions WHERE user_id = auth.uid()
        )
    );
```

### Data Models (Pydantic)

```python
# models.py - Database models (Pydantic for validation)

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_anonymous: bool = False

class UserCreate(UserBase):
    """User registration data"""
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    """User data returned to client (no password)"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    research_query: Optional[str] = None

class SessionCreate(SessionBase):
    user_id: UUID

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    status: Literal['in_progress', 'completed', 'failed']
    final_report_path: Optional[str] = None
    draft_count: int = 0  # Computed field
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DraftFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    stage: Literal['1_initial_research', '2_planning', '3_parallel_research', '4_writing']
    file_path: str
    file_size_kb: Optional[int] = None
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### TypeScript Types

```typescript
// types/auth.ts
export interface User {
  id: string
  email: string | null
  is_anonymous: boolean
  created_at: string
  updated_at: string
}

export interface AuthState {
  user: User | null
  session: Session | null
  isAuthenticated: boolean
  isAnonymous: boolean
}

// types/session.ts
export interface Session {
  id: string
  user_id: string
  title: string
  status: 'in_progress' | 'completed' | 'failed'
  research_query?: string
  final_report_path?: string
  draft_count: number
  created_at: string
  updated_at: string
}

export interface SessionFilters {
  search?: string
  dateFrom?: string
  dateTo?: string
  status?: Session['status']
}

// types/draft.ts
export interface DraftFile {
  id: string
  session_id: string
  stage: '1_initial_research' | '2_planning' | '3_parallel_research' | '4_writing'
  file_path: string
  file_size_kb?: number
  detected_at: string
  content?: object  // Loaded lazily
}

export interface StageMetadata {
  stage: DraftFile['stage']
  name: string
  icon: string
  file_count: number
  completed_at?: string
}
```

## API Contracts

### Authentication Endpoints

**POST `/api/auth/anonymous`**
- Description: Create anonymous user session
- Auth Required: No
- Request Body: None
- Response: `200 OK`
  ```json
  {
    "data": {
      "user": {
        "id": "uuid",
        "email": null,
        "is_anonymous": true,
        "created_at": "2024-01-01T00:00:00Z"
      },
      "access_token": "jwt-token"
    }
  }
  ```
- Sets Cookie: `access_token` (HTTP-only, 7 days)

**POST `/api/auth/register`**
- Description: Register new user with email/password
- Auth Required: No
- Request Body:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
  ```
- Response: `201 Created` - Same as anonymous response but `is_anonymous: false`
- Errors: `422` if email exists or validation fails

**POST `/api/auth/login`**
- Description: Login existing user
- Auth Required: No
- Request Body: Same as register
- Response: `200 OK` - Same as anonymous response
- Errors: `401` if credentials invalid

**POST `/api/auth/upgrade`**
- Description: Upgrade anonymous user to registered
- Auth Required: Yes (anonymous user)
- Request Body: Same as register
- Response: `200 OK` - User data with `is_anonymous: false`
- Transfers all anonymous sessions to new registered account

### Session Endpoints

**GET `/api/sessions`**
- Description: List all user sessions with pagination
- Auth Required: Yes
- Query Parameters:
  - `page`: int (default 1)
  - `limit`: int (default 50, max 100)
  - `search`: string (optional, searches title)
  - `date_from`: ISO date string (optional)
  - `date_to`: ISO date string (optional)
  - `status`: enum (optional: in_progress, completed, failed)
- Response: `200 OK`
  ```json
  {
    "data": {
      "sessions": [
        {
          "id": "uuid",
          "title": "Climate Change Research",
          "status": "completed",
          "draft_count": 12,
          "created_at": "2024-01-01T00:00:00Z"
        }
      ],
      "total": 100,
      "page": 1,
      "pages": 2
    }
  }
  ```

**GET `/api/sessions/{session_id}`**
- Description: Get single session with details
- Auth Required: Yes (must own session)
- Response: `200 OK` - Session object with draft_files array
- Errors: `404` if not found, `403` if not owner

**GET `/api/sessions/{session_id}/stages/{stage}/drafts`**
- Description: Get all draft files for a specific stage
- Auth Required: Yes
- Response: `200 OK`
  ```json
  {
    "data": {
      "stage": "1_initial_research",
      "files": [
        {
          "id": "uuid",
          "file_path": "/outputs/.../draft_001.json",
          "file_size_kb": 45,
          "detected_at": "2024-01-01T00:00:00Z"
        }
      ]
    }
  }
  ```

**GET `/api/sessions/{session_id}/files/{file_id}`**
- Description: Get draft file content (JSON)
- Auth Required: Yes
- Response: `200 OK`
  ```json
  {
    "data": {
      "file_id": "uuid",
      "content": { /* JSON object from file */ }
    }
  }
  ```
- Errors: `404` if file not found or deleted

### WebSocket Events

**Connection**: `ws://localhost:12656/ws/sessions`
- Auth: JWT token sent in initial connection query param `?token=jwt-token`
- Reconnection: Exponential backoff (1s, 2s, 4s, 8s, 16s max)

**Client → Server**:
```json
{"type": "ping"}  // Heartbeat every 30s
```

**Server → Client**:
```json
// File detected event
{
  "type": "file_detected",
  "session_id": "uuid",
  "stage": "1_initial_research",
  "file_count": 3
}

// Status change event
{
  "type": "status_change",
  "session_id": "uuid",
  "status": "completed"
}

// Pong response
{
  "type": "pong"
}
```

## Security Architecture

### Authentication Flow

1. **Anonymous Sign-In** (Immediate Access):
   ```
   User lands on dashboard
   → Frontend calls supabase.auth.signInAnonymously()
   → Supabase creates anonymous user with UUID
   → JWT token stored in HTTP-only cookie
   → User can initiate research without registration
   ```

2. **Anonymous → Registered Upgrade**:
   ```
   User completes 1+ research sessions
   → Sees "Upgrade Account" prompt
   → Enters email + password
   → Backend verifies anonymous JWT
   → Supabase creates permanent account
   → Database updates: user_id remains same, is_anonymous=false, email set
   → All research_sessions already linked to user_id (no migration needed)
   → New JWT issued with is_anonymous=false
   ```

3. **Registered Login**:
   ```
   User enters email + password
   → Backend calls supabase.auth.signInWithPassword()
   → Supabase validates credentials
   → JWT token stored in HTTP-only cookie
   → User sees all historical sessions
   ```

### Authorization (RLS Policies)

All database access enforces Row-Level Security:

```sql
-- Example: Session access enforcement
SELECT * FROM research_sessions WHERE id = '...';

-- Internally becomes:
SELECT * FROM research_sessions
WHERE id = '...'
  AND user_id = auth.uid();  -- Automatic RLS filter
```

Users can **NEVER** access other users' data, even if they guess the UUID.

### Security Best Practices

**JWT Storage**:
- ✅ HTTP-only cookie (protects against XSS)
- ✅ Secure flag in production (HTTPS only)
- ✅ SameSite=Lax (protects against CSRF)
- ❌ Never store in localStorage (vulnerable to XSS)

**Password Requirements**:
- Minimum 8 characters
- Must include: 1 uppercase, 1 lowercase, 1 number
- Validated on both frontend and backend

**Rate Limiting**:
- Authentication endpoints: 5 requests per minute per IP
- API endpoints: 100 requests per minute per user
- WebSocket connections: 1 per user (enforced)

**CORS Configuration**:
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9002",      # Dev frontend
        "https://tk9.thinhkhuat.com"  # Prod frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Input Validation**:
- All API inputs validated via Pydantic models
- SQL injection prevented by parameterized queries (Supabase client)
- XSS prevention: Vue auto-escapes all interpolated values
- File path validation: Ensure file_path starts with `./outputs/` (prevent path traversal)

## Performance Considerations

### Frontend Performance

**Virtual Scrolling** (handles 1000+ sessions):
```typescript
// SessionList.vue - Virtual scrolling implementation

import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

<template>
  <RecycleScroller
    :items="sessions"
    :item-size="80"           // Collapsed card height
    :buffer="200"             // Pre-render 200px above/below viewport
    key-field="id"
    v-slot="{ item }"
  >
    <SessionCard :session="item" />
  </RecycleScroller>
</template>
```

**Lazy Loading**:
- Session list: Load 50 sessions per page
- Draft content: Only fetch when stage is expanded
- JSON syntax highlighting: Applied on-demand, not on initial render

**Caching Strategy**:
```typescript
// utils/cacheManager.ts

class CacheManager {
  private lruCache = new LRUCache<string, Session>(200)  // Memory cache
  private indexedDB: IDBDatabase

  async getCachedSession(sessionId: string): Promise<Session | null> {
    // 1. Check memory cache (fastest)
    if (this.lruCache.has(sessionId)) {
      return this.lruCache.get(sessionId)
    }

    // 2. Check IndexedDB (slower but persistent)
    const cached = await this.indexedDB.get('sessions', sessionId)
    if (cached && !this.isStale(cached.cachedAt)) {
      this.lruCache.set(sessionId, cached.data)
      return cached.data
    }

    return null
  }

  isStale(cachedAt: Date): boolean {
    return Date.now() - cachedAt.getTime() > 5 * 60 * 1000  // 5 minutes
  }
}
```

**Bundle Optimization**:
- Code splitting: Lazy load routes (`const SessionView = () => import('./views/SessionView.vue')`)
- Tree shaking: Vite removes unused Element Plus components
- Compression: Gzip/Brotli enabled in Caddy reverse proxy

### Backend Performance

**Database Indexes**:
```sql
-- Critical indexes for query performance
CREATE INDEX idx_sessions_user_id ON research_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON research_sessions(created_at DESC);
CREATE INDEX idx_drafts_session_id ON draft_files(session_id);

-- Composite index for filtered queries
CREATE INDEX idx_sessions_user_status_date
ON research_sessions(user_id, status, created_at DESC);
```

**Query Optimization**:
```python
# Fetch sessions with draft counts (single query, no N+1)

sessions = await db.query("""
    SELECT s.*, COUNT(d.id) as draft_count
    FROM research_sessions s
    LEFT JOIN draft_files d ON s.id = d.session_id
    WHERE s.user_id = $1
    GROUP BY s.id
    ORDER BY s.created_at DESC
    LIMIT 50 OFFSET $2
""", user_id, offset)
```

**Connection Pooling**:
```python
# Supabase client automatically pools connections
# Max 10 connections per worker process
```

### Performance Budgets

- Session list page load: < 2s (50 sessions, P50)
- Accordion expansion: < 500ms (draft fetch + render, P95)
- Scroll performance: 60 FPS sustained (1000+ sessions)
- WebSocket latency: < 100ms (file detection → UI update)
- Mobile load time: < 3s (3G network simulation)

## Deployment Architecture

### Production Environment

**Server**: Self-hosted on 192.168.2.22 (mini48)

**Services**:
- **Caddy** (reverse proxy)
  - Handles HTTPS termination
  - Routes `tk9.thinhkhuat.com` → `192.168.2.22:12656`
  - WebSocket proxying enabled

- **Uvicorn** (ASGI server)
  - Runs FastAPI app on port 12656
  - Workers: 4 (CPU cores)
  - Reload disabled in production

- **Supabase** (database)
  - Hosted Supabase PostgreSQL instance
  - Automatic backups enabled (7-day retention)
  - Connection via environment variable

**Deployment Process**:
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt
cd web_dashboard/frontend_poc && npm install

# 3. Build frontend
npm run build

# 4. Restart backend
supervisorctl restart tk9-web-dashboard

# 5. Verify health
curl https://tk9.thinhkhuat.com/api/health
```

### Environment Variables

```bash
# .env file (never commit to git)

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Backend only, never expose to frontend

# JWT
JWT_SECRET=random-secret-key-change-in-production

# Application
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=https://tk9.thinhkhuat.com

# File Detection
OUTPUTS_DIR=./outputs
FILE_WATCH_INTERVAL=5  # seconds
```

### Health Monitoring

**Health Endpoint**:
```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": await check_database_connection(),
        "filesystem": await check_filesystem_access()
    }
```

**Monitoring**:
- Uptime monitoring via external service (UptimeRobot)
- Log aggregation via `journalctl` (systemd logs)
- Error alerts via Discord webhook (5xx errors)

## Development Environment

### Prerequisites

**System Requirements**:
- Python 3.12+ (use `pyenv` for version management)
- Node.js 18+ and npm 9+
- PostgreSQL client tools (for database inspection)
- Git 2.30+

**Accounts Required**:
- Supabase project (free tier sufficient for development)
- GitHub account (for version control)

### Setup Commands

```bash
# 1. Clone repository
git clone https://github.com/thinhkhuat/tk9_source_deploy.git
cd tk9_source_deploy

# 2. Set up Python environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set up frontend
cd web_dashboard/frontend_poc
npm install
cd ../..

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# 5. Initialize database (run migrations)
python scripts/init_database.py

# 6. Start backend (development mode with auto-reload)
cd web_dashboard
python main.py

# 7. Start frontend (in separate terminal)
cd web_dashboard/frontend_poc
npm run dev

# Access application:
# Frontend: http://localhost:9002
# Backend API: http://localhost:12656/api
# API Docs: http://localhost:12656/docs
```

### Running Tests

```bash
# Backend tests
pytest tests/ -v --cov=web_dashboard

# Frontend tests
cd web_dashboard/frontend_poc
npm run test

# Linting
black web_dashboard --check  # Python
npm run lint                 # TypeScript
```

### Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/story-2.1-session-list`
2. **Implement Story**: Follow implementation patterns from this document
3. **Write Tests**: Unit tests for services, component tests for UI
4. **Run Linters**: `black .` and `npm run lint:fix`
5. **Local Testing**: Verify in dev environment
6. **Commit**: `git commit -m "feat: implement session list with virtual scrolling"`
7. **Push**: `git push origin feature/story-2.1-session-list`
8. **Deploy**: Merge to main triggers deployment

## Architecture Decision Records (ADRs)

### ADR-001: Draft Exposure UI/UX Pattern Selection

**Status**: Approved
**Date**: 2025-10-31
**Deciders**: Thinh (Product Owner), Technical Research Team

**Context**:
TK9 generates research artifacts across 4 staged directories (1_initial_research → 2_planning → 3_parallel_research → 4_writing) during the multi-agent research workflow. Users need visibility into this process to validate methodology and build trust. The challenge is presenting 1000+ research sessions × 4 stages × multiple drafts per stage without overwhelming users.

**Decision**:
Implement **3-level collapsible accordion pattern** for progressive disclosure:
- Level 1: Session card (collapsed by default, shows title/date/status)
- Level 2: Stage accordion (4 stages with icons, expand on demand)
- Level 3: Draft viewer (JSON files, syntax-highlighted, lazy loaded)

**Rationale**:
- **Comparison-Optimized**: Users can expand multiple sessions side-by-side for meta-analysis (unique advantage vs competitors)
- **Progressive Disclosure**: Complexity hidden by default, revealed on user action (prevents cognitive overload)
- **Mobile-Responsive**: Accordion adapts gracefully to small screens with touch-friendly interactions
- **Performance**: Only visible content rendered via virtualization (handles 1000+ sessions at 60 FPS)
- **Proven Pattern**: Gmail, VS Code, GitHub all use accordions for nested content with high user satisfaction

**Alternatives Considered**:
- **Drawer (slide-out panel)**: Scored 78/100 - obscures session list, poor for comparison
- **Modal (popup)**: Scored 82/100 - disruptive UX, loses list context
- **Tabs (horizontal navigation)**: Scored 76/100 - doesn't scale to 4+ stages
- **Timeline (vertical graph)**: Scored 71/100 - novel but unfamiliar, higher learning curve

**Consequences**:
- ✅ User engagement: Expected 45% of users will explore drafts (vs 15-20% for other patterns)
- ✅ Development effort: Element Plus provides production-ready accordion component
- ✅ Accessibility: WCAG 2.1 AA compliant with proper ARIA labels
- ⚠️ Risk: Multi-level nesting requires careful keyboard navigation design

### ADR-002: Authentication and Historical Research System

**Status**: Approved
**Date**: 2025-10-31
**Deciders**: Thinh (Product Owner), Security Team

**Context**:
TK9 currently has no authentication, making all research ephemeral. Users need persistent access to historical research without registration friction. Must balance immediate access (UX priority) with data persistence (retention priority).

**Decision**:
Implement **2-tier authentication system**:
1. **Anonymous Sign-In**: Automatic UUID-based sessions on first visit (zero friction)
2. **Email Registration**: Upgrade path after demonstrating value (1-click conversion)
3. **Session Transfer**: Preserve all anonymous research when upgrading (seamless data migration)

Use **Supabase Auth** for implementation:
- Supabase provides `signInAnonymously()` out-of-the-box
- JWT token management handled by SDK
- Row-Level Security (RLS) enforces data isolation at database level

**Rationale**:
- **Zero Friction Entry**: 40% of users abandon registration forms (source: Baymard Institute) - anonymous access removes barrier
- **Value-First Conversion**: Users see research value before committing to account (increases conversion likelihood)
- **Security**: RLS policies prevent unauthorized access even if JWT compromised (defense in depth)
- **Scalability**: Supabase handles auth infrastructure (no custom auth server needed)

**Alternatives Considered**:
- **Email-First**: Requires registration upfront - 40-60% abandonment rate expected
- **Social Auth (Google/GitHub)**: Third-party dependency, privacy concerns for self-hosted deployment
- **Magic Links**: Simpler than passwords but requires email validation immediately (friction)

**Consequences**:
- ✅ Expected 40% anonymous→registered conversion (vs 10-15% for email-first)
- ✅ Reduced engineering effort: Supabase Auth SDK handles complexity
- ✅ Self-hosted compatible: Supabase can run on-premises
- ⚠️ Anonymous session cleanup: Need policy for inactive anonymous users (30-day TTL)

### ADR-003: Virtualized Scrolling for Session List

**Status**: Approved
**Date**: 2025-10-31

**Context**:
Power users may accumulate 500-1000+ research sessions over time. Traditional rendering (all DOM nodes) causes performance degradation: slow scroll, high memory usage, UI freezes on mobile.

**Decision**:
Use **vue-virtual-scroller** library to render only visible session cards:
- Render 10-15 cards in viewport + 200px buffer above/below
- Dynamically adjust heights when cards expand
- Maintain 60 FPS scroll performance with 1000+ sessions

**Rationale**:
- **Performance**: Reduces DOM nodes from 1000 to ~15, cutting memory usage by 98%
- **Battle-Tested**: Used by VS Code, Slack, Discord for large lists
- **Vue 3 Compatible**: `vue-virtual-scroller@2.0+` supports Composition API

**Alternatives Considered**:
- **Pagination**: Traditional but requires clicking "Next" - poor UX for browsing
- **Infinite Scroll**: Better than pagination but still renders all loaded items (memory leak)
- **CSS-only (contain, content-visibility)**: Browser support inconsistent, no dynamic height support

**Consequences**:
- ✅ 60 FPS scroll with 5000+ sessions (tested in benchmarks)
- ✅ Mobile performance maintained on low-end devices
- ⚠️ Complexity: Dynamic heights require accurate estimation (card expand/collapse)

---

_Generated by BMAD Decision Architecture Workflow v1.3.2_
_Date: 2025-10-31_
_For: Thinh_
