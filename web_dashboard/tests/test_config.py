"""
Test suite for Phase 1 configuration management.

Tests environment variable loading, parsing, and fallback behavior
for all 8 Phase 1 configuration items in the backend.
"""

import os
from unittest.mock import patch

import pytest


class TestCORSConfiguration:
    """Test CORS origins parsing and configuration."""

    def test_cors_origins_defaults(self):
        """Test that CORS origins use defaults when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Import after clearing env to test defaults
            import importlib
            import sys

            # Remove main module if already loaded
            if "main" in sys.modules:
                del sys.modules["main"]

            # Re-import to get fresh config
            from web_dashboard import main

            importlib.reload(main)

            origins = main.CORS_ORIGINS
            assert isinstance(origins, list)
            assert "http://localhost:5173" in origins
            assert "http://localhost:5174" in origins
            assert "http://127.0.0.1:5173" in origins
            assert "http://127.0.0.1:5174" in origins

    def test_cors_origins_from_env(self):
        """Test CORS origins parsing from comma-separated env var."""
        test_origins = "http://example.com,https://another.com,http://test.local"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            origins = main.CORS_ORIGINS
            assert origins == [
                "http://example.com",
                "https://another.com",
                "http://test.local",
            ]

    def test_cors_origins_wildcard(self):
        """Test CORS wildcard '*' handling."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            origins = main.CORS_ORIGINS
            assert origins == ["*"]

    def test_cors_origins_with_spaces(self):
        """Test CORS origins parsing handles spaces correctly."""
        test_origins = " http://example.com , https://another.com , http://test.local "

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            origins = main.CORS_ORIGINS
            # Should strip whitespace
            assert origins == [
                "http://example.com",
                "https://another.com",
                "http://test.local",
            ]

    def test_cors_origins_empty_string(self):
        """Test CORS origins with empty string env var falls back to defaults."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            origins = main.CORS_ORIGINS
            assert isinstance(origins, list)
            assert len(origins) > 0
            assert "http://localhost:5173" in origins


class TestServerConfiguration:
    """Test server port and timeout configurations."""

    def test_server_port_default(self):
        """Test server port uses default value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.SERVER_PORT == 12656

    def test_server_port_from_env(self):
        """Test server port from environment variable."""
        with patch.dict(os.environ, {"PORT": "8000"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.SERVER_PORT == 8000

    def test_server_port_invalid_raises_error(self):
        """Test invalid port value raises ValueError."""
        with patch.dict(os.environ, {"PORT": "not-a-number"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            with pytest.raises(ValueError):
                from web_dashboard import main

                importlib.reload(main)

    def test_file_wait_timeout_default(self):
        """Test file wait timeout uses default value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.FILE_WAIT_TIMEOUT == 30

    def test_file_wait_timeout_from_env(self):
        """Test file wait timeout from environment variable."""
        with patch.dict(os.environ, {"FILE_WAIT_TIMEOUT": "60"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.FILE_WAIT_TIMEOUT == 60

    def test_session_cleanup_interval_default(self):
        """Test session cleanup interval uses default value."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.SESSION_CLEANUP_INTERVAL == 3600

    def test_session_cleanup_interval_from_env(self):
        """Test session cleanup interval from environment variable."""
        with patch.dict(os.environ, {"SESSION_CLEANUP_INTERVAL": "7200"}):
            import importlib
            import sys

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            assert main.SESSION_CLEANUP_INTERVAL == 7200


class TestResearchConfiguration:
    """Test research language configuration."""

    def test_default_language_fallback(self):
        """Test default research language uses fallback."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import sys

            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import models

            importlib.reload(models)

            assert models.DEFAULT_RESEARCH_LANGUAGE == "vi"

    def test_default_language_from_env(self):
        """Test default research language from environment variable."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "en"}):
            import importlib
            import sys

            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import models

            importlib.reload(models)

            assert models.DEFAULT_RESEARCH_LANGUAGE == "en"

    def test_research_request_uses_default_language(self):
        """Test ResearchRequest model uses configured default language."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "fr"}):
            import importlib
            import sys

            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import models

            importlib.reload(models)

            # Create request without specifying language
            request = models.ResearchRequest(subject="Test research")
            assert request.language == "fr"


class TestConfigurationLogging:
    """Test that configuration values are logged on startup."""

    def test_cors_origins_logged(self, caplog):
        """Test CORS origins are logged on startup."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://test.com"}):
            import importlib
            import logging
            import sys

            caplog.set_level(logging.INFO)

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            # Check if CORS origins were logged
            assert any("CORS Origins" in record.message for record in caplog.records)

    def test_server_port_logged(self, caplog):
        """Test server port is logged on startup."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            import importlib
            import logging
            import sys

            caplog.set_level(logging.INFO)

            if "main" in sys.modules:
                del sys.modules["main"]

            from web_dashboard import main

            importlib.reload(main)

            # Check if server port was logged
            assert any("Server Port" in record.message for record in caplog.records)


class TestBackwardCompatibility:
    """Test backward compatibility with original hardcoded values."""

    def test_all_defaults_match_original_values(self):
        """Verify all defaults match the original hardcoded values."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import sys

            # Reload both modules
            if "main" in sys.modules:
                del sys.modules["main"]
            if "models" in sys.modules:
                del sys.modules["models"]

            from web_dashboard import main, models

            importlib.reload(main)
            importlib.reload(models)

            # Verify original defaults
            assert main.SERVER_PORT == 12656
            assert main.FILE_WAIT_TIMEOUT == 30
            assert main.SESSION_CLEANUP_INTERVAL == 3600
            assert models.DEFAULT_RESEARCH_LANGUAGE == "vi"
            assert isinstance(main.CORS_ORIGINS, list)
            assert len(main.CORS_ORIGINS) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
