# Hardcoded Values Audit & Configuration Proposal

**Date**: 2025-11-01
**Scope**: TK9 Deep Research Web Dashboard (Backend + Frontend)
**Purpose**: Identify hardcoded values suitable for .env configuration

---

## Executive Summary

Found **23 hardcoded values** across backend and frontend that should be configurable via environment variables. These are categorized by priority:

- **🔴 HIGH Priority**: 8 values - Critical for deployment/operations
- **🟡 MEDIUM Priority**: 10 values - Improve flexibility and maintenance
- **🟢 LOW Priority**: 5 values - Nice to have, minimal impact

---

## 🔴 HIGH PRIORITY (8 values)

### 1. CORS Origins (Backend)
**Location**: `web_dashboard/main.py:71-78`
**Current**:
```python
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:12656",
    "http://127.0.0.1:12656",
    "http://192.168.2.22:12656",
    "http://192.168.2.22:5173",
]
```

**Proposed**:
```env
# Backend .env
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:12656,http://127.0.0.1:12656,http://192.168.2.22:12656,http://192.168.2.22:5173,https://tk9.thinhkhuat.com
```

**Rationale**: Production deployments need custom origins. Currently requires code change.

---

### 2. Backend Server Port (Backend)
**Location**: `web_dashboard/main.py:721`
**Current**: `port=12656`
**Proposed**:
```env
PORT=12656  # Already in .env.example but not used in code!
```

**Rationale**: Code ignores PORT env var, uses hardcoded 12656.

---

### 3. API Timeout (Frontend)
**Location**: `frontend_poc/src/services/api.ts:11`
**Current**: `const API_TIMEOUT = 30000 // 30 seconds`
**Proposed**:
```env
# Frontend .env
VITE_API_TIMEOUT=30000
```

**Rationale**: Research operations may need longer timeouts in some environments.

---

### 4. File Download Timeout (Frontend)
**Location**: `frontend_poc/src/services/api.ts:312, 427`
**Current**: `timeout: 60000 // 60 seconds`
**Proposed**:
```env
VITE_FILE_DOWNLOAD_TIMEOUT=60000
```

**Rationale**: Large files may need extended timeouts.

---

### 5. File Wait Timeout (Backend)
**Location**: `web_dashboard/main.py:638`
**Current**: `await file_manager.wait_for_files(session_id, subject, timeout=30)`
**Proposed**:
```env
FILE_WAIT_TIMEOUT=30
```

**Rationale**: Research generation time varies by complexity.

---

### 6. Default Research Language (Backend)
**Location**: `web_dashboard/models.py:13`
**Current**: `language: str = Field(default="vi", description="Output language")`
**Proposed**:
```env
DEFAULT_RESEARCH_LANGUAGE=vi  # Already in .env.example!
```

**Rationale**: Different deployments may prefer different default languages.

---

### 7. Session Cleanup Interval (Backend)
**Location**: `web_dashboard/main.py:702`
**Current**: `await asyncio.sleep(3600)  # 1 hour`
**Proposed**:
```env
SESSION_CLEANUP_INTERVAL=3600
```

**Rationale**: Production may need different cleanup frequencies.

---

### 8. WebSocket Reconnection Delay (Frontend)
**Location**: `frontend_poc/src/stores/sessionStore.ts:180`
**Current**: `console.log('🔄 Attempting to reconnect in 3 seconds...')`
**Proposed**:
```env
VITE_WS_RECONNECT_DELAY=3000
```

**Rationale**: Network conditions vary, reconnection strategy should be configurable.

---

## 🟡 MEDIUM PRIORITY (10 values)

### 9. Auth Initialization Polling (Frontend)
**Location**: Multiple files (HomeView.vue:27, SessionsDashboard.vue:23, router/index.ts:66)
**Current**: `while (authStore.isInitializing && attempts < 50)`
**Proposed**:
```env
VITE_AUTH_MAX_ATTEMPTS=50
VITE_AUTH_POLL_INTERVAL=100
```

**Rationale**: Auth timing may vary across environments.

---

### 10. Pagination Page Size (Frontend)
**Location**: `frontend_poc/src/stores/sessionsStore.ts:43`
**Current**: `const pageSize = ref(20)`
**Proposed**:
```env
VITE_SESSIONS_PAGE_SIZE=20
```

**Rationale**: Users may prefer different page sizes.

---

### 11. Quote Rotation Interval (Frontend)
**Location**: `frontend_poc/src/components/WaitingExperience/QuoteDisplay.vue:56`
**Current**: `const QUOTE_ROTATION_INTERVAL = 10000 // 10 seconds`
**Proposed**:
```env
VITE_QUOTE_ROTATION_INTERVAL=10000
```

**Rationale**: UX preference may vary by deployment.

---

### 12. CLI Process Cleanup Timeout (Backend)
**Location**: `web_dashboard/cli_executor.py:189`
**Current**: `await asyncio.wait_for(process.wait(), timeout=10)`
**Proposed**:
```env
CLI_PROCESS_CLEANUP_TIMEOUT=10
```

**Rationale**: Graceful shutdown timing.

---

### 13. File Discovery Sleep Interval (Backend)
**Location**: `web_dashboard/file_manager.py:223`
**Current**: `await asyncio.sleep(2)`
**Proposed**:
```env
FILE_DISCOVERY_POLL_INTERVAL=2
```

