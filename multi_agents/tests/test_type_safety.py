"""
Test suite for type safety utilities and fixes
"""

import os
import sys

import pytest

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from multi_agents.agents.utils.type_safety import (
    TypeSafetyError,
    ensure_agent_return_dict,
    ensure_dict,
    ensure_list,
    safe_dict_get,
    safe_json_parse,
    safe_string_operation,
    validate_file_path_operation,
    validate_research_state,
    validate_schema,
)


class TestTypeSafetyUtilities:
    """Test type safety utility functions"""

    def test_ensure_dict_with_valid_dict(self):
        """Test ensure_dict with valid dictionary input"""
        input_dict = {"key": "value", "number": 42}
        result = ensure_dict(input_dict)
        assert result == input_dict
        assert isinstance(result, dict)

    def test_ensure_dict_with_string_json(self):
        """Test ensure_dict with valid JSON string"""
        json_string = '{"key": "value", "number": 42}'
        result = ensure_dict(json_string)
        assert result == {"key": "value", "number": 42}
        assert isinstance(result, dict)

    def test_ensure_dict_with_invalid_json(self):
        """Test ensure_dict with invalid JSON string"""
        invalid_json = '{"key": "value", invalid}'
        result = ensure_dict(invalid_json)
        assert result == {"content": invalid_json, "type": "string_fallback"}

    def test_ensure_dict_with_non_dict_types(self):
        """Test ensure_dict with various non-dict types"""
        test_cases = [
            (123, {"data": "123", "original_type": "<class 'int'>"}),
            ([], {"data": "[]", "original_type": "<class 'list'>"}),
            (None, {"data": "None", "original_type": "<class 'NoneType'>"}),
        ]

        for input_val, expected in test_cases:
            result = ensure_dict(input_val)
            assert result["original_type"] == expected["original_type"]

    def test_safe_dict_get_with_valid_dict(self):
        """Test safe_dict_get with valid dictionary"""
        test_dict = {"key1": "value1", "key2": 42, "key3": None}

        assert safe_dict_get(test_dict, "key1") == "value1"
        assert safe_dict_get(test_dict, "key2") == 42
        assert safe_dict_get(test_dict, "key3") is None
        assert safe_dict_get(test_dict, "missing", "default") == "default"

    def test_safe_dict_get_with_type_validation(self):
        """Test safe_dict_get with type validation"""
        test_dict = {"string_key": "value", "int_key": 42, "wrong_type": "not_int"}

        assert safe_dict_get(test_dict, "string_key", expected_type=str) == "value"
        assert safe_dict_get(test_dict, "int_key", expected_type=int) == 42
        assert safe_dict_get(test_dict, "wrong_type", "default", int) == "default"

    def test_safe_dict_get_with_non_dict(self):
        """Test safe_dict_get with non-dictionary input"""
        result = safe_dict_get("not_a_dict", "key", "default")
        assert result == "default"

    def test_ensure_list_with_valid_list(self):
        """Test ensure_list with valid list input"""
        input_list = ["item1", "item2", 42]
        result = ensure_list(input_list)
        assert result == input_list
        assert isinstance(result, list)

    def test_ensure_list_with_single_item(self):
        """Test ensure_list with single item"""
        assert ensure_list("single_item") == ["single_item"]
        assert ensure_list(42) == [42]
        assert ensure_list({"key": "value"}) == [{"key": "value"}]

    def test_ensure_list_with_none(self):
        """Test ensure_list with None"""
        assert ensure_list(None) == []
        assert ensure_list(None, ["default"]) == ["default"]

    def test_safe_string_operation_with_valid_string(self):
        """Test safe_string_operation with valid string"""
        test_string = "hello_world.txt"

        assert safe_string_operation(test_string, "endswith", ".txt") is True
        assert safe_string_operation(test_string, "startswith", "hello") is True
        assert safe_string_operation(test_string, "upper") == "HELLO_WORLD.TXT"
        assert safe_string_operation(test_string, "strip") == "hello_world.txt"

    def test_safe_string_operation_with_non_string(self):
        """Test safe_string_operation with non-string input"""
        assert safe_string_operation(42, "endswith", ".txt") is None
        assert safe_string_operation([], "startswith", "hello") is None
        assert safe_string_operation(None, "upper") is None

    def test_safe_string_operation_with_invalid_method(self):
        """Test safe_string_operation with invalid method"""
        assert safe_string_operation("test", "nonexistent_method") is None

    def test_validate_research_state_with_valid_dict(self):
        """Test validate_research_state with valid dictionary"""
        valid_state = {
            "task": {"query": "test query"},
            "title": "Test Title",
            "draft": "Test content",
            "sections": ["section1", "section2"],
            "research_data": [{"title": "Research 1"}],
        }

        result = validate_research_state(valid_state)
        assert isinstance(result, dict)
        assert result["task"]["query"] == "test query"
        assert result["title"] == "Test Title"
        assert isinstance(result["sections"], list)

    def test_validate_research_state_with_missing_fields(self):
        """Test validate_research_state with missing fields"""
        minimal_state = {"task": {"query": "test"}}

        result = validate_research_state(minimal_state)
        assert isinstance(result, dict)
        assert result["task"]["query"] == "test"
        assert result["title"] == ""  # Should have safe default
        assert result["sections"] == []  # Should have safe default
        assert isinstance(result["headers"], dict)  # Should have safe default

    def test_validate_research_state_with_invalid_types(self):
        """Test validate_research_state with invalid field types"""
        invalid_state = {
            "task": "not_a_dict",  # Should be dict
            "sections": "not_a_list",  # Should be list
            "title": 42,  # Should be string
        }

        result = validate_research_state(invalid_state)
        assert isinstance(result["task"], dict)
        assert isinstance(result["sections"], list)
        assert isinstance(result["title"], str)

    def test_validate_research_state_with_json_string(self):
        """Test validate_research_state with JSON string input"""
        json_state = '{"task": {"query": "test"}, "title": "Test Title"}'

        result = validate_research_state(json_state)
        assert isinstance(result, dict)
        assert result["task"]["query"] == "test"
        assert result["title"] == "Test Title"

    def test_validate_research_state_with_invalid_input(self):
        """Test validate_research_state with invalid input types"""
        with pytest.raises(TypeSafetyError):
            validate_research_state(42)

        with pytest.raises(TypeSafetyError):
            validate_research_state("invalid_json_string")

    def test_safe_json_parse_with_valid_json(self):
        """Test safe_json_parse with valid JSON"""
        json_str = '{"key": "value", "number": 42}'
        result = safe_json_parse(json_str)
        assert result == {"key": "value", "number": 42}

    def test_safe_json_parse_with_invalid_json(self):
        """Test safe_json_parse with invalid JSON"""
        invalid_json = '{"key": "value", invalid}'
        result = safe_json_parse(invalid_json, {"fallback": True})
        assert result == {"fallback": True}

    def test_safe_json_parse_with_non_string(self):
        """Test safe_json_parse with non-string input"""
        result = safe_json_parse(42, "fallback")
        assert result == "fallback"

    def test_ensure_agent_return_dict_with_valid_dict(self):
        """Test ensure_agent_return_dict with valid dictionary"""
        valid_result = {"draft": "content", "status": "success"}
        result = ensure_agent_return_dict(valid_result, "test_agent")
        assert result == valid_result

    def test_ensure_agent_return_dict_with_invalid_return(self):
        """Test ensure_agent_return_dict with invalid return types"""
        original_state = {"task": {"query": "test"}, "draft": "original"}

        # Test with string return
        result = ensure_agent_return_dict("string_result", "test_agent", original_state)
        assert result["test_agent_raw_result"] == "string_result"
        assert result["test_agent_type_error"] is True
        assert result["draft"] == "original"

    def test_ensure_agent_return_dict_without_original_state(self):
        """Test ensure_agent_return_dict without original state"""
        result = ensure_agent_return_dict("string_result", "test_agent")
        assert result["task"]["query"] == "Unknown"
        assert result["draft"] == "string_result"
        assert result["test_agent_type_error"] is True

    def test_validate_file_path_operation_with_valid_path(self):
        """Test validate_file_path_operation with valid paths"""
        assert (
            validate_file_path_operation("/valid/path/file.txt", "read") == "/valid/path/file.txt"
        )
        assert validate_file_path_operation("  relative/path.md  ", "write") == "relative/path.md"

    def test_validate_file_path_operation_with_invalid_input(self):
        """Test validate_file_path_operation with invalid input"""
        assert validate_file_path_operation(42, "read") is None
        assert validate_file_path_operation("", "write") is None
        assert validate_file_path_operation("   ", "delete") is None
        assert validate_file_path_operation(None, "copy") is None

    def test_validate_schema_with_valid_data(self):
        """Test validate_schema with valid data"""
        schema = {"name": str, "age": int, "active": bool}
        valid_data = {"name": "John", "age": 30, "active": True}

        assert validate_schema(valid_data, schema) is True

    def test_validate_schema_with_invalid_types(self):
        """Test validate_schema with invalid types"""
        schema = {"name": str, "age": int, "active": bool}
        invalid_data = {"name": "John", "age": "thirty", "active": True}

        assert validate_schema(invalid_data, schema) is False

    def test_validate_schema_with_missing_fields(self):
        """Test validate_schema with missing fields"""
        schema = {"name": str, "age": int, "active": bool}

        # Non-strict mode (default) - should pass with missing fields
        partial_data = {"name": "John", "active": True}
        assert validate_schema(partial_data, schema, strict=False) is True

        # Strict mode - should fail with missing fields
        assert validate_schema(partial_data, schema, strict=True) is False

    def test_validate_schema_with_non_dict_input(self):
        """Test validate_schema with non-dictionary input"""
        schema = {"name": str}
        assert validate_schema("not_a_dict", schema) is False
        assert validate_schema(42, schema) is False
        assert validate_schema(None, schema) is False


