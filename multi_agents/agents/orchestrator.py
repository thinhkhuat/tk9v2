import os
import time
import datetime
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver
from .utils.views import print_agent_output
from .utils.type_safety import ensure_dict, safe_dict_get
from ..memory.research import ResearchState


def safe_string_operation(data, operation, *args, **kwargs):
    """
    Safely perform string operations with automatic type conversion.
    
    Args:
        data: Input data (any type)
        operation: String method name (e.g., 'lower', 'strip', 'startswith')
        *args, **kwargs: Arguments to pass to the string method
        
    Returns:
        Result of operation or appropriate fallback
    """
    if data is None:
        return "" if operation in ['lower', 'upper', 'strip'] else False
    
    # Convert to string if not already a string
    if not isinstance(data, str):
        data_str = str(data) if data else ""
    else:
        data_str = data
    
    try:
        method = getattr(data_str, operation)
        return method(*args, **kwargs)
    except (AttributeError, TypeError) as e:
        # Return safe defaults for common operations
        if operation == 'lower' or operation == 'upper':
            return data_str
        elif operation == 'strip':
            return data_str
        elif operation in ['startswith', 'endswith', 'find', 'count']:
            return False if operation in ['startswith', 'endswith'] else 0
        else:
            return data_str
from .utils.utils import sanitize_filename
from ..providers.factory import enhanced_config
from ..utils.draft_manager import DraftManager

# Import agent classes
from . import \
    WriterAgent, \
    EditorAgent, \
    PublisherAgent, \
    ResearchAgent, \
    HumanAgent, \
    TranslatorAgent


