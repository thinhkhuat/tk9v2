### Pydantic BaseSettings Migration

**Date**: 2025-11-01
**Status**: ✅ COMPLETE
**Recommended By**: Gemini AI (Session: 0918658b-063a-4fd8-9a04-2bcb34736552)

---

## Overview

Migrated backend configuration from manual `os.getenv()` calls to Pydantic `BaseSettings` for better type safety, automatic validation, and clearer error messages.

---

## Why Pydantic BaseSettings?

### Benefits

1. **Type Safety** ✅
   - Automatic type casting from environment strings
   - Type hints enforce correct usage throughout codebase
   - IDE autocomplete and type checking

2. **Validation** ✅
   - Pydantic validators catch configuration errors at startup
   - Clear error messages with field names and constraints
   - No more cryptic `ValueError: invalid literal for int()`

3. **Centralization** ✅
   - Single source of truth in `config.py`
   - All configuration in one place
   - Easy to see all available settings

4. **Documentation** ✅
   - Field descriptions built into the code
   - Self-documenting configuration
   - Type hints show expected types

5. **Testing** ✅
   - Easier to test with dependency injection
   - Can create Settings instances with test values
   - No module reloading needed

6. **Industry Standard** ✅
   - Recommended best practice for FastAPI
   - Well-documented pattern
   - Community support

---

## What Changed

### Before (Manual os.getenv)

**main.py**:
```python
import os

def get_cors_origins() -> list[str]:
    cors_env = os.getenv("CORS_ORIGINS", "")
    if cors_env == "*":
        return ["*"]
    if not cors_env:
        return [...]  # defaults
    return [origin.strip() for origin in cors_env.split(",")]

CORS_ORIGINS = get_cors_origins()
SERVER_PORT = int(os.getenv("PORT", "12656"))
FILE_WAIT_TIMEOUT = int(os.getenv("FILE_WAIT_TIMEOUT", "30"))

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)
uvicorn.run("main:app", port=SERVER_PORT, ...)
```

**models.py**:
```python
import os

DEFAULT_RESEARCH_LANGUAGE = os.getenv("RESEARCH_LANGUAGE", "vi")

class ResearchRequest(BaseModel):
    language: str = Field(default=DEFAULT_RESEARCH_LANGUAGE, ...)
```

**Issues**:
- ❌ Configuration scattered across files
- ❌ No automatic validation
- ❌ Generic error messages
- ❌ Manual type casting
- ❌ No field documentation

---

### After (Pydantic BaseSettings)

**config.py** (NEW):
```python
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    PORT: int = Field(
        default=12656,
        description="Server port to bind to",
        ge=1, le=65535
    )

    CORS_ORIGINS: List[str] = Field(default=[...])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str) and v == "*":
            return ["*"]
        if isinstance(v, str) and v:
            return [o.strip() for o in v.split(",")]
        return cls.model_fields["CORS_ORIGINS"].default

    # ... more fields ...

settings = Settings()
```

**main.py**:
```python
from config import settings

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
uvicorn.run("main:app", port=settings.PORT, ...)
```

**models.py**:
```python
from config import settings

class ResearchRequest(BaseModel):
    subject: str = Field(
        ...,
        min_length=settings.MIN_SUBJECT_LENGTH,
        max_length=settings.MAX_SUBJECT_LENGTH
    )
    language: str = Field(default=settings.RESEARCH_LANGUAGE, ...)
```

**Benefits**:
- ✅ All configuration centralized in config.py
- ✅ Automatic validation with clear errors
- ✅ Type safety throughout
- ✅ Field documentation built-in
- ✅ Helper methods (is_production(), etc.)

---

## Migration Details

### 1. Added Dependency

**requirements.txt**:
```diff
pydantic==2.5.0
+ pydantic-settings==2.1.0
```

**Install**:
```bash
pip install pydantic-settings==2.1.0
```

---

### 2. Created config.py

**Location**: `web_dashboard/config.py`

**Features**:
- Settings class with all configuration fields
- Field validators for complex logic (CORS parsing)
- Constraints (ge, le, min_length, max_length)
- Helper methods (is_production(), get_cors_origins_display())
- Singleton instance: `settings`
- Auto-validation and logging on import

**Configuration Fields**:

#### Server Configuration
- `PORT` (int, 1-65535, default: 12656)
- `HOST` (str, default: "0.0.0.0")

