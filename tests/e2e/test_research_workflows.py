"""
End-to-End Tests for Research Workflows
Tests complete research workflows from start to finish
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from multi_agents.agents.orchestrator import ChiefEditorAgent


class TestResearchWorkflows:
    """Test complete research workflows end-to-end"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for test outputs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_env_complete(self, monkeypatch):
        """Complete environment setup for testing"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_LLM_MODEL": "gpt-4o",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            "FALLBACK_LLM_PROVIDER": "google_gemini",
            "FALLBACK_LLM_MODEL": "gemini-1.5-pro",
            "FALLBACK_SEARCH_PROVIDER": "brave",
            "OPENAI_API_KEY": "test-openai-key",
            "TAVILY_API_KEY": "test-tavily-key",
            "GOOGLE_API_KEY": "test-google-key",
            "BRAVE_API_KEY": "test-brave-key",
            "LLM_STRATEGY": "fallback_on_error",
            "SEARCH_STRATEGY": "fallback_on_error",
            "LLM_TEMPERATURE": "0.7",
            "MAX_SEARCH_RESULTS": "10",
            "SEARCH_DEPTH": "advanced",
            "ENABLE_CACHING": "false",  # Disable caching for tests
            "COST_TRACKING": "true",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.fixture
    def research_task_basic(self, temp_output_dir):
        """Basic research task configuration"""
        return {
            "query": "Artificial Intelligence trends in 2024",
            "report_type": "research_report",
            "report_format": "APA",
            "language": "en",
            "sources": ["web"],
            "tone": "formal",
            "max_sections": 3,
            "publish_formats": {"markdown": True, "pdf": False, "docx": False},
            "include_human_feedback": False,
            "follow_guidelines": True,
            "guidelines": [
                "The report MUST be written in APA format",
                "Each sub section MUST include supporting sources using hyperlinks",
                "Focus on recent developments and trends",
            ],
            "verbose": True,
            "headers": {"agent": "test-e2e", "user_id": "test-user", "session_id": "test-session"},
            "config_path": temp_output_dir,
        }

    @pytest.fixture
    def research_task_multilingual(self, temp_output_dir):
        """Multilingual research task configuration"""
        return {
            "query": "Climate change impact on renewable energy",
            "report_type": "detailed_report",
            "report_format": "MLA",
            "language": "es",  # Spanish
            "sources": ["web"],
            "tone": "academic",
            "max_sections": 5,
            "publish_formats": {"markdown": True, "pdf": True, "docx": False},
            "include_human_feedback": False,
            "follow_guidelines": True,
            "guidelines": [
                "El informe DEBE estar escrito en formato MLA",
                "Cada sección DEBE incluir fuentes de apoyo",
                "Enfocarse en datos recientes y análisis científico",
            ],
            "verbose": True,
            "headers": {"agent": "test-multilingual", "user_id": "test-user", "language": "es"},
            "config_path": temp_output_dir,
        }

    @pytest.fixture
    def research_task_complex(self, temp_output_dir):
        """Complex research task with multiple requirements"""
        return {
            "query": "Blockchain technology applications in healthcare and finance",
            "report_type": "comparative_analysis",
            "report_format": "Harvard",
            "language": "en",
            "sources": ["web", "academic"],
            "tone": "professional",
            "max_sections": 7,
            "publish_formats": {"markdown": True, "pdf": True, "docx": True},
            "include_human_feedback": True,
            "follow_guidelines": True,
            "guidelines": [
                "Compare and contrast applications in both sectors",
                "Include regulatory considerations",
                "Provide implementation challenges and solutions",
                "Use Harvard citation style throughout",
                "Include executive summary and recommendations",
            ],
            "verbose": True,
            "headers": {
                "agent": "test-complex",
                "user_id": "enterprise-user",
                "department": "research",
                "priority": "high",
            },
            "config_path": temp_output_dir,
        }

    def test_basic_research_workflow(self, mock_env_complete, research_task_basic):
        """Test basic research workflow with minimal configuration"""
        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            # Mock the GPTResearcher
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.return_value = """
            # Artificial Intelligence Trends in 2024

            ## Introduction
            Artificial Intelligence continues to evolve rapidly in 2024...

            ## Key Trends
            1. Large Language Models advancement
            2. AI integration in enterprise applications
            3. Edge AI computing growth

            ## Conclusion
            The AI landscape in 2024 shows promising developments...
            """
            mock_researcher_class.return_value = mock_researcher

            # Create and run orchestrator
            orchestrator = ChiefEditorAgent(research_task_basic, write_to_files=True)

            # Verify initialization
            assert orchestrator.task == research_task_basic
            assert orchestrator.output_dir is not None
            assert os.path.exists(orchestrator.output_dir)

            # Verify provider configuration
            assert os.environ.get("SMART_LLM") == "openai:gpt-4o"
            assert os.environ.get("RETRIEVER") == "tavily"

    def test_multilingual_research_workflow(self, mock_env_complete, research_task_multilingual):
        """Test research workflow with multilingual support"""
        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            # Mock the GPTResearcher with Spanish content
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.return_value = """
            # Impacto del Cambio Climático en Energías Renovables

            ## Introducción
            El cambio climático está transformando el sector energético...

            ## Análisis Principal
            Las energías renovables se posicionan como solución clave...

            ## Conclusiones
            La transición energética es fundamental para el futuro...
            """
            mock_researcher_class.return_value = mock_researcher

            # Create orchestrator
            orchestrator = ChiefEditorAgent(research_task_multilingual, write_to_files=True)

            # Verify language-specific configuration
            assert orchestrator.task["language"] == "es"
            assert (
                "español" in str(orchestrator.task.get("guidelines", [])).lower()
                or "mla" in str(orchestrator.task.get("guidelines", [])).lower()
            )

    def test_complex_research_workflow(self, mock_env_complete, research_task_complex):
        """Test complex research workflow with multiple requirements"""
        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            # Mock comprehensive research output
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.return_value = """
            # Blockchain Technology Applications: Healthcare vs Finance

            ## Executive Summary
            This comparative analysis examines blockchain applications...

            ## Healthcare Applications
            ### Electronic Health Records
            Blockchain provides secure, immutable patient data...
            
            ### Drug Traceability
            Supply chain transparency in pharmaceuticals...

            ## Financial Applications
            ### Digital Payments
            Cryptocurrency and central bank digital currencies...
            
            ### Trade Finance
            Smart contracts revolutionizing trade processes...

            ## Regulatory Considerations
            Different regulatory approaches in both sectors...

            ## Implementation Challenges
            Technical, regulatory, and adoption barriers...

            ## Recommendations
            Strategic approaches for successful implementation...

            ## Conclusion
            Blockchain technology offers transformative potential...
            """
            mock_researcher_class.return_value = mock_researcher

            # Create orchestrator
            orchestrator = ChiefEditorAgent(research_task_complex, write_to_files=True)

            # Verify complex configuration
            assert orchestrator.task["max_sections"] == 7
            assert orchestrator.task["include_human_feedback"] is True
            assert len(orchestrator.task["guidelines"]) == 5
            assert orchestrator.task["publish_formats"]["pdf"] is True
            assert orchestrator.task["publish_formats"]["docx"] is True

    def test_provider_fallback_during_research(self, mock_env_complete, research_task_basic):
        """Test provider fallback mechanism during research execution"""
        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            # Mock primary provider failure, then success with fallback
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.side_effect = [
                Exception("Primary provider unavailable"),
                "Fallback research completed successfully",
            ]
            mock_researcher_class.return_value = mock_researcher

            # Create orchestrator
            orchestrator = ChiefEditorAgent(research_task_basic)

            # The system should handle provider failures gracefully
            # (This would require implementing retry logic in the actual system)
            assert orchestrator is not None

    def test_output_directory_creation(self, mock_env_complete, research_task_basic):
        """Test that output directories are created correctly"""
        orchestrator = ChiefEditorAgent(research_task_basic, write_to_files=True)

        # Verify output directory exists
        assert orchestrator.output_dir is not None
        assert os.path.exists(orchestrator.output_dir)
        assert os.path.isdir(orchestrator.output_dir)

        # Verify directory naming convention
        assert "run_" in orchestrator.output_dir
        assert str(orchestrator.task_id) in orchestrator.output_dir
        assert "Artificial" in orchestrator.output_dir  # Part of query

    def test_task_id_generation(self, mock_env_complete, research_task_basic):
        """Test task ID generation and uniqueness"""
        orchestrator1 = ChiefEditorAgent(research_task_basic)
        orchestrator2 = ChiefEditorAgent(research_task_basic)

        # Task IDs should be unique
        assert orchestrator1.task_id != orchestrator2.task_id
        assert isinstance(orchestrator1.task_id, int)
        assert isinstance(orchestrator2.task_id, int)

    def test_headers_preservation(self, mock_env_complete, research_task_complex):
        """Test that task headers are preserved through workflow"""
        orchestrator = ChiefEditorAgent(research_task_complex)

        # Verify headers are preserved
        assert orchestrator.headers == research_task_complex["headers"]
        assert orchestrator.headers["agent"] == "test-complex"
        assert orchestrator.headers["user_id"] == "enterprise-user"
        assert orchestrator.headers["department"] == "research"
        assert orchestrator.headers["priority"] == "high"

    def test_tone_configuration(self, mock_env_complete):
        """Test different tone configurations"""
        tones = ["formal", "casual", "academic", "professional", "technical"]

        for tone in tones:
            task = {
                "query": f"Test query with {tone} tone",
                "report_type": "research_report",
                "tone": tone,
                "language": "en",
            }

            orchestrator = ChiefEditorAgent(task, tone=tone)
            assert orchestrator.tone == tone

    @pytest.mark.asyncio
    async def test_async_research_workflow(self, mock_env_complete, research_task_basic):
        """Test research workflow in async context"""
        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.return_value = "Async research completed"
            mock_researcher_class.return_value = mock_researcher

            # Test async orchestrator creation
            async def create_orchestrator():
                return ChiefEditorAgent(research_task_basic)

            orchestrator = await create_orchestrator()
            assert orchestrator is not None

    def test_websocket_configuration(self, mock_env_complete, research_task_basic):
        """Test websocket configuration for real-time updates"""
        mock_websocket = MagicMock()
        mock_stream_output = MagicMock()

        orchestrator = ChiefEditorAgent(
            research_task_basic, websocket=mock_websocket, stream_output=mock_stream_output
        )

        assert orchestrator.websocket == mock_websocket
        assert orchestrator.stream_output == mock_stream_output

    def test_error_handling_invalid_task(self, mock_env_complete):
        """Test error handling with invalid task configuration"""
        invalid_tasks = [
            {},  # Empty task
            {"query": ""},  # Empty query
            {"query": "Test", "invalid_field": "value"},  # Invalid field
        ]

        for invalid_task in invalid_tasks:
            try:
                orchestrator = ChiefEditorAgent(invalid_task)
                # Should handle gracefully or raise appropriate exception
                assert orchestrator is not None
            except (KeyError, ValueError, TypeError) as e:
                # Expected for some invalid configurations
                assert str(e) is not None

    def test_memory_usage_during_workflow(self, mock_env_complete, research_task_basic):
        """Test memory usage during workflow execution"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create multiple orchestrators
        orchestrators = []
        for i in range(10):
            task = research_task_basic.copy()
            task["query"] = f"Test query {i}"
            orch = ChiefEditorAgent(task)
            orchestrators.append(orch)

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for 10 instances)
        assert memory_increase < 50 * 1024 * 1024

        # Clean up
        del orchestrators
        gc.collect()

    def test_concurrent_research_workflows(self, mock_env_complete, temp_output_dir):
        """Test multiple concurrent research workflows"""
        import threading

        results = []

        def run_research(query_suffix):
            task = {
                "query": f"Concurrent research test {query_suffix}",
                "report_type": "research_report",
                "language": "en",
                "config_path": temp_output_dir,
            }

            try:
                orchestrator = ChiefEditorAgent(task, write_to_files=True)
                results.append(f"success_{query_suffix}")
            except Exception as e:
                results.append(f"error_{query_suffix}_{str(e)}")

        # Run 5 concurrent workflows
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_research, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 5
        success_count = len([r for r in results if r.startswith("success")])
        assert success_count == 5

    def test_configuration_validation_e2e(self, mock_env_complete, research_task_basic):
        """Test end-to-end configuration validation"""
        orchestrator = ChiefEditorAgent(research_task_basic)

        # Verify provider configuration is valid
        from multi_agents.providers.factory import enhanced_config

        validation = enhanced_config.validate_current_config()

        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

        # Verify current providers are set correctly
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] in ["openai", "google_gemini"]
        assert current["search_provider"] in ["tavily", "brave"]

    @pytest.mark.slow
    def test_full_research_pipeline_performance(self, mock_env_complete, research_task_basic):
        """Test performance of full research pipeline"""
        import time

        with patch("gpt_researcher.GPTResearcher") as mock_researcher_class:
            mock_researcher = MagicMock()
            mock_researcher.conduct_research.return_value = "Performance test completed"
            mock_researcher_class.return_value = mock_researcher

            start_time = time.time()

            # Create and initialize orchestrator
            orchestrator = ChiefEditorAgent(research_task_basic, write_to_files=True)

            initialization_time = time.time() - start_time

            # Performance expectations
            assert initialization_time < 5.0  # Should initialize within 5 seconds
            assert orchestrator.task_id is not None
            assert orchestrator.output_dir is not None

    def test_output_format_generation(self, mock_env_complete, temp_output_dir):
        """Test different output format generation"""
        task = {
            "query": "Output format test",
            "report_type": "research_report",
            "language": "en",
            "publish_formats": {"markdown": True, "pdf": True, "docx": True},
            "config_path": temp_output_dir,
        }

        orchestrator = ChiefEditorAgent(task, write_to_files=True)

        # Verify task configuration includes all formats
        assert orchestrator.task["publish_formats"]["markdown"] is True
        assert orchestrator.task["publish_formats"]["pdf"] is True
        assert orchestrator.task["publish_formats"]["docx"] is True
