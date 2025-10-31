# Provider Integration Guide

## Provider System Architecture

The multi-provider system supports multiple LLM and search providers with automatic failover, load balancing, and environment-based configuration.

## Existing Provider Structure

```
multi_agents/
├── providers/
│   ├── __init__.py              # Provider registry
│   ├── base.py                  # Base provider classes
│   ├── llm/
│   │   ├── openai_provider.py   # OpenAI GPT models
│   │   ├── google_provider.py   # Google Gemini models
│   │   ├── anthropic_provider.py # Claude models
│   │   └── azure_provider.py    # Azure OpenAI
│   └── search/
│       ├── brave_provider.py    # BRAVE Search
│       ├── tavily_provider.py   # Tavily AI Search
│       ├── google_provider.py   # Google Custom Search
│       └── duckduckgo_provider.py # DuckDuckGo
├── config/
│   └── providers.py             # Provider configuration
└── simple_brave_retriever.py    # BRAVE GPT-researcher integration
```

## Base Provider Classes

### BaseLLMProvider
```python
# File: multi_agents/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator

class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30)
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate API key"""
        pass
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get input/output cost per token"""
        return {"input": 0.0, "output": 0.0}
```

### BaseSearchProvider
```python
# File: multi_agents/providers/base.py
class BaseSearchProvider(ABC):
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
        self.max_results = kwargs.get('max_results', 10)
        self.timeout = kwargs.get('timeout', 15)
    
    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform search and return results"""
        pass
    
    @abstractmethod
    async def search_news(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search news specifically"""
        pass
    
    def validate_api_key(self) -> bool:
        """Validate API key if required"""
        return True
```

## LLM Provider Implementation

### Google Gemini Provider Example
```python
# File: multi_agents/providers/llm/google_provider.py
import google.generativeai as genai
from typing import AsyncGenerator
from multi_agents.providers.base import BaseLLMProvider

class GoogleGeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview-04-17-thinking", **kwargs):
        super().__init__(api_key, model, **kwargs)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        
        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Gemini"""
        try:
            response = await self.client.generate_content_async(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": kwargs.get('temperature', self.temperature),
                    "max_output_tokens": kwargs.get('max_tokens', self.max_tokens),
                }
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            response = await self.client.generate_content_async(
                prompt,
                safety_settings=self.safety_settings,
                stream=True,
                generation_config={
                    "temperature": kwargs.get('temperature', self.temperature),
                    "max_output_tokens": kwargs.get('max_tokens', self.max_tokens),
                }
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        return [
            "gemini-2.5-flash-preview-04-17-thinking",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ]
    
    def validate_api_key(self) -> bool:
        try:
            models = genai.list_models()
            return len(list(models)) > 0
        except:
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        # Gemini 2.5 Flash pricing (example)
        return {"input": 0.000001, "output": 0.000002}
```

## Search Provider Implementation

