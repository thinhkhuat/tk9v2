# Provider Reference Documentation

## Overview

The Deep Research MCP system implements a sophisticated multi-provider architecture supporting multiple LLM and search providers with automatic failover, health monitoring, and cost optimization capabilities.

## Provider Architecture

### Core Components
- **Base Provider Classes**: Abstract interfaces for LLM and search providers
- **Factory Pattern**: Dynamic provider instantiation and management
- **Failover System**: Automatic provider switching on failures
- **Health Monitoring**: Continuous provider health checks
- **Configuration Management**: Environment-based provider configuration

### File Structure
```
multi_agents/providers/
├── base.py                      # Base provider interfaces
├── enhanced_base.py              # Enhanced provider with failover
├── factory.py                    # Provider factory implementation
├── enhanced_factory.py           # Enhanced factory with health checks
├── failover_integration.py      # Failover logic implementation
├── llm/                         # LLM provider implementations
│   ├── openai_provider.py
│   ├── google_gemini_provider.py
│   ├── anthropic_provider.py
│   └── azure_openai_provider.py
└── search/                      # Search provider implementations
    ├── tavily_provider.py
    ├── brave_provider.py
    ├── google_provider.py
    ├── duckduckgo_provider.py
    └── serpapi_provider.py
```

## LLM Providers

### 1. OpenAI Provider
**File**: `multi_agents/providers/llm/openai_provider.py`  
**Models Supported**:
- GPT-4o (latest)
- GPT-4o-mini
- GPT-4-turbo
- GPT-3.5-turbo

**Configuration**:
```bash
OPENAI_API_KEY=sk-your-api-key
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
```

**Features**:
- Function calling support
- Streaming responses
- Token usage tracking
- Rate limit handling

### 2. Google Gemini Provider
**File**: `multi_agents/providers/llm/google_gemini_provider.py`  
**Models Supported**:
- gemini-2.5-flash-preview-04-17-thinking (recommended)
- gemini-1.5-pro
- gemini-1.5-flash
- gemini-2.5-flash-preview variants

**Configuration**:
```bash
GOOGLE_API_KEY=your-google-api-key
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
```

**Features**:
- Multi-modal support
- Long context windows
- Fast inference
- Cost-effective

### 3. Anthropic Provider
**File**: `multi_agents/providers/llm/anthropic_provider.py`  
**Models Supported**:
- Claude-sonnet-4
- Claude-3-sonnet
- Claude-3-haiku
- Claude-3-opus

**Configuration**:
```bash
ANTHROPIC_API_KEY=your-anthropic-key
PRIMARY_LLM_PROVIDER=anthropic
PRIMARY_LLM_MODEL=claude-3-sonnet
```

**Features**:
- Constitutional AI
- Long context support
- XML tag support
- High-quality reasoning

### 4. Azure OpenAI Provider
**File**: `multi_agents/providers/llm/azure_openai_provider.py`  
**Models Supported**:
- GPT-4 (Azure deployment)
- GPT-3.5-turbo (Azure deployment)
- Custom deployments

**Configuration**:
```bash
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_NAME=your-deployment
PRIMARY_LLM_PROVIDER=azure_openai
```

**Features**:
- Enterprise security
- Private endpoints
- Regional deployments
- Compliance features

## Search Providers

### 1. BRAVE Search Provider
**File**: `multi_agents/providers/search/brave_provider.py`  
**Custom Integration**: `multi_agents/simple_brave_retriever.py`

**Configuration**:
```bash
BRAVE_API_KEY=your-brave-api-key
PRIMARY_SEARCH_PROVIDER=brave
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local
```

**Features**:
- Independent search engine
- News and web results
- No tracking
- Custom retriever integration
- Module patching for GPT-researcher

**Custom Retriever Details**:
- Converts BRAVE API responses to GPT-researcher format
- Early initialization before GPT-researcher imports
- X-Subscription-Token authentication
- Supports both web and news searches

