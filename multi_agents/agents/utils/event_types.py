"""
Type definitions for structured agent events (Phase 2)

This module defines the JSON schema for agent communication using TypedDict.
These types provide static analysis, autocomplete support, and serve as documentation.

Schema follows envelope-based event pattern for extensibility.
"""

from typing import TypedDict, Literal, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Agent Status Values
# ============================================================================

AgentStatus = Literal["pending", "running", "completed", "error"]
"""
Possible agent status values:
- pending: Agent has not started yet
- running: Agent is currently processing
- completed: Agent finished successfully
- error: Agent encountered an error
"""


# ============================================================================
# Error Structure
# ============================================================================

class AgentError(TypedDict, total=False):
    """
    Structured error information when agent status is 'error'

    Fields:
        code: Machine-readable error code (e.g., "API_TIMEOUT", "INVALID_INPUT")
        message: Human-readable error description
        details: Additional error context (stack trace, request data, etc.)
    """
    code: str
    message: str
    details: Optional[Dict[str, Any]]


# ============================================================================
# Agent Update Payload
# ============================================================================

class AgentUpdatePayload(TypedDict, total=False):
    """
    Payload for agent_update events

    Required fields:
        agent_id: Machine-readable lowercase identifier (e.g., "researcher", "writer")
        agent_name: Human-readable display name (e.g., "RESEARCHER", "Writer")
        status: Current agent state (pending, running, completed, error)
        message: Human-readable log message for display
        timestamp: ISO 8601 timestamp when event was generated

    Optional fields:
        progress: Completion percentage (0-100)
        data: Structured data produced by agent (URLs, document text, etc.)
        error: Error details if status is 'error'
    """
    # Required fields
    agent_id: str
    agent_name: str
    status: AgentStatus
    message: str
    timestamp: str

    # Optional fields
    progress: int  # 0-100
    data: Dict[str, Any]
    error: AgentError


# ============================================================================
# Event Envelope
# ============================================================================

class AgentUpdateEvent(TypedDict):
    """
    Top-level event envelope for agent updates

    The envelope pattern allows introducing new event types in the future
    without breaking existing consumers. All events follow this structure:
    {
        "type": "event_type_name",
        "payload": { ... event-specific data ... }
    }

    Fields:
        type: Always "agent_update" for agent status/progress events
        payload: AgentUpdatePayload with all agent-specific data
    """
    type: Literal["agent_update"]
    payload: AgentUpdatePayload


# ============================================================================
# Helper Functions
# ============================================================================

def create_agent_update_event(
    agent_id: str,
    agent_name: str,
    status: AgentStatus,
    message: str,
    progress: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[AgentError] = None
) -> AgentUpdateEvent:
    """
    Factory function to create a properly structured agent update event

    Args:
        agent_id: Machine-readable agent identifier (lowercase)
        agent_name: Human-readable agent name for display
        status: Current agent status (pending, running, completed, error)
        message: Human-readable status message
        progress: Optional completion percentage (0-100)
        data: Optional structured data produced by agent
        error: Optional error details if status is 'error'

    Returns:
        AgentUpdateEvent with proper envelope structure

    Example:
        event = create_agent_update_event(
            agent_id="researcher",
            agent_name="RESEARCHER",
            status="running",
            message="Found 5 relevant articles",
            progress=60,
            data={"urls_found": ["http://..."]}
        )
    """
    payload: AgentUpdatePayload = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    # Add optional fields only if provided
    if progress is not None:
        payload["progress"] = progress
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error

    return {
        "type": "agent_update",
        "payload": payload
    }
