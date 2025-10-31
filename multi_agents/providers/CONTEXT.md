# Provider System - Component Context

## Purpose

The Provider System is a multi-provider abstraction layer that enables TK9 to seamlessly work with multiple LLM and search providers with automatic failover. It provides a unified interface for OpenAI, Google Gemini, Anthropic, Azure OpenAI (LLMs) and BRAVE, Tavily, Google, DuckDuckGo (search), allowing dynamic provider switching without code changes.

## Current Status: Production Ready

**Last Updated**: 2025-10-31
**Status**: ✅ Stable - Multi-provider support with failover
**Recommended Setup**: Google Gemini + BRAVE Search (primary_only strategy)

## Component-Specific Development Guidelines

### Provider Configuration Pattern
```python
# Environment-based configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
FALLBACK_LLM_PROVIDER=openai
LLM_STRATEGY=fallback_on_error

# Usage in code
from multi_agents.providers.factory import enhanced_config

# Get current provider
current = enhanced_config.get_current_providers()
llm = enhanced_config.get_llm_instance()
search = enhanced_config.get_search_instance()
```

### Adding New LLM Provider
1. Create provider class in `llm/[provider_name].py`
2. Extend `BaseLLMProvider` interface
3. Register in `factory.py` LLM_PROVIDERS dict
4. Add to `LLMProvider` enum in `config/providers.py`
5. Update environment variable docs

### Adding New Search Provider
1. Create provider class in `search/[provider_name].py`
2. Extend `BaseSearchProvider` interface
3. Register in `factory.py` SEARCH_PROVIDERS dict
4. Add to `SearchProvider` enum in `config/providers.py`
5. Update environment variable docs

## Major Subsystem Organization

### 1. Provider Factory (`factory.py` - 420 lines)
**Central provider creation and management**

**Key Classes**:
- `ProviderFactory` - Creates provider instances from config
- `ProviderManager` - Manages provider lifecycle and failover
- `enhanced_config` - Global configuration instance

**Factory Pattern**:
```python
class ProviderFactory:
    LLM_PROVIDERS = {
        LLMProvider.GOOGLE_GEMINI: GeminiProvider,
        LLMProvider.OPENAI: OpenAIProvider,
        # ...
    }

    @classmethod
    def create_llm_provider(cls, config: LLMConfig) -> BaseLLMProvider:
        provider_class = cls.LLM_PROVIDERS.get(config.provider)
        return provider_class(provider_config)
```

### 2. Base Provider Interfaces (`base.py` - 230 lines)
**Abstract base classes for provider implementations**

**LLM Provider Interface**:
```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator:
        """Stream completion tokens"""
        pass
```

**Search Provider Interface**:
```python
class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Execute search query"""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Provider metadata and capabilities"""
        pass
```

### 3. LLM Provider Implementations (`llm/`)
**Concrete LLM provider classes**

**Available Providers**:
- `gemini.py` (150 lines) - Google Gemini with thinking models
- `openai_provider.py` (120 lines) - OpenAI GPT-3.5/4
- `anthropic.py` (110 lines) - Claude 3 Opus/Sonnet/Haiku
- `azure_openai.py` (130 lines) - Azure OpenAI deployment

**Example Implementation** (`llm/gemini.py`):
```python
class GeminiProvider(BaseLLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.client = genai.GenerativeModel(config["model"])
        self.config = config

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.generate_content_async(
            prompt,
            generation_config={
                "temperature": self.config["temperature"],
                "max_output_tokens": self.config["max_tokens"]
            }
        )
        return response.text
```

### 4. Search Provider Implementations (`search/`)
**Concrete search provider classes**

**Available Providers**:
- `brave.py` (180 lines) - BRAVE Search API (recommended primary)
- `tavily.py` (150 lines) - Tavily search (recommended fallback)
- `google_search.py` (140 lines) - Google Custom Search
- `duckduckgo.py` (120 lines) - DuckDuckGo API

**Example Implementation** (`search/brave.py`):
```python
class BraveSearchProvider(BaseSearchProvider):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config["api_key"]
        self.endpoint = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                self.endpoint,
                params={"q": query, "count": num_results},
                headers={"X-Subscription-Token": self.api_key}
            )
            data = await response.json()
            return self._parse_results(data)
```

### 5. Enhanced Factory System (`enhanced_factory.py` - 470 lines)
**Advanced provider management with failover**

**Features**:
- Automatic provider switching on failure
- Strategy-based failover (primary_only, fallback_on_error, round_robin)
- Provider health monitoring
- Request routing based on criteria

