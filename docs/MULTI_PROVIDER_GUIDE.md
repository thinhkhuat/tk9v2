# Multi-Provider Configuration Guide

## Overview

The Deep Research MCP system now supports multiple LLM and search providers with seamless switching, fallback mechanisms, and comprehensive configuration management. This guide shows you how to configure and use different provider combinations.

## 🚀 Quick Start

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Configure Your Providers

**Option A: OpenAI + Tavily (Default)**
```bash
# Edit .env file
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
```

**Option B: Google Gemini + Brave Search**
```bash
# Edit .env file
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-1.5-pro
PRIMARY_SEARCH_PROVIDER=brave
GOOGLE_API_KEY=your_google_key_here
BRAVE_API_KEY=your_brave_key_here
```

### 3. Verify Configuration
```bash
python main.py --provider-info
```

### 4. Run Research
```bash
python main.py --research "Your research question"
```

## 🔧 Supported Providers

### LLM Providers

| Provider | Models | API Key Required | Notes |
|----------|--------|------------------|-------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo | OPENAI_API_KEY | Most reliable, fastest |
| **Google Gemini** | gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro | GOOGLE_API_KEY | Large context window |
| **Anthropic** | claude-3-sonnet, claude-3-haiku | ANTHROPIC_API_KEY | Via gpt-researcher |
| **Azure OpenAI** | gpt-4, gpt-35-turbo | AZURE_OPENAI_API_KEY | Enterprise option |

### Search Providers

| Provider | Features | API Key Required | Notes |
|----------|----------|------------------|-------|
| **Tavily** | AI-optimized search, deep research | TAVILY_API_KEY | Best for research |
| **Brave** | Independent search, news search | BRAVE_API_KEY | Privacy-focused |
| **Google** | Custom search engine | GOOGLE_API_KEY + CSE_ID | Most comprehensive |
| **DuckDuckGo** | Privacy search | None | Free, no tracking |
| **SerpAPI** | Google search scraping | SERPAPI_API_KEY | Reliable results |

## ⚙️ Configuration Options

### Environment Variables

#### Core Provider Settings
```bash
# Primary providers
PRIMARY_LLM_PROVIDER=openai|google_gemini|anthropic|azure_openai
PRIMARY_LLM_MODEL=model_name
PRIMARY_SEARCH_PROVIDER=tavily|brave|google|serpapi|duckduckgo

# Fallback providers (optional)
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_LLM_MODEL=gemini-1.5-pro
FALLBACK_SEARCH_PROVIDER=brave

# Provider strategies
LLM_STRATEGY=primary_only|fallback_on_error|load_balance
SEARCH_STRATEGY=primary_only|fallback_on_error|load_balance
```

#### Model Parameters
```bash
LLM_TEMPERATURE=0.7          # Creativity (0.0-2.0)
LLM_MAX_TOKENS=4000          # Response length
SEARCH_MAX_RESULTS=10        # Number of search results
SEARCH_DEPTH=advanced        # Search thoroughness
```

#### Advanced Settings
```bash
PROVIDER_TIMEOUT=30          # Request timeout (seconds)
PROVIDER_MAX_RETRIES=3       # Retry attempts
ENABLE_CACHING=true          # Cache responses
COST_TRACKING=true           # Track usage costs
```

## 🔀 Provider Strategies

### 1. Primary Only (Default)
- Uses only the primary provider
- Fails if primary provider is unavailable
- Best for: Consistent behavior, cost control

```bash
LLM_STRATEGY=primary_only
SEARCH_STRATEGY=primary_only
```

### 2. Fallback on Error
- Uses primary provider normally
- Switches to fallback if primary fails
- Best for: High reliability, automatic recovery

```bash
LLM_STRATEGY=fallback_on_error
SEARCH_STRATEGY=fallback_on_error
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_SEARCH_PROVIDER=brave
```

### 3. Load Balance (Future)
- Distributes requests across providers
- Optimizes for cost and performance
- Best for: High-volume usage

## 📋 Configuration Examples

### Example 1: Cost-Optimized Setup
```bash
# Use efficient models and free search
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-1.5-flash
PRIMARY_SEARCH_PROVIDER=duckduckgo
GOOGLE_API_KEY=your_google_key
```

### Example 2: High-Reliability Setup
```bash
# Primary: OpenAI + Tavily
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily

# Fallback: Gemini + Brave
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_LLM_MODEL=gemini-1.5-pro
FALLBACK_SEARCH_PROVIDER=brave

# Strategies
LLM_STRATEGY=fallback_on_error
SEARCH_STRATEGY=fallback_on_error

# API Keys
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
GOOGLE_API_KEY=your_google_key
BRAVE_API_KEY=your_brave_key
```

### Example 3: Privacy-Focused Setup
```bash
# Use providers with strong privacy policies
PRIMARY_LLM_PROVIDER=anthropic
PRIMARY_LLM_MODEL=claude-3-sonnet
PRIMARY_SEARCH_PROVIDER=duckduckgo
ANTHROPIC_API_KEY=your_anthropic_key
```

## 🛠️ CLI Commands

### Provider Management
```bash
# Show current provider status
python main.py --provider-info

# Show full configuration
python main.py --config

# List all available providers
python -c "from cli.providers import ProviderCLI; ProviderCLI.list_available_providers()"

# Show configuration examples
python -c "from cli.providers import ProviderCLI; ProviderCLI.show_configuration_examples()"
```