class TestAgentTypeSafety:
    """Test type safety in agent context"""

    def test_translator_file_path_operations(self):
        """Test type safety for translator file operations"""
        # Simulate the translator error scenario
        test_files = ["file1.md", "file2.pdf", None, 42, ""]

        safe_files = []
        for file_path in test_files:
            if safe_string_operation(file_path, "endswith", ".md"):
                safe_files.append(file_path)

        assert safe_files == ["file1.md"]
        assert len(safe_files) == 1

    def test_research_state_propagation(self):
        """Test research state propagation between agents"""
        # Simulate agent chain with different return types
        initial_state = {"task": {"query": "test query"}, "draft": "initial content"}

        # Agent 1 returns valid dict
        agent1_result = {"draft": "updated content", "status": "success"}
        safe_result1 = ensure_agent_return_dict(agent1_result, "agent1", initial_state)

        # Agent 2 returns string (error case)
        agent2_result = "Error: JSON parsing failed"
        safe_result2 = ensure_agent_return_dict(agent2_result, "agent2", safe_result1)

        # Verify state is preserved
        assert safe_result2["draft"] == "updated content"  # From agent1
        assert safe_result2["agent2_type_error"] is True
        assert "agent2_raw_result" in safe_result2

    def test_translation_result_validation(self):
        """Test translation result validation"""
        # Valid translation result
        valid_result = {
            "status": "success",
            "original_files": {"md": "/path/file.md"},
            "translated_files": ["/path/file_vi.md", "/path/file_vi.pdf"],
            "target_language": "vi",
            "language_name": "Vietnamese",
        }

        # Validate using schema
        from multi_agents.agents.utils.type_safety import TRANSLATION_RESULT_SCHEMA

        assert validate_schema(valid_result, TRANSLATION_RESULT_SCHEMA) is True

        # Invalid translation result
        invalid_result = {
            "status": 200,  # Should be string
            "original_files": [],  # Should be dict
            "translated_files": "file.md",  # Should be list
            "target_language": ["vi"],  # Should be string
        }

        assert validate_schema(invalid_result, TRANSLATION_RESULT_SCHEMA) is False


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_suite = TestTypeSafetyUtilities()

    print("Running basic type safety tests...")

    # Test ensure_dict
    print("✓ Testing ensure_dict...")
    test_suite.test_ensure_dict_with_valid_dict()
    test_suite.test_ensure_dict_with_string_json()
    test_suite.test_ensure_dict_with_invalid_json()

    # Test safe_dict_get
    print("✓ Testing safe_dict_get...")
    test_suite.test_safe_dict_get_with_valid_dict()
    test_suite.test_safe_dict_get_with_type_validation()
    test_suite.test_safe_dict_get_with_non_dict()

    # Test safe_string_operation
    print("✓ Testing safe_string_operation...")
    test_suite.test_safe_string_operation_with_valid_string()
    test_suite.test_safe_string_operation_with_non_string()

    # Test validate_research_state
    print("✓ Testing validate_research_state...")
    test_suite.test_validate_research_state_with_valid_dict()
    test_suite.test_validate_research_state_with_missing_fields()

    print("All basic tests passed! ✅")
    print("\nTo run full test suite, use: pytest test_type_safety.py")
