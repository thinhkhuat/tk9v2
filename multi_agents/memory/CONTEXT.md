# Memory System - Feature Documentation

## Purpose

State management and persistence system for TK9's multi-agent research workflows. Manages research state, draft versioning, and session persistence using LangGraph's state management with incremental saves for long-running research tasks.

## Memory Architecture

### ResearchState TypedDict
```python
from typing import TypedDict, List, Dict, Optional

class ResearchState(TypedDict, total=False):
    # Query and configuration
    query: str
    tone: str
    language: str
    guidelines: List[str]

    # Research planning
    research_plan: List[Dict]
    methodology: str

    # Research results
    research_sections: List[Dict]
    research_data: Dict

    # Writing and publishing
    draft_report: str
    final_report: str
    published_files: Dict[str, str]

    # Translation
    translated_report: Optional[str]

    # Review and revision
    review_result: Dict
    revision_notes: List[str]

    # Metadata
    task_id: int
    output_dir: str
    errors: List[str]
```

## Key Components

### 1. Research State Management (`memory/research.py`)
**Purpose**: Immutable state container with type safety

**State Flow**:
```python
# Initial state
state = ResearchState(query="AI trends", tone="objective")

# Agent updates state
updated = {**state, "research_plan": plan}

# LangGraph merges updates
final_state = merge_states(state, updated)
```

**State Validation**:
```python
def validate_state(state: ResearchState) -> bool:
    """Ensure state has required fields"""
    required = ["query", "tone", "language"]
    return all(field in state for field in required)
```

### 2. Draft Management (`memory/draft.py` or `utils/draft_manager.py`)
**Purpose**: Version tracking and incremental saves

**Draft Structure**:
```
outputs/run_[timestamp]_[query]/
├── [uuid].md                    # Final report
├── [uuid]_vi.md                 # Translated report
└── drafts/                      # Complete history
    ├── WORKFLOW_SUMMARY.md      # Workflow execution log
    ├── 1_browsing/
    │   └── [timestamp]_sources.md
    ├── 2_planning/
    │   └── [timestamp]_plan.md
    ├── 3_research/
    │   ├── [timestamp]_section_1.md
    │   └── [timestamp]_section_2.md
    ├── 4_writing/
    │   └── [timestamp]_draft.md
    ├── 5_reviewing/
    │   └── [timestamp]_review.md
    ├── 6_revision/
    │   └── [timestamp]_revised.md
    └── 7_publishing/
        └── [timestamp]_final.md
```

**Draft Manager API**:
```python
class DraftManager:
    def save_draft(self, phase: str, content: str, metadata: Dict):
        """Save draft for specific phase"""
        path = self._get_draft_path(phase)
        self._write_with_metadata(path, content, metadata)

    def load_draft(self, phase: str) -> Optional[str]:
        """Load most recent draft for phase"""
        pass

    def list_drafts(self) -> List[Dict]:
        """List all drafts with timestamps"""
        pass

    def generate_workflow_summary(self):
        """Create workflow execution summary"""
        pass
```

### 3. Session Persistence (`memory/session.py`)
**Purpose**: Enable resumable long-running research

**Session State**:
```python
@dataclass
class SessionState:
    session_id: str
    query: str
    current_phase: str
    completed_phases: List[str]
    research_state: ResearchState
    start_time: datetime
    last_update: datetime

    def save(self):
        """Persist session to disk"""
        path = f".sessions/{self.session_id}.json"
        with open(path, 'w') as f:
            json.dump(asdict(self), f)

    @classmethod
    def load(cls, session_id: str):
        """Resume from saved session"""
        path = f".sessions/{session_id}.json"
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
```

## Integration with LangGraph

### State Updates
```python
# LangGraph automatically merges state updates
def agent_node(state: ResearchState) -> Dict:
    # Agent processes state
    result = process(state)

    # Return only updates
    return {"agent_output": result}

# LangGraph merges: new_state = {**old_state, **updates}
```

### Conditional Edges
```python
def should_revise(state: ResearchState) -> str:
    """Decide next node based on state"""
    if state.get("review_result", {}).get("needs_revision"):
        return "reviser"
    return "end"

workflow.add_conditional_edges(
    "reviewer",
    should_revise,
    {"reviser": "reviser", "end": END}
)
```

## Memory Patterns

### Pattern 1: Incremental Saves
Save state after each agent to prevent data loss:
```python
async def agent_with_checkpoint(state):
    result = await agent.run(state)

    # Save intermediate result
    draft_manager.save_draft(
        phase=agent.phase,
        content=result['output'],
        metadata={'timestamp': now(), 'agent': agent.name}
    )

    return result
```

### Pattern 2: State Composition
Build complex state from multiple sources:
```python
def compose_state(
    base_state: ResearchState,
    research_results: List[Dict],
    review: Dict
) -> ResearchState:
    return {
        **base_state,
        "research_sections": research_results,
        "review_result": review
    }
```

### Pattern 3: State Validation
Ensure state integrity between phases:
```python
def validate_transition(
    from_phase: str,
    to_phase: str,
    state: ResearchState
) -> bool:
    """Ensure required fields present for transition"""
    requirements = {
        "editor": ["query", "tone"],
        "researcher": ["research_plan"],
        "writer": ["research_sections"],
        "reviewer": ["draft_report"]
    }

    required_fields = requirements.get(to_phase, [])
    return all(field in state for field in required_fields)
```

## Development Patterns

### Adding State Fields
1. **Update TypedDict**:
   ```python
   class ResearchState(TypedDict, total=False):
       # ... existing fields
       new_field: str
   ```

2. **Update Initialization**:
   ```python
   initial_state = ResearchState(
       query=query,
       # ... existing fields
       new_field="default_value"
   )
   ```

3. **Access in Agents**:
   ```python
   def agent_run(state):
       value = state.get("new_field", "default")
   ```

### Debugging State Issues
```python
# Print state at each step
def debug_node(state):
    print(f"Current state: {json.dumps(state, indent=2)}")
    return {}  # No updates

workflow.add_node("debug", debug_node)
workflow.add_edge("agent", "debug")
```

## Performance Considerations

### Memory Usage
- **State Size**: Typically < 10 MB for full research state
- **Draft Files**: 1-5 MB per phase
- **Total**: ~50 MB for complete research with all drafts

### Disk I/O
- **Incremental Saves**: ~100ms per draft save
- **Load Time**: < 50ms to load state from disk
- **Cleanup**: Old sessions can be archived/deleted

## Common Issues

### Issue: State Not Persisting
**Symptom**: State changes lost between agents
**Solution**: Ensure agents return updates, not full state
```python
# Wrong
return state  # LangGraph expects updates only

# Correct
return {"field": value}  # LangGraph merges into state
```

### Issue: Draft Files Missing
**Symptom**: Workflow completes but no draft files
**Solution**: Ensure `write_to_files=True` in ChiefEditorAgent init

### Issue: State Type Errors
**Symptom**: TypeErrors when accessing state
**Solution**: Use type-safe accessors
```python
from agents.utils.type_safety import safe_dict_get

value = safe_dict_get(state, 'field', 'default', str)
```

## Cross-References

- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - State management integration
- **[Agent Implementations](/multi_agents/agents/CONTEXT.md)** - How agents use state
- **[Workflow Reference](/ref/workflow.md)** - State flow diagrams

---

*For state schema details, see `memory/research.py`. For draft management, see `utils/draft_manager.py`.*