### 2. Tavily Provider
**File**: `multi_agents/providers/search/tavily_provider.py`

**Configuration**:
```bash
TAVILY_API_KEY=tvly-your-api-key
PRIMARY_SEARCH_PROVIDER=tavily
```

**Features**:
- AI-optimized search
- Deep research capabilities
- Semantic understanding
- Research-focused results

### 3. Google Search Provider
**File**: `multi_agents/providers/search/google_provider.py`

**Configuration**:
```bash
GOOGLE_SEARCH_API_KEY=your-google-search-key
GOOGLE_SEARCH_ENGINE_ID=your-cse-id
PRIMARY_SEARCH_PROVIDER=google
```

**Features**:
- Custom Search Engine API
- Site-specific searches
- Advanced operators
- Image search support

### 4. DuckDuckGo Provider
**File**: `multi_agents/providers/search/duckduckgo_provider.py`

**Configuration**:
```bash
PRIMARY_SEARCH_PROVIDER=duckduckgo
# No API key required
```

**Features**:
- Privacy-focused
- No API key needed
- Instant answers
- Regional search

### 5. SerpAPI Provider
**File**: `multi_agents/providers/search/serpapi_provider.py`

**Configuration**:
```bash
SERPAPI_KEY=your-serpapi-key
PRIMARY_SEARCH_PROVIDER=serpapi
```

**Features**:
- Google search scraping
- Multiple search engines
- Location-based results
- SERP features extraction

## Provider Configuration

### Environment Variables
```bash
# Multi-Provider Configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_MODEL=gpt-4o-mini

PRIMARY_SEARCH_PROVIDER=brave
FALLBACK_SEARCH_PROVIDER=tavily

# Provider Strategies
LLM_STRATEGY=fallback_on_error    # Options: primary_only, fallback_on_error, round_robin
SEARCH_STRATEGY=fallback_on_error  # Options: primary_only, fallback_on_error, round_robin

# Timeout Configuration
PROVIDER_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1

# Cost Optimization
ENABLE_COST_TRACKING=true
MAX_COST_PER_REQUEST=1.0
```

### Configuration File (`multi_agents/config/providers.py`)
```python
PROVIDER_CONFIG = {
    "llm": {
        "primary": {
            "provider": "google_gemini",
            "model": "gemini-2.5-flash-preview-04-17-thinking",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "fallback": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    },
    "search": {
        "primary": {
            "provider": "brave",
            "max_results": 10,
            "search_type": "web"
        },
        "fallback": {
            "provider": "tavily",
            "max_results": 10,
            "search_depth": "advanced"
        }
    }
}
```

## Failover System

### Failover Strategies

#### 1. Primary Only
- Uses only the primary provider
- Fails immediately if primary is unavailable
- Best for testing and development

#### 2. Fallback on Error
- Attempts primary provider first
- Switches to fallback on failure
- Returns to primary after cooldown period
- Recommended for production

#### 3. Round Robin
- Distributes requests across providers
- Load balancing for high volume
- Useful for rate limit management

### Health Monitoring

**Health Check Implementation**:
```python
class ProviderHealthMonitor:
    def check_health(self, provider):
        # Ping endpoint
        # Validate response time
        # Check error rates
        # Monitor token usage
        # Track cost metrics
```

**Health Metrics**:
- Response time
- Error rate
- Success rate
- Token usage
- Cost per request

### Error Handling

**Provider Errors**:
1. **Authentication Errors**: Invalid API keys
2. **Rate Limit Errors**: Quota exceeded
3. **Timeout Errors**: Slow responses
4. **Service Errors**: Provider outages
5. **Validation Errors**: Invalid parameters

**Recovery Mechanisms**:
- Exponential backoff retry
- Circuit breaker pattern
- Graceful degradation
- Error aggregation and reporting

## Provider Factory

