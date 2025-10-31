# File Detection and Availability Logic

**Date**: October 31, 2025
**Status**: ✅ CRITICAL BUG FIXED - File detection now working correctly

## 🎯 Quick Summary

The system detects research output files through a **3-stage process**:

1. **Background Monitoring**: After CLI completes, backend monitors `./outputs/` directory
2. **File Discovery**: Scans session directory for PDF/DOCX/MD files
3. **WebSocket Notification**: Sends `file_generated` events to frontend

---

## 📊 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Research Starts                                          │
│    POST /api/research → background_tasks.add_task()         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CLI Execution                                            │
│    cli_executor.execute_research()                          │
│    → Outputs to: ./outputs/run_{timestamp}_{subject}/      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CLI Completes                                            │
│    websocket_manager.stream_cli_output() finishes           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. File Detection Phase                                     │
│    file_manager.wait_for_files(session_id, timeout=30)      │
│                                                              │
│    Polls every 2 seconds for up to 30 seconds:             │
│      - Calls discover_session_files(session_id)             │
│      - Scans: ./outputs/{session_id}/                       │
│      - Finds: *.pdf, *.docx, *.md                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. File Discovery Logic (file_manager.py:95-124)           │
│                                                              │
│    def discover_session_files(session_id: str):             │
│      session_dir = ./outputs/{session_id}                   │
│                                                              │
│      for file_path in session_dir.iterdir():               │
│        if file_path.is_file():                             │
│          if file_path.suffix in ['.pdf', '.docx', '.md']:  │
│            files.append(FileInfo(...))                     │
│                                                              │
│      return files  # List of FileInfo objects              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. WebSocket Event Broadcasting (main.py:299-312)          │
│                                                              │
│    if files:                                                │
│      for file in files:                                     │
│        file_event = create_file_generated_event(            │
│          session_id=session_id,                             │
│          file_id=file.filename,                             │
│          filename=friendly_name,  # e.g., "research_report.pdf" │
│          file_type="pdf",                                   │
│          language="vi",                                     │
│          size_bytes=file.size                               │
│        )                                                     │
│        await websocket_manager.send_event(session_id, event)│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Frontend Receives Event (sessionStore.ts:208-211)       │
│                                                              │
│    case 'file_generated':                                   │
│      handleFileGenerated(event.payload)                     │
│        → files.value.push(payload)                          │
│        → Console: "📄 File generated: research_report.pdf"  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. UI Updates (FileExplorer.vue)                           │
│                                                              │
│    <div v-for="file in store.files">                        │
│      <button @click="downloadFile(file)">                   │
│        Download {{ file.filename }}                         │
│      </button>                                              │
│    </div>                                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Core Logic Details

### 1. File Monitoring (main.py:297)

**After CLI completes**, the backend waits for files:

```python
# main.py:297
files = await file_manager.wait_for_files(session_id, subject, timeout=30)
```

**How it works**:
```python
# file_manager.py:208-224
async def wait_for_files(session_id: str, timeout: int = 30):
    start_time = datetime.now()

    while (datetime.now() - start_time).seconds < timeout:
        files = await discover_session_files(session_id)  # Poll

        if files:
            return files  # Found files, exit

        await asyncio.sleep(2)  # Wait 2 seconds, try again

    return []  # Timeout, no files found
```

**Key Points**:
- ⏱️ Polls every **2 seconds**
- ⏳ Timeout after **30 seconds**
- 🔁 Keeps checking until files appear or timeout
- ✅ Returns immediately when files found

---

### 2. File Discovery (file_manager.py:95-124)

**Scans the session directory** for output files:

