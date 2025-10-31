# Workflow Fix Script Documentation

## Overview
The `apply_workflow_fixes.sh` script is an automated tool designed to fix dictionary return type issues in the Multi-Agent Deep Research workflow. It specifically addresses problems where the reviewer and reviser agents were returning plain strings instead of properly structured dictionaries, causing LangGraph workflow failures.

## Features

### 🛡️ Safety Features
- **Backup System**: Automatic timestamped backups before any modifications
- **Dry Run Mode**: Preview changes without applying them
- **Restore Capability**: Rollback to any previous backup
- **Validation Checks**: Pre and post-fix validation to ensure correctness
- **Cross-platform Support**: Works on both macOS and Linux

### 🎯 Core Functionality
- Fixes `reviewer.py` to always return dictionaries
- Fixes `reviser.py` to handle edge cases properly
- Validates Python imports and functionality
- Comprehensive edge case testing
- Generates detailed fix reports

## Installation

1. Make the script executable:
```bash
chmod +x apply_workflow_fixes.sh
```

2. Ensure you're in the project root directory:
```bash
cd /path/to/deep-research-mcp-og
```

## Usage

### Interactive Mode (Recommended)
Simply run the script to access the interactive menu:
```bash
./apply_workflow_fixes.sh
```

Menu Options:
1. **Verify Project Structure** - Check if all required files exist
2. **Run Dry Run** - Preview changes without applying them
3. **Apply Fixes** - Apply the fixes with automatic backup
4. **Validate Current Installation** - Check if fixes are already applied
5. **Show Differences** - Compare current files with backup
6. **Restore from Backup** - Rollback to a previous state
7. **Run Tests** - Execute comprehensive validation tests
8. **Generate Report** - Create a detailed fix report
9. **Exit** - Close the script

### Command Line Options
```bash
./apply_workflow_fixes.sh [OPTIONS]

OPTIONS:
    --dry-run       Preview changes without applying them
    --verbose, -v   Enable verbose output
    --force, -f     Skip confirmation prompts
    --help, -h      Show help message
```

### Examples

#### Dry Run (Preview Changes)
```bash
./apply_workflow_fixes.sh --dry-run
```

#### Apply Fixes with Verbose Output
```bash
./apply_workflow_fixes.sh --verbose
```

## How It Works

### 1. Verification Phase
- Checks for required dependencies (python3, diff, md5/md5sum, grep, sed)
- Verifies project structure and target files exist
- Detects operating system for platform-specific commands

### 2. Backup Phase
- Creates timestamped backup directory: `backups/fix_script_YYYYMMDD_HHMMSS/`
- Copies target files with checksum verification
- Saves metadata including user, timestamp, and system information

### 3. Fix Application Phase

#### Reviewer.py Fixes:
- Modifies `review_draft()` to always return a dictionary
- Adds validation for missing draft content and guidelines
- Returns properly structured error messages when validation fails
- Preserves all state fields in the returned dictionary

#### Reviser.py Fixes:
- Modifies `revise_draft()` to always return a dictionary
- Adds error handling for missing review feedback
- Implements try-catch for JSON parsing failures
- Ensures response always has required fields (`draft`, `revision_notes`)
- Merges response with draft_state to preserve workflow fields

### 4. Validation Phase
- Tests Python module imports
- Validates edge case handling (empty drafts, missing guidelines, null reviews)
- Verifies method signatures exist
- Runs comprehensive test suite

### 5. Reporting Phase
- Generates detailed fix report with timestamp
- Documents all changes applied
- Records validation results
- Saves backup location for reference

## Backup Structure

```
backups/
└── fix_script_20250830_181533/
    ├── reviewer.py         # Backup of original reviewer.py
    ├── reviser.py          # Backup of original reviser.py
    ├── checksums.txt       # MD5 checksums for integrity
    └── metadata.json       # Backup metadata and information
```

## Restoration Process

To restore from a backup:

1. Run the script and select option 6
2. Choose from the list of available backups
3. Confirm the restoration
4. Files will be restored with checksum verification

Or restore manually:
```bash
cp backups/fix_script_TIMESTAMP/*.py multi_agents/agents/
```

## Troubleshooting

### Import Errors
If you see import errors during validation, ensure all Python dependencies are installed:
```bash
pip install -r multi_agents/requirements.txt
```

### Permission Denied
Make sure the script is executable:
```bash
chmod +x apply_workflow_fixes.sh
```

### No MD5 Utility
- **macOS**: The script automatically uses `md5 -q`
- **Linux**: The script uses `md5sum`
- If neither is available, install the appropriate package for your system

### Backup Not Found
If restoration fails due to missing backup:
1. Check the `backups/` directory for available backups
2. Verify the backup contains the required files
3. Use manual restoration as a fallback

## Error Codes

The script uses the following exit codes:
- `0`: Success
- `1`: General error (dependencies missing, validation failed, etc.)

## Security Considerations

- The script creates backups with checksums for integrity verification
- All file modifications are validated before and after application
- Python code execution is limited to validation tests
- No external network connections are made
- All operations are confined to the project directory

## Limitations

1. Requires Python 3.x installed and accessible as `python3`
2. Target files must exist in `multi_agents/agents/` directory
3. Requires write permissions in the project directory
4. Does not handle symbolic links or special file types

## Support

For issues or questions:
1. Check the fix report in the project root
2. Review backup files in the `backups/` directory
3. Consult the error messages for specific issues
4. Restore from backup if needed

## Version History

- **v1.0.0** (2025-08-30): Initial release with full feature set
  - Interactive menu system
  - Backup and restore functionality
  - Cross-platform support (macOS/Linux)
  - Comprehensive validation
  - Dry run mode
  - Detailed reporting

## Technical Details

### Files Modified
- `multi_agents/agents/reviewer.py`
- `multi_agents/agents/reviser.py`

### Key Changes
1. **Dictionary Return Guarantee**: Both agents now always return dictionaries
2. **State Preservation**: All workflow state fields are preserved
3. **Error Handling**: Graceful handling of edge cases
4. **JSON Safety**: Robust JSON parsing with fallbacks

### Testing Coverage
- Module import validation
- Edge case scenarios (empty inputs, null values)
- Method signature verification
- Checksum integrity validation
- Cross-platform compatibility

## Best Practices

1. **Always run a dry run first** to preview changes
2. **Keep backups** until you're confident the fixes work correctly
3. **Run validation tests** after applying fixes
4. **Generate a report** for documentation purposes
5. **Test your workflow** after applying fixes to ensure proper operation

## Conclusion

This script provides a safe, automated way to fix critical issues in the Multi-Agent Deep Research workflow. With comprehensive backup mechanisms, validation checks, and cross-platform support, it ensures that fixes can be applied confidently with the ability to rollback if needed.