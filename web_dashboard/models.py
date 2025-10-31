from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ResearchRequest(BaseModel):
    """Model for research request from web dashboard"""
    subject: str = Field(..., min_length=3, max_length=1000, description="Research subject")
    language: str = Field(default="vi", description="Output language")
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
    filename: str = Field(..., description="File name")
    url: str = Field(..., description="Download URL")
    size: Optional[int] = Field(None, description="File size in bytes")
    created: Optional[datetime] = Field(None, description="File creation time")

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