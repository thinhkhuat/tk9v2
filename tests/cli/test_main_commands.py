"""
Tests for Main CLI Commands
Tests the main CLI interface and command parsing
"""

import argparse
import sys
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest
from cli.providers import add_provider_commands


class TestMainCLI:
    """Test main CLI interface and command parsing"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_env_complete(self, monkeypatch):
        """Complete environment setup for CLI testing"""
        env_vars = {
            "PRIMARY_LLM_PROVIDER": "openai",
            "PRIMARY_LLM_MODEL": "gpt-4o",
            "PRIMARY_SEARCH_PROVIDER": "tavily",
            "OPENAI_API_KEY": "test-openai-key",
            "TAVILY_API_KEY": "test-tavily-key",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars

    @pytest.fixture
    def captured_output(self):
        """Capture stdout and stderr for CLI testing"""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        yield {"stdout": stdout_capture, "stderr": stderr_capture}

        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def test_cli_parser_creation(self):
        """Test that CLI parser is created correctly"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")

        # Add provider commands
        provider_parser = add_provider_commands(subparsers)

        # Verify parser structure
        assert provider_parser is not None
        assert hasattr(provider_parser, "_subparsers_action")

        # Test parsing provider status command
        args = parser.parse_args(["providers", "status"])
        assert args.command == "providers"
        assert args.provider_command == "status"

    def test_provider_commands_parsing(self):
        """Test parsing of provider-related commands"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test various provider commands
        test_cases = [
            (["providers", "status"], "status"),
            (["providers", "list"], "list"),
            (["providers", "test"], "test"),
            (["providers", "stats"], "stats"),
            (["providers", "examples"], "examples"),
        ]

        for command_args, expected_subcommand in test_cases:
            args = parser.parse_args(command_args)
            assert args.command == "providers"
            assert args.provider_command == expected_subcommand

    def test_provider_switch_command_parsing(self):
        """Test parsing of provider switch commands"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test switch commands
        test_cases = [
            (["providers", "switch", "llm"], "llm", False),
            (["providers", "switch", "search"], "search", False),
            (["providers", "switch", "llm", "--fallback"], "llm", True),
            (["providers", "switch", "search", "--fallback"], "search", True),
        ]

        for command_args, expected_type, expected_fallback in test_cases:
            args = parser.parse_args(command_args)
            assert args.command == "providers"
            assert args.provider_command == "switch"
            assert args.type == expected_type
            assert args.fallback == expected_fallback

    @patch("cli.providers.ProviderCLI.show_provider_status")
    def test_provider_status_command_execution(self, mock_status, mock_env_complete):
        """Test execution of provider status command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "status"])

        # Execute the command
        if hasattr(args, "func"):
            args.func(args)
            mock_status.assert_called_once()

    @patch("cli.providers.ProviderCLI.list_available_providers")
    def test_provider_list_command_execution(self, mock_list, mock_env_complete):
        """Test execution of provider list command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "list"])

        # Execute the command
        if hasattr(args, "func"):
            args.func(args)
            mock_list.assert_called_once()

    @patch("cli.providers.ProviderCLI.test_providers")
    def test_provider_test_command_execution(self, mock_test, mock_env_complete):
        """Test execution of provider test command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "test"])

        # Execute the command
        if hasattr(args, "func"):
            args.func(args)
            mock_test.assert_called_once()

    @patch("cli.providers.ProviderCLI.switch_provider")
    def test_provider_switch_command_execution(self, mock_switch, mock_env_complete):
        """Test execution of provider switch command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test LLM switch
        args = parser.parse_args(["providers", "switch", "llm"])
        if hasattr(args, "func"):
            args.func(args)
            mock_switch.assert_called_with("llm", "", False)

        # Test search switch with fallback
        args = parser.parse_args(["providers", "switch", "search", "--fallback"])
        if hasattr(args, "func"):
            args.func(args)
            mock_switch.assert_called_with("search", "", True)

    @patch("cli.providers.ProviderCLI.show_usage_stats")
    def test_provider_stats_command_execution(self, mock_stats, mock_env_complete):
        """Test execution of provider stats command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "stats"])

        # Execute the command
        if hasattr(args, "func"):
            args.func(args)
            mock_stats.assert_called_once()

    @patch("cli.providers.ProviderCLI.show_configuration_examples")
    def test_provider_examples_command_execution(self, mock_examples, mock_env_complete):
        """Test execution of provider examples command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "examples"])

        # Execute the command
        if hasattr(args, "func"):
            args.func(args)
            mock_examples.assert_called_once()

    def test_invalid_command_handling(self):
        """Test handling of invalid commands"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test invalid provider subcommand
        with pytest.raises(SystemExit):
            parser.parse_args(["providers", "invalid"])

        # Test missing provider subcommand
        args = parser.parse_args(["providers"])
        assert args.command == "providers"
        assert getattr(args, "provider_command", None) is None

    def test_help_output(self, captured_output):
        """Test CLI help output"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test main help
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

        help_output = captured_output["stdout"].getvalue()
        # Help should be captured or SystemExit should be raised

        # Test provider help
        with pytest.raises(SystemExit):
            parser.parse_args(["providers", "--help"])

    def test_command_argument_validation(self):
        """Test validation of command arguments"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test switch command with invalid type
        with pytest.raises(SystemExit):
            parser.parse_args(["providers", "switch", "invalid"])

        # Test switch command without type
        with pytest.raises(SystemExit):
            parser.parse_args(["providers", "switch"])

    def test_cli_with_configuration_file(self, temp_config_dir, mock_env_complete):
        """Test CLI with configuration file"""
        import json

        # Create a test configuration file
        config_file = f"{temp_config_dir}/test_config.json"
        config_data = {
            "primary_llm_provider": "openai",
            "primary_llm_model": "gpt-4o",
            "primary_search_provider": "tavily",
            "llm_temperature": 0.7,
            "max_search_results": 10,
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Test that config file exists and is readable
        assert os.path.exists(config_file)

        with open(config_file, "r") as f:
            loaded_config = json.load(f)
            assert loaded_config["primary_llm_provider"] == "openai"

    def test_cli_error_handling(self, captured_output):
        """Test CLI error handling"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test with no command
        args = parser.parse_args([])
        assert args.command is None

        # Test with empty providers command
        args = parser.parse_args(["providers"])
        assert args.command == "providers"
        assert getattr(args, "provider_command", None) is None

    def test_cli_environment_variable_integration(self, monkeypatch):
        """Test CLI integration with environment variables"""
        # Test with missing environment
        monkeypatch.delenv("PRIMARY_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        args = parser.parse_args(["providers", "status"])
        assert args.command == "providers"
        assert args.provider_command == "status"

    def test_concurrent_cli_usage(self, mock_env_complete):
        """Test concurrent CLI usage"""
        import threading

        results = []

        def run_cli_parsing():
            try:
                parser = argparse.ArgumentParser()
                subparsers = parser.add_subparsers(dest="command")
                add_provider_commands(subparsers)

                args = parser.parse_args(["providers", "status"])
                if args.command == "providers" and args.provider_command == "status":
                    results.append("success")
                else:
                    results.append("failed")
            except Exception as e:
                results.append(f"error: {str(e)}")

        # Run concurrent CLI parsing
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=run_cli_parsing)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 5
        assert all(result == "success" for result in results)

    def test_cli_memory_usage(self, mock_env_complete):
        """Test memory usage of CLI operations"""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Create multiple CLI parsers
        parsers = []
        for _ in range(10):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest="command")
            add_provider_commands(subparsers)
            parsers.append(parser)

        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Memory increase should be minimal (less than 5MB for 10 parsers)
        assert memory_increase < 5 * 1024 * 1024

        # Clean up
        del parsers
        gc.collect()

    def test_cli_subcommand_isolation(self, mock_env_complete):
        """Test that CLI subcommands are properly isolated"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        provider_parser = add_provider_commands(subparsers)

        # Verify that provider subcommands don't leak into main parser
        main_actions = [action.dest for action in parser._actions]
        assert "provider_command" not in main_actions

        # Verify provider subcommands exist in provider parser
        provider_subparser_actions = provider_parser._subparsers_action
        assert provider_subparser_actions is not None

    def test_cli_command_function_mapping(self):
        """Test that CLI commands are properly mapped to functions"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # Test that commands have associated functions
        commands_with_functions = ["status", "list", "test", "switch", "stats", "examples"]

        for command in commands_with_functions:
            args = parser.parse_args(
                ["providers", command] + (["llm"] if command == "switch" else [])
            )
            assert hasattr(args, "func"), f"Command {command} should have associated function"
            assert callable(args.func), f"Function for {command} should be callable"

    def test_cli_performance(self, mock_env_complete):
        """Test CLI performance characteristics"""
        import time

        # Measure parser creation time
        start_time = time.time()

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        creation_time = time.time() - start_time

        # Parser creation should be fast (less than 100ms)
        assert creation_time < 0.1

        # Measure parsing time
        start_time = time.time()

        for _ in range(100):
            args = parser.parse_args(["providers", "status"])

        parsing_time = time.time() - start_time

        # Parsing 100 commands should be fast (less than 100ms)
        assert parsing_time < 0.1

    def test_cli_argument_consistency(self):
        """Test consistency of CLI arguments across commands"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_provider_commands(subparsers)

        # All provider commands should use consistent naming
        provider_commands = ["status", "list", "test", "stats", "examples"]

        for command in provider_commands:
            args = parser.parse_args(["providers", command])
            assert args.command == "providers"
            assert args.provider_command == command
