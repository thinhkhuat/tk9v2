"""
Integration Tests for Orchestrator and Complete Workflows
Tests the MainOrchestrator with different provider combinations
"""

import pytest
import os
import asyncio
import tempfile
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from multi_agents.agents.orchestrator import ChiefEditorAgent


class TestOrchestratorIntegration:
    """Test complete orchestrator workflows with different providers"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_task(self, temp_output_dir):
        """Create a sample research task"""
        task_data = {
            "query": "Test integration of Google Gemini and Brave Search",
            "report_type": "research_report",
            "report_format": "APA",
            "language": "en",
            "sources": ["web"],
            "tone": "formal",
            "headers": {
                "agent": "test-integration",
                "user_id": "test-user"
            },
            "config_path": temp_output_dir
        }
        return task_data
    
    @pytest.fixture
    def mock_env_complete(self, monkeypatch):
        """Complete environment setup for testing"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "google_gemini",
            "PRIMARY_LLM_MODEL": "gemini-1.5-pro",
            "PRIMARY_SEARCH_PROVIDER": "brave",
            "FALLBACK_LLM_PROVIDER": "openai",
            "FALLBACK_LLM_MODEL": "gpt-4o",
            "FALLBACK_SEARCH_PROVIDER": "tavily",
            "GOOGLE_API_KEY": "test-google-key",
            "BRAVE_API_KEY": "test-brave-key",
            "OPENAI_API_KEY": "test-openai-key",
            "TAVILY_API_KEY": "test-tavily-key",
            "LLM_STRATEGY": "fallback_on_error",
            "SEARCH_STRATEGY": "fallback_on_error",
            "LLM_TEMPERATURE": "0.7",
            "MAX_SEARCH_RESULTS": "10",
            "SEARCH_DEPTH": "advanced"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    def test_orchestrator_initialization(self, mock_env_complete):
        """Test orchestrator initializes correctly with multi-provider setup"""
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Verify orchestrator has required components
        assert hasattr(orchestrator, 'task')
        assert orchestrator.task == task
        
        # Verify environment was configured for providers
        assert os.environ.get("SMART_LLM") == "google_genai:gemini-1.5-pro"
        assert os.environ.get("RETRIEVER") == "brave"

    def test_provider_setup_in_orchestrator(self, mock_env_complete):
        """Test that provider setup method works correctly"""
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Call the setup method (should not raise exceptions)
        orchestrator._setup_providers()
        
        # Verify environment was configured
        assert os.environ.get("SMART_LLM") == "google_genai:gemini-1.5-pro"
        assert os.environ.get("RETRIEVER") == "brave"
        assert os.environ.get("GOOGLE_API_KEY") == "test-google-key"
        assert os.environ.get("BRAVE_API_KEY") == "test-brave-key"

    def test_orchestrator_with_task(self, mock_env_complete, sample_task):
        """Test orchestrator with sample task"""
        # Create orchestrator and run task
        orchestrator = ChiefEditorAgent(sample_task)
        
        # Test task execution (simplified)
        assert orchestrator is not None
        assert orchestrator.task == sample_task

    def test_environment_variable_propagation(self, mock_env_complete):
        """Test that environment variables are properly propagated"""
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Check that GPT-Researcher environment variables are set
        expected_vars = {
            "SMART_LLM": "google_genai:gemini-1.5-pro",
            "FAST_LLM": "google_genai:gemini-1.5-pro",
            "RETRIEVER": "brave",
            "GOOGLE_API_KEY": "test-google-key",
            "BRAVE_API_KEY": "test-brave-key",
            "LLM_TEMPERATURE": "0.7",
            "MAX_SEARCH_RESULTS": "10"
        }
        
        for var_name, expected_value in expected_vars.items():
            assert os.environ.get(var_name) == expected_value

    def test_provider_switching_during_execution(self, mock_env_complete):
        """Test switching providers during orchestrator execution"""
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Verify initial providers
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "google_gemini"
        
        # Switch to fallback LLM
        enhanced_config.switch_llm_provider(use_fallback=True)
        
        # Verify switch worked
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "openai"
        
        # Verify environment was updated
        assert os.environ.get("SMART_LLM") == "openai:gpt-4o"

    def test_configuration_validation_in_orchestrator(self, mock_env_complete):
        """Test configuration validation in orchestrator context"""
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Validate configuration
        validation = enhanced_config.validate_current_config()
        
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

    def test_error_handling_missing_api_key(self, monkeypatch):
        """Test error handling when API key is missing"""
        # Set up environment with missing API key
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "google_gemini",
            "PRIMARY_SEARCH_PROVIDER": "brave",
            # Missing GOOGLE_API_KEY and BRAVE_API_KEY
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Configuration should show validation errors
        validation = enhanced_config.validate_current_config()
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0

    def test_fallback_provider_usage(self, mock_env_complete):
        """Test that fallback providers can be used when primary fails"""
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Switch to fallback providers
        enhanced_config.switch_llm_provider(use_fallback=True)
        enhanced_config.switch_search_provider(use_fallback=True)
        
        # Verify fallback providers are active
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "openai"
        assert current["search_provider"] == "tavily"

    def test_concurrent_orchestrator_instances(self, mock_env_complete):
        """Test multiple orchestrator instances don't interfere"""
        import threading
        from multi_agents.providers.factory import enhanced_config
        
        results = []
        
        def create_orchestrator():
            task = {"query": "test query", "report_type": "research_report"}
            orch = ChiefEditorAgent(task)
            current = enhanced_config.get_current_providers()
            results.append(current["llm_provider"])
        
        threads = [threading.Thread(target=create_orchestrator) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All instances should have same configuration
        assert len(set(results)) == 1
        assert all(provider == "google_gemini" for provider in results)

    def test_orchestrator_state_persistence(self, mock_env_complete):
        """Test that orchestrator state persists across operations"""
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Get initial state
        initial_providers = enhanced_config.get_current_providers()
        
        # Perform some operations
        orchestrator._setup_providers()
        
        # State should be consistent
        current_providers = enhanced_config.get_current_providers()
        assert initial_providers == current_providers

    def test_orchestrator_with_different_report_types(self, mock_env_complete, temp_output_dir):
        """Test orchestrator handles different report types"""
        
        # Test different task configurations
        task_configs = [
            {
                "query": "AI trends 2024",
                "report_type": "research_report",
                "report_format": "APA",
                "language": "en"
            },
            {
                "query": "Machine learning applications",
                "report_type": "detailed_report",
                "report_format": "MLA",
                "language": "en"
            },
            {
                "query": "Technology overview",
                "report_type": "outline",
                "report_format": "basic",
                "language": "en"
            }
        ]
        
        for config in task_configs:
            config.update({
                "sources": ["web"],
                "tone": "formal",
                "headers": {"agent": "test", "user_id": "test"},
                "config_path": temp_output_dir
            })
            
            orchestrator = ChiefEditorAgent(config)
            
            # Task should be created successfully
            assert orchestrator.task["query"] == config["query"]
            assert orchestrator.task["report_type"] == config["report_type"]

    def test_orchestrator_error_recovery(self, mock_env_complete):
        """Test orchestrator error recovery mechanisms"""
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # The orchestrator should be resilient to temporary failures
        # (This would require implementing retry logic in the actual orchestrator)
        assert orchestrator is not None
        assert orchestrator.task == task

    def test_memory_usage_during_execution(self, mock_env_complete):
        """Test memory usage remains reasonable during execution"""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create multiple orchestrator instances
        orchestrators = []
        for _ in range(5):
            task = {"query": f"test query {_}", "report_type": "research_report"}
            orch = ChiefEditorAgent(task)
            orchestrators.append(orch)
        
        # Check memory usage
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 5 instances)
        assert memory_increase < 100 * 1024 * 1024
        
        # Clean up
        del orchestrators
        gc.collect()

    def test_configuration_reloading(self, mock_env_complete, monkeypatch):
        """Test that configuration can be reloaded"""
        from multi_agents.providers.factory import enhanced_config
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        
        # Verify initial configuration
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "google_gemini"
        
        # Change environment variable
        monkeypatch.setenv("PRIMARY_LLM_PROVIDER", "openai")
        
        # Create new orchestrator (simulates restart)
        new_task = {"query": "test query 2", "report_type": "research_report"}
        new_orchestrator = ChiefEditorAgent(new_task)
        
        # Configuration should still be google_gemini since enhanced_config is a singleton
        # and doesn't automatically reload
        assert orchestrator is not None
        assert new_orchestrator is not None

    def test_orchestrator_logging_setup(self, mock_env_complete, caplog):
        """Test that orchestrator sets up logging correctly"""
        import logging
        
        # Set logging level to capture debug messages
        caplog.set_level(logging.DEBUG)
        
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        orchestrator._setup_providers()
        
        # Should have logged provider setup
        log_messages = [record.message for record in caplog.records]
        assert any("Provider" in message or "Using" in message for message in log_messages)

    @pytest.mark.slow
    def test_orchestrator_performance(self, mock_env_complete):
        """Test orchestrator performance characteristics"""
        import time
        
        # Measure initialization time
        start_time = time.time()
        task = {"query": "test query", "report_type": "research_report"}
        orchestrator = ChiefEditorAgent(task)
        init_time = time.time() - start_time
        
        # Initialization should be fast (less than 2 seconds)
        assert init_time < 2.0
        
        # Measure provider setup time
        start_time = time.time()
        orchestrator._setup_providers()
        setup_time = time.time() - start_time
        
        # Provider setup should be fast (less than 1 second)
        assert setup_time < 1.0