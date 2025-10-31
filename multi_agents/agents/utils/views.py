from colorama import Fore, Style
from enum import Enum
import json
import os
from typing import Optional, Dict, Any
from .event_types import (
    AgentStatus,
    AgentError,
    create_agent_update_event
)


class AgentColor(Enum):
    RESEARCHER = Fore.LIGHTBLUE_EX
    EDITOR = Fore.YELLOW
    WRITER = Fore.LIGHTGREEN_EX
    PUBLISHER = Fore.MAGENTA
    REVIEWER = Fore.CYAN
    REVISOR = Fore.LIGHTWHITE_EX
    MASTER = Fore.LIGHTYELLOW_EX
    PROVIDERS = Fore.GREEN
    ERROR = Fore.RED
    ORCHESTRATOR = Fore.LIGHTCYAN_EX
    ORCHESTRATOR_SETUP = Fore.LIGHTCYAN_EX
    DEBUG = Fore.LIGHTMAGENTA_EX
    LANGUAGE = Fore.LIGHTBLUE_EX


# ============================================================================
# Feature Flag for Gradual Migration (Phase 2)
# ============================================================================

def _should_use_json_output() -> bool:
    """
    Check if JSON output should be used based on feature flag

    Feature flag hierarchy:
    1. Environment variable ENABLE_JSON_OUTPUT (highest priority)
    2. Agent-specific override via AGENT_JSON_MIGRATION env var
    3. Default: False (use legacy text output)

    This allows gradual agent-by-agent migration:
    - ENABLE_JSON_OUTPUT=true → all agents use JSON
    - AGENT_JSON_MIGRATION=researcher,writer → only these agents use JSON
    """
    # Global flag
    global_flag = os.getenv('ENABLE_JSON_OUTPUT', '').lower() == 'true'
    if global_flag:
        return True

    # Agent-specific flag is checked at call site
    return False


# ============================================================================
# Legacy Text Output (Phase 1 - to be deprecated)
# ============================================================================

def print_agent_output(output: str, agent: str = "RESEARCHER"):
    """
    Legacy colored text output for agents - AUTO-CONVERTS TO JSON

    For backward compatibility, this automatically converts to JSON output
    when ENABLE_JSON_OUTPUT=true. This allows migration without changing
    all agent code immediately.

    Args:
        output: Message to print
        agent: Agent name (uppercase, e.g., "RESEARCHER", "WRITER")
    """
    # Auto-convert to JSON if enabled
    if os.getenv('ENABLE_JSON_OUTPUT', '').lower() == 'true':
        print_structured_output(
            message=output,
            agent=agent,
            status="running",
            progress=None  # No artificial progress
        )
        return

    # Legacy text output
    try:
        color = AgentColor[agent].value
    except KeyError:
        # Default color if agent not found in enum
        color = Fore.WHITE
    print(f"{color}{agent}: {output}{Style.RESET_ALL}")


# ============================================================================
# Phase 2: Structured JSON Output (NEW)
# ============================================================================

def print_structured_output(
    message: str,
    agent: str,
    status: AgentStatus = "running",
    progress: Optional[int] = None,  # IMPORTANT: Don't use artificial percentages!
    data: Optional[Dict[str, Any]] = None,
    error: Optional[AgentError] = None,
    force_json: bool = False
) -> None:
    """
    Print structured JSON output for agent events (Phase 2)

    This function outputs JSON-formatted events that can be reliably parsed
    by the WebSocket handler, replacing the fragile regex-based text parsing.

    The output follows an envelope-based event pattern:
    {
        "type": "agent_update",
        "payload": {
            "agent_id": "researcher",
            "agent_name": "RESEARCHER",
            "status": "running",
            "progress": 50,
            "message": "Found 5 relevant articles",
            "timestamp": "2025-10-31T12:00:00.123Z",
            "data": {...}
        }
    }

    Args:
        message: Human-readable status message
        agent: Agent name (uppercase, e.g., "RESEARCHER", "WRITER")
        status: Agent status (pending, running, completed, error)
        progress: Optional completion percentage (0-100)
        data: Optional structured data from agent
        error: Optional error details if status is 'error'
        force_json: Force JSON output even if feature flag is disabled

    Example:
        print_structured_output(
            message="Found 5 relevant articles",
            agent="RESEARCHER",
            status="running",
            progress=60,
            data={"urls_found": ["http://..."]}
        )

    Migration:
        This function can coexist with print_agent_output() during migration.
        Use feature flag ENABLE_JSON_OUTPUT or force_json=True to enable.
    """
    # Check feature flag (unless forced)
    if not force_json and not _should_use_json_output():
        # Check agent-specific migration
        migrated_agents = os.getenv('AGENT_JSON_MIGRATION', '').lower().split(',')
        migrated_agents = [a.strip() for a in migrated_agents if a.strip()]

        if agent.lower() not in migrated_agents:
            # Fall back to legacy text output
            print_agent_output(message, agent)
            return

    # Create structured event
    event = create_agent_update_event(
        agent_id=agent.lower(),
        agent_name=agent,
        status=status,
        message=message,
        progress=progress,
        data=data,
        error=error
    )

    # Output as JSON (one line for reliable parsing)
    print(json.dumps(event))


# ============================================================================
# Convenience Wrappers
# ============================================================================

def print_agent_progress(agent: str, message: str, progress: int) -> None:
    """Convenience wrapper for progress updates"""
    print_structured_output(
        message=message,
        agent=agent,
        status="running",
        progress=progress
    )


def print_agent_completion(agent: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Convenience wrapper for completion events"""
    print_structured_output(
        message=message,
        agent=agent,
        status="completed",
        progress=100,
        data=data
    )


def print_agent_error(agent: str, message: str, error_code: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience wrapper for error events"""
    error: AgentError = {
        "code": error_code,
        "message": message,
    }
    if details:
        error["details"] = details

    print_structured_output(
        message=message,
        agent=agent,
        status="error",
        error=error
    )