### BRAVE Search Provider Example
```python
# File: multi_agents/providers/search/brave_provider.py
import aiohttp
from typing import List, Dict, Any
from multi_agents.providers.base import BaseSearchProvider

class BraveSearchProvider(BaseSearchProvider):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.search.brave.com/res/v1"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }
    
    async def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform web search"""
        url = f"{self.base_url}/web/search"
        params = {
            "q": query,
            "count": kwargs.get('count', self.max_results),
            "search_lang": kwargs.get('lang', 'en'),
            "country": kwargs.get('country', 'US'),
            "safesearch": kwargs.get('safesearch', 'moderate'),
            "freshness": kwargs.get('freshness', 'pw'),  # Past week
            "text_decorations": False,
            "extra_snippets": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_web_results(data.get('web', {}).get('results', []))
                else:
                    raise Exception(f"BRAVE search failed: {response.status}")
    
    async def search_news(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search news specifically"""
        url = f"{self.base_url}/news/search"
        params = {
            "q": query,
            "count": kwargs.get('count', self.max_results),
            "search_lang": kwargs.get('lang', 'en'),
            "country": kwargs.get('country', 'US'),
            "freshness": kwargs.get('freshness', 'pd'),  # Past day
            "text_decorations": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_news_results(data.get('results', []))
                else:
                    raise Exception(f"BRAVE news search failed: {response.status}")
    
    def _format_web_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format web search results"""
        formatted = []
        for result in results:
            formatted.append({
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "snippet": result.get('description', ''),
                "published_date": result.get('age', ''),
                "source": "brave_web"
            })
        return formatted
    
    def _format_news_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Format news search results"""
        formatted = []
        for result in results:
            formatted.append({
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "snippet": result.get('description', ''),
                "published_date": result.get('age', ''),
                "source": "brave_news"
            })
        return formatted
    
    def validate_api_key(self) -> bool:
        """Validate BRAVE API key"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run async in already running loop
                return True  # Assume valid for now
            else:
                return asyncio.run(self._test_api_key())
        except:
            return False
    
    async def _test_api_key(self) -> bool:
        """Test API key with simple query"""
        try:
            results = await self.search("test", count=1)
            return len(results) >= 0  # API responds
        except:
            return False
```

## Provider Registration

### Provider Configuration
```python
# File: multi_agents/config/providers.py
from typing import Dict, Type, Any
from multi_agents.providers.base import BaseLLMProvider, BaseSearchProvider

# LLM Providers Registry
LLM_PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
    'openai': 'multi_agents.providers.llm.openai_provider.OpenAIProvider',
    'google_gemini': 'multi_agents.providers.llm.google_provider.GoogleGeminiProvider',
    'anthropic': 'multi_agents.providers.llm.anthropic_provider.AnthropicProvider',
    'azure': 'multi_agents.providers.llm.azure_provider.AzureOpenAIProvider',
}

# Search Providers Registry
SEARCH_PROVIDERS: Dict[str, Type[BaseSearchProvider]] = {
    'brave': 'multi_agents.providers.search.brave_provider.BraveSearchProvider',
    'tavily': 'multi_agents.providers.search.tavily_provider.TavilyProvider',
    'google': 'multi_agents.providers.search.google_provider.GoogleSearchProvider',
    'duckduckgo': 'multi_agents.providers.search.duckduckgo_provider.DuckDuckGoProvider',
}

# Model mappings
MODEL_MAPPINGS = {
    'openai': {
        'gpt-4o': 'gpt-4o',
        'gpt-4o-mini': 'gpt-4o-mini',
        'gpt-4-turbo': 'gpt-4-turbo-preview'
    },
    'google_gemini': {
        'gemini-2.5-flash': 'gemini-2.5-flash-preview-04-17-thinking',
        'gemini-1.5-pro': 'gemini-1.5-pro',
        'gemini-1.5-flash': 'gemini-1.5-flash'
    },
    'anthropic': {
        'claude-sonnet-4': 'claude-3.5-sonnet-20241022',
        'claude-3-sonnet': 'claude-3-sonnet-20240229',
        'claude-3-haiku': 'claude-3-haiku-20240307'
    }
}

# Default configurations
DEFAULT_CONFIGS = {
    'llm': {
        'temperature': 0.7,
        'max_tokens': 4000,
        'timeout': 30
    },
    'search': {
        'max_results': 10,
        'timeout': 15
    }
}
```

