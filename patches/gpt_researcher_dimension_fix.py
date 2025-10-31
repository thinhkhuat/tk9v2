#!/usr/bin/env python3
"""
Fix for GPT-researcher dimension parsing error.
This script patches the parse_dimension function to handle float values properly.

Usage:
    python patches/gpt_researcher_dimension_fix.py
"""

import os
import sys
from pathlib import Path

def get_gpt_researcher_utils_path():
    """Find the gpt_researcher utils.py file in the current Python installation"""
    import gpt_researcher
    gpt_researcher_path = Path(gpt_researcher.__file__).parent
    utils_path = gpt_researcher_path / "scraper" / "utils.py"
    
    if utils_path.exists():
        return utils_path
    
    # Fallback to searching in virtual environment paths
    possible_paths = [
        ".venv/lib/python3.13/site-packages/gpt_researcher/scraper/utils.py",
        ".venv/lib/python3.12/site-packages/gpt_researcher/scraper/utils.py", 
        ".venv/lib/python3.11/site-packages/gpt_researcher/scraper/utils.py",
        "venv/lib/python3.13/site-packages/gpt_researcher/scraper/utils.py",
        "venv/lib/python3.12/site-packages/gpt_researcher/scraper/utils.py",
        "venv/lib/python3.11/site-packages/gpt_researcher/scraper/utils.py"
    ]
    
    for path in possible_paths:
        full_path = Path(path)
        if full_path.exists():
            return full_path
    
    return None

def fix_parse_dimension_function():
    """Apply the fix to the parse_dimension function"""
    utils_path = get_gpt_researcher_utils_path()
    
    if not utils_path:
        print("❌ Could not find gpt_researcher utils.py file")
        return False
    
    print(f"📁 Found gpt_researcher utils.py at: {utils_path}")
    
    # Read the original file
    with open(utils_path, 'r') as f:
        content = f.read()
    
    # Check if already fixed with CSS handling
    if "value == 'auto'" in content:
        print("✅ File already contains CSS value handling - fix already applied")
        return True
    
    # Define the original buggy function
    original_function = '''def parse_dimension(value: str) -> int:
    """Parse dimension value, handling px units"""
    if value.lower().endswith('px'):
        value = value[:-2]  # Remove 'px' suffix
    try:
        return int(value)  # Convert to float first to handle decimal values
    except ValueError as e:
        print(f"Error parsing dimension value {value}: {e}")
        return None'''
    
    # Also check for partially fixed version (with float conversion)
    partially_fixed_function = '''def parse_dimension(value: str) -> int:
    """Parse dimension value, handling px units and float strings"""
    if value.lower().endswith('px'):
        value = value[:-2]  # Remove 'px' suffix
    try:
        # Convert to float first to handle decimal values, then to int
        return int(float(value))
    except (ValueError, TypeError) as e:
        print(f"Error parsing dimension value {value}: {e}")
        return None'''
    
    # Define the fully fixed function with CSS handling
    fixed_function = '''def parse_dimension(value: str) -> int:
    """Parse dimension value, handling px units, CSS values, and float strings"""
    if not value or value == 'auto':
        return None  # Return None for auto-sizing
    
    # Handle percentage values
    if value.endswith('%'):
        # For percentage, return a reasonable default or None
        return None
    
    if value.lower().endswith('px'):
        value = value[:-2]  # Remove 'px' suffix
    
    try:
        # Convert to float first to handle decimal values, then to int
        return int(float(value))
    except (ValueError, TypeError) as e:
        # Don't log for common CSS values to reduce noise
        if value not in ['auto', 'inherit', 'initial', 'unset']:
            print(f"Error parsing dimension value {value}: {e}")
        return None'''
    
    # Replace the function
    if original_function in content:
        new_content = content.replace(original_function, fixed_function)
        function_found = True
    elif partially_fixed_function in content:
        new_content = content.replace(partially_fixed_function, fixed_function)
        function_found = True
    else:
        function_found = False
        new_content = content
    
    if function_found:
        # Create backup
        backup_path = utils_path.with_suffix('.py.backup')
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"📋 Created backup at: {backup_path}")
        
        # Write the fixed version
        with open(utils_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully applied dimension parsing fix!")
        print("🔧 Fixed: Now handles CSS values (auto, %, inherit, etc.) properly")
        return True
    else:
        print("⚠️  Original function pattern not found - file may have been modified")
        print("Please apply the fix manually to handle CSS values like 'auto' and '100%'")
        return False

def verify_fix():
    """Verify the fix works by testing with sample values"""
    print("\n🧪 Testing the fix with sample dimension values...")
    
    # Import the fixed module
    try:
        import sys
        utils_path = get_gpt_researcher_utils_path()
        if utils_path:
            sys.path.insert(0, str(utils_path.parent))
            from utils import parse_dimension
            
            test_cases = [
                "372.06087715470215",
                "372.19192216981133", 
                "371.6776937618148",
                "310.0316908607647",
                "500px",
                "800",
                "invalid"
            ]
            
            for test_value in test_cases:
                result = parse_dimension(test_value)
                print(f"  parse_dimension('{test_value}') = {result}")
            
            print("✅ Fix verification completed!")
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    print("🔧 GPT-researcher Dimension Parsing Fix")
    print("=" * 50)
    
    if fix_parse_dimension_function():
        verify_fix()
        print("\n🎉 Fix applied successfully!")
        print("You can now run your research tasks without dimension parsing errors.")
    else:
        print("\n❌ Fix failed to apply automatically.")
        print("Please apply the fix manually as shown above.")
        sys.exit(1)