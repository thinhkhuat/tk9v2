"""
Enhanced Provider Factory with Robust Failover Logic
Creates and manages provider instances with comprehensive error handling and health monitoring
"""

import logging
from typing import Any, Dict, List

from ..config.providers import (
    LLMConfig,
    LLMProvider,
    ProviderConfigManager,
    SearchConfig,
    SearchProvider,
)
from .enhanced_base import (
    EnhancedBaseLLMProvider,
    EnhancedBaseSearchProvider,
    EnhancedProviderManager,
    FailoverEvent,
)

# Import concrete implementations
from .llm.enhanced_gemini import EnhancedGeminiProvider
from .search.enhanced_brave import EnhancedBraveSearchProvider

logger = logging.getLogger(__name__)


class EnhancedProviderFactory:
    """Enhanced factory for creating provider instances with robust failover capabilities"""

    # Registry of enhanced providers
    LLM_PROVIDERS = {
        LLMProvider.GOOGLE_GEMINI: EnhancedGeminiProvider,
        # Add other enhanced LLM providers as they're implemented
    }

    SEARCH_PROVIDERS = {
        SearchProvider.BRAVE: EnhancedBraveSearchProvider,
        # Add other enhanced search providers as they're implemented
    }

    @classmethod
    def create_llm_provider(
        cls, config: LLMConfig, validate: bool = True
    ) -> EnhancedBaseLLMProvider:
        """
        Create an enhanced LLM provider instance with health monitoring

        Args:
            config: LLM provider configuration
            validate: Whether to validate configuration before creation

        Returns:
            EnhancedBaseLLMProvider instance

        Raises:
            ValueError: If provider is not supported or configuration is invalid
            RuntimeError: If configuration validation fails
        """
        if validate:
            cls._validate_llm_config(config)

        provider_class = cls.LLM_PROVIDERS.get(config.provider)

        if not provider_class:
            # For providers not yet implemented in enhanced layer, fallback to basic implementation
            from .factory import ProviderFactory

            basic_provider = ProviderFactory.create_llm_provider(config, validate=False)
            # Wrap basic provider in enhanced wrapper
            return cls._wrap_basic_llm_provider(basic_provider, config)

        # Convert config to dict format expected by provider
        provider_config = {
            "api_key": config.api_key,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "base_url": config.base_url,
            **config.extra_params,
            # Enhanced configuration
            "health_check_interval": 300,
            "health_check_timeout": 10,
            "max_consecutive_failures": 3,
        }

        return provider_class(provider_config)

    @classmethod
    def create_search_provider(
        cls, config: SearchConfig, validate: bool = True
    ) -> EnhancedBaseSearchProvider:
        """
        Create an enhanced search provider instance with health monitoring

        Args:
            config: Search provider configuration
            validate: Whether to validate configuration before creation

        Returns:
            EnhancedBaseSearchProvider instance

        Raises:
            ValueError: If provider is not supported
            RuntimeError: If configuration validation fails
        """
        if validate:
            cls._validate_search_config(config)

        provider_class = cls.SEARCH_PROVIDERS.get(config.provider)

        if not provider_class:
            # For providers not yet implemented in enhanced layer, fallback to basic implementation
            from .factory import ProviderFactory

            basic_provider = ProviderFactory.create_search_provider(config, validate=False)
            # Wrap basic provider in enhanced wrapper
            return cls._wrap_basic_search_provider(basic_provider, config)

        # Convert config to dict format expected by provider
        provider_config = {
            "api_key": config.api_key,
            "max_results": config.max_results,
            "search_depth": config.search_depth,
            "include_domains": config.include_domains,
            "exclude_domains": config.exclude_domains,
            **config.extra_params,
            # Enhanced configuration
            "health_check_interval": 300,
            "health_check_timeout": 10,
            "max_consecutive_failures": 3,
        }

        return provider_class(provider_config)

    @classmethod
    def _wrap_basic_llm_provider(
        cls, basic_provider, config: LLMConfig
    ) -> "WrappedBasicLLMProvider":
        """Wrap a basic LLM provider to work with enhanced manager"""
        return WrappedBasicLLMProvider(basic_provider, config)

    @classmethod
    def _wrap_basic_search_provider(
        cls, basic_provider, config: SearchConfig
    ) -> "WrappedBasicSearchProvider":
        """Wrap a basic search provider to work with enhanced manager"""
        return WrappedBasicSearchProvider(basic_provider, config)

    @classmethod
    def _validate_llm_config(cls, config: LLMConfig):
        """Enhanced validation for LLM configuration"""
        from .factory import ProviderFactory

        # Reuse existing validation logic
        ProviderFactory._validate_llm_config(config)

    @classmethod
    def _validate_search_config(cls, config: SearchConfig):
        """Enhanced validation for search configuration"""
        from .factory import ProviderFactory

        # Reuse existing validation logic
        ProviderFactory._validate_search_config(config)

    @classmethod
    async def create_provider_manager(
        cls,
        config_manager: ProviderConfigManager,
        validate: bool = True,
        enable_monitoring: bool = True,
    ) -> EnhancedProviderManager:
        """
        Create a fully configured enhanced provider manager

        Args:
            config_manager: Configuration manager instance
            validate: Whether to validate configurations before creating providers
            enable_monitoring: Whether to enable health monitoring

        Returns:
            EnhancedProviderManager with registered providers
        """
        manager = EnhancedProviderManager()

        # Configure manager settings
        manager.failover_enabled = True
        manager.health_check_interval = 300  # 5 minutes

        # Validate overall configuration first if requested
        if validate:
            try:
                config_manager.validate_before_operation("general")
            except RuntimeError as e:
                logger.warning(f"Configuration validation warning: {e}")
                logger.info("Continuing with provider creation...")

        # Create and register primary providers
        primary_llm_registered = False
        try:
            primary_llm = cls.create_llm_provider(
                config_manager.get_llm_config(), validate=validate
            )
            manager.register_llm_provider("primary", primary_llm, is_primary=True)
            primary_llm_registered = True
            logger.info(
                f"Primary LLM provider registered: {config_manager.get_llm_config().provider.value}"
            )
        except Exception as e:
            logger.error(f"Primary LLM provider creation failed: {e}")
            logger.info("System will attempt to use gpt-researcher integration as fallback")

        primary_search_registered = False
        try:
            primary_search = cls.create_search_provider(
                config_manager.get_search_config(), validate=validate
            )
            manager.register_search_provider("primary", primary_search, is_primary=True)
            primary_search_registered = True
            logger.info(
                f"Primary search provider registered: {config_manager.get_search_config().provider.value}"
            )
        except Exception as e:
            logger.error(f"Primary search provider creation failed: {e}")
            logger.info("System will attempt to use gpt-researcher integration as fallback")

        # Create and register fallback providers if configured
        if config_manager.config.fallback_llm and primary_llm_registered:
            try:
                fallback_llm = cls.create_llm_provider(
                    config_manager.get_llm_config(prefer_fallback=True), validate=validate
                )
                manager.register_llm_provider("fallback", fallback_llm, is_primary=False)
                logger.info(
                    f"Fallback LLM provider registered: {config_manager.config.fallback_llm.provider.value}"
                )
            except Exception as e:
                logger.warning(f"Fallback LLM provider creation failed: {e}")

        if config_manager.config.fallback_search and primary_search_registered:
            try:
                fallback_search = cls.create_search_provider(
                    config_manager.get_search_config(prefer_fallback=True), validate=validate
                )
                manager.register_search_provider("fallback", fallback_search, is_primary=False)
                logger.info(
                    f"Fallback search provider registered: {config_manager.config.fallback_search.provider.value}"
                )
            except Exception as e:
                logger.warning(f"Fallback search provider creation failed: {e}")

        # Enable monitoring if requested
        if enable_monitoring:
            manager.enable_monitoring()
            logger.info("Health monitoring enabled for all providers")

        # Add failover event logging
        def log_failover(event: FailoverEvent):
            logger.info(
                f"Failover executed: {event.from_provider} -> {event.to_provider} "
                f"(reason: {event.reason.value}, recovery_time: {event.recovery_time_ms}ms)"
            )
            if event.error_message:
                logger.debug(f"Failover error details: {event.error_message}")

        manager.add_failover_callback(log_failover)

        return manager


