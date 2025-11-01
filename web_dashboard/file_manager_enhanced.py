import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from filename_utils import FilenameParser
from models import FileInfo, ResearchSession

logger = logging.getLogger(__name__)


class EnhancedFileManager:
    """Enhanced file manager with additional download capabilities"""

    def __init__(self, project_root: Path, web_static_path: Path):
        self.project_root = project_root
        self.outputs_path = project_root / "outputs"
        self.web_static_path = web_static_path
        self.downloads_path = web_static_path / "downloads"
        self.temp_path = web_static_path / "temp"

        # Ensure directories exist
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

        # Expected output file extensions from the actual system
        self.supported_extensions = [".pdf", ".docx", ".md", ".txt", ".json"]

        # Preview support
        self.preview_extensions = [".md", ".txt", ".json"]

        # Initialize mimetypes
        mimetypes.init()

        # Download history cache
        self.download_history: List[Dict[str, Any]] = []
        self.max_history = 100

    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for a file - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module (Gemini validation: dc76fc08)
        return FilenameParser.get_mime_type(filename)

    async def create_session_zip(self, session_id: str) -> Optional[Path]:
        """Create a ZIP file containing all files from a session"""
        try:
            session_dir = self.outputs_path / session_id
            if not session_dir.exists():
                logger.error(f"Session directory not found: {session_dir}")
                return None

            # Create temporary ZIP file
            zip_filename = f"{session_id}_all_files.zip"
            zip_path = self.temp_path / zip_filename

            # Check if ZIP already exists and is recent (cache for 1 hour)
            if zip_path.exists():
                file_age = datetime.now() - datetime.fromtimestamp(
                    zip_path.stat().st_mtime
                )
                if file_age < timedelta(hours=1):
                    logger.info(f"Using cached ZIP file: {zip_path}")
                    return zip_path

            # Create new ZIP file
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0

                # Add all supported files from the session directory
                for file_path in session_dir.iterdir():
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in self.supported_extensions
                    ):
                        # Create user-friendly name in ZIP
                        friendly_name = self.create_friendly_filename_from_uuid(
                            file_path.name
                        )
                        zipf.write(file_path, arcname=friendly_name)
                        files_added += 1
                        logger.info(f"Added to ZIP: {friendly_name}")

                # Add drafts if they exist
                drafts_dir = session_dir / "drafts"
                if drafts_dir.exists():
                    for file_path in drafts_dir.rglob("*"):
                        if (
                            file_path.is_file()
                            and file_path.suffix.lower() in self.supported_extensions
                        ):
                            relative_path = file_path.relative_to(session_dir)
                            zipf.write(file_path, arcname=str(relative_path))
                            files_added += 1

            if files_added == 0:
                logger.warning(f"No files found to add to ZIP for session {session_id}")
                zip_path.unlink()  # Remove empty ZIP
                return None

            logger.info(f"Created ZIP with {files_added} files: {zip_path}")
            return zip_path

        except Exception as e:
            logger.error(f"Error creating ZIP for session {session_id}: {e}")
            return None

    async def get_file_preview(
        self, session_id: str, filename: str, max_lines: int = 50
    ) -> Optional[Dict]:
        """Get a preview of a text-based file"""
        try:
            file_path = self.get_file_path(session_id, filename)
            if not file_path:
                return None

            # Check if file is previewable
            if file_path.suffix.lower() not in self.preview_extensions:
                return {"error": "File type not previewable", "supported": False}

            # Read file content
            content_lines = []
            total_lines = 0
            file_size = file_path.stat().st_size

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if line_num <= max_lines:
                        content_lines.append(line.rstrip())
                    total_lines = line_num

            preview_data = {
                "supported": True,
                "filename": filename,
                "content": "\n".join(content_lines),
                "total_lines": total_lines,
                "preview_lines": len(content_lines),
                "truncated": total_lines > max_lines,
                "file_size": file_size,
                "mime_type": self.get_mime_type(filename),
            }

            return preview_data

        except Exception as e:
            logger.error(f"Error getting preview for {filename}: {e}")
            return {"error": str(e), "supported": False}

    # DEPRECATED AND DISABLED - DO NOT USE
    # Reason: Violates DRY principle by calculating file_count and total_size_bytes from filesystem
    # These values are maintained by PostgreSQL trigger on draft_files table
    #
    # IMPACT ANALYSIS:
    # - main.py:214 uses this in get_session_state() - Replace with database.get_session_file_stats()
    # - main.py:763-765 API endpoint /api/session/{session_id}/statistics - Replace entirely
    #
    # UNIQUE FEATURES LOST:
    # - file_types breakdown (e.g., {".pdf": 3, ".docx": 2})
    # - languages detection (Vietnamese, English, Original)
    # - creation_date / last_modified timestamps
    #
    # TODO: Create new database-backed function for these unique features OR
    # store them in draft_files table (file_type, language columns)
    #
    # Commented out: 2025-11-02
    # Will be removed after: All callers migrated to database queries
    async def get_session_statistics(self, session_id: str) -> Dict:
        """
        DISABLED - See deprecation comment above
        """
        raise NotImplementedError(
            "get_session_statistics() is DEPRECATED. "
            "Use database.get_session_file_stats() for file_count and total_size_bytes. "
            "See file_manager_enhanced.py:168 for full deprecation rationale."
        )

    async def search_files(
        self, query: str, session_id: Optional[str] = None
    ) -> List[Dict]:
        """Search for files across sessions or within a specific session"""
        results = []
        query_lower = query.lower()

        try:
            if session_id:
                # Search within specific session
                sessions = [session_id]
            else:
                # Search all sessions
                sessions = [d.name for d in self.outputs_path.iterdir() if d.is_dir()]

            for sess_id in sessions:
                session_dir = self.outputs_path / sess_id
                if not session_dir.exists():
                    continue

                # Parse session info
                timestamp, subject = self.parse_session_info(sess_id)

                # Check if subject matches query
                if query_lower in subject.lower():
                    # Add all files from matching session
                    files = await self.discover_session_files(sess_id)
                    for file in files:
                        results.append(
                            {
                                "session_id": sess_id,
                                "session_subject": subject,
                                "file": file.dict(),
                                "match_type": "session_subject",
                            }
                        )

                # Check individual files
                for file_path in session_dir.iterdir():
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in self.supported_extensions
                    ):
                        friendly_name = self.create_friendly_filename_from_uuid(
                            file_path.name
                        )

                        if query_lower in friendly_name.lower():
                            file_info = FileInfo(
                                filename=friendly_name,
                                url=f"/download/{sess_id}/{file_path.name}",
                                size=file_path.stat().st_size,
                                created=datetime.fromtimestamp(
                                    file_path.stat().st_ctime
                                ),
                            )

                            results.append(
                                {
                                    "session_id": sess_id,
                                    "session_subject": subject,
                                    "file": file_info.dict(),
                                    "match_type": "filename",
                                }
                            )

            return results

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []

    def track_download(
        self, session_id: str, filename: str, user_info: Optional[Dict] = None
    ):
        """Track file download for analytics"""
        download_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "filename": filename,
            "user_info": user_info or {},
        }

        self.download_history.append(download_record)

        # Limit history size
        if len(self.download_history) > self.max_history:
            self.download_history = self.download_history[-self.max_history :]

        # Optionally save to file for persistence
        try:
            history_file = self.downloads_path / "download_history.json"
            with open(history_file, "w") as f:
                json.dump(self.download_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving download history: {e}")

    async def get_download_history(self, limit: int = 10) -> List[Dict]:
        """Get recent download history"""
        return self.download_history[-limit:]

    async def cleanup_temp_files(self, max_age_hours: int = 2):
        """Clean up old temporary files"""
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        try:
            if self.temp_path.exists():
                for file_path in self.temp_path.iterdir():
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"Cleaned up temp file: {file_path.name}")

        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")

        return cleaned_count

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def get_file_metadata(self, session_id: str, filename: str) -> Optional[Dict]:
        """Get detailed metadata for a file"""
        try:
            file_path = self.get_file_path(session_id, filename)
            if not file_path:
                return None

            stat = file_path.stat()

            metadata = {
                "filename": filename,
                "friendly_name": self.create_friendly_filename_from_uuid(filename),
                "size": stat.st_size,
                "size_formatted": self.format_file_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": self.get_mime_type(filename),
                "extension": file_path.suffix.lower(),
                "hash": self.calculate_file_hash(file_path),
                "previewable": file_path.suffix.lower() in self.preview_extensions,
            }

            return metadata

        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return None

    def format_file_size(self, bytes: int) -> str:
        """Format file size in human-readable format"""
        size: float = float(bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    async def get_file_content(self, file_path_str: str) -> Tuple[bytes, str]:
        """
        Get file content for preview.

        Args:
            file_path_str: Relative or absolute path to file

        Returns:
            Tuple of (file_content as bytes, mime_type as string)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large (>50MB)
        """
        # Convert to Path object
        file_path = Path(file_path_str)

        # If relative path, resolve against outputs directory
        if not file_path.is_absolute():
            file_path = self.outputs_path / file_path

        # Security: prevent directory traversal
        try:
            file_path = file_path.resolve()
            # Ensure file is within outputs directory
            if not str(file_path).startswith(str(self.outputs_path.resolve())):
                raise ValueError("Access denied: file path outside allowed directory")
        except Exception as e:
            logger.error(f"Path resolution error: {e}")
            raise FileNotFoundError(f"Invalid file path: {file_path_str}")

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size (50MB limit)
        file_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise ValueError(
                f"File too large for preview: {file_size} bytes (max: {max_size})"
            )

        # Read file content
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

        # Get MIME type
        mime_type = self.get_mime_type(file_path.name)

        return content, mime_type

    # Include all original methods from FileManager
    def parse_session_info(self, dir_name: str) -> Tuple[str, str]:
        """Parse session ID and subject from directory name"""
        if dir_name.startswith("run_"):
            parts = dir_name.split("_", 2)
            if len(parts) >= 3:
                timestamp = parts[1]
                subject = parts[2]
                return timestamp, subject
        return dir_name, "Unknown Subject"

    def create_friendly_filename_from_uuid(self, uuid_filename: str) -> str:
        """Create a user-friendly filename from UUID-based filename"""
        if not uuid_filename or "." not in uuid_filename:
            return uuid_filename

        name_part, extension = uuid_filename.rsplit(".", 1)
        extension = extension.lower()

        if "_" in name_part and len(name_part.split("_")[-1]) <= 3:
            language_code = name_part.split("_")[-1]
            base_name = f"research_report_{language_code}"
        else:
            base_name = "research_report"

        return f"{base_name}.{extension}"

    async def discover_session_files(self, session_id: str) -> List[FileInfo]:
        """Discover actual files in a research session directory"""
        files: List[FileInfo] = []
        session_dir = self.outputs_path / session_id

        if not session_dir.exists():
            return files

        try:
            for file_path in session_dir.iterdir():
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.supported_extensions
                ):
                    # Use actual UUID filename (not friendly name) for uniqueness
                    # This ensures downloads work correctly
                    file_info = FileInfo(
                        filename=file_path.name,  # Use UUID filename directly
                        url=f"/download/{session_id}/{file_path.name}",
                        size=file_path.stat().st_size,
                        created=datetime.fromtimestamp(file_path.stat().st_ctime),
                    )
                    files.append(file_info)

            files.sort(
                key=lambda f: (self.get_file_sort_priority(f.filename), f.filename)
            )

        except Exception as e:
            logger.error(f"Error discovering files for session {session_id}: {e}")

        return files

    def get_file_sort_priority(self, filename: str) -> int:
        """Get sort priority for files - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module (Gemini validation: dc76fc08)
        return FilenameParser.get_sort_priority(filename)

    def get_file_path(self, session_id: str, filename: str) -> Optional[Path]:
        """Get the full path to a downloadable file"""
        file_path = self.downloads_path / session_id / filename
        if file_path.exists() and file_path.is_file():
            return file_path

        session_dir = self.outputs_path / session_id
        if session_dir.exists():
            for file_path in session_dir.iterdir():
                if file_path.is_file() and file_path.name == filename:
                    return file_path

        return None

    def is_valid_filename(self, filename: str) -> bool:
        """Check if filename has a supported extension - delegates to centralized FilenameParser"""
        # MIGRATED: Use centralized module (Gemini validation: dc76fc08)
        return FilenameParser.is_valid(filename)

    async def get_session_files(self, session_id: str) -> List[FileInfo]:
        """Get list of available files for a session"""
        return await self.discover_session_files(session_id)

    async def get_all_research_sessions(self) -> List[ResearchSession]:
        """
        Get all available research sessions.

        DEPRECATED: This method is for filesystem-only mode.
        For database-backed sessions, use database.get_user_sessions() instead.

        DRY VIOLATION WARNING: This calculates file_count on-the-fly.
        Use database columns for production.
        """
        sessions: List[ResearchSession] = []

        if not self.outputs_path.exists():
            return sessions

        try:
            for dir_path in self.outputs_path.iterdir():
                if dir_path.is_dir() and dir_path.name.startswith("run_"):
                    session_id = dir_path.name
                    timestamp, subject = self.parse_session_info(session_id)

                    created = datetime.fromtimestamp(dir_path.stat().st_mtime)
                    session_files = await self.discover_session_files(session_id)

                    # DEPRECATED: Calculating file_count on-the-fly violates DRY
                    # TODO: Remove this method once all sessions use database
                    session = ResearchSession(
                        session_id=session_id,
                        subject=subject,
                        created=created,
                        files=session_files,
                        file_count=len(session_files),  # DEPRECATED - use DB instead
                    )
                    sessions.append(session)

            sessions.sort(key=lambda x: x.created, reverse=True)

        except Exception as e:
            logger.error(f"Error getting research sessions: {e}")

        return sessions
