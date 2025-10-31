"""
Base classes for LLM and Search providers
Defines interfaces for multi-provider support
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """Standardized response from LLM providers"""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Individual search result"""
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResponse:
    """Standardized response from search providers"""
    results: List[SearchResult]
    query: str
    provider: str
    total_results: int = 0
    search_time_ms: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
        
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        """Generate text from the LLM"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming text from the LLM"""
        pass
    
    @abstractmethod
    def estimate_cost(self, prompt: str, response: str = "") -> float:
        """Estimate cost for the API call"""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": self.provider_name,
            "model": self.config.get("model", "unknown"),
            "max_tokens": self.config.get("max_tokens", 0),
            "temperature": self.config.get("temperature", 0.0)
        }


class BaseSearchProvider(ABC):
    """Base class for all search providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> SearchResponse:
        """Perform web search"""
        pass
    
    @abstractmethod
    async def news_search(self, query: str, **kwargs) -> SearchResponse:
        """Perform news search"""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate provider configuration"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the search provider"""
        return {
            "provider": self.provider_name,
            "max_results": self.config.get("max_results", 10),
            "search_depth": self.config.get("search_depth", "basic")
        }


class ProviderError(Exception):
    """Base exception for provider errors"""
    def __init__(self, message: str, provider: str, error_code: str = None):
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class LLMProviderError(ProviderError):
    """Exception for LLM provider errors"""
    pass


class SearchProviderError(ProviderError):
    """Exception for search provider errors"""
    pass


class ProviderManager:
    """Manages multiple providers with fallback and load balancing"""
    
    def __init__(self):
        self.llm_providers: Dict[str, BaseLLMProvider] = {}
        self.search_providers: Dict[str, BaseSearchProvider] = {}
        self.usage_stats = {
            "llm": {},
            "search": {}
        }
    
    def register_llm_provider(self, name: str, provider: BaseLLMProvider):
        """Register an LLM provider"""
        self.llm_providers[name] = provider
        self.usage_stats["llm"][name] = {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
            "last_used": None
        }
    
    def register_search_provider(self, name: str, provider: BaseSearchProvider):
        """Register a search provider"""
        self.search_providers[name] = provider
        self.usage_stats["search"][name] = {
            "requests": 0,
            "results": 0,
            "errors": 0,
            "last_used": None
        }
    
    async def llm_generate(self, prompt: str, provider_name: str = None, 
                          fallback: bool = True, **kwargs) -> LLMResponse:
        """Generate text with optional fallback"""
        providers = [provider_name] if provider_name else list(self.llm_providers.keys())
        
        last_error = None
        for provider_name in providers:
            if provider_name not in self.llm_providers:
                continue
                
            try:
                provider = self.llm_providers[provider_name]
                start_time = time.time()
                
                response = await provider.generate(prompt, **kwargs)
                
                # Update usage stats
                self._update_llm_stats(provider_name, response, time.time() - start_time)
                
                return response
                
            except Exception as e:
                last_error = e
                self.usage_stats["llm"][provider_name]["errors"] += 1
                
                if not fallback:
                    raise LLMProviderError(str(e), provider_name)
                
                continue
        
        # All providers failed
        raise LLMProviderError(f"All LLM providers failed. Last error: {last_error}", "all")
    
    async def search_query(self, query: str, provider_name: str = None, 
                          search_type: str = "web", fallback: bool = True, **kwargs) -> SearchResponse:
        """Perform search with optional fallback"""
        providers = [provider_name] if provider_name else list(self.search_providers.keys())
        
        last_error = None
        for provider_name in providers:
            if provider_name not in self.search_providers:
                continue
                
            try:
                provider = self.search_providers[provider_name]
                start_time = time.time()
                
                if search_type == "news":
                    response = await provider.news_search(query, **kwargs)
                else:
                    response = await provider.search(query, **kwargs)
                
                # Update usage stats
                self._update_search_stats(provider_name, response, time.time() - start_time)
                
                return response
                
            except Exception as e:
                last_error = e
                self.usage_stats["search"][provider_name]["errors"] += 1
                
                if not fallback:
                    raise SearchProviderError(str(e), provider_name)
                
                continue
        
        # All providers failed
        raise SearchProviderError(f"All search providers failed. Last error: {last_error}", "all")
    
    def _update_llm_stats(self, provider_name: str, response: LLMResponse, latency: float):
        """Update LLM usage statistics"""
        stats = self.usage_stats["llm"][provider_name]
        stats["requests"] += 1
        stats["tokens"] += response.tokens_used
        stats["cost"] += response.cost
        stats["last_used"] = time.time()
    
    def _update_search_stats(self, provider_name: str, response: SearchResponse, latency: float):
        """Update search usage statistics"""
        stats = self.usage_stats["search"][provider_name]
        stats["requests"] += 1
        stats["results"] += len(response.results)
        stats["last_used"] = time.time()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all providers"""
        return self.usage_stats.copy()
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        return {
            "llm_providers": {
                name: {
                    "available": True,
                    "info": provider.get_model_info(),
                    "stats": self.usage_stats["llm"][name]
                }
                for name, provider in self.llm_providers.items()
            },
            "search_providers": {
                name: {
                    "available": True,
                    "info": provider.get_provider_info(),
                    "stats": self.usage_stats["search"][name]
                }
                for name, provider in self.search_providers.items()
            }
        }