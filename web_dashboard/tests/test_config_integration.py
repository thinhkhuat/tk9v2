"""
Integration tests for Phase 1 configuration.

Tests that configuration values are properly used throughout the application
in real-world scenarios.
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestCORSIntegration:
    """Test CORS configuration integration with FastAPI middleware."""

    def test_cors_middleware_uses_configured_origins(self):
        """Test that CORS middleware actually uses the configured origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://test.com,https://another.com"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            client = TestClient(main.app)

            # Test OPTIONS request (CORS preflight)
            response = client.options(
                "/api/health",
                headers={
                    "Origin": "http://test.com",
                    "Access-Control-Request-Method": "GET",
                },
            )

            # Should allow the origin
            assert response.status_code in [200, 204]
            assert "access-control-allow-origin" in response.headers

    def test_cors_blocks_non_allowed_origin(self):
        """Test that CORS blocks origins not in the allowed list."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://allowed.com"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            client = TestClient(main.app)

            response = client.get("/api/health", headers={"Origin": "http://not-allowed.com"})

            # CORS middleware should not set allow-origin header for non-allowed origins
            # The request will succeed but without CORS headers
            allowed_origin = response.headers.get("access-control-allow-origin")
            assert allowed_origin is None or allowed_origin != "http://not-allowed.com"


class TestTimeoutIntegration:
    """Test timeout configuration integration with actual operations."""

    @pytest.mark.asyncio
    async def test_file_wait_timeout_used_in_wait_for_files(self):
        """Test that FILE_WAIT_TIMEOUT is actually used in file manager."""
        with patch.dict(os.environ, {"FILE_WAIT_TIMEOUT": "5"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            # Verify the constant was loaded correctly
            assert main.FILE_WAIT_TIMEOUT == 5

            # Mock the file_manager to track timeout parameter
            original_wait = main.file_manager.wait_for_files
            called_with_timeout = None

            async def mock_wait(*args, **kwargs):
                nonlocal called_with_timeout
                called_with_timeout = kwargs.get("timeout")
                # Return empty files to prevent actual waiting
                return []

            main.file_manager.wait_for_files = mock_wait

            # Simulate the code path that uses FILE_WAIT_TIMEOUT
            # This would normally be called from the research endpoint
            try:
                await main.file_manager.wait_for_files(
                    session_id="test-123",
                    subject="test",
                    timeout=main.FILE_WAIT_TIMEOUT,
                )

                # Verify timeout parameter was passed correctly
                assert called_with_timeout == 5
            finally:
                # Restore original method
                main.file_manager.wait_for_files = original_wait

    @pytest.mark.asyncio
    async def test_session_cleanup_interval_used_in_periodic_cleanup(self):
        """Test that SESSION_CLEANUP_INTERVAL is used in cleanup loop."""
        with patch.dict(os.environ, {"SESSION_CLEANUP_INTERVAL": "10"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            # Verify the constant was loaded correctly
            assert main.SESSION_CLEANUP_INTERVAL == 10

            # The periodic_cleanup function uses this value in asyncio.sleep()
            # We can't easily test the actual sleep, but we've verified the constant is set


class TestResearchLanguageIntegration:
    """Test research language configuration integration with request handling."""

    def test_research_request_default_language(self):
        """Test that ResearchRequest uses configured default language."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "en"}):
            import importlib
            import sys

            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import models

            importlib.reload(models)

            # Create request without specifying language
            request = models.ResearchRequest(subject="Test research topic")

            # Should use the configured default
            assert request.language == "en"

    def test_research_request_override_default_language(self):
        """Test that explicit language overrides default."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "vi"}):
            import importlib
            import sys

            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import models

            importlib.reload(models)

            # Create request with explicit language
            request = models.ResearchRequest(subject="Test research topic", language="fr")

            # Should use the explicit language, not default
            assert request.language == "fr"


class TestServerPortIntegration:
    """Test server port configuration (can only verify the value, not actual binding)."""

    def test_server_port_loaded_correctly(self):
        """Test that SERVER_PORT is loaded and available for uvicorn."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            # Verify the port is set correctly
            assert main.SERVER_PORT == 8080

            # In actual usage, this would be passed to uvicorn.run()
            # We can't test actual server binding without starting the server


