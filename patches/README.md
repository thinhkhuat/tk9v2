# Patches Directory

This directory contains patches and fixes for third-party dependencies used in the Deep Research MCP project.

## Applied Patches

### GPT-researcher Dimension Parsing Fix

**File**: `gpt_researcher_dimension_fix.py`  
**Issue**: Error parsing dimension values with invalid literal for int() with base 10  
**Status**: ✅ Applied  

**Problem**: The `parse_dimension` function in `gpt_researcher.scraper.utils` was trying to convert float strings directly to int using `int(value)`, which fails for decimal values like '372.06087715470215'.

**Solution**: Modified the function to use `int(float(value))` instead, which properly handles both integer and decimal dimension strings.

**Error Messages Fixed**:
```
Error parsing dimension value 372.06087715470215: invalid literal for int() with base 10: '372.06087715470215'
Error parsing dimension value 372.19192216981133: invalid literal for int() with base 10: '372.19192216981133'
Error parsing dimension value 371.6776937618148: invalid literal for int() with base 10: '371.6776937618148'
Error parsing dimension value 310.0316908607647: invalid literal for int() with base 10: '310.0316908607647'
```

**Files Modified**:
- `.venv/lib/python3.13/site-packages/gpt_researcher/scraper/utils.py`
- Backup created at: `.venv/lib/python3.13/site-packages/gpt_researcher/scraper/utils.py.backup`

**Test Results**:
- `parse_dimension('372.06087715470215')` → `372` ✅
- `parse_dimension('372.19192216981133')` → `372` ✅  
- `parse_dimension('371.6776937618148')` → `371` ✅
- `parse_dimension('310.0316908607647')` → `310` ✅
- `parse_dimension('500px')` → `500` ✅
- `parse_dimension('800')` → `800` ✅
- `parse_dimension('invalid')` → `None` ✅ (proper error handling)

## Usage

To apply patches automatically:

```bash
# Apply the GPT-researcher dimension fix
python patches/gpt_researcher_dimension_fix.py
```

## Important Notes

1. These patches modify third-party packages in the virtual environment
2. Patches need to be reapplied when updating dependencies  
3. Backups are created automatically before applying fixes
4. All patches include verification tests to ensure they work correctly

## Future Patches

When adding new patches:

1. Create a descriptive Python script in this directory
2. Include proper error handling and backup creation
3. Add verification tests to ensure the fix works
4. Update this README with patch details
5. Consider submitting upstream fixes to the original projects