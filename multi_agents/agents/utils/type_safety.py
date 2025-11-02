"""
Type Safety Utilities for Multi-Agent Research System

This module provides comprehensive type validation and safety utilities to prevent
type-related crashes throughout the multi-agent workflow.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Type definitions
DictType = Dict[str, Any]
StateType = Dict[str, Any]
T = TypeVar("T")

logger = logging.getLogger(__name__)


class TypeSafetyError(Exception):
    """Custom exception for type safety validation failures"""

    pass


def safe_dict_get(data: Any, key: str, default: Any = None, expected_type: type = None) -> Any:
    """
    Safely get a value from a dictionary with type validation.

    Args:
        data: Input data (should be dict, but handles any type)
        key: Key to retrieve
        default: Default value if key not found or type mismatch
        expected_type: Expected type for validation

    Returns:
        Value from dict or default if not found/type mismatch
    """
    if not isinstance(data, dict):
        logger.warning(f"Expected dict but got {type(data)} for key '{key}'")
        return default

    value = data.get(key, default)

    if expected_type and value is not None and not isinstance(value, expected_type):
        logger.warning(
            f"Type mismatch for key '{key}': expected {expected_type}, got {type(value)}"
        )
        return default

    return value


def ensure_dict(data: Any, fallback: DictType = None) -> DictType:
    """
    Ensure data is a dictionary, with intelligent fallback handling.

    Args:
        data: Input data of any type
        fallback: Fallback dictionary if data is not a dict

    Returns:
        Dictionary representation of data or fallback
    """
    if isinstance(data, dict):
        return data

    if fallback is None:
        fallback = {}

    if isinstance(data, str):
        # Try to parse as JSON
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

        # If string parsing fails, create a dict with the string content
        return {"content": data, "type": "string_fallback"}

    logger.warning(f"Converting non-dict type {type(data)} to dict")
    return {"data": str(data), "original_type": str(type(data))}


def ensure_list(data: Any, fallback: List[Any] = None) -> List[Any]:
    """
    Ensure data is a list, with intelligent conversion.

    Args:
        data: Input data of any type
        fallback: Fallback list if conversion fails

    Returns:
        List representation of data or fallback
    """
    if isinstance(data, list):
        return data

    if fallback is None:
        fallback = []

    if data is None:
        return fallback

    # Convert single items to list
    return [data]


def safe_string_operation(data: Any, operation: str, *args, **kwargs) -> Any:
    """
    Safely perform string operations with type checking.

    Args:
        data: Input data
        operation: String method name (e.g., 'endswith', 'startswith', 'strip')
        *args, **kwargs: Arguments to pass to the string method

    Returns:
        Result of operation or None if data is not a string
    """
    if not isinstance(data, str):
        logger.warning(f"Attempted {operation} on non-string type: {type(data)}")
        return None

    try:
        method = getattr(data, operation)
        return method(*args, **kwargs)
    except AttributeError:
        logger.error(f"String method '{operation}' not found")
        return None
    except Exception as e:
        logger.error(f"Error executing string operation '{operation}': {e}")
        return None


def validate_research_state(state: Any) -> StateType:
    """
    Validate and normalize research state dictionary.

    Args:
        state: Input state (any type)

    Returns:
        Valid research state dictionary

    Raises:
        TypeSafetyError: If state cannot be normalized
    """
    if not isinstance(state, dict):
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                raise TypeSafetyError(f"Cannot parse state string as JSON: {state[:100]}...")
        else:
            raise TypeSafetyError(f"Research state must be dict, got {type(state)}")

    # Ensure required fields exist with proper types
    normalized_state = {}

    # Task field validation
    normalized_state["task"] = ensure_dict(state.get("task"), {"query": "Unknown query"})

    # String fields with safe defaults
    string_fields = [
        "initial_research",
        "title",
        "date",
        "table_of_contents",
        "introduction",
        "conclusion",
        "report",
        "draft",
    ]
    for field in string_fields:
        value = state.get(field)
        normalized_state[field] = value if isinstance(value, str) else ""

    # List fields with safe defaults
    list_fields = ["sections", "research_data", "sources"]
    for field in list_fields:
        normalized_state[field] = ensure_list(state.get(field))

    # Dict fields with safe defaults
    dict_fields = ["headers"]
    for field in dict_fields:
        normalized_state[field] = ensure_dict(state.get(field))

    # Preserve any additional fields from original state
    for key, value in state.items():
        if key not in normalized_state:
            normalized_state[key] = value

    return normalized_state


def safe_json_parse(data: str, fallback: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.

    Args:
        data: JSON string to parse
        fallback: Fallback value if parsing fails

    Returns:
        Parsed JSON data or fallback
    """
    if not isinstance(data, str):
        logger.warning(f"Expected string for JSON parsing, got {type(data)}")
        return fallback

    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON parsing failed: {e}")
        return fallback