#### CORS Configuration
- `CORS_ORIGINS` (List[str], parsed from comma-separated or "*")

#### Application Configuration
- `FILE_WAIT_TIMEOUT` (int, 1-3600s, default: 30)
- `SESSION_CLEANUP_INTERVAL` (int, 60-86400s, default: 3600)
- `RESEARCH_LANGUAGE` (str, 2-10 chars, default: "vi")
- `MAX_CONCURRENT_SESSIONS` (int, 1-100, default: 5)
- `SESSION_TIMEOUT` (int, 60-86400s, default: 3600)

#### Validation Configuration
- `MIN_SUBJECT_LENGTH` (int, 1-100, default: 3)
- `MAX_SUBJECT_LENGTH` (int, 10-10000, default: 1000)

#### Supabase Configuration
- `SUPABASE_URL` (str)
- `SUPABASE_SERVICE_KEY` (str)
- `SUPABASE_ANON_KEY` (str)
- `JWT_SECRET` (str)

---

### 3. Updated main.py

**Changes**:
- ❌ Removed: `import os`
- ❌ Removed: `get_cors_origins()` function
- ❌ Removed: Manual config loading (CORS_ORIGINS, SERVER_PORT, etc.)
- ✅ Added: `from config import settings`
- ✅ Updated: `allow_origins=settings.CORS_ORIGINS`
- ✅ Updated: `timeout=settings.FILE_WAIT_TIMEOUT`
- ✅ Updated: `asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL)`
- ✅ Updated: `port=settings.PORT, host=settings.HOST`

---

### 4. Updated models.py

**Changes**:
- ❌ Removed: `import os`
- ❌ Removed: `DEFAULT_RESEARCH_LANGUAGE = os.getenv(...)`
- ✅ Added: `from config import settings`
- ✅ Updated: `default=settings.RESEARCH_LANGUAGE`
- ✅ Updated: `min_length=settings.MIN_SUBJECT_LENGTH`
- ✅ Updated: `max_length=settings.MAX_SUBJECT_LENGTH`

---

### 5. Created New Tests

**test_config_pydantic.py** - Comprehensive test suite for Pydantic Settings:
- Default values testing
- CORS parsing (wildcard, comma-separated, spaces)
- Environment overrides
- Validation error handling
- Helper methods
- Production configuration
- Singleton behavior

**Test Coverage**: 9 test classes, 35+ tests

---

## Validation Error Examples

### Before (Generic Errors)

```python
PORT=abc python main.py
# ValueError: invalid literal for int() with base 10: 'abc'
```

**Problem**: No indication which environment variable caused the error.

---

### After (Clear Errors)

```python
PORT=abc python main.py
# ValidationError: 1 validation error for Settings
# PORT
#   Input should be a valid integer, unable to parse string as an integer
#   [type=int_parsing, input_value='abc', input_type=str]
```

**Benefit**: Clear field name, error type, and input value.

```python
PORT=70000 python main.py
# ValidationError: 1 validation error for Settings
# PORT
#   Input should be less than or equal to 65535
#   [type=less_than_equal, input_value=70000, input_type=int]
```

**Benefit**: Validation constraint clearly stated.

---

## Usage Examples

### Importing Settings

```python
# Import singleton instance (most common)
from config import settings

print(settings.PORT)  # 12656
print(settings.CORS_ORIGINS)  # ['http://localhost:5173', ...]

# Or import class for testing
from config import Settings

test_settings = Settings(PORT=8080, CORS_ORIGINS=["http://test.com"])
```

---

### Using in Application

```python
# FastAPI middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    ...
)

# Uvicorn configuration
uvicorn.run(
    "main:app",
    host=settings.HOST,
    port=settings.PORT,
    ...
)

# Timeouts
await file_manager.wait_for_files(timeout=settings.FILE_WAIT_TIMEOUT)
await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL)

# Pydantic models
class ResearchRequest(BaseModel):
    subject: str = Field(
        min_length=settings.MIN_SUBJECT_LENGTH,
        max_length=settings.MAX_SUBJECT_LENGTH
    )
```

---

### Helper Methods

```python
# Check if in production mode
if settings.is_production():
    logger.warning("Running in production mode")

# Get formatted CORS origins for logging
logger.info(f"CORS Origins: {settings.get_cors_origins_display()}")
# Output: "http://example.com, http://another.com"
# or: "* (all origins)"
```

---

## Testing

### Running Tests

