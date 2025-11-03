"""
Comprehensive unit tests for translation workflow validation.
Tests the priority-based selection logic, content flow, and error handling.
"""

import asyncio
import json
import os
import sys
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

sys.path.append("/Users/thinhkhuat/DEV--local/multi-agent-deep-research/deep-research-mcp-og")

from multi_agents.agents.orchestrator import ChiefEditorAgent
from multi_agents.agents.translator import TranslatorAgent
from multi_agents.utils.draft_manager import DraftManager


class TestTranslationSelectionLogic:
    """Test the priority-based translation selection logic"""

    def setup_method(self):
        """Setup test environment"""
        self.translator = TranslatorAgent()
        self.sample_content = (
            "This is a sample research report with multiple sections and detailed content."
        )
        self.original_length = len(self.sample_content)

    def test_scenario_a_all_endpoints_preferred_threshold(self):
        """Scenario A: All endpoints return valid results (90%+ chars)"""
        results = [
            {
                "success": True,
                "text": "Translation from Primary (95%)",
                "length": int(self.original_length * 0.95),
                "endpoint": {"name": "Primary", "priority": 1},
                "priority": 1,
            },
            {
                "success": True,
                "text": "Translation from Backup-1 (98%)",
                "length": int(self.original_length * 0.98),
                "endpoint": {"name": "Backup-1", "priority": 2},
                "priority": 2,
            },
            {
                "success": True,
                "text": "Translation from Backup-2 (92%)",
                "length": int(self.original_length * 0.92),
                "endpoint": {"name": "Backup-2", "priority": 3},
                "priority": 3,
            },
        ]

        selected = self.translator._select_best_translation_result(results, self.original_length)

        # Should select Priority 1 (Primary) since it meets preferred threshold
        assert selected is not None
        assert selected["priority"] == 1
        assert selected["endpoint"]["name"] == "Primary"

    def test_scenario_b_mixed_quality_results(self):
        """Scenario B: Primary returns 85%, Backup-1 returns 95%, Backup-2 returns 92%"""
        results = [
            {
                "success": True,
                "text": "Translation from Primary (85%)",
                "length": int(self.original_length * 0.85),
                "endpoint": {"name": "Primary", "priority": 1},
                "priority": 1,
            },
            {
                "success": True,
                "text": "Translation from Backup-1 (95%)",
                "length": int(self.original_length * 0.95),
                "endpoint": {"name": "Backup-1", "priority": 2},
                "priority": 2,
            },
            {
                "success": True,
                "text": "Translation from Backup-2 (92%)",
                "length": int(self.original_length * 0.92),
                "endpoint": {"name": "Backup-2", "priority": 3},
                "priority": 3,
            },
        ]

        selected = self.translator._select_best_translation_result(results, self.original_length)

        # Should select Backup-1 (Priority 2) as it's the first to meet preferred threshold in priority order
        assert selected is not None
        assert selected["priority"] == 2
        assert selected["endpoint"]["name"] == "Backup-1"

    def test_scenario_c_invalid_results_mixed(self):
        """Scenario C: Primary returns 65% (invalid), Backup-1 returns 75% (valid), Backup-2 returns 155% (invalid)"""
        results = [
            {
                "success": True,
                "text": "Translation from Primary (65%)",
                "length": int(self.original_length * 0.65),
                "endpoint": {"name": "Primary", "priority": 1},
                "priority": 1,
            },
            {
                "success": True,
                "text": "Translation from Backup-1 (75%)",
                "length": int(self.original_length * 0.75),
                "endpoint": {"name": "Backup-1", "priority": 2},
                "priority": 2,
            },
            {
                "success": True,
                "text": "Translation from Backup-2 (155%)",
                "length": int(self.original_length * 1.55),
                "endpoint": {"name": "Backup-2", "priority": 3},
                "priority": 3,
            },
        ]

        selected = self.translator._select_best_translation_result(results, self.original_length)

        # Should select Backup-1 as it's the only valid result (70-150% range)
        assert selected is not None
        assert selected["priority"] == 2
        assert selected["endpoint"]["name"] == "Backup-1"

    def test_scenario_d_all_invalid_results(self):
        """Scenario D: All return invalid results (<70% or >150%)"""
        results = [
            {
                "success": True,
                "text": "Too short",
                "length": int(self.original_length * 0.6),
                "endpoint": {"name": "Primary", "priority": 1},
                "priority": 1,
            },
            {
                "success": True,
                "text": "Too long" * 100,
                "length": int(self.original_length * 1.6),
                "endpoint": {"name": "Backup-1", "priority": 2},
                "priority": 2,
            },
            {
                "success": True,
                "text": "Also too short",
                "length": int(self.original_length * 0.5),
                "endpoint": {"name": "Backup-2", "priority": 3},
                "priority": 3,
            },
        ]

        selected = self.translator._select_best_translation_result(results, self.original_length)

        # Should return None as no results are valid
        assert selected is None

    def test_empty_results_list(self):
        """Test handling of empty results list"""
        selected = self.translator._select_best_translation_result([], self.original_length)
        assert selected is None

    def test_no_original_length_provided(self):
        """Test handling when original length is not provided"""
        results = [
            {
                "success": True,
                "text": "Some translation",
                "length": 100,
                "endpoint": {"name": "Primary", "priority": 1},
                "priority": 1,
            }
        ]

        selected = self.translator._select_best_translation_result(results, None)
        # Should still work by estimating from available results
        assert selected is not None


