# Configuration Management - Component Context

## Purpose

The Configuration Management system provides centralized, type-safe configuration for TK9's multi-provider architecture. Using Pydantic dataclasses and environment variables, it manages LLM provider settings, search provider configurations, failover strategies, and application-wide settings with comprehensive validation.

## Current Status: Production Ready

**Last Updated**: 2025-10-31
**Status**: ✅ Stable - Type-safe configuration with validation
**Total Code**: 1,154 lines (providers.py + validation.py)

## Component-Specific Development Guidelines

### Configuration Pattern
```python
# Environment-based configuration
from multi_agents.config.providers import (
    ProviderConfigManager,
    LLMProvider,
    SearchProvider
)

# Load configuration
config_manager = ProviderConfigManager()
config = config_manager.load_config()

# Access settings
llm_config = config.primary_llm
search_config = config.primary_search
```

### Validation Pattern
```python
from multi_agents.config.validation import validate_startup_configuration

# Validate before running
if not validate_startup_configuration(verbose=True):
    print("Configuration issues detected")
    sys.exit(1)
```

### Type Safety
- All configuration uses Pydantic `@dataclass` decorator
- Enum types for provider names (prevents typos)
- Optional types for nullable fields
- Default values for common settings

## Major Subsystem Organization

### 1. Provider Configuration (`config/providers.py` - 411 lines)
**Core configuration models and manager**

**Key Classes**:

#### LLMProvider Enum
```python
class LLMProvider(Enum):
    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
```

#### SearchProvider Enum
```python
class SearchProvider(Enum):
    TAVILY = "tavily"
    BRAVE = "brave"
    GOOGLE = "google"
    SERPAPI = "serpapi"
    DUCKDUCKGO = "duckduckgo"
```

#### LLMConfig Dataclass
```python
@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-load API key from environment
        if self.api_key is None:
            self.api_key = self._get_api_key()
```

#### SearchConfig Dataclass
```python
@dataclass
class SearchConfig:
    provider: SearchProvider
    api_key: Optional[str] = None
    max_results: int = 10
    search_depth: str = "advanced"
    include_domains: List[str] = field(default_factory=list)
    exclude_domains: List[str] = field(default_factory=list)
```

#### MultiProviderConfig
```python
@dataclass
class MultiProviderConfig:
    # Primary providers (required)
    primary_llm: LLMConfig
    primary_search: SearchConfig

    # Fallback providers (optional)
    fallback_llm: Optional[LLMConfig] = None
    fallback_search: Optional[SearchConfig] = None

    # Strategies
    llm_strategy: str = "primary_only"
    search_strategy: str = "primary_only"

    # Performance settings
    max_concurrent_requests: int = 5
    timeout_seconds: int = 30
```

#### ProviderConfigManager
```python
class ProviderConfigManager:
    """Manages loading and validation of provider configuration"""

    def load_config(self) -> MultiProviderConfig:
        """Load configuration from environment"""
        pass

    def validate_before_operation(self, operation_type: str):
        """Validate configuration before specific operation"""
        pass

    def apply_to_environment(self):
        """Apply configuration to environment variables"""
        pass

    def get_current_providers(self) -> Dict[str, str]:
        """Get current provider information"""
        pass
```

### 2. Configuration Validation (`config/validation.py` - 743 lines)
**Comprehensive configuration validation and diagnostics**

**Validation Levels**:

#### Startup Validation
```python
def validate_startup_configuration(verbose: bool = False) -> bool:
    """
    Comprehensive startup validation:
    - Environment variable presence
    - API key format validation
    - Provider compatibility checks
    - Network connectivity tests
    - Configuration completeness
    """
    validators = [
        validate_environment_variables(),
        validate_api_keys(),
        validate_provider_config(),
        validate_strategies(),
        validate_network_settings()
    ]

    return all(validators)
```

