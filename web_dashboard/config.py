"""
Centralized configuration management using Pydantic BaseSettings.

This module provides type-safe, validated configuration for the TK9 Deep Research
web dashboard. All configuration values are loaded from environment variables with
sensible defaults.

Environment Variables:
    PORT: Server port (default: 12656)
    CORS_ORIGINS: Comma-separated list of allowed origins (default: localhost origins)
    FILE_WAIT_TIMEOUT: Timeout in seconds for file generation (default: 30)
    SESSION_CLEANUP_INTERVAL: Interval in seconds between cleanup runs (default: 3600)
    RESEARCH_LANGUAGE: Default language for research output (default: "vi")

Example:
    >>> from web_dashboard.config import settings
    >>> print(settings.PORT)
    12656
    >>> print(settings.CORS_ORIGINS)
    ['http://localhost:5173', ...]
"""

from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with automatic environment variable loading.

    Uses Pydantic BaseSettings for:
    - Automatic type casting
    - Validation with clear error messages
    - .env file loading support
    - Single source of truth for configuration
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars not defined here
    )

    # ============================================================
    # Server Configuration
    # ============================================================

    PORT: int = Field(default=12656, description="Server port to bind to", ge=1, le=65535)

    HOST: str = Field(
        default="0.0.0.0",
        description="Server host to bind to (0.0.0.0 for all interfaces)",
    )

    # ============================================================
    # CORS Configuration
    # ============================================================

    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:12656",
            "http://127.0.0.1:12656",
        ],
        description="Allowed CORS origins (comma-separated string or list)",
    )

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        Parse CORS origins from various input formats.

        Handles:
        - Wildcard: "*" → ["*"]
        - Comma-separated string: "http://a.com,http://b.com" → ["http://a.com", "http://b.com"]
        - List: ["http://a.com"] → ["http://a.com"]
        - Empty/None: Use default origins

        Args:
            v: Input value (str, list, or None)

        Returns:
            List of origin strings
        """
        # Default origins to use when input is empty
        default_origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:12656",
            "http://127.0.0.1:12656",
        ]

        # Handle wildcard
        if isinstance(v, str) and v.strip() == "*":
            return ["*"]

        # Handle comma-separated string
        if isinstance(v, str) and v.strip():
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else default_origins

        # Handle list (already parsed)
        if isinstance(v, list) and v:
            return v

        # Handle None or empty - use default
        return default_origins

    # ============================================================
    # Application Configuration
    # ============================================================

    FILE_WAIT_TIMEOUT: int = Field(
        default=30,
        description="Timeout in seconds to wait for file generation",
        ge=1,
        le=3600,
    )

    SESSION_CLEANUP_INTERVAL: int = Field(
        default=3600,
        description="Interval in seconds between session cleanup runs",
        ge=60,
        le=86400,
    )

    RESEARCH_LANGUAGE: str = Field(
        default="vi",
        description="Default language for research output",
        min_length=2,
        max_length=10,
    )

    MAX_CONCURRENT_SESSIONS: int = Field(
        default=5,
        description="Maximum number of concurrent research sessions",
        ge=1,
        le=100,
    )

    SESSION_TIMEOUT: int = Field(
        default=3600, description="Session timeout in seconds", ge=60, le=86400
    )

    # ============================================================
    # Research Subject Validation
    # ============================================================

    MIN_SUBJECT_LENGTH: int = Field(
        default=3, description="Minimum length for research subject", ge=1, le=100
    )

    MAX_SUBJECT_LENGTH: int = Field(
        default=1000, description="Maximum length for research subject", ge=10, le=10000
    )

    # ============================================================
    # Supabase Configuration (Story 1.3)
    # ============================================================

    SUPABASE_URL: str = Field(default="", description="Supabase project URL")

    SUPABASE_SERVICE_KEY: str = Field(
        default="", description="Supabase service role key (bypasses RLS)"
    )

    SUPABASE_ANON_KEY: str = Field(default="", description="Supabase anonymous key (with RLS)")

    JWT_SECRET: str = Field(default="", description="JWT secret for validating Supabase tokens")

    # ============================================================
    # Helper Methods
    # ============================================================

    def is_production(self) -> bool:
        """Check if running in production mode based on CORS origins."""
        return any(origin.startswith("https://") for origin in self.CORS_ORIGINS)

    def get_cors_origins_display(self) -> str:
        """Get formatted string of CORS origins for logging."""
        if self.CORS_ORIGINS == ["*"]:
            return "* (all origins)"
        return ", ".join(self.CORS_ORIGINS)


# ============================================================
# Singleton Instance
# ============================================================

# Single, importable instance of Settings
# This is loaded once when the module is imported
settings = Settings()


# ============================================================
# Validation on Import
# ============================================================


def validate_settings():
    """
    Validate settings on import and log configuration.

    This function is called automatically when the module is imported
    to ensure all settings are valid and provide helpful startup logging.
    """
    import logging

    logger = logging.getLogger(__name__)

    # Log key configuration values
    logger.info("=" * 60)
    logger.info("Configuration Loaded (Pydantic BaseSettings)")
    logger.info("=" * 60)
    logger.info(f"Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"CORS Origins: {settings.get_cors_origins_display()}")
    logger.info(f"File Wait Timeout: {settings.FILE_WAIT_TIMEOUT}s")
    logger.info(f"Session Cleanup Interval: {settings.SESSION_CLEANUP_INTERVAL}s")
    logger.info(f"Default Language: {settings.RESEARCH_LANGUAGE}")
    logger.info(f"Max Concurrent Sessions: {settings.MAX_CONCURRENT_SESSIONS}")
    logger.info(f"Subject Length: {settings.MIN_SUBJECT_LENGTH}-{settings.MAX_SUBJECT_LENGTH}")

    # Validate critical configuration
    if not settings.SUPABASE_URL and settings.is_production():
        logger.warning("⚠️  SUPABASE_URL not set in production mode")

    if not settings.JWT_SECRET and settings.is_production():
        logger.warning("⚠️  JWT_SECRET not set in production mode")

    logger.info("=" * 60)


# Auto-validate on import
validate_settings()