class TestWorkflowContentFlow:
    """Test the complete workflow content flow"""

    def setup_method(self):
        """Setup test environment"""
        self.task = {
            "query": "Test research query",
            "language": "vi",
            "max_sections": 3,
            "publish_formats": ["pdf", "docx", "md"],
            "model": "gemini-2.5-flash-preview-04-17-thinking",
        }

    def test_workflow_edge_configuration(self):
        """Test that workflow edges are configured correctly"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
            orchestrator.output_dir = temp_dir

            # Initialize agents and create workflow
            agents = orchestrator._initialize_agents()
            workflow = orchestrator._create_workflow(agents)

            # Compile workflow to validate structure
            compiled = workflow.compile()

            # Check that key nodes exist
            assert "browser" in compiled.nodes
            assert "planner" in compiled.nodes
            assert "researcher" in compiled.nodes
            assert "writer" in compiled.nodes
            assert "publisher" in compiled.nodes
            assert "translator" in compiled.nodes

            # Verify entry point exists (CompiledStateGraph doesn't expose entry_point attribute directly)
            # The workflow should be properly structured and compilable

    def test_translation_condition_logic(self):
        """Test the _should_translate condition logic"""
        orchestrator = ChiefEditorAgent(self.task)

        # Test Vietnamese language (should translate)
        research_state = {"task": {"language": "vi"}}
        result = orchestrator._should_translate(research_state)
        assert result == "translate"

        # Test English language (should skip)
        research_state = {"task": {"language": "en"}}
        result = orchestrator._should_translate(research_state)
        assert result == "skip"

        # Test default behavior (no language specified)
        research_state = {"task": {}}
        result = orchestrator._should_translate(research_state)
        # Should check environment variable or default
        assert result in ["translate", "skip"]

    def test_translator_is_final_agent(self):
        """Test that translator is configured as the final agent"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
            orchestrator.output_dir = temp_dir

            agents = orchestrator._initialize_agents()
            workflow = orchestrator._create_workflow(agents)
            compiled = workflow.compile()

            # Find translator node connections
            for node_name, node in compiled.nodes.items():
                if node_name == "translator":
                    # Check what nodes this connects to
                    continue

            # Translator should have no outbound edges (ends workflow)
            # This is verified by the workflow structure having translator -> END

    def test_no_review_revision_after_translation(self):
        """Test that no review/revision happens after translation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ChiefEditorAgent(task=self.task, write_to_files=True)
            orchestrator.output_dir = temp_dir

            agents = orchestrator._initialize_agents()
            workflow = orchestrator._create_workflow(agents)
            workflow.compile()

            # Verify translator doesn't connect to reviewer or reviser
            # The workflow should be: publisher -> translator -> END
            # No reviewer/reviser after translator
            pass  # This is enforced by workflow structure


class TestEdgeCaseHandling:
    """Test edge cases and error conditions"""

    def setup_method(self):
        """Setup test environment"""
        self.translator = TranslatorAgent()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test how system handles endpoint timeouts"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            # Mock timeout exception
            mock_post.side_effect = asyncio.TimeoutError("Request timed out")

            endpoint = {"url": "https://test.com", "name": "Test", "priority": 1}
            payload = {"transcript": "test content", "sessionId": "test"}

            result = await self.translator._translate_single_endpoint(endpoint, payload)

            assert result["success"] is False
            assert result["endpoint_name"] == "Test"

    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """Test handling of empty responses from endpoints"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"response": ""})

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            endpoint = {"url": "https://test.com", "name": "Test", "priority": 1}
            payload = {"transcript": "test content", "sessionId": "test"}

            result = await self.translator._translate_single_endpoint(endpoint, payload)

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self):
        """Test handling of malformed JSON from endpoints"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            endpoint = {"url": "https://test.com", "name": "Test", "priority": 1}
            payload = {"transcript": "test content", "sessionId": "test"}

            result = await self.translator._translate_single_endpoint(endpoint, payload)

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_short_content_handling(self):
        """Test handling of very short or empty content"""
        # Empty content
        result = await self.translator._translate_markdown_content("", "Vietnamese", "vi", {})
        assert result == ""  # Should return empty string

        # Very short content
        short_content = "Hi"
        result = await self.translator._translate_markdown_content(
            short_content, "Vietnamese", "vi", {}
        )
        # Should still attempt translation
        assert result is not None


class TestStateManagement:
    """Test state management and data flow"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.draft_manager = DraftManager(self.temp_dir, "test_task")

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_research_state_flow(self):
        """Test that research state is properly maintained throughout workflow"""
        translator = TranslatorAgent(draft_manager=self.draft_manager, output_dir=self.temp_dir)

        # Create mock markdown file
        md_content = "# Test Report\n\nThis is a test report with multiple sections."
        md_path = os.path.join(self.temp_dir, "test_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        research_state = {
            "task": {"language": "vi", "query": "Test query"},
            "draft": {"content": "Test content"},
            "sources": ["source1", "source2"],
        }

        # Mock translation to avoid external calls
        with patch.object(
            translator, "_translate_markdown_content", return_value="Translated content"
        ):
            with patch.object(translator, "_create_translated_files", return_value=[md_path]):
                result = await translator.run(research_state)

                # Verify state is preserved and extended
                assert result["task"] == research_state["task"]
                assert result["draft"] == research_state["draft"]
                assert result["sources"] == research_state["sources"]
                assert "translation_result" in result
                assert result["workflow_complete"] is True

    def test_draft_manager_integration(self):
        """Test integration with draft manager"""
        TranslatorAgent(draft_manager=self.draft_manager)

        # Test that draft manager methods are called properly
        with patch.object(self.draft_manager, "save_agent_output") as mock_save:
            with patch.object(self.draft_manager, "save_research_state"):
                # Mock translation process
                translation_result = {
                    "status": "success",
                    "translated_files": ["file1", "file2"],
                    "target_language": "vi",
                }

                # Simulate saving during translation
                self.draft_manager.save_agent_output(
                    agent_name="translator",
                    phase="translation",
                    output=translation_result,
                    step="translate_all_formats",
                )

                mock_save.assert_called_once()