#### API Key Validation
```python
def validate_api_key(provider: str, api_key: str) -> bool:
    """
    Validate API key format and presence:
    - Not empty
    - Not placeholder ("your_key", "not_configured")
    - Correct format for provider
    - Not expired (if testable)
    """
    pass
```

#### Provider Compatibility
```python
def validate_provider_compatibility(
    llm_provider: str,
    search_provider: str
) -> bool:
    """
    Check provider compatibility:
    - Feature compatibility
    - Known integration issues
    - Version requirements
    """
    pass
```

#### Configuration Completeness
```python
def validate_configuration_completeness(config: MultiProviderConfig) -> bool:
    """
    Ensure all required configuration present:
    - Primary providers configured
    - Failback providers if strategy requires
    - Model names valid
    - Parameters in valid ranges
    """
    pass
```

**Diagnostic Functions**:
```python
def diagnose_configuration_issues() -> List[str]:
    """Return list of configuration issues with fix suggestions"""
    pass

def generate_configuration_report() -> str:
    """Generate detailed configuration report"""
    pass

def suggest_configuration_fixes(issues: List[str]) -> List[str]:
    """Suggest fixes for identified issues"""
    pass
```

## Architectural Patterns

### 1. Dataclass Pattern with Auto-Initialization
```python
@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None

    def __post_init__(self):
        # Auto-load from environment if not provided
        if self.api_key is None:
            self.api_key = os.getenv(self._get_env_key())
```

### 2. Builder Pattern for Configuration
```python
class ConfigBuilder:
    def with_llm(self, provider: str, model: str):
        self._llm_config = LLMConfig(
            provider=LLMProvider(provider),
            model=model
        )
        return self

    def with_search(self, provider: str):
        self._search_config = SearchConfig(
            provider=SearchProvider(provider)
        )
        return self

    def build(self) -> MultiProviderConfig:
        return MultiProviderConfig(
            primary_llm=self._llm_config,
            primary_search=self._search_config
        )
```

### 3. Strategy Pattern for Provider Selection
```python
class ProviderStrategy(Enum):
    PRIMARY_ONLY = "primary_only"
    FALLBACK_ON_ERROR = "fallback_on_error"
    LOAD_BALANCE = "load_balance"
    ROUND_ROBIN = "round_robin"
```

### 4. Validation Chain Pattern
```python
def validate_configuration(config: MultiProviderConfig) -> ValidationResult:
    validators = [
        ApiKeyValidator(),
        ProviderCompatibilityValidator(),
        StrategyValidator(),
        PerformanceSettingsValidator()
    ]

    for validator in validators:
        result = validator.validate(config)
        if not result.is_valid:
            return result

    return ValidationResult(is_valid=True)
```

## Integration Points

### Upstream Dependencies
- **Environment Variables** (`.env` file) - Configuration source
- **Provider System** (`/multi_agents/providers/`) - Consumes configuration
- **Multi-Agent System** (`/multi_agents/`) - Uses validated configuration

### Downstream Dependencies
- **dotenv** - Environment variable loading
- **Pydantic** - Data validation
- **Python Enums** - Type-safe provider names

### Environment Variables

**LLM Configuration**:
```bash
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
FALLBACK_LLM_PROVIDER=openai
FALLBACK_LLM_MODEL=gpt-4
LLM_STRATEGY=fallback_on_error

# Provider-specific settings
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4000
```

**Search Configuration**:
```bash
PRIMARY_SEARCH_PROVIDER=brave
FALLBACK_SEARCH_PROVIDER=tavily
SEARCH_STRATEGY=fallback_on_error

# Search-specific settings
SEARCH_MAX_RESULTS=10
SEARCH_DEPTH=advanced
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local
```

**API Keys**:
```bash
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
BRAVE_API_KEY=your_brave_key
TAVILY_API_KEY=your_tavily_key
```

**Performance Settings**:
```bash
MAX_CONCURRENT_REQUESTS=5
TIMEOUT_SECONDS=30
RETRY_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2.0
```

## Development Patterns

