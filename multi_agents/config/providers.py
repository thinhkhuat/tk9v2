"""
Multi-Provider Configuration System
Supports seamless switching between LLM and search providers
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class SearchProvider(Enum):
    """Supported search providers"""
    TAVILY = "tavily"
    BRAVE = "brave"
    GOOGLE = "google"
    SERPAPI = "serpapi"
    DUCKDUCKGO = "duckduckgo"


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables"""
        key_mappings = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.GOOGLE_GEMINI: "GOOGLE_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY"
        }
        return os.getenv(key_mappings.get(self.provider))


@dataclass
class SearchConfig:
    """Configuration for search providers"""
    provider: SearchProvider
    api_key: Optional[str] = None
    max_results: int = 10
    search_depth: str = "advanced"
    include_domains: List[str] = field(default_factory=list)
    exclude_domains: List[str] = field(default_factory=list)
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = self._get_api_key()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables"""
        key_mappings = {
            SearchProvider.TAVILY: "TAVILY_API_KEY",
            SearchProvider.BRAVE: "BRAVE_API_KEY",
            SearchProvider.GOOGLE: "GOOGLE_API_KEY",
            SearchProvider.SERPAPI: "SERPAPI_API_KEY"
        }
        return os.getenv(key_mappings.get(self.provider))


@dataclass
class MultiProviderConfig:
    """Configuration for multi-provider system"""
    # Primary providers
    primary_llm: LLMConfig
    primary_search: SearchConfig
    
    # Fallback providers (optional)
    fallback_llm: Optional[LLMConfig] = None
    fallback_search: Optional[SearchConfig] = None
    
    # Provider selection strategy
    llm_strategy: str = "primary_only"  # primary_only, fallback_on_error, load_balance
    search_strategy: str = "primary_only"
    
    # Cost and performance settings
    enable_caching: bool = True
    cost_tracking: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3


class ProviderConfigManager:
    """Manages provider configurations and dynamic switching"""
    
    def __init__(self):
        self.config = self._load_config_from_env()
        self._validation_cache = None
        self._last_validation_time = None
    
    def _load_config_from_env(self) -> MultiProviderConfig:
        """Load configuration from environment variables"""
        
        # Primary LLM configuration
        primary_llm_provider = LLMProvider(os.getenv("PRIMARY_LLM_PROVIDER", "google_gemini"))
        primary_llm_model = os.getenv("PRIMARY_LLM_MODEL", self._get_default_model(primary_llm_provider))
        
        primary_llm = LLMConfig(
            provider=primary_llm_provider,
            model=primary_llm_model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.6")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "100000"))
        )
        
        # Primary search configuration
        primary_search_provider = SearchProvider(os.getenv("PRIMARY_SEARCH_PROVIDER", "tavily"))
        primary_search = SearchConfig(
            provider=primary_search_provider,
            max_results=int(os.getenv("SEARCH_MAX_RESULTS", "10")),
            search_depth=os.getenv("SEARCH_DEPTH", "advanced")
        )
        
        # Fallback providers (if configured)
        fallback_llm = None
        if os.getenv("FALLBACK_LLM_PROVIDER"):
            fallback_llm_provider = LLMProvider(os.getenv("FALLBACK_LLM_PROVIDER"))
            fallback_llm_model = os.getenv("FALLBACK_LLM_MODEL", self._get_default_model(fallback_llm_provider))
            fallback_llm = LLMConfig(
                provider=fallback_llm_provider,
                model=fallback_llm_model,
                temperature=float(os.getenv("FALLBACK_LLM_TEMPERATURE", "0.6")),
                max_tokens=int(os.getenv("FALLBACK_LLM_MAX_TOKENS", "100000"))
            )
        
        fallback_search = None
        if os.getenv("FALLBACK_SEARCH_PROVIDER"):
            fallback_search_provider = SearchProvider(os.getenv("FALLBACK_SEARCH_PROVIDER"))
            fallback_search = SearchConfig(
                provider=fallback_search_provider,
                max_results=int(os.getenv("FALLBACK_SEARCH_MAX_RESULTS", "10")),
                search_depth=os.getenv("FALLBACK_SEARCH_DEPTH", "advanced")
            )
        
        return MultiProviderConfig(
            primary_llm=primary_llm,
            primary_search=primary_search,
            fallback_llm=fallback_llm,
            fallback_search=fallback_search,
            llm_strategy=os.getenv("LLM_STRATEGY", "primary_only"),
            search_strategy=os.getenv("SEARCH_STRATEGY", "primary_only"),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            cost_tracking=os.getenv("COST_TRACKING", "true").lower() == "true",
            timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT", "30")),
            max_retries=int(os.getenv("PROVIDER_MAX_RETRIES", "3"))
        )
    
    def _get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for each provider"""
        defaults = {
            LLMProvider.OPENAI: "gpt-4.1",
            LLMProvider.GOOGLE_GEMINI: "gemini-2.5-flash-preview-05-20",
            LLMProvider.ANTHROPIC: "claude-sonnet-4-20250514",
            LLMProvider.AZURE_OPENAI: "gpt-4.1"
        }
        return defaults.get(provider, "gemini-2.5-flash-preview-05-20")
    
    def get_llm_config(self, prefer_fallback: bool = False) -> LLMConfig:
        """Get LLM configuration based on strategy"""
        if prefer_fallback and self.config.fallback_llm:
            return self.config.fallback_llm
        return self.config.primary_llm
    
    def get_search_config(self, prefer_fallback: bool = False) -> SearchConfig:
        """Get search configuration based on strategy"""
        if prefer_fallback and self.config.fallback_search:
            return self.config.fallback_search
        return self.config.primary_search
    
    def get_gpt_researcher_config(self, llm_config: Optional[LLMConfig] = None, 
                                 search_config: Optional[SearchConfig] = None) -> Dict[str, str]:
        """Convert to gpt-researcher compatible configuration"""
        llm_config = llm_config or self.config.primary_llm
        search_config = search_config or self.config.primary_search
        
        # Map to gpt-researcher format
        config = {}
        
        # LLM configuration
        if llm_config.provider == LLMProvider.OPENAI:
            config["SMART_LLM"] = f"openai:{llm_config.model}"
            config["FAST_LLM"] = f"openai:{llm_config.model}"
        elif llm_config.provider == LLMProvider.GOOGLE_GEMINI:
            config["SMART_LLM"] = f"google_genai:{llm_config.model}"
            config["FAST_LLM"] = f"google_genai:{llm_config.model}"
        elif llm_config.provider == LLMProvider.ANTHROPIC:
            config["SMART_LLM"] = f"anthropic:{llm_config.model}"
            config["FAST_LLM"] = f"anthropic:{llm_config.model}"
        
        # Search configuration
        if search_config.provider == SearchProvider.TAVILY:
            config["RETRIEVER"] = "tavily"
        elif search_config.provider == SearchProvider.BRAVE:
            # BRAVE integration will be handled by brave_retriever_integration.py
            # No need to set RETRIEVER here as the integration will handle it
            pass
        elif search_config.provider == SearchProvider.GOOGLE:
            config["RETRIEVER"] = "google"
        elif search_config.provider == SearchProvider.DUCKDUCKGO:
            config["RETRIEVER"] = "duckduckgo"
        
        # Additional parameters
        config["LLM_TEMPERATURE"] = str(llm_config.temperature)
        config["MAX_SEARCH_RESULTS"] = str(search_config.max_results)
        config["SEARCH_DEPTH"] = search_config.search_depth
        
        # API keys
        if llm_config.api_key:
            if llm_config.provider == LLMProvider.OPENAI:
                config["OPENAI_API_KEY"] = llm_config.api_key
            elif llm_config.provider == LLMProvider.GOOGLE_GEMINI:
                config["GOOGLE_API_KEY"] = llm_config.api_key
            elif llm_config.provider == LLMProvider.ANTHROPIC:
                config["ANTHROPIC_API_KEY"] = llm_config.api_key
        
        if search_config.api_key:
            if search_config.provider == SearchProvider.TAVILY:
                config["TAVILY_API_KEY"] = search_config.api_key
            elif search_config.provider == SearchProvider.BRAVE:
                config["BRAVE_API_KEY"] = search_config.api_key
            elif search_config.provider == SearchProvider.GOOGLE:
                # Use separate CSE API key for Google Custom Search if available
                # Otherwise fall back to the same GOOGLE_API_KEY
                cse_api_key = os.getenv("GOOGLE_CSE_API_KEY") or search_config.api_key
                config["GOOGLE_API_KEY"] = cse_api_key
                # Add Google CSE ID for Google search (gpt-researcher expects both names)
                if os.getenv("GOOGLE_CSE_ID"):
                    config["GOOGLE_CSE_ID"] = os.getenv("GOOGLE_CSE_ID")
                if os.getenv("GOOGLE_CX_KEY"):
                    config["GOOGLE_CX_KEY"] = os.getenv("GOOGLE_CX_KEY")
        
        return config
    
    def validate_configuration(self, use_cache: bool = True) -> List[str]:
        """
        Validate current configuration and return issues (legacy method for compatibility)
        
        Args:
            use_cache: Whether to use cached validation results
            
        Returns:
            List of validation issues (strings for backward compatibility)
        """
        import time
        
        # Check cache validity (cache for 60 seconds)
        current_time = time.time()
        if (use_cache and self._validation_cache and self._last_validation_time and 
            current_time - self._last_validation_time < 60):
            return self._validation_cache
        
        # Use the comprehensive validation system
        try:
            from .validation import config_validator
            validation_result = config_validator.run_comprehensive_validation(
                check_env_file=False,  # Skip file checks for runtime validation
                check_task_json=False,
                check_directories=False
            )
            
            # Extract error messages for backward compatibility
            issues = [f"[{issue.component}] {issue.message}" for issue in validation_result.issues]
            
            # Cache results
            self._validation_cache = issues
            self._last_validation_time = current_time
            
            return issues
            
        except ImportError:
            # Fallback to basic validation if comprehensive system not available
            return self._basic_validation()
    
    def _basic_validation(self) -> List[str]:
        """Basic validation fallback method"""
        issues = []
        
        # Check primary LLM
        if not self.config.primary_llm.api_key:
            issues.append(f"Missing API key for primary LLM provider: {self.config.primary_llm.provider.value}")
        
        # Check primary search
        if not self.config.primary_search.api_key and self.config.primary_search.provider != SearchProvider.DUCKDUCKGO:
            issues.append(f"Missing API key for primary search provider: {self.config.primary_search.provider.value}")
        
        # Check fallback providers if configured
        if self.config.fallback_llm and not self.config.fallback_llm.api_key:
            issues.append(f"Missing API key for fallback LLM provider: {self.config.fallback_llm.provider.value}")
        
        if self.config.fallback_search and not self.config.fallback_search.api_key and self.config.fallback_search.provider != SearchProvider.DUCKDUCKGO:
            issues.append(f"Missing API key for fallback search provider: {self.config.fallback_search.provider.value}")
        
        return issues
    
    def validate_before_operation(self, operation_type: str = "general") -> bool:
        """
        Validate configuration before performing an operation
        
        Args:
            operation_type: Type of operation (llm, search, general)
            
        Returns:
            True if configuration is valid for the operation
            
        Raises:
            RuntimeError: If critical configuration is missing
        """
        try:
            from .validation import config_validator
            
            if operation_type == "llm":
                result = config_validator.validate_llm_provider()
            elif operation_type == "search":
                result = config_validator.validate_search_provider()
            else:
                result = config_validator.validate_core_settings()
            
            if result.has_errors():
                error_messages = [issue.message for issue in result.issues]
                raise RuntimeError(
                    f"Configuration validation failed for {operation_type} operation:\n" + 
                    "\n".join(f"  - {msg}" for msg in error_messages)
                )
            
            return True
            
        except ImportError:
            # Fallback to basic validation
            issues = self._basic_validation()
            if issues:
                raise RuntimeError(
                    f"Configuration validation failed:\n" + 
                    "\n".join(f"  - {issue}" for issue in issues)
                )
            return True
    
    def get_validation_status(self) -> Dict[str, Any]:
        """
        Get comprehensive validation status
        
        Returns:
            Dictionary with validation results and recommendations
        """
        try:
            from .validation import config_validator, get_validation_summary
            
            return get_validation_summary()
            
        except ImportError:
            # Fallback to basic status
            issues = self._basic_validation()
            return {
                "valid": len(issues) == 0,
                "error_count": len(issues),
                "errors": [{"component": "Provider", "message": issue} for issue in issues],
                "configuration": self.get_provider_info()
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider configuration"""
        return {
            "primary_llm": {
                "provider": self.config.primary_llm.provider.value,
                "model": self.config.primary_llm.model,
                "has_api_key": bool(self.config.primary_llm.api_key)
            },
            "primary_search": {
                "provider": self.config.primary_search.provider.value,
                "has_api_key": bool(self.config.primary_search.api_key),
                "max_results": self.config.primary_search.max_results
            },
            "fallback_llm": {
                "provider": self.config.fallback_llm.provider.value if self.config.fallback_llm else None,
                "model": self.config.fallback_llm.model if self.config.fallback_llm else None,
                "has_api_key": bool(self.config.fallback_llm.api_key) if self.config.fallback_llm else False
            } if self.config.fallback_llm else None,
            "fallback_search": {
                "provider": self.config.fallback_search.provider.value if self.config.fallback_search else None,
                "has_api_key": bool(self.config.fallback_search.api_key) if self.config.fallback_search else False
            } if self.config.fallback_search else None,
            "strategies": {
                "llm": self.config.llm_strategy,
                "search": self.config.search_strategy
            }
        }


# Global configuration manager instance
config_manager = ProviderConfigManager()