### Provider Factory
```python
# File: multi_agents/providers/__init__.py
import importlib
from typing import Optional, Dict, Any
from multi_agents.config.providers import LLM_PROVIDERS, SEARCH_PROVIDERS, DEFAULT_CONFIGS

class ProviderFactory:
    @staticmethod
    def create_llm_provider(provider_name: str, api_key: str, model: str, **kwargs) -> BaseLLMProvider:
        """Create LLM provider instance"""
        if provider_name not in LLM_PROVIDERS:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
        
        # Import provider class
        module_path, class_name = LLM_PROVIDERS[provider_name].rsplit('.', 1)
        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        
        # Merge with default config
        config = {**DEFAULT_CONFIGS['llm'], **kwargs}
        
        return provider_class(api_key=api_key, model=model, **config)
    
    @staticmethod
    def create_search_provider(provider_name: str, api_key: str = None, **kwargs) -> BaseSearchProvider:
        """Create search provider instance"""
        if provider_name not in SEARCH_PROVIDERS:
            raise ValueError(f"Unknown search provider: {provider_name}")
        
        # Import provider class
        module_path, class_name = SEARCH_PROVIDERS[provider_name].rsplit('.', 1)
        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        
        # Merge with default config
        config = {**DEFAULT_CONFIGS['search'], **kwargs}
        
        return provider_class(api_key=api_key, **config)
    
    @staticmethod
    def get_available_llm_providers() -> List[str]:
        """Get list of available LLM providers"""
        return list(LLM_PROVIDERS.keys())
    
    @staticmethod
    def get_available_search_providers() -> List[str]:
        """Get list of available search providers"""
        return list(SEARCH_PROVIDERS.keys())
```

## BRAVE Search Integration (Special Case)

The BRAVE search integration requires special handling for GPT-researcher compatibility:

```python
# File: multi_agents/simple_brave_retriever.py
import os
import aiohttp
from typing import List, Dict, Any

def setup_brave_retriever():
    """Setup BRAVE search integration BEFORE importing gpt_researcher"""
    
    class BraveSearcher:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.headers = {
                "Accept": "application/json", 
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key
            }
        
        async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
            """Search using BRAVE API"""
            url = "https://api.search.brave.com/res/v1/web/search"
            params = {
                "q": query,
                "count": max_results,
                "search_lang": "en",
                "country": "US",
                "safesearch": "moderate",
                "freshness": "pw",
                "text_decorations": False,
                "extra_snippets": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('web', {}).get('results', [])
                        
                        # Convert to GPT-researcher format
                        formatted_results = []
                        for result in results:
                            formatted_results.append({
                                "href": result.get('url', ''),
                                "title": result.get('title', ''),
                                "body": result.get('description', '')
                            })
                        return formatted_results
                    else:
                        return []
    
    # Patch the retriever before GPT-researcher imports
    brave_api_key = os.getenv('BRAVE_API_KEY')
    if brave_api_key:
        # Store the searcher globally for GPT-researcher to use
        import sys
        sys.modules['__brave_searcher__'] = BraveSearcher(brave_api_key)
```

## Multi-Provider Management