### Research with Specific Providers
```bash
# Standard research
python main.py --research "AI trends in 2024"

# With verbose output to see provider usage
python main.py --research "Climate change impacts" --verbose

# Interactive mode with provider visibility
python main.py --interactive --verbose
```

## 🔑 API Key Setup

### OpenAI
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Google Gemini
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Add to `.env`: `GOOGLE_API_KEY=...`

### Tavily
1. Visit [Tavily API](https://tavily.com/)
2. Sign up and get API key
3. Add to `.env`: `TAVILY_API_KEY=tvly-...`

### Brave Search
1. Visit [Brave Search API](https://brave.com/search/api/)
2. Apply for API access
3. Add to `.env`: `BRAVE_API_KEY=...`

## 📊 Cost Optimization

### Model Cost Comparison (Approximate)
| Provider | Model | Input ($/1K tokens) | Output ($/1K tokens) |
|----------|-------|---------------------|----------------------|
| OpenAI | gpt-4o | $0.005 | $0.015 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| Google | gemini-1.5-pro | $0.00125 | $0.005 |
| Google | gemini-1.5-flash | $0.000075 | $0.0003 |

### Cost-Saving Tips
1. **Use efficient models**: gemini-1.5-flash, gpt-4o-mini for routine tasks
2. **Optimize prompts**: Shorter prompts = lower costs
3. **Enable caching**: Reuse responses when possible
4. **Monitor usage**: Track costs with `COST_TRACKING=true`

## 🔧 Troubleshooting

### Common Issues

#### 1. Provider Not Available
```bash
Error: LLM provider google_gemini not implemented in abstraction layer
```
**Solution**: The provider is available through gpt-researcher. This error is for direct abstraction layer usage only.

#### 2. Missing API Key
```bash
Configuration issues: Missing API key for primary LLM provider: openai
```
**Solution**: Add the required API key to your `.env` file.

#### 3. Rate Limiting
```bash
Error: Rate limit exceeded
```
**Solution**: 
- Enable fallback providers
- Reduce request frequency
- Upgrade API plan if needed

#### 4. Model Not Found
```bash
Error: Unsupported model: gpt-5
```
**Solution**: Use supported models listed in the provider documentation.

### Debug Mode
Enable debug logging for troubleshooting:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Testing Providers
```bash
# Test current configuration
python -c "from cli.providers import ProviderCLI; ProviderCLI.test_providers()"

# Test specific provider by running a simple research
python main.py --research "test" --verbose
```

## 🔄 Migration Guide

### From OpenAI-Only to Multi-Provider

1. **Backup current `.env`**:
   ```bash
   cp .env .env.backup
   ```

2. **Update configuration**:
   ```bash
   # Add new provider settings
   PRIMARY_LLM_PROVIDER=openai
   PRIMARY_SEARCH_PROVIDER=tavily
   
   # Add fallback if desired
   FALLBACK_LLM_PROVIDER=google_gemini
   FALLBACK_SEARCH_PROVIDER=brave
   ```

3. **Test configuration**:
   ```bash
   python main.py --provider-info
   python main.py --research "test migration" --verbose
   ```

### From Tavily-Only to Multi-Search

1. **Add Brave Search**:
   ```bash
   BRAVE_API_KEY=your_brave_api_key
   FALLBACK_SEARCH_PROVIDER=brave
   SEARCH_STRATEGY=fallback_on_error
   ```

2. **Test fallback**:
   ```bash
   # Temporarily disable Tavily to test Brave
   # Comment out TAVILY_API_KEY and run research
   ```

## 🚨 Best Practices

### Security
- Store API keys in `.env`, never in code
- Use environment-specific configurations
- Rotate API keys regularly
- Monitor usage for unusual activity

### Performance
- Choose appropriate models for task complexity
- Use caching to reduce redundant requests
- Set reasonable timeouts and retries
- Monitor provider response times

### Reliability
- Always configure fallback providers for production
- Test provider switches before deployment
- Monitor provider status and error rates
- Have contingency plans for provider outages

### Cost Management
- Set usage alerts on provider dashboards
- Track costs with `COST_TRACKING=true`
- Use cost-effective models for simple tasks
- Review and optimize configurations regularly

## 📚 Advanced Topics

### Custom Provider Implementation
To add a new provider:

1. Implement the provider class:
   ```python
   from ..base import BaseLLMProvider, LLMResponse
   
   class CustomLLMProvider(BaseLLMProvider):
       async def generate(self, prompt: str, **kwargs) -> LLMResponse:
           # Implementation here
           pass
   ```

2. Register in factory:
   ```python
   from .providers.factory import ProviderFactory
   ProviderFactory.LLM_PROVIDERS[LLMProvider.CUSTOM] = CustomLLMProvider
   ```

### Provider Health Monitoring
Monitor provider health:
```python
from multi_agents.providers.factory import provider_manager
status = provider_manager.get_provider_status()
print(status)
```

### Dynamic Provider Switching
Switch providers programmatically:
```python
from multi_agents.providers.factory import enhanced_config
enhanced_config.switch_llm_provider(use_fallback=True)
```

This completes the comprehensive multi-provider system for your Deep Research MCP framework!