```python
async def discover_session_files(session_id: str) -> List[FileInfo]:
    files = []
    session_dir = outputs_path / session_id  # e.g., ./outputs/run_1761898976_...

    # Scan directory for supported files
    for file_path in session_dir.iterdir():
        if file_path.is_file() and file_path.suffix in ['.pdf', '.docx', '.md']:

            # Create friendly name from UUID filename
            # e.g., "abc123.pdf" → "research_report.pdf"
            # e.g., "abc123_vi.pdf" → "research_report_vi.pdf"
            friendly_name = create_friendly_filename_from_uuid(file_path.name)

            file_info = FileInfo(
                filename=friendly_name,
                url=f"/download/{session_id}/{file_path.name}",
                size=file_path.stat().st_size,
                created=datetime.fromtimestamp(file_path.stat().st_ctime)
            )
            files.append(file_info)

    # Sort: English files first, then Vietnamese
    files.sort(key=lambda f: get_file_sort_priority(f.filename))

    return files
```

**What it detects**:
```
./outputs/run_1761898976_Subject_Name/
├── abc123.pdf           → "research_report.pdf" (English)
├── abc123.docx          → "research_report.docx" (English)
├── abc123.md            → "research_report.md" (English)
├── abc123_vi.pdf        → "research_report_vi.pdf" (Vietnamese)
├── abc123_vi.docx       → "research_report_vi.docx" (Vietnamese)
└── abc123_vi.md         → "research_report_vi.md" (Vietnamese)
```

**Detection Logic**:
- ✅ Accepts: `.pdf`, `.docx`, `.md`
- ❌ Ignores: Other file types
- 🔤 Renames: UUID filenames → Friendly names
- 🌐 Detects: Language suffixes (`_vi`, `_en`, etc.)
- 📊 Sorts: Original files first, then translated

---

### 3. File Naming Logic

**UUID → Friendly Name Conversion**:

```python
def create_friendly_filename_from_uuid(uuid_filename: str) -> str:
    # Input: "abc123.pdf"
    # Output: "research_report.pdf"

    # Input: "abc123_vi.pdf"
    # Output: "research_report_vi.pdf"

    name_part, extension = uuid_filename.rsplit('.', 1)

    if '_' in name_part and len(name_part.split('_')[-1]) <= 3:
        # Has language code
        language_code = name_part.split('_')[-1]
        base_name = f"research_report_{language_code}"
    else:
        # Original file
        base_name = "research_report"

    return f"{base_name}.{extension}"
```

**Examples**:
| Original Filename | Friendly Name |
|------------------|---------------|
| `0207792d89fa4ccda371bbfadd9e4184.pdf` | `research_report.pdf` |
| `ed616d3a0a354a5f95eabf6260df2a32.docx` | `research_report.docx` |
| `2804be8a22914bc4a5f58c3ac4eed6c6_vi.md` | `research_report_vi.md` |
| `bade1fc2e1ef4486aea913acf7656d11_vi.pdf` | `research_report_vi.pdf` |

---

### 4. WebSocket Event Broadcast (main.py:299-312)

**After files are detected**, send events to frontend:

```python
if files:
    # Send event for each file discovered
    for file in files:
        file_event = create_file_generated_event(
            session_id=session_id,
            file_id=file.filename,  # Unique identifier
            filename=file.filename,  # "research_report.pdf"
            file_type=file.filename.split('.')[-1],  # "pdf"
            language="vi",  # From session language
            size_bytes=file.size
        )
        await websocket_manager.send_event(session_id, file_event)
```

**Event Structure**:
```json
{
  "event_type": "file_generated",
  "payload": {
    "file_id": "research_report.pdf",
    "filename": "research_report.pdf",
    "file_type": "pdf",
    "language": "vi",
    "size_bytes": 245680,
    "path": null
  },
  "timestamp": "2025-10-31T15:31:52.876363",
  "session_id": "e05fb2f0-639b-4ffd-aa55-3e1b9a04cc96"
}
```

---

### 5. Frontend Reception (sessionStore.ts:253-256)

**Frontend receives and stores** file information:

```typescript
function handleFileGenerated(payload: FileGeneratedPayload) {
  files.value.push(payload)  // Add to reactive array
  console.log(`📄 File generated: ${payload.filename} (${payload.size_bytes} bytes)`)
}
```

**State Update**:
```typescript
// Before event
files.value = []  // Empty

// After event
files.value = [
  {
    file_id: "research_report.pdf",
    filename: "research_report.pdf",
    file_type: "pdf",
    language: "vi",
    size_bytes: 245680
  },
  // ... more files
]
```

