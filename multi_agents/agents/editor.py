import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from langgraph.graph import END, StateGraph

from ..memory.draft import DraftState
from .researcher import ResearchAgent
from .utils.llms import call_model
from .utils.views import print_agent_output  # FIX: Missing import

# Lazy import to avoid circular dependency
# ResearchAgent imported at runtime when needed


class EditorAgent:
    """Agent responsible for editing and managing code."""

    def __init__(
        self, websocket=None, stream_output=None, tone=None, headers=None, draft_manager=None
    ):
        self.websocket = websocket
        self.stream_output = stream_output
        self.tone = tone
        self.headers = headers or {}
        self.draft_manager = draft_manager

    async def plan_research(self, research_state: Dict[str, any]) -> Dict[str, any]:
        """
        Plan the research outline based on initial research and task parameters.

        :param research_state: Dictionary containing research state information
        :return: Dictionary with title, date, and planned sections
        """
        initial_research = research_state.get("initial_research")
        task = research_state.get("task")
        include_human_feedback = task.get("include_human_feedback")
        human_feedback = research_state.get("human_feedback")
        max_sections = task.get("max_sections")

        prompt = self._create_planning_prompt(
            initial_research, include_human_feedback, human_feedback, max_sections
        )

        print_agent_output(
            "Planning an outline layout based on initial research...", agent="EDITOR"
        )
        plan = await call_model(
            prompt=prompt,
            model=task.get("model"),
            response_format="json",
        )

        # Handle case where plan might be a string instead of dict due to JSON parsing failure
        if isinstance(plan, str):
            # Extract the original query from the task for a better fallback
            task = research_state.get("task", {})
            original_query = task.get("query", "Research Report")

            print_agent_output(
                "JSON parsing failed, using query-based fallback plan", agent="EDITOR"
            )

            # Create meaningful sections based on the user's query
            query_words = original_query.lower()
            if any(word in query_words for word in ["tariff", "trade", "policy", "economic"]):
                sections = [
                    "Policy Background and Context",
                    "Economic Impact Analysis",
                    "International Trade Implications",
                    "Implementation and Enforcement",
                    "Future Outlook and Recommendations",
                ]
            elif any(word in query_words for word in ["vietnam", "vietnamese", "vietnam"]):
                sections = [
                    "Vietnam Economic Overview",
                    "Trade Relations Analysis",
                    "Policy Impact Assessment",
                    "Strategic Implications",
                    "Future Prospects",
                ]
            elif any(word in query_words for word in ["court", "ruling", "legal", "appeals"]):
                sections = [
                    "Legal Background and Context",
                    "Court Decision Analysis",
                    "Legal Precedents and Implications",
                    "Enforcement Mechanisms",
                    "Future Legal Considerations",
                ]
            else:
                # Generic fallback based on query
                sections = [
                    f"Background of {original_query}",
                    "Current State Analysis",
                    "Key Factors and Drivers",
                    "Impact Assessment",
                    "Future Implications",
                ]

            plan = {
                "title": original_query,
                "date": datetime.now().strftime("%d/%m/%Y"),
                "sections": sections[:max_sections],  # Respect max_sections limit
            }

        # Apply section limits from task configuration and validate sections
        sections = plan.get("sections", [])
        max_sections = task.get("max_sections", 5)  # Default to 5 if not specified

        # If sections are empty or invalid, generate fallback sections
        if not sections or len(sections) == 0:
            task = research_state.get("task", {})
            original_query = task.get("query", "Research Report")
            print_agent_output(
                "No sections generated, creating fallback sections based on query", agent="EDITOR"
            )

            # Create meaningful sections based on the user's query
            query_words = original_query.lower()
            if any(word in query_words for word in ["tariff", "trade", "policy", "economic"]):
                sections = [
                    "Policy Background and Context",
                    "Economic Impact Analysis",
                    "International Trade Implications",
                    "Implementation and Enforcement",
                    "Future Outlook and Recommendations",
                ]
            elif any(word in query_words for word in ["vietnam", "vietnamese"]):
                sections = [
                    "Vietnam Economic Overview",
                    "Trade Relations Analysis",
                    "Policy Impact Assessment",
                    "Strategic Implications",
                    "Future Prospects",
                ]
            elif any(word in query_words for word in ["court", "ruling", "legal", "appeals"]):
                sections = [
                    "Legal Background and Context",
                    "Court Decision Analysis",
                    "Legal Precedents and Implications",
                    "Enforcement Mechanisms",
                    "Future Legal Considerations",
                ]
            else:
                # Generic fallback based on query
                sections = [
                    "Background and Context",
                    "Current State Analysis",
                    "Key Factors and Impact",
                    "Implications and Effects",
                    "Future Outlook",
                ]

            # Update the plan with fallback sections and correct title
            plan["sections"] = sections
            if plan.get("title") in ["Untitled Research Project", "Research Report", None, ""]:
                plan["title"] = original_query

        # Only limit if we exceed the configured maximum
        if len(sections) > max_sections:
            sections = sections[:max_sections]
            plan["sections"] = sections
            print_agent_output(f"Limited sections to {max_sections} as configured", agent="EDITOR")

        result = {
            "title": plan.get("title"),
            "date": plan.get("date"),
            "sections": sections,
        }

        # Save planning output
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="editor",
                phase="planning",
                output=plan,
                step="plan_research",
                metadata={
                    "max_sections": max_sections,
                    "include_human_feedback": include_human_feedback,
                    "sections_planned": len(sections),
                },
            )

            # Save research state after planning
            self.draft_manager.save_research_state("planning", {**research_state, **result})

        return result

    async def run_parallel_research(self, research_state: Dict[str, any]) -> Dict[str, List[str]]:
        """
        Execute parallel research tasks for each section.

        :param research_state: Dictionary containing research state information
        :return: Dictionary with research results
        """
        agents = self._initialize_agents()
        workflow = self._create_workflow()
        chain = workflow.compile()

        queries = research_state.get("sections")
        title = research_state.get("title")

        self._log_parallel_research(queries)

        final_drafts = [
            chain.ainvoke(self._create_task_input(research_state, query, title))
            for query in queries
        ]
        research_results = [result["draft"] for result in await asyncio.gather(*final_drafts)]

        result = {"research_data": research_results}

        # Save parallel research results
        if self.draft_manager:
            self.draft_manager.save_agent_output(
                agent_name="editor",
                phase="parallel_research",
                output=result,
                step="run_parallel_research",
                metadata={
                    "queries": queries,
                    "title": title,
                    "results_count": len(research_results),
                },
            )

            # Save research state after parallel research
            self.draft_manager.save_research_state(
                "parallel_research", {**research_state, **result}
            )

        return result

    def _create_planning_prompt(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> List[Dict[str, str]]:
        """Create the prompt for research planning."""
        return [
            {
                "role": "system",
                "content": "You are a research editor. Your goal is to oversee the research project "
                "from inception to completion. Your main task is to plan the article section "
                "layout based on an initial research summary.\n ",
            },
            {
                "role": "user",
                "content": self._format_planning_instructions(
                    initial_research, include_human_feedback, human_feedback, max_sections
                ),
            },
        ]

    def _format_planning_instructions(
        self,
        initial_research: str,
        include_human_feedback: bool,
        human_feedback: Optional[str],
        max_sections: int,
    ) -> str:
        """Format the instructions for research planning."""
        today = datetime.now().strftime("%d/%m/%Y")
        feedback_instruction = (
            f"Human feedback: {human_feedback}. You must plan the sections based on the human feedback."
            if include_human_feedback and human_feedback and human_feedback != "no"
            else ""
        )

        return f"""Today's date is {today}
                   Research summary report: '{initial_research}'
                   {feedback_instruction}
                   \nYour task is to generate an outline of sections headers for the research project
                   based on the research summary report above.
                   You must generate a maximum of {max_sections} section headers.
                   You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.
                   
                   You MUST return ONLY a valid JSON object (no markdown code blocks, no additional text) with the following structure:
                   {{
                     "title": "string research title",
                     "date": "{today}",
                     "sections": ["section header 1", "section header 2", "section header 3"]
                   }}
                   
                   Return only valid JSON, nothing else."""

    def _initialize_agents(self) -> Dict[str, any]:
        """Initialize the research agent (simplified workflow)."""
        # Lazy import to avoid circular dependency

        return {
            "research": ResearchAgent(
                self.websocket, self.stream_output, self.tone, self.headers, self.draft_manager
            ),
        }

    def _create_workflow(self) -> StateGraph:
        """Create the simplified workflow for the research process (no review/revision)."""
        agents = self._initialize_agents()
        workflow = StateGraph(DraftState)

        workflow.add_node("researcher", agents["research"].run_depth_research)
        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", END)

        return workflow

    def _should_revise_or_accept(self, draft_state: Dict[str, any]) -> str:
        """
        Determine whether to revise or accept the draft based on review and revision count.

        Args:
            draft_state: The current draft state

        Returns:
            "accept" or "revise"
        """
        MAX_REVISIONS = 3  # Maximum number of revision cycles

        review = draft_state.get("review")
        revision_count = draft_state.get("revision_count", 0)

        # If no review (reviewer accepted the draft), accept
        if review is None:
            return "accept"

        # If we've reached max revisions, force accept to prevent infinite loop
        if revision_count >= MAX_REVISIONS:
            print_agent_output(
                f"Reached maximum revisions ({MAX_REVISIONS}), accepting draft to prevent infinite loop",
                agent="EDITOR",
            )
            return "accept"

        # Otherwise, revise
        return "revise"

    def _log_parallel_research(self, queries: List[str]) -> None:
        """Log the start of parallel research tasks."""
        if self.websocket and self.stream_output:
            asyncio.create_task(
                self.stream_output(
                    "logs",
                    "parallel_research",
                    f"Running parallel research for the following queries: {queries}",
                    self.websocket,
                )
            )
        else:
            print_agent_output(
                f"Running the following research tasks in parallel: {queries}...",
                agent="EDITOR",
            )

    def _create_task_input(
        self, research_state: Dict[str, any], query: str, title: str
    ) -> Dict[str, any]:
        """Create the input for a single research task."""
        return {
            "task": research_state.get("task"),
            "topic": query,
            "title": title,
            "headers": self.headers,
            "revision_count": 0,  # Initialize revision counter
        }
