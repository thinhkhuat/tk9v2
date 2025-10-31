# Configuration Guide

## Overview

This guide covers all configuration options for the Deep Research MCP system, including environment setup, provider configuration, language settings, and advanced customization options.

## Table of Contents

- [Environment Configuration](#environment-configuration)
- [Provider Configuration](#provider-configuration)
- [Language Configuration](#language-configuration)
- [Task Configuration](#task-configuration)
- [Output Configuration](#output-configuration)
- [Performance Configuration](#performance-configuration)
- [Security Configuration](#security-configuration)
- [Development Configuration](#development-configuration)

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Copy template
cp .env.example .env
```

### LLM Provider Configuration

#### OpenAI
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ORG_ID=org-your-organization-id  # Optional
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for proxy
```

#### Google Gemini
```bash
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_PROJECT_ID=your-project-id  # Optional
```

#### Anthropic Claude
```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

#### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=your-azure-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Search Provider Configuration

#### Tavily (Recommended)
```bash
TAVILY_API_KEY=tvly-your-tavily-key-here
```

#### Brave Search
```bash
BRAVE_API_KEY=your-brave-api-key-here
```

#### Google Custom Search
```bash
GOOGLE_CSE_ID=your-custom-search-engine-id
GOOGLE_API_KEY=your-google-api-key-here  # Same as above
```

#### SerpAPI
```bash
SERPAPI_API_KEY=your-serpapi-key-here
```

#### DuckDuckGo
```bash
# No API key required
DUCKDUCKGO_ENABLED=true
```

### Translation Configuration

```bash
# Primary translation endpoint
TRANSLATION_ENDPOINT_PRIMARY=https://n8n.thinhkhuat.com/webhook/agent/translate

# Backup endpoints
TRANSLATION_ENDPOINT_BACKUP1=https://srv.saola-great.ts.net/webhook/agent/translate
TRANSLATION_ENDPOINT_BACKUP2=https://n8n.thinhkhuat.work/webhook/agent/translate

# Translation timeout (seconds)
TRANSLATION_TIMEOUT=120
```

## Provider Configuration

### Primary and Fallback Providers

```bash
# Primary configuration
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4o
PRIMARY_SEARCH_PROVIDER=tavily

# Fallback configuration (activated on primary failure)
FALLBACK_LLM_PROVIDER=google_gemini
FALLBACK_LLM_MODEL=gemini-1.5-pro
FALLBACK_SEARCH_PROVIDER=brave

# Tertiary fallback
TERTIARY_LLM_PROVIDER=anthropic
TERTIARY_LLM_MODEL=claude-3-sonnet
```

### Provider-Specific Settings

#### OpenAI Configuration
```bash
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7
OPENAI_TOP_P=1.0
OPENAI_FREQUENCY_PENALTY=0.0
OPENAI_PRESENCE_PENALTY=0.0
```

#### Google Gemini Configuration
```bash
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
```

#### Search Configuration
```bash
# Tavily settings
TAVILY_MAX_RESULTS=10
TAVILY_SEARCH_DEPTH=advanced
TAVILY_INCLUDE_DOMAINS=
TAVILY_EXCLUDE_DOMAINS=

# Brave settings
BRAVE_COUNTRY=US
BRAVE_SEARCH_LANG=en
BRAVE_SAFESEARCH=moderate
BRAVE_FRESHNESS=
```

### Provider Selection Logic

The system uses this priority order:
1. **Primary Provider**: Configured primary LLM and search
2. **Fallback Provider**: Activated on primary failure
3. **Tertiary Provider**: Last resort option
4. **Auto-switching**: Automatic provider switching on errors

## Language Configuration

### Target Language Settings

```bash
# Default research language
RESEARCH_LANGUAGE=en

# Available languages for translation
SUPPORTED_LANGUAGES=en,vi,es,fr,de,zh,ja,ko

# Language-specific models (optional)
VI_TRANSLATION_MODEL=gpt-4o
ES_TRANSLATION_MODEL=gemini-1.5-pro
```

### Language-Specific Configuration

Create `multi_agents/config/language_settings.json`:

```json
{
  "supported_languages": {
    "en": {
      "name": "English",
      "native_name": "English",
      "rtl": false,
      "preferred_models": ["gpt-4o", "gemini-1.5-pro"]
    },
    "vi": {
      "name": "Vietnamese", 
      "native_name": "Tiếng Việt",
      "rtl": false,
      "preferred_models": ["gpt-4o"],
      "special_instructions": "Maintain formal academic tone"
    },
    "zh": {
      "name": "Chinese",
      "native_name": "中文",
      "rtl": false,
      "preferred_models": ["gpt-4o", "gemini-1.5-pro"]
    }
  }
}
```

## Task Configuration

### Default Task Settings

Edit `multi_agents/task.json`:

```json
{
  "query": "Default research question",
  "max_sections": 5,
  "publish_formats": ["pdf", "docx", "md"],
  "include_human_feedback": false,
  "follow_guidelines": true,
  "model": "gpt-4o",
  "language": "en",
  "tone": "objective",
  "max_sources_per_section": 3,
  "max_research_depth": 3,
  "enable_translation": true,
  "enable_review": true,
  "guidelines": [
    "Focus on recent developments (2023-2024)",
    "Include statistical data and citations",
    "Maintain objective tone throughout",
    "Provide multiple perspectives on controversial topics"
  ]
}
```

### Research Parameters

#### Section Configuration
```json
{
  "max_sections": 5,           // Maximum report sections
  "min_section_length": 500,   // Minimum words per section
  "max_section_length": 2000,  // Maximum words per section
  "enable_subsections": true,  // Allow nested sections
  "auto_generate_outline": true // Generate outline automatically
}
```

#### Source Configuration
```json
{
  "max_sources_per_section": 3,    // Sources per research section
  "source_diversity": true,        // Diverse source types
  "academic_sources_priority": 0.7, // Academic source weight
  "recent_sources_bias": 0.8,      // Prefer recent sources
  "source_verification": true      // Verify source reliability
}
```

#### Quality Control
```json
{
  "enable_fact_checking": true,    // Verify facts
  "citation_style": "apa",         // Citation format
  "plagiarism_check": true,        // Check for duplication
  "readability_target": "academic", // Target audience
  "min_word_count": 2000,          // Minimum report length
  "max_word_count": 10000          // Maximum report length
}
```

## Output Configuration

### File Output Settings

```bash
# Output directory
OUTPUT_DIR=./outputs

# File naming
OUTPUT_FILENAME_PATTERN=research_report_{timestamp}_{query_hash}

# Enabled formats
ENABLE_PDF=true
ENABLE_DOCX=true
ENABLE_MARKDOWN=true
ENABLE_HTML=false

# PDF settings
PDF_ENGINE=xelatex  # xelatex, pdflatex, or weasyprint
PDF_MARGIN=1in
PDF_FONT_SIZE=12pt
PDF_FONT_FAMILY=serif

# DOCX settings
DOCX_TEMPLATE=default  # Path to custom template
DOCX_STYLE_REFERENCE=   # Path to style reference
```

### Draft Management

```bash
# Enable draft saving
SAVE_DRAFTS=true

# Draft organization
DRAFT_STRUCTURE=hierarchical  # flat or hierarchical
DRAFT_RETENTION_DAYS=30      # Days to keep drafts
DRAFT_COMPRESSION=true       # Compress old drafts
```

## Performance Configuration

### Concurrency Settings

```bash
# Maximum concurrent operations
MAX_CONCURRENT_SECTIONS=3      # Parallel research sections
MAX_CONCURRENT_SEARCHES=5      # Parallel searches per section
MAX_CONCURRENT_TRANSLATIONS=2  # Parallel translation requests

# Thread pool settings
THREAD_POOL_SIZE=10           # Worker threads
ASYNC_BATCH_SIZE=5            # Async operation batching
```

### Timeout Configuration

```bash
# API timeouts (seconds)
LLM_REQUEST_TIMEOUT=60        # LLM API calls
SEARCH_REQUEST_TIMEOUT=30     # Search API calls
TRANSLATION_TIMEOUT=120       # Translation requests
FILE_OPERATION_TIMEOUT=30     # File I/O operations

# Retry settings
MAX_RETRY_ATTEMPTS=3          # Failed request retries
RETRY_BACKOFF_FACTOR=2        # Exponential backoff
RETRY_JITTER=true            # Add random jitter
```

### Caching Configuration

```bash
# Enable caching
ENABLE_CACHING=true

# Cache settings
CACHE_DIRECTORY=./.cache
CACHE_TTL=3600               # Cache time-to-live (seconds)
CACHE_MAX_SIZE=1GB           # Maximum cache size
CACHE_COMPRESSION=true       # Compress cached data

# Search result caching
CACHE_SEARCH_RESULTS=true
SEARCH_CACHE_TTL=1800       # 30 minutes
```

### Memory Management

```bash
# Memory limits
MAX_MEMORY_USAGE=2GB         # Maximum memory usage
MEMORY_WARNING_THRESHOLD=1.5GB # Warning threshold
AUTO_GARBAGE_COLLECTION=true # Enable GC

# Large file handling
STREAM_LARGE_FILES=true      # Stream files > 10MB
TEMP_FILE_CLEANUP=true       # Auto cleanup temp files
```

## Security Configuration

### API Security

```bash
# API key rotation
ROTATE_API_KEYS=false        # Enable key rotation
KEY_ROTATION_INTERVAL=86400  # 24 hours

# Rate limiting
ENABLE_RATE_LIMITING=true
REQUESTS_PER_MINUTE=60
REQUESTS_PER_HOUR=1000

# Request signing
SIGN_REQUESTS=false          # Sign API requests
SIGNATURE_METHOD=hmac-sha256
```

### Content Security

```bash
# Content filtering
ENABLE_CONTENT_FILTER=true
FILTER_ADULT_CONTENT=true
FILTER_SPAM=true
FILTER_MALICIOUS_LINKS=true

# Input validation
VALIDATE_INPUTS=true
MAX_QUERY_LENGTH=1000
SANITIZE_OUTPUTS=true
```

### Privacy Settings

```bash
# Data retention
RETAIN_RESEARCH_DATA=true
DATA_RETENTION_DAYS=90
ANONYMIZE_QUERIES=false

# Logging
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
LOG_API_REQUESTS=false       # Log API calls
LOG_PERSONAL_DATA=false      # Log PII
```

## Development Configuration

### Debug Settings

```bash
# Development mode
DEBUG_MODE=false
VERBOSE_LOGGING=false
ENABLE_PROFILING=false

# Testing
RUN_TESTS_ON_START=false
MOCK_API_CALLS=false
TEST_DATA_PATH=./tests/data
```

### Monitoring Configuration

```bash
# LangSmith integration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=deep-research-mcp

# Custom monitoring
ENABLE_METRICS=true
METRICS_ENDPOINT=http://localhost:8080/metrics
HEALTH_CHECK_INTERVAL=60

# Performance monitoring
TRACK_PERFORMANCE=true
PERFORMANCE_LOG_FILE=performance.log
ALERT_ON_SLOW_REQUESTS=true
SLOW_REQUEST_THRESHOLD=30    # seconds
```

### Development Tools

```bash
# Hot reloading
ENABLE_HOT_RELOAD=false      # Development only
WATCH_FILE_CHANGES=false     # Auto-restart on changes

# Code quality
RUN_LINTING=true
RUN_TYPE_CHECKING=true
FORMAT_ON_SAVE=true
```

## Configuration Validation

### Validation Script

Run configuration validation:

```bash
python multi_agents/config/validate_config.py
```

### Required Configuration Check

```python
# multi_agents/config/validate_config.py
def validate_required_config():
    required_vars = [
        'OPENAI_API_KEY',      # Or alternative LLM
        'TAVILY_API_KEY',      # Or alternative search
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
```

### Configuration Templates

#### Minimal Configuration
```bash
# .env.minimal
OPENAI_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here
```

#### Production Configuration
```bash
# .env.production
# LLM Providers
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
FALLBACK_LLM_PROVIDER=google_gemini

# Search Providers
TAVILY_API_KEY=your-key-here
BRAVE_API_KEY=your-key-here
FALLBACK_SEARCH_PROVIDER=brave

# Performance
MAX_CONCURRENT_SECTIONS=5
ENABLE_CACHING=true
CACHE_TTL=3600

# Security
ENABLE_RATE_LIMITING=true
ENABLE_CONTENT_FILTER=true
```

#### Development Configuration
```bash
# .env.development
OPENAI_API_KEY=your-dev-key
DEBUG_MODE=true
VERBOSE_LOGGING=true
MOCK_API_CALLS=true
SAVE_DRAFTS=true
```

## Configuration Best Practices

### Security Best Practices

1. **Never commit API keys**: Use `.env` files in `.gitignore`
2. **Use environment-specific configs**: Separate dev/prod configurations
3. **Regular key rotation**: Rotate API keys periodically
4. **Monitor usage**: Track API consumption and costs
5. **Validate inputs**: Always validate user inputs

### Performance Best Practices

1. **Provider selection**: Choose fastest providers for your region
2. **Caching strategy**: Enable caching for repeated queries
3. **Concurrency limits**: Balance speed vs. API rate limits
4. **Resource monitoring**: Monitor memory and CPU usage
5. **Fallback configuration**: Always configure backup providers

### Reliability Best Practices

1. **Multiple providers**: Configure primary and fallback providers
2. **Timeout settings**: Set appropriate timeouts for your network
3. **Retry logic**: Configure retry attempts and backoff
4. **Error handling**: Implement comprehensive error handling
5. **Health checks**: Monitor provider availability

### Cost Optimization

1. **Model selection**: Choose cost-effective models for your use case
2. **Request optimization**: Minimize unnecessary API calls
3. **Caching**: Cache expensive operations
4. **Rate limiting**: Respect provider rate limits
5. **Usage monitoring**: Track and alert on high costs

This configuration guide provides comprehensive coverage of all available options. Start with the minimal configuration and gradually add features as needed for your specific use case.