**Failover Logic**:
```python
class EnhancedProviderFactory:
    async def generate_with_failover(self, prompt: str) -> str:
        for provider in self.get_provider_sequence():
            try:
                result = await provider.generate(prompt)
                self._record_success(provider)
                return result
            except Exception as e:
                logger.warning(f"{provider} failed: {e}")
                self._record_failure(provider)
                continue
        raise RuntimeError("All providers failed")
```

### 6. Failover Integration (`failover_integration.py` - 350 lines)
**Integrates failover with gpt-researcher**

**Responsibilities**:
- Monitors provider health
- Triggers automatic failover
- Logs provider switches
- Maintains failure statistics

## Architectural Patterns

### 1. Strategy Pattern (Failover Strategies)
```python
class FailoverStrategy(Enum):
    PRIMARY_ONLY = "primary_only"          # No failover
    FALLBACK_ON_ERROR = "fallback_on_error"  # Switch on failure
    ROUND_ROBIN = "round_robin"            # Rotate providers
```

### 2. Factory Pattern (Provider Creation)
Centralized provider instantiation with validation

### 3. Dependency Injection
Providers injected into agents via configuration

### 4. Circuit Breaker
Providers temporarily disabled after repeated failures

### 5. Configuration Management
Environment-driven with Pydantic validation

## Integration Points

### Upstream Dependencies
- **Multi-Agent System** (`/multi_agents/`) - Consumes providers
- **Configuration** (`/multi_agents/config/`) - Provider settings
- **Orchestrator** (`/multi_agents/agents/orchestrator.py`) - Initializes providers

### Downstream Dependencies
- **External APIs**: OpenAI, Google, Anthropic, Azure, BRAVE, Tavily
- **gpt-researcher**: Uses provider configuration
- **Environment Variables**: API keys and settings

### Environment Variables
```bash
# LLM Configuration
PRIMARY_LLM_PROVIDER=google_gemini  # openai|google_gemini|anthropic|azure_openai
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
FALLBACK_LLM_PROVIDER=openai
LLM_STRATEGY=fallback_on_error

# Search Configuration
PRIMARY_SEARCH_PROVIDER=brave  # brave|tavily|google|duckduckgo
FALLBACK_SEARCH_PROVIDER=tavily
SEARCH_STRATEGY=fallback_on_error

# API Keys
GOOGLE_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
BRAVE_API_KEY=your_key
TAVILY_API_KEY=your_key
```

## Performance Considerations

### Provider Latency
- **Google Gemini**: ~500ms average (fastest)
- **OpenAI GPT-4**: ~2000ms average
- **Anthropic Claude**: ~1000ms average
- **BRAVE Search**: ~300ms average

### Cost Optimization
- **Primary Strategy**: Use fastest/cheapest provider
- **Failover Strategy**: Balance cost and availability
- **Caching**: Provider-level caching where available

### Rate Limiting
- Each provider has independent rate limits
- Failover distributes load across providers
- Circuit breaker prevents quota exhaustion

## Common Issues and Solutions

### Issue: Provider API Key Invalid
**Solution**: Configuration validation at startup
```bash
python main.py --config  # Validate configuration
```

### Issue: All Providers Failing
**Solution**: Check network, API status, and rate limits
**Pattern**: Failover exhausted all providers

### Issue: Slow Response Times
**Solution**: Switch to faster provider or adjust model
**Recommendation**: Use Google Gemini Flash models

### Issue: Rate Limit Exceeded
**Solution**: Configure failover to secondary provider
**Strategy**: `fallback_on_error` distributes load

## Cross-References

### Related Documentation
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Provider consumers
- **[Configuration](/multi_agents/config/CONTEXT.md)** - Provider settings
- **[Provider Reference](/ref/providers.md)** - Comprehensive provider guide
- **[Multi-Provider Guide](/docs/MULTI_PROVIDER_GUIDE.md)** - Setup instructions

### Key Files
- `multi_agents/providers/factory.py:1-420` - Factory implementation
- `multi_agents/providers/enhanced_factory.py:1-470` - Enhanced failover
- `multi_agents/providers/base.py:1-230` - Base interfaces
- `multi_agents/providers/llm/gemini.py:1-150` - Gemini provider
- `multi_agents/providers/search/brave.py:1-180` - BRAVE provider
- `multi_agents/config/providers.py` - Configuration models

---

*This component context provides architectural guidance for the Provider System. For detailed provider configuration, see `/docs/MULTI_PROVIDER_GUIDE.md`.*
