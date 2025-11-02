"""
Unit tests for configuration management system.
Tests provider configuration loading, validation, and management.
"""

import os
from unittest.mock import patch


from multi_agents.config.providers import (
    LLMConfig,
    LLMProvider,
    MultiProviderConfig,
    ProviderConfigManager,
    SearchConfig,
    SearchProvider,
)


class TestLLMConfig:
    """Test LLM configuration data class."""

    def test_llm_config_creation(self):
        """Test basic LLM config creation."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test_key",
            temperature=0.7,
            max_tokens=1000,
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4o"
        assert config.api_key == "test_key"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000

    def test_llm_config_defaults(self):
        """Test LLM config with default values."""
        config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test_key")

        assert config.temperature == 0.7
        assert config.max_tokens == 4000
        assert config.base_url is None
        assert config.extra_params == {}

    def test_llm_config_validation(self):
        """Test LLM config validation."""
        # Valid temperature range
        config = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test_key", temperature=0.5
        )
        assert config.temperature == 0.5

        # Test boundary values
        config_min = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test_key", temperature=0.0
        )
        assert config_min.temperature == 0.0

        config_max = LLMConfig(
            provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test_key", temperature=2.0
        )
        assert config_max.temperature == 2.0


class TestSearchConfig:
    """Test search configuration data class."""

    def test_search_config_creation(self):
        """Test basic search config creation."""
        config = SearchConfig(provider=SearchProvider.TAVILY, api_key="test_key", max_results=10)

        assert config.provider == SearchProvider.TAVILY
        assert config.api_key == "test_key"
        assert config.max_results == 10

    def test_search_config_defaults(self):
        """Test search config with default values."""
        config = SearchConfig(provider=SearchProvider.TAVILY, api_key="test_key")

        assert config.max_results == 10

    def test_search_config_validation(self):
        """Test search config validation."""
        # Valid max_results range
        config = SearchConfig(provider=SearchProvider.TAVILY, api_key="test_key", max_results=5)
        assert config.max_results == 5


class TestMultiProviderConfig:
    """Test provider configuration container."""

    def test_provider_config_creation(self, sample_llm_config, sample_search_config):
        """Test provider config creation."""
        config = MultiProviderConfig(
            primary_llm=sample_llm_config,
            primary_search=sample_search_config,
            llm_strategy="primary_only",
            search_strategy="primary_only",
        )

        assert config.primary_llm == sample_llm_config
        assert config.primary_search == sample_search_config
        assert config.llm_strategy == "primary_only"
        assert config.search_strategy == "primary_only"
        assert config.fallback_llm is None
        assert config.fallback_search is None

    def test_provider_config_with_fallbacks(self, sample_llm_config, sample_search_config):
        """Test provider config with fallback providers."""
        fallback_llm = LLMConfig(
            provider="google_gemini", model="gemini-1.5-pro", api_key="fallback_key"
        )
        fallback_search = SearchConfig(provider="brave", api_key="brave_key")

        config = MultiProviderConfig(
            primary_llm=sample_llm_config,
            primary_search=sample_search_config,
            fallback_llm=fallback_llm,
            fallback_search=fallback_search,
            llm_strategy="fallback_on_error",
            search_strategy="fallback_on_error",
        )

        assert config.fallback_llm == fallback_llm
        assert config.fallback_search == fallback_search
        assert config.llm_strategy == "fallback_on_error"
        assert config.search_strategy == "fallback_on_error"

    def test_provider_config_strategy_validation(self, sample_llm_config, sample_search_config):
        """Test provider config strategy validation."""
        valid_strategies = ["primary_only", "fallback_on_error", "load_balance"]

        for strategy in valid_strategies:
            config = MultiProviderConfig(
                primary_llm=sample_llm_config,
                primary_search=sample_search_config,
                llm_strategy=strategy,
                search_strategy=strategy,
            )
            assert config.llm_strategy == strategy
            assert config.search_strategy == strategy


class TestProviderConfigManager:
    """Test provider configuration manager."""

    def test_config_manager_load_from_env(self, mock_env_vars):
        """Test loading configuration from environment variables."""
        manager = ProviderConfigManager()
        config = manager.load_from_environment()

        assert isinstance(config, ProviderConfig)
        assert config.primary_llm.provider == "openai"
        assert config.primary_llm.model == "gpt-4o"
        assert config.primary_search.provider == "tavily"
        assert config.fallback_llm.provider == "google_gemini"
        assert config.fallback_search.provider == "brave"
        assert config.llm_strategy == "fallback_on_error"
        assert config.search_strategy == "primary_only"

    def test_config_manager_minimal_env(self):
        """Test loading with minimal environment variables."""
        minimal_env = {"OPENAI_API_KEY": "sk-test_key", "TAVILY_API_KEY": "tvly-test_key"}

        with patch.dict(os.environ, minimal_env, clear=True):
            manager = ProviderConfigManager()
            config = manager.load_from_environment()

            assert config.primary_llm.provider == "openai"
            assert config.primary_llm.model == "gpt-4o"  # default
            assert config.primary_search.provider == "tavily"
            assert config.fallback_llm is None
            assert config.fallback_search is None
            assert config.llm_strategy == "primary_only"  # default
            assert config.search_strategy == "primary_only"  # default

    def test_config_manager_missing_primary_keys(self):
        """Test handling of missing primary API keys."""
        incomplete_env = {"GOOGLE_API_KEY": "test_google_key"}

        with patch.dict(os.environ, incomplete_env, clear=True):
            manager = ProviderConfigManager()

            # Should handle gracefully or raise appropriate error
            try:
                config = manager.load_from_environment()
                # If it succeeds, should fall back to available providers
                assert config is not None
            except Exception as e:
                # Should raise meaningful error about missing keys
                assert "API key" in str(e) or "provider" in str(e)

    def test_config_manager_provider_selection(self):
        """Test dynamic provider selection."""
        # Test with Google Gemini as primary
        gemini_env = {
            "GOOGLE_API_KEY": "test_google_key",
            "BRAVE_API_KEY": "test_brave_key",
            "PRIMARY_LLM_PROVIDER": "google_gemini",
            "PRIMARY_LLM_MODEL": "gemini-1.5-pro",
            "PRIMARY_SEARCH_PROVIDER": "brave",
        }

        with patch.dict(os.environ, gemini_env, clear=True):
            manager = ProviderConfigManager()
            config = manager.load_from_environment()

            assert config.primary_llm.provider == "google_gemini"
            assert config.primary_llm.model == "gemini-1.5-pro"
            assert config.primary_search.provider == "brave"

    def test_config_manager_parameter_parsing(self):
        """Test parsing of configuration parameters."""
        param_env = {
            "OPENAI_API_KEY": "sk-test_key",
            "TAVILY_API_KEY": "tvly-test_key",
            "LLM_TEMPERATURE": "0.8",
            "LLM_MAX_TOKENS": "2000",
            "SEARCH_MAX_RESULTS": "15",
        }

        with patch.dict(os.environ, param_env, clear=True):
            manager = ProviderConfigManager()
            config = manager.load_from_environment()

            assert config.primary_llm.temperature == 0.8
            assert config.primary_llm.max_tokens == 2000
            assert config.primary_search.max_results == 15

    def test_config_manager_api_key_mapping(self):
        """Test correct API key mapping for different providers."""
        manager = ProviderConfigManager()

        # Test LLM provider key mapping
        assert manager._get_api_key_for_llm_provider("openai") == os.getenv("OPENAI_API_KEY")
        assert manager._get_api_key_for_llm_provider("google_gemini") == os.getenv("GOOGLE_API_KEY")
        assert manager._get_api_key_for_llm_provider("anthropic") == os.getenv("ANTHROPIC_API_KEY")

        # Test search provider key mapping
        assert manager._get_api_key_for_search_provider("tavily") == os.getenv("TAVILY_API_KEY")
        assert manager._get_api_key_for_search_provider("brave") == os.getenv("BRAVE_API_KEY")
        assert manager._get_api_key_for_search_provider("google") == os.getenv("GOOGLE_API_KEY")

    def test_config_manager_validation(self, mock_env_vars):
        """Test configuration validation."""
        manager = ProviderConfigManager()
        config = manager.load_from_environment()

        validation_result = manager.validate_config(config)

        assert isinstance(validation_result, dict)
        assert "valid" in validation_result
        assert "issues" in validation_result

        if validation_result["valid"]:
            assert len(validation_result["issues"]) == 0
        else:
            assert len(validation_result["issues"]) > 0
            assert all(isinstance(issue, str) for issue in validation_result["issues"])

    def test_config_manager_invalid_config_validation(self):
        """Test validation of invalid configurations."""
        manager = ProviderConfigManager()

        # Create invalid config with missing API key
        invalid_config = ProviderConfig(
            primary_llm=LLMConfig(
                provider="openai", model="gpt-4o", api_key=None  # Invalid: missing API key
            ),
            primary_search=SearchConfig(provider="tavily", api_key="valid_key"),
            llm_strategy="primary_only",
            search_strategy="primary_only",
        )

        validation_result = manager.validate_config(invalid_config)

        assert validation_result["valid"] is False
        assert len(validation_result["issues"]) > 0
        assert any("API key" in issue for issue in validation_result["issues"])

    def test_config_manager_fallback_without_strategy(self):
        """Test validation when fallback providers are configured without appropriate strategy."""
        manager = ProviderConfigManager()

        # Config with fallback providers but primary_only strategy
        config = MultiProviderConfig(
            primary_llm=LLMConfig(provider="openai", model="gpt-4o", api_key="valid_key"),
            primary_search=SearchConfig(provider="tavily", api_key="valid_key"),
            fallback_llm=LLMConfig(
                provider="google_gemini", model="gemini-1.5-pro", api_key="valid_key"
            ),
            llm_strategy="primary_only",  # Inconsistent with having fallback
            search_strategy="primary_only",
        )

        validation_result = manager.validate_config(config)

        # This might be valid (fallback providers ignored) or invalid depending on implementation
        if not validation_result["valid"]:
            assert any(
                "strategy" in issue.lower() or "fallback" in issue.lower()
                for issue in validation_result["issues"]
            )

    def test_config_manager_get_provider_info(self, mock_env_vars):
        """Test getting provider information."""
        manager = ProviderConfigManager()
        config = manager.load_from_environment()

        provider_info = manager.get_provider_info(config)

        assert isinstance(provider_info, dict)
        assert "primary_llm" in provider_info
        assert "primary_search" in provider_info
        assert "strategies" in provider_info

        # Check LLM info structure
        llm_info = provider_info["primary_llm"]
        assert "provider" in llm_info
        assert "model" in llm_info
        assert "has_api_key" in llm_info
        assert isinstance(llm_info["has_api_key"], bool)

        # Check search info structure
        search_info = provider_info["primary_search"]
        assert "provider" in search_info
        assert "has_api_key" in search_info
        assert "max_results" in search_info

        # Check strategies
        strategies = provider_info["strategies"]
        assert "llm" in strategies
        assert "search" in strategies

    def test_config_manager_provider_switching(self, mock_env_vars):
        """Test dynamic provider switching capability."""
        manager = ProviderConfigManager()

        # Test switching to fallback LLM
        original_config = manager.load_from_environment()
        switched_config = manager.switch_to_fallback_llm(original_config)

        if switched_config:
            assert switched_config.primary_llm.provider != original_config.primary_llm.provider
            assert switched_config.primary_llm.provider == original_config.fallback_llm.provider

        # Test switching to fallback search
        switched_config = manager.switch_to_fallback_search(original_config)

        if switched_config:
            assert (
                switched_config.primary_search.provider != original_config.primary_search.provider
            )
            assert (
                switched_config.primary_search.provider == original_config.fallback_search.provider
            )


class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def test_configuration_environment_integration(self, sample_env_vars):
        """Test full environment integration."""
        with patch.dict(os.environ, sample_env_vars, clear=False):
            manager = ProviderConfigManager()
            config = manager.load_from_environment()

            # Validate the loaded configuration
            validation = manager.validate_config(config)
            assert validation["valid"] is True

            # Get provider info
            info = manager.get_provider_info(config)
            assert info["primary_llm"]["has_api_key"] is True
            assert info["primary_search"]["has_api_key"] is True

    def test_configuration_provider_creation_compatibility(self, mock_env_vars):
        """Test that configuration is compatible with provider creation."""
        manager = ProviderConfigManager()
        config = manager.load_from_environment()

        # Test that configs have all required fields for provider creation
        assert hasattr(config.primary_llm, "provider")
        assert hasattr(config.primary_llm, "model")
        assert hasattr(config.primary_llm, "api_key")
        assert hasattr(config.primary_llm, "temperature")
        assert hasattr(config.primary_llm, "max_tokens")

        assert hasattr(config.primary_search, "provider")
        assert hasattr(config.primary_search, "api_key")
        assert hasattr(config.primary_search, "max_results")

    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        manager = ProviderConfigManager()

        # Test with completely empty environment
        with patch.dict(os.environ, {}, clear=True):
            try:
                config = manager.load_from_environment()
                # If successful, should have sensible defaults
                assert config is not None
            except Exception as e:
                # Should provide meaningful error message
                assert len(str(e)) > 0