def ensure_agent_return_dict(
    result: Any, agent_name: str, original_state: StateType = None
) -> StateType:
    """
    Ensure agent returns a proper dictionary state.

    Args:
        result: Agent return value (any type)
        agent_name: Name of the agent for logging
        original_state: Original state to preserve if result is invalid

    Returns:
        Valid state dictionary
    """
    if isinstance(result, dict):
        return result

    logger.warning(f"Agent '{agent_name}' returned non-dict type: {type(result)}")

    # Preserve original state and add result as additional field
    if original_state:
        return {
            **original_state,
            f"{agent_name}_raw_result": str(result) if result else None,
            f"{agent_name}_type_error": True,
        }

    # Create minimal valid state
    return {
        "task": {"query": "Unknown"},
        "draft": str(result) if result else "",
        f"{agent_name}_type_error": True,
    }


def validate_file_path_operation(file_path: Any, operation_name: str) -> Optional[str]:
    """
    Validate file path before performing operations.

    Args:
        file_path: Potential file path (any type)
        operation_name: Name of operation being performed

    Returns:
        Valid file path string or None if invalid
    """
    if not isinstance(file_path, str):
        logger.error(f"File path for {operation_name} must be string, got {type(file_path)}")
        return None

    if not file_path.strip():
        logger.error(f"Empty file path for {operation_name}")
        return None

    return file_path.strip()


def safe_list_operation(data: Any, operation: str, *args, **kwargs) -> Any:
    """
    Safely perform list operations with type checking.

    Args:
        data: Input data
        operation: List method name (e.g., 'append', 'extend', 'filter')
        *args, **kwargs: Arguments to pass to the list method

    Returns:
        Result of operation or appropriate fallback
    """
    if not isinstance(data, list):
        logger.warning(f"Attempted {operation} on non-list type: {type(data)}")
        # Convert to list if possible
        data = ensure_list(data)

    try:
        if operation == "filter":
            # Special handling for filter operations
            filter_func = args[0] if args else lambda x: True
            return [item for item in data if filter_func(item)]
        else:
            method = getattr(data, operation)
            return method(*args, **kwargs)
    except (AttributeError, TypeError) as e:
        logger.error(f"Error executing list operation '{operation}': {e}")
        return data  # Return original data as fallback


def type_safe_decorator(expected_types: Dict[str, type]):
    """
    Decorator to validate function argument types.

    Args:
        expected_types: Dict mapping parameter names to expected types

    Returns:
        Decorated function with type validation
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # This is a simplified version - in production you'd want more sophisticated
            # argument mapping and validation
            for param, expected_type in expected_types.items():
                if param in kwargs:
                    value = kwargs[param]
                    if not isinstance(value, expected_type):
                        logger.warning(
                            f"Type mismatch in {func.__name__}.{param}: "
                            f"expected {expected_type}, got {type(value)}"
                        )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Validation schemas for common data structures
TRANSLATION_RESULT_SCHEMA = {
    "status": str,
    "original_files": dict,
    "translated_files": list,
    "target_language": str,
    "language_name": str,
}

RESEARCH_DATA_SCHEMA = {"title": str, "content": str, "sources": list}


def validate_schema(data: Any, schema: Dict[str, type], strict: bool = False) -> bool:
    """
    Validate data against a schema.

    Args:
        data: Data to validate
        schema: Schema dictionary mapping field names to expected types
        strict: If True, requires all schema fields to be present

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    for field, expected_type in schema.items():
        if field in data:
            if not isinstance(data[field], expected_type):
                logger.warning(
                    f"Schema validation failed for field '{field}': "
                    f"expected {expected_type}, got {type(data[field])}"
                )
                return False
        elif strict:
            logger.warning(f"Required field '{field}' missing from data")
            return False

    return True


def create_type_safe_wrapper(
    func: Callable, input_validator: Callable = None, output_validator: Callable = None
) -> Callable:
    """
    Create a type-safe wrapper for any function.

    Args:
        func: Function to wrap
        input_validator: Function to validate/normalize inputs
        output_validator: Function to validate/normalize outputs

    Returns:
        Type-safe wrapped function
    """

    async def async_wrapper(*args, **kwargs):
        try:
            # Validate inputs if validator provided
            if input_validator:
                args, kwargs = input_validator(*args, **kwargs)

            # Execute original function
            result = await func(*args, **kwargs) if hasattr(func, "__call__") else func

            # Validate outputs if validator provided
            if output_validator:
                result = output_validator(result)

            return result

        except Exception as e:
            logger.error(f"Error in type-safe wrapper for {func.__name__}: {e}")
            # Return a safe fallback based on expected output type
            if output_validator:
                try:
                    return output_validator(None)
                except:
                    pass
            return None

    def sync_wrapper(*args, **kwargs):
        try:
            # Validate inputs if validator provided
            if input_validator:
                args, kwargs = input_validator(*args, **kwargs)

            # Execute original function
            result = func(*args, **kwargs)

            # Validate outputs if validator provided
            if output_validator:
                result = output_validator(result)

            return result

        except Exception as e:
            logger.error(f"Error in type-safe wrapper for {func.__name__}: {e}")
            # Return a safe fallback based on expected output type
            if output_validator:
                try:
                    return output_validator(None)
                except:
                    pass
            return None

    # Return appropriate wrapper based on function type
    if hasattr(func, "__call__") and hasattr(func, "__await__"):
        return async_wrapper
    else:
        return sync_wrapper
