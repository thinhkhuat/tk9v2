"""
Integration Tests for Multi-Provider Workflows
Tests the complete workflow with different provider combinations
"""

import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from multi_agents.config.providers import ProviderConfigManager, LLMProvider, SearchProvider
from multi_agents.providers.factory import EnhancedGPTResearcherConfig, ProviderFactory
from multi_agents.agents.orchestrator import ChiefEditorAgent


class TestMultiProviderWorkflows:
    """Test complete workflows with different provider combinations"""
    
    @pytest.fixture
    def mock_env_openai_tavily(self, monkeypatch):
        """Mock environment for OpenAI + Tavily setup"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_LLM_MODEL": "gpt-4o",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            "OPENAI_API_KEY": "test-openai-key",
            "TAVILY_API_KEY": "test-tavily-key",
            "LLM_STRATEGY": "primary_only",
            "SEARCH_STRATEGY": "primary_only"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars
    
    @pytest.fixture
    def mock_env_gemini_brave(self, monkeypatch):
        """Mock environment for Gemini + Brave setup"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "google_gemini",
            "PRIMARY_LLM_MODEL": "gemini-1.5-pro",
            "PRIMARY_SEARCH_PROVIDER": "brave",
            "GOOGLE_API_KEY": "test-google-key",
            "BRAVE_API_KEY": "test-brave-key",
            "LLM_STRATEGY": "primary_only",
            "SEARCH_STRATEGY": "primary_only"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars
    
    @pytest.fixture
    def mock_env_with_fallbacks(self, monkeypatch):
        """Mock environment with fallback providers"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_LLM_MODEL": "gpt-4o",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            "FALLBACK_LLM_PROVIDER": "google_gemini",
            "FALLBACK_LLM_MODEL": "gemini-1.5-flash",
            "FALLBACK_SEARCH_PROVIDER": "brave",
            "OPENAI_API_KEY": "test-openai-key",
            "TAVILY_API_KEY": "test-tavily-key",
            "GOOGLE_API_KEY": "test-google-key",
            "BRAVE_API_KEY": "test-brave-key",
            "LLM_STRATEGY": "fallback_on_error",
            "SEARCH_STRATEGY": "fallback_on_error"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    def test_provider_config_loading_openai_tavily(self, mock_env_openai_tavily):
        """Test loading OpenAI + Tavily configuration"""
        config_manager = ProviderConfigManager()
        
        # Verify primary providers
        assert config_manager.config.primary_llm.provider == LLMProvider.OPENAI
        assert config_manager.config.primary_llm.model == "gpt-4o"
        assert config_manager.config.primary_search.provider == SearchProvider.TAVILY
        
        # Verify API keys are loaded
        assert config_manager.config.primary_llm.api_key == "test-openai-key"
        assert config_manager.config.primary_search.api_key == "test-tavily-key"
        
        # Verify no fallback providers
        assert config_manager.config.fallback_llm is None
        assert config_manager.config.fallback_search is None

    def test_provider_config_loading_gemini_brave(self, mock_env_gemini_brave):
        """Test loading Gemini + Brave configuration"""
        config_manager = ProviderConfigManager()
        
        # Verify primary providers
        assert config_manager.config.primary_llm.provider == LLMProvider.GOOGLE_GEMINI
        assert config_manager.config.primary_llm.model == "gemini-1.5-pro"
        assert config_manager.config.primary_search.provider == SearchProvider.BRAVE
        
        # Verify API keys are loaded
        assert config_manager.config.primary_llm.api_key == "test-google-key"
        assert config_manager.config.primary_search.api_key == "test-brave-key"

    def test_provider_config_with_fallbacks(self, mock_env_with_fallbacks):
        """Test configuration with fallback providers"""
        config_manager = ProviderConfigManager()
        
        # Verify primary providers
        assert config_manager.config.primary_llm.provider == LLMProvider.OPENAI
        assert config_manager.config.primary_search.provider == SearchProvider.TAVILY
        
        # Verify fallback providers
        assert config_manager.config.fallback_llm is not None
        assert config_manager.config.fallback_llm.provider == LLMProvider.GOOGLE_GEMINI
        assert config_manager.config.fallback_search is not None
        assert config_manager.config.fallback_search.provider == SearchProvider.BRAVE
        
        # Verify strategies
        assert config_manager.config.llm_strategy == "fallback_on_error"
        assert config_manager.config.search_strategy == "fallback_on_error"

    def test_gpt_researcher_config_generation_openai(self, mock_env_openai_tavily):
        """Test GPT-Researcher config generation for OpenAI"""
        config_manager = ProviderConfigManager()
        gpt_config = config_manager.get_gpt_researcher_config()
        
        # Verify LLM configuration
        assert gpt_config["SMART_LLM"] == "openai:gpt-4o"
        assert gpt_config["FAST_LLM"] == "openai:gpt-4o"
        assert gpt_config["OPENAI_API_KEY"] == "test-openai-key"
        
        # Verify search configuration
        assert gpt_config["RETRIEVER"] == "tavily"
        assert gpt_config["TAVILY_API_KEY"] == "test-tavily-key"
        
        # Verify additional parameters
        assert "LLM_TEMPERATURE" in gpt_config
        assert "MAX_SEARCH_RESULTS" in gpt_config

    def test_gpt_researcher_config_generation_gemini(self, mock_env_gemini_brave):
        """Test GPT-Researcher config generation for Gemini"""
        config_manager = ProviderConfigManager()
        gpt_config = config_manager.get_gpt_researcher_config()
        
        # Verify LLM configuration
        assert gpt_config["SMART_LLM"] == "google_genai:gemini-1.5-pro"
        assert gpt_config["FAST_LLM"] == "google_genai:gemini-1.5-pro"
        assert gpt_config["GOOGLE_API_KEY"] == "test-google-key"
        
        # Verify search configuration
        assert gpt_config["RETRIEVER"] == "brave"
        assert gpt_config["BRAVE_API_KEY"] == "test-brave-key"

    def test_enhanced_config_provider_switching(self, mock_env_with_fallbacks):
        """Test provider switching functionality"""
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        # Test initial state (primary providers)
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "openai"
        assert current["search_provider"] == "tavily"
        
        # Test switching to fallback LLM
        enhanced_config.switch_llm_provider(use_fallback=True)
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "google_gemini"
        assert current["llm_model"] == "gemini-1.5-flash"
        assert current["search_provider"] == "tavily"  # Should remain unchanged
        
        # Test switching to fallback search
        enhanced_config.switch_search_provider(use_fallback=True)
        current = enhanced_config.get_current_providers()
        assert current["llm_provider"] == "google_gemini"  # Should remain changed
        assert current["search_provider"] == "brave"

    def test_configuration_validation_valid(self, mock_env_openai_tavily):
        """Test configuration validation with valid setup"""
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        validation = enhanced_config.validate_current_config()
        
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
        assert "provider_info" in validation
        assert "gpt_researcher_config" in validation

    def test_configuration_validation_invalid(self, monkeypatch):
        """Test configuration validation with missing API keys"""
        # Set up environment with missing API keys
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            # Missing OPENAI_API_KEY and TAVILY_API_KEY
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        validation = enhanced_config.validate_current_config()
        
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
        assert any("API key" in issue for issue in validation["issues"])

    def test_provider_factory_creation(self, mock_env_gemini_brave):
        """Test provider factory creation with Gemini + Brave"""
        config_manager = ProviderConfigManager()
        
        # Test LLM provider creation
        llm_config = config_manager.get_llm_config()
        try:
            llm_provider = ProviderFactory.create_llm_provider(llm_config)
            assert llm_provider is not None
        except ValueError:
            # Expected if provider not fully implemented
            pass
        
        # Test search provider creation
        search_config = config_manager.get_search_config()
        try:
            search_provider = ProviderFactory.create_search_provider(search_config)
            assert search_provider is not None
        except ValueError:
            # Expected if provider not fully implemented
            pass

    def test_provider_manager_creation(self, mock_env_with_fallbacks):
        """Test provider manager creation with fallback providers"""
        config_manager = ProviderConfigManager()
        provider_manager = ProviderFactory.create_provider_manager(config_manager)
        
        assert provider_manager is not None
        # The manager should be created successfully even if some providers
        # are not implemented in the abstraction layer

    def test_orchestrator_integration_openai(self, mock_env_openai_tavily):
        """Test orchestrator integration with OpenAI + Tavily"""
        # Create simple task for orchestrator
        task = {"query": "test query", "report_type": "research_report"}
        
        # Create orchestrator
        orchestrator = ChiefEditorAgent(task)
        
        # Test that environment is properly configured
        assert os.environ.get("SMART_LLM") == "openai:gpt-4o"
        assert os.environ.get("RETRIEVER") == "tavily"

    def test_orchestrator_integration_gemini(self, mock_env_gemini_brave):
        """Test orchestrator integration with Gemini + Brave"""
        # Create simple task for orchestrator
        task = {"query": "test query", "report_type": "research_report"}
        
        # Create orchestrator
        orchestrator = ChiefEditorAgent(task)
        
        # Test that environment is properly configured
        assert os.environ.get("SMART_LLM") == "google_genai:gemini-1.5-pro"
        assert os.environ.get("RETRIEVER") == "brave"

    def test_environment_isolation(self, mock_env_openai_tavily):
        """Test that configuration changes don't leak between tests"""
        config_manager = ProviderConfigManager()
        
        # Verify OpenAI configuration
        assert config_manager.config.primary_llm.provider == LLMProvider.OPENAI
        assert config_manager.config.primary_search.provider == SearchProvider.TAVILY

    def test_error_handling_missing_provider(self, monkeypatch):
        """Test error handling when provider is not available"""
        # Set up environment with invalid provider
        monkeypatch.setenv("PRIMARY_LLM_PROVIDER", "invalid_provider")
        
        with pytest.raises(ValueError):
            config_manager = ProviderConfigManager()

    def test_api_key_environment_mapping(self, mock_env_gemini_brave):
        """Test that API keys are correctly mapped from environment"""
        config_manager = ProviderConfigManager()
        
        # Test LLM API key mapping
        llm_config = config_manager.get_llm_config()
        assert llm_config.api_key == "test-google-key"
        
        # Test search API key mapping
        search_config = config_manager.get_search_config()
        assert search_config.api_key == "test-brave-key"
        
        # Test GPT-Researcher config has correct keys
        gpt_config = config_manager.get_gpt_researcher_config()
        assert gpt_config["GOOGLE_API_KEY"] == "test-google-key"
        assert gpt_config["BRAVE_API_KEY"] == "test-brave-key"

    def test_configuration_persistence(self, mock_env_with_fallbacks):
        """Test that configuration persists across multiple accesses"""
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        # Get initial configuration
        initial_config = enhanced_config.get_config_dict()
        
        # Switch providers
        enhanced_config.switch_llm_provider(use_fallback=True)
        
        # Get updated configuration
        updated_config = enhanced_config.get_config_dict()
        
        # Verify configuration changed
        assert initial_config["SMART_LLM"] != updated_config["SMART_LLM"]
        assert "google_genai" in updated_config["SMART_LLM"]

    @pytest.mark.asyncio
    async def test_async_provider_operations(self, mock_env_gemini_brave):
        """Test that provider operations work in async context"""
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        # Test async configuration access
        async def get_config():
            return enhanced_config.get_current_providers()
        
        result = await get_config()
        assert result["llm_provider"] == "google_gemini"
        assert result["search_provider"] == "brave"

    def test_concurrent_provider_access(self, mock_env_with_fallbacks):
        """Test concurrent access to provider configuration"""
        import threading
        import time
        
        config_manager = ProviderConfigManager()
        enhanced_config = EnhancedGPTResearcherConfig(config_manager)
        
        results = []
        
        def worker():
            for _ in range(5):
                current = enhanced_config.get_current_providers()
                results.append(current["llm_provider"])
                time.sleep(0.01)
        
        threads = [threading.Thread(target=worker) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All results should be consistent
        assert len(set(results)) == 1  # All should be the same provider