**Rationale**: File system polling frequency.

---

### 14. WebSocket Health Check Interval (Backend)
**Location**: `web_dashboard/websocket_handler.py:387`
**Current**: `await asyncio.sleep(2)`
**Proposed**:
```env
WS_HEALTH_CHECK_INTERVAL=2
```

**Rationale**: Network stability varies.

---

### 15. WebSocket Receive Timeout (Backend)
**Location**: `web_dashboard/websocket_handler.py:407`
**Current**: `message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)`
**Proposed**:
```env
WS_RECEIVE_TIMEOUT=1.0
```

**Rationale**: WebSocket timing configuration.

---

### 16. Max Concurrent Sessions (Backend)
**Location**: `.env.example:49` (already exists but may not be enforced)
**Current**: `MAX_CONCURRENT_SESSIONS=5`
**Status**: ✅ Already in .env.example
**Action**: Verify enforcement in code

---

### 17. Session Timeout (Backend)
**Location**: `.env.example:52` (already exists but may not be enforced)
**Current**: `SESSION_TIMEOUT=3600`
**Status**: ✅ Already in .env.example
**Action**: Verify enforcement in code

---

### 18. API Base URL Fallback (Frontend)
**Location**: `frontend_poc/src/services/api.ts:10`
**Current**: `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:12656'`
**Status**: ✅ Already configurable
**Note**: Fallback value is appropriate

---

## 🟢 LOW PRIORITY (5 values)

### 19. WebSocket Reconnection Max Attempts (Legacy Frontend)
**Location**: `web_dashboard/static/js/websocket-client.js:8-10`
**Current**:
```javascript
this.reconnectAttempts = 0;
this.reconnectDelay = 1000;
this.maxReconnectAttempts = 10; // Inferred from context
```

**Proposed**:
```env
WS_MAX_RECONNECT_ATTEMPTS=10
WS_INITIAL_RECONNECT_DELAY=1000
WS_MAX_RECONNECT_DELAY=30000
```

**Rationale**: Legacy code, Vue frontend is primary.

---

### 20-23. Animation & UX Timings (Frontend)
**Locations**: Various WaitingExperience components
**Examples**:
- Fade transition: 300ms (QuoteDisplay.vue:323)
- Shape rotation intervals (origami-shapes.ts)
- Stage acceleration thresholds (types.ts)

**Proposed**: Generally **NOT recommended** for configuration
**Rationale**: These are UX design decisions, not operational config. Changing them requires design review.

---

## Proposed Implementation Plan

### Phase 1: Critical Operations (HIGH Priority)
**Timeline**: Immediate
**Items**: 1-8 above
**Impact**: High - Enables proper deployment configuration

### Phase 2: Flexibility Improvements (MEDIUM Priority)
**Timeline**: Next sprint
**Items**: 9-18 above
**Impact**: Medium - Improves maintainability

### Phase 3: Nice-to-Have (LOW Priority)
**Timeline**: Future/As needed
**Items**: 19-23 above
**Impact**: Low - Minimal operational benefit

---

## File Changes Required

### Backend Files to Modify:
1. `web_dashboard/main.py` - CORS origins, server port, file wait timeout, cleanup interval
2. `web_dashboard/models.py` - Default language (use env var)
3. `web_dashboard/cli_executor.py` - Process cleanup timeout
4. `web_dashboard/file_manager.py` - File discovery interval
5. `web_dashboard/websocket_handler.py` - WebSocket timeouts

### Frontend Files to Modify:
1. `frontend_poc/src/services/api.ts` - API timeout, file download timeout
2. `frontend_poc/src/stores/sessionStore.ts` - WebSocket reconnection delay
3. `frontend_poc/src/stores/sessionsStore.ts` - Pagination page size
4. `frontend_poc/src/router/index.ts` - Auth polling config
5. `frontend_poc/src/views/HomeView.vue` - Auth polling config
6. `frontend_poc/src/views/SessionsDashboard.vue` - Auth polling config
7. `frontend_poc/src/components/WaitingExperience/QuoteDisplay.vue` - Quote rotation interval

### Environment Files to Update:
1. `web_dashboard/.env.example` - Add all backend env vars
2. `frontend_poc/.env` - Add all frontend env vars

### New Config Files to Create:
1. `frontend_poc/src/config/api.ts` - API configuration module
2. `frontend_poc/src/config/timing.ts` - Timing/polling configuration module
3. `frontend_poc/src/config/pagination.ts` - Pagination configuration module

---

## Validation Checklist

Before implementation:
- [ ] Review with team for additional hardcoded values
- [ ] Confirm default values are appropriate
- [ ] Ensure backward compatibility (fallback values)
- [ ] Plan deployment configuration updates
- [ ] Document all new environment variables

---

## Notes

1. **Validation Constraints**: MIN/MAX_SUBJECT_LENGTH already configurable ✅
2. **Port Configuration**: Backend .env.example has PORT but code doesn't use it ❌
3. **CORS**: Most critical - blocks production deployment currently
4. **Timeouts**: Second most critical - affects user experience
5. **Auth Polling**: Duplicated across 3 files - consolidate to config module

---

## Recommendation

**Start with Phase 1 (items 1-8)** - These are critical for production deployment and will have immediate operational benefits.

Would you like me to proceed with implementing these changes?