```bash
# Pydantic-specific tests
pytest tests/test_config_pydantic.py -v

# All configuration tests
pytest tests/test_config*.py -v

# With coverage
pytest tests/test_config_pydantic.py --cov=web_dashboard.config --cov-report=html
```

---

### Writing Tests

**With Environment Override**:
```python
from unittest.mock import patch

def test_custom_port():
    with patch.dict(os.environ, {"PORT": "8080"}):
        from web_dashboard.config import Settings

        settings = Settings()
        assert settings.PORT == 8080
```

**With Validation**:
```python
def test_invalid_port():
    with patch.dict(os.environ, {"PORT": "70000"}):
        from web_dashboard.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any("PORT" in str(error) for error in errors)
```

---

## Backward Compatibility

✅ **Fully Backward Compatible**

All defaults match the original hardcoded values from Phase 1:
- PORT: 12656 ✅
- FILE_WAIT_TIMEOUT: 30 ✅
- SESSION_CLEANUP_INTERVAL: 3600 ✅
- RESEARCH_LANGUAGE: "vi" ✅
- CORS_ORIGINS: Development defaults ✅

**No breaking changes** to:
- Environment variable names
- Default values
- API behavior
- Configuration file format

---

## Deployment Notes

### Development

No changes needed - everything works with defaults:
```bash
python main.py
```

---

### Production

Set environment variables as before:
```bash
# .env file
PORT=12656
CORS_ORIGINS=https://tk9.thinhkhuat.com,http://192.168.2.22:12656
FILE_WAIT_TIMEOUT=60
RESEARCH_LANGUAGE=vi
```

Or export them:
```bash
export CORS_ORIGINS="https://tk9.thinhkhuat.com"
export PORT=12656
python main.py
```

---

### Debugging

The new config system logs all settings on startup:
```
================================================================
Configuration Loaded (Pydantic BaseSettings)
================================================================
Server: 0.0.0.0:12656
CORS Origins: http://localhost:5173, http://localhost:5174, ...
File Wait Timeout: 30s
Session Cleanup Interval: 3600s
Default Language: vi
Max Concurrent Sessions: 5
Subject Length: 3-1000
================================================================
```

---

## Comparison: Before vs After

| Aspect | Before (os.getenv) | After (Pydantic) |
|--------|-------------------|------------------|
| **Type Safety** | Manual casting | Automatic ✅ |
| **Validation** | Runtime crashes | Clear errors ✅ |
| **Centralization** | Scattered | Single file ✅ |
| **Documentation** | External | Built-in ✅ |
| **Error Messages** | Generic | Specific ✅ |
| **Testing** | Module reload | Instances ✅ |
| **IDE Support** | Limited | Full autocomplete ✅ |
| **Constraints** | Manual checks | Declarative ✅ |

---

## Next Steps

### Immediate

1. ✅ Install pydantic-settings: `pip install pydantic-settings==2.1.0`
2. ✅ Run tests: `pytest tests/test_config_pydantic.py -v`
3. ✅ Verify application starts: `python main.py`
4. ✅ Check logs for configuration output

### Optional

1. Add more validation constraints (e.g., URL format validation for SUPABASE_URL)
2. Add environment-specific settings classes (DevelopmentSettings, ProductionSettings)
3. Add .env.example documentation for all new fields
4. Create configuration migration guide for other projects

---

## Troubleshooting

### Import Error

**Problem**: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution**:
```bash
pip install pydantic-settings==2.1.0
```

---

### Validation Error on Startup

**Problem**: `ValidationError: 1 validation error for Settings`

**Solution**: Check the error message for the specific field and constraint. Update your environment variable or .env file.

Example:
```
PORT: Input should be less than or equal to 65535
```

Fix: Set PORT to a valid value (1-65535).

---

### Circular Import

**Problem**: Circular import between config.py and other modules

**Solution**: Import settings inside functions if needed, or restructure imports. The current implementation avoids this by importing config after load_dotenv().

---

## References

- [Pydantic BaseSettings Documentation](https://docs.pydantic.dev/latest/usage/pydantic_settings/)
- [FastAPI Configuration Guide](https://fastapi.tiangolo.com/advanced/settings/)
- Gemini AI Session: 0918658b-063a-4fd8-9a04-2bcb34736552

---

**Status**: ✅ MIGRATION COMPLETE
**Date**: 2025-11-01
**Recommended**: Yes - Industry best practice for FastAPI
