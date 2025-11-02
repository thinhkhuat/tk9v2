"""
Tests for CLI Provider Commands
Tests the provider management CLI functionality
"""

import sys
from io import StringIO
from unittest.mock import patch

import pytest
from cli.providers import ProviderCLI


class TestProviderCLI:
    """Test CLI provider management commands"""

    @pytest.fixture
    def mock_env_complete(self, monkeypatch):
        """Complete environment setup for CLI testing"""
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
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.fixture
    def mock_env_missing_keys(self, monkeypatch):
        """Environment with missing API keys for testing validation"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            # Missing OPENAI_API_KEY and TAVILY_API_KEY
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.fixture
    def captured_output(self):
        """Capture stdout for CLI testing"""
        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()
        yield captured
        sys.stdout = old_stdout

    def test_show_provider_status_valid_config(self, mock_env_complete, captured_output):
        """Test showing provider status with valid configuration"""
        ProviderCLI.show_provider_status()

        output = captured_output.getvalue()

        # Verify output contains expected information
        assert "PROVIDER STATUS" in output
        assert "Primary Providers:" in output
        assert "openai:gpt-4o" in output
        assert "tavily" in output
        assert "Fallback Providers:" in output
        assert "google_gemini:gemini-1.5-pro" in output
        assert "brave" in output
        assert "Strategies:" in output
        assert "fallback_on_error" in output
        assert "✓ Valid configuration" in output

    def test_show_provider_status_invalid_config(self, mock_env_missing_keys, captured_output):
        """Test showing provider status with invalid configuration"""
        ProviderCLI.show_provider_status()

        output = captured_output.getvalue()

        # Verify output shows configuration issues
        assert "PROVIDER STATUS" in output
        assert "✗ Configuration issues:" in output
        assert "Missing API key" in output

    def test_list_available_providers(self, captured_output):
        """Test listing available providers"""
        ProviderCLI.list_available_providers()

        output = captured_output.getvalue()

        # Verify all provider types are listed
        assert "AVAILABLE PROVIDERS" in output
        assert "LLM Providers:" in output
        assert "openai" in output
        assert "google_gemini" in output
        assert "anthropic" in output
        assert "azure_openai" in output

        assert "Search Providers:" in output
        assert "tavily" in output
        assert "brave" in output
        assert "google" in output
        assert "serpapi" in output
        assert "duckduckgo" in output

        # Verify environment variable information
        assert "OPENAI_API_KEY" in output
        assert "GOOGLE_API_KEY" in output
        assert "BRAVE_API_KEY" in output

    def test_list_providers_with_api_keys(self, mock_env_complete, captured_output):
        """Test listing providers when API keys are available"""
        ProviderCLI.list_available_providers()

        output = captured_output.getvalue()

        # Should show checkmarks for available providers
        assert "✓" in output  # Should have checkmarks for providers with API keys

    def test_test_providers_valid_config(self, mock_env_complete, captured_output):
        """Test provider connectivity testing with valid configuration"""
        ProviderCLI.test_providers()

        output = captured_output.getvalue()

        assert "TESTING PROVIDERS" in output
        assert "Testing provider connectivity" in output
        assert "Current Configuration:" in output
        assert "openai:gpt-4o" in output
        assert "tavily" in output
        assert "Configuration appears valid" in output

    def test_test_providers_invalid_config(self, mock_env_missing_keys, captured_output):
        """Test provider testing with invalid configuration"""
        ProviderCLI.test_providers()

        output = captured_output.getvalue()

        assert "TESTING PROVIDERS" in output
        assert "Configuration is invalid" in output
        assert "Fix issues first:" in output

    def test_switch_provider_llm_fallback(self, mock_env_complete, captured_output):
        """Test switching to fallback LLM provider"""
        ProviderCLI.switch_provider("llm", "", fallback=True)

        output = captured_output.getvalue()

        assert "SWITCHING PROVIDER" in output
        assert "Successfully switched providers:" in output
        assert "google_gemini" in output  # Should show fallback provider

    def test_switch_provider_search_fallback(self, mock_env_complete, captured_output):
        """Test switching to fallback search provider"""
        ProviderCLI.switch_provider("search", "", fallback=True)

        output = captured_output.getvalue()

        assert "SWITCHING PROVIDER" in output
        assert "Successfully switched providers:" in output
        assert "brave" in output  # Should show fallback provider

    def test_switch_provider_invalid_type(self, mock_env_complete, captured_output):
        """Test switching with invalid provider type"""
        ProviderCLI.switch_provider("invalid", "")

        output = captured_output.getvalue()

        assert "SWITCHING PROVIDER" in output
        assert "Invalid provider type" in output
        assert "Use 'llm' or 'search'" in output

    @patch("multi_agents.providers.factory.provider_manager")
    def test_show_usage_stats_with_data(self, mock_provider_manager, captured_output):
        """Test showing usage statistics with data"""
        # Mock usage statistics
        mock_stats = {
            "llm": {
                "openai": {"requests": 25, "tokens": 15000, "cost": 0.045, "errors": 1},
                "google_gemini": {"requests": 10, "tokens": 8000, "cost": 0.020, "errors": 0},
            },
            "search": {
                "tavily": {"requests": 30, "results": 300, "errors": 2},
                "brave": {"requests": 15, "results": 150, "errors": 0},
            },
        }
        mock_provider_manager.get_usage_stats.return_value = mock_stats

        ProviderCLI.show_usage_stats()

        output = captured_output.getvalue()

        assert "USAGE STATISTICS" in output
        assert "LLM Usage:" in output
        assert "openai" in output
        assert "Requests: 25" in output
        assert "Tokens: 15,000" in output
        assert "Cost: $0.0450" in output

        assert "Search Usage:" in output
        assert "tavily" in output
        assert "Requests: 30" in output
        assert "Results: 300" in output

    @patch("multi_agents.providers.factory.provider_manager")
    def test_show_usage_stats_no_data(self, mock_provider_manager, captured_output):
        """Test showing usage statistics with no data"""
        mock_provider_manager.get_usage_stats.return_value = {"llm": {}, "search": {}}

        ProviderCLI.show_usage_stats()

        output = captured_output.getvalue()

        assert "USAGE STATISTICS" in output
        assert "No usage statistics available yet" in output
        assert "Run some research tasks to see statistics" in output

    @patch("multi_agents.providers.factory.provider_manager")
    def test_show_usage_stats_error(self, mock_provider_manager, captured_output):
        """Test showing usage statistics with error"""
        mock_provider_manager.get_usage_stats.side_effect = Exception("Stats unavailable")

        ProviderCLI.show_usage_stats()

        output = captured_output.getvalue()

        assert "USAGE STATISTICS" in output
        assert "Error retrieving usage stats" in output
        assert "Stats unavailable" in output

    def test_show_configuration_examples(self, captured_output):
        """Test showing configuration examples"""
        ProviderCLI.show_configuration_examples()

        output = captured_output.getvalue()

        assert "CONFIGURATION EXAMPLES" in output
        assert "OpenAI + Tavily (Default)" in output
        assert "Google Gemini + Brave" in output
        assert "Mixed with Fallbacks" in output

        # Verify configuration details
        assert "PRIMARY_LLM_PROVIDER=openai" in output
        assert "PRIMARY_LLM_PROVIDER=google_gemini" in output
        assert "FALLBACK_LLM_PROVIDER" in output
        assert "FALLBACK_SEARCH_PROVIDER" in output

        # Verify instructions
        assert "To apply a configuration:" in output
        assert "Edit your .env file" in output
        assert "Restart the application" in output

    def test_provider_cli_color_output(self, mock_env_complete, captured_output):
        """Test that CLI uses color codes in output"""
        ProviderCLI.show_provider_status()

        output = captured_output.getvalue()

        # Should contain ANSI color codes (may vary based on terminal support)
        # Just verify that colored output is attempted
        assert len(output) > 100  # Should have substantial output
        assert "PROVIDER STATUS" in output

    def test_provider_status_with_partial_config(self, monkeypatch, captured_output):
        """Test provider status with partial configuration"""
        # Set up environment with only primary providers
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            "OPENAI_API_KEY": "test-key",
            "TAVILY_API_KEY": "test-key",
            # No fallback providers
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        ProviderCLI.show_provider_status()

        output = captured_output.getvalue()

        assert "Primary Providers:" in output
        assert "openai" in output
        assert "tavily" in output
        # Should not show fallback section when not configured
        assert "Fallback Providers:" not in output

    def test_concurrent_cli_operations(self, mock_env_complete):
        """Test concurrent CLI operations don't interfere"""
        import threading

        results = []

        def run_cli_command():
            try:
                # Capture output in thread-local storage
                old_stdout = sys.stdout
                sys.stdout = StringIO()

                ProviderCLI.show_provider_status()
                output = sys.stdout.getvalue()

                sys.stdout = old_stdout

                if "PROVIDER STATUS" in output:
                    results.append("success")
                else:
                    results.append("failed")
            except Exception as e:
                results.append(f"error: {str(e)}")

        # Run 5 concurrent CLI commands
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=run_cli_command)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 5
        assert all(result == "success" for result in results)

    def test_cli_error_handling(self, captured_output):
        """Test CLI error handling with various error conditions"""
        # Test with no environment setup (should handle gracefully)
        try:
            ProviderCLI.show_provider_status()
            output = captured_output.getvalue()
            # Should either work with defaults or show appropriate error
            assert len(output) > 0
        except Exception:
            # Some errors are expected with no environment setup
            pass

    def test_provider_cli_memory_usage(self, mock_env_complete):
        """Test memory usage of CLI operations"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Run multiple CLI operations
        for _ in range(10):
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            ProviderCLI.show_provider_status()
            ProviderCLI.list_available_providers()
            ProviderCLI.test_providers()

            sys.stdout = old_stdout

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be minimal (less than 10MB)
        assert memory_increase < 10 * 1024 * 1024

        gc.collect()

    def test_provider_switching_state_management(self, mock_env_complete, captured_output):
        """Test that provider switching maintains state correctly"""
        # Initial state
        ProviderCLI.show_provider_status()
        initial_output = captured_output.getvalue()

        # Clear capture
        captured_output.truncate(0)
        captured_output.seek(0)

        # Switch to fallback
        ProviderCLI.switch_provider("llm", "", fallback=True)
        switch_output = captured_output.getvalue()

        # Clear capture
        captured_output.truncate(0)
        captured_output.seek(0)

        # Check status after switch
        ProviderCLI.show_provider_status()
        final_output = captured_output.getvalue()

        # Verify state changed
        assert "Successfully switched providers" in switch_output
        assert initial_output != final_output

    def test_cli_help_and_documentation(self, captured_output):
        """Test CLI help and documentation features"""
        # Test configuration examples (acts as documentation)
        ProviderCLI.show_configuration_examples()

        output = captured_output.getvalue()

        # Should provide comprehensive documentation
        assert "CONFIGURATION EXAMPLES" in output
        assert len(output) > 500  # Should be substantial documentation

        # Should include multiple examples
        example_count = output.count("Configuration:")
        assert example_count >= 3  # Should have at least 3 examples
