"""
Event schemas for WebSocket communication between backend and frontend.

This module defines the formal event contract using Pydantic models for type safety
and validation. All WebSocket events must conform to these schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentUpdatePayload(BaseModel):
    """Payload for agent status updates"""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_name: str = Field(..., description="Human-readable agent name")
    status: Literal["pending", "running", "completed", "error"] = Field(
        ..., description="Current status of the agent"
    )
    progress: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage (0-100), None if not applicable",
    )
    message: str = Field(..., description="Status message or description")
    stats: Optional[Dict[str, Any]] = Field(None, description="Optional statistics")


class FileGeneratedPayload(BaseModel):
    """Payload for file generation events"""

    file_id: str = Field(..., description="Unique identifier for the file")
    filename: str = Field(..., description="Name of the generated file (UUID format)")
    file_type: str = Field(..., description="File type (e.g., 'pdf', 'docx', 'md')")
    language: str = Field(..., description="Language of the content")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    path: Optional[str] = Field(None, description="Relative path to the file")
    friendly_name: str = Field(..., description="User-friendly display name (e.g., 'research_report_vi.pdf')")


class ResearchStatusPayload(BaseModel):
    """Payload for overall research status updates"""

    session_id: str = Field(..., description="Research session identifier")
    overall_status: Literal["initializing", "running", "completed", "failed"] = Field(
        ..., description="Overall research status"
    )
    progress: float = Field(ge=0, le=100, description="Overall progress percentage")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )
    current_stage: Optional[str] = Field(None, description="Current research stage")
    agents_completed: int = Field(ge=0, description="Number of agents completed")
    agents_total: int = Field(ge=0, description="Total number of agents")


class LogPayload(BaseModel):
    """Payload for log messages"""

    level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        ..., description="Log level"
    )
    message: str = Field(..., description="Log message")
    source: Optional[str] = Field(
        None, description="Source of the log (e.g., agent name)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the log was created"
    )


class ErrorPayload(BaseModel):
    """Payload for error events"""

    error_type: str = Field(..., description="Type/category of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    recoverable: bool = Field(
        default=True, description="Whether the error is recoverable"
    )
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")


# Discriminated Union Event Classes


class AgentUpdateEvent(BaseModel):
    """Agent update event with strongly-typed payload"""

    event_type: Literal["agent_update"] = "agent_update"
    payload: AgentUpdatePayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class FileGeneratedEvent(BaseModel):
    """File generated event with strongly-typed payload"""

    event_type: Literal["file_generated"] = "file_generated"
    payload: FileGeneratedPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class ResearchStatusEvent(BaseModel):
    """Research status event with strongly-typed payload"""

    event_type: Literal["research_status"] = "research_status"
    payload: ResearchStatusPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class LogEvent(BaseModel):
    """Log event with strongly-typed payload"""

    event_type: Literal["log"] = "log"
    payload: LogPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class ErrorEvent(BaseModel):
    """Error event with strongly-typed payload"""

    event_type: Literal["error"] = "error"
    payload: ErrorPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class ConnectionStatusPayload(BaseModel):
    """Payload for connection status updates"""

    status: Literal["connected", "disconnected", "reconnecting"] = Field(
        ..., description="Connection status"
    )
    message: Optional[str] = Field(None, description="Status message")


class ConnectionStatusEvent(BaseModel):
    """Connection status event with strongly-typed payload"""

    event_type: Literal["connection_status"] = "connection_status"
    payload: ConnectionStatusPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class FilesReadyPayload(BaseModel):
    """Payload for when files are ready for download"""

    file_count: int = Field(ge=0, description="Number of files ready")
    files: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of file information"
    )
    total_size_bytes: int = Field(ge=0, description="Total size of all files")


class FilesReadyEvent(BaseModel):
    """Files ready event with strongly-typed payload"""

    event_type: Literal["files_ready"] = "files_ready"
    payload: FilesReadyPayload
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.model_dump(mode="json"),
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


# Discriminated Union Type
from typing import Union

WebSocketEvent = Union[
    AgentUpdateEvent,
    FileGeneratedEvent,
    ResearchStatusEvent,
    LogEvent,
    ErrorEvent,
    ConnectionStatusEvent,
    FilesReadyEvent,
]


# Helper functions for creating typed events


def create_agent_update_event(
    session_id: str,
    agent_id: str,
    agent_name: str,
    status: str,
    progress: Optional[float],  # Allow None for agents without progress tracking
    message: str,
    stats: Optional[Dict[str, Any]] = None,
) -> AgentUpdateEvent:
    """Create a typed agent update event"""
    payload = AgentUpdatePayload(
        agent_id=agent_id,
        agent_name=agent_name,
        status=status,  # type: ignore
        progress=progress,
        message=message,
        stats=stats,
    )

    return AgentUpdateEvent(payload=payload, session_id=session_id)


def create_file_generated_event(
    session_id: str,
    file_id: str,
    filename: str,
    file_type: str,
    language: str,
    size_bytes: int,
    friendly_name: str,
    path: Optional[str] = None,
) -> FileGeneratedEvent:
    """Create a typed file generated event"""
    payload = FileGeneratedPayload(
        file_id=file_id,
        filename=filename,
        file_type=file_type,
        language=language,
        size_bytes=size_bytes,
        path=path,
        friendly_name=friendly_name,
    )

    return FileGeneratedEvent(payload=payload, session_id=session_id)


def create_research_status_event(
    session_id: str,
    overall_status: str,
    progress: float,
    current_stage: Optional[str] = None,
    agents_completed: int = 0,
    agents_total: int = 7,  # 7 active agents (includes Orchestrator)
    estimated_completion: Optional[datetime] = None,
) -> ResearchStatusEvent:
    """Create a typed research status event"""
    payload = ResearchStatusPayload(
        session_id=session_id,
        overall_status=overall_status,  # type: ignore
        progress=progress,
        current_stage=current_stage,
        agents_completed=agents_completed,
        agents_total=agents_total,
        estimated_completion=estimated_completion,
    )

    return ResearchStatusEvent(payload=payload, session_id=session_id)


def create_log_event(
    session_id: str, level: str, message: str, source: Optional[str] = None
) -> LogEvent:
    """Create a typed log event"""
    payload = LogPayload(level=level, message=message, source=source)  # type: ignore

    return LogEvent(payload=payload, session_id=session_id)


def create_error_event(
    session_id: str,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = True,
    stack_trace: Optional[str] = None,
) -> ErrorEvent:
    """Create a typed error event"""
    payload = ErrorPayload(
        error_type=error_type,
        message=message,
        details=details,
        recoverable=recoverable,
        stack_trace=stack_trace,
    )

    return ErrorEvent(payload=payload, session_id=session_id)