class ChiefEditorAgent:
    """Agent responsible for managing and coordinating editing tasks."""

    def __init__(self, task: Dict[str, Any], websocket=None, stream_output=None, tone=None, headers=None, write_to_files: bool = False, task_id=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        # Use provided task_id (from web dashboard) or generate timestamp-based ID
        self.task_id = task_id if task_id is not None else self._generate_task_id()
        self.output_dir = self._create_output_directory() if write_to_files else None
        
        # Initialize draft manager if writing to files
        self.draft_manager = DraftManager(self.output_dir, self.task_id) if write_to_files else None
        
        # Initialize multi-provider configuration
        self._setup_providers()
        
        # Initialize language configuration
        self._setup_language()

    def _generate_task_id(self):
        # Currently time based, but can be any unique identifier
        return int(time.time())

    def _create_output_directory(self):
        query = safe_dict_get(self.task, 'query', 'unknown_query', str)

        # Check if task_id is a UUID (from web dashboard)
        # UUIDs are strings with dashes (e.g., "f84a84cb-dc65-4321-abe1-169c502ad2fe")
        # Traditional task_ids are integers (timestamps)
        is_uuid = isinstance(self.task_id, str) and '-' in str(self.task_id)

        if is_uuid:
            # Web dashboard session - use session_id directly
            output_dir = f"./outputs/{self.task_id}"
        else:
            # CLI manual run - use traditional run_timestamp_query format
            output_dir = "./outputs/" + \
                sanitize_filename(
                    f"run_{self.task_id}_{query[0:40]}")

        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _setup_providers(self):
        """Setup multi-provider configuration with validation"""
        try:
            # Force reload environment variables and provider configuration
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            # Reload the provider configuration with updated environment
            enhanced_config.config_manager.config = enhanced_config.config_manager._load_config_from_env()
            enhanced_config._update_config()
            
            # Validate configuration before proceeding
            try:
                enhanced_config.config_manager.validate_before_operation("general")
                print_agent_output("Configuration validated successfully", "PROVIDERS")
                
            except RuntimeError as validation_error:
                error_msg = f"Configuration validation failed: {str(validation_error)}"
                print_agent_output(error_msg, "ERROR")
                print_agent_output("🛠️  Quick fix suggestions:", "PROVIDERS")
                print_agent_output("   1. Check your .env file exists and has valid API keys", "PROVIDERS")
                print_agent_output("   2. Ensure PRIMARY_LLM_PROVIDER and PRIMARY_SEARCH_PROVIDER are set", "PROVIDERS")
                print_agent_output("   3. Run 'python main.py --config' for detailed diagnostics", "PROVIDERS")
                
                # Don't fail completely - attempt to continue
                print_agent_output("Attempting to continue despite configuration issues...", "PROVIDERS")
            
            # Apply current provider configuration to environment
            enhanced_config.apply_to_environment()
            
            # Log current provider information
            current_providers = enhanced_config.get_current_providers()
            provider_msg = (f"Using LLM: {current_providers['llm_provider']}:{current_providers['llm_model']}, "
                          f"Search: {current_providers['search_provider']}")
            
            print_agent_output(f"Providers - {provider_msg}", "PROVIDERS")
                
        except Exception as e:
            error_msg = f"Provider setup error: {str(e)}"
            print_agent_output(error_msg, "ERROR")
            
            # Provide actionable guidance
            print_agent_output("🚨 Critical provider setup failure!", "ERROR")
            print_agent_output("🛠️  Troubleshooting steps:", "ERROR")
            print_agent_output("   1. Copy .env.example to .env", "ERROR")
            print_agent_output("   2. Configure API keys in .env file", "ERROR")
            print_agent_output("   3. Set PRIMARY_LLM_PROVIDER (openai/google_gemini/anthropic)", "ERROR")
            print_agent_output("   4. Set PRIMARY_SEARCH_PROVIDER (tavily/brave/google/duckduckgo)", "ERROR")
            print_agent_output("   5. Run 'python main.py --config' to validate", "ERROR")
    
    def _setup_language(self):
        """Setup language configuration for the entire research process"""
        try:
            from ..utils.language_config import language_config
            
            # Apply language settings to environment
            language_config.apply_to_environment()
            
            # Store language configuration for use by agents
            self.language_config = language_config
            
            # Display language status
            lang_status = language_config.get_status_message()
            print_agent_output(f"Language - {lang_status}", "LANGUAGE")
                
        except Exception as e:
            error_msg = f"Language setup error: {str(e)}"
            print_agent_output(error_msg, "ERROR")
    
    def switch_providers(self, llm_fallback: bool = False, search_fallback: bool = False):
        """Switch to fallback providers if needed"""
        try:
            if llm_fallback:
                enhanced_config.switch_llm_provider(use_fallback=True)
                
            if search_fallback:
                enhanced_config.switch_search_provider(use_fallback=True)
            
            current_providers = enhanced_config.get_current_providers()
            return current_providers
            
        except Exception as e:
            print_agent_output(f"Provider switch error: {str(e)}", "ERROR")
            return None

    def _initialize_agents(self):
        return {
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers, self.draft_manager),
            "editor": EditorAgent(self.websocket, self.stream_output, self.tone, self.headers, self.draft_manager),
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers, self.draft_manager),
            "translator": TranslatorAgent(self.websocket, self.stream_output, self.headers, self.draft_manager, self.output_dir),
            "publisher": PublisherAgent(self.output_dir, self.websocket, self.stream_output, self.headers, self.draft_manager),
            "human": HumanAgent(self.websocket, self.stream_output, self.headers, self.draft_manager)
        }

    def _create_workflow(self, agents):
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        workflow.add_node("browser", agents["research"].run_initial_research)
        workflow.add_node("planner", agents["editor"].plan_research)
        workflow.add_node("researcher", agents["editor"].run_parallel_research)
        workflow.add_node("writer", agents["writer"].run)
        workflow.add_node("translator", agents["translator"].run)
        workflow.add_node("publisher", agents["publisher"].run)
        workflow.add_node("human", agents["human"].review_plan)

        # Add edges
        self._add_workflow_edges(workflow)

        return workflow

    def _add_workflow_edges(self, workflow):
        workflow.add_edge('browser', 'planner')
        workflow.add_edge('planner', 'human')
        workflow.add_edge('researcher', 'writer')
        workflow.set_entry_point("browser")

        # SIMPLIFIED WORKFLOW: Direct path from writer to publisher (no review/revision)
        # Writer → Publisher (bypass reviewer/reviser agents)
        workflow.add_edge('writer', 'publisher')
        
        # Publisher → conditional translation
        workflow.add_conditional_edges(
            'publisher',
            self._should_translate,
            {"translate": "translator", "skip": END}
        )
        
        # TRANSLATOR IS THE FINAL AGENT - it ends the workflow
        workflow.add_edge('translator', END)

        # Add human in the loop
        workflow.add_conditional_edges(
            'human',
            lambda review: "accept" if review['human_feedback'] is None else "revise",
            {"accept": "researcher", "revise": "planner"}
        )


    def _should_translate(self, research_state: Dict[str, Any]) -> str:
        """
        Determine if translation is needed based on language configuration.
        
        Args:
            research_state: The current research state
            
        Returns:
            "translate" if translation needed, "skip" if not
        """
        task = ensure_dict(research_state.get("task"))
        target_language = safe_dict_get(task, "language", os.getenv("RESEARCH_LANGUAGE", "en"), str)
        
        # Only translate if target language is not English
        target_lang_str = str(target_language) if target_language else "en"
        if target_lang_str and safe_string_operation(target_lang_str, 'lower') != "en":
            print_agent_output(f"Translation needed for language: {target_language}", "ORCHESTRATOR")
            return "translate"
        else:
            print_agent_output("Skipping translation for English content", "ORCHESTRATOR")
            return "skip"

    

    def init_research_team(self):
        """Initialize and create a workflow for the research team."""
        agents = self._initialize_agents()
        return self._create_workflow(agents)

    async def _log_research_start(self):
        message = f"Starting the research process for query '{safe_dict_get(self.task, 'query', 'Unknown Query')}'..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "starting_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")

    async def _log_workflow_structure(self):
        """Log the simplified workflow structure"""
        workflow_message = """
Simplified Multi-Agent Workflow Architecture:
1. Browser → Initial web research
2. Planner → Structure outline (EditorAgent.plan_research)  
3. Human → Review and feedback (optional)
4. Researcher → Deep research (EditorAgent.run_parallel_research)
5. Writer → Create draft
6. Publisher → Save to files (DIRECT - no review/revision)
7. Translator → Translate and save (if needed)

Simplification Benefits:
- Faster processing time (3-4 minutes vs 6+ minutes)
- Lower API costs (no BRAVE calls for fact-checking)
- Direct path from research to publication
- Maintains output quality while eliminating resource waste
        """.strip()
        
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "workflow_structure", workflow_message, self.websocket)
        else:
            print_agent_output(workflow_message, "ORCHESTRATOR")

    async def run_research_task(self, task_id=None):
        """
        Run a research task with the initialized research team.

        Args:
            task_id (optional): The ID of the task to run.

        Returns:
            The result of the research task.
        """
        try:
            research_team = self.init_research_team()
            chain = research_team.compile()

            await self._log_research_start()
            await self._log_workflow_structure()

            config = {
                "configurable": {
                    "thread_id": task_id,
                    "thread_ts": datetime.datetime.utcnow()
                }
            }

            # Initialize the research state for simplified workflow
            initial_state = {
                "task": self.task
            }
            
            result = await chain.ainvoke(initial_state, config=config)
            
        except Exception as e:
            error_msg = f"Error in research workflow: {str(e)}"
            print_agent_output(error_msg, agent="ORCHESTRATOR")
            
            # Create error result with partial state if available
            result = {
                "task": self.task,
                "error": error_msg,
                "workflow_failed": True
            }
            
            # Try to save error state if draft manager exists
            if self.draft_manager:
                try:
                    self.draft_manager.save_agent_output(
                        agent_name="orchestrator",
                        phase="error_handling",
                        output={"error": error_msg, "task_id": task_id},
                        step="workflow_error",
                        metadata={"exception_type": type(e).__name__}
                    )
                except Exception as save_error:
                    print_agent_output(f"Failed to save error state: {save_error}", agent="ORCHESTRATOR")
        
        # Save final workflow completion
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="orchestrator",
                phase="workflow_completion",
                output=result,
                step="final_result",
                metadata={
                    "task_id": task_id,
                    "workflow_completed": True,
                    "total_phases": len(self.draft_manager.metadata.get("phases", []))
                }
            )
            
            # Create comprehensive workflow summary
            self._create_workflow_summary()
        
        return result
    
    def _create_workflow_summary(self):
        """Create a comprehensive summary of the entire workflow"""
        if not self.draft_manager:
            return
            
        import json
        from datetime import datetime
        
        summary_content = f"# Research Workflow Summary\n\n"
        summary_content += f"**Task ID:** {self.task_id}\n"
        summary_content += f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary_content += f"**Query:** {safe_dict_get(self.task, 'query', 'N/A')}\n\n"
        
        # Phase overview
        phases = self.draft_manager.metadata.get("phases", [])
        summary_content += f"## Workflow Phases Completed ({len(phases)})\n\n"
        for i, phase in enumerate(phases, 1):
            phase_history = self.draft_manager.get_phase_history(phase)
            summary_content += f"{i}. **{phase.title()}** - {len(phase_history)} outputs\n"
        
        summary_content += "\n## Agent Activity Summary\n\n"
        
        # Agent activity summary
        agent_outputs = self.draft_manager.metadata.get("agent_outputs", {})
        for agent, agent_data in agent_outputs.items():
            total_outputs = sum(len(outputs) for outputs in agent_data.values())
            summary_content += f"- **{agent.title()}**: {total_outputs} outputs across {len(agent_data)} phases\n"
        
        summary_content += "\n## Draft Files Organization\n\n"
        summary_content += "All intermediate outputs have been saved in the following structure:\n\n"
        summary_content += "```\n"
        summary_content += f"{self.draft_manager.output_dir}/\n"
        summary_content += "├── drafts/\n"
        summary_content += "│   ├── 1_initial_research/\n"
        summary_content += "│   ├── 2_planning/\n"  
        summary_content += "│   ├── 3_parallel_research/\n"
        summary_content += "│   ├── 4_writing/\n"
        summary_content += "│   ├── 5_publishing/\n"
        summary_content += "│   ├── 6_translating/\n"
        summary_content += "│   ├── human_feedback/\n"
        summary_content += "│   └── metadata.json\n"
        summary_content += "└── [final outputs]\n"
        summary_content += "```\n\n"
        
        summary_content += "## Key Insights\n\n"
        summary_content += f"- **Total agents involved:** {len(agent_outputs)}\n"
        summary_content += f"- **Total phases completed:** {len(phases)}\n"
        summary_content += f"- **Total draft files created:** {sum(len(agent_data.get(phase, [])) for agent_data in agent_outputs.values() for phase in agent_data)}\n"
        
        if "human_feedback" in phases:
            summary_content += "- **Human feedback was provided during the workflow**\n"
            
        summary_content += f"\n**All intermediate work has been preserved and is available for review in the drafts folder.**\n"
        
        # Save workflow summary
        summary_path = os.path.join(self.draft_manager.drafts_dir, "WORKFLOW_SUMMARY.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
            
        print_agent_output(f"Workflow summary saved to: {summary_path}", "ORCHESTRATOR")
