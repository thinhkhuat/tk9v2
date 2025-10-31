---
description: Mandatory protocol for using Serena and Archon MCP servers to replace bundled Claude tools WHERE equivalents exist. Other MCP servers and unique bundled tools remain available.
---

# SERENARCHON: Smart MCP Tool Replacement Protocol

**SCOPE**: This protocol ONLY applies to bundled Claude tools that have Serena/Archon equivalents.
- ✅ Other MCP servers (supabase, github, etc.) are ALLOWED
- ✅ Bundled tools WITHOUT MCP equivalents are ALLOWED  
- ❌ Bundled tools WITH MCP equivalents are PROHIBITED

## Step 0: MANDATORY ONBOARDING (First Time Only)

**Every agent MUST complete this onboarding when first using serenarchon:**

```python
# 1. SERENA ONBOARDING - Learn proper usage
mcp__serena__check_onboarding_performed()
if not_performed:
    mcp__serena__onboarding()  # Read ALL instructions
    
# 2. READ SERENA DOCUMENTATION
mcp__serena__list_memories()
mcp__serena__read_memory("code_style_conventions")
mcp__serena__read_memory("project_overview")

# 3. ARCHON ONBOARDING - Learn proper usage  
mcp__archon__rag_search_knowledge_base(
    query="serena MCP server usage instructions",
    match_count=5
)
mcp__archon__rag_search_knowledge_base(
    query="archon MCP server best practices", 
    match_count=5
)

# 4. UNDERSTAND TOOL CAPABILITIES
mcp__archon__rag_search_code_examples(
    query="MCP server tool examples",
    match_count=3
)
```

**DO NOT PROCEED until you understand both MCP servers' methodologies.**

## Step 1: Verify MCP Servers

```python
# Both MUST be available for replacements to work
mcp__serena__list_memories()
mcp__archon__health_check()
```

If unavailable: Report and use bundled tools as fallback.

## Step 2: Tool Replacement Matrix (WHERE EQUIVALENTS EXIST)

### FILE/CODE OPERATIONS - Use Serena Instead

| Bundled Tool | Serena Replacement | When to Replace |
|--------------|-------------------|-----------------|
| `Read()` | `mcp__serena__find_symbol()` | When reading code files |
| `Write()` | `mcp__serena__replace_symbol_body()` | When writing code |
| `Edit()` | `mcp__serena__replace_symbol_body()` | When editing code |
| `Glob()` | `mcp__serena__find_file()` | When searching for files |
| `Grep()` | `mcp__serena__search_for_pattern()` | When searching in code |

### TASK OPERATIONS - Use Archon Instead

| Bundled Tool | Archon Replacement | When to Replace |
|--------------|-------------------|-----------------|
| `TodoWrite()` | `mcp__archon__manage_task()` | When managing tasks |
| `Task()` for agents | `mcp__archon__find_tasks()` | When querying tasks |

### KNOWLEDGE OPERATIONS - Use Archon Instead

| Bundled Tool | Archon Replacement | When to Replace |
|--------------|-------------------|-----------------|
| `WebSearch()` | `mcp__archon__rag_search_knowledge_base()` | When docs exist in Archon |
| `WebFetch()` | `mcp__archon__rag_search_knowledge_base()` | When content is in Archon |

## Step 3: Tools That REMAIN AVAILABLE

### Other MCP Servers (ALWAYS ALLOWED)
```python
# These are NOT affected by this protocol:
mcp__supabase__*      # Database operations
mcp__github__*        # GitHub operations
mcp__context7__*      # Documentation lookups
mcp__brave_search__*  # Web searches
mcp__acp__*          # Advanced code operations
# ... any other MCP servers
```

### Bundled Tools WITHOUT Equivalents (ALLOWED)
```python
# Use these when MCP servers don't provide alternatives:
WebFetch()  # For URLs not in Archon's knowledge base
WebSearch() # For searches outside Archon's documentation
ExitPlanMode() # No MCP equivalent
NotebookEdit() # No MCP equivalent
KillShell()    # No MCP equivalent
# ... any bundled tool without MCP equivalent
```

## Step 4: Decision Flow

```
Need to perform operation?
    ↓
Does Serena/Archon have this tool?
    ├─ YES → MUST use MCP version
    └─ NO → Can use:
           ├─ Other MCP servers
           ├─ Bundled tool
           └─ Any available option
```

## Step 5: Correct Usage Examples

### CODE READING (Serena is better for this)
```python
# ❌ WRONG: Using bundled when Serena exists
Read("file.py")  

# ✅ CORRECT: Using Serena for code
mcp__serena__get_symbols_overview("file.py")
mcp__serena__find_symbol("Class/method", include_body=True)

# ✅ ALSO CORRECT: Using ACP when needed
mcp__acp__read("config.json")  # For non-code files
```

### WEB OPERATIONS (Check Archon first)
```python
# First: Check if content exists in Archon
sources = mcp__archon__rag_get_available_sources()
result = mcp__archon__rag_search_knowledge_base("topic")

# If not found in Archon:
WebSearch("topic")  # ✅ ALLOWED - Archon doesn't have it
WebFetch("https://external-site.com")  # ✅ ALLOWED - Not in Archon
```

### TASK MANAGEMENT (Archon required)
```python
# ❌ WRONG: TodoWrite when Archon available
TodoWrite([{"content": "task"}])

# ✅ CORRECT: Using Archon
mcp__archon__manage_task("create", project_id="X", title="task")
```

## Step 6: Thinking Tools (MANDATORY USE)

After gathering information, ALWAYS use:
```python
mcp__serena__think_about_collected_information()
mcp__serena__think_about_task_adherence()
mcp__serena__think_about_whether_you_are_done()
```

## Violation Handling

**VIOLATION**: Using bundled tool when Serena/Archon equivalent exists
**RESPONSE**: 
1. Stop and report: "Used [bundled] instead of [MCP equivalent]"
2. Correct by using MCP tool
3. Continue

**NOT A VIOLATION**:
- Using other MCP servers
- Using bundled tools without MCP equivalents
- Using bundled tools when MCP servers are down

## Quick Reference

```
REPLACE (when equivalents exist):
  Code ops: Read/Write/Edit/Glob/Grep → Serena
  Task ops: TodoWrite → Archon  
  Docs: WebSearch/WebFetch → Archon (if content exists there)

KEEP USING:
  All other MCP servers
  Bundled tools without MCP equivalents
  WebSearch/WebFetch for content NOT in Archon
```

**Remember**: This protocol makes you SMARTER by using specialized tools where they exist, not RESTRICTED from legitimate operations.