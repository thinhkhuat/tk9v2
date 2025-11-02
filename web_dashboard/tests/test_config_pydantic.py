"""
Test suite for Pydantic BaseSettings configuration management.

Tests environment variable loading, validation, and error handling
for the Pydantic-based configuration system.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestSettingsDefaults:
    """Test default values without environment variables."""

    def test_all_defaults_loaded(self):
        """Test that Settings loads with all default values."""
        from web_dashboard.config import Settings

        settings = Settings()

        # Server configuration
        assert settings.PORT == 12656
        assert settings.HOST == "0.0.0.0"

        # CORS configuration
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:5173" in settings.CORS_ORIGINS

        # Application configuration
        assert settings.FILE_WAIT_TIMEOUT == 30
        assert settings.SESSION_CLEANUP_INTERVAL == 3600
        assert settings.RESEARCH_LANGUAGE == "vi"

        # Validation configuration
        assert settings.MIN_SUBJECT_LENGTH == 3
        assert settings.MAX_SUBJECT_LENGTH == 1000

    def test_defaults_match_original_hardcoded_values(self):
        """Verify backward compatibility with original hardcoded values."""
        from web_dashboard.config import Settings

        settings = Settings()

        # These should match the original hardcoded values from Phase 1
        assert settings.PORT == 12656
        assert settings.FILE_WAIT_TIMEOUT == 30
        assert settings.SESSION_CLEANUP_INTERVAL == 3600
        assert settings.RESEARCH_LANGUAGE == "vi"


class TestCORSOriginsParsing:
    """Test CORS origins parsing with field validator."""

    def test_cors_wildcard(self):
        """Test CORS wildcard '*' handling."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.CORS_ORIGINS == ["*"]

    def test_cors_comma_separated(self):
        """Test comma-separated CORS origins."""
        test_origins = "http://example.com,https://another.com,http://test.local"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.CORS_ORIGINS == [
                "http://example.com",
                "https://another.com",
                "http://test.local",
            ]

    def test_cors_with_spaces(self):
        """Test CORS origins with spaces are trimmed."""
        test_origins = " http://example.com , https://another.com , http://test.local "

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.CORS_ORIGINS == [
                "http://example.com",
                "https://another.com",
                "http://test.local",
            ]

    def test_cors_empty_string_uses_defaults(self):
        """Test empty CORS string falls back to defaults."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert isinstance(settings.CORS_ORIGINS, list)
            assert len(settings.CORS_ORIGINS) > 0
            assert "http://localhost:5173" in settings.CORS_ORIGINS


class TestEnvironmentOverrides:
    """Test environment variable overrides."""

    def test_port_override(self):
        """Test PORT environment variable override."""
        with patch.dict(os.environ, {"PORT": "8000"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.PORT == 8000

    def test_file_wait_timeout_override(self):
        """Test FILE_WAIT_TIMEOUT environment variable override."""
        with patch.dict(os.environ, {"FILE_WAIT_TIMEOUT": "60"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.FILE_WAIT_TIMEOUT == 60

    def test_session_cleanup_interval_override(self):
        """Test SESSION_CLEANUP_INTERVAL environment variable override."""
        with patch.dict(os.environ, {"SESSION_CLEANUP_INTERVAL": "7200"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.SESSION_CLEANUP_INTERVAL == 7200

    def test_research_language_override(self):
        """Test RESEARCH_LANGUAGE environment variable override."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "en"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.RESEARCH_LANGUAGE == "en"

    def test_multiple_overrides(self):
        """Test multiple environment variable overrides at once."""
        with patch.dict(
            os.environ,
            {
                "PORT": "9000",
                "FILE_WAIT_TIMEOUT": "120",
                "RESEARCH_LANGUAGE": "fr",
                "CORS_ORIGINS": "https://prod.example.com",
            },
        ):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.PORT == 9000
            assert settings.FILE_WAIT_TIMEOUT == 120
            assert settings.RESEARCH_LANGUAGE == "fr"
            assert settings.CORS_ORIGINS == ["https://prod.example.com"]


