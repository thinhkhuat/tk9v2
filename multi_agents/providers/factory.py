"""
Provider Factory
Creates and manages LLM and Search provider instances
"""

import logging
from typing import Any, Dict

from ..config.providers import (
    LLMConfig,
    LLMProvider,
    ProviderConfigManager,
    SearchConfig,
    SearchProvider,
)
from .base import BaseLLMProvider, BaseSearchProvider, ProviderManager
from .llm.gemini import GeminiProvider
from .search.brave import BraveSearchProvider

# Enhanced system imports (with fallback)
try:
    from .enhanced_factory import EnhancedProviderFactory, initialize_enhanced_system
    from .failover_integration import failover_integration

    ENHANCED_SYSTEM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Enhanced provider system not available: {e}")
    ENHANCED_SYSTEM_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating provider instances"""

    # Registry of available providers
    LLM_PROVIDERS = {
        LLMProvider.GOOGLE_GEMINI: GeminiProvider,
        # Add other LLM providers here as they're implemented
    }

    SEARCH_PROVIDERS = {
        SearchProvider.BRAVE: BraveSearchProvider,
        # Add other search providers here as they're implemented
    }

    @classmethod
    def create_llm_provider(cls, config: LLMConfig, validate: bool = True) -> BaseLLMProvider:
        """
        Create an LLM provider instance

        Args:
            config: LLM provider configuration
            validate: Whether to validate configuration before creation

        Returns:
            BaseLLMProvider instance

        Raises:
            ValueError: If provider is not supported or configuration is invalid
            RuntimeError: If configuration validation fails
        """
        if validate:
            cls._validate_llm_config(config)

        provider_class = cls.LLM_PROVIDERS.get(config.provider)

        if not provider_class:
            # For providers not yet implemented in our abstraction layer,
            # we can still use them through gpt-researcher
            raise ValueError(
                f"LLM provider {config.provider.value} not implemented in abstraction layer"
            )

        # Convert config to dict format expected by provider
        provider_config = {
            "api_key": config.api_key,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "base_url": config.base_url,
            **config.extra_params,
        }

        return provider_class(provider_config)

    @classmethod
    def _validate_llm_config(cls, config: LLMConfig):
        """Validate LLM configuration before creating provider"""
        issues = []

        # Check API key
        if not config.api_key:
            issues.append(f"Missing API key for {config.provider.value}")
        elif config.api_key.startswith("your_") or config.api_key == "not_configured":
            issues.append(f"API key for {config.provider.value} contains placeholder value")

        # Check model
        if not config.model:
            issues.append(f"Model not specified for {config.provider.value}")

        # Check numeric values
        if config.temperature < 0.0 or config.temperature > 2.0:
            issues.append(f"Temperature {config.temperature} outside valid range (0.0-2.0)")

        if config.max_tokens < 1:
            issues.append(f"Max tokens {config.max_tokens} must be positive")

        if issues:
            raise RuntimeError(
                f"LLM configuration validation failed for {config.provider.value}:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )

    @classmethod
    def create_search_provider(
        cls, config: SearchConfig, validate: bool = True
    ) -> BaseSearchProvider:
        """
        Create a search provider instance

        Args:
            config: Search provider configuration
            validate: Whether to validate configuration before creation

        Returns:
            BaseSearchProvider instance

        Raises:
            ValueError: If provider is not supported
            RuntimeError: If configuration validation fails
        """
        if validate:
            cls._validate_search_config(config)

        provider_class = cls.SEARCH_PROVIDERS.get(config.provider)

        if not provider_class:
            raise ValueError(
                f"Search provider {config.provider.value} not implemented in abstraction layer"
            )

        # Convert config to dict format expected by provider
        provider_config = {
            "api_key": config.api_key,
            "max_results": config.max_results,
            "search_depth": config.search_depth,
            "include_domains": config.include_domains,
            "exclude_domains": config.exclude_domains,
            **config.extra_params,
        }

        return provider_class(provider_config)

    @classmethod
    def _validate_search_config(cls, config: SearchConfig):
        """Validate search configuration before creating provider"""
        issues = []

        # Check API key (if required)
        providers_requiring_api_key = [
            SearchProvider.TAVILY,
            SearchProvider.BRAVE,
            SearchProvider.GOOGLE,
            SearchProvider.SERPAPI,
        ]
        if config.provider in providers_requiring_api_key:
            if not config.api_key:
                issues.append(f"Missing API key for {config.provider.value}")
            elif config.api_key.startswith("your_") or config.api_key == "not_configured":
                issues.append(f"API key for {config.provider.value} contains placeholder value")

        # Check numeric values
        if config.max_results < 1 or config.max_results > 100:
            issues.append(f"Max results {config.max_results} outside valid range (1-100)")

        # Check search depth
        valid_depths = ["basic", "advanced", "standard"]
        if config.search_depth not in valid_depths:
            issues.append(
                f"Search depth '{config.search_depth}' not in valid options: {valid_depths}"
            )

        if issues:
            raise RuntimeError(
                f"Search configuration validation failed for {config.provider.value}:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
            )

    @classmethod
    def create_provider_manager(
        cls, config_manager: ProviderConfigManager, validate: bool = True
    ) -> ProviderManager:
        """
        Create a fully configured provider manager

        Args:
            config_manager: Configuration manager instance
            validate: Whether to validate configurations before creating providers

        Returns:
            ProviderManager with registered providers
        """
        manager = ProviderManager()

        # Validate overall configuration first if requested
        if validate:
            try:
                config_manager.validate_before_operation("general")
            except RuntimeError as e:
                print(f"⚠️  Configuration validation warning: {e}")
                print("   Continuing with provider creation...")

        # Create and register primary providers
        try:
            primary_llm = cls.create_llm_provider(
                config_manager.get_llm_config(), validate=validate
            )
            manager.register_llm_provider("primary", primary_llm)
        except (ValueError, RuntimeError) as e:
            # Log the specific error
            print(f"⚠️  Primary LLM provider creation failed: {e}")
            print("   Falling back to gpt-researcher integration")

        try:
            primary_search = cls.create_search_provider(
                config_manager.get_search_config(), validate=validate
            )
            manager.register_search_provider("primary", primary_search)
        except (ValueError, RuntimeError) as e:
            # Log the specific error
            print(f"⚠️  Primary search provider creation failed: {e}")
            print("   Falling back to gpt-researcher integration")

        # Create and register fallback providers if configured
        if config_manager.config.fallback_llm:
            try:
                fallback_llm = cls.create_llm_provider(
                    config_manager.get_llm_config(prefer_fallback=True), validate=validate
                )
                manager.register_llm_provider("fallback", fallback_llm)
            except (ValueError, RuntimeError) as e:
                print(f"⚠️  Fallback LLM provider creation failed: {e}")

        if config_manager.config.fallback_search:
            try:
                fallback_search = cls.create_search_provider(
                    config_manager.get_search_config(prefer_fallback=True), validate=validate
                )
                manager.register_search_provider("fallback", fallback_search)
            except (ValueError, RuntimeError) as e:
                print(f"⚠️  Fallback search provider creation failed: {e}")

        return manager


class EnhancedGPTResearcherConfig:
    """Enhanced configuration that bridges our provider system with gpt-researcher"""

    def __init__(self, config_manager: ProviderConfigManager):
        self.config_manager = config_manager
        self.gpt_researcher_config = None
        self._update_config()

    def _update_config(self):
        """Update gpt-researcher configuration based on current provider settings"""
        self.gpt_researcher_config = self.config_manager.get_gpt_researcher_config()

    def get_config_dict(self) -> Dict[str, str]:
        """Get configuration dictionary for gpt-researcher"""
        return self.gpt_researcher_config.copy()

    def apply_to_environment(self):
        """Apply configuration to environment variables"""
        import os

        for key, value in self.gpt_researcher_config.items():
            os.environ[key] = value

    def switch_llm_provider(self, use_fallback: bool = False):
        """Switch to primary or fallback LLM provider"""
        llm_config = self.config_manager.get_llm_config(prefer_fallback=use_fallback)
        search_config = self.config_manager.get_search_config()

        # Update configuration
        new_config = self.config_manager.get_gpt_researcher_config(llm_config, search_config)
        self.gpt_researcher_config.update(new_config)

        # Apply to environment
        self.apply_to_environment()

    def switch_search_provider(self, use_fallback: bool = False):
        """Switch to primary or fallback search provider"""
        llm_config = self.config_manager.get_llm_config()
        search_config = self.config_manager.get_search_config(prefer_fallback=use_fallback)

        # Update configuration
        new_config = self.config_manager.get_gpt_researcher_config(llm_config, search_config)
        self.gpt_researcher_config.update(new_config)

        # Apply to environment
        self.apply_to_environment()

    def get_current_providers(self) -> Dict[str, str]:
        """Get information about currently active providers"""
        llm_config = self.config_manager.get_llm_config()
        search_config = self.config_manager.get_search_config()

        return {
            "llm_provider": llm_config.provider.value,
            "llm_model": llm_config.model,
            "search_provider": search_config.provider.value,
            "search_max_results": search_config.max_results,
        }

    def validate_current_config(self) -> Dict[str, Any]:
        """Validate current configuration and return status"""
        issues = self.config_manager.validate_configuration()

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "provider_info": self.config_manager.get_provider_info(),
            "gpt_researcher_config": self.gpt_researcher_config,
        }


# Global instances for easy access
config_manager = ProviderConfigManager()
enhanced_config = EnhancedGPTResearcherConfig(config_manager)
provider_manager = ProviderFactory.create_provider_manager(config_manager)


# Enhanced system integration
class EnhancedSystemBridge:
    """Bridge between enhanced and basic provider systems"""

    def __init__(self):
        self.enhanced_available = ENHANCED_SYSTEM_AVAILABLE
        self.enhanced_initialized = False
        self.use_enhanced = True

    async def initialize_if_available(self):
        """Initialize enhanced system if available"""
        if not self.enhanced_available or self.enhanced_initialized:
            return

        try:
            await failover_integration.initialize(enable_monitoring=True)
            self.enhanced_initialized = failover_integration.is_initialized
            if self.enhanced_initialized:
                logger.info("Enhanced provider system initialized successfully")
            else:
                logger.info("Enhanced provider system initialization failed, using basic system")
        except Exception as e:
            logger.warning(f"Could not initialize enhanced system: {e}")
            self.enhanced_initialized = False

    async def get_llm_response(self, prompt: str, system_prompt: str = None, **kwargs):
        """Get LLM response using enhanced system if available"""
        if self.enhanced_initialized and self.use_enhanced:
            try:
                return await failover_integration.get_llm_response(prompt, system_prompt, **kwargs)
            except Exception as e:
                logger.error(f"Enhanced LLM generation failed: {e}")
                logger.info("Falling back to basic provider system")

        # Fallback to basic system
        return await provider_manager.llm_generate(prompt, system_prompt=system_prompt, **kwargs)

    async def get_search_results(self, query: str, search_type: str = "web", **kwargs):
        """Get search results using enhanced system if available"""
        if self.enhanced_initialized and self.use_enhanced:
            try:
                return await failover_integration.get_search_results(query, search_type, **kwargs)
            except Exception as e:
                logger.error(f"Enhanced search failed: {e}")
                logger.info("Falling back to basic provider system")

        # Fallback to basic system
        return await provider_manager.search_query(query, search_type=search_type, **kwargs)

    async def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            "enhanced_available": self.enhanced_available,
            "enhanced_initialized": self.enhanced_initialized,
            "using_enhanced": self.use_enhanced,
            "basic_provider_status": provider_manager.get_provider_status(),
        }

        if self.enhanced_initialized:
            try:
                status["enhanced_status"] = await failover_integration.get_comprehensive_status()
            except Exception as e:
                status["enhanced_status_error"] = str(e)

        return status

    def enable_enhanced(self):
        """Enable enhanced system usage"""
        self.use_enhanced = True

    def disable_enhanced(self):
        """Disable enhanced system usage (use basic only)"""
        self.use_enhanced = False

    async def cleanup(self):
        """Cleanup enhanced system resources"""
        if self.enhanced_initialized:
            try:
                await failover_integration.cleanup()
                self.enhanced_initialized = False
            except Exception as e:
                logger.error(f"Error during enhanced system cleanup: {e}")


# Global bridge instance
enhanced_bridge = EnhancedSystemBridge()


# Convenience functions for backward compatibility
async def get_enhanced_llm_response(prompt: str, system_prompt: str = None, **kwargs):
    """Get LLM response with enhanced failover if available"""
    return await enhanced_bridge.get_llm_response(prompt, system_prompt, **kwargs)


async def get_enhanced_search_results(query: str, search_type: str = "web", **kwargs):
    """Get search results with enhanced failover if available"""
    return await enhanced_bridge.get_search_results(query, search_type, **kwargs)


async def initialize_enhanced_providers():
    """Initialize enhanced provider system"""
    await enhanced_bridge.initialize_if_available()


async def get_provider_system_status():
    """Get status of provider systems"""
    return await enhanced_bridge.get_system_status()
