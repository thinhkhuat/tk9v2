# Archived: Old CLI Interface (August 2025)

**Archived on**: October 31, 2025
**Reason**: Replaced by `multi_agents/main.py`

## What was archived

1. **`main.py`** (root directory)
   - Old CLI entry point
   - Last modified: August 31, 2025
   - Imported from `cli/` directory

2. **`cli/` directory**
   - `interactive.py` - Interactive chat mode
   - `commands.py` - CLI command implementations
   - `providers.py` - Provider status display
   - `CONTEXT.md` - Documentation

## Why it was archived

This old CLI interface was causing conflicts with the newer `multi_agents/main.py`:

- When running `uv run python -m main` from project root, Python would load the old `main.py` instead of `multi_agents/main.py`
- The old CLI didn't have the `--session-id` argument needed for web dashboard integration
- Led to "unrecognized arguments" errors when the web dashboard tried to pass `--session-id`

## Current CLI

The active CLI is now **`multi_agents/main.py`**, which should be run as:

```bash
# From project root
python -m multi_agents.main --research "query"

# Or with uv
uv run python -m multi_agents.main --research "query"
```

## Migration notes

If you need to restore this old CLI:
1. Move files back to their original locations
2. Update documentation to clarify which CLI to use
3. Consider renaming to avoid conflicts (e.g., `legacy_main.py`)