class TestValidation:
    """Test Pydantic validation rules."""

    def test_port_out_of_range_raises_error(self):
        """Test that invalid port raises ValidationError."""
        with patch.dict(os.environ, {"PORT": "70000"}):
            from web_dashboard.config import Settings

            with pytest.raises(ValidationError) as exc_info:
                Settings()

            # Check error message mentions port validation
            errors = exc_info.value.errors()
            assert any("PORT" in str(error) or "port" in str(error).lower() for error in errors)

    def test_negative_port_raises_error(self):
        """Test that negative port raises ValidationError."""
        with patch.dict(os.environ, {"PORT": "-1"}):
            from web_dashboard.config import Settings

            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_port_type_raises_error(self):
        """Test that non-numeric port raises ValidationError."""
        with patch.dict(os.environ, {"PORT": "not-a-number"}):
            from web_dashboard.config import Settings

            with pytest.raises(ValidationError):
                Settings()

    def test_research_language_too_short_raises_error(self):
        """Test that too-short language code raises ValidationError."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "a"}):
            from web_dashboard.config import Settings

            with pytest.raises(ValidationError):
                Settings()

    def test_research_language_too_long_raises_error(self):
        """Test that too-long language code raises ValidationError."""
        with patch.dict(os.environ, {"RESEARCH_LANGUAGE": "a" * 11}):
            from web_dashboard.config import Settings

            with pytest.raises(ValidationError):
                Settings()


class TestHelperMethods:
    """Test Settings helper methods."""

    def test_is_production_false_for_http(self):
        """Test is_production() returns False for HTTP origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:5173"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.is_production() is False

    def test_is_production_true_for_https(self):
        """Test is_production() returns True for HTTPS origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://prod.example.com"}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.is_production() is True

    def test_is_production_true_for_mixed_origins(self):
        """Test is_production() returns True if any origin is HTTPS."""
        origins = "http://localhost:5173,https://prod.example.com"
        with patch.dict(os.environ, {"CORS_ORIGINS": origins}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.is_production() is True

    def test_get_cors_origins_display_normal(self):
        """Test get_cors_origins_display() for normal origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://example.com,http://test.com"}):
            from web_dashboard.config import Settings

            settings = Settings()
            display = settings.get_cors_origins_display()
            assert "http://example.com" in display
            assert "http://test.com" in display

    def test_get_cors_origins_display_wildcard(self):
        """Test get_cors_origins_display() for wildcard."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            from web_dashboard.config import Settings

            settings = Settings()
            display = settings.get_cors_origins_display()
            assert "all origins" in display.lower()


class TestProductionConfiguration:
    """Test production-like configuration."""

    def test_production_cors_origins(self):
        """Test production CORS configuration."""
        prod_origins = "https://tk9.thinhkhuat.com,http://192.168.2.22:12656"

        with patch.dict(os.environ, {"CORS_ORIGINS": prod_origins}):
            from web_dashboard.config import Settings

            settings = Settings()
            assert "https://tk9.thinhkhuat.com" in settings.CORS_ORIGINS
            assert "http://192.168.2.22:12656" in settings.CORS_ORIGINS

    def test_production_timeouts(self):
        """Test production timeout values."""
        with patch.dict(
            os.environ,
            {"FILE_WAIT_TIMEOUT": "120", "SESSION_CLEANUP_INTERVAL": "21600"},
        ):
            from web_dashboard.config import Settings

            settings = Settings()
            assert settings.FILE_WAIT_TIMEOUT == 120
            assert settings.SESSION_CLEANUP_INTERVAL == 21600


class TestSingletonBehavior:
    """Test that the settings singleton works correctly."""

    def test_settings_singleton_imported(self):
        """Test that settings singleton can be imported."""
        from web_dashboard.config import settings

        assert settings is not None
        assert settings.PORT == 12656  # Default value

    def test_settings_type_is_settings_class(self):
        """Test that settings is an instance of Settings."""
        from web_dashboard.config import Settings, settings

        assert isinstance(settings, Settings)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