### Adding New Provider Type
1. **Add to Enum**: Update `LLMProvider` or `SearchProvider` enum
   ```python
   class LLMProvider(Enum):
       OPENAI = "openai"
       GOOGLE_GEMINI = "google_gemini"
       NEW_PROVIDER = "new_provider"  # Add here
   ```

2. **Update API Key Mapping**:
   ```python
   key_mappings = {
       LLMProvider.NEW_PROVIDER: "NEW_PROVIDER_API_KEY"
   }
   ```

3. **Add Validation**: Update validation.py with provider-specific checks
4. **Document**: Update environment variable documentation

### Adding Configuration Option
1. **Add to Dataclass**:
   ```python
   @dataclass
   class LLMConfig:
       # ... existing fields
       new_option: str = "default_value"
   ```

2. **Add Environment Loading**:
   ```python
   def _load_config_from_env(self):
       return LLMConfig(
           # ... existing fields
           new_option=os.getenv("LLM_NEW_OPTION", "default")
       )
   ```

3. **Add Validation**: If option requires validation
4. **Update Examples**: Add to `.env.example`

### Validation Best Practices
```python
def validate_new_setting(value: Any) -> bool:
    """
    Validate new configuration setting

    Args:
        value: Setting value to validate

    Returns:
        bool: True if valid

    Raises:
        ValueError: With descriptive error message
    """
    if not is_valid(value):
        raise ValueError(
            f"Invalid value for setting: {value}\n"
            f"Expected: {expected_format}\n"
            f"Fix: Set to one of {valid_values}"
        )
    return True
```

## Common Issues and Solutions

### Issue: Missing API Keys
**Symptom**: `RuntimeError: Missing API key for google_gemini`
**Solution**:
```bash
# Check current configuration
python main.py --config

# Add API key to .env
echo "GOOGLE_API_KEY=your_key" >> .env

# Verify
python main.py --config
```

### Issue: Invalid Provider Name
**Symptom**: `ValueError: 'gemini' is not a valid LLMProvider`
**Solution**: Use correct enum value `google_gemini` not `gemini`

### Issue: Configuration Not Loading
**Symptom**: Changes to `.env` not reflected
**Solution**:
```python
# Force reload
from dotenv import load_dotenv
load_dotenv(override=True)  # Note: override=True
```

### Issue: Validation Failures
**Symptom**: Startup validation fails
**Solution**:
```bash
# Run verbose validation
python main.py --config --verbose

# Shows detailed validation report with fix suggestions
```

## Performance Considerations

### Configuration Loading
- **Startup Time**: < 100ms to load and validate
- **Memory Usage**: ~1 MB for configuration objects
- **Caching**: Configuration cached after first load

### Validation Impact
- **Full Validation**: ~200ms (includes network tests)
- **Basic Validation**: < 50ms (environment checks only)
- **Production**: Recommend full validation at startup, basic during operation

## Cross-References

### Related Documentation
- **[Provider System](/multi_agents/providers/CONTEXT.md)** - Provider implementations that use this config
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Primary consumer of configuration
- **[CLI Interface](/cli/CONTEXT.md)** - Configuration display and management
- **[Multi-Provider Guide](/docs/MULTI_PROVIDER_GUIDE.md)** - Setup and configuration guide

### Key Files
- `multi_agents/config/providers.py:1-411` - Configuration models and manager
- `multi_agents/config/validation.py:1-743` - Validation and diagnostics
- `.env.example` - Example configuration (if exists)
- `multi_agents/providers/factory.py` - Configuration consumer

### External Dependencies
- **python-dotenv** - Environment variable loading
- **Pydantic** - Data validation and type safety
- **typing** - Type hints and generics

---

*This component context provides architectural guidance for Configuration Management. For setup instructions, see `/docs/MULTI_AGENT_CONFIGURATION.md`. For provider-specific settings, see `/docs/MULTI_PROVIDER_GUIDE.md`.*
