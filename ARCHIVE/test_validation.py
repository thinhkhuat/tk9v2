#!/usr/bin/env python3
"""
Test script to validate the workflow fixes without requiring provider dependencies.
This demonstrates that the validation can work using AST parsing instead of imports.
"""

import ast
import sys
import re
from pathlib import Path


def test_ast_validation():
    """Test that we can validate the agents without importing them"""
    print("Testing AST-based validation (no imports required)...")
    
    def check_file_structure(file_path, class_name, required_methods):
        """Check if a Python file has the required class and methods without importing"""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Find the class
            class_found = False
            methods_found = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_found = True
                    # Check methods in the class
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods_found.add(item.name)
            
            if not class_found:
                print(f"  ✗ Class {class_name} not found in {file_path}")
                return False
            
            missing_methods = set(required_methods) - methods_found
            if missing_methods:
                print(f"  ✗ Missing methods in {class_name}: {missing_methods}")
                return False
            
            print(f"  ✓ {class_name} structure validated")
            return True
            
        except Exception as e:
            print(f"  ✗ Error checking {file_path}: {e}")
            return False
    
    # Check ReviewerAgent
    reviewer_ok = check_file_structure(
        'multi_agents/agents/reviewer.py',
        'ReviewerAgent',
        ['__init__', 'review_draft', 'run']
    )
    
    # Check ReviserAgent
    reviser_ok = check_file_structure(
        'multi_agents/agents/reviser.py',
        'ReviserAgent',
        ['__init__', 'revise_draft', 'run']
    )
    
    return reviewer_ok and reviser_ok


def test_error_handling_patterns():
    """Test that error handling patterns are present"""
    print("\nTesting error handling patterns...")
    
    def check_patterns(file_path, patterns):
        """Check that file contains expected patterns"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            missing_patterns = []
            for pattern_name, pattern in patterns.items():
                if not re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    missing_patterns.append(pattern_name)
            
            if missing_patterns:
                print(f"  ✗ Missing patterns in {file_path}: {', '.join(missing_patterns)}")
                return False
            
            print(f"  ✓ All patterns found in {file_path}")
            return True
        except Exception as e:
            print(f"  ✗ Error checking patterns: {e}")
            return False
    
    # Patterns to check in reviewer
    reviewer_patterns = {
        "draft_validation": r"if not draft_content:",
        "guidelines_validation": r"if not guidelines_list:",
        "dict_return": r"return\s+\{.*\*\*draft_state",
    }
    
    # Patterns to check in reviser
    reviser_patterns = {
        "review_validation": r"if not review:",
        "draft_validation": r"if not draft_report:",
        "dict_return": r"return\s+\{.*\*\*draft_state"
    }
    
    reviewer_ok = check_patterns('multi_agents/agents/reviewer.py', reviewer_patterns)
    reviser_ok = check_patterns('multi_agents/agents/reviser.py', reviser_patterns)
    
    return reviewer_ok and reviser_ok


def test_method_signatures():
    """Test that methods have correct signatures"""
    print("\nTesting method signatures...")
    
    def check_methods(file_path, class_name, expected_methods):
        """Check that class has expected methods"""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    methods = {}
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            is_async = isinstance(item, ast.AsyncFunctionDef)
                            methods[item.name] = is_async
                    
                    # Check expected methods
                    for method_name, should_be_async in expected_methods.items():
                        if method_name not in methods:
                            print(f"  ✗ Missing method {method_name} in {class_name}")
                            return False
                        
                        if methods[method_name] != should_be_async:
                            async_str = "async" if should_be_async else "non-async"
                            print(f"  ✗ Method {method_name} should be {async_str}")
                            return False
                    
                    print(f"  ✓ {class_name} methods validated")
                    return True
            
            print(f"  ✗ Class {class_name} not found")
            return False
        except Exception as e:
            print(f"  ✗ Error checking methods: {e}")
            return False
    
    # Expected methods (method_name: is_async)
    reviewer_methods = {
        '__init__': False,
        'review_draft': True,
        'run': True,
    }
    
    reviser_methods = {
        '__init__': False,
        'revise_draft': True,
        'run': True,
    }
    
    reviewer_ok = check_methods('multi_agents/agents/reviewer.py', 'ReviewerAgent', reviewer_methods)
    reviser_ok = check_methods('multi_agents/agents/reviser.py', 'ReviserAgent', reviser_methods)
    
    return reviewer_ok and reviser_ok


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Workflow Fix Validation Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: AST validation
    if not test_ast_validation():
        all_passed = False
    
    # Test 2: Error handling patterns
    if not test_error_handling_patterns():
        all_passed = False
    
    # Test 3: Method signatures
    if not test_method_signatures():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All validation tests passed!")
        print("The workflow fixes are properly applied.")
        print("No provider dependencies were required for validation.")
        return 0
    else:
        print("❌ Some validation tests failed.")
        print("Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())