"""
Draft Manager
Handles saving and organizing draft outputs from each research phase and agent
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Import sanitize_filename or provide a fallback
try:
    from ..agents.utils.utils import sanitize_filename
except (ImportError, ValueError):
    # Fallback implementation
    def sanitize_filename(name):
        """Simple sanitize function for filenames"""
        return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).rstrip()


class DraftManager:
    """Manages draft outputs from all research phases and agents"""

    def __init__(self, output_dir: str, task_id: int):
        """
        Initialize the draft manager

        Args:
            output_dir: Main output directory for the research task
            task_id: Unique identifier for the research task
        """
        self.output_dir = output_dir
        self.task_id = task_id
        self.drafts_dir = os.path.join(output_dir, "drafts")
        self.file_counter = 0  # FIX: Counter for unique filenames instead of timestamp
        self.metadata = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "phases": [],
            "agent_outputs": {},
        }

        # Create drafts directory structure
        self._create_drafts_structure()

    def _create_drafts_structure(self):
        """Create the drafts directory structure"""
        os.makedirs(self.drafts_dir, exist_ok=True)

        # Create subdirectories for each phase
        phase_dirs = [
            "1_initial_research",
            "2_planning",
            "3_parallel_research",
            "4_writing",
            "5_translation",
            "6_editing",
            "7_publishing",
            "human_feedback",
            "revisions",
            "workflow_completion",
            "error_handling",  # FIX: Added for orchestrator error logging
        ]

        for phase_dir in phase_dirs:
            os.makedirs(os.path.join(self.drafts_dir, phase_dir), exist_ok=True)

    def save_agent_output(
        self,
        agent_name: str,
        phase: str,
        output: Union[str, Dict, List],
        step: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Save output from a specific agent and phase

        Args:
            agent_name: Name of the agent (researcher, writer, editor, etc.)
            phase: Research phase (initial_research, planning, etc.)
            output: The output content to save
            step: Optional step within the phase (for metadata only, not filename)
            metadata: Optional metadata about the output

        Returns:
            Path to the saved file
        """
        # FIX: Use session ID + counter for unique, filesystem-safe filenames
        # Old format: {timestamp}_{agent_name}_{step}.{ext} <- step had illegal chars
        # New format: {session_id}_{agent_name}_{counter}.{ext}
        self.file_counter += 1

        # Determine file extension based on content type
        if isinstance(output, (dict, list)):
            ext = "json"
            content = json.dumps(output, indent=2, ensure_ascii=False)
        else:
            ext = "md" if phase in ["writing", "editing"] else "txt"
            content = str(output)

        # Create filesystem-safe filename using session ID
        # Format: {session_id}_{agent_name}_{counter}.{ext}
        filename = f"{self.task_id}_{agent_name}_{self.file_counter:04d}.{ext}"
        phase_dir = self._get_phase_directory(phase)

        # FIX: Ensure directory exists before writing (defensive programming)
        os.makedirs(phase_dir, exist_ok=True)

        filepath = os.path.join(phase_dir, filename)

        # Save content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Update metadata (step stored in metadata, not filename)
        self._update_metadata(agent_name, phase, filepath, step, metadata)

        return filepath

    def save_research_state(
        self, phase: str, research_state: Dict[str, Any], step: Optional[str] = None
    ) -> str:
        """
        Save the complete research state at a specific phase

        Args:
            phase: Research phase name
            research_state: Complete research state dictionary
            step: Optional step within the phase (for metadata only)

        Returns:
            Path to the saved state file
        """
        # FIX: Use session ID + counter format
        self.file_counter += 1

        filename = f"{self.task_id}_research_state_{self.file_counter:04d}.json"
        phase_dir = self._get_phase_directory(phase)

        # FIX: Ensure directory exists
        os.makedirs(phase_dir, exist_ok=True)

        filepath = os.path.join(phase_dir, filename)

        # Clean and prepare state for JSON serialization
        clean_state = self._clean_state_for_json(research_state)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(clean_state, f, indent=2, ensure_ascii=False, default=str)

        # Update metadata
        self._update_metadata(
            "system",
            phase,
            filepath,
            step,
            {"type": "research_state", "keys": list(research_state.keys())},
        )

        return filepath

    def save_intermediate_draft(
        self, content: str, phase: str, section: Optional[str] = None, agent: str = "writer"
    ) -> str:
        """
        Save intermediate draft content during writing/editing phases

        Args:
            content: Draft content to save
            phase: Current phase (writing, editing, etc.)
            section: Optional section name being worked on (for metadata only)
            agent: Agent creating the draft

        Returns:
            Path to the saved draft
        """
        # FIX: Use session ID + counter format
        self.file_counter += 1

        filename = f"{self.task_id}_{agent}_draft_{self.file_counter:04d}.md"
        phase_dir = self._get_phase_directory(phase)

        # FIX: Ensure directory exists
        os.makedirs(phase_dir, exist_ok=True)

        filepath = os.path.join(phase_dir, filename)

        # Ensure content is a string for writing to file
        if isinstance(content, str):
            content_to_write = content
        else:
            # If content is not a string (e.g., dict), convert to JSON string
            import json

            content_to_write = json.dumps(content, indent=2, ensure_ascii=False)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_to_write)

        # Update metadata
        # Handle case where content might be a dict instead of string
        try:
            if isinstance(content, str):
                word_count = len(content.split())
            else:
                # If content is not a string, convert it and count words
                content_str = str(content) if content else ""
                word_count = len(content_str.split())
        except Exception:
            word_count = 0

        self._update_metadata(
            agent,
            phase,
            filepath,
            section,
            {"type": "intermediate_draft", "word_count": word_count},
        )

        return filepath

    def save_human_feedback(self, feedback: str, context: Optional[Dict] = None) -> str:
        """
        Save human feedback and context

        Args:
            feedback: Human feedback content
            context: Optional context about what was being reviewed

        Returns:
            Path to the saved feedback file
        """
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_human_feedback.json"

        feedback_dir = os.path.join(self.drafts_dir, "human_feedback")
        filepath = os.path.join(feedback_dir, filename)

        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "context": context or {},
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)

        # Update metadata
        self._update_metadata("human", "feedback", filepath, None, {"type": "human_feedback"})

        return filepath

    def save_revision_history(
        self, original: str, revised: str, changes: str, agent: str = "reviser"
    ) -> str:
        """
        Save revision history showing changes made

        Args:
            original: Original content before revision
            revised: Revised content after changes
            changes: Description of changes made
            agent: Agent that made the revisions

        Returns:
            Path to the saved revision file
        """
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_{agent}_revision.json"

        revisions_dir = os.path.join(self.drafts_dir, "revisions")
        filepath = os.path.join(revisions_dir, filename)

        # Handle case where original/revised might be dicts instead of strings
        try:
            if isinstance(original, str):
                word_count_original = len(original.split())
            else:
                original_str = str(original) if original else ""
                word_count_original = len(original_str.split())
        except Exception:
            word_count_original = 0

        try:
            if isinstance(revised, str):
                word_count_revised = len(revised.split())
            else:
                revised_str = str(revised) if revised else ""
                word_count_revised = len(revised_str.split())
        except Exception:
            word_count_revised = 0

        revision_data = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "changes_description": changes,
            "original_content": original,
            "revised_content": revised,
            "word_count_original": word_count_original,
            "word_count_revised": word_count_revised,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(revision_data, f, indent=2, ensure_ascii=False)

        # Update metadata
        self._update_metadata(
            agent, "revisions", filepath, None, {"type": "revision_history", "changes": changes}
        )

        return filepath

    def get_phase_history(self, phase: str) -> List[Dict]:
        """
        Get history of all outputs for a specific phase

        Args:
            phase: Phase name to get history for

        Returns:
            List of output records for the phase
        """
        phase_outputs = []
        for agent, agent_data in self.metadata["agent_outputs"].items():
            if phase in agent_data:
                for output in agent_data[phase]:
                    output["agent"] = agent
                    phase_outputs.append(output)

        # Sort by timestamp
        phase_outputs.sort(key=lambda x: x.get("timestamp", ""))
        return phase_outputs

    def get_agent_history(self, agent: str) -> List[Dict]:
        """
        Get complete history of outputs from a specific agent

        Args:
            agent: Agent name to get history for

        Returns:
            List of all outputs from the agent
        """
        if agent not in self.metadata["agent_outputs"]:
            return []

        agent_outputs = []
        for phase, outputs in self.metadata["agent_outputs"][agent].items():
            for output in outputs:
                output["phase"] = phase
                agent_outputs.append(output)

        # Sort by timestamp
        agent_outputs.sort(key=lambda x: x.get("timestamp", ""))
        return agent_outputs

    def create_phase_summary(self, phase: str) -> str:
        """
        Create a summary file for a complete phase

        Args:
            phase: Phase to create summary for

        Returns:
            Path to the summary file
        """
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{timestamp}_phase_summary.md"
        phase_dir = self._get_phase_directory(phase)
        filepath = os.path.join(phase_dir, filename)

        phase_history = self.get_phase_history(phase)

        summary_content = f"# Phase Summary: {phase.title()}\n\n"
        summary_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        summary_content += f"**Total Outputs:** {len(phase_history)}\n\n"

        if phase_history:
            summary_content += "## Outputs Created:\n\n"
            for output in phase_history:
                summary_content += (
                    f"- **{output['agent']}** ({output['timestamp']}): {output['filepath']}\n"
                )
                if output.get("step"):
                    summary_content += f"  - Step: {output['step']}\n"
                if output.get("metadata"):
                    summary_content += f"  - Metadata: {output['metadata']}\n"
                summary_content += "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary_content)

        return filepath

    def save_metadata(self) -> str:
        """
        Save the complete metadata file

        Returns:
            Path to the metadata file
        """
        metadata_path = os.path.join(self.drafts_dir, "metadata.json")

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False, default=str)

        return metadata_path

    def _get_phase_directory(self, phase: str) -> str:
        """Get the directory path for a specific phase"""
        phase_mapping = {
            "initial_research": "1_initial_research",
            "planning": "2_planning",
            "parallel_research": "3_parallel_research",
            "writing": "4_writing",
            "translation": "5_translation",
            "editing": "6_editing",
            "publishing": "7_publishing",
            "feedback": "human_feedback",
            "revisions": "revisions",
            "workflow_completion": "workflow_completion",
            "error_handling": "error_handling",  # FIX: Map error_handling phase
        }

        phase_dir = phase_mapping.get(phase, phase)
        return os.path.join(self.drafts_dir, phase_dir)

    def _update_metadata(
        self, agent: str, phase: str, filepath: str, step: Optional[str], metadata: Optional[Dict]
    ):
        """Update the metadata tracking"""
        if agent not in self.metadata["agent_outputs"]:
            self.metadata["agent_outputs"][agent] = {}

        if phase not in self.metadata["agent_outputs"][agent]:
            self.metadata["agent_outputs"][agent][phase] = []

        output_record = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "step": step,
            "metadata": metadata or {},
        }

        self.metadata["agent_outputs"][agent][phase].append(output_record)

        # Track phases
        if phase not in self.metadata["phases"]:
            self.metadata["phases"].append(phase)

        # Auto-save metadata
        self.save_metadata()

    def _clean_state_for_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clean research state for JSON serialization"""
        clean_state = {}

        for key, value in state.items():
            try:
                if value is None:
                    clean_state[key] = None
                elif isinstance(value, (str, int, float, bool)):
                    clean_state[key] = value
                elif isinstance(value, (list, dict)):
                    clean_state[key] = value
                else:
                    # Convert complex objects to string representation
                    clean_state[key] = str(value)
            except Exception:
                # If all else fails, convert to string
                clean_state[key] = str(value)

        return clean_state

    def cleanup_old_drafts(self, keep_last_n: int = 10):
        """
        Clean up old draft files, keeping only the most recent ones

        Args:
            keep_last_n: Number of most recent files to keep per phase
        """
        for phase_dir in os.listdir(self.drafts_dir):
            phase_path = os.path.join(self.drafts_dir, phase_dir)
            if not os.path.isdir(phase_path):
                continue

            files = []
            for file in os.listdir(phase_path):
                file_path = os.path.join(phase_path, file)
                if os.path.isfile(file_path):
                    files.append((file_path, os.path.getmtime(file_path)))

            # Sort by modification time (newest first)
            files.sort(key=lambda x: x[1], reverse=True)

            # Remove old files beyond keep_last_n
            for file_path, _ in files[keep_last_n:]:
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # Ignore errors during cleanup