### Factory Pattern Implementation
```python
class ProviderFactory:
    @staticmethod
    def create_llm_provider(provider_name: str):
        # Dynamic provider instantiation
        # Configuration injection
        # Health check initialization
        # Failover setup
        
    @staticmethod
    def create_search_provider(provider_name: str):
        # Provider selection
        # API key validation
        # Custom configuration
        # Error handling setup
```

### Provider Registration
```python
# Register custom provider
ProviderFactory.register_provider(
    "custom_llm",
    CustomLLMProvider,
    config={...}
)
```

## Cost Management

### Cost Tracking
```python
class CostTracker:
    def track_request(self, provider, tokens, operation):
        # Calculate cost based on provider pricing
        # Log usage metrics
        # Alert on threshold exceeded
        # Generate cost reports
```

### Provider Pricing (Approximate)
| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|----------------------|------------------------|
| OpenAI | GPT-4o | $5.00 | $15.00 |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 |
| Google | Gemini 1.5 Flash | $0.35 | $1.05 |
| Anthropic | Claude 3 Sonnet | $3.00 | $15.00 |
| Tavily | Search API | $0.001 per search | - |
| BRAVE | Search API | $0.003 per search | - |

## Performance Optimization

### Caching Strategy
- Response caching for identical queries
- Provider response caching
- Search result deduplication
- Token usage optimization

### Parallel Processing
- Concurrent provider requests
- Batch processing support
- Async/await throughout
- Connection pooling

### Rate Limiting
- Per-provider rate limits
- Global rate limiting
- Request queuing
- Backpressure handling

## Testing Providers

### Unit Testing
```bash
# Test specific provider
python -m pytest tests/unit/test_providers.py::TestGoogleGeminiProvider

# Test all providers
python -m pytest tests/unit/test_providers.py
```

### Integration Testing
```bash
# Test provider failover
python -m pytest tests/integration/test_multi_provider_workflows.py

# Test provider factory
python tests/test_providers.py
```

### Provider Status Check
```bash
# Check provider configuration
python main.py --provider-info

# Test provider connectivity
python -c "from multi_agents.providers.factory import ProviderFactory; ProviderFactory.test_providers()"
```

## Troubleshooting

### Common Issues

#### 1. Provider Authentication Failed
```bash
# Check API key
echo $OPENAI_API_KEY

# Validate in .env file
grep "API_KEY" .env

# Test provider directly
python -c "from multi_agents.providers.llm.openai_provider import OpenAIProvider; OpenAIProvider().test_connection()"
```

#### 2. Failover Not Working
```bash
# Check strategy setting
echo $LLM_STRATEGY

# Verify fallback provider configured
echo $FALLBACK_LLM_PROVIDER

# Enable debug logging
export PROVIDER_DEBUG=true
```

#### 3. BRAVE Search Integration Issues
```bash
# Verify custom retriever setup
echo $RETRIEVER  # Should be "custom"

# Check endpoint configuration
echo $RETRIEVER_ENDPOINT  # Should be "https://brave-local-provider.local"

# Test BRAVE API directly
curl -H "X-Subscription-Token: $BRAVE_API_KEY" "https://api.search.brave.com/res/v1/web/search?q=test"
```

## Best Practices

### Configuration
1. Always configure both primary and fallback providers
2. Use environment variables for sensitive data
3. Set appropriate timeouts for your use case
4. Monitor provider costs regularly
5. Implement rate limiting proactively

### Development
1. Test with `primary_only` strategy first
2. Implement proper error handling
3. Log provider switches for debugging
4. Cache responses when appropriate
5. Use async operations throughout

### Production
1. Use `fallback_on_error` strategy
2. Implement health monitoring
3. Set up alerts for provider failures
4. Regular cost analysis
5. Provider performance benchmarking

## Future Enhancements

### Planned Features
- Dynamic provider selection based on query type
- ML-based provider routing
- Cost-optimized provider selection
- Custom provider plugins
- Provider response quality scoring
- A/B testing framework for providers