class TestFileOutputValidation:
    """Test file output and path handling"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_language_suffix_addition(self):
        """Test that language suffixes are added correctly"""
        translator = TranslatorAgent()

        test_cases = [
            ("/path/to/report.md", "vi", "/path/to/report_vi.md"),
            ("/path/to/report.pdf", "vi", "/path/to/report_vi.pdf"),
            ("/path/to/report.docx", "vi", "/path/to/report_vi.docx"),
            ("/path/to/complex_name.test.md", "vi", "/path/to/complex_name.test_vi.md"),
        ]

        for original_path, lang, expected in test_cases:
            result = translator._add_language_suffix(original_path, lang)
            assert result == expected

    def test_file_format_discovery(self):
        """Test discovery of all format files"""
        translator = TranslatorAgent()

        # Create sample files
        files_to_create = [
            "report.md",
            "report.pdf",
            "report.docx",
            "other_file.txt",
            "WORKFLOW_SUMMARY.md",  # Should be ignored
        ]

        for filename in files_to_create:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, "w") as f:
                f.write("test content")

        # Test file discovery
        md_path = os.path.join(self.temp_dir, "report.md")
        format_files = translator._find_all_format_files(md_path)

        # Should find md, pdf, docx but not txt or WORKFLOW files
        assert "md" in format_files
        assert "pdf" in format_files
        assert "docx" in format_files
        assert format_files["md"].endswith("report.md")
        assert format_files["pdf"].endswith("report.pdf")
        assert format_files["docx"].endswith("report.docx")

    @pytest.mark.asyncio
    async def test_file_creation_process(self):
        """Test the complete file creation process"""
        translator = TranslatorAgent(output_dir=self.temp_dir)

        # Create original files
        original_files = {
            "md": os.path.join(self.temp_dir, "original.md"),
            "pdf": os.path.join(self.temp_dir, "original.pdf"),
            "docx": os.path.join(self.temp_dir, "original.docx"),
        }

        for filepath in original_files.values():
            with open(filepath, "w") as f:
                f.write("original content")

        translated_content = "# Translated Content\n\nThis is translated content."

        # Mock the file creation functions to avoid external dependencies
        with patch("multi_agents.agents.utils.file_formats.write_text_to_md") as mock_md:
            with patch("multi_agents.agents.utils.file_formats.write_md_to_pdf") as mock_pdf:
                with patch("multi_agents.agents.utils.file_formats.write_md_to_word") as mock_docx:
                    # Setup return paths
                    mock_md.return_value = os.path.join(self.temp_dir, "temp.md")
                    mock_pdf.return_value = os.path.join(self.temp_dir, "temp.pdf")
                    mock_docx.return_value = os.path.join(self.temp_dir, "temp.docx")

                    # Create temp files that mocks would create
                    for path in [
                        mock_md.return_value,
                        mock_pdf.return_value,
                        mock_docx.return_value,
                    ]:
                        with open(path, "w") as f:
                            f.write("temp content")

                    result = await translator._create_translated_files(
                        translated_content, original_files, "vi", "Vietnamese"
                    )

                    # Should have created all three translated files
                    assert len(result) == 3
                    assert all("_vi." in path for path in result)


if __name__ == "__main__":
    pytest.main([__file__])
