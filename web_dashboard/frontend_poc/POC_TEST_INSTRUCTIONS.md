# Phase 0 POC - Test Instructions

## What Was Created

✅ **Backend:** Added POC test event to WebSocket handler
✅ **Frontend:** Complete Vue.js 3 + TypeScript + Pinia app
✅ **State Management:** Pinia store for WebSocket connection
✅ **UI:** Proof-of-concept dashboard component

## How to Test

### Terminal 1: Start FastAPI Backend

```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy/web_dashboard
python main.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:12656
```

### Terminal 2: Start Vue.js Dev Server

```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy/web_dashboard/frontend_poc
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Open Browser

Navigate to: `http://localhost:5173`

## Expected Results

### Step 1: Initial State (0-2 seconds)
- See "🎯 TK9 Dashboard - Proof of Concept" header
- Status indicator shows "connecting" (yellow/orange background)
- Loading spinner visible
- Message: "⏳ Connecting to WebSocket..."
- Hint: "(This should appear after ~2 seconds)"

### Step 2: Connected (after 2 seconds)
- Status indicator changes to "connected" (green background)
- Loading message disappears
- Success message appears: "✅ Connection Successful!"
- Checklist of validated components:
  - ✓ Vue.js 3 + TypeScript
  - ✓ Vite development server
  - ✓ Pinia state management
  - ✓ WebSocket connection established
  - ✓ FastAPI backend sending structured JSON events
  - ✓ Reactive UI updates on state changes

### Step 3: Event Data Display
- JSON event data displayed in formatted code block:
  ```json
  {
    "event_type": "agent_update",
    "payload": {
      "agent_id": "proof_of_concept_agent",
      "agent_name": "PoC Agent",
      "status": "completed",
      "message": "Connection validated ✅"
    },
    "timestamp": "2025-10-31T..."
  }
  ```

### Step 4: Next Steps Displayed
- Section showing next steps:
  1. Consult Gemini for validation
  2. Begin Phase 1 (State Management & Infrastructure)
  3. Build the full agent dashboard

## Success Criteria

✅ **All of these must be true:**

1. WebSocket connects successfully (green status indicator)
2. Event is received after ~2 seconds
3. UI updates reactively (loading → success)
4. JSON data is displayed correctly
5. No errors in browser console
6. No errors in FastAPI backend logs

## Troubleshooting

### Issue: WebSocket fails to connect

**Check:**
- Is FastAPI running on port 12656?
- Run: `lsof -i :12656` to verify
- Check FastAPI logs for errors

**Fix:**
```bash
# Restart backend
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy/web_dashboard
python main.py
```

### Issue: CORS errors in browser console

**Fix:** Add CORS middleware to FastAPI (if not present):

```python
# In main.py, add:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Module not found errors

**Fix:**
```bash
cd frontend_poc
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: TypeScript errors

**Check:** Ensure `sessionStore.ts` is in `src/stores/` directory

**Verify:**
```bash
ls -la src/stores/
```

## Browser DevTools Inspection

### Console Tab
**Expected logs:**
```
✅ WebSocket connected
📨 Received: {event_type: "agent_update", ...}
```

### Network Tab (WebSocket filter)
- Should see WebSocket connection to `ws://localhost:12656/ws/test-session-poc`
- Status: 101 Switching Protocols
- Messages tab shows sent/received data

## What This Validates

This POC proves that:

✅ **Technology Stack:**
- Vue.js 3 with TypeScript works
- Vite dev server works
- Pinia state management works

✅ **Architecture:**
- WebSocket connection establishes
- Backend can send structured JSON events
- Pinia store receives and processes events
- Vue components react to state changes

✅ **Data Flow:**
```
FastAPI Backend
    ↓ (WebSocket)
Pinia Store (state update)
    ↓ (reactive)
Vue Component (UI update)
```

## Next Steps After Successful POC

1. **Document Results:** Take screenshots of success state
2. **Consult Gemini:** Validate approach with AI expert
3. **Begin Phase 1:** Full implementation of production app

## Files Created

```
web_dashboard/
├── websocket_handler.py (modified - added POC event)
└── frontend_poc/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.ts (modified - added Pinia)
        ├── App.vue (replaced - POC UI)
        └── stores/
            └── sessionStore.ts (new - state management)
```

## Clean Up (Optional)

After validation, to remove POC event from backend:

```python
# In web_dashboard/websocket_handler.py, remove lines 98-109:
# POC: Send test event after 2 seconds
# await asyncio.sleep(2)
# await websocket.send_text(json.dumps({
#     ...
# }))
```

**But keep it for now** - it's useful for testing during Phase 1!

---

**POC Created:** 2025-10-31
**Ready to Test:** YES
**Expected Duration:** 5 minutes
**Success Rate:** High (validated approach)
