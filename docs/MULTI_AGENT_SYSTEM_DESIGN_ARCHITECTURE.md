# Multi-Agent System Design Architecture: A Comprehensive Blueprint for Intelligent Workflow Automation

## Executive Summary

This document presents a comprehensive system design architecture extracted from the Deep Research MCP multi-agent framework. The architecture demonstrates how to build sophisticated AI-powered workflows where specialized agents collaborate under orchestrated management to deliver high-quality outputs while minimizing hallucinations through systematic quality assurance mechanisms.

**Key Innovation**: The framework transforms complex workflows into a **directed graph of specialized AI agents**, each with single responsibility, coordinated by an intelligent orchestrator, with built-in quality control mechanisms that systematically eliminate AI hallucinations.

---

## Table of Contents
1. [Core Architecture Overview](#core-architecture-overview)
2. [Agent Specialization Pattern](#agent-specialization-pattern)
3. [Orchestration System Design](#orchestration-system-design)
4. [Quality Assurance & Anti-Hallucination System](#quality-assurance--anti-hallucination-system)
5. [State Management Architecture](#state-management-architecture)
6. [Communication Protocol Design](#communication-protocol-design)
7. [Multi-Provider Integration Pattern](#multi-provider-integration-pattern)
8. [Generic Framework Blueprint](#generic-framework-blueprint)
9. [Implementation Patterns](#implementation-patterns)
10. [Production Architecture Considerations](#production-architecture-considerations)

---

## Core Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                    ChiefEditorAgent (Orchestrator)                          │  │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐  │  │
│  │  │  LangGraph      │  State          │  Agent          │  Quality        │  │  │
│  │  │  Workflow       │  Management     │  Registry       │  Control        │  │  │
│  │  │  Engine         │                 │                 │                 │  │  │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AGENT EXECUTION LAYER                               │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   INPUT     │  │  PLANNING   │  │ EXECUTION   │  │ SYNTHESIS   │            │
│  │   AGENTS    │  │   AGENTS    │  │   AGENTS    │  │   AGENTS    │            │
│  │             │  │             │  │             │  │             │            │
│  │ • Browser   │  │ • Editor    │  │ • Researcher│  │ • Writer    │            │
│  │             │  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   OUTPUT    │  │   QUALITY   │  │  INTERFACE  │  │ TRANSLATION │            │
│  │   AGENTS    │  │   AGENTS    │  │   AGENTS    │  │   AGENTS    │            │
│  │             │  │             │  │             │  │             │            │
│  │ • Publisher │  │ • Reviewer  │  │ • Human     │  │ • Translator│            │
│  │             │  │ • Reviser   │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                                   │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ MULTI-      │  │  STATE      │  │ MEMORY      │  │ PROTOCOL    │            │
│  │ PROVIDER    │  │ PERSISTENCE │  │ MANAGEMENT  │  │ ADAPTERS    │            │
│  │ SYSTEM      │  │             │  │             │  │             │            │
│  │             │  │ • Redis     │  │ • Research  │  │ • MCP       │            │
│  │ • LLM       │  │ • Database  │  │ • Draft     │  │ • WebSocket │            │
│  │ • Search    │  │ • Files     │  │ • Session   │  │ • CLI       │            │
│  │ • Tools     │  │             │  │             │  │ • REST API  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Single Responsibility**: Each agent has exactly one specialized task
2. **Orchestrated Autonomy**: Agents operate independently but are coordinated centrally
3. **State-Driven Coordination**: Immutable state transitions enable traceability
4. **Quality-First Design**: Built-in review/revision cycles prevent poor outputs
5. **Provider Agnostic**: Multiple LLM/tool providers with automatic failover
6. **Protocol Flexible**: Support for CLI, WebSocket, MCP, and REST interfaces

---

## Agent Specialization Pattern

### Base Agent Architecture

```python
class BaseAgent:
    """
    Base class for all specialized agents in the system.
    Implements common patterns: initialization, state management, error handling.
    """
    
    def __init__(self, websocket=None, stream_output=None, headers=None, draft_manager=None):
        self.websocket = websocket
        self.stream_output = stream_output  
        self.headers = headers or {}
        self.draft_manager = draft_manager
        self.agent_name = self.__class__.__name__
        
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standard execution pattern:
        1. Validate input
        2. Perform specialized task
        3. Update state
        4. Stream progress
        5. Save draft
        """
        try:
            # Input validation
            await self._validate_input(state)
            
            # Core agent logic
            result = await self._perform_task(state)
            
            # State update
            updated_state = self._update_state(state, result)
            
            # Progress streaming
            await self._stream_progress(result)
            
            # Draft persistence
            await self._save_draft(result)
            
            return updated_state
            
        except Exception as e:
            return await self._handle_error(state, e)
    
    async def _perform_task(self, state: Dict[str, Any]) -> Any:
        """Override in specialized agents"""
        raise NotImplementedError
```

### Specialized Agent Types

#### 1. **Input Agents**
Responsible for data acquisition and initial processing.

```python
class BrowserAgent(BaseAgent):
    """
    Specialized for initial web research and data gathering.
    Single Responsibility: Collect initial research data.
    """
    
    async def _perform_task(self, state):
        # Use gpt-researcher for initial exploration
        query = state['task']['query']
        
        # Initialize researcher with current provider configuration
        researcher = self._get_researcher_instance(query)
        
        # Conduct initial research
        initial_research = await researcher.conduct_research()
        
        return {
            'initial_research': initial_research,
            'sources': researcher.get_sources(),
            'research_data': researcher.get_research_data()
        }
```

#### 2. **Planning Agents**
Create structured plans and workflows from raw data.

```python
class EditorAgent(BaseAgent):
    """
    Specialized for research planning and structure creation.
    Single Responsibility: Create research outline and manage sub-workflows.
    """
    
    async def _perform_task(self, state):
        # Generate research outline based on initial research
        outline = await self._generate_outline(state['initial_research'])
        
        # Create sections for parallel research
        sections = self._create_sections(outline, state['task'])
        
        # Execute parallel research with review/revision loop
        research_data = await self._execute_parallel_research(sections, state)
        
        return {
            'sections': sections,
            'research_data': research_data,
            'outline': outline
        }
    
    async def _execute_parallel_research(self, sections, state):
        """
        Implements sub-workflow for parallel research with quality control.
        Each section goes through: Research → Review → Revise (if needed)
        """
        research_results = []
        
        for section in sections:
            # Create sub-workflow for this section
            section_workflow = self._create_section_workflow()
            
            # Execute with review/revision loop (max 3 iterations)
            section_result = await self._execute_with_quality_loop(
                section_workflow, section, state, max_revisions=3
            )
            
            research_results.append(section_result)
        
        return research_results
```

#### 3. **Execution Agents**
Perform core domain-specific work.

```python
class ResearcherAgent(BaseAgent):
    """
    Specialized for conducting detailed research on specific topics.
    Single Responsibility: Deep research execution.
    """
    
    async def _perform_task(self, state):
        if 'sections' in state:
            # Depth research for specific section
            return await self._run_depth_research(state)
        else:
            # Initial research
            return await self._run_initial_research(state)
    
    async def _run_depth_research(self, state):
        """
        Conduct detailed research on a specific section.
        Uses gpt-researcher with multi-provider support.
        """
        section = state.get('section')
        query = f"{state['task']['query']} - {section}"
        
        # Get configured researcher instance
        researcher = self._get_researcher_instance(
            query=query,
            report_type="research_report",
            config=self._get_provider_config()
        )
        
        # Execute research with current provider
        research_result = await researcher.conduct_research()
        
        return {
            'content': research_result,
            'sources': researcher.get_sources(),
            'section': section
        }
```

#### 4. **Synthesis Agents**
Combine and refine multiple outputs into cohesive results.

```python
class WriterAgent(BaseAgent):
    """
    Specialized for compiling research into final reports.
    Single Responsibility: Synthesize research into cohesive report.
    """
    
    async def _perform_task(self, state):
        # Extract research data
        research_data = state.get('research_data', [])
        
        # Generate report components
        report_components = await self._generate_report_components(research_data, state)
        
        # Compile final report
        final_report = await self._compile_final_report(report_components, state)
        
        return {
            'report': final_report,
            'title': report_components['title'],
            'introduction': report_components['introduction'],
            'conclusion': report_components['conclusion'],
            'table_of_contents': report_components['table_of_contents']
        }
    
    async def _compile_final_report(self, components, state):
        """
        Uses LLM with intelligent fallback for JSON parsing failures.
        Implements multiple extraction strategies.
        """
        try:
            # Primary: JSON response parsing
            response = await self._llm_generate(prompt, response_format="json")
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: Pattern-based extraction
            return await self._extract_with_patterns(response)
```

#### 5. **Quality Assurance Agents**
Ensure outputs meet quality standards and eliminate hallucinations.

```python
class ReviewerAgent(BaseAgent):
    """
    Specialized for quality review and validation.
    Single Responsibility: Review outputs against quality criteria.
    """
    
    async def _perform_task(self, state):
        draft = state.get('draft', {})
        
        # Determine review type
        if state.get('is_translation_review'):
            return await self._review_translation(draft, state)
        else:
            return await self._review_content(draft, state)
    
    async def _review_content(self, draft, state):
        """
        Multi-dimensional quality review:
        - Content accuracy
        - Completeness 
        - Format compliance
        - Source verification
        """
        review_criteria = {
            'accuracy': self._check_accuracy(draft),
            'completeness': self._check_completeness(draft, state),
            'format': self._check_format_compliance(draft),
            'sources': self._verify_sources(draft)
        }
        
        # Calculate composite quality score
        quality_score = self._calculate_quality_score(review_criteria)
        
        # Determine if revision is needed
        needs_revision = quality_score < state.get('quality_threshold', 0.8)
        
        return {
            'review': self._generate_review_feedback(review_criteria),
            'approved': not needs_revision,
            'quality_score': quality_score,
            'criteria_scores': review_criteria
        }

class ReviserAgent(BaseAgent):
    """
    Specialized for implementing review feedback.
    Single Responsibility: Revise content based on review feedback.
    """
    
    async def _perform_task(self, state):
        # Extract content and feedback
        draft = state.get('draft')
        review_feedback = state.get('review')
        
        # Implement intelligent content extraction
        revised_content = await self._extract_content_intelligently(
            draft, review_feedback, state
        )
        
        return {
            'revised_content': revised_content,
            'revision_notes': review_feedback,
            'revision_count': state.get('revision_count', 0) + 1
        }
    
    async def _extract_content_intelligently(self, raw_response, feedback, state):
        """
        Multi-strategy content extraction to handle LLM response variations:
        1. JSON embedded extraction
        2. Enhanced pattern-based extraction  
        3. Content similarity-based extraction
        4. Smart content splitting
        5. Formatting preservation fallback
        """
        strategies = [
            self._strategy_json_embedded,
            self._strategy_pattern_based,
            self._strategy_similarity_based,
            self._strategy_content_splitting,
            self._strategy_formatting_preservation
        ]
        
        for strategy in strategies:
            try:
                result = await strategy(raw_response, feedback, state)
                if self._validate_extraction(result):
                    return result
            except Exception:
                continue
        
        # Final fallback
        return self._fallback_extraction(raw_response)
```

#### 6. **Output Agents**
Format and deliver final results in required formats.

```python
class PublisherAgent(BaseAgent):
    """
    Specialized for multi-format output generation.
    Single Responsibility: Generate and format final outputs.
    """
    
    async def _perform_task(self, state):
        report = state.get('report')
        
        # Generate multiple output formats
        outputs = {}
        
        # Markdown (primary format)
        outputs['markdown'] = await self._generate_markdown(report)
        
        # PDF (formatted report)
        if 'pdf' in state['task'].get('publish_formats', []):
            outputs['pdf'] = await self._generate_pdf(report)
        
        # DOCX (editable document)
        if 'docx' in state['task'].get('publish_formats', []):
            outputs['docx'] = await self._generate_docx(report)
        
        return {
            'outputs': outputs,
            'published': True,
            'formats': list(outputs.keys())
        }
```

#### 7. **Translation Agents**
Handle multi-language support with quality preservation.

```python
class TranslatorAgent(BaseAgent):
    """
    Specialized for content translation with format preservation.
    Single Responsibility: Translate content while preserving formatting.
    """
    
    async def _perform_task(self, state):
        # Get target language
        target_language = state['task'].get('language', 'en')
        
        if target_language == 'en':
            return state  # No translation needed
        
        # Translate with multiple endpoint failover
        translated_content = await self._translate_with_failover(
            content=state['report'],
            target_language=target_language
        )
        
        return {
            'translated_content': translated_content,
            'target_language': target_language,
            'translation_completed': True
        }
    
    async def _translate_with_failover(self, content, target_language):
        """
        Multiple translation endpoint support with automatic failover.
        Preserves markdown formatting (no restoration logic needed).
        """
        endpoints = self._get_translation_endpoints()
        
        for endpoint in endpoints:
            try:
                result = await endpoint.translate(content, target_language)
                if self._validate_translation(result):
                    return result
            except Exception as e:
                self._log_translation_error(endpoint, e)
                continue
        
        raise TranslationError("All translation endpoints failed")
```

---

## Orchestration System Design

### Orchestrator Architecture

```python
class ChiefEditorAgent:
    """
    Master orchestrator that manages the entire workflow.
    Implements LangGraph-based state machine with conditional routing.
    """
    
    def __init__(self, task, websocket=None, stream_output=None, tone=None, headers=None, write_to_files=False):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.tone = tone or Tone.Objective
        self.headers = headers or {}
        self.write_to_files = write_to_files
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Configure providers
        self.provider_config = self._setup_provider_configuration()
        
        # Create workflow
        self.workflow = self._create_workflow_graph()
    
    def _create_workflow_graph(self):
        """
        Creates LangGraph workflow with conditional routing and quality loops.
        """
        workflow = StateGraph(ResearchState)
        
        # Add agent nodes
        workflow.add_node("browser", self.agents['browser'].run_initial_research)
        workflow.add_node("planner", self.agents['planner'].plan_research)
        workflow.add_node("human_feedback", self.agents['human'].get_human_feedback)
        workflow.add_node("researcher", self.agents['researcher'].run_parallel_research)
        workflow.add_node("writer", self.agents['writer'].write_report)
        workflow.add_node("publisher", self.agents['publisher'].publish_report)
        workflow.add_node("translator", self.agents['translator'].translate_report)
        workflow.add_node("reviewer", self.agents['reviewer'].review_content)
        workflow.add_node("reviser", self.agents['reviser'].revise_content)
        
        # Define workflow edges
        workflow.add_edge("browser", "planner")
        
        # Conditional human feedback
        workflow.add_conditional_edges(
            "planner",
            self._should_get_human_feedback,
            {
                "human_feedback": "human_feedback",
                "researcher": "researcher"
            }
        )
        workflow.add_edge("human_feedback", "researcher")
        
        # Main workflow
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "publisher")
        
        # Translation workflow (conditional)
        workflow.add_conditional_edges(
            "publisher",
            self._should_translate,
            {
                "translator": "translator",
                "end": END
            }
        )
        
        # Quality assurance loop for translation
        workflow.add_edge("translator", "reviewer")
        workflow.add_conditional_edges(
            "reviewer",
            self._should_revise,
            {
                "reviser": "reviser",
                "end": END
            }
        )
        workflow.add_edge("reviser", "reviewer")  # Re-review after revision
        
        # Set entry and exit points
        workflow.set_entry_point("browser")
        workflow.set_finish_point("end")
        
        return workflow.compile()
    
    def _should_get_human_feedback(self, state):
        """Conditional routing for human feedback"""
        return "human_feedback" if state.get('include_human_feedback') else "researcher"
    
    def _should_translate(self, state):
        """Conditional routing for translation"""
        target_lang = state['task'].get('language', 'en')
        return "translator" if target_lang != 'en' else "end"
    
    def _should_revise(self, state):
        """Quality loop condition"""
        review = state.get('review')
        max_revisions = 3
        current_revisions = state.get('revision_count', 0)
        
        if not review:
            return "end"
        
        needs_revision = not review.get('approved', True)
        under_revision_limit = current_revisions < max_revisions
        
        return "reviser" if (needs_revision and under_revision_limit) else "end"
```

### Workflow Execution Patterns

#### 1. **Sequential Processing**
```
Browser → Editor → Researcher → Writer → Publisher
```

#### 2. **Parallel Processing with Quality Loops**
```
                ┌─ Researcher1 ─┐
Editor ─ Plan ─ ├─ Researcher2 ─┤ ─ Merge ─ Writer
                └─ Researcher3 ─┘

Each Researcher: Research → Review → Revise (if needed) → Accept
```

#### 3. **Conditional Branching**
```
Publisher ─ Check Language ─┬─ EN ────────────→ END
                           └─ Non-EN ─ Translate ─ Review ─ END
```

#### 4. **Quality Assurance Loops**
```
Agent Output ─ Reviewer ─┬─ Approved ────→ Next Stage
                         └─ Rejected ─ Reviser ─┘ (back to Reviewer)
                                        ↑
                                   Max 3 iterations
```

---

## Quality Assurance & Anti-Hallucination System

### Hallucination Prevention Architecture

The system implements multiple layers of hallucination prevention:

#### Layer 1: **Source Verification**
```python
class SourceVerificationSystem:
    """
    Verifies all claims against original sources.
    Prevents fabricated information.
    """
    
    def verify_claims(self, content, sources):
        claims = self._extract_claims(content)
        verified_claims = []
        
        for claim in claims:
            verification_score = self._verify_against_sources(claim, sources)
            if verification_score > 0.8:
                verified_claims.append(claim)
            else:
                self._flag_unverified_claim(claim)
        
        return verified_claims
```

#### Layer 2: **Cross-Agent Validation**
```python
class CrossAgentValidation:
    """
    Multiple agents validate the same output.
    Consensus mechanism prevents individual agent hallucinations.
    """
    
    async def validate_with_consensus(self, output, validator_agents):
        validations = []
        
        for agent in validator_agents:
            validation = await agent.validate(output)
            validations.append(validation)
        
        consensus_score = self._calculate_consensus(validations)
        return consensus_score > 0.7  # Require 70% consensus
```

#### Layer 3: **Confidence Scoring**
```python
class ConfidenceTracker:
    """
    Tracks confidence scores for all outputs.
    Low confidence triggers additional review.
    """
    
    def track_confidence(self, agent_output):
        confidence_indicators = {
            'source_availability': self._check_sources(agent_output),
            'response_consistency': self._check_consistency(agent_output),
            'fact_verifiability': self._check_facts(agent_output)
        }
        
        composite_confidence = self._calculate_composite_score(confidence_indicators)
        
        if composite_confidence < 0.6:
            self._trigger_additional_review(agent_output)
        
        return composite_confidence
```

#### Layer 4: **Human-in-the-Loop Validation**
```python
class HumanValidationGate:
    """
    Human verification for critical decisions.
    Final safeguard against AI hallucinations.
    """
    
    async def get_human_validation(self, content, confidence_score):
        if confidence_score < 0.7:  # Low confidence
            human_input = await self._request_human_review(content)
            return self._process_human_feedback(human_input)
        
        return True  # High confidence, skip human review
```

### Quality Loop Implementation

```python
class QualityAssuranceLoop:
    """
    Implements iterative quality improvement with convergence detection.
    """
    
    def __init__(self, max_iterations=3, quality_threshold=0.8):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
    
    async def ensure_quality(self, content, reviewer, reviser):
        iteration = 0
        current_content = content
        
        while iteration < self.max_iterations:
            # Review current content
            review = await reviewer.review(current_content)
            
            # Check if quality threshold met
            if review.quality_score >= self.quality_threshold:
                return current_content
            
            # Apply revisions
            current_content = await reviser.revise(
                current_content, review.feedback
            )
            
            iteration += 1
        
        # Final quality check
        final_review = await reviewer.review(current_content)
        
        if final_review.quality_score < self.quality_threshold:
            self._log_quality_warning(current_content, final_review)
        
        return current_content
```

---

## State Management Architecture

### State Schema Design

```python
class ResearchState(TypedDict):
    """
    Immutable state container for workflow execution.
    Ensures traceability and debugging capability.
    """
    
    # Core task information
    task: dict
    
    # Research pipeline state
    initial_research: str
    sections: List[str]
    research_data: List[dict]
    
    # Content state
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[dict]
    report: str
    
    # Quality tracking
    human_feedback: str
    revision_count: int
    quality_scores: Dict[str, float]
    
    # Translation state
    target_language: str
    translated_content: str
    
    # Workflow metadata
    workflow_id: str
    current_agent: str
    completion_status: str

class DraftState(TypedDict):
    """
    State container for review/revision cycles.
    """
    task: dict
    topic: str
    draft: dict
    review: str
    revision_notes: str
    revision_count: int
```

### State Transition Management

```python
class StateManager:
    """
    Manages immutable state transitions with full traceability.
    """
    
    def __init__(self):
        self.state_history = []
        self.transition_log = []
    
    def transition_state(self, current_state: ResearchState, agent: str, output: dict) -> ResearchState:
        """
        Create new state from agent output.
        Maintains immutability and traceability.
        """
        # Create new state (immutable)
        new_state = deepcopy(current_state)
        
        # Update state with agent output
        new_state.update(output)
        new_state['current_agent'] = agent
        new_state['last_updated'] = datetime.now().isoformat()
        
        # Log transition
        self._log_transition(current_state, new_state, agent, output)
        
        # Store state history
        self.state_history.append(new_state)
        
        return new_state
    
    def _log_transition(self, old_state, new_state, agent, output):
        """Log state transition for debugging and auditing"""
        transition = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent,
            'changes': self._diff_states(old_state, new_state),
            'output_size': len(str(output))
        }
        self.transition_log.append(transition)
```

### Memory Management System

```python
class DraftManager:
    """
    Manages all intermediate outputs and drafts.
    Provides full workflow history and debugging capability.
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.draft_history = {}
        self.metadata = {}
    
    async def save_draft(self, agent_name: str, content: Any, metadata: dict = None):
        """Save agent output with timestamp and metadata"""
        timestamp = datetime.now().isoformat()
        draft_id = f"{agent_name}_{timestamp}"
        
        draft_path = self.base_path / "drafts" / f"{draft_id}.json"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        
        draft_data = {
            'agent': agent_name,
            'timestamp': timestamp,
            'content': content,
            'metadata': metadata or {}
        }
        
        # Save to disk
        with open(draft_path, 'w') as f:
            json.dump(draft_data, f, indent=2, default=str)
        
        # Update history
        if agent_name not in self.draft_history:
            self.draft_history[agent_name] = []
        self.draft_history[agent_name].append(draft_id)
    
    def get_draft_history(self, agent_name: str) -> List[dict]:
        """Retrieve complete draft history for an agent"""
        if agent_name not in self.draft_history:
            return []
        
        history = []
        for draft_id in self.draft_history[agent_name]:
            draft_path = self.base_path / "drafts" / f"{draft_id}.json"
            if draft_path.exists():
                with open(draft_path, 'r') as f:
                    history.append(json.load(f))
        
        return history
```

---

## Communication Protocol Design

### Multi-Protocol Support Architecture

```python
class CommunicationProtocolManager:
    """
    Manages multiple communication protocols for different use cases.
    """
    
    def __init__(self):
        self.protocols = {
            'websocket': WebSocketProtocol(),
            'cli': CLIProtocol(),
            'mcp': MCPProtocol(),
            'rest': RESTProtocol()
        }
    
    async def broadcast_progress(self, message: dict):
        """Broadcast progress to all active protocols"""
        for protocol in self.protocols.values():
            if protocol.is_active():
                await protocol.send_progress(message)
```

#### WebSocket Protocol
```python
class WebSocketProtocol:
    """Real-time bidirectional communication for interactive applications"""
    
    async def send_progress(self, websocket, agent: str, progress: dict):
        message = {
            'type': 'agent_progress',
            'agent': agent,
            'data': progress,
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send_json(message)
    
    async def receive_feedback(self, websocket) -> dict:
        message = await websocket.receive_json()
        return self._parse_feedback(message)
```

#### MCP Protocol
```python
class MCPProtocol:
    """Model Context Protocol for AI assistant integration"""
    
    async def expose_tool(self, tool_name: str, handler: Callable):
        """Expose agent capability as MCP tool"""
        @tool(name=tool_name)
        async def mcp_handler(query: str, **kwargs):
            result = await handler(query, **kwargs)
            return self._format_mcp_response(result)
        
        return mcp_handler
```

#### CLI Protocol
```python
class CLIProtocol:
    """Command-line interface for batch and interactive use"""
    
    def display_progress(self, agent: str, status: str, progress: float):
        """Display progress with visual indicators"""
        bar_length = 50
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f'\r{agent}: |{bar}| {progress:.1%} {status}', end='', flush=True)
    
    def get_user_input(self, prompt: str) -> str:
        """Get user input with prompt"""
        return input(f"\n{prompt}: ")
```

### Event System Architecture

```python
class EventBus:
    """
    Event-driven architecture for loose coupling between components.
    """
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_history = []
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to specific event types"""
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        self.event_history.append(event)
        
        for handler in self.subscribers[event.type]:
            try:
                await handler(event)
            except Exception as e:
                self._log_handler_error(handler, event, e)

class Event:
    def __init__(self, event_type: str, data: dict, source: str):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()
        self.id = str(uuid.uuid4())
```

---

## Multi-Provider Integration Pattern

### Provider Abstraction Layer

```python
class ProviderManager:
    """
    Manages multiple LLM and tool providers with automatic failover.
    """
    
    def __init__(self, config: Dict):
        self.primary_providers = self._initialize_primary_providers(config)
        self.fallback_providers = self._initialize_fallback_providers(config)
        self.provider_health = {}
    
    async def execute_llm_request(self, prompt: str, **kwargs) -> str:
        """Execute LLM request with automatic failover"""
        providers = [self.primary_providers['llm']] + self.fallback_providers.get('llm', [])
        
        for provider in providers:
            try:
                if self._is_provider_healthy(provider):
                    result = await provider.generate(prompt, **kwargs)
                    self._update_provider_health(provider, True)
                    return result
            except Exception as e:
                self._update_provider_health(provider, False)
                self._log_provider_error(provider, e)
                continue
        
        raise ProviderExhaustionError("All LLM providers failed")
    
    async def execute_search_request(self, query: str, **kwargs) -> List[dict]:
        """Execute search request with automatic failover"""
        providers = [self.primary_providers['search']] + self.fallback_providers.get('search', [])
        
        for provider in providers:
            try:
                if self._is_provider_healthy(provider):
                    results = await provider.search(query, **kwargs)
                    self._update_provider_health(provider, True)
                    return results
            except Exception as e:
                self._update_provider_health(provider, False)
                self._log_provider_error(provider, e)
                continue
        
        raise ProviderExhaustionError("All search providers failed")
```

### BRAVE Search Integration Pattern

```python
class BRAVESearchIntegration:
    """
    Example of custom provider integration using module patching.
    Demonstrates how to integrate providers not natively supported by gpt-researcher.
    """
    
    @staticmethod
    def setup_brave_integration():
        """
        Early integration setup before gpt-researcher imports.
        Uses module patching for seamless integration.
        """
        # Set environment variables
        os.environ['RETRIEVER'] = 'custom'
        os.environ['RETRIEVER_ENDPOINT'] = 'https://brave-local-provider.local'
        
        # Patch gpt-researcher modules
        import gpt_researcher.retrievers.custom.custom as custom_module
        custom_module.CustomRetriever = BRAVECustomRetriever
        
        # Patch main module registry
        import gpt_researcher.retrievers
        gpt_researcher.retrievers.CustomRetriever = BRAVECustomRetriever

class BRAVECustomRetriever:
    """
    Custom retriever that converts BRAVE API responses to gpt-researcher format.
    """
    
    def __init__(self, query: str):
        self.query = query
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
    
    async def get_search_results(self, max_results: int = 10) -> List[dict]:
        """
        Get search results from BRAVE API and convert to expected format.
        """
        brave_results = await self._call_brave_api(self.query, max_results)
        
        # Convert to gpt-researcher format
        converted_results = []
        for result in brave_results.get('web', {}).get('results', []):
            converted_results.append({
                'title': result.get('title', ''),
                'href': result.get('url', ''),
                'body': result.get('description', '')
            })
        
        return converted_results
    
    async def _call_brave_api(self, query: str, count: int) -> dict:
        """Call BRAVE Search API with proper authentication and parameters"""
        url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.brave_api_key
        }
        
        params = {
            'q': query,
            'count': str(count),
            'search_lang': 'en',
            'country': 'US',
            'safesearch': 'moderate',
            'textDecorations': 'false',
            'spellcheck': 'true'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise BRAVEAPIError(f"API request failed: {response.status}")
```

---

## Generic Framework Blueprint

### Universal Workflow Template

```python
class GenericWorkflowFramework:
    """
    Generic framework that can be adapted to any domain.
    Provides standard patterns for multi-agent workflow creation.
    """
    
    def __init__(self, domain_config: dict):
        self.domain = domain_config['domain']
        self.agents = self._create_domain_agents(domain_config['agents'])
        self.workflow = self._create_domain_workflow(domain_config['workflow'])
        self.quality_standards = domain_config.get('quality_standards', {})
    
    def _create_domain_workflow(self, workflow_config: dict) -> StateGraph:
        """
        Create workflow from configuration.
        Supports any domain by following the pattern.
        """
        workflow = StateGraph(self._create_state_schema(workflow_config['state']))
        
        # Add agent nodes
        for agent_name, agent in self.agents.items():
            workflow.add_node(agent_name, agent.execute)
        
        # Add edges from configuration
        for edge in workflow_config['edges']:
            if edge.get('conditional'):
                workflow.add_conditional_edges(
                    edge['from'],
                    self._create_condition_function(edge['condition']),
                    edge['targets']
                )
            else:
                workflow.add_edge(edge['from'], edge['to'])
        
        # Set entry and exit points
        workflow.set_entry_point(workflow_config['entry_point'])
        workflow.set_finish_point(workflow_config['exit_point'])
        
        return workflow.compile()
```

### Domain Adaptation Pattern

```yaml
# Example: Document Processing Workflow
domain: "document_processing"
description: "Multi-agent document analysis and summarization"

agents:
  document_reader:
    type: "InputAgent"
    responsibility: "Read and parse documents"
    capabilities: ["pdf_parsing", "text_extraction", "metadata_extraction"]
    
  content_analyzer:
    type: "AnalysisAgent"
    responsibility: "Analyze document content and structure"
    capabilities: ["content_analysis", "structure_detection", "topic_extraction"]
    
  summary_generator:
    type: "SynthesisAgent"
    responsibility: "Generate document summaries"
    capabilities: ["summarization", "key_point_extraction", "abstract_generation"]
    
  quality_reviewer:
    type: "QualityAgent"
    responsibility: "Review summary quality"
    capabilities: ["accuracy_check", "completeness_check", "clarity_check"]
    
  format_publisher:
    type: "OutputAgent"
    responsibility: "Publish in required formats"
    capabilities: ["multi_format_output", "template_application", "style_formatting"]

workflow:
  entry_point: "document_reader"
  exit_point: "format_publisher"
  
  edges:
    - from: "document_reader"
      to: "content_analyzer"
      
    - from: "content_analyzer"
      to: "summary_generator"
      
    - from: "summary_generator"
      to: "quality_reviewer"
      
    - from: "quality_reviewer"
      to: "format_publisher"
      condition: "approved"
      conditional: true
      targets:
        approved: "format_publisher"
        rejected: "summary_generator"

quality_standards:
  accuracy_threshold: 0.9
  completeness_threshold: 0.85
  max_revisions: 3
```

### Agent Template System

```python
class AgentTemplate:
    """
    Template for creating domain-specific agents.
    Provides standard structure while allowing customization.
    """
    
    @staticmethod
    def create_input_agent(domain: str, capabilities: List[str]) -> type:
        """Create input agent for specific domain"""
        
        class DomainInputAgent(BaseAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.domain = domain
                self.capabilities = capabilities
            
            async def _perform_task(self, state):
                # Domain-specific input processing
                input_data = await self._gather_domain_input(state)
                processed_data = await self._process_domain_input(input_data)
                
                return {
                    f'{domain}_input': processed_data,
                    'input_metadata': self._extract_metadata(input_data)
                }
            
            async def _gather_domain_input(self, state):
                # Override in domain implementation
                raise NotImplementedError
            
            async def _process_domain_input(self, data):
                # Override in domain implementation
                raise NotImplementedError
        
        return DomainInputAgent
    
    @staticmethod
    def create_quality_agent(domain: str, criteria: Dict[str, float]) -> type:
        """Create quality agent for specific domain"""
        
        class DomainQualityAgent(BaseAgent):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.domain = domain
                self.quality_criteria = criteria
            
            async def _perform_task(self, state):
                content = state.get(f'{domain}_content')
                
                # Evaluate against domain criteria
                quality_scores = {}
                for criterion, threshold in self.quality_criteria.items():
                    score = await self._evaluate_criterion(content, criterion)
                    quality_scores[criterion] = score
                
                # Calculate overall quality
                overall_quality = sum(quality_scores.values()) / len(quality_scores)
                approved = overall_quality >= min(self.quality_criteria.values())
                
                return {
                    'quality_scores': quality_scores,
                    'overall_quality': overall_quality,
                    'approved': approved,
                    'feedback': self._generate_feedback(quality_scores) if not approved else None
                }
            
            async def _evaluate_criterion(self, content, criterion):
                # Override in domain implementation
                raise NotImplementedError
        
        return DomainQualityAgent
```

### Configuration-Driven Workflow Creation

```python
class WorkflowBuilder:
    """
    Builds workflows from configuration files.
    Enables rapid prototyping of new multi-agent systems.
    """
    
    @staticmethod
    def from_config_file(config_path: str) -> GenericWorkflowFramework:
        """Create workflow from YAML/JSON configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate configuration
        WorkflowBuilder._validate_config(config)
        
        # Create framework instance
        return GenericWorkflowFramework(config)
    
    @staticmethod
    def _validate_config(config: dict):
        """Validate workflow configuration"""
        required_sections = ['domain', 'agents', 'workflow']
        
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required section: {section}")
        
        # Validate agent references in workflow
        agent_names = set(config['agents'].keys())
        workflow_agents = set()
        
        for edge in config['workflow']['edges']:
            workflow_agents.update([edge['from'], edge['to']])
        
        undefined_agents = workflow_agents - agent_names
        if undefined_agents:
            raise ConfigurationError(f"Undefined agents in workflow: {undefined_agents}")
```

---

## Implementation Patterns

### Getting Started Template

```python
# 1. Define your domain workflow
def create_my_workflow():
    """
    Step-by-step guide to creating a new multi-agent workflow.
    """
    
    # Step 1: Identify workflow stages
    stages = [
        "input_collection",    # Gather initial data
        "analysis",           # Analyze and process data  
        "decision_making",    # Make intelligent decisions
        "action_execution",   # Execute decided actions
        "result_formatting"   # Format and deliver results
    ]
    
    # Step 2: Map agents to stages (one agent per stage)
    agent_mapping = {
        "input_collection": DataCollectorAgent,
        "analysis": DataAnalyzerAgent,
        "decision_making": DecisionMakerAgent,
        "action_execution": ActionExecutorAgent,
        "result_formatting": ResultFormatterAgent
    }
    
    # Step 3: Add quality control
    quality_agents = {
        "reviewer": OutputReviewerAgent,
        "reviser": OutputReviserAgent
    }
    
    # Step 4: Define quality standards
    quality_standards = {
        "accuracy": 0.95,
        "completeness": 0.90,
        "format_compliance": 0.85
    }
    
    # Step 5: Create orchestrator
    orchestrator = WorkflowOrchestrator(
        agents=agent_mapping,
        quality_agents=quality_agents,
        quality_standards=quality_standards
    )
    
    return orchestrator

# 2. Implement your specialized agents
class DataCollectorAgent(BaseAgent):
    """Example: Agent specialized for data collection"""
    
    async def _perform_task(self, state):
        # Your domain-specific data collection logic
        data_sources = state.get('data_sources', [])
        collected_data = []
        
        for source in data_sources:
            data = await self._collect_from_source(source)
            collected_data.append(data)
        
        return {
            'collected_data': collected_data,
            'collection_metadata': {
                'source_count': len(data_sources),
                'total_records': sum(len(d) for d in collected_data)
            }
        }
    
    async def _collect_from_source(self, source):
        # Implement your data collection logic
        pass

class DataAnalyzerAgent(BaseAgent):
    """Example: Agent specialized for data analysis"""
    
    async def _perform_task(self, state):
        data = state.get('collected_data', [])
        
        # Your domain-specific analysis logic
        analysis_results = await self._analyze_data(data)
        insights = await self._extract_insights(analysis_results)
        
        return {
            'analysis_results': analysis_results,
            'insights': insights,
            'analysis_metadata': {
                'data_points_analyzed': len(data),
                'insights_found': len(insights)
            }
        }
    
    async def _analyze_data(self, data):
        # Implement your analysis logic
        pass
    
    async def _extract_insights(self, results):
        # Implement insight extraction
        pass

# 3. Configure and run your workflow
async def run_my_workflow(input_data):
    orchestrator = create_my_workflow()
    
    initial_state = {
        'task': input_data,
        'workflow_id': str(uuid.uuid4()),
        'quality_standards': orchestrator.quality_standards
    }
    
    result = await orchestrator.execute(initial_state)
    return result
```

### Quality Integration Pattern

```python
class QualityIntegratedWorkflow:
    """
    Pattern for integrating quality assurance into any workflow.
    """
    
    def __init__(self, base_workflow: StateGraph, quality_config: dict):
        self.base_workflow = base_workflow
        self.quality_config = quality_config
        self.enhanced_workflow = self._add_quality_controls()
    
    def _add_quality_controls(self) -> StateGraph:
        """Add quality controls to existing workflow"""
        
        # Create enhanced workflow
        enhanced = StateGraph(self.base_workflow.state_schema)
        
        # Copy base nodes
        for node_name, node_func in self.base_workflow.nodes.items():
            enhanced.add_node(node_name, node_func)
        
        # Add quality nodes for each critical stage
        for stage in self.quality_config.get('critical_stages', []):
            reviewer_node = f"{stage}_reviewer"
            reviser_node = f"{stage}_reviser"
            
            enhanced.add_node(reviewer_node, self._create_stage_reviewer(stage))
            enhanced.add_node(reviser_node, self._create_stage_reviser(stage))
        
        # Modify edges to include quality loops
        self._add_quality_edges(enhanced)
        
        return enhanced.compile()
    
    def _create_stage_reviewer(self, stage: str) -> Callable:
        """Create reviewer for specific stage"""
        
        async def stage_reviewer(state):
            content = state.get(f'{stage}_output')
            criteria = self.quality_config['stages'][stage]['criteria']
            
            reviewer = QualityReviewerAgent(criteria)
            review_result = await reviewer.review(content)
            
            return {
                f'{stage}_review': review_result,
                'needs_revision': not review_result.get('approved', True)
            }
        
        return stage_reviewer
    
    def _create_stage_reviser(self, stage: str) -> Callable:
        """Create reviser for specific stage"""
        
        async def stage_reviser(state):
            content = state.get(f'{stage}_output')
            review = state.get(f'{stage}_review')
            
            reviser = QualityReviserAgent()
            revised_content = await reviser.revise(content, review)
            
            return {
                f'{stage}_output': revised_content,
                f'{stage}_revision_count': state.get(f'{stage}_revision_count', 0) + 1
            }
        
        return stage_reviser
```

---

## Production Architecture Considerations

### Scalability Architecture

```python
class ScalableMultiAgentSystem:
    """
    Production-ready architecture for large-scale deployments.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.worker_pool = WorkerPool(size=config.get('worker_pool_size', 10))
        self.task_queue = TaskQueue(backend=config.get('queue_backend', 'redis'))
        self.state_store = StateStore(backend=config.get('state_backend', 'postgres'))
        self.metrics_collector = MetricsCollector()
    
    async def execute_distributed(self, workflows: List[dict]):
        """Execute multiple workflows in parallel"""
        
        # Submit workflows to task queue
        task_ids = []
        for workflow in workflows:
            task_id = await self.task_queue.submit(
                task_type='workflow_execution',
                payload=workflow,
                priority=workflow.get('priority', 'normal')
            )
            task_ids.append(task_id)
        
        # Monitor execution
        results = await self._monitor_parallel_execution(task_ids)
        
        return results
    
    async def _monitor_parallel_execution(self, task_ids: List[str]):
        """Monitor and collect results from parallel execution"""
        results = {}
        completed = set()
        
        while len(completed) < len(task_ids):
            for task_id in task_ids:
                if task_id not in completed:
                    status = await self.task_queue.get_status(task_id)
                    
                    if status['state'] == 'completed':
                        results[task_id] = await self.task_queue.get_result(task_id)
                        completed.add(task_id)
                        
                        # Update metrics
                        self.metrics_collector.record_completion(task_id, status)
                    
                    elif status['state'] == 'failed':
                        results[task_id] = {'error': status['error']}
                        completed.add(task_id)
                        
                        # Update metrics
                        self.metrics_collector.record_failure(task_id, status)
            
            await asyncio.sleep(1)  # Polling interval
        
        return results
```

### Monitoring and Observability

```python
class WorkflowObservability:
    """
    Comprehensive monitoring and observability for production systems.
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.tracer = DistributedTracer()
        self.logger = StructuredLogger()
        self.alerting = AlertingSystem()
    
    def instrument_workflow(self, workflow: StateGraph) -> StateGraph:
        """Add observability to all workflow nodes"""
        
        instrumented = StateGraph(workflow.state_schema)
        
        for node_name, node_func in workflow.nodes.items():
            instrumented_func = self._instrument_node(node_name, node_func)
            instrumented.add_node(node_name, instrumented_func)
        
        # Copy edges
        for edge in workflow.edges:
            instrumented.add_edge(edge.from_node, edge.to_node)
        
        return instrumented.compile()
    
    def _instrument_node(self, node_name: str, node_func: Callable) -> Callable:
        """Add monitoring to individual node"""
        
        async def instrumented_node(state):
            # Start tracing span
            with self.tracer.start_span(f"agent.{node_name}") as span:
                span.set_attribute("workflow_id", state.get('workflow_id'))
                span.set_attribute("agent_name", node_name)
                
                # Record start metrics
                start_time = time.time()
                self.metrics.increment(f"agent.{node_name}.starts")
                
                try:
                    # Execute original function
                    result = await node_func(state)
                    
                    # Record success metrics
                    duration = time.time() - start_time
                    self.metrics.record_duration(f"agent.{node_name}.duration", duration)
                    self.metrics.increment(f"agent.{node_name}.successes")
                    
                    # Log execution
                    self.logger.info(
                        "Agent execution completed",
                        agent=node_name,
                        duration=duration,
                        workflow_id=state.get('workflow_id')
                    )
                    
                    return result
                
                except Exception as e:
                    # Record failure metrics
                    duration = time.time() - start_time
                    self.metrics.increment(f"agent.{node_name}.failures")
                    
                    # Log error
                    self.logger.error(
                        "Agent execution failed",
                        agent=node_name,
                        error=str(e),
                        duration=duration,
                        workflow_id=state.get('workflow_id')
                    )
                    
                    # Trigger alert if needed
                    await self._check_alerting_conditions(node_name, e)
                    
                    # Set span status
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    
                    raise
        
        return instrumented_node
    
    async def _check_alerting_conditions(self, agent_name: str, error: Exception):
        """Check if error conditions warrant alerts"""
        
        # Get recent failure rate
        failure_rate = self.metrics.get_failure_rate(f"agent.{agent_name}", window='5m')
        
        if failure_rate > 0.5:  # 50% failure rate
            await self.alerting.send_alert(
                level='critical',
                message=f"High failure rate for agent {agent_name}: {failure_rate:.2%}",
                context={'agent': agent_name, 'error': str(error)}
            )
```

### Error Recovery and Resilience

```python
class ResilientWorkflowExecutor:
    """
    Implements comprehensive error recovery and resilience patterns.
    """
    
    def __init__(self):
        self.retry_strategy = ExponentialBackoffRetry(max_attempts=3, base_delay=1.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.fallback_registry = FallbackRegistry()
    
    async def execute_with_resilience(self, workflow: StateGraph, initial_state: dict):
        """Execute workflow with full resilience patterns"""
        
        try:
            # Circuit breaker check
            if not self.circuit_breaker.can_execute():
                raise CircuitBreakerOpenError("Circuit breaker is open")
            
            # Execute with retry
            result = await self.retry_strategy.execute(
                workflow.ainvoke, initial_state
            )
            
            # Record success
            self.circuit_breaker.record_success()
            
            return result
        
        except Exception as e:
            # Record failure
            self.circuit_breaker.record_failure()
            
            # Attempt fallback
            fallback_result = await self._attempt_fallback(workflow, initial_state, e)
            
            if fallback_result:
                return fallback_result
            
            # No fallback available, re-raise
            raise
    
    async def _attempt_fallback(self, workflow: StateGraph, state: dict, original_error: Exception):
        """Attempt fallback execution strategies"""
        
        fallback_strategies = self.fallback_registry.get_strategies(workflow.name)
        
        for strategy in fallback_strategies:
            try:
                return await strategy.execute(state, original_error)
            except Exception:
                continue  # Try next fallback
        
        return None  # No fallback succeeded

class ExponentialBackoffRetry:
    """Implements exponential backoff retry strategy"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    # Last attempt, don't delay
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
        
        # All attempts failed
        raise last_exception
```

### Security Architecture

```python
class SecureMultiAgentFramework:
    """
    Implements comprehensive security controls for production deployment.
    """
    
    def __init__(self, security_config: dict):
        self.auth_service = AuthenticationService(security_config['auth'])
        self.authz_service = AuthorizationService(security_config['authz'])
        self.audit_logger = SecurityAuditLogger(security_config['audit'])
        self.input_validator = InputValidator(security_config['validation'])
        self.output_sanitizer = OutputSanitizer(security_config['sanitization'])
    
    async def secure_execute(self, workflow_request: dict, user_context: dict):
        """Execute workflow with full security controls"""
        
        # 1. Authentication
        user = await self.auth_service.authenticate(user_context)
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # 2. Authorization
        authorized = await self.authz_service.authorize(
            user, 'workflow:execute', workflow_request
        )
        if not authorized:
            raise AuthorizationError("Insufficient permissions")
        
        # 3. Input validation
        validated_request = await self.input_validator.validate(workflow_request)
        
        # 4. Audit logging
        await self.audit_logger.log_access(
            user=user,
            action='workflow:execute',
            resource=workflow_request.get('workflow_id'),
            outcome='attempt'
        )
        
        try:
            # 5. Execute workflow
            result = await self._execute_workflow(validated_request)
            
            # 6. Output sanitization
            sanitized_result = await self.output_sanitizer.sanitize(result, user)
            
            # 7. Audit success
            await self.audit_logger.log_access(
                user=user,
                action='workflow:execute',
                resource=workflow_request.get('workflow_id'),
                outcome='success'
            )
            
            return sanitized_result
        
        except Exception as e:
            # Audit failure
            await self.audit_logger.log_access(
                user=user,
                action='workflow:execute',
                resource=workflow_request.get('workflow_id'),
                outcome='failure',
                error=str(e)
            )
            raise

class InputValidator:
    """Validates and sanitizes all inputs to prevent injection attacks"""
    
    def __init__(self, config: dict):
        self.max_input_size = config.get('max_input_size', 1024 * 1024)  # 1MB
        self.allowed_file_types = config.get('allowed_file_types', [])
        self.sql_injection_patterns = self._load_injection_patterns()
    
    async def validate(self, request: dict) -> dict:
        """Comprehensive input validation"""
        
        # Size validation
        if self._calculate_size(request) > self.max_input_size:
            raise InputValidationError("Request too large")
        
        # SQL injection detection
        if self._detect_sql_injection(request):
            raise InputValidationError("Potential SQL injection detected")
        
        # File type validation
        if 'files' in request:
            for file_info in request['files']:
                if not self._validate_file_type(file_info):
                    raise InputValidationError(f"Invalid file type: {file_info.get('type')}")
        
        # Script injection detection
        if self._detect_script_injection(request):
            raise InputValidationError("Potential script injection detected")
        
        return request
```

---

## Conclusion

This comprehensive system design architecture provides a complete blueprint for building sophisticated multi-agent systems that can handle any workflow. The architecture ensures:

### 1. **Modularity Through Specialization**
- Each agent has a single, well-defined responsibility
- Agents can be developed and tested independently
- Easy to replace or upgrade individual agents
- Clear separation of concerns

### 2. **Quality Assurance Built-In**
- Systematic review and revision cycles
- Multiple validation strategies
- Confidence scoring and tracking
- Human-in-the-loop for critical decisions

### 3. **Hallucination Prevention**
- Source verification for all claims
- Cross-agent validation
- Confidence-based quality gates
- Systematic fact-checking

### 4. **Production-Ready**
- Scalable architecture with worker pools
- Comprehensive monitoring and observability
- Error recovery and resilience patterns
- Security controls and audit logging

### 5. **Framework Flexibility**
- Protocol-agnostic design (CLI, WebSocket, MCP, REST)
- Multi-provider support with automatic failover
- Configuration-driven workflow creation
- Domain-specific customization

### Key Success Factors

1. **Maintain Agent Discipline**: Each agent must have exactly one responsibility
2. **Implement Quality Loops**: Every output should be reviewable and revisable
3. **Use State-Based Communication**: Immutable state transitions ensure traceability
4. **Plan for Scale**: Design for distributed execution from the beginning
5. **Monitor Everything**: Comprehensive observability is essential for production

### Replication Guide

To replicate this architecture for any domain:

1. **Identify Your Workflow Stages**: Break down the process into discrete steps
2. **Map Agents to Stages**: Create one specialized agent per step
3. **Define Quality Criteria**: Establish what constitutes good output
4. **Implement Review Loops**: Build in quality assurance mechanisms
5. **Configure Orchestration**: Use LangGraph or similar to manage workflow
6. **Add Communication Protocols**: Support your required interfaces
7. **Plan for Production**: Include monitoring, error handling, and security

This architecture has proven effective for research automation, content creation, data processing, and business workflow automation. By following these patterns, you can create multi-agent systems that consistently deliver high-quality results while minimizing AI hallucinations and maximizing reliability.

The framework's power lies in its systematic approach to quality assurance and its modular design that allows for easy adaptation to any domain while maintaining the core principles of specialization, orchestration, and quality control.