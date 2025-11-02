# Configuration Module

This directory contains centralized configuration for the TK9 Deep Research frontend.

## Files

### `api.ts`

Centralized API and timing configuration for HTTP requests and WebSocket connections.

**Purpose:**
- Single source of truth for API timeouts and connection settings
- Prevents hardcoded timeout values scattered across codebase
- Configurable via environment variables for different deployment environments

**Usage:**

```typescript
import { API_TIMEOUT, FILE_DOWNLOAD_TIMEOUT, WS_RECONNECT_DELAY, API_CONFIG } from '@/config/api'

// Use individual constants
const timeout = API_TIMEOUT // 30000ms (30 seconds)

// Or use the configuration object
const config = API_CONFIG
console.log(config.timeout) // 30000
console.log(config.fileDownloadTimeout) // 60000
console.log(config.wsReconnectDelay) // 3000
```

**Configuration:**

Set these environment variables in `.env`:

```env
VITE_API_TIMEOUT=30000
VITE_FILE_DOWNLOAD_TIMEOUT=60000
VITE_WS_RECONNECT_DELAY=3000
```

**Exported Constants:**
- `API_BASE_URL` - Backend API base URL
- `WS_BASE_URL` - WebSocket base URL
- `API_TIMEOUT` - Standard API request timeout (30s default)
- `FILE_DOWNLOAD_TIMEOUT` - Extended timeout for file downloads (60s default)
- `WS_RECONNECT_DELAY` - WebSocket reconnection delay (3s default)
- `API_CONFIG` - Complete configuration object

---

### `validation.ts`

Centralized validation rules for form inputs that must match backend constraints.

**Purpose:**
- Single source of truth for validation rules
- Prevents frontend/backend validation mismatches
- Configurable via environment variables

**Usage:**

```typescript
import { MIN_SUBJECT_LENGTH, MAX_SUBJECT_LENGTH, VALIDATION_CONFIG } from '@/config/validation'

// Use constants
const maxLength = MAX_SUBJECT_LENGTH // 1000

// Use validation helper
const result = VALIDATION_CONFIG.validateSubject(userInput)
if (!result.valid) {
  console.error(result.error)
}
```

**Configuration:**

Set these environment variables in `.env`:

```env
VITE_MIN_SUBJECT_LENGTH=3
VITE_MAX_SUBJECT_LENGTH=1000
```

**IMPORTANT:** These values MUST match backend validation in:
- `web_dashboard/models.py` (ResearchRequest Pydantic model)
- `web_dashboard/.env.example`

## Adding New Configuration

When adding new configurable values:

1. **Add to `.env` files:**
   - `frontend_poc/.env` (development)
   - `web_dashboard/.env.example` (documentation)

2. **Create config module:**
   - Add a new file in `src/config/` (e.g., `feature.ts`)
   - Export constants with fallback values
   - Document usage in this README

3. **Update components:**
   - Import from config module (not direct env access)
   - This ensures consistency and testability

## Best Practices

✅ **DO:**
- Use centralized config modules
- Provide sensible fallback values
- Document backend dependencies
- Keep frontend/backend in sync

❌ **DON'T:**
- Read `import.meta.env` directly in components
- Hardcode validation rules
- Forget to update .env.example
- Change values without checking backend

## Environment Variable Naming

- Frontend: `VITE_*` prefix (required by Vite)
- Backend: No prefix needed
- Keep names consistent between frontend/backend where possible
