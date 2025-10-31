# Phase 2 JSON Output Migration - Root Cause Analysis

## Issue Summary

**Symptom**: Agent cards in Vue frontend remained stuck at "Pending" status despite backend successfully sending WebSocket events with agent status updates.

**Root Cause**: Map key mismatch in Pinia reactive store causing O(N) lookup failure.

## Technical Analysis

### The Bug

The frontend store had a critical inconsistency:

**Writing to Map** (in `handleAgentUpdate()`):
```typescript
// Used agent_id as key (e.g., "researcher")
agents.value.set(payload.agent_id, payload)
```

**Reading from Map** (in `orderedAgents` computed):
```typescript
// Searched for agent_name in values (e.g., "Researcher")
const agentData = Array.from(agents.value.values()).find(
  a => a.agent_name === agentName  // Never matched!
)
```

### Why This Failed

1. **Key Mismatch**: Storing by `agent_id` ("researcher") but looking up by `agent_name` ("Researcher")
2. **Silent Failure**: The `.find()` always returned `undefined`, causing fallback to default "Pending" state
3. **Misleading Logs**: `console.log` in `handleAgentUpdate()` showed data arriving, making it seem like everything worked
4. **Reactivity Blind Spot**: Vue's reactivity system worked perfectly - but the computed property never found the updated data

### Data Flow Breakdown

```
Backend sends:
{
  "agent_id": "researcher",      ← lowercase ID
  "agent_name": "Researcher",    ← PascalCase name
  "status": "running"
}

Store receives → handleAgentUpdate()
  ↓
agents.value.set("researcher", payload)  ← Stored by ID
  ↓
Map: { "researcher": {...} }

UI requests → orderedAgents computed
  ↓
AGENT_PIPELINE_ORDER.map("Researcher" => ...)  ← Looking for name
  ↓
agents.value.get("researcher")  ← Key doesn't match!
  ↓
Returns: undefined → fallback to "Pending"
```

## The Fix

### Change 1: Use Consistent Key

```typescript
function handleAgentUpdate(payload: AgentUpdatePayload) {
  // Before: agents.value.set(payload.agent_id, payload)
  // After:
  agents.value.set(payload.agent_name, payload)  // ← Use agent_name
}
```

### Change 2: Optimize Lookup (O(N) → O(1))

```typescript
const orderedAgents = computed(() => {
  return AGENT_PIPELINE_ORDER.map(agentName => {
    // Before: Array.from(agents.value.values()).find(a => a.agent_name === agentName)
    // After:
    const agentData = agents.value.get(agentName)  // ← Direct O(1) lookup

    return agentData || { /* default pending state */ }
  })
})
```

## Impact Analysis

### Performance Improvement

**Before** (broken):
- Lookup: O(N) where N = number of agents (8)
- Runs on every WebSocket event for every agent in pipeline
- Total complexity: O(N²) per update

**After** (fixed):
- Lookup: O(1) constant time
- Direct hash map access
- Total complexity: O(N) per update

### Reactivity Chain Restoration

✅ **Working Flow**:
```
Backend WebSocket Event
  ↓
sessionStore.handleEvent()
  ↓
handleAgentUpdate(payload)
  ↓
agents.value.set(payload.agent_name, payload)  ← Map updated
  ↓
Vue reactivity triggers
  ↓
orderedAgents computed() re-runs
  ↓
agents.value.get("Researcher")  ← Finds data!
  ↓
Returns updated agent data
  ↓
AgentCard.vue receives new props
  ↓
UI updates to show "Running" status
```

## Lessons Learned

### 1. Reactive Store Design Principles

**Critical Rule**: When using `Map` or `Set` in reactive stores:
- **Write Key** must match **Read Key** exactly
- Use the same field as the canonical key throughout
- If UI is driven by names, use names as keys
- If UI is driven by IDs, use IDs as keys

**Best Practice**:
```typescript
// Define the canonical key upfront
const CANONICAL_KEY = 'agent_name'  // Document your choice!

// Use it consistently
function set(payload) {
  store.set(payload[CANONICAL_KEY], payload)
}

function get(name) {
  return store.get(name)  // Same key!
}
```