### Provider Manager
```python
# File: multi_agents/providers/manager.py
import os
from typing import Optional, List, Dict, Any
from multi_agents.providers import ProviderFactory
from multi_agents.providers.base import BaseLLMProvider, BaseSearchProvider

class ProviderManager:
    def __init__(self):
        self.llm_provider: Optional[BaseLLMProvider] = None
        self.search_provider: Optional[BaseSearchProvider] = None
        self.fallback_llm_provider: Optional[BaseLLMProvider] = None
        self.fallback_search_provider: Optional[BaseSearchProvider] = None
        
    def initialize_from_env(self):
        """Initialize providers from environment variables"""
        # Primary LLM provider
        primary_llm = os.getenv('PRIMARY_LLM_PROVIDER', 'google_gemini')
        primary_model = os.getenv('PRIMARY_LLM_MODEL', 'gemini-2.5-flash-preview-04-17-thinking')
        llm_api_key = self._get_api_key_for_provider(primary_llm)
        
        if llm_api_key:
            self.llm_provider = ProviderFactory.create_llm_provider(
                primary_llm, llm_api_key, primary_model
            )
        
        # Primary search provider
        primary_search = os.getenv('PRIMARY_SEARCH_PROVIDER', 'brave')
        search_api_key = self._get_api_key_for_provider(primary_search)
        
        self.search_provider = ProviderFactory.create_search_provider(
            primary_search, search_api_key
        )
        
        # Setup fallbacks if strategy allows
        strategy = os.getenv('LLM_STRATEGY', 'primary_only')
        if strategy == 'fallback_on_error':
            self._setup_fallbacks()
    
    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        key_mapping = {
            'openai': 'OPENAI_API_KEY',
            'google_gemini': 'GOOGLE_API_KEY', 
            'anthropic': 'ANTHROPIC_API_KEY',
            'azure': 'AZURE_OPENAI_API_KEY',
            'brave': 'BRAVE_API_KEY',
            'tavily': 'TAVILY_API_KEY',
            'google': 'GOOGLE_SEARCH_API_KEY'
        }
        return os.getenv(key_mapping.get(provider))
    
    def _setup_fallbacks(self):
        """Setup fallback providers"""
        # Implementation for fallback setup
        pass
    
    async def generate_with_fallback(self, prompt: str, **kwargs) -> str:
        """Generate with primary provider and fallback on error"""
        try:
            if self.llm_provider:
                return await self.llm_provider.generate(prompt, **kwargs)
        except Exception as e:
            if self.fallback_llm_provider:
                return await self.fallback_llm_provider.generate(prompt, **kwargs)
            raise e
    
    async def search_with_fallback(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search with primary provider and fallback on error"""
        try:
            if self.search_provider:
                return await self.search_provider.search(query, **kwargs)
        except Exception as e:
            if self.fallback_search_provider:
                return await self.fallback_search_provider.search(query, **kwargs)
            raise e
```

## Environment Configuration

### Required Environment Variables
```bash
# .env file example
# Primary providers
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave

# Provider strategies
LLM_STRATEGY=primary_only  # or fallback_on_error
SEARCH_STRATEGY=primary_only  # or fallback_on_error

# API Keys (provide only what you use)
GOOGLE_API_KEY=your_google_key
BRAVE_API_KEY=your_brave_key
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
ANTHROPIC_API_KEY=your_anthropic_key

# BRAVE Search specific (for GPT-researcher integration)
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local
```

## Testing Providers

### Unit Test Template
```python
# File: tests/unit/test_providers.py
import pytest
from unittest.mock import AsyncMock, patch
from multi_agents.providers.llm.google_provider import GoogleGeminiProvider

@pytest.mark.asyncio
async def test_google_provider_generate():
    provider = GoogleGeminiProvider("test_key", "gemini-1.5-flash")
    
    with patch.object(provider.client, 'generate_content_async') as mock_generate:
        mock_response = AsyncMock()
        mock_response.text = "Test response"
        mock_generate.return_value = mock_response
        
        result = await provider.generate("Test prompt")
        
        assert result == "Test response"
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_provider_factory():
    from multi_agents.providers import ProviderFactory
    
    provider = ProviderFactory.create_llm_provider(
        "google_gemini", 
        "test_key", 
        "gemini-1.5-flash"
    )
    
    assert provider is not None
    assert provider.model == "gemini-1.5-flash"
```

## Adding New Providers

### Checklist for New LLM Provider
1. Create provider class inheriting from `BaseLLMProvider`
2. Implement all abstract methods: `generate`, `generate_stream`, `get_available_models`, `validate_api_key`
3. Add provider to `LLM_PROVIDERS` registry
4. Add model mappings to `MODEL_MAPPINGS`
5. Add API key mapping to `ProviderManager._get_api_key_for_provider`
6. Create unit tests
7. Update `.env.example` with new environment variables
8. Document pricing in `get_cost_per_token` method

### Checklist for New Search Provider  
1. Create provider class inheriting from `BaseSearchProvider`
2. Implement abstract methods: `search`, `search_news`, `validate_api_key`
3. Add provider to `SEARCH_PROVIDERS` registry
4. Add API key mapping if required
5. Create unit tests
6. Update `.env.example` if API key required
7. Document rate limits and features