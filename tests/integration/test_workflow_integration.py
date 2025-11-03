"""
Integration tests for the complete translation workflow.
Tests the actual workflow execution and agent coordination.
"""

import asyncio
import os
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.append("/Users/thinhkhuat/DEV--local/multi-agent-deep-research/deep-research-mcp-og")

from multi_agents.agents.orchestrator import ChiefEditorAgent
from multi_agents.agents.translator import TranslatorAgent
from multi_agents.utils.draft_manager import DraftManager


class TestWorkflowIntegration:
    """Integration tests for the complete workflow"""

    def setup_method(self):
        """Setup test environment"""
        self.task = {
            "query": "Integration test research query",
            "language": "vi",
            "max_sections": 2,
            "publish_formats": ["md", "pdf", "docx"],
            "model": "gemini-2.5-flash-preview-04-17-thinking",
            "guidelines": ["Use reliable sources", "Include citations"],
        }
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_publisher_to_translator_flow(self):
        """Test the complete flow from publisher to translator"""

        # Setup orchestrator with file output
        orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
        orchestrator.output_dir = self.temp_dir
        orchestrator.draft_manager = DraftManager(self.temp_dir, "integration_test")

        # Initialize agents
        agents = orchestrator._initialize_agents()
        publisher = agents["publisher"]
        translator = agents["translator"]

        # Mock research state with completed content
        research_state = {
            "task": self.task,
            "draft": {
                "content": "# Integration Test Report\n\nThis is a comprehensive test report with multiple sections.\n\n## Section 1\n\nDetailed content here.\n\n## Section 2\n\nMore detailed content here.\n\n## Conclusion\n\nSummary of findings.",
                "structure": ["Introduction", "Section 1", "Section 2", "Conclusion"],
            },
            "sources": [
                {"url": "https://example.com/source1", "title": "Test Source 1"},
                {"url": "https://example.com/source2", "title": "Test Source 2"},
            ],
            "sections": [
                {"title": "Section 1", "content": "Section 1 content"},
                {"title": "Section 2", "content": "Section 2 content"},
            ],
        }

        # Mock external dependencies for publisher
        with patch("multi_agents.agents.utils.file_formats.write_text_to_md") as mock_md:
            with patch("multi_agents.agents.utils.file_formats.write_md_to_pdf") as mock_pdf:
                with patch("multi_agents.agents.utils.file_formats.write_md_to_word") as mock_docx:
                    # Setup publisher file creation
                    md_path = os.path.join(self.temp_dir, "report.md")
                    pdf_path = os.path.join(self.temp_dir, "report.pdf")
                    docx_path = os.path.join(self.temp_dir, "report.docx")

                    mock_md.return_value = md_path
                    mock_pdf.return_value = pdf_path
                    mock_docx.return_value = docx_path

                    # Create the actual files that would be generated
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(research_state["draft"]["content"])
                    with open(pdf_path, "wb") as f:
                        f.write(b"PDF content")
                    with open(docx_path, "wb") as f:
                        f.write(b"DOCX content")

                    # Run publisher
                    publisher_result = await publisher.run(research_state)

                    # Verify publisher created files
                    assert "published_files" in publisher_result
                    assert len(publisher_result["published_files"]) == 3

                    # Mock translation process
                    with patch.object(translator, "_translate_markdown_content") as mock_translate:
                        mock_translate.return_value = "# Báo Cáo Kiểm Tra Tích Hợp\n\nĐây là báo cáo kiểm tra toàn diện với nhiều phần."

                        # Run translator
                        translator_result = await translator.run(publisher_result)

                        # Verify translation completed
                        assert "translation_result" in translator_result
                        assert translator_result["workflow_complete"] is True

                        # Verify translation was called
                        mock_translate.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self):
        """Test that workflow state is properly persisted between agents"""

        orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
        orchestrator.output_dir = self.temp_dir
        orchestrator.draft_manager = DraftManager(self.temp_dir, "persistence_test")

        # Create initial state
        initial_state = {
            "task": self.task,
            "query_analysis": "Test analysis",
            "research_data": {"key": "value"},
            "draft": {"content": "Test content"},
        }

        # Save state through draft manager
        orchestrator.draft_manager.save_research_state("test_phase", initial_state)

        # Verify state was saved
        saved_files = os.listdir(orchestrator.draft_manager.drafts_dir)
        assert any("research_state" in f for f in saved_files)

    def test_translation_condition_integration(self):
        """Test translation condition logic in workflow context"""

        orchestrator = ChiefEditorAgent(self.task)

        # Test cases for different language configurations
        test_cases = [
            ({"task": {"language": "vi"}}, "translate"),
            ({"task": {"language": "en"}}, "skip"),
            ({"task": {"language": "fr"}}, "translate"),
            ({"task": {}}, "translate"),  # Default is Vietnamese in this environment
        ]

        for state, expected in test_cases:
            result = orchestrator._should_translate(state)
            assert result == expected

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test error recovery during workflow execution"""

        orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
        orchestrator.output_dir = self.temp_dir

        # Create a scenario where translation fails
        agents = orchestrator._initialize_agents()
        translator = agents["translator"]

        research_state = {
            "task": self.task,
            "draft": {"content": "Test content for error recovery"},
        }

        # Mock translation failure
        with patch.object(translator, "_translate_markdown_content", return_value=None):
            with patch("os.listdir", return_value=["test.md"]):
                with patch("builtins.open", mock_open_with_content("Test content")):
                    result = await translator.translate_report_file(research_state)

                    # Should handle error gracefully
                    assert result["status"] == "error"
                    assert "message" in result


def mock_open_with_content(content):
    """Helper function to mock file open with specific content"""
    from unittest.mock import mock_open

    return mock_open(read_data=content)


class TestConcurrentTranslation:
    """Integration tests for concurrent translation endpoints"""

    def setup_method(self):
        """Setup test environment"""
        self.translator = TranslatorAgent()

    @pytest.mark.asyncio
    async def test_concurrent_endpoint_calls(self):
        """Test that concurrent endpoint calls work correctly"""

        # Mock multiple endpoint responses
        async def mock_endpoint_1(endpoint, payload):
            await asyncio.sleep(0.1)  # Simulate network delay
            return {
                "success": True,
                "text": "Translation from endpoint 1",
                "length": 100,
                "endpoint_name": "Primary",
            }

        async def mock_endpoint_2(endpoint, payload):
            await asyncio.sleep(0.2)  # Simulate slower response
            return {
                "success": True,
                "text": "Translation from endpoint 2",
                "length": 120,
                "endpoint_name": "Backup-1",
            }

        async def mock_endpoint_3(endpoint, payload):
            await asyncio.sleep(0.05)  # Simulate fastest response
            return {
                "success": True,
                "text": "Translation from endpoint 3",
                "length": 90,
                "endpoint_name": "Backup-2",
            }

        # Patch the single endpoint method to return different results
        mock_responses = [mock_endpoint_1, mock_endpoint_2, mock_endpoint_3]

        with patch.object(
            self.translator, "_translate_single_endpoint", side_effect=mock_responses
        ):
            result = await self.translator._translate_chunk_concurrent(
                "Test content for concurrent translation", "Vietnamese", "vi", {}
            )

            # Should return the primary endpoint result (priority 1)
            assert result == "Translation from endpoint 1"

    @pytest.mark.asyncio
    async def test_concurrent_with_failures(self):
        """Test concurrent translation with some endpoint failures"""

        async def mock_failing_endpoint(endpoint, payload):
            return {"success": False, "endpoint_name": "Primary"}

        async def mock_working_endpoint(endpoint, payload):
            return {
                "success": True,
                "text": "Translation from backup",
                "length": 100,
                "endpoint_name": "Backup-1",
            }

        async def mock_timeout_endpoint(endpoint, payload):
            raise asyncio.TimeoutError("Endpoint timed out")

        mock_responses = [mock_failing_endpoint, mock_working_endpoint, mock_timeout_endpoint]

        with patch.object(
            self.translator, "_translate_single_endpoint", side_effect=mock_responses
        ):
            result = await self.translator._translate_chunk_concurrent(
                "Test content", "Vietnamese", "vi", {}
            )

            # Should return the working backup endpoint result
            assert result == "Translation from backup"


class TestMemoryIntegration:
    """Integration tests for memory and state management"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.draft_manager = DraftManager(self.temp_dir, "memory_test")

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_draft_manager_workflow_tracking(self):
        """Test that draft manager correctly tracks workflow progress"""

        # Simulate workflow progress
        phases = ["initial_research", "planning", "parallel_research", "writing", "translation"]

        for phase in phases:
            self.draft_manager.save_agent_output(
                agent_name="test_agent",
                phase=phase,
                output={"phase": phase, "data": f"Data for {phase}"},
                step=f"{phase}_step",
            )

        # Verify all phases were tracked
        for phase in phases:
            phase_history = self.draft_manager.get_phase_history(phase)
            assert len(phase_history) > 0

    def test_memory_persistence_across_agents(self):
        """Test that memory persists correctly across different agents"""

        # Agent 1 saves state
        state_1 = {
            "agent": "publisher",
            "files_created": ["file1.md", "file1.pdf"],
            "timestamp": "2024-01-01T10:00:00",
        }

        self.draft_manager.save_research_state("publishing", state_1)

        # Agent 2 saves state
        state_2 = {
            "agent": "translator",
            "translation_status": "completed",
            "files_translated": ["file1_vi.md", "file1_vi.pdf"],
        }

        self.draft_manager.save_research_state("translation", state_2)

        # Verify both states are accessible
        assert os.path.exists(os.path.join(self.draft_manager.drafts_dir, "2_publishing"))
        assert os.path.exists(os.path.join(self.draft_manager.drafts_dir, "5_translation"))

    @pytest.mark.asyncio
    async def test_workflow_completion_tracking(self):
        """Test that workflow completion is properly tracked"""

        orchestrator = ChiefEditorAgent(
            task={"query": "Test completion tracking", "language": "vi"}, write_to_files=True
        )
        orchestrator.output_dir = self.temp_dir
        orchestrator.draft_manager = self.draft_manager

        # Simulate workflow completion
        final_result = {
            "task": {"query": "Test completion tracking", "language": "vi"},
            "translation_result": {"status": "success"},
            "workflow_complete": True,
        }

        # Save completion state
        orchestrator.draft_manager.save_agent_output(
            agent_name="orchestrator",
            phase="workflow_completion",
            output=final_result,
            step="final_result",
            metadata={"workflow_completed": True, "total_phases": 6},
        )

        # Create workflow summary
        orchestrator._create_workflow_summary()

        # Verify summary was created
        summary_path = os.path.join(self.draft_manager.drafts_dir, "WORKFLOW_SUMMARY.md")
        assert os.path.exists(summary_path)

        with open(summary_path, "r", encoding="utf-8") as f:
            summary_content = f.read()
            assert "Research Workflow Summary" in summary_content
            assert "Test completion tracking" in summary_content


if __name__ == "__main__":
    pytest.main([__file__])
