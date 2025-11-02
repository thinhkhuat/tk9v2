# Pydantic BaseSettings - Quick Reference

**Status**: ✅ IMPLEMENTED
**Recommended By**: Gemini AI

---

## 🚀 Quick Start

```bash
# Install
pip install pydantic-settings>=2.1.0

# Test
python -c "from config import settings; print('✅ OK')"

# Run Application
python main.py
```

---

## 📖 Usage

### Import Settings

```python
from config import settings

# Access configuration
print(settings.PORT)  # 12656
print(settings.CORS_ORIGINS)  # ['http://localhost:5173', ...]
```

### Use in Code

```python
# FastAPI middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    ...
)

# Uvicorn
uvicorn.run("main:app", host=settings.HOST, port=settings.PORT)

# Timeouts
await file_manager.wait_for_files(timeout=settings.FILE_WAIT_TIMEOUT)
```

### Helper Methods

```python
# Check if production
if settings.is_production():
    logger.warning("Production mode")

# Format CORS for logging
logger.info(settings.get_cors_origins_display())
```

---

## 📋 Configuration Fields

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| PORT | int | 12656 | 1-65535 |
| HOST | str | "0.0.0.0" | - |
| CORS_ORIGINS | List[str] | [...] | Parsed |
| FILE_WAIT_TIMEOUT | int | 30 | 1-3600 |
| SESSION_CLEANUP_INTERVAL | int | 3600 | 60-86400 |
| RESEARCH_LANGUAGE | str | "vi" | 2-10 chars |
| MIN_SUBJECT_LENGTH | int | 3 | 1-100 |
| MAX_SUBJECT_LENGTH | int | 1000 | 10-10000 |

---

## ⚙️ Environment Variables

```bash
# .env file
PORT=12656
HOST=0.0.0.0
CORS_ORIGINS=https://tk9.thinhkhuat.com,http://192.168.2.22:12656
FILE_WAIT_TIMEOUT=60
SESSION_CLEANUP_INTERVAL=3600
RESEARCH_LANGUAGE=vi
```

---

## ✅ Testing

```bash
# Run Pydantic tests
pytest tests/test_config_pydantic.py -v

# Expected: 35+ tests passed
```

---

## 🐛 Common Issues

### 1. Module Not Found

```
ModuleNotFoundError: No module named 'pydantic_settings'
```

**Fix**: `pip install pydantic-settings>=2.1.0`

---

### 2. Validation Error

```
ValidationError: PORT: Input should be less than or equal to 65535
```

**Fix**: Check .env file, set PORT to valid value (1-65535)

---

### 3. CORS Issues

**Problem**: CORS blocking requests

**Fix**: Add your domain to CORS_ORIGINS:
```bash
CORS_ORIGINS=https://yourdomain.com,http://localhost:5173
```

---

## 📚 Documentation

- **Full Guide**: PYDANTIC_BASESETTINGS_MIGRATION.md
- **Summary**: PYDANTIC_COMPLETE_SUMMARY.md
- **Config File**: web_dashboard/config.py
- **Tests**: tests/test_config_pydantic.py

---

## 🎯 Benefits

| Feature | Status |
|---------|--------|
| Type Safety | ✅ |
| Auto Validation | ✅ |
| Clear Errors | ✅ |
| Centralized | ✅ |
| Tested | ✅ |
| Documented | ✅ |

---

## 🔄 Migration Path

**From**: Manual `os.getenv()` with scattered config
**To**: Pydantic BaseSettings with centralized validation

**Backward Compatible**: ✅ Yes, all defaults match original values

---

## 🚦 Status

✅ Implemented
✅ Tested (35+ tests passing)
✅ Documented
✅ Production Ready

---

**Last Updated**: 2025-11-01