class WrappedBasicLLMProvider(EnhancedBaseLLMProvider):
    """Wrapper to adapt basic LLM providers to enhanced interface"""

    def __init__(self, basic_provider, config: LLMConfig):
        # Initialize enhanced base
        super().__init__(
            {
                "api_key": config.api_key,
                "model": config.model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                **config.extra_params,
            }
        )
        self.basic_provider = basic_provider
        self.config_obj = config

    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Delegate to basic provider"""
        return await self.basic_provider.generate(prompt, system_prompt, **kwargs)

    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs):
        """Delegate to basic provider"""
        async for chunk in self.basic_provider.generate_stream(prompt, system_prompt, **kwargs):
            yield chunk

    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Delegate to basic provider"""
        return self.basic_provider.estimate_cost(prompt, response)

    def validate_config(self) -> List[str]:
        """Delegate to basic provider"""
        return self.basic_provider.validate_config()


class WrappedBasicSearchProvider(EnhancedBaseSearchProvider):
    """Wrapper to adapt basic search providers to enhanced interface"""

    def __init__(self, basic_provider, config: SearchConfig):
        # Initialize enhanced base
        super().__init__(
            {
                "api_key": config.api_key,
                "max_results": config.max_results,
                "search_depth": config.search_depth,
                "include_domains": config.include_domains,
                "exclude_domains": config.exclude_domains,
                **config.extra_params,
            }
        )
        self.basic_provider = basic_provider
        self.config_obj = config

    async def search(self, query: str, **kwargs):
        """Delegate to basic provider"""
        return await self.basic_provider.search(query, **kwargs)

    async def news_search(self, query: str, **kwargs):
        """Delegate to basic provider"""
        return await self.basic_provider.news_search(query, **kwargs)

    def validate_config(self) -> List[str]:
        """Delegate to basic provider"""
        return self.basic_provider.validate_config()