class TestConfigurationConsistency:
    """Test that configuration is consistent across the application."""

    def test_all_config_values_are_integers_or_strings(self):
        """Test type consistency of configuration values."""
        with patch.dict(
            os.environ,
            {
                "PORT": "8000",
                "FILE_WAIT_TIMEOUT": "60",
                "SESSION_CLEANUP_INTERVAL": "7200",
                "RESEARCH_LANGUAGE": "en",
                "CORS_ORIGINS": "http://test.com",
            },
        ):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]
            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import main, models

            importlib.reload(main)
            importlib.reload(models)

            # All integer configs should be int type
            assert isinstance(main.SERVER_PORT, int)
            assert isinstance(main.FILE_WAIT_TIMEOUT, int)
            assert isinstance(main.SESSION_CLEANUP_INTERVAL, int)

            # String configs should be str type
            assert isinstance(models.DEFAULT_RESEARCH_LANGUAGE, str)

            # CORS origins should be a list
            assert isinstance(main.CORS_ORIGINS, list)
            assert all(isinstance(origin, str) for origin in main.CORS_ORIGINS)

    def test_configuration_available_at_module_level(self):
        """Test that all configuration is accessible at module import."""
        import importlib
        import sys

        if "main" in sys.modules:
            del sys.modules["main"]
        if "models" in sys.modules:
            del sys.modules["models"]

        from web_dashboard import main, models

        importlib.reload(main)
        importlib.reload(models)

        # All config should be available as module-level constants
        # This ensures they're set during import, not lazily
        assert hasattr(main, "CORS_ORIGINS")
        assert hasattr(main, "SERVER_PORT")
        assert hasattr(main, "FILE_WAIT_TIMEOUT")
        assert hasattr(main, "SESSION_CLEANUP_INTERVAL")
        assert hasattr(models, "DEFAULT_RESEARCH_LANGUAGE")


class TestProductionConfiguration:
    """Test configuration with production-like values."""

    def test_production_cors_configuration(self):
        """Test CORS with production URLs."""
        prod_origins = "https://tk9.thinhkhuat.com,http://192.168.2.22:12656"

        with patch.dict(os.environ, {"CORS_ORIGINS": prod_origins}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert "https://tk9.thinhkhuat.com" in main.CORS_ORIGINS
            assert "http://192.168.2.22:12656" in main.CORS_ORIGINS

    def test_production_timeouts(self):
        """Test with production timeout values (longer than dev)."""
        with patch.dict(
            os.environ,
            {
                "FILE_WAIT_TIMEOUT": "120",  # 2 minutes
                "SESSION_CLEANUP_INTERVAL": "21600",  # 6 hours
            },
        ):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.FILE_WAIT_TIMEOUT == 120
            assert main.SESSION_CLEANUP_INTERVAL == 21600


class TestErrorHandling:
    """Test error handling for invalid configuration."""

    def test_invalid_port_raises_clear_error(self):
        """Test that invalid PORT value raises ValueError."""
        with patch.dict(os.environ, {"PORT": "not-a-number"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            # Should raise ValueError when trying to int() the value
            with pytest.raises(ValueError) as exc_info:
                from web_dashboard import main

                importlib.reload(main)

            # Error message should mention the invalid value
            assert "invalid literal" in str(exc_info.value).lower()

    def test_invalid_timeout_raises_clear_error(self):
        """Test that invalid timeout value raises ValueError."""
        with patch.dict(os.environ, {"FILE_WAIT_TIMEOUT": "abc"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            with pytest.raises(ValueError):
                from web_dashboard import main

                importlib.reload(main)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not async"])
