from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Configuration
from config import settings


class ResearchRequest(BaseModel):
    """Model for research request from web dashboard"""

    subject: str = Field(
        ...,
        min_length=settings.MIN_SUBJECT_LENGTH,
        max_length=settings.MAX_SUBJECT_LENGTH,
        description="Research subject",
    )
    language: str = Field(default=settings.RESEARCH_LANGUAGE, description="Output language")
    save_files: bool = Field(default=True, description="Save output files")


class ResearchResponse(BaseModel):
    """Model for research response"""

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Request status")
    message: str = Field(..., description="Response message")
    websocket_url: str = Field(..., description="WebSocket URL for log streaming")


class LogMessage(BaseModel):
    """Model for log messages streamed via WebSocket"""

    timestamp: datetime = Field(default_factory=datetime.now)
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: str = Field(default="cli", description="Message source")


class FileInfo(BaseModel):
    """Model for downloadable file information"""

    filename: str = Field(..., description="File name (UUID format)")
    url: str = Field(..., description="Download URL")
    size: Optional[int] = Field(None, description="File size in bytes")
    created: Optional[datetime] = Field(None, description="File creation time")
    file_type: str = Field(..., description="File type extension (e.g., 'pdf', 'docx', 'md')")
    language: str = Field(default="en", description="Language code (e.g., 'en', 'vi')")
    friendly_name: str = Field(
        ..., description="User-friendly display name (e.g., 'research_report_vi.pdf')"
    )


class SessionStatus(BaseModel):
    """Model for session status"""

    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Session status: pending, running, completed, failed")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    files: list[FileInfo] = Field(default_factory=list, description="Available download files")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ResearchSession(BaseModel):
    """Model for research session information"""

    session_id: str = Field(..., description="Session identifier (directory name)")
    subject: str = Field(..., description="Research subject/query")
    created: datetime = Field(..., description="Session creation time")
    status: str = Field(default="completed", description="Session status")
    files: List[FileInfo] = Field(default_factory=list, description="Available files")
    file_count: int = Field(default=0, description="Number of files generated")


class TransferSessionsRequest(BaseModel):
    """Model for session transfer request"""

    old_user_id: str = Field(..., description="Anonymous user UUID")
    new_user_id: str = Field(..., description="Permanent account UUID")


# ============================================================
# Database Models (Story 1.3)
# ============================================================


class SessionStatusEnum(str, Enum):
    """Enum for research session status"""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStageEnum(str, Enum):
    """Enum for research stages"""

    INITIAL_RESEARCH = "1_initial_research"
    PLANNING = "2_planning"
    PARALLEL_RESEARCH = "3_parallel_research"
    WRITING = "4_writing"


class User(BaseModel):
    """
    Database model for auth.users table (managed by Supabase Auth).

    NOTE: This model is for TYPE REFERENCE ONLY. Do NOT create a custom
    public.users table. Always reference auth.users directly in foreign keys.

    The auth.users table is managed by Supabase Auth and contains user
    authentication data. See migration 20251101040000 for details.
    """

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="User UUID (primary key)")
    email: Optional[str] = Field(None, description="User email (nullable for anonymous users)")
    is_anonymous: bool = Field(default=False, description="Whether user is anonymous")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ResearchSessionDB(BaseModel):
    """
    Database model for research_sessions table.

    Includes all columns from migration 20251102_add_session_metadata.sql.
    DRY: file_count and total_size_bytes are maintained by database triggers
    and update_session_file_stats() function.
    """

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Session UUID (primary key)")
    user_id: UUID = Field(..., description="Foreign key to auth.users(id)")
    title: str = Field(..., description="Research session title/subject")
    status: SessionStatusEnum = Field(
        default=SessionStatusEnum.IN_PROGRESS, description="Session status"
    )
    language: str = Field(default="vi", description="Research output language (ISO 639-1 code)")
    parameters: Optional[dict] = Field(
        default_factory=dict,
        description="Research parameters (tone, depth, format options) as JSON",
    )
    file_count: int = Field(
        default=0, description="Number of files generated (DRY: maintained by DB)"
    )
    total_size_bytes: int = Field(
        default=0, description="Total size of all files in bytes (DRY: maintained by DB)"
    )
    archived_at: Optional[datetime] = Field(
        None, description="Timestamp when session was archived (NULL = active)"
    )
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DraftFile(BaseModel):
    """
    Database model for draft_files table.

    DRY: file_size_bytes must be populated when file is detected
    to enable accurate total_size_bytes calculation.
    """

    model_config = {"from_attributes": True}

    id: UUID = Field(..., description="Draft file UUID (primary key)")
    session_id: UUID = Field(..., description="Foreign key to research_sessions.id")
    stage: ResearchStageEnum = Field(..., description="Research stage")
    file_path: str = Field(..., description="Path to draft file")
    file_size_bytes: int = Field(
        default=0, description="File size in bytes (DRY: required for aggregation)"
    )
    detected_at: datetime = Field(..., description="File detection timestamp")