class EnhancedGPTResearcherConfig:
    """Enhanced configuration bridge with improved failover support"""

    def __init__(
        self,
        config_manager: ProviderConfigManager,
        provider_manager: EnhancedProviderManager = None,
    ):
        self.config_manager = config_manager
        self.provider_manager = provider_manager
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

    async def switch_llm_provider(self, provider_name: str = None, use_fallback: bool = False):
        """Switch to specific LLM provider or fallback"""
        if self.provider_manager:
            # Use enhanced provider manager
            if use_fallback:
                await self.provider_manager.force_failover("llm", "fallback")
            elif provider_name:
                await self.provider_manager.force_failover("llm", provider_name)
        else:
            # Fallback to config-based switching
            llm_config = self.config_manager.get_llm_config(prefer_fallback=use_fallback)
            search_config = self.config_manager.get_search_config()

            # Update configuration
            new_config = self.config_manager.get_gpt_researcher_config(llm_config, search_config)
            self.gpt_researcher_config.update(new_config)

            # Apply to environment
            self.apply_to_environment()

    async def switch_search_provider(self, provider_name: str = None, use_fallback: bool = False):
        """Switch to specific search provider or fallback"""
        if self.provider_manager:
            # Use enhanced provider manager
            if use_fallback:
                await self.provider_manager.force_failover("search", "fallback")
            elif provider_name:
                await self.provider_manager.force_failover("search", provider_name)
        else:
            # Fallback to config-based switching
            llm_config = self.config_manager.get_llm_config()
            search_config = self.config_manager.get_search_config(prefer_fallback=use_fallback)

            # Update configuration
            new_config = self.config_manager.get_gpt_researcher_config(llm_config, search_config)
            self.gpt_researcher_config.update(new_config)

            # Apply to environment
            self.apply_to_environment()

    async def get_current_providers(self) -> Dict[str, Any]:
        """Get information about currently active providers"""
        if self.provider_manager:
            status = await self.provider_manager.get_comprehensive_status()
            return {
                "llm_provider": status["active_providers"]["llm"],
                "search_provider": status["active_providers"]["search"],
                "provider_health": {
                    name: info["health"] for name, info in status["llm_providers"].items()
                },
                "search_health": {
                    name: info["health"] for name, info in status["search_providers"].items()
                },
            }
        else:
            # Fallback to basic info
            llm_config = self.config_manager.get_llm_config()
            search_config = self.config_manager.get_search_config()

            return {
                "llm_provider": llm_config.provider.value,
                "llm_model": llm_config.model,
                "search_provider": search_config.provider.value,
                "search_max_results": search_config.max_results,
            }

    async def validate_current_config(self) -> Dict[str, Any]:
        """Validate current configuration and return comprehensive status"""
        issues = self.config_manager.validate_configuration()

        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "provider_info": self.config_manager.get_provider_info(),
            "gpt_researcher_config": self.gpt_researcher_config,
        }

        if self.provider_manager:
            # Add enhanced status information
            status = await self.provider_manager.get_comprehensive_status()
            result["enhanced_status"] = status

        return result


# Global enhanced instances for easy access
config_manager = ProviderConfigManager()
enhanced_provider_manager = None  # Will be initialized in main or as needed
enhanced_config = EnhancedGPTResearcherConfig(config_manager)


async def initialize_enhanced_system(enable_monitoring: bool = True) -> EnhancedProviderManager:
    """Initialize the enhanced provider system"""
    global enhanced_provider_manager, enhanced_config

    try:
        enhanced_provider_manager = await EnhancedProviderFactory.create_provider_manager(
            config_manager, validate=True, enable_monitoring=enable_monitoring
        )

        # Update enhanced config with provider manager
        enhanced_config.provider_manager = enhanced_provider_manager

        logger.info("Enhanced provider system initialized successfully")
        return enhanced_provider_manager

    except Exception as e:
        logger.error(f"Failed to initialize enhanced provider system: {e}")
        logger.info("Falling back to basic provider system")
        # Fallback to basic system
        from .factory import provider_manager

        return provider_manager


async def shutdown_enhanced_system():
    """Shutdown the enhanced provider system"""
    global enhanced_provider_manager

    if enhanced_provider_manager:
        await enhanced_provider_manager.cleanup()
        logger.info("Enhanced provider system shutdown completed")