### 2. Debugging Reactive State Issues

**Symptoms to Watch For**:
- ✓ Backend logs show success
- ✓ Frontend logs show data arriving
- ✗ UI doesn't update
- ✗ Computed properties return default/fallback values

**Debug Strategy**:
1. **Trace the key**: What field is used to store vs retrieve?
2. **Log inside computed**: Add console.log to see what computed finds
3. **Verify reactivity**: Check if Map/Set updates trigger computed
4. **Check data types**: Ensure no type coercion issues ("1" vs 1)

### 3. The Danger of Inefficient Lookups

**Why `.find()` Failed Here**:
- It worked logically (searching values for matching name)
- But it was both slow AND buggy due to key mismatch
- The O(N) complexity masked the real issue

**When to Use Each**:
| Pattern | Use When | Time Complexity |
|---------|----------|-----------------|
| `map.get(key)` | You have the exact key | O(1) |
| `map.values().find()` | You need to search by non-key field | O(N) |
| Wrong pattern | Key mismatch between set/get | 💥 Bug |

### 4. Vue 3 + Pinia Reactive Maps

**What Worked**:
- Using `ref<Map>()` for reactive Map
- Vue's reactivity system tracking `.set()` operations
- Computed properties re-running on Map changes

**What Broke**:
- Inconsistent key usage between mutation and access
- Silently returning undefined instead of error

**Fix Pattern**:
```typescript
// ✅ Correct
const store = ref(new Map())
store.value.set(KEY, data)    // Set with KEY
const result = store.value.get(KEY)  // Get with same KEY

// ❌ Wrong (subtle bug)
const store = ref(new Map())
store.value.set(data.id, data)      // Set with id
const result = store.value.get(data.name)  // Get with name ← Bug!
```

## Testing Verification

After implementing the fix, verify:

1. **Backend logs**: `✅ Sent JSON-based agent_update: Researcher → running`
2. **Frontend console**: `🤖 Agent Researcher: running (status update)`
3. **Browser DevTools Network → WS**: See incoming JSON messages
4. **UI**: Agent cards change from "Pending" to "Running" to "Completed"
5. **Performance**: No lag or delays in UI updates

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `sessionStore.ts` | Changed Map key from `agent_id` to `agent_name` | 237, 73 |
| `sessionStore.ts` | Optimized lookup from `.find()` to `.get()` | 73 |

## Related Issues Fixed

This root cause fix also resolved:
- ✓ Progress percentages not displaying when provided
- ✓ Status changes not reflecting in UI
- ✓ Completed agents showing as pending
- ✓ Running count always showing 0
- ✓ Overall progress stuck at 0%

All of these were symptoms of the same underlying bug: the computed property never finding updated agent data.

## Prevention

**Code Review Checklist for Reactive Stores**:
- [ ] Map keys are consistent between `.set()` and `.get()`
- [ ] Lookup strategy is documented (by ID, by name, etc.)
- [ ] Computed properties use efficient O(1) lookups where possible
- [ ] Type safety enforces consistent key usage
- [ ] Tests verify reactive updates propagate to UI

**TypeScript Helper** (optional):
```typescript
// Enforce key consistency at type level
type AgentKey = AgentUpdatePayload['agent_name']

const agents = ref<Map<AgentKey, AgentUpdatePayload>>(new Map())

function set(payload: AgentUpdatePayload) {
  agents.value.set(payload.agent_name, payload)  // Type-safe!
}

function get(name: AgentKey) {
  return agents.value.get(name)  // Same key type!
}
```

## Conclusion

This bug was a textbook case of:
1. **Silent failure** - wrong key caused lookup to fail without error
2. **Performance anti-pattern** - using O(N) search instead of O(1) lookup
3. **Inconsistent abstraction** - storing by ID but retrieving by name
4. **Misleading debugging** - logs showed success at wrong layer

The fix was simple once identified: use the same field as the key throughout the reactive store's lifecycle.

---

**Date**: October 31, 2025
**Diagnosed by**: Gemini AI via /gemini-consult
**Session ID**: 1e4013ce-7cd5-44b8-843e-b93314782a81
**Fixed by**: TK9 Development Team