---

### 6. UI Display (FileExplorer.vue)

**Component reactively displays** files:

```vue
<template>
  <!-- Empty state when no files -->
  <div v-if="store.totalFilesGenerated === 0">
    📁 No files generated yet
  </div>

  <!-- File cards when files available -->
  <div v-else>
    <div v-for="file in store.files" :key="file.file_id">
      <button @click="downloadFile(file)">
        {{ file.filename }} ({{ formatFileSize(file.size_bytes) }})
      </button>
    </div>
  </div>
</template>
```

**Reactive Binding**:
```typescript
const store = useSessionStore()

// Automatically updates when store.files changes
computed(() => store.files)  // Vue reactivity
```

---

## ✅ ISSUE RESOLVED (2025-10-31)

### **The Critical Bug - FIXED**

**Problem**: Files NEVER appeared in UI despite research completing successfully
- Files created in: `./outputs/run_1761898976_Subject_Name/`
- Detection looked in: `./outputs/session-uuid/`
- System had **NEVER** successfully detected files through web dashboard

**Root Cause**: Directory name mismatch
- `ChiefEditorAgent.__init__()` always generated timestamp-based `task_id`
- Completely ignored UUID `session_id` passed from web dashboard
- Output directory created in `__init__()` before `run_research_task()` was called
- By the time session_id reached the orchestrator, directory already existed with wrong name

**Fix Applied**:
1. Added `task_id` parameter to `ChiefEditorAgent.__init__()` (orchestrator.py:63)
2. Constructor now uses provided task_id or generates timestamp as fallback (orchestrator.py:70)
3. Pass session_id to constructor from both call sites (main.py:165, main.py:324)

**Files Modified**:
- `multi_agents/agents/orchestrator.py`
- `multi_agents/main.py`

**Result**: ✅ Directories now correctly use UUID format, file detection working perfectly!

---

## 🚨 Previous Issues (Historical Reference)

### **Issue 1: Files Never Appear** ❌ **[RESOLVED]**

This was the critical bug described above. Fixed by ensuring UUID session_id is used for directory creation.

### **Issue 2: Silent File Detection** 🔇 **[PARTIALLY ADDRESSED]**

Files are now detected correctly. Future enhancement could add toast notifications when first file appears.

---

## 📋 Configuration

### File Manager Settings (file_manager.py:16-26)

```python
self.outputs_path = project_root / "outputs"  # Where CLI writes files
self.supported_extensions = ['.pdf', '.docx', '.md']  # What to detect
```

### Wait Timeout (main.py:297)

```python
files = await file_manager.wait_for_files(
    session_id,
    subject,
    timeout=30  # 30 seconds max wait time
)
```

### Poll Interval (file_manager.py:221)

```python
await asyncio.sleep(2)  # Check every 2 seconds
```

---

## 🎯 Key Takeaways

1. **Passive Detection**: Backend doesn't watch files - it **polls** the directory
2. **Fixed Interval**: Checks every **2 seconds** for up to **30 seconds**
3. **Event-Driven UI**: Frontend updates **immediately** when event received
4. **No Real-Time Watch**: Not using `inotify` or file system watchers
5. **UUID Hiding**: Internal UUIDs hidden from users via friendly names

---

## 🔧 Potential Improvements

### 1. Real-Time File Watching
```python
# Use watchdog library for instant detection
from watchdog.observers import Observer

observer = Observer()
observer.schedule(FileHandler(), session_dir, recursive=False)
observer.start()
```

### 2. Progress Feedback
```python
# Send progress event while waiting
await websocket_manager.send_event(session_id, {
    "event_type": "file_detection_status",
    "payload": {"status": "waiting", "elapsed": 5}
})
```

### 3. Toast Notifications
```typescript
// In handleFileGenerated()
if (files.value.length === 1) {
  toast.success('📄 First file ready for download!')
} else if (files.value.length === 6) {
  toast.success('🎉 All 6 files generated!')
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-31
**Maintainer**: AI Analysis
